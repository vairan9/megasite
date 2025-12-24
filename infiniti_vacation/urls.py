from django.urls import path
from .views import website_home

app_name = "infiniti_vacation"

urlpatterns = [
    path("", website_home, name="home"),
]