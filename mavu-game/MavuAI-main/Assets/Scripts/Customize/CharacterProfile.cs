using UnityEngine;
using UnityEngine.Localization;
using System.Collections.Generic;

// --- Класс для хранения одной настройки параметра ---

[System.Serializable]
public class ParameterSetting
{
    public string parameterId;
    public float value;
}

// --- Класс для хранения полного набора настроек внешности ---

[System.Serializable]
public class SelectedTextureSetting
{
    public string originalTextureName; // "texture_00"
    public string selectedOptionId;   // "blue"
}
[System.Serializable]
public class SelectedParameterSetting
{
    public string slotId;           // Например: "clothing_color"
    public string selectedOptionId; // Например: "red_color"
}

// --- Обновленный класс внешности ---
[System.Serializable]
public class CharacterAppearanceData
{
    [Header("Настройки параметров модели")]
    public List<ParameterSetting> parameterSettings;

    [Header("Настройки параметров (новая система)")]
    public List<SelectedParameterSetting> selectedParameterSettings;
    
    [Header("Настройки текстур (перекраска)")]
    [Tooltip("Список ВЫБРАННЫХ вариантов текстур")]
    public List<SelectedTextureSetting> textureSettings; // Заменяем List<Texture2D> textureOverrides

    // Старое поле textureOverrides можно удалить или оставить для обратной совместимости,
    // но для новой системы оно не нужно.
}


// --- Основной класс "паспорта" персонажа ---
[CreateAssetMenu(fileName = "New Character Profile", menuName = "Characters/Character Profile")]
public class CharacterProfile : ScriptableObject
{
    [Header("Основная информация")]
    public LocalizedString entryName;
    public LocalizedString description;
    public int characterId;

    [Header("Модель и Анимации")]
    [Tooltip("Ссылка на ЕДИНЫЙ базовый префаб модели")]
    public GameObject characterPrefab; // Сюда всегда будет ставиться один и тот же префаб
    public List<EmotionData> emotions; // Твой класс EmotionData

    [Header("Настройки Голоса")]
    public string voiceNameRu, voiceNameEn;
    [Range(0.5f, 2.0f)]
    public float voicePitch = 1.0f;

    [Header("Настройки внешности по умолчанию")]
    [Tooltip("Уникальные черты этого персонажа")]
    public CharacterAppearanceData defaultAppearance;
}