using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Events;
using UnityEngine.UI;

public class AgeSelector : MonoBehaviour
{
    public UnityEvent OnAgeChanged;
    
    [Header("Настройки возраста")]
    [SerializeField] private int minAge = 18;
    [SerializeField] private int maxAge = 99;

    [Header("Компоненты и префабы")]
    [SerializeField] private AgeCell ageCellPrefab;
    [SerializeField] private Transform contentParent;
    [SerializeField] private ScrollRect scrollRect;
    [SerializeField] private HorizontalLayoutGroup contentLayoutGroup;

    [Header("Спрайты для ячеек")]
    [SerializeField] private Sprite normalCellSprite;
    [SerializeField] private Sprite highlightedCellSprite;

    public int SelectedAge { get; private set; }

    private List<AgeCell> _ageCells = new List<AgeCell>();
    private Coroutine _scrollCoroutine;
    private bool _isScrolling;

    void Start()
    {
        PopulateAgeCells();
        SetPadding();
    }

    void Update()
    {
        if (!_isScrolling)
        {
            UpdateHighlightedCell();
        }
    }

    private void SetPadding()
    {
        float viewportWidth = scrollRect.viewport.rect.width;
        float cellWidth = ageCellPrefab.GetComponent<RectTransform>().rect.width;
        int padding = Mathf.RoundToInt((viewportWidth / 2f) - (cellWidth / 2f));
        contentLayoutGroup.padding.left = padding;
        contentLayoutGroup.padding.right = padding;
    }
    private void PopulateAgeCells()
    {
        for (int age = minAge; age <= maxAge; age++)
        {
            AgeCell newCell = Instantiate(ageCellPrefab, contentParent);
            newCell.Setup(age, this);
            _ageCells.Add(newCell);
        }
    }
    
    private void UpdateHighlightedCell()
    {
        Vector3[] viewportCorners = new Vector3[4];
        scrollRect.viewport.GetWorldCorners(viewportCorners);
        float viewportWorldCenterX = (viewportCorners[0].x + viewportCorners[2].x) / 2f;
        float minDistance = float.MaxValue;
        AgeCell centerCell = null;
        foreach (var cell in _ageCells)
        {
            float distance = Mathf.Abs(viewportWorldCenterX - cell.RectTransform.position.x);

            if (distance < minDistance)
            {
                minDistance = distance;
                centerCell = cell;
            }
        }
        
        if (centerCell != null)
        {
            int previouslySelectedAge = SelectedAge;
            foreach (var cell in _ageCells)
            {
                Image cellImage = cell.GetComponent<Image>();
                cellImage.sprite = (cell == centerCell) ? highlightedCellSprite : normalCellSprite;
            }
            SelectedAge = int.Parse(centerCell.GetComponentInChildren<TMPro.TextMeshProUGUI>().text);
            if(previouslySelectedAge != SelectedAge)
            {
                OnAgeChanged?.Invoke();
            }
        }
    }
    public void ScrollToCell(AgeCell targetCell)
    {
        if (_scrollCoroutine != null)
        {
            StopCoroutine(_scrollCoroutine);
        }
        _scrollCoroutine = StartCoroutine(SmoothScrollTo(targetCell));
    }
    private IEnumerator SmoothScrollTo(AgeCell targetCell)
    {
        _isScrolling = true;
        
        float contentTargetX = scrollRect.viewport.rect.width / 2 - targetCell.RectTransform.anchoredPosition.x;
        Vector2 targetPos = new Vector2(contentTargetX, contentParent.GetComponent<RectTransform>().anchoredPosition.y);
        
        float timer = 0f;
        float duration = 0.3f;
        Vector2 startPos = contentParent.GetComponent<RectTransform>().anchoredPosition;

        while (timer < duration)
        {
            contentParent.GetComponent<RectTransform>().anchoredPosition = Vector2.Lerp(startPos, targetPos, timer / duration);
            timer += Time.deltaTime;
            yield return null;
        }

        contentParent.GetComponent<RectTransform>().anchoredPosition = targetPos;
        _isScrolling = false;
    }
}