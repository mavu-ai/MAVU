using UnityEngine;
using UnityEngine.InputSystem;

public class RippleTrigger : MonoBehaviour
{
    [SerializeField] private GameObject prefabToSpawn; 
    [SerializeField] private float spawnInterval = 0.5f; 
    [SerializeField] private float followSpeed = 10f;

    private InputAction pressAction;
    private InputAction positionAction;
    private Camera mainCamera;
    private Vector3 targetPosition;
    private float nextSpawnTime;

    void Awake()
    {
        mainCamera = Camera.main;

        if (prefabToSpawn == null)
        {
            Debug.LogWarning("No prefab assigned to spawn!");
            return;
        }

        pressAction = new InputAction("Press", InputActionType.Button, "<Pointer>/press");
        positionAction = new InputAction("Position", binding: "<Pointer>/position");

        targetPosition = transform.position;
        nextSpawnTime = Time.time;
    }

    private void OnEnable()
    {
        pressAction.Enable();
        positionAction.Enable();

        pressAction.started += OnPressStarted;
    }

    private void OnDisable()
    {
        pressAction.started -= OnPressStarted;

        pressAction.Disable();
        positionAction.Disable();
    }

    private void OnPressStarted(InputAction.CallbackContext context)
    {
        Vector2 screenPos = positionAction.ReadValue<Vector2>();
        Vector3 worldPos = mainCamera.ScreenToWorldPoint(new Vector3(screenPos.x, screenPos.y, 2f));
        transform.position = worldPos;
        targetPosition = worldPos;

        if (spawnInterval > 0)
        {
            Instantiate(prefabToSpawn, transform.position, Quaternion.identity);
            nextSpawnTime = Time.time + spawnInterval;
        }
    }

    void Update()
    {
        if (pressAction.IsPressed())
        {
            Vector2 screenPos = positionAction.ReadValue<Vector2>();
            Vector3 worldPos = mainCamera.ScreenToWorldPoint(new Vector3(screenPos.x, screenPos.y, 2f));
            targetPosition = worldPos;

            if (Time.time >= nextSpawnTime)
            {
                Instantiate(prefabToSpawn, transform.position, Quaternion.identity);
                nextSpawnTime = Time.time + spawnInterval;
            }
        }

        transform.position = Vector3.Lerp(transform.position, targetPosition, followSpeed * Time.deltaTime);
    }
}