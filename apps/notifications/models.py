from django.conf import settings
from django.db import models
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


class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name=_("Benutzer"),
    )
    category = models.CharField(
        max_length=40,
        choices=Category.CHOICES,
        verbose_name=_("Kategorie"),
    )
    object_id = models.PositiveIntegerField(verbose_name=_("Objekt-ID"))
    message = models.CharField(max_length=255, verbose_name=_("Meldung"))
    is_read = models.BooleanField(default=False, verbose_name=_("Gelesen"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Erstellt am"))

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Benachrichtigung")
        verbose_name_plural = _("Benachrichtigungen")
        constraints = [
            models.UniqueConstraint(
                fields=["user", "category", "object_id"],
                name="unique_notification_per_user_category_object",
            )
        ]

    def __str__(self):
        return f"{self.user} — {self.category} #{self.object_id}"
