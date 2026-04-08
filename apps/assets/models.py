from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.audit.mixins import AuditedModel

from .constants import AssetStatus, Department


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
    device_code = models.CharField(
        max_length=50,
        verbose_name=_("Gerätekürzel"),
    )
    inventory_number = models.CharField(
        max_length=100,
        verbose_name=_("Inventarnummer"),
    )
    service_provider = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Servicedienstleister"),
    )
    department = models.CharField(
        max_length=30,
        choices=Department.CHOICES,
        default=Department.HERSTELLUNG,  # migration default only; form enforces explicit choice
        db_index=True,
        verbose_name=_("Zugehörigkeit"),
    )
    responsible = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="responsible_assets",
        verbose_name=_("Verantwortlicher"),
    )
    deputy = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="deputy_assets",
        verbose_name=_("Stellvertreter"),
    )
    status = models.CharField(
        max_length=20,
        choices=AssetStatus.CHOICES,
        default=AssetStatus.FREE,
        db_index=True,
        verbose_name=_("Status"),
    )
    lock_reason = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_("Sperrgrund"),
    )
    owner = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Eigentümer"),
    )
    log_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Logbuch (LOG)"),
    )
    manual_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Bedienungsanleitung (BAL)"),
    )
    has_computer = models.BooleanField(
        default=False,
        verbose_name=_("Hat zugehörigen Computer"),
    )
    computer_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Computername"),
    )
    computer_ip = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("IP-Adresse"),
    )
    computer_network_port = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Netzwerkdose"),
    )
    computer_windows_version = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Windows-Version"),
    )
    computer_software_version = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Software-Version"),
    )
    computer_backups_enabled = models.BooleanField(
        default=False,
        verbose_name=_("Backups eingerichtet"),
    )
    computer_backups_description = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_("Backup-Beschreibung"),
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
    def is_locked(self):
        return self.status == AssetStatus.LOCKED

    @property
    def status_badge_class(self):
        return AssetStatus.BADGE_CLASS.get(self.status, "badge-neutral")
