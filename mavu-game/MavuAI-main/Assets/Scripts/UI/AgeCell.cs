using TMPro;
using UnityEngine;
using UnityEngine.UI;

public class AgeCell : MonoBehaviour
{
    [SerializeField] private TextMeshProUGUI ageText;
    
    private int _ageValue;
    private AgeSelector _ageSelector;
    
    public void Setup(int age, AgeSelector selector)
    {
        _ageValue = age;
        _ageSelector = selector;
        ageText.text = _ageValue.ToString();
        
        GetComponent<Button>().onClick.AddListener(OnCellClick);
    }

    private void OnCellClick()
    {
        _ageSelector.ScrollToCell(this);
    }
    
    public RectTransform RectTransform => (RectTransform)transform;
}