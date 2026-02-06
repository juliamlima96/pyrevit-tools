# -*- coding: utf-8 -*-
from pyrevit import revit, DB, forms
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInParameter, ElementId, BuiltInCategory, Transaction
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
    forms.alert("No category was selected", title="Cancelled")
else:
    categoria_escolhida = categoria_opcoes[categoria_escolhida_nome]

    # Obter nível da vista ativa
    active_view = revit.doc.ActiveView

    if not hasattr(active_view, "GenLevel") or active_view.GenLevel is None:
        forms.alert("The current view is not associated with a level. Please open a floor plan that is associated with the level you wish to check.", title="Level Association Error")
    else:
        active_view_level = revit.doc.GetElement(active_view.GenLevel.Id)

        # Coletar elementos da categoria na vista ativa
        elementos = FilteredElementCollector(revit.doc, active_view.Id) \
            .OfCategory(categoria_escolhida) \
            .WhereElementIsNotElementType() \
            .ToElements()

        corrigidos = []

        t = Transaction(revit.doc, "Corrigir níveis")
        t.Start()
        try:
            for elemento in elementos:
                level_param = elemento.get_Parameter(BuiltInParameter.INSTANCE_SCHEDULE_ONLY_LEVEL_PARAM)
                if level_param is None or not level_param.HasValue:
                    level_param = elemento.get_Parameter(BuiltInParameter.FAMILY_LEVEL_PARAM)

                if level_param and not level_param.IsReadOnly:
                    current_level_id = level_param.AsElementId()
                    if current_level_id != active_view_level.Id:
                        level_param.Set(active_view_level.Id)
                        corrigidos.append(elemento)
            t.Commit()
        except Exception as e:
            t.RollBack()
            forms.alert("An error occurred while attempting to check the levels: {}".format(e), title="Error")

        if corrigidos:
            ids = List[ElementId]([e.Id for e in corrigidos])
            revit.uidoc.Selection.SetElementIds(ids)
            forms.alert("{} elements have been corrected to match the level of the current view.".format(len(corrigidos)), title="Level Correction Successful", warn_icon=False)
        else:
            forms.alert("All category elements in the current view are correctly assigned to the correct level.", title="No Corrections Needed", warn_icon=False)