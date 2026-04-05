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
            name="Task",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255, verbose_name="Titel")),
                ("description", models.TextField(blank=True, verbose_name="Beschreibung")),
                ("due_date", models.DateField(blank=True, null=True, verbose_name="Fällig am")),
                ("priority", models.CharField(
                    choices=[("low", "Niedrig"), ("medium", "Mittel"), ("high", "Hoch")],
                    db_index=True,
                    default="medium",
                    max_length=10,
                    verbose_name="Priorität",
                )),
                ("status", models.CharField(
                    choices=[("open", "Offen"), ("in_progress", "In Bearbeitung"), ("done", "Erledigt")],
                    db_index=True,
                    default="open",
                    max_length=15,
                    verbose_name="Status",
                )),
                ("change_reason", models.TextField(blank=True, verbose_name="Änderungsgrund")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "asset",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="tasks",
                        to="assets.asset",
                        verbose_name="Anlage",
                    ),
                ),
                (
                    "assigned_to",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="assigned_tasks",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Zugewiesen an",
                    ),
                ),
            ],
            options={
                "verbose_name": "Aufgabe",
                "verbose_name_plural": "Aufgaben",
                "ordering": ["status", "-priority", "due_date"],
            },
        ),
    ]
