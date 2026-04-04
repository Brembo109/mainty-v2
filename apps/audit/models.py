from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _

from .constants import Action


class AuditLog(models.Model):
    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name=_("Zeitstempel"),
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name=_("Benutzer"),
    )
    # Username snapshot so entries remain readable after a user is deleted.
    actor_username = models.CharField(
        max_length=150,
        blank=True,
        verbose_name=_("Benutzername"),
    )
    action = models.CharField(
        max_length=20,
        choices=Action.CHOICES,
        db_index=True,
        verbose_name=_("Aktion"),
    )
    content_type = models.ForeignKey(
        ContentType,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_("Objekttyp"),
    )
    object_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Objekt-ID"),
    )
    # Human-readable snapshot of the object at time of event.
    object_repr = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Objekt"),
    )
    # For UPDATE: {field: [old_value, new_value]}.  For CREATE: all field values.
    changes = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Änderungen"),
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_("IP-Adresse"),
    )

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = _("Audit-Eintrag")
        verbose_name_plural = _("Audit-Trail")

    def __str__(self):
        return f"{self.timestamp:%Y-%m-%d %H:%M:%S} | {self.actor_username} | {self.action}"
