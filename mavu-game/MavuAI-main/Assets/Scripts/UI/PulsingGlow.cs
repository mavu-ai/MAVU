using UnityEngine;
using UnityEngine.UI; // Обязательно для работы с Image
using DG.Tweening;    

[RequireComponent(typeof(Image))]
public class PulsingGlow : MonoBehaviour
{
    [Header("Настройки Пульсации")]

    [Tooltip("Минимальная прозрачность (0 = полностью невидимый)")]
    [Range(0f, 1f)]
    [SerializeField]
    private float _minAlpha = 0.3f;

    [Tooltip("Максимальная прозрачность (1 = полностью видимый)")]
    [Range(0f, 1f)]
    [SerializeField]
    private float _maxAlpha = 1.0f;

    [Tooltip("Время на один цикл (от макс. до мин.) в секундах")]
    [SerializeField]
    private float _duration = 1.5f;

    [Tooltip("Тип плавности. Ease.InOutSine отлично подходит для 'дыхания'")]
    [SerializeField]
    private Ease _easeType = Ease.InOutSine;

    private Image _glowImage;
    private Tweener _fadeTween;

    private void Awake()
    {
        _glowImage = GetComponent<Image>();
    }

    private void Start()
    {
        Color startColor = _glowImage.color;
        startColor.a = _maxAlpha;
        _glowImage.color = startColor;

        StartPulsing();
    }

    private void StartPulsing()
    {
        _fadeTween?.Kill();

        _fadeTween = _glowImage.DOFade(_minAlpha, _duration)
            .SetEase(_easeType)
            .SetLoops(-1, LoopType.Yoyo)
            .SetUpdate(true); 
    }
    
    private void OnDestroy()
    {
        _fadeTween?.Kill();
    }
}