import json
from unittest.mock import patch

from django.db import OperationalError
from django.test import Client, TestCase

from apps.audit.models import AuditLog


class LivenessViewTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_liveness_returns_200(self):
        response = self.client.get("/healthz/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), {"status": "ok"})

    def test_head_allowed(self):
        response = self.client.head("/healthz/")
        self.assertEqual(response.status_code, 200)

    def test_post_not_allowed(self):
        response = self.client.post("/healthz/")
        self.assertEqual(response.status_code, 405)

    def test_liveness_not_audited(self):
        before = AuditLog.objects.count()
        self.client.get("/healthz/")
        self.assertEqual(AuditLog.objects.count(), before)


class ReadinessViewTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_readiness_ok(self):
        response = self.client.get("/readyz/")
        self.assertEqual(response.status_code, 200)
        body = json.loads(response.content)
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["components"]["database"], "ok")
        self.assertIn(body["components"]["cache"], ("ok", "skipped"))

    def test_readiness_db_error(self):
        with patch(
            "django.db.backends.base.base.BaseDatabaseWrapper.ensure_connection",
            side_effect=OperationalError("db down"),
        ):
            response = self.client.get("/readyz/")
        self.assertEqual(response.status_code, 503)
        body = json.loads(response.content)
        self.assertEqual(body["status"], "error")
        self.assertEqual(body["components"]["database"], "error")

    def test_post_not_allowed(self):
        response = self.client.post("/readyz/")
        self.assertEqual(response.status_code, 405)
