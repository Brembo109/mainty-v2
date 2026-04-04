from django import forms
from django.utils.translation import gettext_lazy as _

from .constants import Action

_INPUT_CLASS = "form-input"


class AuditFilterForm(forms.Form):
    date_from = forms.DateField(
        required=False,
        label=_("Von"),
        widget=forms.DateInput(attrs={"type": "date", "class": _INPUT_CLASS}),
    )
    date_to = forms.DateField(
        required=False,
        label=_("Bis"),
        widget=forms.DateInput(attrs={"type": "date", "class": _INPUT_CLASS}),
    )
    actor = forms.CharField(
        required=False,
        label=_("Benutzer"),
        widget=forms.TextInput(attrs={
            "class": _INPUT_CLASS,
            "placeholder": _("Benutzername…"),
            "autocomplete": "off",
        }),
    )
    action = forms.ChoiceField(
        required=False,
        label=_("Aktion"),
        choices=[("", _("Alle Aktionen"))] + Action.CHOICES,
        widget=forms.Select(attrs={"class": _INPUT_CLASS}),
    )
