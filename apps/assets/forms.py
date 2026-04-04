from django import forms
from django.utils.translation import gettext_lazy as _

from .constants import AssetStatus
from .models import Asset

_INPUT_CLASS = "form-input"


class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ["name", "location", "serial_number", "manufacturer", "status"]
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
        }


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
