from django.urls import path
from .views import availability, home, website_login, website_register, website_logout

app_name = "infiniti_vacation"

urlpatterns = [
    path("", home, name="home"),
    path("availability/", availability, name="availability"),
    path("login/", website_login, name="website_login"),
    path("register/", website_register, name="website_register"),
    path("logout/", website_logout, name="website_logout"),
]
