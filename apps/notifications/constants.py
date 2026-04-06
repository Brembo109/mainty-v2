from django.utils.translation import gettext_lazy as _


class Category:
    MAINTENANCE_OVERDUE = "maintenance_overdue"
    MAINTENANCE_DUE_SOON = "maintenance_due_soon"
    QUALIFICATION_OVERDUE = "qualification_overdue"
    QUALIFICATION_DUE_SOON = "qualification_due_soon"
    QUALIFICATION_NEVER_SIGNED = "qualification_never_signed"
    CONTRACT_EXPIRING = "contract_expiring"
    CONTRACT_EXPIRED = "contract_expired"
    TASK_OVERDUE = "task_overdue"

    CHOICES = [
        (MAINTENANCE_OVERDUE, _("Wartung überfällig")),
        (MAINTENANCE_DUE_SOON, _("Wartung fällig bald")),
        (QUALIFICATION_OVERDUE, _("Qualifizierung überfällig")),
        (QUALIFICATION_DUE_SOON, _("Qualifizierung fällig bald")),
        (QUALIFICATION_NEVER_SIGNED, _("Qualifizierung nie signiert")),
        (CONTRACT_EXPIRING, _("Vertrag läuft aus")),
        (CONTRACT_EXPIRED, _("Vertrag abgelaufen")),
        (TASK_OVERDUE, _("Aufgabe überfällig")),
    ]
