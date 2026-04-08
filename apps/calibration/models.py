from datetime import date, timedelta

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.audit.mixins import AuditedModel

from .constants import CALIBRATION_WARNING_DAYS, CalibrationResult, CalibrationStatus


class TestEquipment(AuditedModel):
    name = models.CharField(
        max_length=255,
        verbose_name=_("Bezeichnung"),
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
    location = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Standort"),
    )
    calibration_interval_days = models.PositiveIntegerField(
        verbose_name=_("Kalibrierintervall (Tage)"),
        help_text=_("z.B. 365 für jährlich, 730 für zweijährlich"),
    )
    tolerance = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Toleranz"),
        help_text=_("z.B. ±0,1°C oder ±0,5%"),
    )
    asset = models.ForeignKey(
        "assets.Asset",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="test_equipment",
        verbose_name=_("Zugehörige Anlage"),
    )
    responsible = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="responsible_equipment",
        verbose_name=_("Verantwortlicher"),
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
        verbose_name = _("Prüfmittel")
        verbose_name_plural = _("Prüfmittel")

    def __str__(self):
        return f"{self.name} ({self.serial_number})"

    @property
    def next_due(self):
        """Next calibration due date based on last complete record; None if never calibrated."""
        last = self.records.filter(
            calibrated_at__isnull=False
        ).order_by("-calibrated_at").first()
        if last is None:
            return None
        return last.next_due_override or (
            last.calibrated_at + timedelta(days=self.calibration_interval_days)
        )

    @property
    def open_record(self):
        """Returns the current open at-lab record if one exists, else None."""
        return self.records.filter(
            sent_at__isnull=False,
            calibrated_at__isnull=True,
        ).order_by("-sent_at").first()

    @property
    def status(self):
        # Equipment currently at an external lab takes priority.
        # For list sizes typical in GMP (< 500 items), Python-side iteration is acceptable.
        if self.open_record is not None:
            return CalibrationStatus.AT_LAB
        nd = self.next_due
        if nd is None:
            return CalibrationStatus.NEVER
        today = date.today()
        if nd < today:
            return CalibrationStatus.OVERDUE
        if nd <= today + timedelta(days=CALIBRATION_WARNING_DAYS):
            return CalibrationStatus.DUE_SOON
        return CalibrationStatus.VALID

    @property
    def status_label(self):
        return CalibrationStatus.LABEL[self.status]

    @property
    def status_badge_class(self):
        return CalibrationStatus.BADGE_CLASS[self.status]

    @property
    def days_until_due(self):
        nd = self.next_due
        if nd is None:
            return None
        return (nd - date.today()).days


class CalibrationRecord(AuditedModel):
    equipment = models.ForeignKey(
        TestEquipment,
        on_delete=models.CASCADE,
        related_name="records",
        verbose_name=_("Prüfmittel"),
    )
    # Calibration result fields (internal or after external return)
    calibrated_at = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Kalibriert am"),
    )
    result = models.CharField(
        max_length=20,
        choices=CalibrationResult.CHOICES,
        blank=True,
        verbose_name=_("Ergebnis"),
    )
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name=_("Durchgeführt von"),
    )
    certificate_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Zertifikatsnummer"),
    )
    next_due_override = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Nächste Fälligkeit (manuell)"),
        help_text=_("Überschreibt die automatische Berechnung aus dem Intervall"),
    )
    # External lab tracking
    external_lab = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Externes Labor"),
    )
    sent_at = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Eingesendet am"),
    )
    returned_at = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Zurückerhalten am"),
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_("Notizen"),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Erfasst am"),
    )

    class Meta:
        ordering = ["-calibrated_at", "-sent_at", "-created_at"]
        verbose_name = _("Kalibrierungsdurchführung")
        verbose_name_plural = _("Kalibrierungsdurchführungen")

    def __str__(self):
        return f"{self.equipment} — {self.calibrated_at or self.sent_at}"

    @property
    def result_badge_class(self):
        return CalibrationResult.BADGE_CLASS.get(self.result, "badge-neutral")

    @property
    def result_label(self):
        return CalibrationResult.LABEL.get(self.result, "—")

    @property
    def is_open(self):
        """True if equipment is currently at the lab (sent but not yet returned/calibrated)."""
        return bool(self.sent_at and not self.calibrated_at)
