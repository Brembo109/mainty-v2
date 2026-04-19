from django.utils.translation import gettext_lazy as _

from apps.core.filters import FilterDimension


CALIBRATION_FILTER_DIMENSIONS = [
    FilterDimension("status", _("Status")),
    FilterDimension("location", _("Standort")),
    FilterDimension("responsible", _("Verantwortlich")),
]
