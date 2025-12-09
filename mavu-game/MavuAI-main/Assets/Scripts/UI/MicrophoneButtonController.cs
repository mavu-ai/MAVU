using UnityEngine;
using UnityEngine.UI;

[RequireComponent(typeof(Button))]
public class MicrophoneButtonController : MonoBehaviour
{
    [Header("Ссылки на компоненты")]
    [SerializeField] private MavuRealtimeService mavuService; 
    
    [Tooltip("Компонент Image этой кнопки для смены спрайта")]
    [SerializeField] private Image buttonImage;

    [Header("Спрайты состояний")]
    [SerializeField] private Sprite microphoneOnSprite;
    [SerializeField] private Sprite microphoneOffSprite;

    private Button _button;

    private void Awake()
    {
        _button = GetComponent<Button>();
        
        if (mavuService == null)
        {
            mavuService = FindObjectOfType<MavuRealtimeService>();
        }

        if (mavuService == null || buttonImage == null)
        {
            Debug.LogError("MavuService не найден или Image не привязан!", this);
            _button.interactable = false;
        }
    }

    private void Start()
    {
        _button.onClick.AddListener(OnButtonClicked);
        
        mavuService.Started.AddListener(SetMicOn);
        mavuService.Finished.AddListener(SetMicOff);
        
        if (mavuService.IsListening)
        {
            SetMicOn();
        }
        else
        {
            SetMicOff();
        }
    }

    private void OnButtonClicked()
    {
        mavuService.ToggleSession();
    }
    
    private void SetMicOn()
    {
        if(microphoneOnSprite != null) buttonImage.sprite = microphoneOnSprite;
    }

    private void SetMicOff()
    {
        if(microphoneOffSprite != null) buttonImage.sprite = microphoneOffSprite;
    }
}