using System;
using UnityEngine;
using System.Collections;
using Live2D.Cubism.Core;
using Live2D.Cubism.Framework.Expression;
using Live2D.Cubism.Framework.Motion;
using Live2D.Cubism.Samples.OriginalWorkflow.Expression;
using Unity.VisualScripting;
using UnityEngine.Serialization; 

public class ManualAnimationPlayer : MonoBehaviour
{
    [FormerlySerializedAs("_motionController")]
    [Header("Ссылки")]
    [Tooltip("Ссылка на компонент, который проигрывает анимации Cubism")]
    [SerializeField] private CubismMotionController motionController;

    [FormerlySerializedAs("_idleClip")]
    [Header("Анимационные клипы")]
    [Tooltip("Анимация покоя, которая будет проигрываться по умолчанию")]
    [SerializeField] private AnimationClip idleClip;
    
    [FormerlySerializedAs("_actionClipBody")]
    [FormerlySerializedAs("_actionClipA")]
    [Tooltip("Пример 'активной' анимации А")]
    [SerializeField] private AnimationClip actionClipBody;

    [FormerlySerializedAs("_actionClipHat")]
    [Tooltip("Пример 'активной' анимации B")]
    [SerializeField] private AnimationClip actionClipHat;
    
    [SerializeField] private CubismExpressionPreview expressionPreview;
    
    private Coroutine _currentAnimationCoroutine;
    private CubismExpressionController _expressionController;
    private int _startIdleExpressionId;
    private CubismModel _model;

    void Start()
    {
        _expressionController = gameObject.GetComponent<CubismExpressionController>();
        _startIdleExpressionId = _expressionController.CurrentExpressionIndex;
        PlayIdle();
    }

    void Awake()
    {
        _model = this.FindCubismModel();
    }

    private void OnEnable()
    {
        PlayIdle();
    }
    
    public void PlayIdle()
    {
        if (idleClip != null)
        {
            motionController.PlayAnimation(idleClip, isLoop: true, priority:CubismMotionPriority.PriorityForce);
            expressionPreview.ChangeExpression(_startIdleExpressionId);
        }
    }
    
    public void PlayActionThenIdle(AnimationClip clipToPlay, int id)
    {
        if (_currentAnimationCoroutine != null)
        {
            StopCoroutine(_currentAnimationCoroutine);
        }
        
        _currentAnimationCoroutine = StartCoroutine(PlaySequenceCoroutine(clipToPlay));
        expressionPreview.ChangeExpression(id);
    }
    
    private IEnumerator PlaySequenceCoroutine(AnimationClip actionClip)
    {
        motionController.PlayAnimation(actionClip, isLoop: false, priority:CubismMotionPriority.PriorityForce);
        float clipLength = actionClip.length;
        yield return new WaitForSeconds(clipLength);
        PlayIdle();
        _currentAnimationCoroutine = null;
    }
}