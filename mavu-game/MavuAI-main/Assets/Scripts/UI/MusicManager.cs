using Scripts;
using UnityEngine;
using UnityEngine.Events; 

public class MusicManager : Singleton<MusicManager>
{
    [SerializeField] private AudioSource musicSource;
    private const string MUSIC_MUTED_KEY = "MusicMuted";
    public UnityEvent<bool> onMusicStateChanged = new UnityEvent<bool>();

    private bool _isMuted = false;
    
    private void Awake()
    {
        _isMuted = PlayerPrefs.GetInt(MUSIC_MUTED_KEY, 0) == 1;
        musicSource.mute = _isMuted;
        
        if (!musicSource.playOnAwake)
        {
            musicSource.Play();
        }
    }

    /// <summary>
    /// Переключает состояние музыки (Вкл/Выкл)
    /// </summary>
    public void ToggleMusic()
    {
        _isMuted = !_isMuted;
        musicSource.mute = _isMuted;
        PlayerPrefs.SetInt(MUSIC_MUTED_KEY, _isMuted ? 1 : 0);
        PlayerPrefs.Save();
        onMusicStateChanged?.Invoke(_isMuted);
    }
    
    public bool IsMusicMuted()
    {
        return _isMuted;
    }
}