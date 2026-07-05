from django.urls import path
from .views import (
    availability,
    home,
    reservation_confirm,
    reservation_search,
    website_login,
    website_logout,
    website_register,
)

app_name = "infiniti_vacation"

urlpatterns = [
    path("", home, name="home"),
    path("availability/", availability, name="availability"),
    path("reservation/", reservation_search, name="reservation_search"),
    path("reservation/confirm/", reservation_confirm, name="reservation_confirm"),
    path("login/", website_login, name="website_login"),
    path("register/", website_register, name="website_register"),
    path("logout/", website_logout, name="website_logout"),
]
