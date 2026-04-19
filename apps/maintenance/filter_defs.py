from django.utils.translation import gettext_lazy as _

from apps.core.filters import FilterDimension


MAINTENANCE_FILTER_DIMENSIONS = [
    FilterDimension("status", _("Status")),
    FilterDimension("asset", _("Anlage")),
    FilterDimension("responsible", _("Verantwortlich")),
]
