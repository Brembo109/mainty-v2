from django.utils.translation import gettext_lazy as _

from apps.core.filters import FilterDimension


CONTRACT_FILTER_DIMENSIONS = [
    FilterDimension("status", _("Status")),
    FilterDimension("vendor", _("Dienstleister")),
    FilterDimension("asset", _("Anlage")),
]
