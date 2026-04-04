from django.contrib import admin

from .models import Asset


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ["name", "serial_number", "location", "manufacturer", "status"]
    list_filter = ["status"]
    search_fields = ["name", "serial_number", "location", "manufacturer"]
