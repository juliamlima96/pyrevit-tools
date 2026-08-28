# -*- coding: utf-8 -*-
import clr
clr.AddReference("RevitAPI")
clr.AddReference("RevitServices")

import sys
from Autodesk.Revit.DB import *
from RevitServices.Persistence import DocumentManager
from Autodesk.Revit.UI import TaskDialog

# pyRevit: obter o doc corretamente
doc = __revit__.ActiveUIDocument.Document

if not doc.IsWorkshared:
    TaskDialog.Show("Erro", "This project is not workshared.")
    sys.exit()

# Coletar worksets de usuário
worksets = FilteredWorksetCollector(doc).OfKind(WorksetKind.UserWorkset).ToWorksets()

workset_finishes = None
workset_partitions = None
workset_ceilings = None
workset_placeholderARC = None
workset_PartitionsWC = None

for ws in worksets:
    name = ws.Name.lower()
    if "finishes" in name and workset_finishes is None:
        workset_finishes = ws
    elif "partitions" in name and workset_partitions is None:
        workset_partitions = ws
    elif "ceilings" in name and workset_ceilings is None:
        workset_ceilings = ws

missing_worksets = []

if not workset_finishes:
    missing_worksets.append("Finishes")
if not workset_partitions:
    missing_worksets.append("Partitions")
if not workset_ceilings:
    missing_worksets.append("Ceilings")

# Coletar paredes
walls = FilteredElementCollector(doc)\
    .OfClass(Wall)\
    .ToElements()

# Prefixos (em MAIÚSCULAS porque vamos comparar com name_upper)
FINISHES_KEYWORDS   = ("WLF","FINISH","H+A_ID_")
PARTITIONS_KEYWORDS = ("WAL", "WALL","H+A_AR_")
CEILINGS_KEYWORDS   = ("CEI", "BULKHEAD")

param_workset = BuiltInParameter.ELEM_PARTITION_PARAM

t = Transaction(doc, "Update wall worksets")
t.Start()

count = 0

try:
    for wall in walls:
        # Pular Curtain Walls de forma robusta
        wt = wall.WallType
        if wt is not None and wt.Kind == WallKind.Curtain:
            continue

        name_upper = wall.Name.upper()
        current_workset_id = wall.WorksetId

        target_workset = None         
        
        # FINISHES
        if any(keyword in name_upper for keyword in FINISHES_KEYWORDS):
            target_workset = workset_finishes

        # CEILINGS
        elif any(keyword in name_upper for keyword in CEILINGS_KEYWORDS):
            target_workset = workset_ceilings
        
        #PARTITIONS
        else:
            if any(keyword in name_upper for keyword in PARTITIONS_KEYWORDS):
                target_workset = workset_partitions

        if target_workset is None:
            continue

        if current_workset_id == target_workset.Id:
            continue

        p = wall.get_Parameter(param_workset)

        if p and not p.IsReadOnly:
            p.Set(target_workset.Id.IntegerValue)
            count += 1

    t.Commit()

except Exception as e:
    t.RollBack()
    TaskDialog.Show("Error", "An error occurred:\n{}".format(str(e)))
    sys.exit()

msg = "{} walls were updated.".format(count)

if missing_worksets:
    msg += "\n\nThe following worksets were not found:\n- "
    msg += "\n- ".join(missing_worksets)

TaskDialog.Show("Task Completed", msg)
