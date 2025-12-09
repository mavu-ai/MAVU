using UnityEngine;
using System.Runtime.InteropServices;

public class iOSAudioFix : MonoBehaviour
{
#if UNITY_IOS && !UNITY_EDITOR
        [DllImport("__Internal")]
        private static extern void SetiOSAudioPlayback();
#endif

    void Awake()
    {
        RestoreAudioSession();
    }

    void OnApplicationFocus(bool hasFocus)
    {
        if (hasFocus)
        {
            RestoreAudioSession();
        }
    }
    
    public static void RestoreAudioSession()
    {
#if UNITY_IOS && !UNITY_EDITOR
            Debug.Log("[iOSAudioFix] Restoring audio session...");
            SetiOSAudioPlayback();
#endif
    }
}