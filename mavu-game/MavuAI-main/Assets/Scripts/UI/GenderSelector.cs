using System.Collections;
using UnityEngine;
using UnityEngine.UI;
using TMPro;
using UnityEngine.Events;

public class GenderSelector : MonoBehaviour
{
    public enum Gender { None, Boy, Girl }
    public UnityEvent OnGenderSelected;

    [Header("Кнопки и Текст")]
    [SerializeField] private Button boyButton;
    [SerializeField] private Button girlButton;
    [SerializeField] private TextMeshProUGUI boyButtonText;
    [SerializeField] private TextMeshProUGUI girlButtonText;

    [Header("Настройки Анимации")]
    [Tooltip("Длительность плавной смены цвета в секундах")]
    [SerializeField] private float transitionDuration = 0.2f;

    [Header("Цвета для Фона Кнопок")]
    [SerializeField] private Color boySelectedColor = new Color(0.2f, 0.6f, 1f);
    [SerializeField] private Color girlSelectedColor = new Color(1f, 0.4f, 0.7f);
    [SerializeField] private Color defaultColor = Color.white;
    
    [Header("Цвета для Текста")]
    [SerializeField] private Color selectedTextColor = Color.white;
    [SerializeField] private Color defaultTextColor = Color.black;

    public Gender SelectedGender { get; private set; }

    private Image _boyButtonImage;
    private Image _girlButtonImage;

    // Ссылки на запущенные корутины, чтобы их можно было остановить
    private Coroutine _boyAnimationCoroutine;
    private Coroutine _girlAnimationCoroutine;

    void Awake()
    {
        _boyButtonImage = boyButton.GetComponent<Image>();
        _girlButtonImage = girlButton.GetComponent<Image>();

        boyButton.onClick.AddListener(() => Select(Gender.Boy));
        girlButton.onClick.AddListener(() => Select(Gender.Girl));
    }

    void Start()
    {
        Select(Gender.None, true);
    }

    public void Select(Gender gender, bool instant = false)
    {
        if (SelectedGender == gender) return;

        SelectedGender = gender;
        OnGenderSelected?.Invoke();
        
        if (_boyAnimationCoroutine != null) StopCoroutine(_boyAnimationCoroutine);
        if (_girlAnimationCoroutine != null) StopCoroutine(_girlAnimationCoroutine);

        if (instant)
        {
            _boyButtonImage.color = (SelectedGender == Gender.Boy) ? boySelectedColor : defaultColor;
            _girlButtonImage.color = (SelectedGender == Gender.Girl) ? girlSelectedColor : defaultColor;
            boyButtonText.color = (SelectedGender == Gender.Boy) ? selectedTextColor : defaultTextColor;
            girlButtonText.color = (SelectedGender == Gender.Girl) ? selectedTextColor : defaultTextColor;
        }
        else
        {
            _boyAnimationCoroutine = StartCoroutine(AnimateColor(
                _boyButtonImage, boyButtonText,
                (SelectedGender == Gender.Boy) ? boySelectedColor : defaultColor,
                (SelectedGender == Gender.Boy) ? selectedTextColor : defaultTextColor
            ));

            _girlAnimationCoroutine = StartCoroutine(AnimateColor(
                _girlButtonImage, girlButtonText,
                (SelectedGender == Gender.Girl) ? girlSelectedColor : defaultColor,
                (SelectedGender == Gender.Girl) ? selectedTextColor : defaultTextColor
            ));
        }
    }
    
    private IEnumerator AnimateColor(Image targetImage, TextMeshProUGUI targetText, Color targetImageColor, Color targetTextColor)
    {
        float timer = 0f;
        
        Color startImageColor = targetImage.color;
        Color startTextColor = targetText.color;

        while (timer < transitionDuration)
        {
            float progress = timer / transitionDuration;

            targetImage.color = Color.Lerp(startImageColor, targetImageColor, progress);
            if (targetText != null)
            {
                targetText.color = Color.Lerp(startTextColor, targetTextColor, progress);
            }
            
            timer += Time.deltaTime;
            yield return null;
        }

        targetImage.color = targetImageColor;
        if (targetText != null)
        {
            targetText.color = targetTextColor;
        }
    }
}