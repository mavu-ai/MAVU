using System.Collections;
using System.Text;
using UnityEngine;

// Убедись, что namespace Core2 (где лежит Singleton) подключен,
// или удали using, если Singleton в глобальном namespace
using Scripts;
using Scripts.Models;
using UnityEngine.Networking;

public class AuthService : Singleton<AuthService>
{
    public AuthStatus CurrentAuthStatus => _currentAuthStatus;

    public enum AuthStatus { None, Guest, FullUser }
    private const string AuthStatusKey = "PlayerAuthStatus";
    private AuthStatus _currentAuthStatus = AuthStatus.None;
    public string SessionToken { get; private set; }
    private const string SessionTokenKey = "PlayerSessionToken";
    [Header("Настройки API")]
    [Tooltip("Базовый URL вашего API.")]
    [SerializeField]
    private string baseUrl = "https://mavu-api.aey-inc.uz/api/v1";
    protected AppManager appManager;
    private string _registrationName;
    private int _registrationAge;
    private GenderSelector.Gender _registrationGender;
    
    public void Init(AppManager _appManager)
    {
        appManager = _appManager;
    }

    public void SaveSessionToken(string token, AuthStatus status)
    {
        SessionToken = token;
        _currentAuthStatus = status;
    
        PlayerPrefs.SetString(SessionTokenKey, token);
        PlayerPrefs.SetInt(AuthStatusKey, (int)status);
        PlayerPrefs.Save();
    }

    public void LoadSessionToken()
    {
        SessionToken = PlayerPrefs.GetString(SessionTokenKey, null);
        _currentAuthStatus = (AuthStatus)PlayerPrefs.GetInt(AuthStatusKey, (int)AuthStatus.None);
    }
    
    public IEnumerator CheckSessionTokenOnStart()
    {
        if (string.IsNullOrEmpty(SessionToken) || _currentAuthStatus == AuthStatus.None)
        {
            Debug.Log("Сохраненный токен не найден. Показываем MainApp + Попап Промокода.");
            appManager.SwitchToPanel(AppManager.UIPanel.MainApp);
            appManager.ShowPopup(AppManager.UIPopup.PromoCode);
            yield break;
        }

        if (_currentAuthStatus == AuthStatus.Guest)
        {
            Debug.Log($"Найден 'гостевой' токен. Доверяем ему и входим в приложение.");
            appManager.HideAllAuthPanels();
            appManager.HidePopup(AppManager.UIPopup.PromoCode);
            yield break;
        }

        if (_currentAuthStatus == AuthStatus.FullUser)
        {
            Debug.Log($"Найден 'полный' токен. Проверяем его валидность через /profile/...");
            string url = $"{baseUrl}/auth/profile/";
            using (UnityWebRequest request = UnityWebRequest.Get(url))
            {
                request.SetRequestHeader("X-Session-Token", SessionToken);
                yield return request.SendWebRequest();

                if (request.result == UnityWebRequest.Result.Success)
                {
                    Debug.Log("Успешная проверка 'полного' токена. Вход выполнен.");
                    appManager.HideAllAuthPanels();
                    appManager.HidePopup(AppManager.UIPopup.PromoCode);
                
                    if (!string.IsNullOrEmpty(FirebaseInitializer.FcmToken))
                    {
                        StartCoroutine(NotificationService.Instance.RegisterDeviceForPush(FirebaseInitializer.FcmToken));
                    }
                }
                else
                {
                    Debug.LogWarning($"'Полный' токен не прошел проверку: {request.error}. Выполняем Logout.");
                    Logout();
                }
            }
        }
    }
    public void Logout()
    {
        SessionToken = null;
        _currentAuthStatus = AuthStatus.None;
    
        PlayerPrefs.DeleteKey(SessionTokenKey);
        PlayerPrefs.DeleteKey(AuthStatusKey);
        PlayerPrefs.Save();
    
        Debug.Log("ВЫХОД ИЗ СИСТЕМЫ: Токен и статус сессии были удалены.");

        appManager.SwitchToPanel(AppManager.UIPanel.MainApp);
        appManager.ShowPopup(AppManager.UIPopup.PromoCode);
    }
    
    public void SetProfileDataForRegistration(string name, int age, GenderSelector.Gender gender)
    {
        _registrationName = name;
        _registrationAge = age;
        _registrationGender = gender;
        Debug.Log(
            $"Данные для регистрации сохранены: Имя={_registrationName}, Возраст={_registrationAge}, Пол={_registrationGender}");
    }
    
    public void TryAttachEmail()
    {
        string email = appManager.attachEmailInputField.text.Replace("\u200B", "").Trim();

        if (string.IsNullOrWhiteSpace(email) || !email.Contains("@"))
        {
            Debug.LogError("Ошибка: Введите корректный email для привязки.");
            return;
        }
        
        if (string.IsNullOrEmpty(SessionToken) || _currentAuthStatus == AuthStatus.None)
        {
            Debug.LogError("Ошибка: Невозможно привязать email, сессия не найдена.");
            Logout();
            return;
        }

        appManager.StartCoroutine(SendVerificationEmail(email));
    }
    private IEnumerator SendVerificationEmail(string email)
    {
        if (appManager.attachEmailButton != null) appManager.attachEmailButton.interactable = false;

        string url = $"{baseUrl}/auth/email/send-verification/";

        SendVerificationEmailRequest requestData = new SendVerificationEmailRequest { new_email = email };
        string jsonBody = JsonUtility.ToJson(requestData);
        byte[] bodyRaw = Encoding.UTF8.GetBytes(jsonBody);

        Debug.Log($"[AttachEmail] Отправка запроса на {url} с email: {email}");

        using (var request =
               new UnityWebRequest(url, "POST", new DownloadHandlerBuffer(), new UploadHandlerRaw(bodyRaw)))
        {
            request.SetRequestHeader("Content-Type", "application/json");
            request.SetRequestHeader("X-Session-Token", SessionToken); 

            yield return request.SendWebRequest();

            if (request.result == UnityWebRequest.Result.Success)
            {
                Debug.Log("УСПЕХ! Запрос на привязку email отправлен. Проверьте почту.");
                appManager.SwitchToPanel(AppManager.UIPanel.WaitingForEmail);
            }
            else
            {
                Debug.LogError($"[AttachEmail] Ошибка: {request.error}\nТело ответа: {request.downloadHandler.text}");
                UINotificationService.Instance.ShowError(request.downloadHandler.text);
                if (appManager.attachEmailButton != null) appManager.attachEmailButton.interactable = true;
            }
        }
    }
    private IEnumerator RequestRegistration(string email, string userName, int userAge,
        GenderSelector.Gender userGender)
    {
        if (appManager.registerButton != null) appManager.registerButton.interactable = false;

        string url = $"{baseUrl}/auth/register/";

        string genderString;
        switch (userGender)
        {
            case GenderSelector.Gender.Boy:
                genderString = "male";
                break;
            case GenderSelector.Gender.Girl:
                genderString = "female";
                break;
            default:
                Debug.LogWarning($"[РЕГИСТРАЦИЯ] Пол не был выбран (None). Отправка 'male' по умолчанию.");
                genderString = "male";
                break;
        }

        UserSettingsData settingsData = new UserSettingsData { name = userName, age = userAge, gender = genderString };
        RegisterRequestData requestData = new RegisterRequestData { email = email, settings = settingsData };

        Debug.Log($"[РЕГИСТРАЦИЯ] Отправка JSON: {JsonUtility.ToJson(requestData)}");

        string jsonBody = JsonUtility.ToJson(requestData);
        byte[] bodyRaw = Encoding.UTF8.GetBytes(jsonBody);

        using (var request =
               new UnityWebRequest(url, "POST", new DownloadHandlerBuffer(), new UploadHandlerRaw(bodyRaw)))
        {
            request.SetRequestHeader("Content-Type", "application/json");
            yield return request.SendWebRequest();

            if (request.result == UnityWebRequest.Result.Success)
            {
                Debug.Log("УСПЕХ РЕГИСТРАЦИИ! Проверьте почту. Переключаемся на окно ожидания.");
                appManager.SwitchToPanel(AppManager.UIPanel.WaitingForEmail);
                
                StartCoroutine(SendSecondaryRegistrationRequest(email, settingsData, 5.0f));
            }
            else
            {
                Debug.LogError($"[РЕГИСТРАЦИЯ] Ошибка: {request.error}\nТело ответа: {request.downloadHandler.text}");
                UINotificationService.Instance.ShowError(request.downloadHandler.text);
                if (appManager.registerButton != null) appManager.registerButton.interactable = true;
            }
        }
    }
    private IEnumerator SendSecondaryRegistrationRequest(string email, UserSettingsData settings, float delay)
    {
        yield return new WaitForSeconds(delay);

        Debug.Log($"[КОСТЫЛЬ-РЕГИСТРАЦИЯ] Отправка повторного запроса для email: {email}...");

        string url = $"{baseUrl}/auth/register/";
        RegisterRequestData requestData = new RegisterRequestData { email = email, settings = settings };
        string jsonBody = JsonUtility.ToJson(requestData);
        byte[] bodyRaw = Encoding.UTF8.GetBytes(jsonBody);

        using (var request =
               new UnityWebRequest(url, "POST", new DownloadHandlerBuffer(), new UploadHandlerRaw(bodyRaw)))
        {
            request.SetRequestHeader("Content-Type", "application/json");
            yield return request.SendWebRequest();

            if (request.result == UnityWebRequest.Result.Success)
            {
                Debug.LogWarning(
                    "[КОСТЫЛЬ-РЕГИСТРАЦИЯ] Повторный запрос почему-то прошел успешно. Этого не должно было случиться.");
            }
            else
            {
                Debug.Log(
                    $"[КОСТЫЛЬ-РЕГИСТРАЦИЯ] Повторный запрос ожидаемо вернул ошибку (это нормально): {request.error}");
            }
        }
    }
    
    public void TryRegister()
    {
        if (string.IsNullOrEmpty(_registrationName))
        {
            Debug.LogError("Ошибка: Данные профиля (имя/возраст) не были установлены. Возврат на стартовый экран.");
            appManager.SwitchToPanel(AppManager.UIPanel.Start);
            return;
        }
        string email = appManager.registerEmailInputField.text.Replace("\u200B", "").Trim();

        if (string.IsNullOrWhiteSpace(email) || !email.Contains("@"))
        {
            Debug.LogError("Ошибка: Введите корректный email для регистрации.");
            return;
        }
        StartCoroutine(RequestRegistration(email, _registrationName, _registrationAge, _registrationGender));
    }

    public void TryLogin()
    {
        string email = appManager.loginEmailInputField.text.Replace("\u200B", "").Trim();
        if (string.IsNullOrWhiteSpace(email) || !email.Contains("@"))
        {
            Debug.LogError("Ошибка: Введите корректный email для входа.");
            return;
        }

        StartCoroutine(RequestLoginLink(email));
    }
    
    public IEnumerator VerifyRegistrationEmail(string token)
    {
        appManager.SwitchToPanel(AppManager.UIPanel.WaitingForEmail);

        string url = $"{baseUrl}/auth/verify-email/{token}/";
        using (var request = UnityWebRequest.Get(url))
        {
            yield return request.SendWebRequest();

            if (request.result == UnityWebRequest.Result.Success)
            {
                Debug.Log("УСПЕХ! Email успешно подтвержден. Переходим к окну входа.");
                appManager.SwitchToPanel(AppManager.UIPanel.Login);
            }
            else
            {
                Debug.LogError(
                    $"[ПОДТВЕРЖДЕНИЕ EMAIL] Ошибка: {request.error}\nТело ответа: {request.downloadHandler.text}");
                UINotificationService.Instance.ShowError(request.downloadHandler.text);
                appManager.SwitchToPanel(AppManager.UIPanel.Register);
            }
        }
    }
    
    private IEnumerator RequestLoginLink(string email)
    {
        if (appManager.loginButton != null) appManager.loginButton.interactable = false;

        string url = $"{baseUrl}/auth/login/";
        var requestData = new LoginRequestData { email = email };
        string jsonBody = JsonUtility.ToJson(requestData);
        byte[] bodyRaw = Encoding.UTF8.GetBytes(jsonBody);

        using (var request =
               new UnityWebRequest(url, "POST", new DownloadHandlerBuffer(), new UploadHandlerRaw(bodyRaw)))
        {
            request.SetRequestHeader("Content-Type", "application/json");
            yield return request.SendWebRequest();

            if (request.result == UnityWebRequest.Result.Success)
            {
                Debug.Log("УСПЕХ ЗАПРОСА НА ВХОД! Проверьте почту. Переключаемся на окно ожидания.");
                appManager.SwitchToPanel(AppManager.UIPanel.WaitingForEmail);
            }
            else
            {
                Debug.LogError($"[ВХОД] Ошибка: {request.error}\nТело ответа: {request.downloadHandler.text}");
                UINotificationService.Instance.ShowError(request.downloadHandler.text);
                if (appManager.loginButton != null) appManager.loginButton.interactable = true;
                
            }
        }
    }

    public IEnumerator VerifyLoginAndGetSessionToken(string token)
    {
        appManager.SwitchToPanel(AppManager.UIPanel.WaitingForEmail);

        string url = $"{baseUrl}/auth/verify-login/{token}/";
        using (var request =
               new UnityWebRequest(url, "POST", new DownloadHandlerBuffer(), new UploadHandlerRaw(new byte[0])))
        {
            yield return request.SendWebRequest();

            if (request.result == UnityWebRequest.Result.Success)
            {
                var responseData = JsonUtility.FromJson<RegisterResponse>(request.downloadHandler.text);
                if (responseData != null && !string.IsNullOrEmpty(responseData.session_token))
                { 
                    SaveSessionToken(responseData.session_token, AuthStatus.FullUser);
                    Debug.Log("ВХОД ВЫПОЛНЕН! Получен и сохранен ключ сессии. Скрываем UI авторизации.");
                    if (!string.IsNullOrEmpty(FirebaseInitializer.FcmToken))
                    {
                        StartCoroutine(NotificationService.Instance.RegisterDeviceForPush(FirebaseInitializer.FcmToken));
                    }

                    appManager.HideAllAuthPanels();
                    appManager.HidePopup(AppManager.UIPopup.PromoCode);
                }
                else
                {
                    Debug.LogError(
                        "[ПРОВЕРКА ТОКЕНА] Ошибка: 'session_token' не найден в ответе. Возвращаемся к логину.");
                    appManager.SwitchToPanel(AppManager.UIPanel.Login);
                }
            }
            else
            {
                Debug.LogError(
                    $"[ПРОВЕРКА ТОКЕНА] Ошибка: {request.error}\nТело ответа: {request.downloadHandler.text}");
                UINotificationService.Instance.ShowError(request.downloadHandler.text);
                appManager.SwitchToPanel(AppManager.UIPanel.Login);
            }
        }
    }
}