# -*- coding: utf-8 -*-
import clr
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")

from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *
from System.Windows.Forms import (
    Application, Form, Label, ComboBox, Button, DialogResult,
    FormStartPosition, ComboBoxStyle
)
from System.Drawing import Point, Size

doc = __revit__.ActiveUIDocument.Document

# Verifica se é workshared
if not doc.IsWorkshared:
    TaskDialog.Show("Error", "This document is not workshared.")
    raise SystemExit

# Pega categorias de família válidas, ordenadas por nome
all_categories = doc.Settings.Categories
family_categories = sorted(
    [c for c in all_categories if c.AllowsBoundParameters],
    key=lambda c: c.Name
)

# Pega os worksets de usuário, ordenados por nome
worksets = sorted(
    FilteredWorksetCollector(doc).OfKind(WorksetKind.UserWorkset).ToWorksets(),
    key=lambda ws: ws.Name
)

# Interface do formulário
class WorksetForm(Form):
    def __init__(self):
        self.Text = "Assign Workset"
        self.Size = Size(400, 220)
        self.StartPosition = FormStartPosition.CenterScreen

        self.label_cat = Label()
        self.label_cat.Text = "Family Category:"
        self.label_cat.Location = Point(20, 20)
        self.label_cat.AutoSize = True  # Ensures the text stays on one line
        self.Controls.Add(self.label_cat)

        self.combo_cat = ComboBox()
        self.combo_cat.Location = Point(20, 45)
        self.combo_cat.Size = Size(340, 25)
        self.combo_cat.DropDownStyle = ComboBoxStyle.DropDownList
        for cat in family_categories:
            self.combo_cat.Items.Add(cat.Name)
        self.Controls.Add(self.combo_cat)

        self.label_ws = Label()
        self.label_ws.Text = "Workset:"
        self.label_ws.Location = Point(20, 80)
        self.label_ws.AutoSize = True  # Ensures the text stays on one line
        self.Controls.Add(self.label_ws)

        self.combo_ws = ComboBox()
        self.combo_ws.Location = Point(20, 105)
        self.combo_ws.Size = Size(340, 25)
        self.combo_ws.DropDownStyle = ComboBoxStyle.DropDownList
        for ws in worksets:
            self.combo_ws.Items.Add(ws.Name)
        self.Controls.Add(self.combo_ws)

        self.ok_button = Button()
        self.ok_button.Text = "Apply"
        self.ok_button.Location = Point(150, 140)
        self.ok_button.Click += self.apply_workset
        self.Controls.Add(self.ok_button)

    def apply_workset(self, sender, args):
        cat_index = self.combo_cat.SelectedIndex
        ws_index = self.combo_ws.SelectedIndex

        if cat_index < 0 or ws_index < 0:
            TaskDialog.Show("Error", "Please select a category and a workset.")
            return

        selected_category = family_categories[cat_index]
        selected_workset = worksets[ws_index]

        collector = FilteredElementCollector(doc)\
            .WherePasses(ElementCategoryFilter(selected_category.Id))\
            .WhereElementIsNotElementType().ToElements()

        t = Transaction(doc, "Assign Workset")
        t.Start()
        count = 0
        for el in collector:
            param = el.get_Parameter(BuiltInParameter.ELEM_PARTITION_PARAM)
            if param and not param.IsReadOnly and param.AsInteger() != selected_workset.Id.IntegerValue:
                param.Set(selected_workset.Id.IntegerValue)
                count += 1
        t.Commit()

        msg = "{0} elements moved to the workset '{1}'.".format(count, selected_workset.Name)
        TaskDialog.Show("Completed", msg)
        self.DialogResult = DialogResult.OK
        self.Close()

# Execute the form
form = WorksetForm()
Application.Run(form)
