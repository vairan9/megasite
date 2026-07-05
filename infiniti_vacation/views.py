import calendar
from datetime import date, timedelta
from itertools import combinations

from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.db import transaction
from django.shortcuts import render, redirect
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods

from .forms import ReservationRequestForm
from .models import Apartment, ApartmentPrice, Booking


def home(request):
    apartments = list(Apartment.objects.filter(is_active=True).order_by("name"))
    return render(
        request,
        "infiniti_vacation/page.html",
        {
            "apartments": apartments,
            "booking_max_rooms": min(4, len(apartments)) or 1,
        },
    )


def _parse_date(value):
    if not value:
        return None

    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _booking_for_day(bookings, day):
    return next(
        (
            booking
            for booking in bookings
            if booking.start_date <= day < booking.end_date
        ),
        None,
    )


def _price_for_day(apartment, price_ranges, day):
    price_range = next(
        (
            item
            for item in price_ranges
            if item.start_date <= day <= item.end_date
        ),
        None,
    )
    if price_range:
        return (
            price_range.price_per_night_pln,
            price_range.note or "Cena okresowa",
        )

    return apartment.price_per_night_pln, "Cena bazowa"


def _bounded_int(value, default, minimum, maximum):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, parsed))


def _booking_search_values(data):
    check_in = _parse_date(data.get("check_in"))
    check_out = _parse_date(data.get("check_out"))
    guests = _bounded_int(data.get("guests"), 2, 1, 12)
    rooms = _bounded_int(data.get("rooms"), 1, 1, 4)
    errors = []
    today = timezone.localdate()

    if not check_in or not check_out:
        errors.append("Wybierz date przyjazdu i wyjazdu.")
    elif check_in < today:
        errors.append("Data przyjazdu nie moze byc w przeszlosci.")
    elif check_out <= check_in:
        errors.append("Data wyjazdu musi byc pozniejsza niz data przyjazdu.")
    elif (check_out - check_in).days > 30:
        errors.append("Jedno wyszukiwanie moze obejmowac maksymalnie 30 nocy.")

    if rooms > guests:
        errors.append("Liczba apartamentow nie moze byc wieksza niz liczba gosci.")

    return {
        "check_in": check_in,
        "check_out": check_out,
        "guests": guests,
        "rooms": rooms,
        "errors": errors,
    }


def _booking_widget_context(values, max_rooms):
    return {
        "booking_check_in": values["check_in"].isoformat() if values["check_in"] else "",
        "booking_check_out": values["check_out"].isoformat() if values["check_out"] else "",
        "booking_guests": values["guests"],
        "booking_rooms": values["rooms"],
        "booking_max_rooms": max_rooms,
    }


def _available_apartments(check_in, check_out):
    apartments = list(Apartment.objects.filter(is_active=True).order_by("name"))
    blocked_ids = set(
        Booking.objects.filter(
            apartment__in=apartments,
            start_date__lt=check_out,
            end_date__gt=check_in,
        )
        .exclude(status=Booking.Status.CANCELLED)
        .values_list("apartment_id", flat=True)
    )
    return [apartment for apartment in apartments if apartment.pk not in blocked_ids]


def _price_ranges_by_apartment(apartments, check_in, check_out):
    result = {apartment.pk: [] for apartment in apartments}
    ranges = ApartmentPrice.objects.filter(
        apartment__in=apartments,
        start_date__lt=check_out,
        end_date__gte=check_in,
    ).order_by("start_date")
    for price_range in ranges:
        result.setdefault(price_range.apartment_id, []).append(price_range)
    return result


def _apartment_stay_price(apartment, price_ranges, check_in, check_out):
    total = 0
    day = check_in
    while day < check_out:
        total += _price_for_day(apartment, price_ranges, day)[0]
        day += timedelta(days=1)
    return total


def _reservation_packages(check_in, check_out, guests, rooms):
    apartments = _available_apartments(check_in, check_out)
    price_ranges = _price_ranges_by_apartment(apartments, check_in, check_out)
    packages = []

    for apartment_group in combinations(apartments, rooms):
        capacity = sum(apartment.guests_max for apartment in apartment_group)
        if capacity < guests:
            continue

        apartment_rows = []
        total_price = 0
        for apartment in apartment_group:
            stay_price = _apartment_stay_price(
                apartment,
                price_ranges.get(apartment.pk, []),
                check_in,
                check_out,
            )
            total_price += stay_price
            apartment_rows.append(
                {
                    "apartment": apartment,
                    "stay_price": stay_price,
                }
            )

        packages.append(
            {
                "apartments": apartment_rows,
                "capacity": capacity,
                "total_price": total_price,
                "slug_query": ",".join(apartment.slug for apartment in apartment_group),
            }
        )

    return sorted(packages, key=lambda item: (item["total_price"], -item["capacity"]))


def reservation_search(request):
    values = _booking_search_values(request.GET)
    active_count = Apartment.objects.filter(is_active=True).count()
    packages = []

    if not values["errors"]:
        packages = _reservation_packages(
            values["check_in"],
            values["check_out"],
            values["guests"],
            values["rooms"],
        )

    context = {
        **_booking_widget_context(values, min(4, active_count) or 1),
        "search": values,
        "packages": packages,
        "nights": (
            (values["check_out"] - values["check_in"]).days
            if values["check_in"] and values["check_out"]
            else 0
        ),
    }
    return render(request, "infiniti_vacation/reservation_results.html", context)


@require_http_methods(["GET", "POST"])
def reservation_confirm(request):
    data = request.POST if request.method == "POST" else request.GET
    values = _booking_search_values(data)
    requested_slugs = [slug for slug in data.get("apartments", "").split(",") if slug]
    apartments_by_slug = {
        apartment.slug: apartment
        for apartment in Apartment.objects.filter(is_active=True, slug__in=requested_slugs)
    }
    apartments = [apartments_by_slug[slug] for slug in requested_slugs if slug in apartments_by_slug]
    package_error = ""

    if len(apartments) != values["rooms"] or len(apartments) != len(set(requested_slugs)):
        package_error = "Wybrany zestaw apartamentow jest nieprawidlowy."
    elif values["check_in"] and values["check_out"]:
        available_ids = {
            apartment.pk
            for apartment in _available_apartments(values["check_in"], values["check_out"])
        }
        if any(apartment.pk not in available_ids for apartment in apartments):
            package_error = "Jeden z apartamentow nie jest juz dostepny w tym terminie."
        elif sum(apartment.guests_max for apartment in apartments) < values["guests"]:
            package_error = "Wybrane apartamenty nie maja wystarczajacej liczby miejsc."

    price_ranges = (
        _price_ranges_by_apartment(apartments, values["check_in"], values["check_out"])
        if apartments and values["check_in"] and values["check_out"]
        else {}
    )
    apartment_rows = []
    total_price = 0
    if not values["errors"] and not package_error:
        for apartment in apartments:
            stay_price = _apartment_stay_price(
                apartment,
                price_ranges.get(apartment.pk, []),
                values["check_in"],
                values["check_out"],
            )
            total_price += stay_price
            apartment_rows.append({"apartment": apartment, "stay_price": stay_price})

    form = ReservationRequestForm(request.POST or None)
    success = False
    if request.method == "POST" and form.is_valid() and not values["errors"] and not package_error:
        try:
            with transaction.atomic():
                fresh_available_ids = {
                    apartment.pk
                    for apartment in _available_apartments(values["check_in"], values["check_out"])
                }
                if any(apartment.pk not in fresh_available_ids for apartment in apartments):
                    raise ValidationError("Wybrany termin zostal wlasnie zajety.")

                for apartment in apartments:
                    Booking.objects.create(
                        apartment=apartment,
                        start_date=values["check_in"],
                        end_date=values["check_out"],
                        status=Booking.Status.TENTATIVE,
                        kind=Booking.Kind.BOOKING,
                        guest_name=form.cleaned_data["guest_name"],
                        guest_email=form.cleaned_data["guest_email"],
                        guest_phone=form.cleaned_data["guest_phone"],
                        note=form.cleaned_data["note"],
                    )
            success = True
        except ValidationError as error:
            form.add_error(None, error.messages[0])

    return render(
        request,
        "infiniti_vacation/reservation_confirm.html",
        {
            "search": values,
            "apartments": apartment_rows,
            "apartment_slugs": ",".join(requested_slugs),
            "total_price": total_price,
            "nights": (
                (values["check_out"] - values["check_in"]).days
                if values["check_in"] and values["check_out"]
                else 0
            ),
            "package_error": package_error,
            "form": form,
            "success": success,
        },
    )


def _calendar_for_apartment(apartment, bookings, price_ranges, year):
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
                booking = _booking_for_day(bookings, day) if is_current_month else None
                is_blocked = booking is not None
                price = None
                price_note = ""
                status_label = ""

                if is_current_month:
                    price, price_note = _price_for_day(apartment, price_ranges, day)
                    if not booking:
                        status_label = "Wolny"
                    elif booking.kind == Booking.Kind.BLOCK:
                        status_label = "Zablokowany"
                    elif booking.status == Booking.Status.TENTATIVE:
                        status_label = "Wstepnie zajety"
                    else:
                        status_label = "Zajety"

                days.append(
                    {
                        "date": day,
                        "number": day.day,
                        "in_month": is_current_month,
                        "is_blocked": is_blocked,
                        "is_available": is_current_month and not is_blocked,
                        "is_today": day == today,
                        "price": price,
                        "price_note": price_note,
                        "status_label": status_label,
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
    selected_slug = request.GET.get("room")
    view_all_rooms = request.GET.get("view") == "all"
    selected_apartment = next(
        (apartment for apartment in apartments if apartment.slug == selected_slug),
        None,
    )
    if view_all_rooms:
        selected_apartment = None

    selected_room_query = ""
    if view_all_rooms:
        selected_room_query = "&view=all"
    elif selected_apartment:
        selected_room_query = f"&room={selected_apartment.slug}"

    booking_filter = {"apartment__in": apartments} if view_all_rooms else {"apartment": selected_apartment}
    bookings = (
        Booking.objects.select_related("apartment")
        .filter(
            **booking_filter,
            start_date__lt=year_end,
            end_date__gt=year_start,
        )
        .exclude(status=Booking.Status.CANCELLED)
        .order_by("start_date")
    )
    price_ranges = (
        ApartmentPrice.objects.select_related("apartment")
        .filter(
            **booking_filter,
            start_date__lt=year_end,
            end_date__gte=year_start,
        )
        .order_by("start_date")
    )

    check_in = _parse_date(request.GET.get("check_in"))
    check_out = _parse_date(request.GET.get("check_out"))
    range_error = ""
    availability_result = None
    availability_results = []

    if request.GET.get("check_in") or request.GET.get("check_out"):
        if not check_in or not check_out:
            range_error = "Podaj poprawne daty przyjazdu i wyjazdu."
        elif check_out <= check_in:
            range_error = "Data wyjazdu musi byc pozniejsza niz data przyjazdu."
        elif view_all_rooms:
            blocked_ids = set(
                Booking.objects.filter(
                    apartment__in=apartments,
                    start_date__lt=check_out,
                    end_date__gt=check_in,
                )
                .exclude(status=Booking.Status.CANCELLED)
                .values_list("apartment_id", flat=True)
            )
            availability_results = [
                {
                    "apartment": apartment,
                    "is_available": apartment.pk not in blocked_ids,
                }
                for apartment in apartments
            ]
        elif selected_apartment:
            is_blocked = (
                Booking.objects.filter(
                    apartment=selected_apartment,
                    start_date__lt=check_out,
                    end_date__gt=check_in,
                )
                .exclude(status=Booking.Status.CANCELLED)
                .exists()
            )
            availability_result = {
                "apartment": selected_apartment,
                "is_available": not is_blocked,
            }

    selected_calendar = None
    calendars = []
    if selected_apartment:
        selected_calendar = _calendar_for_apartment(
            selected_apartment,
            list(bookings),
            list(price_ranges),
            year,
        )
        calendars = [selected_calendar]
    elif view_all_rooms:
        bookings_by_apartment = {apartment.pk: [] for apartment in apartments}
        for booking in bookings:
            bookings_by_apartment.setdefault(booking.apartment_id, []).append(booking)

        prices_by_apartment = {apartment.pk: [] for apartment in apartments}
        for price_range in price_ranges:
            prices_by_apartment.setdefault(price_range.apartment_id, []).append(price_range)

        calendars = [
            _calendar_for_apartment(
                apartment,
                bookings_by_apartment.get(apartment.pk, []),
                prices_by_apartment.get(apartment.pk, []),
                year,
            )
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
            "selected_room_query": selected_room_query,
            "view_all_rooms": view_all_rooms,
            "apartments": apartments,
            "selected_apartment": selected_apartment,
            "calendar": selected_calendar,
            "calendars": calendars,
            "check_in": check_in,
            "check_out": check_out,
            "range_error": range_error,
            "availability_result": availability_result,
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
