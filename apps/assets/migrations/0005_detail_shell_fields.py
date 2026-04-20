from django.db import migrations, models


def backfill_short_code_from_device_code(apps, schema_editor):
    Asset = apps.get_model("assets", "Asset")
    seen = set()
    for asset in Asset.objects.all():
        base = (asset.short_code or "").strip()
        if not base:
            base = f"ASSET-{asset.pk}"
        candidate = base
        suffix = 2
        while candidate in seen:
            candidate = f"{base}-{suffix}"
            suffix += 1
        if candidate != asset.short_code:
            asset.short_code = candidate
            asset.save(update_fields=["short_code"])
        seen.add(candidate)


class Migration(migrations.Migration):

    dependencies = [
        ("assets", "0004_asset_extended_fields_v2"),
    ]

    operations = [
        migrations.RenameField(
            model_name="asset",
            old_name="device_code",
            new_name="short_code",
        ),
        migrations.RenameField(
            model_name="asset",
            old_name="log_number",
            new_name="logbook_ref",
        ),
        migrations.RenameField(
            model_name="asset",
            old_name="manual_number",
            new_name="bal_ref",
        ),
        migrations.RunPython(
            backfill_short_code_from_device_code,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="asset",
            name="short_code",
            field=models.CharField(
                help_text="Internes Kürzel, eindeutig pro Gerät (z.B. HPLC-A1).",
                max_length=50,
                unique=True,
                verbose_name="Kürzel",
            ),
        ),
        migrations.AddField(
            model_name="asset",
            name="logbook_url",
            field=models.URLField(blank=True, verbose_name="Logbuch-Link"),
        ),
        migrations.AddField(
            model_name="asset",
            name="bal_url",
            field=models.URLField(blank=True, verbose_name="BAL-Link"),
        ),
        migrations.AddField(
            model_name="asset",
            name="requalification_interval_years",
            field=models.PositiveSmallIntegerField(
                default=4,
                help_text="Intervall für die turnusmäßige Requalifizierung (RQ).",
                verbose_name="Requalifizierungs-Intervall (Jahre)",
            ),
        ),
        migrations.AddField(
            model_name="asset",
            name="pq_required",
            field=models.BooleanField(
                default=False,
                help_text="Ist eine Performance-Qualifizierung für diese Anlage vorgesehen?",
                verbose_name="PQ erforderlich",
            ),
        ),
    ]
