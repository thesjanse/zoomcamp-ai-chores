from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from households.forms import CreateHouseholdForm, JoinHouseholdForm
from households.models import Household, HouseholdMember


def _current_household(user):
    membership = HouseholdMember.objects.filter(user=user).first()
    if membership is None:
        return None
    return membership.household


def _current_membership(user):
    return HouseholdMember.objects.filter(user=user).first()


def _household_or_redirect_decorator(view_func):
    def wrapper(request, *args, **kwargs):
        household = _current_household(request.user)
        if household is None:
            return redirect("onboarding")
        request.household = household
        return view_func(request, *args, **kwargs)

    wrapper.__name__ = view_func.__name__
    return wrapper


def _admin_required_decorator(view_func):
    def wrapper(request, *args, **kwargs):
        household = _current_household(request.user)
        if household is None:
            return redirect("onboarding")
        membership = _current_membership(request.user)
        if membership is None or not membership.is_admin:
            raise PermissionDenied
        request.household = household
        return view_func(request, *args, **kwargs)

    wrapper.__name__ = view_func.__name__
    return wrapper


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
                    household=household,
                    user=request.user,
                    role=HouseholdMember.Role.ADMIN,
                )
                return redirect("home")
        elif "join" in request.POST:
            join_form = JoinHouseholdForm(request.POST)
            if join_form.is_valid():
                code = join_form.cleaned_data["invite_code"]
                household = Household.objects.get(invite_code__iexact=code)
                HouseholdMember.objects.create(
                    household=household,
                    user=request.user,
                    role=HouseholdMember.Role.MEMBER,
                )
                return redirect("home")

    return render(request, "households/onboarding.html", {
        "create_form": create_form,
        "join_form": join_form,
    })


@login_required
@_admin_required_decorator
def household_members(request):
    members = HouseholdMember.objects.filter(
        household=request.household
    ).select_related("user")
    return render(request, "households/members.html", {"members": members})


@login_required
@_admin_required_decorator
def member_promote(request, pk):
    membership = get_object_or_404(
        HouseholdMember, pk=pk, household=request.household
    )
    membership.role = HouseholdMember.Role.ADMIN
    membership.save(update_fields=["role"])
    return redirect("household_members")


@login_required
@_admin_required_decorator
def member_demote(request, pk):
    membership = get_object_or_404(
        HouseholdMember, pk=pk, household=request.household
    )
    admin_count = HouseholdMember.objects.filter(
        household=request.household, role=HouseholdMember.Role.ADMIN
    ).count()
    if membership.is_admin and admin_count <= 1:
        raise PermissionDenied(
            "A household must have at least one admin"
        )
    membership.role = HouseholdMember.Role.MEMBER
    membership.save(update_fields=["role"])
    return redirect("household_members")


@login_required
@_admin_required_decorator
def household_settings(request):
    return render(request, "households/settings.html", {
        "household": request.household,
    })
