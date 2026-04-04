import threading

_thread_local = threading.local()


def get_current_user():
    """Return the authenticated user for the current request thread, or None."""
    return getattr(_thread_local, "user", None)


def get_current_ip():
    """Return the client IP address for the current request thread, or None."""
    return getattr(_thread_local, "ip_address", None)


def _extract_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


class AuditMiddleware:
    """Store the current request user and IP in thread-local storage.

    Signal handlers use get_current_user() / get_current_ip() to record who
    triggered a model change.  Non-request contexts (management commands,
    Celery tasks) return None — these are logged as 'system' actions.

    Must be placed after AuthenticationMiddleware in MIDDLEWARE.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_local.user = request.user if request.user.is_authenticated else None
        _thread_local.ip_address = _extract_ip(request)
        try:
            return self.get_response(request)
        finally:
            _thread_local.user = None
            _thread_local.ip_address = None
