using UnityEngine;
using UnityEngine.UI; 

/// <summary>
/// Автоматически добавляет звук клика к любой кнопке, 
/// на которую повешен этот компонент.
/// </summary>
[RequireComponent(typeof(Button))]
public class ButtonClickSound : MonoBehaviour
{
    [Header("Настройки Звука")]
    
    [Tooltip("ID звука из GlobalSoundManager, который нужно проиграть")]
    [SerializeField]
    private int _soundIndex = 0; // 0 - звук клика

    [Tooltip("Если true, звук не будет играться, если кнопка неактивна (Not Interactable)")]
    [SerializeField]
    private bool _checkInteractable = true;

    private Button _button;

    private void Awake()
    {
        _button = GetComponent<Button>();
        _button.onClick.AddListener(PlaySound);
    }

    private void PlaySound()
    {
        if (_checkInteractable && !_button.interactable)
        {
            return;
        }

        GlobalSoundManager.Instance?.PlaySound(_soundIndex);
    }
    
    private void OnDestroy()
    {
        if (_button != null)
        {
            _button.onClick.RemoveListener(PlaySound);
        }
    }
}