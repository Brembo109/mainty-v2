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
            name="QualificationCycle",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("qual_type", models.CharField(
                    choices=[
                        ("IQ", "IQ — Installationsqualifizierung"),
                        ("OQ", "OQ — Operationsqualifizierung"),
                        ("PQ", "PQ — Performanzqualifizierung"),
                    ],
                    db_index=True,
                    max_length=2,
                    verbose_name="Qualifizierungstyp",
                )),
                ("title", models.CharField(max_length=255, verbose_name="Bezeichnung")),
                ("description", models.TextField(blank=True, verbose_name="Beschreibung")),
                ("responsible", models.CharField(blank=True, max_length=255, verbose_name="Verantwortlich")),
                ("interval_days", models.PositiveIntegerField(
                    help_text="z.B. 730 für alle 2 Jahre",
                    verbose_name="Wiederholungsintervall (Tage)",
                )),
                ("change_reason", models.TextField(blank=True, verbose_name="Änderungsgrund")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "asset",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="qualification_cycles",
                        to="assets.asset",
                        verbose_name="Anlage",
                    ),
                ),
            ],
            options={
                "verbose_name": "Qualifizierungszyklus",
                "verbose_name_plural": "Qualifizierungszyklen",
                "ordering": ["asset", "qual_type", "title"],
            },
        ),
        migrations.CreateModel(
            name="QualificationSignature",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("signed_at", models.DateField(verbose_name="Signierdatum")),
                ("signed_by_username", models.CharField(max_length=150, verbose_name="Benutzername")),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True, verbose_name="IP-Adresse")),
                ("meaning", models.CharField(
                    default="Geprüft und freigegeben",
                    max_length=255,
                    verbose_name="Bedeutung der Signatur",
                )),
                ("notes", models.TextField(blank=True, verbose_name="Notizen")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "cycle",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="signatures",
                        to="qualification.qualificationcycle",
                        verbose_name="Qualifizierungszyklus",
                    ),
                ),
                (
                    "signed_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Signiert von",
                    ),
                ),
            ],
            options={
                "verbose_name": "Elektronische Signatur",
                "verbose_name_plural": "Elektronische Signaturen",
                "ordering": ["-signed_at", "-created_at"],
            },
        ),
    ]
