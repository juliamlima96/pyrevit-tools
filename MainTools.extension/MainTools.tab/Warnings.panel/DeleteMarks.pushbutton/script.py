# -*- coding: utf-8 -*-
import clr
clr.AddReference("RevitAPI")
clr.AddReference("RevitServices")

from Autodesk.Revit.DB import *  
from pyrevit import script,forms

app    = __revit__.Application
uidoc  = __revit__.ActiveUIDocument
doc    = __revit__.ActiveUIDocument.Document #type:Document


#All Marks
mark = ElementId(BuiltInParameter.ALL_MODEL_MARK) 
mark_param = ParameterValueProvider(mark) 

#Evaluator and Value 
evaluator = FilterStringEquals() 
value = "" 

#Rule 
rvt_year = int(app.VersionNumber) 
if rvt_year >= 2023: 
    rule_empty_mark = FilterStringRule(mark_param, evaluator, value) 
else: 
    rule_empty_mark = FilterStringRule(mark_param, evaluator, value, False) 
    
mark_not_empty = ElementParameterFilter(rule_empty_mark, True) 

all_elements = (FilteredElementCollector(doc).WherePasses(mark_not_empty).WhereElementIsNotElementType().ToElements()) 

to_be_cleaned = [] 
for e in all_elements: 
    if e.GetType().Name == "Material":
        continue 
    else: to_be_cleaned.append(e)

if not to_be_cleaned:
    print("Nothing to clean.")
    script.exit()

forms.alert("This will clear the Mark parameter for {} elements, excepting materials. Do you want to continue?".format(len(to_be_cleaned)), title="Clear Marks", yes=True, no=True)

t = Transaction(doc, "Clear Marks")
t.Start()

changed_count = 0

for e in to_be_cleaned:
    p = e.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)

    if p and not p.IsReadOnly and p.AsString():
        p.Set("")
        changed_count += 1

t.Commit()

forms.alert("Done! Cleared Mark for {} elements.".format(changed_count), title="Clear Marks", ok=True)
    
#print("Elements:") 
#for e in to_be_cleaned: 
#    print(" - {} ({}, {})".format(e.Name, e.Category.Name, e.get_Parameter(BuiltInParameter.ALL_MODEL_MARK).AsString()))









    
