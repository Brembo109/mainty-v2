"""Health-check endpoints for external monitoring (Uptime Kuma etc.).

Liveness confirms the worker is serving requests. Readiness additionally
checks critical dependencies (database, cache). Both endpoints bypass auth,
CSRF, and i18n so monitoring tools can poll them from outside the network.
"""

from django.core.cache import cache, caches
from django.db import OperationalError, connection
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt


@method_decorator(csrf_exempt, name="dispatch")
@method_decorator(never_cache, name="dispatch")
class LivenessView(View):
    http_method_names = ["get", "head"]

    def get(self, request):
        return JsonResponse({"status": "ok"})


@method_decorator(csrf_exempt, name="dispatch")
@method_decorator(never_cache, name="dispatch")
class ReadinessView(View):
    http_method_names = ["get", "head"]

    def get(self, request):
        db_status = "ok"
        cache_status = "skipped"
        overall_ok = True

        try:
            connection.ensure_connection()
        except (OperationalError, Exception):
            db_status = "error"
            overall_ok = False

        backend = caches["default"].__class__.__module__
        if "dummy" not in backend.lower():
            try:
                cache.set("health", "ok", 5)
                if cache.get("health") != "ok":
                    raise RuntimeError("cache roundtrip failed")
                cache_status = "ok"
            except Exception:
                cache_status = "error"
                overall_ok = False

        payload = {
            "status": "ok" if overall_ok else "error",
            "components": {
                "database": db_status,
                "cache": cache_status,
            },
        }
        return JsonResponse(payload, status=200 if overall_ok else 503)
