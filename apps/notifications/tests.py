import itertools
from datetime import date, timedelta

from django.contrib.auth.models import AnonymousUser, Group
from django.db import IntegrityError
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse

from apps.accounts.constants import Role
from apps.accounts.models import User
from apps.assets.constants import Department
from apps.assets.models import Asset
from apps.contracts.models import Contract
from apps.maintenance.models import MaintenancePlan
from apps.tasks.models import Task

# Note: many imports above are used by test classes added in Tasks 2–4.

_counter = itertools.count(1)


def _make_user(username="user", role=Role.USER):
    c = next(_counter)
    u = User.objects.create_user(username=f"{username}_{c}", password="pass")
    Group.objects.get_or_create(name=role)
    u.set_role(role)
    return u


def _make_asset():
    c = next(_counter)
    return Asset.objects.create(
        name=f"Asset {c}",
        serial_number=f"SN-{c:04d}",
        location="Halle 1",
        device_code=f"DEV-{c:02d}",
        inventory_number=f"INV-{c:03d}",
        department=Department.HERSTELLUNG,
    )


# ── Model ─────────────────────────────────────────────────────────────────────

class NotificationModelTest(TestCase):
    def test_unique_constraint_prevents_duplicate(self):
        from apps.notifications.models import Category, Notification
        user = _make_user("model1")
        Notification.objects.create(
            user=user, category=Category.TASK_OVERDUE, object_id=1, message="test"
        )
        with self.assertRaises(IntegrityError):
            Notification.objects.create(
                user=user, category=Category.TASK_OVERDUE, object_id=1, message="dup"
            )

    def test_different_users_same_category_object_allowed(self):
        from apps.notifications.models import Category, Notification
        u1 = _make_user("model2")
        u2 = _make_user("model3")
        Notification.objects.create(
            user=u1, category=Category.TASK_OVERDUE, object_id=1, message="u1"
        )
        Notification.objects.create(
            user=u2, category=Category.TASK_OVERDUE, object_id=1, message="u2"
        )
        self.assertEqual(Notification.objects.count(), 2)
