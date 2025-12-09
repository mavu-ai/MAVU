using System;
using UnityEngine;
using Scripts;
using UnityEngine.Localization.Settings;


public class ChatService : Singleton<ChatService>
{
    [Header("Настройки привязки Email")]
    [Tooltip("Сколько сообщений должен отправить пользователь, прежде чем сможет привязать email")]
    [SerializeField] private int messageThresholdForEmailAttach = 0;

    private int _sentMessagesCount = 0;
    public event Action OnEmailAttachAvailable;
    
    [Header("Настройки API")]
    [Tooltip("Базовый URL вашего API.")]
    [SerializeField]
    private string baseUrl = "https://mavu-api.aey-inc.uz/api/v1";
    
    [Header("Настройки TTS")]
    public AudioSource ttsAudioSource;
    
    public int CurrentCharacterId { get; private set; }
    protected AppManager appManager;

    public void Init(AppManager _appManager)
    {
        appManager = _appManager;
        OnEmailAttachAvailable?.Invoke();
    }
    
    public void SetCurrentCharacter(int newId)
    {
        CurrentCharacterId = newId;
        Debug.Log($"[Connecter] Персонаж сменен. Новый ID: {CurrentCharacterId}");
    }
    
}