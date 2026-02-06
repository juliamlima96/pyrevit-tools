# -*- coding: utf-8 -*-

from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import TaskDialog
from pyrevit import script,forms

output = script.get_output()
doc = __revit__.ActiveUIDocument.Document

#WORKSHARED DOCUMENT?
if not doc.IsWorkshared:
    TaskDialog.Show("Erro", "This project is not workshared.")
    script.exit()

#COLLECT WORKSETS
all_worksets = list(FilteredWorksetCollector(doc).OfKind(WorksetKind.UserWorkset).ToWorksets())
workset_names = sorted(all_worksets, key=lambda ws: ws.Name)
select_workset = forms.SelectFromList.show(workset_names, name_attr="Name", multiselect=False,
                                           title= "Select Workset")


if not select_workset:
    forms.alert("No workset was selected.")
    script.exit()

#COLLECT CATEGORIES
all_categories = doc.Settings.Categories
model_categories = [
    cat for cat in all_categories
    if cat.CategoryType == CategoryType.Model
]
family_categories = sorted(model_categories, key=lambda fm: fm.Name)
select_categories = forms.SelectFromList.show(family_categories, name_attr="Name", multiselect = True,
                                              title="Select Categories")

if not select_categories:
    forms.alert("No category was selected.")
    script.exit()

#COLLECT INSTANCES
instances = []
for cat in select_categories:
    elems = FilteredElementCollector(doc).WherePasses(ElementCategoryFilter(cat.Id)).WhereElementIsNotElementType().ToElements()
    instances.extend(elems)


#TRANSACTION
t = Transaction(doc, "Assign Workset")
t.Start()
count = 0

for el in instances:
    param = el.get_Parameter(BuiltInParameter.ELEM_PARTITION_PARAM)
    if param and not param.IsReadOnly and param.AsInteger() != select_workset.Id.IntegerValue:
        try:
            param.Set(select_workset.Id.IntegerValue)
            count += 1
        except Exception as ex:
            output.print_md("Falha no elemento Id {} | {} | {}".format(el.Id.IntegerValue, el.GetType().Name, ex))

t.Commit()

forms.alert("{} elements moved to the workset {}".format(count, select_workset.Name))