from django import forms
from django.utils.translation import gettext_lazy as _

from apps.core.models import SiteConfig

_INPUT_CLASS = "form-input"


class SiteConfigForm(forms.ModelForm):
    class Meta:
        model = SiteConfig
        fields = [
            "company_name",
            "site_url",
            "contract_expiry_warning_days",
            "reminder_email_subject",
            "email_from",
            "email_host",
            "email_port",
            "email_use_tls",
            "email_host_user",
            "email_host_password",
        ]
        widgets = {
            "company_name": forms.TextInput(attrs={"class": _INPUT_CLASS}),
            "site_url": forms.URLInput(attrs={"class": _INPUT_CLASS}),
            "contract_expiry_warning_days": forms.NumberInput(attrs={"class": _INPUT_CLASS}),
            "reminder_email_subject": forms.TextInput(attrs={"class": _INPUT_CLASS}),
            "email_from": forms.EmailInput(attrs={"class": _INPUT_CLASS}),
            "email_host": forms.TextInput(attrs={"class": _INPUT_CLASS}),
            "email_port": forms.NumberInput(attrs={"class": _INPUT_CLASS}),
            "email_host_user": forms.TextInput(attrs={"class": _INPUT_CLASS}),
            "email_host_password": forms.PasswordInput(
                render_value=True, attrs={"class": _INPUT_CLASS}
            ),
        }
