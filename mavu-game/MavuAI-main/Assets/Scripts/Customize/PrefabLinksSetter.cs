using System;
using Live2D.Cubism.Framework.LookAt;
using Live2D.Cubism.Framework.MouthMovement;
using Scripts;
using UnityEngine;
using UnityEngine.UI;

namespace Scripts.Customize
{


    public class PrefabLinksSetter : Singleton<PrefabLinksSetter>
    {
        [SerializeField] private GameObject target;
        [SerializeField] private GameObject center;
        [SerializeField] private AudioSource audioSource;
        [SerializeField] private GameObject debugPrefab;
        [SerializeField] private MavuRealtimeService mavuRealtimeService;
        public Button hatClick, bodyClick, faceClick;

        private CubismAudioMouthInput _activeLipsync;
        
// Этот метод будет вызываться при создании нового аватара
        public void InitPrefab(GameObject prefab)
        {
            prefab.GetComponent<CubismLookController>().Center = center.transform;
            prefab.GetComponent<CubismLookController>().Target = target;
            prefab.GetComponent<CubismAudioMouthInput>().AudioInput = audioSource;
            //_activeLipsync = prefab.GetComponent<CubismAudioMouthInput>();
            prefab.GetComponent<MavuLive2DLipSync>().MavuService = mavuRealtimeService;
            
            //_activeLipsync.AudioInput = audioSource;
        }
        
        private void UpdateLipsyncSource(AudioSource newActiveSource)
        {
            if (_activeLipsync != null)
            {
                Debug.Log($"[PrefabLinksSetter] Обновляю источник звука для липсинка на {newActiveSource.name}");
                _activeLipsync.AudioInput = newActiveSource;
            }
        }
        
    }
}
