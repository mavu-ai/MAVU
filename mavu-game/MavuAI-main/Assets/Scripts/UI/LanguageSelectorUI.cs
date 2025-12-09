using UnityEngine;
using UnityEngine.Localization.Settings;
using UnityEngine.UI;

public class LanguageSelectorUI : MonoBehaviour
{
    [Header("Настройки языка этой кнопки")]
    [SerializeField] private int localeID;

    [Header("Визуальные состояния")]
    [SerializeField] private GameObject selectedStateObject;
    [SerializeField] private GameObject deselectedStateObject;

    private void Awake()
    {
        if (deselectedStateObject != null)
        {
            Button buttonToClick = deselectedStateObject.GetComponent<Button>();
            if (buttonToClick != null)
            {
                buttonToClick.onClick.AddListener(SelectLanguage);
            }
            else
            {
                Debug.LogError("На объекте deselectedStateObject не найден компонент Button!", this);
            }
        }
        else
        {
            Debug.LogError("Объект deselectedStateObject не назначен в инспекторе!", this);
        }
    }

    private void OnEnable()
    {
        LanguageManager.OnLanguageChanged += UpdateVisuals;
        UpdateVisuals(0);
    }

    private void OnDisable()
    {
        LanguageManager.OnLanguageChanged -= UpdateVisuals;
    }
    
    private void SelectLanguage()
    {
        LanguageManager.Instance.ChangeLocale(localeID);
    }
    
    private void UpdateVisuals(int newLocaleID)
    {
        bool isSelected = (LocalizationSettings.AvailableLocales.Locales[localeID] == LocalizationSettings.SelectedLocale);
        
        if (selectedStateObject != null) selectedStateObject.SetActive(isSelected);
        if (deselectedStateObject != null) deselectedStateObject.SetActive(!isSelected);
    }
}