using UnityEngine;
using UnityEngine.EventSystems;

public class HideInputAccessory : MonoBehaviour, ISelectHandler, IDeselectHandler
{
    public void OnSelect(BaseEventData eventData)
    {
#if UNITY_IOS
        TouchScreenKeyboard.hideInput = true;
#endif
    }
    public void OnDeselect(BaseEventData eventData)
    {
#if UNITY_IOS
        TouchScreenKeyboard.hideInput = false;
#endif
    }
}