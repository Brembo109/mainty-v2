from django.utils.translation import gettext_lazy as _

from apps.core.filters import FilterDimension


QUALIFICATION_FILTER_DIMENSIONS = [
    FilterDimension("status", _("Status")),
    FilterDimension(
        "qual_type", _("Typ"),
        display_map={"IQ": "IQ", "OQ": "OQ", "PQ": "PQ"},
    ),
    FilterDimension("asset", _("Anlage")),
]
