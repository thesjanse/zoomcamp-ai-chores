from django import forms

from chores.models import Chore


class ChoreForm(forms.ModelForm):
    class Meta:
        model = Chore
        fields = ("title", "description", "due_date")
        widgets = {
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }
