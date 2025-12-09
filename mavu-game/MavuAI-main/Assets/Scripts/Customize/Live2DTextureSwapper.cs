using UnityEngine;
using Live2D.Cubism.Rendering;
using System.Collections.Generic;
using System.Linq;

// Этот скрипт нужно повесить на корневой объект Live2D модели.
public class Live2DTextureSwapper : MonoBehaviour
{
    [Tooltip("Перетащите сюда все новые текстуры из папки recolor")]
    [SerializeField]
    private List<Texture2D> newTextures;
    public void SetNewTextures(List<Texture2D> textures)
    {
        newTextures = textures;
    }

    // Этот метод можно вызвать при старте или по нажатию кнопки в UI.
    public void ApplyRecolor()
    {
        if (newTextures == null || !newTextures.Any())
        {
            Debug.LogWarning("Список новых текстур пуст. Замена невозможна.", this);
            return;
        }

        // Находим все компоненты CubismRenderer в дочерних объектах модели.
        var renderers = this.GetComponentsInChildren<CubismRenderer>();

        // Для удобства и скорости создаем словарь, где ключ - это имя текстуры.
        // Например: {"texture_00" -> Texture2D_recolor_asset, "texture_01" -> ...}
        var textureMap = newTextures.ToDictionary(t => t.name, t => t);

        // Проходим по каждому рендереру модели.
        foreach (var renderer in renderers)
        {
            // Узнаем имя его текущей, оригинальной текстуры.
            string originalTextureName = renderer.MainTexture.name;

            // Ищем в нашем словаре новую текстуру с таким же именем.
            if (textureMap.TryGetValue(originalTextureName, out Texture2D replacementTexture))
            {
                // Если нашли - заменяем!
                renderer.MainTexture = replacementTexture;
                Debug.Log($"Текстура '{originalTextureName}' успешно заменена на рендерере '{renderer.name}'.", renderer);
            }
        }
    }

    // Для удобства можно вызывать замену прямо при старте сцены.
    void Start()
    {
        ApplyRecolor();
    }
}