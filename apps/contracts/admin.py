from django.contrib import admin

from .models import Contract


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ["title", "contract_number", "vendor", "start_date", "end_date"]
    list_filter = ["vendor"]
    search_fields = ["title", "contract_number", "vendor"]
    filter_horizontal = ["assets"]
