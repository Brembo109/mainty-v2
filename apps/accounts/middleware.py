from datetime import timedelta

from django.conf import settings
from django.shortcuts import redirect
from django.utils import timezone

# URL path prefixes that bypass the expiry check.
# All auth routes (/accounts/), admin, health, and static files are exempt.
_EXEMPT_PREFIXES = (
    "/accounts/",
    "/admin/",
    "/health/",
    "/static/",
    "/i18n/",
)


class PasswordExpiryMiddleware:
    """Redirect authenticated users to change their password when it has expired.

    Expiry threshold is controlled by the PASSWORD_EXPIRY_DAYS setting (default 90).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not self._is_exempt(request.path_info):
            changed_at = request.user.password_changed_at
            if changed_at is None:
                return redirect("accounts:password_expired")
            max_age = timedelta(days=getattr(settings, "PASSWORD_EXPIRY_DAYS", 90))
            if (timezone.now() - changed_at) >= max_age:
                return redirect("accounts:password_expired")

        return self.get_response(request)

    def _is_exempt(self, path):
        # Check bare prefixes
        for prefix in _EXEMPT_PREFIXES:
            if path.startswith(prefix):
                return True
        # Check language-prefixed variants (e.g. /en/accounts/ when using i18n_patterns)
        for lang_code, _ in settings.LANGUAGES:
            for prefix in _EXEMPT_PREFIXES:
                if path.startswith(f"/{lang_code}{prefix}"):
                    return True
        return False
