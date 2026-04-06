import datetime
import itertools
from datetime import date, timedelta

from django.utils import timezone

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
        from apps.notifications.constants import Category
        from apps.notifications.models import Notification
        user = _make_user("model1")
        Notification.objects.create(
            user=user, category=Category.TASK_OVERDUE, object_id=1, message="test"
        )
        with self.assertRaises(IntegrityError):
            Notification.objects.create(
                user=user, category=Category.TASK_OVERDUE, object_id=1, message="dup"
            )

    def test_different_users_same_category_object_allowed(self):
        from apps.notifications.constants import Category
        from apps.notifications.models import Notification
        u1 = _make_user("model2")
        u2 = _make_user("model3")
        Notification.objects.create(
            user=u1, category=Category.TASK_OVERDUE, object_id=1, message="u1"
        )
        Notification.objects.create(
            user=u2, category=Category.TASK_OVERDUE, object_id=1, message="u2"
        )
        self.assertEqual(Notification.objects.count(), 2)


# ── Collector ─────────────────────────────────────────────────────────────────

class CollectorTest(TestCase):
    def setUp(self):
        self.today = date.today()

    def test_overdue_task_included(self):
        from apps.notifications.collector import collect_critical_items
        from apps.notifications.constants import Category
        task = Task.objects.create(
            title="Late Task",
            due_date=self.today - timedelta(days=1),
            status="open",
            priority="medium",
        )
        items = collect_critical_items(self.today, 90)
        keys = [(cat, oid) for cat, oid, _ in items]
        self.assertIn((Category.TASK_OVERDUE, task.pk), keys)

    def test_done_task_not_included(self):
        from apps.notifications.collector import collect_critical_items
        from apps.notifications.constants import Category
        Task.objects.create(
            title="Done Task",
            due_date=self.today - timedelta(days=1),
            status="done",
            priority="medium",
        )
        items = collect_critical_items(self.today, 90)
        keys = [(cat, oid) for cat, oid, _ in items]
        task_overdue_ids = [oid for cat, oid in keys if cat == Category.TASK_OVERDUE]
        self.assertEqual(task_overdue_ids, [])

    def test_expired_contract_included(self):
        from apps.notifications.collector import collect_critical_items
        from apps.notifications.constants import Category
        contract = Contract.objects.create(
            title="Old Contract",
            vendor="Vendor X",
            start_date=self.today - timedelta(days=400),
            end_date=self.today - timedelta(days=1),
        )
        items = collect_critical_items(self.today, 90)
        keys = [(cat, oid) for cat, oid, _ in items]
        self.assertIn((Category.CONTRACT_EXPIRED, contract.pk), keys)

    def test_overdue_maintenance_included(self):
        from apps.notifications.collector import collect_critical_items
        from apps.notifications.constants import Category
        asset = _make_asset()
        plan = MaintenancePlan.objects.create(
            asset=asset, title="Test Plan", interval_days=30, responsible="",
        )
        # Force created_at 60 days ago → next_due = created_at + 30 = 30 days ago (overdue)
        MaintenancePlan.objects.filter(pk=plan.pk).update(
            created_at=timezone.make_aware(
                datetime.datetime.combine(self.today - timedelta(days=60), datetime.time.min)
            )
        )
        items = collect_critical_items(self.today, 90)
        keys = [(cat, oid) for cat, oid, _ in items]
        self.assertIn((Category.MAINTENANCE_OVERDUE, plan.pk), keys)


# ── Context Processor ─────────────────────────────────────────────────────────

class ContextProcessorTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_unauthenticated_returns_empty_dict(self):
        from apps.notifications.context_processors import notifications as cp
        from apps.notifications.models import Notification
        request = self.factory.get("/")
        request.user = AnonymousUser()
        result = cp(request)
        self.assertEqual(result, {})
        self.assertEqual(Notification.objects.count(), 0)

    def test_badge_count_equals_unread_notifications(self):
        from apps.notifications.context_processors import notifications as cp
        user = _make_user("cp1")
        Task.objects.create(
            title="Late",
            due_date=date.today() - timedelta(days=1),
            status="open",
            priority="medium",
        )
        request = self.factory.get("/")
        request.user = user
        result = cp(request)
        self.assertIn("notification_unread_count", result)
        self.assertEqual(result["notification_unread_count"], 1)

    def test_is_read_preserved_on_resync(self):
        from apps.notifications.context_processors import notifications as cp
        from apps.notifications.models import Notification
        user = _make_user("cp2")
        Task.objects.create(
            title="Late",
            due_date=date.today() - timedelta(days=1),
            status="open",
            priority="medium",
        )
        request = self.factory.get("/")
        request.user = user
        cp(request)
        Notification.objects.filter(user=user).update(is_read=True)
        cp(request)
        self.assertEqual(
            Notification.objects.filter(user=user, is_read=True).count(), 1
        )

    def test_auto_resolve_deletes_stale_notification(self):
        from apps.notifications.context_processors import notifications as cp
        from apps.notifications.models import Notification
        user = _make_user("cp3")
        task = Task.objects.create(
            title="Late",
            due_date=date.today() - timedelta(days=1),
            status="open",
            priority="medium",
        )
        request = self.factory.get("/")
        request.user = user
        cp(request)
        self.assertEqual(Notification.objects.filter(user=user).count(), 1)
        # Resolve: mark task done → no longer critical
        task.status = "done"
        task.save()
        cp(request)
        self.assertEqual(Notification.objects.filter(user=user).count(), 0)
