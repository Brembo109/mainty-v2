from django import forms
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import User
from .constants import AssetStatus, Department
from .models import Asset

_INPUT_CLASS = "form-input"
_CHECKBOX_CLASS = "h-4 w-4 rounded border-border cursor-pointer"


class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = [
            "name", "serial_number", "location", "manufacturer", "status",
            "lock_reason",
            "device_code", "inventory_number", "service_provider", "department",
            "owner",
            "responsible", "deputy",
            "log_number", "manual_number",
            "has_computer",
            "computer_name", "computer_ip", "computer_network_port",
            "computer_windows_version", "computer_software_version",
            "computer_backups_enabled", "computer_backups_description",
        ]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": _INPUT_CLASS,
                "placeholder": _("z.B. Autoklav A1"),
                "autofocus": True,
            }),
            "location": forms.TextInput(attrs={
                "class": _INPUT_CLASS,
                "placeholder": _("z.B. Halle 3, Raum 12"),
            }),
            "serial_number": forms.TextInput(attrs={
                "class": _INPUT_CLASS,
                "placeholder": _("z.B. SN-2024-00123"),
            }),
            "manufacturer": forms.TextInput(attrs={
                "class": _INPUT_CLASS,
                "placeholder": _("z.B. Siemens"),
            }),
            "status": forms.Select(attrs={"class": _INPUT_CLASS}),
            "lock_reason": forms.TextInput(attrs={
                "class": _INPUT_CLASS,
                "placeholder": _("z.B. Kalibrierung überfällig"),
            }),
            "device_code": forms.TextInput(attrs={
                "class": _INPUT_CLASS,
                "placeholder": _("z.B. AKL-01"),
            }),
            "inventory_number": forms.TextInput(attrs={
                "class": _INPUT_CLASS,
                "placeholder": _("z.B. INV-2024-0042"),
            }),
            "service_provider": forms.TextInput(attrs={
                "class": _INPUT_CLASS,
                "placeholder": _("z.B. Siemens Service GmbH"),
            }),
            "department": forms.Select(attrs={"class": _INPUT_CLASS}),
            "owner": forms.TextInput(attrs={
                "class": _INPUT_CLASS,
                "placeholder": _("z.B. Abteilung QK"),
            }),
            "responsible": forms.Select(attrs={"class": _INPUT_CLASS}),
            "deputy": forms.Select(attrs={"class": _INPUT_CLASS}),
            "log_number": forms.TextInput(attrs={
                "class": _INPUT_CLASS,
                "placeholder": _("z.B. LOG-2024-001"),
            }),
            "manual_number": forms.TextInput(attrs={
                "class": _INPUT_CLASS,
                "placeholder": _("z.B. BAL-2024-001"),
            }),
            "has_computer": forms.CheckboxInput(attrs={"class": _CHECKBOX_CLASS}),
            "computer_name": forms.TextInput(attrs={
                "class": _INPUT_CLASS,
                "placeholder": _("z.B. PC-LAB-01"),
            }),
            "computer_ip": forms.TextInput(attrs={
                "class": _INPUT_CLASS,
                "placeholder": _("z.B. 192.168.1.100"),
            }),
            "computer_network_port": forms.TextInput(attrs={
                "class": _INPUT_CLASS,
                "placeholder": _("z.B. Switch A / Port 12"),
            }),
            "computer_windows_version": forms.TextInput(attrs={
                "class": _INPUT_CLASS,
                "placeholder": _("z.B. Windows 10 22H2"),
            }),
            "computer_software_version": forms.TextInput(attrs={
                "class": _INPUT_CLASS,
                "placeholder": _("z.B. 3.4.1"),
            }),
            "computer_backups_enabled": forms.CheckboxInput(attrs={"class": _CHECKBOX_CLASS}),
            "computer_backups_description": forms.TextInput(attrs={
                "class": _INPUT_CLASS,
                "placeholder": _("z.B. Täglich nach NAS, 30 Tage Aufbewahrung"),
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        active_users = User.objects.filter(is_active=True).order_by("username")
        # GMP requirement: responsible and deputy must be explicitly set.
        # ModelChoiceField is required=True by default — do not override without change-control sign-off.
        self.fields["responsible"].queryset = active_users
        self.fields["deputy"].queryset = active_users

    def clean(self):
        cleaned_data = super().clean()
        # Clear lock_reason when device is not locked — audit trail preserves the old value.
        if cleaned_data.get("status") != AssetStatus.LOCKED:
            cleaned_data["lock_reason"] = ""
        # Clear all computer fields when has_computer is unchecked.
        if not cleaned_data.get("has_computer"):
            for field in (
                "computer_name", "computer_ip", "computer_network_port",
                "computer_windows_version", "computer_software_version",
                "computer_backups_description",
            ):
                cleaned_data[field] = ""
            cleaned_data["computer_backups_enabled"] = False
        # Clear backup description when backups are disabled.
        elif not cleaned_data.get("computer_backups_enabled"):
            cleaned_data["computer_backups_description"] = ""
        return cleaned_data


class AssetFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        label=_("Suche"),
        widget=forms.TextInput(attrs={
            "class": _INPUT_CLASS,
            "placeholder": _("Name oder Seriennummer…"),
            "autocomplete": "off",
        }),
    )
    status = forms.ChoiceField(
        required=False,
        label=_("Status"),
        choices=[("", _("Alle Status"))] + AssetStatus.CHOICES,
        widget=forms.Select(attrs={"class": _INPUT_CLASS}),
    )
    location = forms.CharField(
        required=False,
        label=_("Standort"),
        widget=forms.TextInput(attrs={
            "class": _INPUT_CLASS,
            "placeholder": _("Standort…"),
            "autocomplete": "off",
        }),
    )
    department = forms.ChoiceField(
        required=False,
        label=_("Zugehörigkeit"),
        choices=[("", _("Alle Bereiche"))] + Department.CHOICES,
        widget=forms.Select(attrs={"class": _INPUT_CLASS}),
    )
    responsible = forms.ModelChoiceField(
        required=False,
        label=_("Verantwortlicher"),
        queryset=None,
        empty_label=_("Alle Verantwortlichen"),
        widget=forms.Select(attrs={"class": _INPUT_CLASS}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["responsible"].queryset = User.objects.filter(
            is_active=True
        ).order_by("username")
