from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.views.decorators.http import require_http_methods

from .models import Apartment


def home(request):
    apartments = Apartment.objects.filter(is_active=True).order_by("name")
    return render(request, "infiniti_vacation/page.html", {"apartments": apartments})


@require_http_methods(["GET", "POST"])
def website_login(request):
    if request.user.is_authenticated:
        return redirect("infiniti_vacation:home")

    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect("infiniti_vacation:home")

    return render(request, "infiniti_vacation/auth/login.html", {"form": form})


@require_http_methods(["GET", "POST"])
def website_register(request):
    if request.user.is_authenticated:
        return redirect("infiniti_vacation:home")

    form = UserCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)  # auto-login after register
        return redirect("infiniti_vacation:home")

    return render(request, "infiniti_vacation/auth/register.html", {"form": form})


@require_http_methods(["GET", "POST"])
def website_logout(request):
    logout(request)
    return redirect("infiniti_vacation:home")
