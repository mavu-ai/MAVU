using System.Collections.Generic;

namespace Scripts.Models
{
    [System.Serializable]
    public class SendVerificationEmailRequest
    {
        public string new_email;
    }
    [System.Serializable]
    public class UpdateSettingsRequestData
    {
        public string name;
    
        public int age;
    }
    
    [System.Serializable]
    public class PromoCodeLoginRequestData
    {
        public string promo_code; 
    }
    
    [System.Serializable]
    public class UserSettingsData
    {
        public string name;
        public int age;
        public string gender;
    }
    
    [System.Serializable]
    public class RegisterRequestData
    {
        public string email;
        public UserSettingsData settings;
    }
    
    [System.Serializable]
    public class LoginRequestData
    {
        public string email;
    }
    
    [System.Serializable]
    public class RegisterResponse
    {
        public int user_id;
        public string session_token;
        public string status;
        public string message;
    }
    
    [System.Serializable]
    public class PromoCodeRequestData
    {
        public string code;
    }
    
    [System.Serializable]
    public class ChatRequestData
    {
        public string message;
        public int skin_id;
    }
    
    [System.Serializable]
    public class StreamChunk
    {
        public string c;
        public bool f;
    }
    
    [System.Serializable]
    public class TTSRequestData
    {
        public string text;
    }
    
    [System.Serializable]
    public class TTSResponseData
    {
        public List<string> urls;
    }
    
    [System.Serializable]
    public class FCMDeviceRequest
    {
        public string device_id;
        public string registration_id;
        public string device_type;
    }
    
    [System.Serializable]
    public class TTSResponse
    {
        public string audio_url;
        public string text;
        public bool success;
        public string error;
    }
    
    [System.Serializable]
    public class TTSRequest
    {
        public string message;
        public int skin_id;
        public string language;
    }
}