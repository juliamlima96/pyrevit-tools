# -*- coding: utf-8 -*-

import clr
clr.AddReference('RevitServices')
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')

from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import TaskDialog
from RevitServices.Persistence import DocumentManager

doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument


# ============================================================
# MAPEAMENTO:
# final do nome do Group -> sufixo do Workset
# ============================================================

group_suffix_map = {
    "Joinery": "Furniture & Equipment",
    "Joineries": "Furniture & Equipment",
    "Partitions": "Partitions",
    "Placeholder": "Placeholder-ID",
    "Plumbing": "Plumbing Fixture",
    "Finishes": "Finishes"
}


# ============================================================
# COLETA OS WORKSETS
# ============================================================

worksets = list(FilteredWorksetCollector(doc))

workset_dict = {}

for ws in worksets:
    for suffix in group_suffix_map.values():

        if ws.Name.lower().endswith(suffix.lower()):
            workset_dict[suffix] = ws
            break


# ============================================================
# MOSTRA QUAIS WORKSETS FORAM ENCONTRADOS
# ============================================================

for suffix in group_suffix_map.values():

    if suffix in workset_dict:
        print("Workset encontrado: '{}' -> '{}'".format(
            suffix,
            workset_dict[suffix].Name
        ))
    else:
        print("WARNING: Workset nao encontrado para '{}'.".format(suffix))


# ============================================================
# INICIA TRANSAÇÃO
# ============================================================

t = Transaction(doc, "Update Groups Worksets")
t.Start()

try:

    groups = FilteredElementCollector(doc).OfClass(Group).ToElements()

    for group in groups:

        group_name = group.Name.strip()

        # ----------------------------------------------------
        # Ignora Array Groups
        # ----------------------------------------------------

        if group_name.startswith("Array Group"):
            continue


        # ----------------------------------------------------
        # Descobre o Workset pelo final do nome do Group
        # ----------------------------------------------------

        target_suffix = None

        for group_suffix in group_suffix_map:

            if group_name.lower().endswith(group_suffix.lower()):
                target_suffix = group_suffix
                break


        # ----------------------------------------------------
        # Se não encontrou nenhum sufixo
        # ----------------------------------------------------

        if target_suffix is None:

            print(
                "Group '{}' -> nenhum sufixo correspondente.".format(
                    group_name
                )
            )

            continue


        # ----------------------------------------------------
        # Descobre o sufixo do Workset
        # ----------------------------------------------------

        workset_suffix = group_suffix_map[target_suffix]


        # ----------------------------------------------------
        # Verifica se o Workset existe
        # ----------------------------------------------------

        if workset_suffix not in workset_dict:

            print(
                "WARNING: Group '{}' -> Workset '{}' nao encontrado.".format(
                    group_name,
                    workset_suffix
                )
            )

            continue


        target_workset = workset_dict[workset_suffix]


        # ----------------------------------------------------
        # Aplica o Workset ao Group
        # ----------------------------------------------------

        try:

            group.get_Parameter(
                BuiltInParameter.ELEM_PARTITION_PARAM
            ).Set(
                target_workset.Id.IntegerValue
            )

            print(
                "Group '{}' -> '{}'".format(
                    group_name,
                    target_workset.Name
                )
            )

        except Exception as e:

            print(
                "ERROR: Group '{}' -> {}".format(
                    group_name,
                    e
                )
            )


    t.Commit()

    print("Processo concluido.")

except Exception as e:

    t.RollBack()

    print(
        "ERROR durante a transacao: {}".format(e)
    )