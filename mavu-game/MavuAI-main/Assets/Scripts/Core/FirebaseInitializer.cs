using UnityEngine;
using Firebase.Extensions;

public class FirebaseInitializer : MonoBehaviour
{
    public static string FcmToken { get; private set; }

    void Start()
    {
        Firebase.FirebaseApp.CheckAndFixDependenciesAsync().ContinueWithOnMainThread(task => {
            
            var dependencyStatus = task.Result;
            if (dependencyStatus == Firebase.DependencyStatus.Available)
            {
                Debug.Log("Firebase готов к работе!");
                GetFirebaseToken();
            }
            else
            {
                Debug.LogError($"Не удалось разрешить все зависимости Firebase: {dependencyStatus}");
            }
        });
    }

    private void GetFirebaseToken()
    {
        Firebase.Messaging.FirebaseMessaging.GetTokenAsync().ContinueWithOnMainThread(task =>
        {
            if (task.IsFaulted || task.IsCanceled)
            {
                Debug.LogError("Не удалось получить Firebase-токен: " + task.Exception);
                return;
            }

            FcmToken = task.Result;
            Debug.Log("Firebase Token получен и сохранен: " + FcmToken);
        });
    }
}