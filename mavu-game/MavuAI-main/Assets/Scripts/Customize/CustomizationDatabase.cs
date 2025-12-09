using UnityEngine;
using System.Collections.Generic;
using System.Linq;

// --- Одна конкретная опция (например, "Синий цвет волос") ---
[System.Serializable]
public class TextureOption
{
    [Tooltip("Удобное имя для инспектора и для сохранения, например, 'blue' или 'green'")]
    public string optionId; // "blue", "green", "red"
    [Tooltip("Сама текстура для этого варианта")]
    public Texture2D texture;
    public Sprite icon;
}

// --- Один слот для кастомизации (например, "Цвет Волос") ---
[System.Serializable]
public class TextureSlot
{
    [Tooltip("Оригинальное имя текстуры, которую нужно заменить (texture_00, texture_01)")]
    public string originalTextureName; // "texture_00" для волос, "texture_01" для глаз
    [Tooltip("Список всех доступных вариантов для этого слота")]
    public List<TextureOption> options;
}

[System.Serializable]
public class ParameterOption
{
    [Tooltip("ID для сохранения и вызова из кода, например, 'red_shirt' или 'cat_ears_on'")]
    public string optionId;
    [Tooltip("Иконка для отображения в UI")]
    public Sprite icon;
    [Tooltip("Список параметров и их значений для этой опции. Можно менять несколько параметров одной кнопкой!")]
    public List<ParameterSetting> settings; // Используем твой уже существующий класс!
}

[System.Serializable]
public class ParameterSlot
{
    [Tooltip("Уникальный ID слота, например, 'clothing_color' или 'head_accessory'")]
    public string slotId;
    [Tooltip("Список всех доступных вариантов для этого слота")]
    public List<ParameterOption> options;
}


public class CustomizationDatabase : ScriptableObject
{
    public List<TextureSlot> textureSlots;

    // Удобный метод, чтобы быстро найти нужную текстуру
    public Texture2D GetTexture(string originalName, string optionId)
    {
        // Находим нужный слот (например, для "texture_00")
        var slot = textureSlots.FirstOrDefault(s => s.originalTextureName == originalName);
        if (slot == null) return null;

        // Внутри слота находим нужную опцию (например, "blue")
        var option = slot.options.FirstOrDefault(o => o.optionId == optionId);
        if (option == null) return null;

        return option.texture;
    }
    
    public List<ParameterSlot> parameterSlots; // <-- Наше главное нововведение

}