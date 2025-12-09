using UnityEngine;
using Live2D.Cubism.Core;
using System.Linq;
using System.Collections.Generic;

public class AvatarCustomizer : MonoBehaviour
{
    private CubismModel _model;
    private Live2DTextureSwapper _textureSwapper;

    void Awake()
    {
        _model = this.GetComponent<CubismModel>();
        _textureSwapper = this.GetComponent<Live2DTextureSwapper>();
    }

    public void ApplyAppearance(CharacterAppearanceData appearanceData, CustomizationDatabase database)
    {
        if (appearanceData == null || _model == null || database == null) return;

        // --- 1. Применяем текстуры (как и раньше) ---
        ApplyTextures(appearanceData, database);

        // --- 2. Применяем параметры из СТАРОЙ системы (для обратной совместимости) ---
        foreach (var setting in appearanceData.parameterSettings)
        {
            var parameter = _model.Parameters.FirstOrDefault(p => p.Id == setting.parameterId);
            if (parameter != null) { parameter.Value = setting.value; }
        }
        
        // --- 3. Применяем параметры из НОВОЙ системы ---
        foreach (var selection in appearanceData.selectedParameterSettings)
        {
            // Находим нужный слот в базе (например, "clothing_color")
            var slot = database.parameterSlots.FirstOrDefault(s => s.slotId == selection.slotId);
            if (slot == null) continue;

            // Внутри слота находим выбранную опцию (например, "red_color")
            var option = slot.options.FirstOrDefault(o => o.optionId == selection.selectedOptionId);
            if (option == null) continue;

            // Применяем ВСЕ настройки из этой опции
            foreach (var setting in option.settings)
            {
                var parameter = _model.Parameters.FirstOrDefault(p => p.Id == setting.parameterId);
                if (parameter != null)
                {
                    parameter.Value = setting.value;
                    Debug.Log($"Применен параметр: {parameter.Id} = {setting.value}");
                }
            }
        }
    }
    
    // Метод для текстур вынесен для чистоты кода
    private void ApplyTextures(CharacterAppearanceData appearanceData, CustomizationDatabase database)
    {
         if (_textureSwapper != null && appearanceData.textureSettings.Count > 0)
        {
            var texturesToApply = new List<Texture2D>();
            foreach (var setting in appearanceData.textureSettings)
            {
                var slot = database.textureSlots.FirstOrDefault(s => s.originalTextureName == setting.originalTextureName);
                if (slot == null) continue;

                var option = slot.options.FirstOrDefault(o => o.optionId == setting.selectedOptionId);
                if (option != null && option.texture != null)
                {
                    texturesToApply.Add(option.texture);
                }
            }
            _textureSwapper.SetNewTextures(texturesToApply);
            _textureSwapper.ApplyRecolor();
        }
    }
}