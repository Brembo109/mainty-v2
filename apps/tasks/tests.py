from django.test import TestCase, Client
from django.urls import reverse

from apps.accounts.models import User
from apps.assets.models import Asset
from apps.assets.constants import Department
from apps.tasks.forms import TaskCreateForm
from apps.tasks.models import Task


_counter = 0


def _make_user(username="writer", role=None):
    from django.contrib.auth.models import Group
    from apps.accounts.constants import Role
    global _counter
    _counter += 1
    u = User.objects.create_user(username=f"{username}_{_counter}", password="pass")
    if role:
        Group.objects.get_or_create(name=role)
        u.set_role(role)
    return u


def _make_asset(name=None):
    global _counter
    _counter += 1
    return Asset.objects.create(
        name=name or f"Asset {_counter}",
        serial_number=f"SN-{_counter:04d}",
        location="Halle 1",
        device_code=f"DEV-{_counter:02d}",
        inventory_number=f"INV-{_counter:03d}",
        department=Department.HERSTELLUNG,
    )


class TaskCreateFormAssetsFieldTest(TestCase):
    def test_assets_field_present_in_create_form(self):
        form = TaskCreateForm()
        self.assertIn("assets", form.fields)

    def test_assets_field_not_required(self):
        form = TaskCreateForm()
        self.assertFalse(form.fields["assets"].required)

    def test_asset_field_not_in_create_form(self):
        """Single-asset 'asset' FK field must NOT be in TaskCreateForm."""
        form = TaskCreateForm()
        self.assertNotIn("asset", form.fields)

    def test_form_valid_with_no_assets(self):
        form = TaskCreateForm(data={
            "title": "Test Task",
            "priority": "medium",
            "status": "open",
            "assets": [],
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_form_valid_with_multiple_assets(self):
        a1 = _make_asset()
        a2 = _make_asset()
        form = TaskCreateForm(data={
            "title": "Multi Asset Task",
            "priority": "medium",
            "status": "open",
            "assets": [a1.pk, a2.pk],
        })
        self.assertTrue(form.is_valid(), form.errors)
