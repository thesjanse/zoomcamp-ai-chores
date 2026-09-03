from django.shortcuts import render

from households.models import HouseholdMember


def home(request):
    context = {}
    if request.user.is_authenticated:
        membership = HouseholdMember.objects.select_related("household").filter(
            user=request.user
        ).first()
        if membership:
            context["household_name"] = membership.household.name
    return render(request, "app/home.html", context)
