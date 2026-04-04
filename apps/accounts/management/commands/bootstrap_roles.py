from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from apps.accounts.constants import Role


class Command(BaseCommand):
    help = "Create the three default roles (Admin, User, Viewer) as Django Groups."

    def handle(self, *args, **options):
        for role_name in Role.ALL:
            _, created = Group.objects.get_or_create(name=role_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f"  Created role: {role_name}"))
            else:
                self.stdout.write(f"  Role already exists: {role_name}")

        self.stdout.write(self.style.SUCCESS("bootstrap_roles complete."))
