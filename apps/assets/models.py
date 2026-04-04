from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.audit.mixins import AuditedModel

from .constants import AssetStatus


class Asset(AuditedModel):
    name = models.CharField(
        max_length=255,
        verbose_name=_("Name"),
    )
    location = models.CharField(
        max_length=255,
        verbose_name=_("Standort"),
    )
    serial_number = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("Seriennummer"),
    )
    manufacturer = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Hersteller"),
    )
    status = models.CharField(
        max_length=20,
        choices=AssetStatus.CHOICES,
        default=AssetStatus.FREE,
        db_index=True,
        verbose_name=_("Status"),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Erstellt am"),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Geändert am"),
    )

    class Meta:
        ordering = ["name"]
        verbose_name = _("Anlage")
        verbose_name_plural = _("Anlagen")

    def __str__(self):
        return f"{self.name} ({self.serial_number})"

    @property
    def status_badge_class(self):
        return AssetStatus.BADGE_CLASS.get(self.status, "badge-neutral")
