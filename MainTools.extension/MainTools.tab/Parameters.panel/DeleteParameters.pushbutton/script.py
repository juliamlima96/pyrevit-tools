# -*- coding: utf-8 -*-
import clr
clr.AddReference("RevitAPI")
clr.AddReference("RevitServices")

from Autodesk.Revit.DB import *  
from pyrevit import script,forms

app    = __revit__.Application
uidoc  = __revit__.ActiveUIDocument
doc    = __revit__.ActiveUIDocument.Document



#collect elements
elements_doc = FilteredElementCollector(doc).OfClass(FamilySymbol).ToElements()

#categories
categories = set()

for e in elements_doc:
    if e.Category:
        categories.add(e.Category.Name)

categories = sorted(categories)

#select category
select_category = forms.SelectFromList.show(categories, title="Select Category to Delete Values")
if not select_category:
    script.exit()

#get elements of that category
category_elems = [e for e in elements_doc if e.Category and e.Category.Name == select_category]

#list elements
final_elems = []
for e in category_elems:
    #fam_name = e.Family.Name if e.Family else "<sem família>"
    #type_name = Element.Name.GetValue(e)
    final_elems.append((e))

#get parameters
params = set()
for e in final_elems:
    for p in e.Parameters:
        if p and (not p.IsReadOnly) and (p.StorageType == StorageType.String):
            params.add((e.Family.Name, Element.Name.GetValue(e), p.Definition.Name, p.AsString()))

unique_params = set([p[2] for p in params])
unique_params = sorted(unique_params)

#select parameters
select_params = forms.SelectFromList.show(unique_params, title="Select Parameters to Cleared", multiselect=True)
if not select_params:
    script.exit()

#clear parameters
t = Transaction(doc, "Clear Parameters")
t.Start()

cleared = 0
skipped = 0

for e in final_elems:
    for p in select_params:
        param_name = p
        param = e.LookupParameter(param_name)
        if param and param.HasValue:

            try:
                param.Set("")
                cleared += 1
            except Exception as ex:
                print("Failed to clear parameter '{}' in family '{}': {}".format(param_name, e.Family.Name, ex))
                skipped += 1

t.Commit()

#test print
print("Categories: ")
print(select_category)

print("\nsource Document: ")
print(doc.Title)

print("\nElements and Parameters: ")
for p in select_params:
    print(" - {}".format(p))

print("\nCleared: {}".format(cleared))
print("Skipped: {}".format(skipped))





    
