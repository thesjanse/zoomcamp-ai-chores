from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import redirect, render

from households.forms import CreateHouseholdForm, JoinHouseholdForm
from households.models import Household, HouseholdMember


@login_required
def onboarding(request):
    if HouseholdMember.objects.filter(user=request.user).exists():
        return redirect("home")

    create_form = CreateHouseholdForm()
    join_form = JoinHouseholdForm()

    if request.method == "POST":
        if "create" in request.POST:
            create_form = CreateHouseholdForm(request.POST)
            if create_form.is_valid():
                household = Household.objects.create(
                    name=create_form.cleaned_data["name"]
                )
                HouseholdMember.objects.create(
                    household=household, user=request.user
                )
                return redirect("home")
        elif "join" in request.POST:
            join_form = JoinHouseholdForm(request.POST)
            if join_form.is_valid():
                code = join_form.cleaned_data["invite_code"]
                household = Household.objects.get(invite_code__iexact=code)
                HouseholdMember.objects.create(
                    household=household, user=request.user
                )
                return redirect("home")

    return render(request, "households/onboarding.html", {
        "create_form": create_form,
        "join_form": join_form,
    })
