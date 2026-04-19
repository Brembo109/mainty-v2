from django.utils.translation import gettext_lazy as _

from apps.core.filters import FilterDimension


AUDIT_FILTER_DIMENSIONS = [
    FilterDimension("action", _("Aktion")),
    FilterDimension("model", _("Objekttyp")),
]
