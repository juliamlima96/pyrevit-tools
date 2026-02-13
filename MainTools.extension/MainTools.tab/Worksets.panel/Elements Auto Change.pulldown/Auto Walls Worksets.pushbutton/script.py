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

for ws in worksets:
    name = ws.Name.lower()
    if "finishes" in name and workset_finishes is None:
        workset_finishes = ws
    elif "partitions" in name and workset_partitions is None:
        workset_partitions = ws
    elif "ceilings" in name and workset_ceilings is None:
        workset_ceilings = ws
    elif "placeholder arc" in name and workset_placeholderARC is None:
        workset_placeholderARC = ws

if not workset_finishes or not workset_partitions or not workset_ceilings or not workset_placeholderARC:
    msg = "Missing required worksets:\n"
    if not workset_finishes: msg += "Finishes\n"
    if not workset_partitions: msg += "Partitions\n"
    if not workset_ceilings: msg += "Ceilings\n"
    if not workset_placeholderARC: msg += "Placeholder ARC\n"
    TaskDialog.Show("Erro", msg)
    raise Exception("Missing required worksets.")

# Coletar paredes
walls = FilteredElementCollector(doc)\
    .OfCategory(BuiltInCategory.OST_Walls)\
    .WhereElementIsNotElementType()\
    .ToElements()

# Prefixos (em MAIÚSCULAS porque vamos comparar com name_upper)
FINISHES_PREFIXES   = ("H+A_ID_WLF", "H+A_COVERING_WALLFINISH", "ATR_ID_COVERING_WALLFINISH")
PARTITIONS_PREFIXES = ("H+A_ID_WAL", "H+A_WALL", "ATR_ID_WALL")
CEILINGS_PREFIXES   = ("H+A_ID_CEI", "H+A_COVERING_CEILING", "ATR_ID_COVERING_CEILING")
PLACEHOLDER_PREFIXES = ("H+A_COVERING_EXTERIORCLADDING", "ATR_ID_COVERING_EXTERIORCLADDING")

t = Transaction(doc, "Update wall worksets")
t.Start()

count = 0
param_workset = BuiltInParameter.ELEM_PARTITION_PARAM

for wall in walls:
    try:
        # Pular Curtain Walls de forma robusta
        wt = wall.WallType
        if wt is not None and wt.Kind == WallKind.Curtain:
            continue

        name_upper = wall.Name.upper()
        current_workset_id = wall.WorksetId

        # FINISHES
        if name_upper.startswith(FINISHES_PREFIXES):
            if current_workset_id != workset_finishes.Id:
                wall.get_Parameter(param_workset).Set(workset_finishes.Id.IntegerValue)
                count += 1

        # PARTITIONS
        elif name_upper.startswith(PARTITIONS_PREFIXES):
            if current_workset_id != workset_partitions.Id:
                wall.get_Parameter(param_workset).Set(workset_partitions.Id.IntegerValue)
                count += 1

        # CEILINGS
        elif name_upper.startswith(CEILINGS_PREFIXES):
            if current_workset_id != workset_ceilings.Id:
                wall.get_Parameter(param_workset).Set(workset_ceilings.Id.IntegerValue)
                count += 1
        # PLACEHOLDER ID
        elif name_upper.startswith(PLACEHOLDER_PREFIXES):
            if current_workset_id != workset_placeholderARC.Id:
                wall.get_Parameter(param_workset).Set(workset_placeholderARC.Id.IntegerValue)
                count += 1

    except Exception as e:
        # Se quiser debugar: TaskDialog.Show("Erro", str(e))
        pass

t.Commit()

TaskDialog.Show("Task Completed", "Updated Walls (w/o curtain walls): {}".format(count))
