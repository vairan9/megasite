from django.urls import path
from .views import home, website_login, website_register, website_logout

app_name = "infiniti_vacation"

urlpatterns = [
    path("", home, name="home"),
    path("website/login/", website_login, name="website_login"),
    path("website/register/", website_register, name="website_register"),
    path("website/logout/", website_logout, name="website_logout"),
]
