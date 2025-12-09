using TMPro;
using UnityEngine;
using UnityEngine.UI;
using System.Text.RegularExpressions; 

[RequireComponent(typeof(TMP_InputField))]
public class FieldValidator : MonoBehaviour
{
    [Header("Целевые объекты")]
    [Tooltip("Кнопка, которую нужно активировать/деактивировать")]
    [SerializeField] private Button targetButton;
    [Tooltip("Текстовый компонент на кнопке (TextMeshPro)")]
    [SerializeField] private TextMeshProUGUI buttonText;

    [Header("Спрайты для кнопки")]
    [Tooltip("Спрайт для активного состояния кнопки")]
    [SerializeField] private Sprite activeSprite;
    [Tooltip("Спрайт для неактивного состояния кнопки")]
    [SerializeField] private Sprite inactiveSprite;
    
    // +++ НОВОЕ: Цвета для текста кнопки +++
    [Header("Цвета для текста кнопки")]
    [Tooltip("Цвет текста, когда кнопка активна")]
    [SerializeField] private Color activeTextColor = Color.white;
    [Tooltip("Цвет текста, когда кнопка неактивна")]
    [SerializeField] private Color inactiveTextColor = new Color(0.615f, 0.615f, 0.615f); // Это #9D9D9D

    private TMP_InputField _inputField;
    private Image _buttonImage;
    private const string EmailPattern = @"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$";

    private void Awake()
    {
        _inputField = GetComponent<TMP_InputField>();
        if (targetButton != null)
        {
            _buttonImage = targetButton.GetComponent<Image>();
        }
    }

    private void OnEnable()
    {
        _inputField.onValueChanged.AddListener(ValidateInput);
        ValidateInput(_inputField.text);
    }

    private void OnDisable()
    {
        _inputField.onValueChanged.RemoveListener(ValidateInput);
    }

    private void ValidateInput(string inputText)
    {
        if (targetButton == null) return;

        bool isValid = IsValidEmailFormat(inputText);

        targetButton.interactable = isValid;

        if (_buttonImage != null && activeSprite != null && inactiveSprite != null)
        {
            _buttonImage.sprite = isValid ? activeSprite : inactiveSprite;
        }

        if (buttonText != null)
        {
            buttonText.color = isValid ? activeTextColor : inactiveTextColor;
        }
    }

    private bool IsValidEmailFormat(string email)
    {
        if (string.IsNullOrEmpty(email))
            return false;
        
        return Regex.IsMatch(email, EmailPattern);
    }
}