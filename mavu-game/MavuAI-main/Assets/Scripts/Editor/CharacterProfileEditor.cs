using UnityEngine;
using UnityEditor;
using Live2D.Cubism.Core;
using System.Linq; // Добавлено для использования .Any()

[CustomEditor(typeof(CharacterProfile))]
public class CharacterProfileEditor : Editor
{
    // Список префиксов параметров, которые нужно игнорировать (физика, повороты головы и т.д.)
    private static readonly string[] IgnoredPrefixes = 
    { 
        "ParamAngle", 
        "ParamBodyAngle",
        "ParamPhysics", 
        //"ParamHair", 
        //"ParamBreath",
        "ParamEyeBall" // Движение зрачков тоже обычно не часть пресета
    };

    public override void OnInspectorGUI()
    {
        base.OnInspectorGUI();
        CharacterProfile profile = (CharacterProfile)target;
        EditorGUILayout.Space(20);

        if (GUILayout.Button("Сделать снимок с выбранной модели (Полный)", GUILayout.Height(40)))
        {
            SnapshotParameters(profile);
        }
    }

    private void SnapshotParameters(CharacterProfile profile)
    {
        GameObject selectedObject = Selection.activeGameObject;
        if (selectedObject == null) { Debug.LogError("Ошибка! Сначала выберите модель в иерархии."); return; }

        CubismModel model = selectedObject.GetComponent<CubismModel>();
        if (model == null) { Debug.LogError("Ошибка! Выбранный объект не является Live2D моделью."); return; }

        profile.defaultAppearance.parameterSettings.Clear();
        int savedCount = 0;
        int skippedCount = 0;

        foreach (var parameter in model.Parameters)
        {
            // ПРОВЕРКА: Если ID параметра начинается с одного из игнорируемых префиксов,
            // пропускаем его и переходим к следующему.
            if (IgnoredPrefixes.Any(prefix => parameter.Id.StartsWith(prefix)))
            {
                skippedCount++;
                continue; // Пропустить этот параметр
            }

            // УСЛОВИЕ УБРАНО: Теперь мы добавляем ВСЕ остальные параметры, независимо от их значения.
            profile.defaultAppearance.parameterSettings.Add(new ParameterSetting { parameterId = parameter.Id, value = parameter.Value });
            savedCount++;
        }

        EditorUtility.SetDirty(profile);
        Debug.Log($"Снимок параметров успешно сохранен в '{profile.name}'! Сохранено: {savedCount} параметров. Пропущено (физика): {skippedCount}.");
    }
}