from django.utils.translation import gettext_lazy as _

from apps.core.filters import FilterDimension


ASSET_FILTER_DIMENSIONS = [
    FilterDimension("status", _("Status")),
    FilterDimension("location", _("Standort")),
    FilterDimension("department", _("Abteilung")),
    FilterDimension("responsible", _("Verantwortlich")),
    FilterDimension("manufacturer", _("Hersteller")),
    FilterDimension(
        "has_contract", _("Servicevertrag"),
        display_map={"yes": _("Vorhanden"), "no": _("Fehlt")},
    ),
]
