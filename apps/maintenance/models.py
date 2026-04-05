from datetime import date, timedelta

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.audit.mixins import AuditedModel

from .constants import MAINTENANCE_WARNING_DAYS, MaintenanceStatus


class MaintenancePlan(AuditedModel):
    asset = models.ForeignKey(
        "assets.Asset",
        on_delete=models.CASCADE,
        related_name="maintenance_plans",
        verbose_name=_("Anlage"),
    )
    title = models.CharField(
        max_length=255,
        verbose_name=_("Bezeichnung"),
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Beschreibung / Anweisungen"),
    )
    responsible = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Verantwortlich"),
    )
    interval_days = models.PositiveIntegerField(
        verbose_name=_("Intervall (Tage)"),
        help_text=_("z.B. 365 für jährlich, 90 für quartalsweise"),
    )
    change_reason = models.TextField(
        blank=True,
        verbose_name=_("Änderungsgrund"),
        help_text=_("Begründung der letzten Planänderung"),
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
        ordering = ["asset__name", "title"]
        verbose_name = _("Wartungsplan")
        verbose_name_plural = _("Wartungspläne")

    def __str__(self):
        return f"{self.title} ({self.asset})"

    @property
    def next_due(self):
        """Next maintenance date. Uses annotated last_performed_at if available."""
        if hasattr(self, "last_performed_at") and self.last_performed_at is not None:
            base = self.last_performed_at
            # Max() over DateField returns a date, but guard against datetime
            if hasattr(base, "date"):
                base = base.date()
        else:
            last = self.records.order_by("-performed_at").first()
            base = last.performed_at if last else self.created_at.date()
        return base + timedelta(days=self.interval_days)

    @property
    def status(self):
        today = date.today()
        nd = self.next_due
        if nd < today:
            return MaintenanceStatus.OVERDUE
        if nd <= today + timedelta(days=MAINTENANCE_WARNING_DAYS):
            return MaintenanceStatus.DUE_SOON
        return MaintenanceStatus.OK

    @property
    def status_label(self):
        return MaintenanceStatus.LABEL[self.status]

    @property
    def status_badge_class(self):
        return MaintenanceStatus.BADGE_CLASS[self.status]

    @property
    def days_until_due(self):
        return (self.next_due - date.today()).days


class MaintenanceRecord(AuditedModel):
    plan = models.ForeignKey(
        MaintenancePlan,
        on_delete=models.CASCADE,
        related_name="records",
        verbose_name=_("Wartungsplan"),
    )
    performed_at = models.DateField(
        verbose_name=_("Durchgeführt am"),
    )
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name=_("Durchgeführt von"),
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_("Notizen / Beobachtungen"),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Erfasst am"),
    )

    class Meta:
        ordering = ["-performed_at"]
        verbose_name = _("Wartungsdurchführung")
        verbose_name_plural = _("Wartungsdurchführungen")

    def __str__(self):
        return f"{self.plan.title} — {self.performed_at}"
