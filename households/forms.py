from django import forms

from households.models import Household


class JoinHouseholdForm(forms.Form):
    invite_code = forms.CharField(
        label="Invite code", max_length=12, strip=True
    )

    def clean_invite_code(self):
        code = self.cleaned_data["invite_code"]
        if not Household.objects.filter(invite_code__iexact=code).exists():
            raise forms.ValidationError("Invalid invite code.")
        return code


class CreateHouseholdForm(forms.Form):
    name = forms.CharField(label="Household name", max_length=255)

    def clean_name(self):
        name = self.cleaned_data["name"]
        if not name.strip():
            raise forms.ValidationError("Household name cannot be blank.")
        return name
