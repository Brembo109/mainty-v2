from django.core.mail.backends.smtp import EmailBackend as SmtpEmailBackend

from apps.core.models import SiteConfig


class SiteConfigEmailBackend(SmtpEmailBackend):
    """SMTP backend that reads connection settings from SiteConfig at runtime.

    This ensures that SMTP changes made via the admin settings page take
    effect for all outgoing emails (password reset, reminders, test mail)
    without requiring a server restart or .env change.
    """

    def __init__(self, **kwargs):
        cfg = SiteConfig.get()
        kwargs.setdefault("host", cfg.email_host)
        kwargs.setdefault("port", cfg.email_port)
        kwargs.setdefault("username", cfg.email_host_user)
        kwargs.setdefault("password", cfg.email_host_password)
        kwargs.setdefault("use_tls", cfg.email_use_tls)
        # use_ssl is intentionally omitted — SiteConfig does not expose it.
        # If SiteConfig gains an email_use_ssl field in future, add:
        #   kwargs.setdefault("use_ssl", cfg.email_use_ssl)
        # Any caller can still pass use_ssl=True explicitly via **kwargs.
        super().__init__(**kwargs)
