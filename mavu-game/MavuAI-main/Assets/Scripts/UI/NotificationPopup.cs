using UnityEngine;
using TMPro;
using DG.Tweening; 

[RequireComponent(typeof(CanvasGroup))]
public class NotificationPopup : MonoBehaviour
{
    [SerializeField] private TMP_Text notificationText;
    [SerializeField] private CanvasGroup canvasGroup;

    [Header("Настройки анимации")]
    [SerializeField] private float moveAmount = 150f;
    [SerializeField] private float moveDuration = 1.5f;
    [SerializeField] private float fadeOutDuration = 1.0f;
    [SerializeField] private Ease moveEase = Ease.OutQuad;

    private Sequence _animationSequence;
    private Vector3 _initialPosition;

    private void Awake()
    {
        _initialPosition = transform.localPosition;
        if (notificationText == null)
            notificationText = GetComponentInChildren<TMP_Text>();
        if (canvasGroup == null)
            canvasGroup = GetComponent<CanvasGroup>();
    }
    public void Show(string message)
    {
        _animationSequence?.Kill();
        gameObject.SetActive(true);
        notificationText.text = message;
        canvasGroup.alpha = 1f;
        transform.localPosition = _initialPosition;

        _animationSequence = DOTween.Sequence();
        
        _animationSequence.Append(
            transform.DOLocalMoveY(_initialPosition.y + moveAmount, moveDuration)
                .SetEase(moveEase)
        );
        
        float fadeStartTime = moveDuration - fadeOutDuration;
        _animationSequence.Insert(fadeStartTime,
            canvasGroup.DOFade(0f, fadeOutDuration)
        );

        _animationSequence.OnComplete(() =>
        {
            gameObject.SetActive(false);
        });

        _animationSequence.Play();
    }
}