from django import forms
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import User
from .constants import AssetStatus, Department
from .models import Asset

_INPUT_CLASS = "form-input"


class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = [
            "name", "serial_number", "location", "manufacturer", "status",
            "device_code", "inventory_number", "service_provider", "department",
            "responsible", "deputy",
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
            "responsible": forms.Select(attrs={"class": _INPUT_CLASS}),
            "deputy": forms.Select(attrs={"class": _INPUT_CLASS}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        active_users = User.objects.filter(is_active=True).order_by("username")
        # GMP requirement: responsible and deputy must be explicitly set.
        # ModelChoiceField is required=True by default — do not override without change-control sign-off.
        self.fields["responsible"].queryset = active_users
        self.fields["deputy"].queryset = active_users


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
