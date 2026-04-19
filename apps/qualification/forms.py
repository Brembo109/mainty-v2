from django import forms
from django.utils.translation import gettext_lazy as _

from apps.assets.models import Asset

from .constants import QualStatus, QualType
from .models import QualificationCycle

_INPUT_CLASS = "form-input"
_FILTER_INPUT_CLASS = "filter-toolbar__inline-input"

_CYCLE_FIELDS = ["asset", "qual_type", "title", "description", "responsible", "interval_days"]

_CYCLE_WIDGETS = {
    "asset": forms.Select(attrs={"class": _INPUT_CLASS}),
    "qual_type": forms.Select(attrs={"class": _INPUT_CLASS}),
    "title": forms.TextInput(attrs={
        "class": _INPUT_CLASS,
        "placeholder": _("z.B. Erstqualifizierung HPLC-Anlage"),
        "autofocus": True,
    }),
    "description": forms.Textarea(attrs={
        "class": _INPUT_CLASS,
        "rows": 3,
        "placeholder": _("Prüfumfang, Anforderungen, Referenzdokumente…"),
    }),
    "responsible": forms.TextInput(attrs={
        "class": _INPUT_CLASS,
        "placeholder": _("z.B. QA-Abteilung"),
    }),
    "interval_days": forms.NumberInput(attrs={
        "class": _INPUT_CLASS,
        "placeholder": _("z.B. 730"),
        "min": 1,
    }),
}


class QualificationCycleCreateForm(forms.ModelForm):
    class Meta:
        model = QualificationCycle
        fields = _CYCLE_FIELDS
        widgets = _CYCLE_WIDGETS


class QualificationCycleUpdateForm(forms.ModelForm):
    change_reason = forms.CharField(
        required=True,
        label=_("Änderungsgrund"),
        widget=forms.Textarea(attrs={
            "class": _INPUT_CLASS,
            "rows": 2,
            "placeholder": _("Pflichtfeld — Begründung der Änderung…"),
        }),
    )

    class Meta:
        model = QualificationCycle
        fields = _CYCLE_FIELDS + ["change_reason"]
        widgets = _CYCLE_WIDGETS


class QualificationCycleFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        label=_("Suche"),
        widget=forms.TextInput(attrs={
            "class": _FILTER_INPUT_CLASS,
            "autocomplete": "off",
        }),
    )
    status = forms.ChoiceField(
        required=False,
        label=_("Status"),
        choices=[
            ("", _("Alle Status")),
            (QualStatus.OVERDUE, _("Überfällig")),
            (QualStatus.DUE_SOON, _("Fällig bald")),
            (QualStatus.OK, _("OK")),
            (QualStatus.NEVER_SIGNED, _("Nie signiert")),
        ],
        widget=forms.Select(attrs={"class": _FILTER_INPUT_CLASS}),
    )
    qual_type = forms.ChoiceField(
        required=False,
        label=_("Typ"),
        choices=[("", _("Alle Typen")), ("IQ", "IQ"), ("OQ", "OQ"), ("PQ", "PQ")],
        widget=forms.Select(attrs={"class": _FILTER_INPUT_CLASS}),
    )
    asset = forms.ModelChoiceField(
        required=False,
        label=_("Anlage"),
        queryset=None,
        empty_label=_("Alle Anlagen"),
        widget=forms.Select(attrs={"class": _FILTER_INPUT_CLASS}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["asset"].queryset = Asset.objects.order_by("name")


class SignatureForm(forms.Form):
    """Re-authentication + signature metadata form for CFR 21 Part 11."""

    password = forms.CharField(
        label=_("Passwort bestätigen"),
        widget=forms.PasswordInput(attrs={
            "class": _INPUT_CLASS,
            "placeholder": _("Ihr aktuelles Passwort…"),
            "autofocus": True,
        }),
    )
    meaning = forms.CharField(
        label=_("Bedeutung der Signatur"),
        initial="Geprüft und freigegeben",
        widget=forms.TextInput(attrs={"class": _INPUT_CLASS}),
    )
    notes = forms.CharField(
        label=_("Notizen (optional)"),
        required=False,
        widget=forms.Textarea(attrs={
            "class": _INPUT_CLASS,
            "rows": 2,
            "placeholder": _("Befunde, Abweichungen, Kommentare…"),
        }),
    )
