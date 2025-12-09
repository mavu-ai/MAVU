using UnityEngine;
using Scripts; 

public class UINotificationService : Singleton<UINotificationService>
{
    [Header("Префаб Уведомления")]
    [SerializeField] private NotificationPopup notificationPrefab;
    
    [Header("Куда спавнить")]
    [SerializeField] private Transform notificationParent;

    private NotificationPopup _notificationInstance;

    protected override void AwakeSingletone()
    {
        base.AwakeSingletone();
        
        if (notificationParent == null)
        {
            notificationParent = FindObjectOfType<Canvas>().transform;
            if (notificationParent == null)
            {
                Debug.LogError("[UINotificationService] Не найден Canvas!");
                return;
            }
        }

        if (notificationPrefab != null)
        {
            _notificationInstance = Instantiate(notificationPrefab, notificationParent);
            _notificationInstance.gameObject.SetActive(false);
        }
        else
        {
            Debug.LogError("[UINotificationService] Префаб уведомления не назначен!");
        }
    }
    
    public void ShowError(string message)
    {
        if (_notificationInstance == null) return;
        
        _notificationInstance.Show(message);
    }

    public void ShowSuccess(string message)
    {
        if (_notificationInstance == null) return;

        _notificationInstance.Show(message);
    }
}