from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from chores.forms import ChoreForm
from chores.models import Chore
from households.models import HouseholdMember


def _current_household(user):
    membership = HouseholdMember.objects.filter(user=user).first()
    if membership is None:
        return None
    return membership.household


def _household_or_redirect_decorator(view_func):
    def wrapper(request, *args, **kwargs):
        household = _current_household(request.user)
        if household is None:
            return redirect("onboarding")
        request.household = household
        return view_func(request, *args, **kwargs)

    wrapper.__name__ = view_func.__name__
    return wrapper


@login_required
@_household_or_redirect_decorator
def chore_list(request):
    chores = Chore.objects.filter(household=request.household)
    return render(request, "chores/chore_list.html", {"chores": chores})


@login_required
@_household_or_redirect_decorator
def chore_create(request):
    if request.method == "POST":
        form = ChoreForm(request.POST)
        if form.is_valid():
            chore = form.save(commit=False)
            chore.household = request.household
            chore.save()
            return redirect("chore_list")
    else:
        form = ChoreForm()
    return render(request, "chores/chore_form.html", {"form": form})


@login_required
@_household_or_redirect_decorator
def chore_detail(request, pk):
    chore = get_object_or_404(
        Chore, pk=pk, household=request.household
    )
    return render(request, "chores/chore_detail.html", {"chore": chore})


@login_required
@_household_or_redirect_decorator
def chore_update(request, pk):
    chore = get_object_or_404(
        Chore, pk=pk, household=request.household
    )
    if request.method == "POST":
        form = ChoreForm(request.POST, instance=chore)
        if form.is_valid():
            form.save()
            return redirect("chore_list")
    else:
        form = ChoreForm(instance=chore)
    return render(request, "chores/chore_form.html", {"form": form, "chore": chore})


@login_required
@_household_or_redirect_decorator
def chore_delete(request, pk):
    chore = get_object_or_404(
        Chore, pk=pk, household=request.household
    )
    if request.method == "POST":
        chore.delete()
        return redirect("chore_list")
    return render(
        request, "chores/chore_confirm_delete.html", {"chore": chore}
    )


@login_required
@_household_or_redirect_decorator
def chore_market(request):
    chores = Chore.objects.filter(
        household=request.household,
        status="open",
        assigned_to__isnull=True,
    )
    return render(request, "chores/chore_market.html", {"chores": chores})


@login_required
@_household_or_redirect_decorator
def chore_claim(request, pk):
    get_object_or_404(
        Chore,
        pk=pk,
        household=request.household,
    )
    Chore.objects.filter(
        pk=pk,
        household=request.household,
        status="open",
        assigned_to__isnull=True,
    ).update(assigned_to=request.user, status="in_progress")
    return HttpResponse(status=200)
