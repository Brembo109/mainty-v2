from django.utils.translation import gettext_lazy as _

# Days before next_due to show DUE_SOON warning
MAINTENANCE_WARNING_DAYS = 30


class MaintenanceStatus:
    OK = "ok"
    DUE_SOON = "due_soon"
    OVERDUE = "overdue"

    BADGE_CLASS = {
        OK: "badge-success border border-status-success",
        DUE_SOON: "badge-warning border border-status-warning",
        OVERDUE: "badge-danger border border-status-danger",
    }

    LABEL = {
        OK: _("OK"),
        DUE_SOON: _("Fällig bald"),
        OVERDUE: _("Überfällig"),
    }
