# -*- coding: utf-8 -*-
import clr
clr.AddReference('RevitServices')
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')

from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import TaskDialog
from RevitServices.Persistence import DocumentManager
from collections import defaultdict

doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument

# Mapeamento de categorias para sufixos de workset
category_workset_map = {
    BuiltInCategory.OST_PlumbingFixtures: "Plumbing Fixture",
    BuiltInCategory.OST_Ceilings: "Ceilings",
    BuiltInCategory.OST_SpecialityEquipment: "Ceilings",
    BuiltInCategory.OST_Doors: "Doors and Openings",
    BuiltInCategory.OST_Windows: "Doors and Openings",
    BuiltInCategory.OST_ElectricalFixtures: "Small Power",
    BuiltInCategory.OST_Floors: "Floors",
    BuiltInCategory.OST_Furniture: "Furniture + Equipment",
    BuiltInCategory.OST_Casework: "Joinery",  # padrão, se não for H+A_TEC
    BuiltInCategory.OST_Levels: "Shared Levels + Grids",
    BuiltInCategory.OST_Grids: "Shared Levels + Grids",
    BuiltInCategory.OST_Rooms: "Rooms&Areas",
    BuiltInCategory.OST_Areas: "Rooms&Areas",
    BuiltInCategory.OST_Walls: "Partitions",  # <- vai ser substituído por regra especial
    BuiltInCategory.OST_Reveals: "Finishes",   
    BuiltInCategory.OST_CLines: "Groups (temp)"
}

allowed_category_ids = [ElementId(bic) for bic in category_workset_map.keys()]

# Mapear nomes de categoria para sufixos
category_name_to_suffix = {}
for bic, suffix in category_workset_map.items():
    cat = doc.Settings.Categories.get_Item(bic)
    if cat:  # só adiciona se realmente existir no documento
        category_name_to_suffix[cat.Name] = suffix

# Inverso: sufixo -> BuiltInCategory
suffix_to_categories = defaultdict(list)
for bic, suffix in category_workset_map.items():
    suffix_to_categories[suffix].append(bic)

# Coleta todos os worksets do projeto
worksets = list(FilteredWorksetCollector(doc))
matching_worksets = [ws for ws in worksets if any(ws.Name.endswith(suffix) for suffix in suffix_to_categories)]

# Mapeia sufixos para Workset real
workset_dict = {}
for ws in matching_worksets:
    for suffix in suffix_to_categories:
        if ws.Name.endswith(suffix):
            workset_dict[suffix] = ws
            break

# Adiciona manualmente o Placeholder MEP
placeholder_mep_ws = next((ws for ws in worksets if ws.Name.endswith("Placeholder MEP")), None)
if placeholder_mep_ws:
    workset_dict["Placeholder MEP"] = placeholder_mep_ws

# Inicia transação
t = Transaction(doc, "Update Groups Worksets")
t.Start()

try:
    groups = FilteredElementCollector(doc).OfClass(Group).ToElements()

    for group in groups:
        if group.Name.startswith("Array Group"):
            continue

        category_counts = defaultdict(int)
        casework_family_names = []
        has_wall = False
        has_reveal = False

        # Conta categorias + coleta nomes das famílias de Casework
        for elem_id in group.GetMemberIds():
            elem = doc.GetElement(elem_id)
            if elem is None or elem.Category is None:
                continue
            if elem.Category.Id not in allowed_category_ids:
                continue
            if elem.Category.CategoryType != CategoryType.Model:
                continue

            cat_name = elem.Category.Name
            category_counts[cat_name] += 1

            # Flag para Walls e Reveals
            if elem.Category.BuiltInCategory == BuiltInCategory.OST_Walls:
                has_wall = True
            if elem.Category.BuiltInCategory == BuiltInCategory.OST_Reveals:
                has_reveal = True

            # Se for casework, pega o nome da família
            if cat_name == "Casework":
                family = elem.Document.GetElement(elem.GetTypeId()).Family
                if family:
                    casework_family_names.append(family.Name)

        if category_counts:
            dominant_category = max(category_counts, key=category_counts.get)
            count_dominant = category_counts[dominant_category]

            # --- regra especial para Walls ---
            if has_wall:
                if has_reveal:
                    suffix = "Finishes"
                else:
                    suffix = "Partitions"

            # --- regra especial para Casework ---
            elif dominant_category == "Casework":
                count_hatec = sum(1 for name in casework_family_names if "TEC" in name)
                if count_hatec > len(casework_family_names) / 2.0:
                    suffix = "Placeholder MEP"
                else:
                    suffix = "Joinery"

            # --- regra normal para os demais ---
            else:
                suffix = category_name_to_suffix.get(dominant_category, None)

            # Aplica o workset
            if suffix and suffix in workset_dict:
                target_workset = workset_dict[suffix]
                try:
                    group.get_Parameter(BuiltInParameter.ELEM_PARTITION_PARAM).Set(target_workset.Id.IntegerValue)
                    print("Group '{}' updated to workset '{}' based in '{}'.".format(
                        group.Name, target_workset.Name,
                        "Wall and Reveal Count" if has_wall else dominant_category
                    ))
                except Exception as e:
                    print("⚠️ Error updating the group's workset '{}': {}".format(group.Name, e))
            else:
                print("⚠️ Group '{}' without correspondent workset to '{}' category.".format(
                    group.Name, dominant_category))
        else:
            print("⚠️ Group '{}' — no valid category found.".format(group.Name))

    t.Commit()
except Exception as e:
    print("❌ Error during transaction: {}".format(e))
    t.RollBack()