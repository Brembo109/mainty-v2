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
