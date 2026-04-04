import getpass
import os

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError

from apps.accounts.constants import Role


class Command(BaseCommand):
    help = (
        "Create the initial admin user. "
        "Reads credentials from DJANGO_ADMIN_USER / DJANGO_ADMIN_EMAIL / "
        "DJANGO_ADMIN_PASSWORD env vars, or prompts interactively."
    )

    def handle(self, *args, **options):
        User = get_user_model()

        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write("An admin user already exists. Skipping.")
            return

        username = os.environ.get("DJANGO_ADMIN_USER") or self._prompt("Admin username: ")
        email = os.environ.get("DJANGO_ADMIN_EMAIL") or self._prompt("Admin email: ")
        password = os.environ.get("DJANGO_ADMIN_PASSWORD") or self._prompt_password()

        if not username or not password:
            raise CommandError("Username and password are required.")

        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
        )

        try:
            user.set_role(Role.ADMIN)
        except Group.DoesNotExist:
            self.stderr.write(
                self.style.WARNING(
                    f"Admin user '{username}' created WITHOUT a role — "
                    "the 'Admin' group does not exist yet. "
                    "Run 'bootstrap_roles' first, then assign the role manually."
                )
            )
            return

        self.stdout.write(self.style.SUCCESS(f"Admin user '{username}' created with Admin role."))

    def _prompt(self, label):
        return input(label).strip()

    def _prompt_password(self):
        while True:
            password = getpass.getpass("Admin password: ")
            confirm = getpass.getpass("Confirm password: ")
            if password == confirm:
                return password
            self.stdout.write("Passwords do not match. Try again.")
