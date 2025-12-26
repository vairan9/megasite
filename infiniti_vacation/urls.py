from django.urls import path, include
from django.contrib import admin
from .views import home

app_name = "infiniti_vacation"
urlpatterns = [
    path("", home, name="home"),
]
