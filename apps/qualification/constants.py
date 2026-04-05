from django.utils.translation import gettext_lazy as _

# Days before next_due to show DUE_SOON warning
QUALIFICATION_WARNING_DAYS = 60


class QualType:
    IQ = "IQ"
    OQ = "OQ"
    PQ = "PQ"

    CHOICES = [
        (IQ, _("IQ — Installationsqualifizierung")),
        (OQ, _("OQ — Operationsqualifizierung")),
        (PQ, _("PQ — Performanzqualifizierung")),
    ]

    LABEL = {
        IQ: _("Installationsqualifizierung"),
        OQ: _("Operationsqualifizierung"),
        PQ: _("Performanzqualifizierung"),
    }


class QualStatus:
    OK = "ok"
    DUE_SOON = "due_soon"
    OVERDUE = "overdue"
    NEVER_SIGNED = "never_signed"

    BADGE_CLASS = {
        OK: "badge-success border border-status-success",
        DUE_SOON: "badge-warning border border-status-warning",
        OVERDUE: "badge-danger border border-status-danger",
        NEVER_SIGNED: "badge-neutral border border-border",
    }

    LABEL = {
        OK: _("OK"),
        DUE_SOON: _("Fällig bald"),
        OVERDUE: _("Überfällig"),
        NEVER_SIGNED: _("Nie signiert"),
    }
