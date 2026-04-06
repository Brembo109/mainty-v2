from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from .constants import Category


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
