from django.utils.translation import gettext_lazy as _


class ContractStatus:
    ACTIVE = "active"
    EXPIRING = "expiring"
    EXPIRED = "expired"

    CHOICES = [
        (ACTIVE, _("Aktiv")),
        (EXPIRING, _("Läuft aus")),
        (EXPIRED, _("Abgelaufen")),
    ]

    BADGE_CLASS = {
        ACTIVE: "badge-success border border-status-success",
        EXPIRING: "badge-warning border border-status-warning",
        EXPIRED: "badge-danger border border-status-danger",
    }

    LABEL = {
        ACTIVE: _("Aktiv"),
        EXPIRING: _("Läuft aus"),
        EXPIRED: _("Abgelaufen"),
    }
