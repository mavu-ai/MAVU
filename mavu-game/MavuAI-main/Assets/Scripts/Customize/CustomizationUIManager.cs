using UnityEngine;
using System.Collections; // Нужно для корутин
using System.Collections.Generic;
using System.Linq;

public class CustomizationUIManager : MonoBehaviour
{
    [Header("Ссылки на основные объекты")]
    [SerializeField] private ModelsHandler modelsHandler;
    [SerializeField] private CustomizationDatabase customizationDatabase;

    [Header("Настройки анимации аватара (Lerp)")]
    [SerializeField] private Transform avatarTransform;
    [SerializeField] private Vector3 avatarHiddenPos;
    [SerializeField] private Vector3 avatarShownPos;
    [SerializeField] private float moveSpeed = 5f;

    [Header("Настройки UI")]
    [SerializeField] private GameObject customizationPanel;
    [SerializeField] private RectTransform optionsContent;
    [SerializeField] private GameObject colorOptionButtonPrefab;

    [Header("Кнопки категорий и их обводки")]
    [SerializeField] private GameObject hairButtonOutline;
    [SerializeField] private GameObject eyesButtonOutline;
    [SerializeField] private GameObject clothingButtonOutline;
    [SerializeField] private GameObject accessoryButtonOutline;

    // --- Приватные поля для отслеживания состояния ---
    private string _currentTextureCategory = "";
    private string _currentParameterCategory = "";
    private Coroutine _moveCoroutine;

    void Start()
    {
        // При старте запоминаем начальную позицию, если она не задана вручную
        if (avatarHiddenPos == Vector3.zero && avatarTransform != null)
        {
            avatarHiddenPos = avatarTransform.localPosition;
        }
    }

    /// <summary>
    /// Открывает или закрывает всю панель кастомизации.
    /// </summary>
    public void ToggleCustomizationPanel(bool show)
    {
        customizationPanel.SetActive(show);
        Vector3 targetPos = show ? avatarShownPos : avatarHiddenPos;
        if (_moveCoroutine != null) StopCoroutine(_moveCoroutine);
        _moveCoroutine = StartCoroutine(MoveAvatar(targetPos));

        if (show)
        {
            // При открытии по умолчанию показываем волосы
            OpenTextureCategory("texture_00"); 
        }
    }

    /// <summary>
    /// Генерирует кнопки для категорий, использующих ТЕКСТУРЫ (волосы, глаза).
    /// </summary>
    public void OpenTextureCategory(string textureToChange)
    {
        _currentTextureCategory = textureToChange;
        _currentParameterCategory = ""; // Сбрасываем выбор другой категории
        UpdateCategorySelectionUI();
        ClearOptionButtons();

        var slot = customizationDatabase.textureSlots.FirstOrDefault(s => s.originalTextureName == textureToChange);
        if (slot == null) return;

        var currentProfile = modelsHandler.GetCurrentCharacterProfile();
        var currentSetting = currentProfile.defaultAppearance.textureSettings
                             .FirstOrDefault(s => s.originalTextureName == textureToChange);
        string currentOptionId = currentSetting?.selectedOptionId;

        foreach (var option in slot.options)
        {
            GameObject buttonGO = Instantiate(colorOptionButtonPrefab, optionsContent);
            var buttonScript = buttonGO.GetComponent<ColorOptionButton>();
            buttonScript.Setup(option, textureToChange, OnTextureOptionSelected); // Передаем обработчик для текстур
            buttonScript.SetSelected(option.optionId == currentOptionId);
        }
    }

    /// <summary>
    /// Генерирует кнопки для категорий, использующих ПАРАМЕТРЫ (одежда, аксессуары).
    /// </summary>
    public void OpenParameterCategory(string slotId)
    {
        _currentParameterCategory = slotId;
        _currentTextureCategory = ""; // Сбрасываем выбор другой категории
        UpdateCategorySelectionUI();
        ClearOptionButtons();

        var slot = customizationDatabase.parameterSlots.FirstOrDefault(s => s.slotId == slotId);
        if (slot == null) return;

        var currentProfile = modelsHandler.GetCurrentCharacterProfile();
        var currentSetting = currentProfile.defaultAppearance.selectedParameterSettings
                             .FirstOrDefault(s => s.slotId == slotId);
        string currentOptionId = currentSetting?.selectedOptionId;

        foreach (var option in slot.options)
        {
            GameObject buttonGO = Instantiate(colorOptionButtonPrefab, optionsContent);
            var buttonScript = buttonGO.GetComponent<ColorOptionButton>();
            buttonScript.Setup(option, slotId, OnParameterOptionSelected); // Передаем обработчик для параметров
            buttonScript.SetSelected(option.optionId == currentOptionId);
        }
    }

    // --- Обработчики кликов по кнопкам опций ---
    private void OnTextureOptionSelected(string textureToChange, string optionId)
    {
        modelsHandler.SetTextureOption(textureToChange, optionId);
        Invoke(nameof(RefreshCurrentTextureCategory), 0.05f); // Вызываем правильный метод обновления
    }

    private void OnParameterOptionSelected(string slotId, string optionId)
    {
        modelsHandler.SetParameterOption(slotId, optionId);
        Invoke(nameof(RefreshCurrentParameterCategory), 0.05f); // Вызываем правильный метод обновления
    }
    
    // --- Вспомогательные методы ---
    private void ClearOptionButtons()
    {
        foreach (Transform child in optionsContent)
        {
            Destroy(child.gameObject);
        }
    }
    
    private void UpdateCategorySelectionUI()
    {
        // Обновляем все обводки разом, проверяя на null на всякий случай
        if(hairButtonOutline) hairButtonOutline.SetActive(_currentTextureCategory == "texture_00");
        if(eyesButtonOutline) eyesButtonOutline.SetActive(_currentTextureCategory == "texture_01");
        if(clothingButtonOutline) clothingButtonOutline.SetActive(_currentParameterCategory == "clothing_color");
        if(accessoryButtonOutline) accessoryButtonOutline.SetActive(_currentParameterCategory == "head_accessory");
    }

    // Методы для обновления UI после смены модели
    private void RefreshCurrentTextureCategory() => OpenTextureCategory(_currentTextureCategory);
    private void RefreshCurrentParameterCategory() => OpenParameterCategory(_currentParameterCategory);

    // Корутина для плавного движения аватара
    private IEnumerator MoveAvatar(Vector3 targetPosition)
    {
        while (Vector3.Distance(avatarTransform.localPosition, targetPosition) > 0.01f)
        {
            avatarTransform.localPosition = Vector3.Lerp(avatarTransform.localPosition, targetPosition, Time.deltaTime * moveSpeed);
            yield return null;
        }
        avatarTransform.localPosition = targetPosition;
    }
}