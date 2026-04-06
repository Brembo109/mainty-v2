# Generated migration for adding theme field to User model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='theme',
            field=models.CharField(
                choices=[('dark', 'Dark'), ('light', 'Light')],
                default='dark',
                max_length=5,
                verbose_name='Theme',
            ),
        ),
    ]
