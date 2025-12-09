using UnityEngine;
using UnityEngine.UI;

[RequireComponent(typeof(Image))]
public class SpriteSizeUpdater : MonoBehaviour
{
    private Image img;
    private RectTransform rectTransform;

    // Сюда мы впишем максимальные размеры твоего контейнера
    [Tooltip("Максимальная ширина, в которую нужно вписать спрайт")]
    public float maxWidth = 89f;
    [Tooltip("Максимальная высота, в которую нужно вписать спрайт")]
    public float maxHeight = 85f;

    void Start()
    {
        img = GetComponent<Image>();
        rectTransform = GetComponent<RectTransform>();

        if (img != null)
        {
            img.preserveAspect = false;
        }

        if (img != null && img.sprite != null)
        {
            UpdateSize();
        }
    }
    public void UpdateSize()
    {
        if (img == null || rectTransform == null)
        {
            Debug.LogWarning("Компоненты Image или RectTransform не найдены.");
            return;
        }

        if (img.sprite == null)
        {
            rectTransform.sizeDelta = Vector2.zero;
            return;
        }

        float spriteWidth = img.sprite.rect.width;
        float spriteHeight = img.sprite.rect.height;
        float spriteRatio = spriteWidth / spriteHeight;
        float containerRatio = maxWidth / maxHeight;
        float newWidth;
        float newHeight;

        if (spriteRatio > containerRatio)
        {
            newWidth = maxWidth;
            newHeight = newWidth / spriteRatio;
        }
        else
        {
            newHeight = maxHeight;
            newWidth = newHeight * spriteRatio;
        }

        rectTransform.sizeDelta = new Vector2(newWidth, newHeight);
    }
    
    public void ChangeSprite(Sprite newSprite)
    {
        if (img == null) img = GetComponent<Image>();
        
        img.sprite = newSprite;
        UpdateSize();
    }
}