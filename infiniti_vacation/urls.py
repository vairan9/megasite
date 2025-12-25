from django.urls import path, include
from django.contrib import admin
from .views import website_home

app_name = "infiniti_vacation"

urlpatterns = [
    path("", website_home, name="home"),
]