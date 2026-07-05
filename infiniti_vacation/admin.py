from django.contrib import admin
from .models import Apartment, ApartmentPrice, Booking


class ApartmentPriceInline(admin.TabularInline):
    model = ApartmentPrice
    extra = 1
    fields = ("start_date", "end_date", "price_per_night_pln", "note")


@admin.register(Apartment)
class ApartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "guests_max", "beds", "price_per_night_pln", "is_active")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    list_filter = ("is_active", "has_kitchen", "has_terrace", "forest_view")
    inlines = (ApartmentPriceInline,)


@admin.register(ApartmentPrice)
class ApartmentPriceAdmin(admin.ModelAdmin):
    list_display = ("apartment", "start_date", "end_date", "price_per_night_pln", "note")
    list_filter = ("apartment",)
    search_fields = ("apartment__name", "note")
    date_hierarchy = "start_date"


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("apartment", "start_date", "end_date", "status", "kind", "guest_name")
    list_filter = ("status", "kind", "apartment")
    search_fields = ("apartment__name", "guest_name", "guest_email", "guest_phone")
    date_hierarchy = "start_date"
