from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from .models import Apartment, Booking


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

    def test_availability_page_lists_rooms_for_logged_in_user(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("infiniti_vacation:availability"),
            {"year": self.year},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Room A")
        self.assertContains(response, "Room B")
        self.assertContains(response, str(self.year))

    def test_date_range_checker_marks_blocked_and_open_rooms(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("infiniti_vacation:availability"),
            {
                "year": self.year,
                "check_in": f"{self.year}-06-11",
                "check_out": f"{self.year}-06-12",
            },
        )

        self.assertEqual(response.status_code, 200)
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
                "check_in": f"{self.year}-06-11",
                "check_out": f"{self.year}-06-12",
            },
        )

        results = {
            item["apartment"].slug: item["is_available"]
            for item in response.context["availability_results"]
        }
        self.assertTrue(results["room-b"])
