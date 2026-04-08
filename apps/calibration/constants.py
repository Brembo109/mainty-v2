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
        NEVER: "badge-neutral",
        AT_LAB: "badge-neutral border border-border",
        VALID: "badge-success border border-status-success",
        DUE_SOON: "badge-warning border border-status-warning",
        OVERDUE: "badge-danger border border-status-danger",
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
        PASS: "badge-success border border-status-success",
        FAIL: "badge-danger border border-status-danger",
        CONDITIONAL: "badge-warning border border-status-warning",
    }
