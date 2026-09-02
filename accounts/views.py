from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect, render

from accounts.forms import RegistrationForm


def register(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful.")
            return redirect("onboarding")
    else:
        form = RegistrationForm()

    return render(request, "accounts/register.html", {"form": form})
