from django import forms
from django.utils.translation import gettext_lazy as _

from apps.assets.models import Asset

from .constants import ContractStatus
from .models import Contract, ContractRenewal

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
            "contact_name",
            "contact_details",
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
            "start_date": forms.DateInput(
                attrs={"type": "date", "class": _INPUT_CLASS},
                format="%Y-%m-%d",
            ),
            "end_date": forms.DateInput(
                attrs={"type": "date", "class": _INPUT_CLASS},
                format="%Y-%m-%d",
            ),
            "contact_name": forms.TextInput(attrs={
                "class": _INPUT_CLASS,
                "placeholder": _("z.B. Max Mustermann"),
            }),
            "contact_details": forms.Textarea(attrs={
                "class": _INPUT_CLASS,
                "rows": 3,
                "placeholder": _("z.B. Tel: +49 89 123456\nE-Mail: max@example.com"),
            }),
            "notes": forms.Textarea(attrs={
                "class": _INPUT_CLASS,
                "rows": 4,
                "placeholder": _("Optionale Notizen…"),
            }),
        }


class ContractRenewalForm(forms.ModelForm):
    class Meta:
        model = ContractRenewal
        fields = ["new_end_date", "notes"]
        widgets = {
            "new_end_date": forms.DateInput(
                attrs={"type": "date", "class": _INPUT_CLASS, "autofocus": True},
                format="%Y-%m-%d",
            ),
            "notes": forms.Textarea(attrs={
                "class": _INPUT_CLASS,
                "rows": 3,
                "placeholder": _("Optionale Notiz zur Verlängerung…"),
            }),
        }

    def clean_new_end_date(self):
        new_date = self.cleaned_data["new_end_date"]
        previous = self.initial.get("previous_end_date")
        if previous and new_date <= previous:
            raise forms.ValidationError(
                _("Das neue Vertragsende muss nach dem bisherigen Enddatum liegen.")
            )
        return new_date


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
