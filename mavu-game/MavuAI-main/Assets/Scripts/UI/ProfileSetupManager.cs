using TMPro;
using UnityEngine;
using UnityEngine.Serialization;
using UnityEngine.UI;

public class ProfileSetupManager : MonoBehaviour
{
    [Header("Поля для данных")]
    [SerializeField] private TMP_InputField nameInputField;
    [SerializeField] private AgeSelector ageSelector;
    [SerializeField] private GenderSelector genderSelector;

    [Header("Управление")]
    [SerializeField] private Button continueButton;
    [FormerlySerializedAs("authManager")] [SerializeField] private AppManager appManager;

    [Header("Окна для переключения")]
    [SerializeField] private GameObject profileSetupPanel;
    [SerializeField] private GameObject emailPanel;

    [Header("Внешний вид кнопки 'Продолжить'")]
    [SerializeField] private Sprite activeSprite;
    [SerializeField] private Sprite inactiveSprite;
    [SerializeField] private Color activeTextColor = Color.white;
    [SerializeField] private Color inactiveTextColor = new Color(0.5f, 0.5f, 0.5f);

    private Image _continueButtonImage;
    private TextMeshProUGUI _continueButtonText;

    private void Awake()
    {
        if (continueButton != null)
        {
            _continueButtonImage = continueButton.GetComponent<Image>();
            _continueButtonText = continueButton.GetComponentInChildren<TextMeshProUGUI>();
        }
    }

    private void Start()
    {
        nameInputField.onValueChanged.AddListener(delegate { ValidateInputs(); });
        continueButton.onClick.AddListener(OnContinuePressed);
        ValidateInputs();
    }
    
    public void ValidateInputs()
    {
        bool isNameValid = !string.IsNullOrWhiteSpace(nameInputField.text);
        bool isGenderSelected = genderSelector.SelectedGender != GenderSelector.Gender.None;
        bool isFormValid = isNameValid && isGenderSelected;
        continueButton.interactable = isFormValid;

        if (_continueButtonImage != null && _continueButtonText != null)
        {
            _continueButtonImage.sprite = isFormValid ? activeSprite : inactiveSprite;
            _continueButtonText.color = isFormValid ? activeTextColor : inactiveTextColor;
        }
    }
    
    private void OnContinuePressed()
    {
        string userName = nameInputField.text;
        int userAge = ageSelector.SelectedAge;
        GenderSelector.Gender userGender = genderSelector.SelectedGender;
        
        AuthService.Instance.SetProfileDataForRegistration(userName, userAge, userGender);
        
        if (profileSetupPanel != null) profileSetupPanel.SetActive(false);
        if (emailPanel != null) emailPanel.SetActive(true);
    }
}