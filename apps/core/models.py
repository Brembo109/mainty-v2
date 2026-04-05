from django.db import models
from django.utils.translation import gettext_lazy as _


class ReminderLog(models.Model):
    """Tracks when reminder emails were last sent to prevent duplicate daily sends."""

    sent_at = models.DateTimeField(auto_now_add=True, db_index=True)
    recipient_count = models.PositiveIntegerField(default=0)
    # Serialised summary of what was included (for audit purposes)
    summary = models.JSONField(default=dict)

    class Meta:
        ordering = ["-sent_at"]
        verbose_name = _("Reminder-Protokoll")
        verbose_name_plural = _("Reminder-Protokolle")

    def __str__(self):
        return f"{self.sent_at:%Y-%m-%d %H:%M} — {self.recipient_count} Empfänger"
