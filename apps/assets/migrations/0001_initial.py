from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Asset",
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
                ("name", models.CharField(max_length=255, verbose_name="Name")),
                (
                    "location",
                    models.CharField(max_length=255, verbose_name="Standort"),
                ),
                (
                    "serial_number",
                    models.CharField(
                        max_length=100, unique=True, verbose_name="Seriennummer"
                    ),
                ),
                (
                    "manufacturer",
                    models.CharField(
                        blank=True, max_length=255, verbose_name="Hersteller"
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("free", "Frei"),
                            ("locked", "Gesperrt"),
                            ("out_of_service", "Außer Betrieb"),
                        ],
                        db_index=True,
                        default="free",
                        max_length=20,
                        verbose_name="Status",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Erstellt am"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="Geändert am"),
                ),
            ],
            options={
                "verbose_name": "Anlage",
                "verbose_name_plural": "Anlagen",
                "ordering": ["name"],
            },
        ),
    ]
