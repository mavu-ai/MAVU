using UnityEngine;

[RequireComponent(typeof(RectTransform))]
public class KeyboardAwarePanel : MonoBehaviour
{
    [Tooltip("Высота, на которую панель поднимется при появлении клавиатуры (в юнитах канваса). Подбирается вручную.")]
    [SerializeField] private float liftHeight = 450f;

    [Tooltip("Скорость, с которой панель будет двигаться.")]
    [SerializeField] private float smoothTime = 0.2f;

    private RectTransform _panelTransform;
    private Vector2 _originalPosition;
    
    private Vector2 _velocity = Vector2.zero;

    void OnEnable()
    {
        _panelTransform = GetComponent<RectTransform>();
        _originalPosition = _panelTransform.anchoredPosition;
    }

    void Update()
    {
        Vector2 targetPosition = _originalPosition + (TouchScreenKeyboard.visible ? new Vector2(0, liftHeight) : Vector2.zero);

        _panelTransform.anchoredPosition = Vector2.SmoothDamp(
            _panelTransform.anchoredPosition,
            targetPosition,
            ref _velocity,
            smoothTime
        );
    }
}