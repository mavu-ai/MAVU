using UnityEngine;
using Live2D.Cubism.Core; 
using Live2D.Cubism.Framework;
using UnityEngine.Serialization;

public class MavuLive2DLipSync : MonoBehaviour
{
    [FormerlySerializedAs("mavuService")] [Header("Links")]
    public MavuRealtimeService MavuService;
    [SerializeField] private CubismModel model;

    [Header("Settings")]
    [Range(0.1f, 10.0f)] 
    [SerializeField] private float sensitivity = 3.0f;
    [Range(0.0f, 1.0f)]
    [SerializeField] private float smoothing = 0.1f;

    private CubismParameter _mouthOpenParam;
    private float _currentValue = 0f;

    private void Start()
    {
        if (MavuService == null) MavuService = FindObjectOfType<MavuRealtimeService>();
        if (model == null) model = GetComponent<CubismModel>();

        if (model != null)
        {
            _mouthOpenParam = model.Parameters.FindById("ParamMouthOpenY");
        }
    }

    private void LateUpdate()
    {
        if (_mouthOpenParam == null || MavuService == null) return;
        float targetVolume = MavuService.CurrentVolume;
        targetVolume *= sensitivity;
        targetVolume = Mathf.Clamp01(targetVolume);
        _currentValue = Mathf.Lerp(_currentValue, targetVolume, 1f - smoothing);
        _mouthOpenParam.Value = _currentValue;
    }
}