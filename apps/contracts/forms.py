from django import forms
from django.utils.translation import gettext_lazy as _

from apps.assets.models import Asset

from .constants import ContractStatus
from .models import Contract

_INPUT_CLASS = "form-input"


class ContractForm(forms.ModelForm):
    assets = forms.ModelMultipleChoiceField(
        queryset=Asset.objects.all(),
        required=False,
        label=_("Anlagen"),
        widget=forms.CheckboxSelectMultiple(),
    )

    class Meta:
        model = Contract
        fields = [
            "title",
            "contract_number",
            "vendor",
            "start_date",
            "end_date",
            "assets",
            "notes",
        ]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": _INPUT_CLASS,
                "placeholder": _("z.B. Wartungsvertrag Autoklav 2024"),
                "autofocus": True,
            }),
            "contract_number": forms.TextInput(attrs={
                "class": _INPUT_CLASS,
                "placeholder": _("z.B. VTR-2024-001"),
            }),
            "vendor": forms.TextInput(attrs={
                "class": _INPUT_CLASS,
                "placeholder": _("z.B. TÜV Süd"),
            }),
            "start_date": forms.DateInput(attrs={
                "type": "date",
                "class": _INPUT_CLASS,
            }),
            "end_date": forms.DateInput(attrs={
                "type": "date",
                "class": _INPUT_CLASS,
            }),
            "notes": forms.Textarea(attrs={
                "class": _INPUT_CLASS,
                "rows": 4,
                "placeholder": _("Optionale Notizen…"),
            }),
        }


class ContractFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        label=_("Suche"),
        widget=forms.TextInput(attrs={
            "class": _INPUT_CLASS,
            "placeholder": _("Bezeichnung, Anbieter oder Nr.…"),
            "autocomplete": "off",
        }),
    )
    status = forms.ChoiceField(
        required=False,
        label=_("Status"),
        choices=[("", _("Alle Status"))] + ContractStatus.CHOICES,
        widget=forms.Select(attrs={"class": _INPUT_CLASS}),
    )
