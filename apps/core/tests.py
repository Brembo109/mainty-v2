from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.conf import settings as django_settings
from django.contrib.auth.models import Group
from django.core import mail

from apps.accounts.models import User
from apps.accounts.constants import Role


def _make_user(username, role=None):
    u = User.objects.create_user(username=username, password="pass")
    if role:
        Group.objects.get_or_create(name=role)
        u.set_role(role)
    return u


class SiteConfigModelTest(TestCase):
    def test_get_creates_instance_on_first_call(self):
        from apps.core.models import SiteConfig
        self.assertEqual(SiteConfig.objects.count(), 0)
        config = SiteConfig.get()
        self.assertEqual(SiteConfig.objects.count(), 1)
        self.assertEqual(config.pk, 1)

    def test_get_returns_same_instance_on_second_call(self):
        from apps.core.models import SiteConfig
        first = SiteConfig.get()
        second = SiteConfig.get()
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(SiteConfig.objects.count(), 1)

    def test_get_seeds_contract_warning_days_from_django_settings(self):
        from apps.core.models import SiteConfig
        config = SiteConfig.get()
        expected = getattr(django_settings, "CONTRACT_EXPIRY_WARNING_DAYS", 90)
        self.assertEqual(config.contract_expiry_warning_days, expected)

    def test_get_seeds_email_host_from_django_settings(self):
        from apps.core.models import SiteConfig
        config = SiteConfig.get()
        expected = getattr(django_settings, "EMAIL_HOST", "localhost")
        self.assertEqual(config.email_host, expected)

    def test_get_seeds_site_url_from_django_settings(self):
        from apps.core.models import SiteConfig
        config = SiteConfig.get()
        expected = getattr(django_settings, "SITE_URL", "http://localhost:8000")
        self.assertEqual(config.site_url, expected)


class SettingsViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = _make_user("admin", role=Role.ADMIN)
        self.user = _make_user("user", role=Role.USER)
        self.viewer = _make_user("viewer", role=Role.VIEWER)

    def test_admin_can_get_settings(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("core:settings"))
        self.assertEqual(response.status_code, 200)

    def test_user_gets_403(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("core:settings"))
        self.assertEqual(response.status_code, 403)

    def test_viewer_gets_403(self):
        self.client.force_login(self.viewer)
        response = self.client.get(reverse("core:settings"))
        self.assertEqual(response.status_code, 403)

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(reverse("core:settings"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response["Location"])

    def test_admin_can_save_settings(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("core:settings"), {
            "company_name": "Acme GmbH",
            "site_url": "https://acme.example.com",
            "contract_expiry_warning_days": 60,
            "reminder_email_subject": "[acme] Reminder",
            "email_from": "noreply@acme.example.com",
            "email_host": "smtp.acme.example.com",
            "email_port": 465,
            "email_use_tls": True,
            "email_host_user": "smtp_user",
            "email_host_password": "secret",
        })
        self.assertRedirects(response, reverse("core:settings"), fetch_redirect_response=False)
        from apps.core.models import SiteConfig
        config = SiteConfig.objects.get(pk=1)
        self.assertEqual(config.company_name, "Acme GmbH")
        self.assertEqual(config.contract_expiry_warning_days, 60)

    def test_invalid_form_shows_errors(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("core:settings"), {
            "company_name": "",
            "site_url": "not-a-url",
            "contract_expiry_warning_days": "abc",
            "reminder_email_subject": "[test]",
            "email_from": "noreply@example.com",
            "email_host": "localhost",
            "email_port": 587,
            "email_use_tls": True,
            "email_host_user": "",
            "email_host_password": "",
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)
