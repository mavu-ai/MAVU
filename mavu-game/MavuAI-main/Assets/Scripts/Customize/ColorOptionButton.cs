using UnityEngine;
using UnityEngine.UI;
using System;

public class ColorOptionButton : MonoBehaviour
{
    // --- Публичные поля, которые настроит менеджер ---
    public Image buttonImage; // Ссылка на изображение кнопки (для смены цвета/спрайта)
    public GameObject selectedOutline; // Ссылка на обводку

    // --- Приватные данные ---
    private string _textureToChange; // "texture_00" или "texture_01"
    private string _optionId; // "blue", "green"
    private Action<string, string> _onClickAction;

    // Метод для "зарядки" кнопки данными при ее создании
    public void Setup(TextureOption option, string textureSlot, Action<string, string> onClick)
    {
        _textureToChange = textureSlot;
        _optionId = option.optionId;
        _onClickAction = onClick;

        if (buttonImage != null && option.icon != null)
        {
            buttonImage.sprite = option.icon; // <-- ДОБАВЬ ЭТУ СТРОКУ
        }
        
        // Подписываемся на клик
        GetComponent<Button>().onClick.AddListener(OnButtonClick);
    }

    public void Setup(ParameterOption option, string slotId, System.Action<string, string> onClick)
    {
        _textureToChange = slotId; // Используем ту же переменную для ID слота
        _optionId = option.optionId;
        _onClickAction = onClick;

        if (buttonImage != null && option.icon != null)
        {
            buttonImage.sprite = option.icon;
        }
        
        GetComponent<Button>().onClick.AddListener(OnButtonClick);
    }
    private void OnButtonClick()
    {
        // Когда на кнопку нажимают, она вызывает действие, которое ей передал менеджер
        _onClickAction?.Invoke(_textureToChange, _optionId);
    }

    // Метод для управления обводкой
    public void SetSelected(bool isSelected)
    {
        if (selectedOutline != null)
        {
            selectedOutline.SetActive(isSelected);
        }
    }
}