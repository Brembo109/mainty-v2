from django.utils.translation import gettext_lazy as _

# Days before next_due to show DUE_SOON warning
MAINTENANCE_WARNING_DAYS = 30


class MaintenanceStatus:
    OK = "ok"
    DUE_SOON = "due_soon"
    OVERDUE = "overdue"

    BADGE_CLASS = {
        OK: "status-dot status-dot-ok",
        DUE_SOON: "status-dot status-dot-warn",
        OVERDUE: "status-dot status-dot-danger",
    }

    LABEL = {
        OK: _("OK"),
        DUE_SOON: _("Fällig bald"),
        OVERDUE: _("Überfällig"),
    }
