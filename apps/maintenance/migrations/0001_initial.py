import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("assets", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="MaintenancePlan",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255, verbose_name="Bezeichnung")),
                ("description", models.TextField(blank=True, verbose_name="Beschreibung / Anweisungen")),
                ("responsible", models.CharField(blank=True, max_length=255, verbose_name="Verantwortlich")),
                ("interval_days", models.PositiveIntegerField(help_text="z.B. 365 für jährlich, 90 für quartalsweise", verbose_name="Intervall (Tage)")),
                ("change_reason", models.TextField(blank=True, help_text="Begründung der letzten Planänderung", verbose_name="Änderungsgrund")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Erstellt am")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Geändert am")),
                (
                    "asset",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="maintenance_plans",
                        to="assets.asset",
                        verbose_name="Anlage",
                    ),
                ),
            ],
            options={
                "verbose_name": "Wartungsplan",
                "verbose_name_plural": "Wartungspläne",
                "ordering": ["asset__name", "title"],
            },
        ),
        migrations.CreateModel(
            name="MaintenanceRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("performed_at", models.DateField(verbose_name="Durchgeführt am")),
                ("notes", models.TextField(blank=True, verbose_name="Notizen / Beobachtungen")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Erfasst am")),
                (
                    "plan",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="records",
                        to="maintenance.maintenanceplan",
                        verbose_name="Wartungsplan",
                    ),
                ),
                (
                    "performed_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Durchgeführt von",
                    ),
                ),
            ],
            options={
                "verbose_name": "Wartungsdurchführung",
                "verbose_name_plural": "Wartungsdurchführungen",
                "ordering": ["-performed_at"],
            },
        ),
    ]
