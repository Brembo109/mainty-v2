from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def seed_qualifications_from_cycles(apps, schema_editor):
    """Backfill new Qualification records from legacy cycles + signatures.

    For each (asset, qual_type) pair, take the earliest signed_at as the
    one-time Qualification.completed_on. Subsequent signatures on the
    same cycle are left in the legacy tables — they can be re-entered
    as RQ records later if needed.
    """

    QualificationCycle = apps.get_model("qualification", "QualificationCycle")
    Qualification = apps.get_model("qualification", "Qualification")

    seen = set()
    for cycle in QualificationCycle.objects.all().order_by("asset_id", "qual_type"):
        key = (cycle.asset_id, cycle.qual_type)
        if key in seen:
            continue
        first_sig = cycle.signatures.order_by("signed_at", "created_at").first()
        if first_sig is None:
            continue
        Qualification.objects.create(
            asset_id=cycle.asset_id,
            stage=cycle.qual_type,
            completed_on=first_sig.signed_at,
            completed_by_id=first_sig.signed_by_id,
            completed_by_username=first_sig.signed_by_username,
        )
        seen.add(key)


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("assets", "0005_detail_shell_fields"),
        ("qualification", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Qualification",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("stage", models.CharField(
                    choices=[
                        ("QP", "QP — Qualifizierungsplan"),
                        ("DQ", "DQ — Designqualifizierung"),
                        ("IQ", "IQ — Installationsqualifizierung"),
                        ("OQ", "OQ — Operationsqualifizierung"),
                        ("PQ", "PQ — Performanzqualifizierung"),
                        ("QB", "QB — Qualifizierungsbericht"),
                        ("RQ", "RQ — Requalifizierung"),
                    ],
                    db_index=True,
                    max_length=2,
                    verbose_name="Stufe",
                )),
                ("planned_for", models.DateField(blank=True, null=True, verbose_name="Geplant für")),
                ("completed_on", models.DateField(blank=True, null=True, verbose_name="Abgeschlossen am")),
                ("rq_cycle", models.PositiveIntegerField(
                    blank=True,
                    null=True,
                    help_text="Nur für RQ-Stufen: fortlaufende Zyklus-Nr.",
                    verbose_name="RQ-Zyklus",
                )),
                ("completed_by_username", models.CharField(blank=True, max_length=150, verbose_name="Benutzername")),
                ("notes", models.TextField(blank=True, verbose_name="Notizen")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("asset", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="qualifications",
                    to="assets.asset",
                    verbose_name="Anlage",
                )),
                ("completed_by", models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="+",
                    to=settings.AUTH_USER_MODEL,
                    verbose_name="Abgeschlossen von",
                )),
            ],
            options={
                "verbose_name": "Qualifizierung",
                "verbose_name_plural": "Qualifizierungen",
                "ordering": ["asset", "stage", "rq_cycle"],
            },
        ),
        migrations.AddConstraint(
            model_name="qualification",
            constraint=models.UniqueConstraint(
                condition=models.Q(("stage", "RQ"), _negated=True),
                fields=("asset", "stage"),
                name="qualification_first_stage_unique",
            ),
        ),
        migrations.AddConstraint(
            model_name="qualification",
            constraint=models.UniqueConstraint(
                condition=models.Q(("stage", "RQ")),
                fields=("asset", "stage", "rq_cycle"),
                name="qualification_rq_cycle_unique",
            ),
        ),
        migrations.RunPython(
            seed_qualifications_from_cycles,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
