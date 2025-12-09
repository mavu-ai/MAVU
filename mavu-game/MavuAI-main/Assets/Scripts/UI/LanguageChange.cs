using Scripts;
using UnityEngine;
using UnityEngine.Localization.Settings;

public class LanguageChange : Singleton<LanguageChange>
{
    [SerializeField] private GameObject changeToRuCurrent, changeToRu;
    [SerializeField] private GameObject changeToEnCurrent, changeToEn;

    private int _enId = 0;
    private int _ruId = 1;

    public void ChangeToRu()
    {
        changeToRuCurrent.SetActive(true);
        changeToRu.SetActive(false);
        changeToEnCurrent.SetActive(false);
        changeToEn.SetActive(true);
        LocalizationSettings.SelectedLocale = LocalizationSettings.AvailableLocales.Locales[_ruId];
    }

    public void ChangeToEn()
    {
        changeToEnCurrent.SetActive(true);
        changeToEn.SetActive(false);
        changeToRuCurrent.SetActive(false);
        changeToRu.SetActive(true);
        LocalizationSettings.SelectedLocale = LocalizationSettings.AvailableLocales.Locales[_enId];
    }
}
