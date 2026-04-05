from django.contrib import admin

from .models import QualificationCycle, QualificationSignature


@admin.register(QualificationCycle)
class QualificationCycleAdmin(admin.ModelAdmin):
    list_display = ["title", "asset", "qual_type", "interval_days", "responsible"]
    list_filter = ["qual_type"]
    search_fields = ["title", "asset__name"]


@admin.register(QualificationSignature)
class QualificationSignatureAdmin(admin.ModelAdmin):
    list_display = ["cycle", "signed_by_username", "signed_at", "meaning", "ip_address"]
    readonly_fields = ["cycle", "signed_by", "signed_by_username", "signed_at",
                       "meaning", "notes", "ip_address", "created_at"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
