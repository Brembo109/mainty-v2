from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ReminderLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("sent_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("recipient_count", models.PositiveIntegerField(default=0)),
                ("summary", models.JSONField(default=dict)),
            ],
            options={
                "verbose_name": "Reminder-Protokoll",
                "verbose_name_plural": "Reminder-Protokolle",
                "ordering": ["-sent_at"],
            },
        ),
    ]
