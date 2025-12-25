from django.urls import path
from django.shortcuts import render
from . import views

def launcher(request):
    return render(request, "base_launcher.html")

urlpatterns = [
    path("", launcher, name="launcher"),
    path("portfolio/", views.portfolio, name="portfolio"),
]