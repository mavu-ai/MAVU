using System.Collections; // Для корутин
using Scripts;
using UnityEngine;
using UnityEngine.Audio;

public class GlobalSoundManager : Singleton<GlobalSoundManager>
{
    [SerializeField] private AudioSource[] audioSources;

    private bool _isMuted = false;

    private void Start()
    {
        StartCoroutine(TemporaryMuteOnStart(1.0f));
    }

    private IEnumerator TemporaryMuteOnStart(float duration)
    {
        foreach (var source in audioSources)
        {
            source.mute = true;
        }

        yield return new WaitForSeconds(duration);
        
        foreach (var source in audioSources)
        {
            source.mute = false;
        }
    }

    public void PlaySound(int soundIndex)
    {
        if (_isMuted) return;

        if (soundIndex < 0 || soundIndex >= audioSources.Length)
        {
            Debug.LogWarning($"[GlobalSoundManager] Попытка проиграть несуществующий звук: {soundIndex}");
            return;
        }

        audioSources[soundIndex].Play();
    }

    
    public void ToggleUISounds(bool isMuted)
    {
        _isMuted = isMuted;
    }

    public void MuteUISounds()
    {
        _isMuted = true;
    }

    public void UnmuteUISounds()
    {
        _isMuted = false;
    }
    
    public static void MuteMasterSound()
    {
        AudioListener.pause = true;
    }
    
    public static void UnmuteMasterSound()
    {
        AudioListener.pause = false;
    }
    
    public static void ToggleMasterSound()
    {
        AudioListener.pause = !AudioListener.pause;
    }
}