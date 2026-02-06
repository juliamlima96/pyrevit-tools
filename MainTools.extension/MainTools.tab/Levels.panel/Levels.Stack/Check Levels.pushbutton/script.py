# -*- coding: utf-8 -*-
from pyrevit import revit, forms
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInParameter, ElementId, BuiltInCategory, Level
from System.Collections.Generic import List

# Lista de categorias disponíveis
categoria_opcoes = {
    "Plumbing Fixtures": BuiltInCategory.OST_PlumbingFixtures,
    "Furniture": BuiltInCategory.OST_Furniture,
    "Doors": BuiltInCategory.OST_Doors,
    "Windows": BuiltInCategory.OST_Windows,
    "Generic Models": BuiltInCategory.OST_GenericModel,
    "Casework": BuiltInCategory.OST_Casework,
    "Specialty Equipment": BuiltInCategory.OST_SpecialityEquipment,
    "Electrical Fixtures": BuiltInCategory.OST_ElectricalFixtures,
}

# Seleção da categoria
categoria_escolhida_nome = forms.SelectFromList.show(
    sorted(categoria_opcoes.keys()),
    title="Choose Category",
    multiselect=False
)

if not categoria_escolhida_nome:
    forms.alert("No category was selected.", title="Cancelled")
else:
    categoria_escolhida = categoria_opcoes[categoria_escolhida_nome]

    # Nível da vista ativa
    active_view = revit.doc.ActiveView
    if not hasattr(active_view, "GenLevel") or active_view.GenLevel is None:
        forms.alert("The current view isn’t associated with a level. Please open a floor plan that’s linked to the level you want to check.", title="Invalid View")
    else:
        active_view_level = revit.doc.GetElement(active_view.GenLevel.Id)

        # Coleta elementos da categoria na vista ativa
        elementos = FilteredElementCollector(revit.doc, active_view.Id) \
            .OfCategory(categoria_escolhida) \
            .WhereElementIsNotElementType() \
            .ToElements()

        sem_nivel = []
        nivel_diferente = []

        for elemento in elementos:
            level_param = elemento.get_Parameter(BuiltInParameter.INSTANCE_SCHEDULE_ONLY_LEVEL_PARAM)
            if level_param is None or not level_param.HasValue:
                level_param = elemento.get_Parameter(BuiltInParameter.FAMILY_LEVEL_PARAM)

            if level_param is None or not level_param.HasValue:
                sem_nivel.append(elemento)
            else:
                level_id = level_param.AsElementId()
                level = revit.doc.GetElement(level_id)
                if level is None or level.Id == ElementId.InvalidElementId:
                    sem_nivel.append(elemento)
                elif active_view_level and level.Id != active_view_level.Id:
                    nivel_diferente.append(elemento)

        todos_problemas = list(set(sem_nivel + nivel_diferente))
        if todos_problemas:
            ids = List[ElementId]([e.Id for e in todos_problemas])
            revit.uidoc.Selection.SetElementIds(ids)

            msg = "{} elements were found without an assigned level, and {} with a level differing from that of the active view.".format(
                len(sem_nivel), len(nivel_diferente))
            forms.alert(msg, title="Missing Level Information", warn_icon=False)
        else:
            forms.alert("All elements of the '{}' category in the current view are assigned to the correct level.".format(
                categoria_escolhida_nome), title="All Levels Correct", warn_icon=False)
