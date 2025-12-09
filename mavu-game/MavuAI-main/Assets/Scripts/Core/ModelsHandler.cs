using System;
using UnityEngine;
using System.Collections.Generic;
using System.Linq;
using Scripts.Customize;
using TMPro;
using UnityEngine.Audio;
using UnityEngine.UI;
using UnityEngine.Localization;
using UnityEngine.Localization.Settings;
using UnityEngine.ResourceManagement.AsyncOperations;
using UnityEngine.Serialization;

// Если эти пространства имен не используются, их можно удалить.
// using Core2; 
// using Scripts.Customize; 

// Класс EmotionData можно оставить здесь или вынести в отдельный файл, если он используется где-то еще.
[System.Serializable]
public class EmotionData
{
    [SerializeField] private AnimationClip animationClip;
    [SerializeField] private int emotionID;
    [SerializeField] private Button emotePlayButton; // Это поле может быть уже не нужно, если кнопки общие
    public AnimationClip AnimationClip => animationClip;
    public int EmotionID => emotionID;
}

public class ModelsHandler : MonoBehaviour
{
    [Header("База данных персонажей")]
    [Tooltip("Перетащи сюда ассеты CharacterProfile")]
    [SerializeField] private List<CharacterProfile> characterProfiles;

    // --- НОВОЕ ПОЛЕ ---
    [Header("Кастомизация")]
    [Tooltip("Перетащи сюда ассет CustomizationDatabase")]
    [SerializeField] private CustomizationDatabase customizationDatabase;
    // ------------------

    [Header("UI Элементы")]
    [SerializeField] private TextMeshProUGUI uiName;
    [SerializeField] private TextMeshProUGUI uiDescription;
    [SerializeField] private TextMeshProUGUI uiCount;
    [SerializeField] private GameObject uiSelectedButton, uiSelectButton;

    [Header("Настройки Локализации")]
    [SerializeField] private LocalizedString characterCountFormat;

    [Header("Настройки Аудио")]
    [SerializeField] private AudioMixer mainMixer;
    [SerializeField] private string pitchParameterName = "VoicePitch";

    [Header("Прочие ссылки")]

    private GameObject _currentModelInstance;
    private CharacterProfile _currentCharacter;
    private ManualAnimationPlayer _currentManualAnimationPlayer;
    private int _currentCharacterIndex;
    private int _lastSelectedCharacterIndex;

    private AsyncOperationHandle<string> _nameHandle;
    private AsyncOperationHandle<string> _descriptionHandle;
    private AsyncOperationHandle<string> _countHandle;
    private ChatService _chatService;

    private void OnEnable()
    {
        LocalizationSettings.SelectedLocaleChanged += OnLocaleChanged;
    }

    private void OnDisable()
    {
        LocalizationSettings.SelectedLocaleChanged -= OnLocaleChanged;
    }

    private void Awake()
    {
        _chatService = ChatService.Instance;
    }

    void Start()
    {
        if (characterProfiles != null && characterProfiles.Count > 0)
        {
            _lastSelectedCharacterIndex = PlayerPrefs.GetInt("LastSelectedCharacter", 0);
            ChangeCurrentModel(_lastSelectedCharacterIndex);
        }
    }

    public void ChangeCurrentModel(int id)
    {
        if (_currentModelInstance != null)
        {
            Destroy(_currentModelInstance);
        }
        GlobalSoundManager.Instance?.PlaySound(2);
        
        _currentCharacterIndex = id;
        _currentCharacter = characterProfiles[_currentCharacterIndex];

        _currentModelInstance = Instantiate(_currentCharacter.characterPrefab, transform);
        _currentModelInstance.SetActive(false);

        var customizer = _currentModelInstance.GetComponent<AvatarCustomizer>();
        if (customizer != null)
        {
            if (customizationDatabase == null)
            {
                Debug.LogError("CustomizationDatabase не назначена в инспекторе ModelsHandler!", this);
            }
            else
            {
                customizer.ApplyAppearance(_currentCharacter.defaultAppearance, customizationDatabase);
            }
        }
        else
        {
            Debug.LogWarning($"На префабе {_currentCharacter.characterPrefab.name} отсутствует компонент AvatarCustomizer!");
        }
        _currentModelInstance.SetActive(true);

        PrefabLinksSetter.Instance.InitPrefab(_currentModelInstance); 
        _chatService.SetCurrentCharacter(_currentCharacter.characterId);
        mainMixer.SetFloat(pitchParameterName, _currentCharacter.voicePitch);
        _currentManualAnimationPlayer = _currentModelInstance.GetComponent<ManualAnimationPlayer>();

        SetButtons();
        if (_currentManualAnimationPlayer != null) _currentManualAnimationPlayer.PlayIdle();

        UpdateLocalizedUI();
        ChangeButtonSelect();
    }
    
    public void CycleClothingColor()
    {
        if (_currentCharacter == null)
        {
            Debug.LogError("Профиль персонажа не выбран!");
            return;
        }

        var colorSetting = _currentCharacter.defaultAppearance.parameterSettings.FirstOrDefault(s => s.parameterId == "ParamCostumeColor3");

        if (colorSetting == null)
        {
            colorSetting = new ParameterSetting { parameterId = "ParamCostumeColor3", value = 0f };
            _currentCharacter.defaultAppearance.parameterSettings.Add(colorSetting);
        }

        float newValue = colorSetting.value + 0.05f;
        if (newValue >= 1.0f)
        {
            newValue = 0f;
        }

        colorSetting.value = newValue;
        Debug.Log($"Новое значение цвета в профиле: {newValue}");

        ChangeCurrentModel(_currentCharacterIndex);
    }

    public void SetParameterOption(string slotId, string optionId)
    {
        if (_currentCharacter == null) return;

        var currentSetting = _currentCharacter.defaultAppearance.selectedParameterSettings
            .FirstOrDefault(s => s.slotId == slotId);

        if (currentSetting == null)
        {
            currentSetting = new SelectedParameterSetting { slotId = slotId };
            _currentCharacter.defaultAppearance.selectedParameterSettings.Add(currentSetting);
        }
        currentSetting.selectedOptionId = optionId;
        Debug.Log($"Установлена опция параметра '{optionId}' для слота '{slotId}'");
        ChangeCurrentModel(_currentCharacterIndex);
    }
    public CharacterProfile GetCurrentCharacterProfile()
    {
        return _currentCharacter;
    }

    /// <summary>
    /// Переключает текстуру на следующую доступную в базе данных.
    /// Идеально для одной кнопки "Следующий цвет".
    /// </summary>
    /// <param name="textureToChange">Оригинальное имя текстуры, например, "texture_00"</param>
    public void CycleTextureOption(string textureToChange)
    {
        if (_currentCharacter == null || customizationDatabase == null) return;

        var slot = customizationDatabase.textureSlots.FirstOrDefault(s => s.originalTextureName == textureToChange);
        if (slot == null || slot.options.Count == 0)
        {
            Debug.LogWarning($"Слот {textureToChange} не найден в базе или в нем нет опций.");
            return;
        }
        var availableOptions = slot.options;

        var currentSetting = _currentCharacter.defaultAppearance.textureSettings.FirstOrDefault(s => s.originalTextureName == textureToChange);

        if (currentSetting == null)
        {
            currentSetting = new SelectedTextureSetting { originalTextureName = textureToChange, selectedOptionId = availableOptions[0].optionId };
            _currentCharacter.defaultAppearance.textureSettings.Add(currentSetting);
        }

        int currentIndex = availableOptions.FindIndex(o => o.optionId == currentSetting.selectedOptionId);
        if (currentIndex == -1) { currentIndex = 0; }

        int nextIndex = (currentIndex + 1) % availableOptions.Count;

        currentSetting.selectedOptionId = availableOptions[nextIndex].optionId;
        Debug.Log($"Новая опция для {textureToChange}: {currentSetting.selectedOptionId}");

        ChangeCurrentModel(_currentCharacterIndex);
    }

    /// <summary>
    /// Устанавливает конкретную текстуру по ее ID.
    /// </summary>
    /// <param name="textureToChange">Оригинальное имя текстуры, например, "texture_01"</param>
    /// <param name="optionId">ID опции, который задается в базе, например, "blue"</param>
    public void SetTextureOption(string textureToChange, string optionId)
    {
        if (_currentCharacter == null) return;

        var currentSetting = _currentCharacter.defaultAppearance.textureSettings.FirstOrDefault(s => s.originalTextureName == textureToChange);

        if (currentSetting == null)
        {
            currentSetting = new SelectedTextureSetting { originalTextureName = textureToChange };
            _currentCharacter.defaultAppearance.textureSettings.Add(currentSetting);
        }

        currentSetting.selectedOptionId = optionId;
        Debug.Log($"Установлена опция '{optionId}' для '{textureToChange}'");

        ChangeCurrentModel(_currentCharacterIndex);
    }
    
    
    private void OnLocaleChanged(Locale newLocale)
    {
        UpdateLocalizedUI();
    }

    private void UpdateLocalizedUI()
    {
        if (_currentCharacter == null) return;

        _nameHandle = _currentCharacter.entryName.GetLocalizedStringAsync();
        _nameHandle.Completed += (handle) => uiName.text = handle.Result;

        _descriptionHandle = _currentCharacter.description.GetLocalizedStringAsync();
        _descriptionHandle.Completed += (handle) => uiDescription.text = handle.Result;

        characterCountFormat.Arguments = new object[] { _currentCharacterIndex + 1, characterProfiles.Count };
        _countHandle = characterCountFormat.GetLocalizedStringAsync();
        _countHandle.Completed += (handle) => uiCount.text = handle.Result;
    }

    private void SetButtons()
    {
        if (_currentCharacter.emotions.Count < 3)
        {
            Debug.LogWarning($"У персонажа '{_currentCharacter.name}' меньше 3 эмоций. Кнопки могут работать некорректно.");
            return;
        }

        var links = PrefabLinksSetter.Instance;


        links.bodyClick.onClick.RemoveAllListeners();

        links.bodyClick.onClick.AddListener(() => _currentManualAnimationPlayer.PlayActionThenIdle(_currentCharacter.emotions[0].AnimationClip, _currentCharacter.emotions[0].EmotionID));


        links.faceClick.onClick.RemoveAllListeners();

        links.faceClick.onClick.AddListener(() => _currentManualAnimationPlayer.PlayActionThenIdle(_currentCharacter.emotions[1].AnimationClip, _currentCharacter.emotions[1].EmotionID));


        links.hatClick.onClick.RemoveAllListeners();

        links.hatClick.onClick.AddListener(() => _currentManualAnimationPlayer.PlayActionThenIdle(_currentCharacter.emotions[2].AnimationClip, _currentCharacter.emotions[2].EmotionID));
    }
    
    public void ModelSelect()
    {
        _lastSelectedCharacterIndex = _currentCharacterIndex;
        PlayerPrefs.SetInt("LastSelectedCharacter", _lastSelectedCharacterIndex);
        PlayerPrefs.Save();

        uiSelectButton.SetActive(false);
        uiSelectedButton.SetActive(true);
        GlobalSoundManager.Instance?.PlaySound(1);
    }

    private void ChangeButtonSelect()
    {
        uiSelectButton.SetActive(_lastSelectedCharacterIndex != _currentCharacterIndex);
        uiSelectedButton.SetActive(_lastSelectedCharacterIndex == _currentCharacterIndex);
    }
    
    public void SetNextModel()
    {
        int nextCharacterIndex = (_currentCharacterIndex + 1) % characterProfiles.Count;
        ChangeCurrentModel(nextCharacterIndex);
    }
    
    public void SetPreviousModel()
    {
        int total = characterProfiles.Count;
        int previousCharacterIndex = (_currentCharacterIndex - 1 + total) % total;
        ChangeCurrentModel(previousCharacterIndex);
    }
    
    public void TryChangeToLast()
    {
        if (_currentCharacterIndex != _lastSelectedCharacterIndex)
        {
            ChangeCurrentModel(_lastSelectedCharacterIndex);
            GlobalSoundManager.Instance?.PlaySound(2);
        }
    }
}