from django.contrib import admin

from .models import MaintenancePlan, MaintenanceRecord


class MaintenanceRecordInline(admin.TabularInline):
    model = MaintenanceRecord
    extra = 0
    fields = ["performed_at", "performed_by", "notes"]
    readonly_fields = ["created_at"]


@admin.register(MaintenancePlan)
class MaintenancePlanAdmin(admin.ModelAdmin):
    list_display = ["title", "asset", "interval_days", "responsible"]
    list_filter = ["asset"]
    search_fields = ["title", "asset__name", "responsible"]
    inlines = [MaintenanceRecordInline]


@admin.register(MaintenanceRecord)
class MaintenanceRecordAdmin(admin.ModelAdmin):
    list_display = ["plan", "performed_at", "performed_by"]
    list_filter = ["plan__asset"]
    search_fields = ["plan__title"]
