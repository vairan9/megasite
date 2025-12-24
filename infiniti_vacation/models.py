from django.db import models
from django.core.exceptions import ValidationError


class Apartment(models.Model):
    """
    Apartment you can show on the website.
    Availability is determined by Booking records.
    """
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)

    short_description = models.CharField(max_length=220, blank=True)
    description = models.TextField(blank=True)

    guests_max = models.PositiveSmallIntegerField(default=2)
    beds = models.PositiveSmallIntegerField(default=1)

    has_kitchen = models.BooleanField(default=False)
    has_terrace = models.BooleanField(default=False)
    forest_view = models.BooleanField(default=True)

    price_per_night_pln = models.DecimalField(max_digits=8, decimal_places=2)

    # No Pillow required:
    # Put a static path like "infiniti_vacation/img/slide-1.jpg"
    # or an external URL if you want.
    cover_image_path = models.CharField(
        max_length=255,
        blank=True,
        help_text="Example: infinitivacation/img/apt-1.jpg or static path: infiniti_vacation/img/slide-1.jpg",
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["is_active"]),
            models.Index(fields=["slug"]),
        ]

    def __str__(self) -> str:
        return self.name


class Booking(models.Model):
    """
    A booking or a manual block (maintenance, owner stay, etc.).
    If status != CANCELLED, it blocks availability.
    Range is [start_date, end_date) (end date is checkout day, not a night).
    """

    class Status(models.TextChoices):
        TENTATIVE = "tentative", "Tentative"
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"

    class Kind(models.TextChoices):
        BOOKING = "booking", "Booking"
        BLOCK = "block", "Block (maintenance)"

    apartment = models.ForeignKey(
        Apartment, on_delete=models.CASCADE, related_name="bookings"
    )

    start_date = models.DateField()  # check-in day
    end_date = models.DateField()    # check-out day (not included)

    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.CONFIRMED
    )
    kind = models.CharField(
        max_length=16, choices=Kind.choices, default=Kind.BOOKING
    )

    # Optional guest/contact fields (can be empty for BLOCK)
    guest_name = models.CharField(max_length=120, blank=True)
    guest_email = models.EmailField(blank=True)
    guest_phone = models.CharField(max_length=40, blank=True)

    note = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-start_date"]
        indexes = [
            models.Index(fields=["apartment", "start_date", "end_date"]),
            models.Index(fields=["status"]),
            models.Index(fields=["kind"]),
        ]

    def __str__(self) -> str:
        return f"{self.apartment.name}: {self.start_date} → {self.end_date} ({self.status})"

    def clean(self):
        # basic validation
        if self.end_date <= self.start_date:
            raise ValidationError("end_date must be after start_date.")

        # cancelled bookings do not block availability
        if self.status == self.Status.CANCELLED:
            return

        # overlap protection
        qs = Booking.objects.filter(apartment=self.apartment).exclude(pk=self.pk)
        qs = qs.exclude(status=self.Status.CANCELLED)

        # Overlap rule for [start, end):
        # start < existing_end AND end > existing_start
        overlap = qs.filter(start_date__lt=self.end_date, end_date__gt=self.start_date)
        if overlap.exists():
            raise ValidationError("This date range overlaps with an existing booking/block.")

    def save(self, *args, **kwargs):
        self.full_clean()  # runs clean() every time
        return super().save(*args, **kwargs)
