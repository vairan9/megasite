import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("infiniti_vacation", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ApartmentPrice",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("start_date", models.DateField(verbose_name="Start date")),
                (
                    "end_date",
                    models.DateField(
                        help_text="Last date when this price applies (inclusive).",
                        verbose_name="End date",
                    ),
                ),
                (
                    "price_per_night_pln",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=8,
                        verbose_name="Price per night (PLN)",
                    ),
                ),
                ("note", models.CharField(blank=True, max_length=120, verbose_name="Note")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Created at")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Updated at")),
                (
                    "apartment",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="price_ranges",
                        to="infiniti_vacation.apartment",
                        verbose_name="Apartment",
                    ),
                ),
            ],
            options={
                "verbose_name": "Apartment price",
                "verbose_name_plural": "Apartment prices",
                "ordering": ["apartment", "start_date"],
                "indexes": [
                    models.Index(
                        fields=["apartment", "start_date", "end_date"],
                        name="iv_price_range_idx",
                    )
                ],
            },
        ),
    ]
