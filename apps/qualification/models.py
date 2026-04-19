from datetime import date, datetime, timedelta

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.audit.mixins import AuditedModel

from .constants import QUALIFICATION_WARNING_DAYS, QualStatus, QualType


class QualificationCycle(AuditedModel):
    asset = models.ForeignKey(
        "assets.Asset",
        on_delete=models.CASCADE,
        related_name="qualification_cycles",
        verbose_name=_("Anlage"),
    )
    qual_type = models.CharField(
        max_length=2,
        choices=QualType.CHOICES,
        db_index=True,
        verbose_name=_("Qualifizierungstyp"),
    )
    title = models.CharField(
        max_length=255,
        verbose_name=_("Bezeichnung"),
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Beschreibung"),
    )
    responsible = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Verantwortlich"),
    )
    interval_days = models.PositiveIntegerField(
        verbose_name=_("Wiederholungsintervall (Tage)"),
        help_text=_("z.B. 730 für alle 2 Jahre"),
    )
    change_reason = models.TextField(
        blank=True,
        verbose_name=_("Änderungsgrund"),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["asset", "qual_type", "title"]
        verbose_name = _("Qualifizierungszyklus")
        verbose_name_plural = _("Qualifizierungszyklen")

    def __str__(self):
        return f"{self.asset} — {self.qual_type}: {self.title}"

    def _get_last_signed_at(self):
        """Return last signature date, using annotation when available."""
        # Annotation set by _cycle_qs() — avoids N+1 in list views.
        if hasattr(self, "last_signed_at") and self.last_signed_at is not None:
            val = self.last_signed_at
            return val.date() if isinstance(val, datetime) else val
        last = self.signatures.order_by("-signed_at").first()
        return last.signed_at if last else None

    @property
    def next_due(self):
        base = self._get_last_signed_at()
        if base is None:
            return self.created_at.date()
        return base + timedelta(days=self.interval_days)

    @property
    def status(self):
        if self._get_last_signed_at() is None:
            return QualStatus.NEVER_SIGNED
        today = date.today()
        nd = self.next_due
        if nd < today:
            return QualStatus.OVERDUE
        if nd <= today + timedelta(days=QUALIFICATION_WARNING_DAYS):
            return QualStatus.DUE_SOON
        return QualStatus.OK

    @property
    def status_label(self):
        return QualStatus.LABEL.get(self.status, self.status)

    @property
    def status_badge_class(self):
        return QualStatus.BADGE_CLASS.get(self.status, "status-dot status-dot-idle")

    @property
    def days_until_due(self):
        return (self.next_due - date.today()).days


class QualificationSignature(AuditedModel):
    """Immutable CFR 21 Part 11 electronic signature record."""

    cycle = models.ForeignKey(
        QualificationCycle,
        on_delete=models.PROTECT,  # CFR 21 Part 11: signatures cannot be silently deleted via CASCADE
        related_name="signatures",
        verbose_name=_("Qualifizierungszyklus"),
    )
    signed_at = models.DateField(verbose_name=_("Signierdatum"))
    signed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name=_("Signiert von"),
    )
    # Username snapshot — readable after user deletion (CFR 21 Part 11).
    signed_by_username = models.CharField(
        max_length=150,
        verbose_name=_("Benutzername"),
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_("IP-Adresse"),
    )
    meaning = models.CharField(
        max_length=255,
        default="Geprüft und freigegeben",
        verbose_name=_("Bedeutung der Signatur"),
    )
    notes = models.TextField(blank=True, verbose_name=_("Notizen"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-signed_at", "-created_at"]
        verbose_name = _("Elektronische Signatur")
        verbose_name_plural = _("Elektronische Signaturen")

    def __str__(self):
        return f"{self.cycle} | {self.signed_by_username} | {self.signed_at}"

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValueError(
                "QualificationSignature records are immutable and cannot be updated."
            )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError(
            "QualificationSignature records are immutable and cannot be deleted."
        )
