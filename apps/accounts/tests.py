from django.test import TestCase

from apps.accounts.models import User


class UserThemeDefaultTest(TestCase):
    def test_theme_defaults_to_dark(self):
        user = User.objects.create_user(username="testuser", password="testpass123")
        self.assertEqual(user.theme, "dark")

    def test_theme_can_be_set_to_light(self):
        user = User.objects.create_user(username="testuser2", password="testpass123")
        user.theme = "light"
        user.save(update_fields=["theme"])
        user.refresh_from_db()
        self.assertEqual(user.theme, "light")
