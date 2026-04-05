from django.contrib import admin

from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ["title", "status", "priority", "assigned_to", "due_date", "asset"]
    list_filter = ["status", "priority"]
    search_fields = ["title", "assigned_to__username", "asset__name"]
