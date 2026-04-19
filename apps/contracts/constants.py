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
        ACTIVE: "status-dot status-dot-ok",
        EXPIRING: "status-dot status-dot-warn",
        EXPIRED: "status-dot status-dot-danger",
    }

    LABEL = {
        ACTIVE: _("Aktiv"),
        EXPIRING: _("Läuft aus"),
        EXPIRED: _("Abgelaufen"),
    }
