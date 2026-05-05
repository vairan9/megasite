import calendar
from datetime import date

from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.shortcuts import render, redirect
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods

from .models import Apartment, Booking


def home(request):
    apartments = Apartment.objects.filter(is_active=True).order_by("name")
    return render(request, "infiniti_vacation/page.html", {"apartments": apartments})


def _parse_date(value):
    if not value:
        return None

    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _booking_blocks_day(bookings, day):
    return any(booking.start_date <= day < booking.end_date for booking in bookings)


def _calendar_for_apartment(apartment, bookings, year):
    cal = calendar.Calendar(firstweekday=0)
    today = timezone.localdate()
    month_names = [
        "Styczen",
        "Luty",
        "Marzec",
        "Kwiecien",
        "Maj",
        "Czerwiec",
        "Lipiec",
        "Sierpien",
        "Wrzesien",
        "Pazdziernik",
        "Listopad",
        "Grudzien",
    ]

    months = []
    for month in range(1, 13):
        weeks = []
        for week in cal.monthdatescalendar(year, month):
            days = []
            for day in week:
                is_current_month = day.month == month
                is_blocked = is_current_month and _booking_blocks_day(bookings, day)
                days.append(
                    {
                        "date": day,
                        "number": day.day,
                        "in_month": is_current_month,
                        "is_blocked": is_blocked,
                        "is_available": is_current_month and not is_blocked,
                        "is_today": day == today,
                    }
                )
            weeks.append(days)

        months.append(
            {
                "name": month_names[month - 1],
                "number": month,
                "weeks": weeks,
            }
        )

    return {
        "apartment": apartment,
        "months": months,
        "bookings": bookings,
    }


@login_required(login_url="infiniti_vacation:website_login")
def availability(request):
    current_year = timezone.localdate().year
    raw_year = request.GET.get("year")

    try:
        year = int(raw_year) if raw_year else current_year
    except (TypeError, ValueError):
        year = current_year

    year = max(current_year - 1, min(current_year + 2, year))
    year_start = date(year, 1, 1)
    year_end = date(year + 1, 1, 1)

    apartments = list(Apartment.objects.filter(is_active=True).order_by("name"))
    bookings = (
        Booking.objects.select_related("apartment")
        .filter(
            apartment__in=apartments,
            start_date__lt=year_end,
            end_date__gt=year_start,
        )
        .exclude(status=Booking.Status.CANCELLED)
        .order_by("start_date")
    )

    bookings_by_apartment = {apartment.pk: [] for apartment in apartments}
    for booking in bookings:
        bookings_by_apartment.setdefault(booking.apartment_id, []).append(booking)

    check_in = _parse_date(request.GET.get("check_in"))
    check_out = _parse_date(request.GET.get("check_out"))
    range_error = ""
    availability_results = []

    if request.GET.get("check_in") or request.GET.get("check_out"):
        if not check_in or not check_out:
            range_error = "Podaj poprawne daty przyjazdu i wyjazdu."
        elif check_out <= check_in:
            range_error = "Data wyjazdu musi byc pozniejsza niz data przyjazdu."
        else:
            range_bookings = (
                Booking.objects.filter(
                    apartment__in=apartments,
                    start_date__lt=check_out,
                    end_date__gt=check_in,
                )
                .exclude(status=Booking.Status.CANCELLED)
                .values_list("apartment_id", flat=True)
            )
            blocked_ids = set(range_bookings)
            availability_results = [
                {
                    "apartment": apartment,
                    "is_available": apartment.pk not in blocked_ids,
                }
                for apartment in apartments
            ]

    calendars = [
        _calendar_for_apartment(apartment, bookings_by_apartment.get(apartment.pk, []), year)
        for apartment in apartments
    ]

    return render(
        request,
        "infiniti_vacation/availability.html",
        {
            "year": year,
            "current_year": current_year,
            "previous_year": year - 1,
            "next_year": year + 1,
            "can_show_previous_year": year > current_year - 1,
            "can_show_next_year": year < current_year + 2,
            "calendars": calendars,
            "check_in": check_in,
            "check_out": check_out,
            "range_error": range_error,
            "availability_results": availability_results,
        },
    )


@require_http_methods(["GET", "POST"])
def website_login(request):
    if request.user.is_authenticated:
        next_url = request.GET.get("next")
        if next_url and url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return redirect(next_url)
        return redirect("infiniti_vacation:home")

    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        next_url = request.POST.get("next") or request.GET.get("next")
        if next_url and url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return redirect(next_url)
        return redirect("infiniti_vacation:home")

    return render(
        request,
        "infiniti_vacation/auth/login.html",
        {"form": form, "next": request.GET.get("next", "")},
    )


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
