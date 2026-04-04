from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from apps.core.views import health

# Non-i18n routes (health must be at a fixed URL for infrastructure monitoring)
urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),
    path("health/", health, name="health"),
]

# i18n-prefixed routes (prefix_default_language=False keeps /de/ optional)
urlpatterns += i18n_patterns(
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls")),
    path("audit/", include("apps.audit.urls")),
    path("", include("apps.core.urls")),
    prefix_default_language=False,
)
