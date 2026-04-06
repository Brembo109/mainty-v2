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


class SiteConfig(models.Model):
    """Singleton configuration row. Use SiteConfig.get() — never instantiate directly."""

    # General
    company_name = models.CharField(max_length=100, default="mainty", verbose_name=_("Firmenname"))
    site_url = models.URLField(default="http://localhost:8000", verbose_name=_("Site-URL"))

    # Notifications
    contract_expiry_warning_days = models.PositiveIntegerField(
        default=90,
        verbose_name=_("Vertragswarnung (Tage)"),
    )
    reminder_email_subject = models.CharField(
        max_length=200,
        default="[mainty] GMP-Erinnerung — Handlungsbedarf",
        verbose_name=_("E-Mail-Betreff (Erinnerung)"),
    )

    # Email server
    email_from = models.EmailField(
        default="mainty@localhost",
        verbose_name=_("Absender-Adresse"),
    )
    email_host = models.CharField(max_length=200, default="localhost", verbose_name=_("SMTP-Host"))
    email_port = models.PositiveIntegerField(default=587, verbose_name=_("SMTP-Port"))
    email_use_tls = models.BooleanField(default=True, verbose_name=_("TLS verwenden"))
    email_host_user = models.CharField(
        max_length=200, blank=True, default="", verbose_name=_("SMTP-Benutzer")
    )
    email_host_password = models.CharField(
        max_length=200, blank=True, default="", verbose_name=_("SMTP-Passwort")
    )

    class Meta:
        verbose_name = _("Site-Konfiguration")

    @classmethod
    def get(cls):
        """Return the singleton, creating it with current settings.* as defaults on first call."""
        from django.conf import settings as django_settings

        instance, _ = cls.objects.get_or_create(
            pk=1,
            defaults={
                "site_url": getattr(django_settings, "SITE_URL", "http://localhost:8000"),
                "contract_expiry_warning_days": getattr(
                    django_settings, "CONTRACT_EXPIRY_WARNING_DAYS", 90
                ),
                "reminder_email_subject": getattr(
                    django_settings,
                    "REMINDER_EMAIL_SUBJECT",
                    "[mainty] GMP-Erinnerung — Handlungsbedarf",
                ),
                "email_from": getattr(django_settings, "DEFAULT_FROM_EMAIL", "mainty@localhost"),
                "email_host": getattr(django_settings, "EMAIL_HOST", "localhost"),
                "email_port": getattr(django_settings, "EMAIL_PORT", 587),
                "email_use_tls": getattr(django_settings, "EMAIL_USE_TLS", True),
                "email_host_user": getattr(django_settings, "EMAIL_HOST_USER", ""),
                "email_host_password": getattr(django_settings, "EMAIL_HOST_PASSWORD", ""),
            },
        )
        return instance
