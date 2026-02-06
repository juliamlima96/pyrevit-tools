# -*- coding: utf-8 -*-
import clr
clr.AddReference("RevitAPI")
clr.AddReference("RevitServices")

import sys
from Autodesk.Revit.DB import *
from RevitServices.Persistence import DocumentManager
from Autodesk.Revit.UI import TaskDialog

doc = __revit__.ActiveUIDocument.Document

# Verifica se o documento é workshared
if not doc.IsWorkshared:
    TaskDialog.Show("Erro", "This project is not workshared.")
    sys.exit()

# Coleta os worksets do tipo usuário
worksets = FilteredWorksetCollector(doc).OfKind(WorksetKind.UserWorkset).ToWorksets()

# Dicionário de sufixos de worksets por categoria
workset_suffix_map = {
    BuiltInCategory.OST_PlumbingFixtures: "Plumbing Fixture",
    BuiltInCategory.OST_Ceilings: "Ceilings",
    BuiltInCategory.OST_SpecialityEquipment: "Ceilings",
    BuiltInCategory.OST_Doors: "Doors and Openings",
    BuiltInCategory.OST_Windows: "Doors and Openings",
    BuiltInCategory.OST_ElectricalFixtures: "Small Power",
    BuiltInCategory.OST_Floors: "Floors",
    BuiltInCategory.OST_Furniture: "Furniture + Equipment",
    BuiltInCategory.OST_Casework: "Joinery",  # padrão
    BuiltInCategory.OST_Levels: "Shared Levels + Grids",
    BuiltInCategory.OST_Grids: "Shared Levels + Grids",
    BuiltInCategory.OST_Rooms: "Rooms&Areas",
    BuiltInCategory.OST_Areas: "Rooms&Areas",
    BuiltInCategory.OST_CLines: "Groups (temp)",
    BuiltInCategory.OST_IOSModelGroups: "Groups (temp)"
}

# Adiciona manualmente a exceção para Placeholder MEP
special_suffix = "Placeholder MEP"

# Procura os worksets desejados usando sufixo
target_worksets = {}
missing_worksets = []

# Mapeia worksets disponíveis
for cat, ws_suffix in workset_suffix_map.items():
    found = False
    for workset in worksets:
        if workset.Name.strip().endswith(ws_suffix):
            target_worksets[cat] = workset
            found = True
            break
    if not found and ws_suffix not in missing_worksets:
        missing_worksets.append(ws_suffix)

# Tenta localizar o Placeholder MEP
placeholder_ws = None
for workset in worksets:
    if workset.Name.strip().endswith(special_suffix):
        placeholder_ws = workset
        break
if not placeholder_ws:
    missing_worksets.append(special_suffix)

# Prefixos (em MAIÚSCULAS porque vamos comparar com name_upper)
SHAFTS_PREFIXES   = ("H+A_TEC", "H+A_MechanicalEquipment")

# Inicia a transação
t = Transaction(doc, "Move elements to correct workset")
t.Start()

count = 0
try:
    for cat, default_ws in target_worksets.items():
        try:
            elements = FilteredElementCollector(doc).OfCategory(cat).WhereElementIsNotElementType().ToElements()
        except:
            continue

        cat_id = Category.GetCategory(doc, cat).Id
        for el in elements:
            if not el.IsValidObject:
                continue
            if el.Category.Id != cat_id:
                continue

            param = el.get_Parameter(BuiltInParameter.ELEM_PARTITION_PARAM)
            if param and not param.IsReadOnly:
                target_ws = default_ws

                # Regras especiais para Casework com prefixo H+A_TEC
                if cat == BuiltInCategory.OST_Casework and placeholder_ws:
                    type_id = el.GetTypeId()
                    type_elem = doc.GetElement(type_id)
                    if type_elem:
                        try:
                            family = type_elem.Family
                            if family and family.Name.startswith(SHAFTS_PREFIXES):
                                target_ws = placeholder_ws
                        except:
                            pass

                param.Set(target_ws.Id.IntegerValue)
                count += 1

    t.Commit()

    msg = "{} elements were assigned to their respective worksets.".format(count)
    if missing_worksets:
        msg += "\n\nThe following workset suffixes were not matched:\n- " + "\n- ".join(missing_worksets)

    TaskDialog.Show("Result", msg)

except Exception as e:
    t.RollBack()
    TaskDialog.Show("Error", "An error occurred: {}".format(str(e)))
