from django.utils.translation import gettext_lazy as _

from apps.core.filters import FilterDimension


USER_FILTER_DIMENSIONS = [
    FilterDimension("role", _("Rolle")),
    FilterDimension(
        "is_active",
        _("Status"),
        display_map={"yes": _("Aktiv"), "no": _("Inaktiv")},
    ),
]
