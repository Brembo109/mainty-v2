from django.test import TestCase, Client
from django.urls import reverse

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


class SetThemeViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="themeuser", password="testpass123")
        self.client.login(username="themeuser", password="testpass123")

    def test_set_theme_to_light(self):
        response = self.client.post(
            reverse("accounts:set_theme"),
            {"theme": "light", "next": "/"},
        )
        self.assertRedirects(response, "/", fetch_redirect_response=False)
        self.user.refresh_from_db()
        self.assertEqual(self.user.theme, "light")

    def test_set_theme_to_dark(self):
        self.user.theme = "light"
        self.user.save(update_fields=["theme"])
        self.client.post(
            reverse("accounts:set_theme"),
            {"theme": "dark", "next": "/"},
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.theme, "dark")

    def test_invalid_theme_ignored(self):
        self.client.post(
            reverse("accounts:set_theme"),
            {"theme": "rainbow", "next": "/"},
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.theme, "dark")  # unchanged

    def test_requires_login(self):
        self.client.logout()
        response = self.client.post(
            reverse("accounts:set_theme"),
            {"theme": "light", "next": "/"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response["Location"])
