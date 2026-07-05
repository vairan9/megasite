from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from .models import Apartment, ApartmentPrice, Booking


class AvailabilityViewTests(TestCase):
    def setUp(self):
        self.year = timezone.localdate().year
        self.user = get_user_model().objects.create_user(
            username="calendar-user",
            password="strong-test-password",
        )
        self.apartment_a = Apartment.objects.create(
            name="Room A",
            slug="room-a",
            guests_max=2,
            beds=1,
            price_per_night_pln="320.00",
            is_active=True,
        )
        self.apartment_b = Apartment.objects.create(
            name="Room B",
            slug="room-b",
            guests_max=4,
            beds=2,
            price_per_night_pln="460.00",
            is_active=True,
        )
        Booking.objects.create(
            apartment=self.apartment_a,
            start_date=date(self.year, 6, 10),
            end_date=date(self.year, 6, 13),
            status=Booking.Status.CONFIRMED,
        )

    def test_availability_requires_login(self):
        response = self.client.get(reverse("infiniti_vacation:availability"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("infiniti_vacation:website_login"), response["Location"])

    def test_availability_page_lists_rooms_before_selection(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("infiniti_vacation:availability"),
            {"year": self.year},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Room A")
        self.assertContains(response, "Room B")
        self.assertContains(response, str(self.year))
        self.assertIsNone(response.context["selected_apartment"])
        self.assertIsNone(response.context["calendar"])
        self.assertContains(response, "Wybierz pokoj powyzej")
        self.assertContains(response, "data-snake-game")

    def test_availability_page_selects_room_from_query(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("infiniti_vacation:availability"),
            {"year": self.year, "room": "room-b"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["selected_apartment"], self.apartment_b)
        self.assertEqual(response.context["calendar"]["apartment"], self.apartment_b)

    def test_calendar_uses_date_range_price_and_base_price_as_fallback(self):
        ApartmentPrice.objects.create(
            apartment=self.apartment_a,
            start_date=date(self.year, 7, 10),
            end_date=date(self.year, 7, 15),
            price_per_night_pln="510.00",
            note="Wysoki sezon",
        )
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("infiniti_vacation:availability"),
            {"year": self.year, "room": "room-a"},
        )

        july = response.context["calendar"]["months"][6]
        days = [day for week in july["weeks"] for day in week if day["in_month"]]
        regular_day = next(day for day in days if day["number"] == 9)
        seasonal_day = next(day for day in days if day["number"] == 11)
        seasonal_end_day = next(day for day in days if day["number"] == 15)
        after_season_day = next(day for day in days if day["number"] == 16)

        self.assertEqual(regular_day["price"], Decimal("320.00"))
        self.assertEqual(regular_day["price_note"], "Cena bazowa")
        self.assertEqual(seasonal_day["price"], Decimal("510.00"))
        self.assertEqual(seasonal_day["price_note"], "Wysoki sezon")
        self.assertEqual(seasonal_end_day["price"], Decimal("510.00"))
        self.assertEqual(after_season_day["price"], Decimal("320.00"))

    def test_price_ranges_for_the_same_room_cannot_overlap(self):
        ApartmentPrice.objects.create(
            apartment=self.apartment_a,
            start_date=date(self.year, 7, 1),
            end_date=date(self.year, 7, 10),
            price_per_night_pln="500.00",
        )

        with self.assertRaises(ValidationError):
            ApartmentPrice.objects.create(
                apartment=self.apartment_a,
                start_date=date(self.year, 7, 10),
                end_date=date(self.year, 7, 20),
                price_per_night_pln="550.00",
            )

    def test_availability_page_can_show_all_rooms_together(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("infiniti_vacation:availability"),
            {"year": self.year, "view": "all"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["view_all_rooms"])
        self.assertIsNone(response.context["selected_apartment"])
        self.assertEqual(len(response.context["calendars"]), 2)
        self.assertContains(response, "Wszystkie pokoje razem")

    def test_date_range_checker_marks_selected_room_blocked(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("infiniti_vacation:availability"),
            {
                "year": self.year,
                "room": "room-a",
                "check_in": f"{self.year}-06-11",
                "check_out": f"{self.year}-06-12",
            },
        )

        self.assertEqual(response.status_code, 200)
        result = response.context["availability_result"]
        self.assertEqual(result["apartment"], self.apartment_a)
        self.assertFalse(result["is_available"])

    def test_date_range_checker_marks_selected_room_open(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("infiniti_vacation:availability"),
            {
                "year": self.year,
                "room": "room-b",
                "check_in": f"{self.year}-06-11",
                "check_out": f"{self.year}-06-12",
            },
        )

        result = response.context["availability_result"]
        self.assertEqual(result["apartment"], self.apartment_b)
        self.assertTrue(result["is_available"])

    def test_date_range_checker_marks_all_rooms_when_all_view_is_selected(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("infiniti_vacation:availability"),
            {
                "year": self.year,
                "view": "all",
                "check_in": f"{self.year}-06-11",
                "check_out": f"{self.year}-06-12",
            },
        )

        results = {
            item["apartment"].slug: item["is_available"]
            for item in response.context["availability_results"]
        }
        self.assertFalse(results["room-a"])
        self.assertTrue(results["room-b"])

    def test_cancelled_booking_does_not_block_availability(self):
        Booking.objects.create(
            apartment=self.apartment_b,
            start_date=date(self.year, 6, 11),
            end_date=date(self.year, 6, 12),
            status=Booking.Status.CANCELLED,
        )
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("infiniti_vacation:availability"),
            {
                "year": self.year,
                "room": "room-b",
                "check_in": f"{self.year}-06-11",
                "check_out": f"{self.year}-06-12",
            },
        )

        result = response.context["availability_result"]
        self.assertEqual(result["apartment"], self.apartment_b)
        self.assertTrue(result["is_available"])

    def test_homepage_contains_booking_search(self):
        response = self.client.get(reverse("infiniti_vacation:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-booking-search")
        self.assertContains(response, reverse("infiniti_vacation:reservation_search"))

    def test_reservation_search_filters_by_capacity_and_calculates_total(self):
        check_in = timezone.localdate() + timedelta(days=40)
        check_out = check_in + timedelta(days=3)

        response = self.client.get(
            reverse("infiniti_vacation:reservation_search"),
            {
                "check_in": check_in.isoformat(),
                "check_out": check_out.isoformat(),
                "guests": 3,
                "rooms": 1,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["packages"]), 1)
        package = response.context["packages"][0]
        self.assertEqual(package["apartments"][0]["apartment"], self.apartment_b)
        self.assertEqual(package["total_price"], Decimal("1380.00"))

    def test_reservation_search_uses_seasonal_price_for_each_night(self):
        check_in = timezone.localdate() + timedelta(days=50)
        check_out = check_in + timedelta(days=3)
        ApartmentPrice.objects.create(
            apartment=self.apartment_b,
            start_date=check_in,
            end_date=check_out,
            price_per_night_pln="500.00",
            note="Pakiet wakacyjny",
        )

        response = self.client.get(
            reverse("infiniti_vacation:reservation_search"),
            {
                "check_in": check_in.isoformat(),
                "check_out": check_out.isoformat(),
                "guests": 3,
                "rooms": 1,
            },
        )

        self.assertEqual(response.context["packages"][0]["total_price"], Decimal("1500.00"))

    def test_reservation_search_builds_multi_apartment_package(self):
        check_in = timezone.localdate() + timedelta(days=60)
        check_out = check_in + timedelta(days=2)

        response = self.client.get(
            reverse("infiniti_vacation:reservation_search"),
            {
                "check_in": check_in.isoformat(),
                "check_out": check_out.isoformat(),
                "guests": 5,
                "rooms": 2,
            },
        )

        self.assertEqual(len(response.context["packages"]), 1)
        package = response.context["packages"][0]
        self.assertEqual(package["capacity"], 6)
        self.assertEqual(package["total_price"], Decimal("1560.00"))

    def test_reservation_confirmation_creates_tentative_booking(self):
        check_in = timezone.localdate() + timedelta(days=70)
        check_out = check_in + timedelta(days=2)

        response = self.client.post(
            reverse("infiniti_vacation:reservation_confirm"),
            {
                "check_in": check_in.isoformat(),
                "check_out": check_out.isoformat(),
                "guests": 3,
                "rooms": 1,
                "apartments": self.apartment_b.slug,
                "guest_name": "Jan Kowalski",
                "guest_email": "jan@example.com",
                "guest_phone": "+48 500 500 500",
                "note": "Pozny przyjazd",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["success"])
        booking = Booking.objects.get(
            apartment=self.apartment_b,
            start_date=check_in,
            end_date=check_out,
        )
        self.assertEqual(booking.status, Booking.Status.TENTATIVE)
        self.assertEqual(booking.guest_email, "jan@example.com")
