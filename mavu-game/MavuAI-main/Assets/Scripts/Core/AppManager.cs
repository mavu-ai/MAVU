using System.Web;
using Scripts;
using TMPro;
using UnityEngine;
using UnityEngine.UI;


public class AppManager : Singleton<AppManager>
{
    [Header("Ключевые настройки API")]
    [Tooltip("Базовый URL вашего API. Например: https://api.mavu.app")]
    [SerializeField]
    private string baseUrl = "https://api.mavu.app/api/v1";

    [Header("Окна UI")] [Tooltip("Самая первая панель с кнопками 'Войти' и 'Регистрация'")] [SerializeField]
    private GameObject startPanel;

    [Tooltip("Панель с UI для регистрации")] [SerializeField]
    private GameObject registrationPanel;

    [Tooltip("Панель с UI для входа")] [SerializeField]
    private GameObject loginPanel;

    [Tooltip("Панель, которая показывается после отправки письма")] [SerializeField]
    private GameObject waitingForEmailPanel;

    [SerializeField] private GameObject mainPanel;
    [SerializeField] private GameObject avatarPanel;

    [Header("UI для регистрации")] [Tooltip("Поле для ввода email при РЕГИСТРАЦИИ")]
    public TMP_InputField registerEmailInputField;
    [Header("UI для привязки Email")]
    [Tooltip("Поле для ввода email для привязки к аккаунту")]
    public TMP_InputField attachEmailInputField;

    [Tooltip("Кнопка 'Привязать Email'")]
    public Button attachEmailButton;

    [Tooltip("Кнопка 'Зарегистрироваться'")]
    public Button registerButton;

    [Header("UI для настроек профиля")] [Tooltip("Поле для ввода нового имени")]
    public TMP_InputField nameInputField; // Это поле теперь для смены имени

    [Tooltip("Кнопка 'Сохранить' в настройках профиля")]
    public Button updateSettingsButton;

    [Header("UI для промокодов")] [Tooltip("Поле для ввода промокода")]
    public TMP_InputField promoCodeInputField;

    [Header("UI для входа")] [Tooltip("Поле для ввода email при ВХОДЕ")]
    public TMP_InputField loginEmailInputField;

    [Tooltip("Кнопка 'Войти'")] public Button loginButton;

    [Header("Окна UI (Попапы)")]
    [Tooltip("Панель для ввода промокода (поверх MainApp)")]
    [SerializeField] private GameObject promoCodePopup;

    public enum UIPanel
    {
        Start,
        Register,
        Login,
        WaitingForEmail,
        MainApp, // Это наша "главная" сцена с аватаром
    }

    public enum UIPopup
    {
        None,
        PromoCode
    }
    private void OnEnable()
    {
        Application.deepLinkActivated += OnDeepLinkActivated;
    }

    private void OnDisable()
    {
        Application.deepLinkActivated -= OnDeepLinkActivated;
    }

    private void Awake()
    {
        QualitySettings.vSyncCount = 0;
        Application.targetFrameRate = 60;
        if (AuthService.Instance != null) AuthService.Instance.Init(this);
        if (ChatService.Instance != null)
        {
            ChatService.Instance.Init(this);
            // Подписываемся на событие из ChatService
            ChatService.Instance.OnEmailAttachAvailable += EnableAttachEmailButton;
        }
        if (attachEmailButton != null)
        {
            attachEmailButton.interactable = false;
        }
        if (UserProfileService.Instance != null) UserProfileService.Instance.Init(this);
        if (NotificationService.Instance != null) NotificationService.Instance.Init(this);
    }

    private void Start()
    {
        AuthService.Instance.LoadSessionToken();
        StartCoroutine(AuthService.Instance.CheckSessionTokenOnStart());
        if (!string.IsNullOrEmpty(Application.absoluteURL))
        {
            OnDeepLinkActivated(Application.absoluteURL);
        }
    }

    private void OnDeepLinkActivated(string url)
    {
        Debug.Log($"[DeepLink] Приложение активировано по ссылке: {url}");

        try
        {
            System.Uri uri = new System.Uri(url);
            var queryParams = HttpUtility.ParseQueryString(uri.Query);
            string token = queryParams["token"];

            if (string.IsNullOrEmpty(token))
            {
                Debug.LogError("[DeepLink] Токен в ссылке не найден!");
                return;
            }

            if (uri.AbsolutePath.Contains("/verify-email/"))
            {
                Debug.Log($"[DeepLink] Обнаружен токен подтверждения регистрации: {token}");
                StartCoroutine(AuthService.Instance.VerifyRegistrationEmail(token));
            }
            else if (uri.AbsolutePath.Contains("/login-verify/"))
            {
                Debug.Log($"[DeepLink] Обнаружен токен для входа: {token}");
                StartCoroutine(AuthService.Instance.VerifyLoginAndGetSessionToken(token));
            }
        }
        catch (System.Exception e)
        {
            Debug.LogError($"[DeepLink] Ошибка парсинга URL: {e.Message}");
        }
    }
    public void EnableAttachEmailButton()
    {
        if (attachEmailButton != null)
        {
            attachEmailButton.interactable = true;
        }
    }

    public void TryEntry(string url) //дебажный вход, для отладки в Unity
    {
        Debug.Log($"[DeepLink] Приложение активировано по ссылке: {url}");

        try
        {
            System.Uri uri = new System.Uri(url);
            var queryParams = HttpUtility.ParseQueryString(uri.Query);
            string token = queryParams["token"];

            if (string.IsNullOrEmpty(token))
            {
                Debug.LogError("[DeepLink] Токен в ссылке не найден!");
                return;
            }

            if (uri.AbsolutePath.Contains("/verify-email/"))
            {
                Debug.Log($"[DeepLink] Обнаружен токен подтверждения регистрации: {token}");
                StartCoroutine(AuthService.Instance.VerifyRegistrationEmail(token));
            }
            else if (uri.AbsolutePath.Contains("/login-verify/"))
            {
                Debug.Log($"[DeepLink] Обнаружен токен для входа: {token}");
                StartCoroutine(AuthService.Instance.VerifyLoginAndGetSessionToken(token));
            }
        }
        catch (System.Exception e)
        {
            Debug.LogError($"[DeepLink] Ошибка парсинга URL: {e.Message}");
        }
    }
    
    public void OnAttachEmailPressed()
    {
        AuthService.Instance.TryAttachEmail();
    }


    public void OnLoginButtonPressed()
    {
        AuthService.Instance.TryLogin();
    }

    public void OnActivatePromoCodePressed()
    {
        string promoCode = promoCodeInputField.text.Trim();
        if (string.IsNullOrWhiteSpace(promoCode))
        {
            Debug.LogError("Ошибка: Поле промокода не может быть пустым.");
            UINotificationService.Instance.ShowError("Empty Field!");
            return;
        }
        
        StartCoroutine(UserProfileService.Instance.LoginWithPromoCode(promoCode));
    }
    
    public void OnSendChatMessage(string _message)
    {
        string message = _message;
        if (string.IsNullOrWhiteSpace(message))
        {
            Debug.LogError("Сообщение не может быть пустым.");
            return;
        }

        if (string.IsNullOrEmpty(AuthService.Instance.SessionToken))
        {
            Debug.LogError("Ошибка: Вы не авторизованы. Сначала войдите в систему.");
            return;
        }

        Debug.Log(message);
    }


    public void ShowMainPanel()
    {
        SwitchToPanel(UIPanel.MainApp);
    }
    
    public void ShowMainPanelAndPromo()
    {
        SwitchToPanel(UIPanel.MainApp);
        if (AuthService.Instance.SessionToken != null)
        {
            return;
        }
        ShowPopup(UIPopup.PromoCode);
    }

    public void ShowLoginPanel()
    {
        SwitchToPanel(UIPanel.Login);
        HidePopup(UIPopup.PromoCode);
    }
    
    public void ShowRegisterPanel()
    {
        SwitchToPanel(UIPanel.Register);
    }
    public void SwitchToPanel(UIPanel panelKey)
    {
        if (startPanel != null) startPanel.SetActive(false);
        if (registrationPanel != null) registrationPanel.SetActive(false);
        if (loginPanel != null) loginPanel.SetActive(false);
        if (waitingForEmailPanel != null) waitingForEmailPanel.SetActive(false);
        if (mainPanel != null) mainPanel.SetActive(false);
        if (avatarPanel != null) avatarPanel.SetActive(false);

        switch (panelKey)
        {
            case UIPanel.Start:
                if (startPanel != null) startPanel.SetActive(true);
                break;
            case UIPanel.Register:
                if (registrationPanel != null) registrationPanel.SetActive(true);
                break;
            case UIPanel.Login:
                if (loginPanel != null) loginPanel.SetActive(true);
                break;
            case UIPanel.WaitingForEmail:
                if (waitingForEmailPanel != null) waitingForEmailPanel.SetActive(true);
                break;
            case UIPanel.MainApp:
                if (mainPanel != null) mainPanel.SetActive(true);
                if (avatarPanel != null) avatarPanel.SetActive(true);
                break;
        }
    }

    public void HideAllAuthPanels()
    {
        SwitchToPanel(UIPanel.MainApp);
    }

    
    public void ShowPopup(UIPopup popupKey)
    {
        switch (popupKey)
        {
            case UIPopup.PromoCode:
                if (promoCodePopup != null) promoCodePopup.SetActive(true);
                break;
        }
    }

    public void HidePopup(UIPopup popupKey)
    {
        switch (popupKey)
        {
            case UIPopup.PromoCode:
                if (promoCodePopup != null) promoCodePopup.SetActive(false);
                break;
        }
    }

    public void OnRegisterButtonPressed()
    {
        AuthService.Instance.TryRegister();
    }
}