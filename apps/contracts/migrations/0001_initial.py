from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("assets", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Contract",
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
                (
                    "title",
                    models.CharField(max_length=255, verbose_name="Bezeichnung"),
                ),
                (
                    "contract_number",
                    models.CharField(
                        blank=True, max_length=100, verbose_name="Vertragsnummer"
                    ),
                ),
                (
                    "vendor",
                    models.CharField(max_length=255, verbose_name="Vertragspartner"),
                ),
                ("start_date", models.DateField(verbose_name="Vertragsbeginn")),
                (
                    "end_date",
                    models.DateField(db_index=True, verbose_name="Vertragsende"),
                ),
                (
                    "notes",
                    models.TextField(blank=True, verbose_name="Notizen"),
                ),
                (
                    "assets",
                    models.ManyToManyField(
                        blank=True,
                        related_name="contracts",
                        to="assets.asset",
                        verbose_name="Anlagen",
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
                "verbose_name": "Servicevertrag",
                "verbose_name_plural": "Serviceverträge",
                "ordering": ["end_date"],
            },
        ),
    ]
