using UnityEngine;
using UnityEngine.UI; // Для Image и Button

[RequireComponent(typeof(Button))]
[RequireComponent(typeof(Image))]
public class MusicToggleButton : MonoBehaviour
{
    [Header("Спрайты состояния")]
    [SerializeField] private Sprite _musicOnSprite;
    [SerializeField] private Sprite _musicOffSprite;
    private Button _button;
    private Image _buttonImage;

    private void Start()
    {
        _button = GetComponent<Button>();
        _buttonImage = GetComponent<Image>();
        _button.onClick.AddListener(OnButtonClick);
        MusicManager.Instance.onMusicStateChanged.AddListener(UpdateSprite);
        UpdateSprite(MusicManager.Instance.IsMusicMuted());
    }
    
    private void OnButtonClick()
    {
        MusicManager.Instance.ToggleMusic();
    }
    private void UpdateSprite(bool isMuted)
    {
        if (isMuted)
        {
            _buttonImage.sprite = _musicOffSprite;
        }
        else
        {
            _buttonImage.sprite = _musicOnSprite;
        }
    }
    private void OnDestroy()
    {
        if (_button != null)
        {
            _button.onClick.RemoveListener(OnButtonClick);
        }
    }
}