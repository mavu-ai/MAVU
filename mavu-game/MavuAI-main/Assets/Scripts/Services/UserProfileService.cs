using System.Collections;
using System.Text;
using UnityEngine;
using Scripts;
using Scripts.Models;
using TMPro;
using UnityEngine.Networking;
using UnityEngine.UI;

public class UserProfileService : Singleton<UserProfileService>
{
    [Header("Настройки API")] 
    [Tooltip("Базовый URL вашего API.")] 
    [SerializeField] private string baseUrl = "https://mavu-api.aey-inc.uz/api/v1";

    protected AppManager appManager;
    protected Button updateSettingsButton;
    protected TMP_InputField promoCodeInputField;
    
    private bool _isLoginInProgress = false; 

    public void Init(AppManager _appManager)
    {
        appManager = _appManager;
        updateSettingsButton = AppManager.Instance.updateSettingsButton;
        promoCodeInputField = AppManager.Instance.promoCodeInputField;
    }

    public IEnumerator LoginWithPromoCode(string promoCodeRaw)
    {
        if (_isLoginInProgress) yield break;
        
        string cleanPromoCode = promoCodeRaw.Replace("\u200B", "").Trim();

        if (string.IsNullOrEmpty(cleanPromoCode))
        {
            Debug.LogError("Промокод пустой после очистки!");
            yield break;
        }

        _isLoginInProgress = true;

        string url = $"{baseUrl}/auth/register"; 

        PromoCodeLoginRequestData requestData = new PromoCodeLoginRequestData { promo_code = cleanPromoCode };
        string jsonBody = JsonUtility.ToJson(requestData);
        
        Debug.Log($"[PromoLogin] JSON Body: {jsonBody}"); 

        byte[] bodyRaw = Encoding.UTF8.GetBytes(jsonBody);

        using (var request = new UnityWebRequest(url, "POST"))
        {
            request.uploadHandler = new UploadHandlerRaw(bodyRaw);
            request.downloadHandler = new DownloadHandlerBuffer();
            request.SetRequestHeader("Content-Type", "application/json");
            request.SetRequestHeader("Accept", "application/json"); 

            yield return request.SendWebRequest();
            _isLoginInProgress = false;

            if (request.result == UnityWebRequest.Result.Success)
            {
                var responseData = JsonUtility.FromJson<RegisterResponse>(request.downloadHandler.text);

                if (responseData != null && !string.IsNullOrEmpty(responseData.session_token))
                {
                    AuthService.Instance.SaveSessionToken(responseData.session_token, AuthService.AuthStatus.Guest);
                    Debug.Log($"ВХОД ВЫПОЛНЕН! UserID: {responseData.user_id}");

                    if (!string.IsNullOrEmpty(FirebaseInitializer.FcmToken))
                    {
                        appManager.StartCoroutine(
                            NotificationService.Instance.RegisterDeviceForPush(FirebaseInitializer.FcmToken));
                    }

                    appManager.HidePopup(AppManager.UIPopup.PromoCode);
                }
                else
                {
                    Debug.LogError("[PromoLogin] Токен не пришел.");
                    UINotificationService.Instance.ShowError("System error: no token");
                }
            }
            else
            {
                Debug.LogError($"[PromoLogin] Ошибка {request.responseCode}: {request.downloadHandler.text}");
                
                if (request.responseCode == 500)
                {
                    UINotificationService.Instance.ShowError("Ошибка сервера. Попробуйте еще раз.");
                }
                else
                {
                    UINotificationService.Instance.ShowError($"Ошибка: {request.downloadHandler.text}");
                }
            }
        }
    }

    public IEnumerator UpdateSettings(string newName, int newAge)
    {
        if (string.IsNullOrEmpty(AuthService.Instance.SessionToken))
        {
            Debug.LogError("Невозможно обновить данные, пользователь не авторизован.");
            yield break;
        }

        if (updateSettingsButton != null) updateSettingsButton.interactable = false;

        string url = $"{baseUrl}/profile/me"; 

        UpdateSettingsRequestData requestData = new UpdateSettingsRequestData { name = newName, age = newAge };
        string jsonBody = JsonUtility.ToJson(requestData);
        byte[] bodyRaw = Encoding.UTF8.GetBytes(jsonBody);

        using (var request = new UnityWebRequest(url, "PATCH"))
        {
            request.uploadHandler = new UploadHandlerRaw(bodyRaw);
            request.downloadHandler = new DownloadHandlerBuffer();
            request.SetRequestHeader("Content-Type", "application/json");
            request.SetRequestHeader("Accept", "application/json");
            request.SetRequestHeader("X-Session-Token", AuthService.Instance.SessionToken);

            yield return request.SendWebRequest();

            if (request.result == UnityWebRequest.Result.Success)
            {
                Debug.Log("УСПЕХ! Данные профиля обновлены.");
            }
            else
            {
                Debug.LogError($"[ОБНОВЛЕНИЕ] Ошибка: {request.error}\nТело: {request.downloadHandler.text}");
            }
        }

        if (updateSettingsButton != null) updateSettingsButton.interactable = true;
    }
}