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


class QualStage:
    """Stage model for the Qualification records (PR #7).

    Six one-time stages for the initial qualification, plus RQ for the
    recurring requalification cycles.
    """

    QP = "QP"
    DQ = "DQ"
    IQ = "IQ"
    OQ = "OQ"
    PQ = "PQ"
    QB = "QB"
    RQ = "RQ"

    FIRST_STAGES = [QP, DQ, IQ, OQ, PQ, QB]

    CHOICES = [
        (QP, _("QP — Qualifizierungsplan")),
        (DQ, _("DQ — Designqualifizierung")),
        (IQ, _("IQ — Installationsqualifizierung")),
        (OQ, _("OQ — Operationsqualifizierung")),
        (PQ, _("PQ — Performanzqualifizierung")),
        (QB, _("QB — Qualifizierungsbericht")),
        (RQ, _("RQ — Requalifizierung")),
    ]

    LONG_LABEL = {
        QP: _("Qualifizierungsplan"),
        DQ: _("Designqualifizierung"),
        IQ: _("Installationsqualifizierung"),
        OQ: _("Operationsqualifizierung"),
        PQ: _("Performanzqualifizierung"),
        QB: _("Qualifizierungsbericht"),
        RQ: _("Requalifizierung"),
    }


class QualStatus:
    OK = "ok"
    DUE_SOON = "due_soon"
    OVERDUE = "overdue"
    NEVER_SIGNED = "never_signed"

    BADGE_CLASS = {
        OK: "status-dot status-dot-ok",
        DUE_SOON: "status-dot status-dot-warn",
        OVERDUE: "status-dot status-dot-danger",
        NEVER_SIGNED: "status-dot status-dot-idle",
    }

    LABEL = {
        OK: _("OK"),
        DUE_SOON: _("Fällig bald"),
        OVERDUE: _("Überfällig"),
        NEVER_SIGNED: _("Nie signiert"),
    }
