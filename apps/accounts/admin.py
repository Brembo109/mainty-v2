from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "email", "get_role", "is_active", "date_joined")
    list_filter = ("groups", "is_active", "is_staff")
    fieldsets = BaseUserAdmin.fieldsets + (
        (_("Passwort-Rotation"), {"fields": ("password_changed_at",)}),
    )
    readonly_fields = ("password_changed_at",)

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("groups")

    @admin.display(description=_("Rolle"))
    def get_role(self, obj):
        return obj.role or "—"
