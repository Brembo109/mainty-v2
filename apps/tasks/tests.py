import itertools

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import Group

from apps.accounts.models import User
from apps.assets.models import Asset
from apps.assets.constants import Department
from apps.tasks.forms import TaskCreateForm
from apps.tasks.models import Task


_counter = itertools.count(1)


def _make_user(username="writer", role=None):
    global _counter
    c = next(_counter)
    u = User.objects.create_user(username=f"{username}_{c}", password="pass")
    if role:
        Group.objects.get_or_create(name=role)
        u.set_role(role)
    return u


def _make_asset(name=None):
    global _counter
    c = next(_counter)
    return Asset.objects.create(
        name=name or f"Asset {c}",
        serial_number=f"SN-{c:04d}",
        location="Halle 1",
        device_code=f"DEV-{c:02d}",
        inventory_number=f"INV-{c:03d}",
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


from apps.accounts.constants import Role


class TaskCreateViewBulkTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = _make_user(role=Role.USER)
        self.client.force_login(self.user)

    def test_create_task_no_asset(self):
        response = self.client.post(reverse("tasks:create"), {
            "title": "No Asset Task",
            "priority": "medium",
            "status": "open",
            "assets": [],
        })
        self.assertEqual(Task.objects.count(), 1)
        task = Task.objects.first()
        self.assertIsNone(task.asset)
        self.assertRedirects(response, reverse("tasks:detail", kwargs={"pk": task.pk}),
                             fetch_redirect_response=False)

    def test_create_task_single_asset(self):
        asset = _make_asset()
        response = self.client.post(reverse("tasks:create"), {
            "title": "Single Asset Task",
            "priority": "medium",
            "status": "open",
            "assets": [asset.pk],
        })
        self.assertEqual(Task.objects.count(), 1)
        task = Task.objects.first()
        self.assertEqual(task.asset, asset)
        self.assertRedirects(response, reverse("tasks:detail", kwargs={"pk": task.pk}),
                             fetch_redirect_response=False)

    def test_create_task_multiple_assets_creates_one_per_asset(self):
        a1 = _make_asset()
        a2 = _make_asset()
        a3 = _make_asset()
        response = self.client.post(reverse("tasks:create"), {
            "title": "Multi Asset Task",
            "priority": "high",
            "status": "open",
            "assets": [a1.pk, a2.pk, a3.pk],
        })
        self.assertEqual(Task.objects.count(), 3)
        asset_pks = set(Task.objects.values_list("asset_id", flat=True))
        self.assertEqual(asset_pks, {a1.pk, a2.pk, a3.pk})
        self.assertRedirects(response, reverse("tasks:list"),
                             fetch_redirect_response=False)

    def test_create_task_multiple_assets_all_have_same_title(self):
        a1 = _make_asset()
        a2 = _make_asset()
        self.client.post(reverse("tasks:create"), {
            "title": "Jährliche Kalibrierung",
            "priority": "high",
            "status": "open",
            "assets": [a1.pk, a2.pk],
        })
        titles = list(Task.objects.values_list("title", flat=True))
        self.assertEqual(titles, ["Jährliche Kalibrierung", "Jährliche Kalibrierung"])

    def test_create_task_multiple_assets_success_message(self):
        a1 = _make_asset()
        a2 = _make_asset()
        response = self.client.post(reverse("tasks:create"), {
            "title": "Kalibrierung",
            "priority": "medium",
            "status": "open",
            "assets": [a1.pk, a2.pk],
        }, follow=True)
        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("2", str(messages[0]))
