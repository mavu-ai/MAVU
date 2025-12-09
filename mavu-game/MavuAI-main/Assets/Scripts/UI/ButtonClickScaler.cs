using UnityEngine;
using UnityEngine.EventSystems; // Для обработки нажатий
using DG.Tweening;            

public class ButtonClickScaler : MonoBehaviour, IPointerDownHandler, IPointerUpHandler, IPointerExitHandler
{
    [Header("Настройки Анимации")]
    
    [Tooltip("Во сколько раз уменьшить кнопку при нажатии (0.95 = на 5%)")]
    [SerializeField]
    private float _scaleFactor = 0.95f;

    [Tooltip("Скорость анимации в секундах (туда и обратно)")]
    [SerializeField]
    private float _duration = 0.1f;

    [Tooltip("Тип плавности. Ease.OutQuad обычно выглядит хорошо.")]
    [SerializeField]
    private Ease _easeType = Ease.OutQuad;

    private Vector3 _originalScale;
    private Tweener _currentTween;
    private bool _isPressed = false;

    private void Awake()
    {
        _originalScale = transform.localScale;
    }
    public void OnPointerDown(PointerEventData eventData)
    {
        _isPressed = true;
        _currentTween?.Kill();
        _currentTween = transform.DOScale(_originalScale * _scaleFactor, _duration)
                                 .SetEase(_easeType)
                                 .SetUpdate(true); 
    }
    
    public void OnPointerUp(PointerEventData eventData)
    {
        if (!_isPressed) return;
        _isPressed = false;
        _currentTween?.Kill();
        _currentTween = transform.DOScale(_originalScale, _duration)
                                 .SetEase(_easeType)
                                 .SetUpdate(true);
    }
    public void OnPointerExit(PointerEventData eventData)
    {
        if (_isPressed)
        {
            _isPressed = false;
            _currentTween?.Kill();
            _currentTween = transform.DOScale(_originalScale, _duration)
                                     .SetEase(_easeType)
                                     .SetUpdate(true);
        }
    }
    
    private void OnDestroy()
    {
        _currentTween?.Kill();
    }
}