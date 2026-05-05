from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class Apartment(models.Model):
    """
    Apartment you can show on the website.
    Availability is determined by Booking records.
    """

    name = models.CharField(_("Name"), max_length=120)
    slug = models.SlugField(_("Slug"), max_length=140, unique=True)

    short_description = models.CharField(
        _("Short description"), max_length=220, blank=True
    )
    description = models.TextField(_("Description"), blank=True)

    guests_max = models.PositiveSmallIntegerField(_("Max guests"), default=2)
    beds = models.PositiveSmallIntegerField(_("Beds"), default=1)

    has_kitchen = models.BooleanField(_("Kitchen"), default=False)
    has_terrace = models.BooleanField(_("Terrace"), default=False)
    forest_view = models.BooleanField(_("Forest view"), default=True)

    price_per_night_pln = models.DecimalField(
        _("Price per night (PLN)"), max_digits=8, decimal_places=2
    )

    cover_image_path = models.CharField(
        _("Cover image path"),
        max_length=255,
        blank=True,
        help_text=_(
            "Example: infinitivacation/img/apt-1.jpg or static path: "
            "infiniti_vacation/img/slide-1.jpg"
        ),
    )

    is_active = models.BooleanField(_("Active"), default=True)

    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)

    class Meta:
        verbose_name = _("Apartment")
        verbose_name_plural = _("Apartments")
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
    Range is [start_date, end_date).
    """

    class Status(models.TextChoices):
        TENTATIVE = "tentative", _("Tentative")
        CONFIRMED = "confirmed", _("Confirmed")
        CANCELLED = "cancelled", _("Cancelled")

    class Kind(models.TextChoices):
        BOOKING = "booking", _("Booking")
        BLOCK = "block", _("Block (maintenance)")

    apartment = models.ForeignKey(
        Apartment,
        on_delete=models.CASCADE,
        related_name="bookings",
        verbose_name=_("Apartment"),
    )

    start_date = models.DateField(_("Start date"))  # check-in
    end_date = models.DateField(_("End date"))      # check-out

    status = models.CharField(
        _("Status"),
        max_length=16,
        choices=Status.choices,
        default=Status.CONFIRMED,
    )
    kind = models.CharField(
        _("Kind"),
        max_length=16,
        choices=Kind.choices,
        default=Kind.BOOKING,
    )

    guest_name = models.CharField(_("Guest name"), max_length=120, blank=True)
    guest_email = models.EmailField(_("Guest email"), blank=True)
    guest_phone = models.CharField(_("Guest phone"), max_length=40, blank=True)

    note = models.TextField(_("Note"), blank=True)

    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)

    class Meta:
        verbose_name = _("Booking")
        verbose_name_plural = _("Bookings")
        ordering = ["-start_date"]
        indexes = [
            models.Index(fields=["apartment", "start_date", "end_date"]),
            models.Index(fields=["status"]),
            models.Index(fields=["kind"]),
        ]

    def __str__(self) -> str:
        return _(
            "%(apartment)s: %(start)s → %(end)s (%(status)s)"
        ) % {
            "apartment": self.apartment.name,
            "start": self.start_date,
                        "end": self.end_date,
            "status": self.status,
        }

    def clean(self):
        if self.end_date <= self.start_date:
            raise ValidationError(
                _("End date must be after start date.")
            )

        if self.status == self.Status.CANCELLED:
            return

        qs = Booking.objects.filter(apartment=self.apartment).exclude(pk=self.pk)
        qs = qs.exclude(status=self.Status.CANCELLED)

        overlap = qs.filter(
            start_date__lt=self.end_date,
            end_date__gt=self.start_date,
        )

        if overlap.exists():
            raise ValidationError(
                _("This date range overlaps with an existing booking or block.")
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
