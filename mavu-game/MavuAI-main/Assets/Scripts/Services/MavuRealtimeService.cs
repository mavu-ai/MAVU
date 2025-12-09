using System;
using System.Collections;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Net.WebSockets;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using UnityEngine;
using UnityEngine.Events;

[RequireComponent(typeof(AudioSource))]
public class MavuRealtimeService : MonoBehaviour
{
    // --- Конфигурация ---
    [Header("Настройки")]
    [SerializeField] private string socketUrl = "wss://mavu-api.aey-inc.uz/api/v1/realtime";
    [SerializeField] private int serverSampleRate = 24000;
    [SerializeField] private bool muteMicWhenAiSpeaks = true;
    [SerializeField] private float sendInterval = 0.25f; // Интервал из логов веба
    public float CurrentVolume { get; private set; }

    // --- События ---
    public UnityEvent Started = new UnityEvent();
    public UnityEvent Finished = new UnityEvent();
    [Serializable] public class PhraseEvent : UnityEvent<string> { }
    public PhraseEvent OnPhraseRecognized;

    // --- Состояние ---
    public bool IsListening { get; private set; } = false;
    public bool IsAiSpeaking { get; private set; } = false;

    // --- Внутренности ---
    private ClientWebSocket _webSocket;
    private CancellationTokenSource _cts;
    private AudioSource _audioSource;
    private string _micDevice;
    private AudioClip _micClip;
    private bool _isMicRecording;
    
    // Частоты
    private int _actualMicFrequency;
    private int _outputSampleRate;
    
    // Очереди
    private readonly ConcurrentQueue<float> _audioReceiveQueue = new ConcurrentQueue<float>();
    private readonly ConcurrentQueue<ArraySegment<byte>> _sendQueue = new ConcurrentQueue<ArraySegment<byte>>();

    private void Awake()
    {
        _audioSource = GetComponent<AudioSource>();
        _audioSource.loop = true;
        _audioSource.playOnAwake = false;
        
        // Узнаем, какая частота у Unity на этом устройстве (обычно 48000 или 44100)
        _outputSampleRate = AudioSettings.outputSampleRate;
        Debug.Log($"[Audio] System Output Rate: {_outputSampleRate} Hz");

        _audioSource.clip = AudioClip.Create("Dummy", 1, 1, _outputSampleRate, false); 
    }

    private IEnumerator Start()
    {
        if (!Application.HasUserAuthorization(UserAuthorization.Microphone))
            yield return Application.RequestUserAuthorization(UserAuthorization.Microphone);
    }

    private void OnDestroy() { StopSession(); }
    public void ToggleSession() { if (IsListening) StopSession(); else StartSession(); }

    public void StartSession()
    {
        if (IsListening) return;
        if (string.IsNullOrEmpty(AuthService.Instance.SessionToken)) { Debug.LogError("[Mavu] Нет токена!"); return; }
        StartCoroutine(ConnectRoutine(AuthService.Instance.SessionToken));
    }

    public void StopSession()
    {
        if (!IsListening) return;
        IsListening = false;
        _cts?.Cancel();
        Microphone.End(_micDevice);
        
        while (_audioReceiveQueue.TryDequeue(out _)) { }
        while (_sendQueue.TryDequeue(out _)) { }
        
        Finished?.Invoke();
        Debug.Log("[Mavu] Сессия остановлена.");
    }

    private IEnumerator ConnectRoutine(string token)
    {
        _cts = new CancellationTokenSource();
        _webSocket = new ClientWebSocket();
        
        var uriBuilder = new UriBuilder(socketUrl);
        uriBuilder.Query = $"session_token={token}";

        Debug.Log($"[Mavu] 🚀 Подключение...");

        var connectTask = _webSocket.ConnectAsync(uriBuilder.Uri, _cts.Token);
        yield return new WaitUntil(() => connectTask.IsCompleted);

        if (connectTask.Exception != null)
        {
            Debug.LogError($"[Mavu] ❌ Ошибка: {connectTask.Exception.InnerException?.Message ?? connectTask.Exception.Message}");
            StopSession();
            yield break;
        }

        Debug.Log("[Mavu] ✅ Подключено!");
        IsListening = true;
        Started?.Invoke();

        _ = ReadLoop(_cts.Token);
        _ = SendLoop(_cts.Token);
        
        StartMicrophone();
        _audioSource.Play();
    }

    // --- МИКРОФОН ---
    private void StartMicrophone()
    {
        _micDevice = Microphone.devices[0];
        _micClip = Microphone.Start(_micDevice, true, 10, serverSampleRate);
        _actualMicFrequency = _micClip.frequency;
        
        Debug.Log($"[Mic] Hardware Rate: {_actualMicFrequency} Hz -> Target: {serverSampleRate} Hz");
        
        _isMicRecording = true;
        iOSAudioFix.RestoreAudioSession();
        StartCoroutine(ProcessMicrophoneRoutine());
    }

    private IEnumerator ProcessMicrophoneRoutine()
    {
        int lastPos = 0;
        
        while (_isMicRecording && IsListening)
        {
            int pos = Microphone.GetPosition(_micDevice);
            if (pos < 0 || _micClip == null) { yield return null; continue; }
            if (pos < lastPos) lastPos = 0;

            if (pos > lastPos)
            {
                if (muteMicWhenAiSpeaks && IsAiSpeaking)
                {
                    lastPos = pos;
                    yield return new WaitForSeconds(sendInterval);
                    continue;
                }

                int len = pos - lastPos;
                float[] rawSamples = new float[len];
                _micClip.GetData(rawSamples, lastPos);

                ProcessAndEnqueueAudio(rawSamples);
                lastPos = pos;
            }
            yield return new WaitForSeconds(sendInterval);
        }
    }

    private void ProcessAndEnqueueAudio(float[] inputSamples)
    {
        float[] sentSamples;

        // 1. Ресемплинг (Mic -> Server)
        if (_actualMicFrequency != serverSampleRate)
            sentSamples = Resample(inputSamples, _actualMicFrequency, serverSampleRate);
        else
            sentSamples = inputSamples;

        // 2. Gain
        float gain = 5.0f; 

        byte[] pcmData = new byte[sentSamples.Length * 2];
        for (int i = 0; i < sentSamples.Length; i++)
        {
            float val = sentSamples[i] * gain;
            short pcmShort = (short)(Mathf.Clamp(val, -1f, 1f) * 32767f);
            
            byte[] bytes = BitConverter.GetBytes(pcmShort);
            if (!BitConverter.IsLittleEndian) Array.Reverse(bytes);

            pcmData[i * 2] = bytes[0];
            pcmData[i * 2 + 1] = bytes[1];
        }

        string base64 = Convert.ToBase64String(pcmData);
        string json = $"{{\"type\":\"audio.append\",\"audio\":\"{base64}\"}}";
        EnqueueMessage(json);
    }

    private float[] Resample(float[] input, int sourceRate, int targetRate)
    {
        if (sourceRate == targetRate) return input;
        
        float ratio = (float)sourceRate / targetRate;
        int newLength = (int)(input.Length / ratio);
        
        float[] output = new float[newLength];

        for (int i = 0; i < newLength; i++)
        {
            float position = i * ratio;
            int index = (int)position;
            float fraction = position - index;

            if (index >= input.Length - 1)
            {
                output[i] = input[input.Length - 1];
            }
            else
            {
                output[i] = Mathf.Lerp(input[index], input[index + 1], fraction);
            }
        }
        return output;
    }

    private void EnqueueMessage(string json)
    {
        byte[] bytes = Encoding.UTF8.GetBytes(json);
        _sendQueue.Enqueue(new ArraySegment<byte>(bytes));
    }

    private async Task SendLoop(CancellationToken token)
    {
        while (!token.IsCancellationRequested && _webSocket.State == WebSocketState.Open)
        {
            if (_sendQueue.TryDequeue(out var message))
            {
                try { await _webSocket.SendAsync(message, WebSocketMessageType.Text, true, token); }
                catch { break; }
            }
            else { await Task.Delay(10); }
        }
    }

    private async Task ReadLoop(CancellationToken token)
    {
        var buffer = new byte[1024 * 64];
        try
        {
            while (_webSocket.State == WebSocketState.Open && !token.IsCancellationRequested)
            {
                var resultBuffer = new List<byte>();
                WebSocketReceiveResult result;
                do
                {
                    result = await _webSocket.ReceiveAsync(new ArraySegment<byte>(buffer), token);
                    resultBuffer.AddRange(new ArraySegment<byte>(buffer, 0, result.Count));
                } while (!result.EndOfMessage);

                if (result.MessageType == WebSocketMessageType.Close) { StopSession(); break; }

                string json = Encoding.UTF8.GetString(resultBuffer.ToArray());
                HandleMessage(json);
            }
        }
        catch (Exception e) { Debug.LogError($"[Reader] {e.Message}"); }
    }

    [Serializable] private class WSMessage { public string type; public string audio; public string text; public string error; }

    private void HandleMessage(string json)
    {
        var msg = JsonUtility.FromJson<WSMessage>(json);
        
        if (msg.type == "audio.delta" && !string.IsNullOrEmpty(msg.audio))
        {
            byte[] audioBytes = Convert.FromBase64String(msg.audio);
            EnqueueAudio(audioBytes);
            UnityMainThreadDispatcher.Instance().Enqueue(() => IsAiSpeaking = true);
        }
        else if (msg.type == "transcription")
        {
            UnityMainThreadDispatcher.Instance().Enqueue(() => {
                Debug.Log($"[ИИ]: {msg.text}"); 
                OnPhraseRecognized?.Invoke(msg.text);
            });
        }
    }

    private void EnqueueAudio(byte[] pcmData)
    {
        int sourceCount = pcmData.Length / 2;
        float[] sourceData = new float[sourceCount];
        
        for (int i = 0; i < sourceCount; i++)
        {
            short val = BitConverter.ToInt16(pcmData, i * 2);
            sourceData[i] = val / 32768f;
        }

        
        float[] resampledData = Resample(sourceData, serverSampleRate, _outputSampleRate);

        foreach (var sample in resampledData)
        {
            _audioReceiveQueue.Enqueue(sample);
        }
    }

    private void OnAudioFilterRead(float[] data, int channels)
    {
        if (!IsListening) return;

        float sumAmplitude = 0f;
        int samplesCount = 0;

        for (int i = 0; i < data.Length; i += channels)
        {
            if (_audioReceiveQueue.TryDequeue(out float sample))
            {
                for (int c = 0; c < channels; c++) 
                {
                    data[i + c] = sample;
                }
                sumAmplitude += Mathf.Abs(sample);
                samplesCount++;
            }
            else
            {
                for (int c = 0; c < channels; c++) data[i + c] = 0;
                if (IsAiSpeaking) IsAiSpeaking = false;
            }
        }

        if (samplesCount > 0)
        {
            float instantVolume = sumAmplitude / samplesCount;
            CurrentVolume = instantVolume; 
        }
        else
        {
            CurrentVolume = 0f;
        }
    }
}