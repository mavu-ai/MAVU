using System.Collections;
using UnityEngine;
using Scripts;
using Scripts.Models;
using UnityEngine.Networking; // Понадобится для RegisterDeviceForPush

public class NotificationService : Singleton<NotificationService>
{
    // Сюда переедет RegisterDeviceForPush
    
    [Header("Настройки API")]
    [Tooltip("Базовый URL вашего API.")]
    [SerializeField]
    private string baseUrl = "https://mavu-api.aey-inc.uz/api/v1";
    protected AppManager appManager;

    public IEnumerator RegisterDeviceForPush(string fcmToken)
    {
        yield break;
        if (string.IsNullOrEmpty(AuthService.Instance.SessionToken))
        {
            Debug.LogWarning("[FCM] Невозможно зарегистрировать устройство, пользователь не авторизован.");
            yield break;
        }

        string url = $"{baseUrl}/fcm_device/";

        FCMDeviceRequest requestData = new FCMDeviceRequest();
        requestData.registration_id = fcmToken;
        requestData.device_id = SystemInfo.deviceUniqueIdentifier;

#if UNITY_IOS
        requestData.device_type = "ios";
#elif UNITY_ANDROID
        requestData.device_type = "android";
#else
    requestData.device_type = "web";
#endif

        string jsonBody = JsonUtility.ToJson(requestData);
        byte[] bodyRaw = System.Text.Encoding.UTF8.GetBytes(jsonBody);

        using (var request =
               new UnityWebRequest(url, "POST", new DownloadHandlerBuffer(), new UploadHandlerRaw(bodyRaw)))
        {
            request.SetRequestHeader("Content-Type", "application/json");
            request.SetRequestHeader("X-Session-Token", AuthService.Instance.SessionToken);

            yield return request.SendWebRequest();

            if (request.result == UnityWebRequest.Result.Success)
            {
                Debug.Log("[FCM] Устройство успешно зарегистрировано для получения push-уведомлений!");
            }
            else
            {
                Debug.LogError(
                    $"[FCM] Ошибка регистрации устройства: {request.error}\nТело ответа: {request.downloadHandler.text}");
            }
        }
    }
    // Мы будем постепенно переносить сюда переменные и методы
    public void Init(AppManager _appManager)
    {
        appManager = _appManager;
    }
}