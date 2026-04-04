from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "actor_username", "action", "content_type", "object_repr", "ip_address")
    list_filter = ("action", "content_type")
    search_fields = ("actor_username", "object_repr")
    readonly_fields = (
        "timestamp", "actor", "actor_username", "action",
        "content_type", "object_id", "object_repr", "changes", "ip_address",
    )
    date_hierarchy = "timestamp"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
