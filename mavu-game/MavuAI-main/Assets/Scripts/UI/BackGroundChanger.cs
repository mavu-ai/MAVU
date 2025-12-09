using UnityEngine;
using System.Collections;
using System.Collections.Generic;
using UnityEngine.UI;
using TMPro;
using UnityEngine.Localization;
using UnityEngine.Localization.Settings;
using UnityEngine.ResourceManagement.AsyncOperations;

// +++ НОВЫЙ КЛАСС для хранения 4-х вариаций фона +++
[System.Serializable]
public class TimeOfDaySprites
{
    public Sprite dawn;   // Рассвет
    public Sprite day;    // День
    public Sprite sunset; // Закат
    public Sprite night;  // Ночь
}

// <<< ИЗМЕНЕНО: BackGroundEntry теперь хранит 4 спрайта >>>
[System.Serializable]
public class BackGroundEntry
{
    [Tooltip("Название для удобства в редакторе")]
    [SerializeField] private string editorName;
    [SerializeField] private LocalizedString entryName;
    [SerializeField] private LocalizedString description;

    [Tooltip("4 вариации фона для разного времени суток")]
    [SerializeField] private TimeOfDaySprites backgroundVariations;
    
    public LocalizedString EntryName => entryName;
    public LocalizedString Description => description;
    public TimeOfDaySprites BackgroundVariations => backgroundVariations;
}


public class BackGroundChanger : MonoBehaviour
{
    private enum TimeOfDayPeriod { Dawn, Day, Sunset, Night }

    [Header("База данных фонов")]
    [SerializeField] private List<BackGroundEntry> backGrounds;

    [Header("UI Элементы для связи")]
    [SerializeField] private Image uiBackGroundImage;
    [SerializeField] private Image uiFadeImage;
    [SerializeField] private TextMeshProUGUI uiName;
    [SerializeField] private TextMeshProUGUI uiDescription;
    [SerializeField] private TextMeshProUGUI uiCount;
    [SerializeField] private GameObject uiSelectedButton, uiSelectButton;
    
    
    [Header("Настройки Локализации")]
    [SerializeField] private LocalizedString counterFormat;

    [Header("Настройки времени суток и переходов")]
    [Tooltip("Длительность плавного перехода между фонами в секундах")]
    [SerializeField] private float fadeDuration = 1.0f;
    [Tooltip("С какого часа начинается 'Рассвет' (0-23)")]
    [SerializeField] [Range(0, 23)] private int dawnStartTime = 5;
    [Tooltip("С какого часа начинается 'День' (0-23)")]
    [SerializeField] [Range(0, 23)] private int dayStartTime = 10;
    [Tooltip("С какого часа начинается 'Закат' (0-23)")]
    [SerializeField] [Range(0, 23)] private int sunsetStartTime = 18;
    [Tooltip("С какого часа начинается 'Ночь' (0-23)")]
    [SerializeField] [Range(0, 23)] private int nightStartTime = 22;


    private int _currentBackGroundIndex;
    private int _lastSelectedBackGroundIndex;
    private TimeOfDayPeriod _currentTimePeriod;
    private Coroutine _fadeCoroutine;

    private AsyncOperationHandle<string> _nameHandle;
    private AsyncOperationHandle<string> _descriptionHandle;
    private AsyncOperationHandle<string> _countHandle;
    private Sprite _currentTargetSprite;

    private void OnEnable()
    {
        LocalizationSettings.SelectedLocaleChanged += OnLocaleChanged;
    }

    private void OnDisable()
    {
        LocalizationSettings.SelectedLocaleChanged -= OnLocaleChanged;
    }

    IEnumerator Start()
    {
        // Прячем верхнее изображение в самом начале
        if (uiFadeImage != null)
        {
            uiFadeImage.color = new Color(1, 1, 1, 0);
        }

        if (backGrounds != null && backGrounds.Count > 0)
        {
            _lastSelectedBackGroundIndex = 0;
            // Устанавливаем фон в первый раз без анимации
            _currentTimePeriod = GetCurrentTimePeriod();
            uiBackGroundImage.sprite = GetCurrentSprite();
            ChangeCurrentBackGround(0);
        }
        else
        {
            Debug.LogError("Список фонов пуст! Нечего отображать.");
        }

        // Запускаем бесконечный цикл проверки времени
        while (true)
        {
            CheckTimeOfDay();
            // Проверяем время каждые 5 минут (300 секунд)
            yield return new WaitForSeconds(300); 
        }
    }
    
    private void OnLocaleChanged(Locale locale)
    {
        UpdateLocalizedText();
    }

    public void ChangeCurrentBackGround(int id)
    {
        if (backGrounds.Count == 0 || id < 0 || id >= backGrounds.Count) return;

        _currentBackGroundIndex = id;
        UpdateBackgroundDisplay();
        UpdateSelectButtonState();
        GlobalSoundManager.Instance?.PlaySound(2);
    }
    
    private void CheckTimeOfDay()
    {
        TimeOfDayPeriod newPeriod = GetCurrentTimePeriod();

        // Если период изменился, обновляем фон
        if (newPeriod != _currentTimePeriod)
        {
            _currentTimePeriod = newPeriod;
            UpdateBackgroundDisplay();
        }
    }

    private TimeOfDayPeriod GetCurrentTimePeriod()
    {
        int currentHour = System.DateTime.Now.Hour;
        
        if (currentHour >= nightStartTime || currentHour < dawnStartTime) return TimeOfDayPeriod.Night;
        if (currentHour >= sunsetStartTime) return TimeOfDayPeriod.Sunset;
        if (currentHour >= dayStartTime) return TimeOfDayPeriod.Day;
        return TimeOfDayPeriod.Dawn;
    }

    private Sprite GetCurrentSprite()
    {
        if (backGrounds.Count == 0) return null;
        
        BackGroundEntry currentEntry = backGrounds[_currentBackGroundIndex];
        switch (_currentTimePeriod)
        {
            case TimeOfDayPeriod.Dawn:   return currentEntry.BackgroundVariations.dawn;
            case TimeOfDayPeriod.Day:    return currentEntry.BackgroundVariations.day;
            case TimeOfDayPeriod.Sunset: return currentEntry.BackgroundVariations.sunset;
            case TimeOfDayPeriod.Night:  return currentEntry.BackgroundVariations.night;
            default:                     return currentEntry.BackgroundVariations.day;
        }
    }

    private void UpdateBackgroundDisplay()
    {
        if (backGrounds.Count == 0) return;

        Sprite spriteToSet = GetCurrentSprite();
    
        if (spriteToSet != null && _currentTargetSprite != spriteToSet)
        {
            if (_fadeCoroutine != null) StopCoroutine(_fadeCoroutine);
        
            _currentTargetSprite = spriteToSet; 
        
            _fadeCoroutine = StartCoroutine(CrossFadeToSprite(spriteToSet));
        }
    
        UpdateLocalizedText();
    }
    
    private IEnumerator CrossFadeToSprite(Sprite newSprite)
    {
        uiFadeImage.sprite = newSprite;
        
        float timer = 0f;
        while (timer < fadeDuration)
        {
            float alpha = Mathf.Lerp(0, 1, timer / fadeDuration);
            uiFadeImage.color = new Color(1, 1, 1, alpha);
            timer += Time.deltaTime;
            yield return null;
        }
        
        uiBackGroundImage.sprite = newSprite;
        uiFadeImage.color = new Color(1, 1, 1, 0);
    }

    private void UpdateLocalizedText()
    {
        if (backGrounds.Count == 0 || _currentBackGroundIndex >= backGrounds.Count) return;

        BackGroundEntry currentEntry = backGrounds[_currentBackGroundIndex];

        if (uiName != null)
        {
            _nameHandle = currentEntry.EntryName.GetLocalizedStringAsync();
            if (_nameHandle.IsDone)
                uiName.text = _nameHandle.Result;
            else
                _nameHandle.Completed += (handle) => uiName.text = handle.Result;
        }

        if (uiDescription != null)
        {
            _descriptionHandle = currentEntry.Description.GetLocalizedStringAsync();
            if (_descriptionHandle.IsDone)
                uiDescription.text = _descriptionHandle.Result;
            else
                _descriptionHandle.Completed += (handle) => uiDescription.text = handle.Result;
        }
        
        if (uiCount != null)
        {
            counterFormat.Arguments = new object[] { _currentBackGroundIndex + 1, backGrounds.Count };
            _countHandle = counterFormat.GetLocalizedStringAsync();
            if (_countHandle.IsDone)
                uiCount.text = _countHandle.Result;
            else
                _countHandle.Completed += (handle) => uiCount.text = handle.Result;
        }
    }
    
    public void SelectCurrentBackGround()
    {
        _lastSelectedBackGroundIndex = _currentBackGroundIndex;
        UpdateSelectButtonState();
        GlobalSoundManager.Instance?.PlaySound(1);
    }

    private void UpdateSelectButtonState()
    {
        if (_lastSelectedBackGroundIndex == _currentBackGroundIndex)
        {
            uiSelectButton.SetActive(false);
            uiSelectedButton.SetActive(true);
        }
        else
        {
            uiSelectButton.SetActive(true);
            uiSelectedButton.SetActive(false);
        }
    }

    public void SetNextBackGround()
    {
        int nextIndex = (_currentBackGroundIndex + 1) % backGrounds.Count;
        ChangeCurrentBackGround(nextIndex);
    }

    public void SetPreviousBackGround()
    {
        int total = backGrounds.Count;
        int previousIndex = (_currentBackGroundIndex - 1 + total) % total;
        ChangeCurrentBackGround(previousIndex);
    }

    public void TryChangeToLast()
    {
        if (_currentBackGroundIndex != _lastSelectedBackGroundIndex)
        {
            ChangeCurrentBackGround(_lastSelectedBackGroundIndex);
        }
    }
}