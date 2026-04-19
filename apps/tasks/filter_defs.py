from django.utils.translation import gettext_lazy as _

from apps.core.filters import FilterDimension


TASK_FILTER_DIMENSIONS = [
    FilterDimension("status", _("Status")),
    FilterDimension("priority", _("Priorität")),
    FilterDimension("assigned_to", _("Zugewiesen")),
    FilterDimension("asset", _("Anlage")),
    FilterDimension(
        "overdue", _("Überfällig"),
        display_map={"yes": _("Ja"), "no": _("Nein")},
    ),
]
