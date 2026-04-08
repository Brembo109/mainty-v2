from datetime import date, timedelta

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.audit.mixins import AuditedModel

from .constants import ContractStatus

_EXPIRY_WARNING_DAYS = getattr(settings, "CONTRACT_EXPIRY_WARNING_DAYS", 90)

class Contract(AuditedModel):
    title = models.CharField(
        max_length=255,
        verbose_name=_("Bezeichnung"),
    )
    contract_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Vertragsnummer"),
    )
    vendor = models.CharField(
        max_length=255,
        verbose_name=_("Vertragspartner"),
    )
    start_date = models.DateField(
        verbose_name=_("Vertragsbeginn"),
    )
    end_date = models.DateField(
        db_index=True,
        verbose_name=_("Vertragsende"),
    )
    contact_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Ansprechpartner"),
    )
    contact_details = models.TextField(
        blank=True,
        verbose_name=_("Kontaktdaten"),
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_("Notizen"),
    )
    assets = models.ManyToManyField(
        "assets.Asset",
        blank=True,
        related_name="contracts",
        verbose_name=_("Anlagen"),
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
        ordering = ["end_date"]
        verbose_name = _("Servicevertrag")
        verbose_name_plural = _("Serviceverträge")

    def __str__(self):
        return f"{self.title} ({self.vendor})"

    @property
    def status(self):
        today = date.today()
        if self.end_date < today:
            return ContractStatus.EXPIRED
        if self.end_date <= today + timedelta(days=_EXPIRY_WARNING_DAYS):
            return ContractStatus.EXPIRING
        return ContractStatus.ACTIVE

    @property
    def status_label(self):
        return ContractStatus.LABEL[self.status]

    @property
    def status_badge_class(self):
        return ContractStatus.BADGE_CLASS[self.status]

    @property
    def days_remaining(self):
        """Days until contract expires; negative if already expired."""
        return (self.end_date - date.today()).days

    @property
    def days_overdue(self):
        """Days since contract expired (always positive); 0 if not expired."""
        return max(0, (date.today() - self.end_date).days)


class ContractRenewal(AuditedModel):
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name="renewals",
        verbose_name=_("Vertrag"),
    )
    previous_end_date = models.DateField(
        verbose_name=_("Altes Vertragsende"),
    )
    new_end_date = models.DateField(
        verbose_name=_("Neues Vertragsende"),
    )
    renewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="contract_renewals",
        verbose_name=_("Verlängert von"),
    )
    renewed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Verlängert am"),
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_("Notiz"),
    )

    class Meta:
        ordering = ["-renewed_at"]
        verbose_name = _("Vertragsverlängerung")
        verbose_name_plural = _("Vertragsverlängerungen")

    def __str__(self):
        return f"{self.contract} → {self.new_end_date}"
