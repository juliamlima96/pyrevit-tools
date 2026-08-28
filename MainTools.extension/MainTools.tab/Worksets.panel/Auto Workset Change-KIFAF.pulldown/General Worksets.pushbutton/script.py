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
    BuiltInCategory.OST_PlumbingFixtures: "PLUMBING FIXTURES",
    BuiltInCategory.OST_Ceilings: "CEILINGS",
    BuiltInCategory.OST_SpecialityEquipment: "CEILINGS",
    BuiltInCategory.OST_Doors: "PARTITIONS AND DOORS",
    BuiltInCategory.OST_Floors: "FINISHES",
    BuiltInCategory.OST_Furniture: "FURNITURE",
    BuiltInCategory.OST_LightingFixtures: "FURNITURE",
    BuiltInCategory.OST_ElectricalEquipment: "FURNITURE",
    BuiltInCategory.OST_ElectricalFixtures: "FURNITURE",
    BuiltInCategory.OST_Casework: "CASEWORK",  # padrão
    BuiltInCategory.OST_Levels: "SHARED LEVELS AND GRIDS",
    BuiltInCategory.OST_Grids: "SHARED LEVELS AND GRIDS",
    BuiltInCategory.OST_Rooms: "ROOMS AND AREAS",
    BuiltInCategory.OST_Areas: "ROOMS AND AREAS",
    BuiltInCategory.OST_RoomSeparationLines: "ROOMS AND AREAS",
    BuiltInCategory.OST_Planting: "FURNITURE"
}

# Procura os worksets desejados usando sufixo
target_worksets = {}
missing_worksets = []

# Mapeia worksets disponíveis
for cat, ws_suffix in workset_suffix_map.items():
    found = False
    for workset in worksets:
        if workset.Name.strip().upper().endswith(ws_suffix):
            target_worksets[cat] = workset
            found = True
            break
    if not found and ws_suffix not in missing_worksets:
        missing_worksets.append(ws_suffix)

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

                # Só altera se estiver no workset errado
                if el.WorksetId != target_ws.Id:
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
