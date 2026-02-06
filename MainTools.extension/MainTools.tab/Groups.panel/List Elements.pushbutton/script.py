# -*- coding: utf-8 -*-
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *
from collections import defaultdict
from pyrevit import script
output = script.get_output()

import clr

clr.AddReference('RevitServices')
from RevitServices.Persistence import DocumentManager

doc = __revit__.ActiveUIDocument.Document

collector = FilteredElementCollector(doc).OfClass(Group)

group_data = {}

for group in collector:
    group_name = group.Name
    
    # Ignore automatic Array Groups
    if group_name.startswith("Array Group"):
        continue

    group_elements = group.GetMemberIds()

    category_count = defaultdict(int)
    
    for elem_id in group_elements:
        element = doc.GetElement(elem_id)
        if (element is not None and
            element.Category is not None and
            element.Category.CategoryType == CategoryType.Model):
            
            category_name = element.Category.Name
            
            # Ignore empty categories and internal ones like <Sketch>
            if category_name and category_name.strip() != "" and not category_name.startswith("<"):
                category_count[category_name] += 1
    
    if category_count:
        group_data[group_name] = dict(category_count)
    else:
        # Debug for groups without valid categorized elements
        output.print_md("### Group: `{}` — No valid categorized elements found".format(group_name))

if group_data:
    output.print_md("## Groups and Categories Found")
    for group_name, categories in group_data.items():
        output.print_md("### Group: `{}`".format(group_name))
        for cat, count in categories.items():
            output.print_md("- **{}**: {}".format(cat, count))
        output.print_md("---")
else:
    output.print_md("No groups with categorized elements were found.")
