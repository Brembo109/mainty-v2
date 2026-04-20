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
    short_code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Kürzel"),
        help_text=_("Internes Kürzel, eindeutig pro Gerät (z.B. HPLC-A1)."),
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
    logbook_ref = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Logbuch (LOG)"),
    )
    logbook_url = models.URLField(
        blank=True,
        verbose_name=_("Logbuch-Link"),
    )
    bal_ref = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Bedienungsanleitung (BAL)"),
    )
    bal_url = models.URLField(
        blank=True,
        verbose_name=_("BAL-Link"),
    )
    requalification_interval_years = models.PositiveSmallIntegerField(
        default=4,
        verbose_name=_("Requalifizierungs-Intervall (Jahre)"),
        help_text=_("Intervall für die turnusmäßige Requalifizierung (RQ)."),
    )
    pq_required = models.BooleanField(
        default=False,
        verbose_name=_("PQ erforderlich"),
        help_text=_("Ist eine Performance-Qualifizierung für diese Anlage vorgesehen?"),
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
        return AssetStatus.BADGE_CLASS.get(self.status, "status-dot status-dot-idle")

    @property
    def status_dot(self):
        return {
            "class": self.status_badge_class,
            "label": self.get_status_display(),
        }

    def tab_count(self, slug):
        from django.contrib.contenttypes.models import ContentType
        from apps.audit.models import AuditLog

        documents_count = sum(1 for ref in (self.logbook_ref, self.bal_ref) if ref)
        if slug == "audit":
            return AuditLog.objects.filter(
                content_type=ContentType.objects.get_for_model(Asset),
                object_id=str(self.pk),
            ).count()
        counts = {
            "overview": None,
            "maintenance": self.maintenance_plans.count(),
            "qualification": self.qualification_cycles.count(),
            "documents": documents_count,
        }
        return counts.get(slug)

    def meta_items(self):
        items = [
            {"label": _("Standort"), "value_html": self.location or "—"},
            {"label": _("Zugehörigkeit"), "value_html": self.get_department_display()},
            {
                "label": _("Verantwortlich"),
                "value_html": (
                    self.responsible.get_full_name() or self.responsible.username
                    if self.responsible
                    else "—"
                ),
            },
            {
                "label": _("Stellvertreter"),
                "value_html": (
                    self.deputy.get_full_name() or self.deputy.username
                    if self.deputy
                    else "—"
                ),
            },
        ]
        if self.manufacturer:
            items.append({"label": _("Hersteller"), "value_html": self.manufacturer})
        return items
