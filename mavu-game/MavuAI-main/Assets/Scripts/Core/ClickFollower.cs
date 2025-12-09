using UnityEngine;
// 1. Убедись, что это пространство имен подключено
using UnityEngine.InputSystem;

public class ClickFollower : MonoBehaviour
{
    [Tooltip("Объект, который будет становиться активным при нажатии")]
    [SerializeField] private GameObject target;

    [Tooltip("Объект, который будет следовать за курсором")]
    [SerializeField] private GameObject handler;

    private Camera _mainCamera;

    private ClickPosInput playerControls; 
    
    void Awake()
    {
        _mainCamera = Camera.main;
        
        playerControls = new ClickPosInput();

        if (target != null)
        {
            target.SetActive(false);
        }
    }

    private void OnEnable()
    {
        playerControls.GamePlay.Enable();
        playerControls.GamePlay.Click.started += OnClickStarted;
        playerControls.GamePlay.Click.canceled += OnClickCanceled;
    }
    private void OnDisable()
    {
        playerControls.GamePlay.Click.started -= OnClickStarted;
        playerControls.GamePlay.Click.canceled -= OnClickCanceled;
        
        playerControls.GamePlay.Disable();
    }
    
    private void OnClickStarted(InputAction.CallbackContext context)
    {
        // Это полная замена `Input.GetMouseButtonDown(0)`
        if (target != null)
        {
            target.SetActive(true);
        }
    }
    private void OnClickCanceled(InputAction.CallbackContext context)
    {
        // Это полная замена `Input.GetMouseButtonUp(0)`
        if (target != null)
        {
            target.SetActive(false);
        }
    }

    void Update()
    {
        // Это замена `Input.GetMouseButton(0)`
        if (playerControls.GamePlay.Click.IsPressed())
        {
            MoveHandlerToCursor();
        }
    }
    
    void MoveHandlerToCursor()
    {
        if (handler == null) return;
        Vector2 mouseScreenPosition = playerControls.GamePlay.MousePosition.ReadValue<Vector2>();
        Vector3 mouseWorldPosition = _mainCamera.ScreenToWorldPoint(mouseScreenPosition);
        handler.transform.position = new Vector3(mouseWorldPosition.x, mouseWorldPosition.y, handler.transform.position.z);
    }
}