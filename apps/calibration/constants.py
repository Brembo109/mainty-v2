from django.utils.translation import gettext_lazy as _

CALIBRATION_WARNING_DAYS = 30


class CalibrationStatus:
    NEVER = "never"
    AT_LAB = "at_lab"
    VALID = "valid"
    DUE_SOON = "due_soon"
    OVERDUE = "overdue"

    CHOICES = [
        (NEVER, _("Nie kalibriert")),
        (AT_LAB, _("Beim Labor")),
        (VALID, _("Gültig")),
        (DUE_SOON, _("Bald fällig")),
        (OVERDUE, _("Überfällig")),
    ]

    LABEL = {
        NEVER: _("Nie kalibriert"),
        AT_LAB: _("Beim Labor"),
        VALID: _("Gültig"),
        DUE_SOON: _("Bald fällig"),
        OVERDUE: _("Überfällig"),
    }

    BADGE_CLASS = {
        NEVER: "status-dot status-dot-idle",
        AT_LAB: "status-dot status-dot-info",
        VALID: "status-dot status-dot-ok",
        DUE_SOON: "status-dot status-dot-warn",
        OVERDUE: "status-dot status-dot-danger",
    }


class CalibrationResult:
    PASS = "pass"
    FAIL = "fail"
    CONDITIONAL = "conditional"

    CHOICES = [
        (PASS, _("Bestanden")),
        (FAIL, _("Nicht bestanden")),
        (CONDITIONAL, _("Bedingt bestanden")),
    ]

    LABEL = {
        PASS: _("Bestanden"),
        FAIL: _("Nicht bestanden"),
        CONDITIONAL: _("Bedingt bestanden"),
    }

    BADGE_CLASS = {
        PASS: "status-dot status-dot-ok",
        FAIL: "status-dot status-dot-danger",
        CONDITIONAL: "status-dot status-dot-warn",
    }
