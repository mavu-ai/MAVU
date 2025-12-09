using System;
using Scripts;
using UnityEngine;
using UnityEngine.Localization.Settings;

public class LanguageManager : Singleton<LanguageManager>
{ 
    public static event Action<int> OnLanguageChanged;

    public void ChangeLocale(int localeID)
    {
        if (localeID >= 0 && localeID < LocalizationSettings.AvailableLocales.Locales.Count)
        {
            LocalizationSettings.SelectedLocale = LocalizationSettings.AvailableLocales.Locales[localeID];
            OnLanguageChanged?.Invoke(localeID);
            Debug.Log($"Language changed to: {LocalizationSettings.SelectedLocale.LocaleName}");
        }
    }
}