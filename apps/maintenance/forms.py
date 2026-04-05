from django import forms
from django.utils.translation import gettext_lazy as _

from .models import MaintenancePlan, MaintenanceRecord

_INPUT_CLASS = "form-input"

_PLAN_FIELDS = ["asset", "title", "description", "responsible", "interval_days"]

_PLAN_WIDGETS = {
    "asset": forms.Select(attrs={"class": _INPUT_CLASS}),
    "title": forms.TextInput(attrs={
        "class": _INPUT_CLASS,
        "placeholder": _("z.B. Jährliche Kalibrierung"),
        "autofocus": True,
    }),
    "description": forms.Textarea(attrs={
        "class": _INPUT_CLASS,
        "rows": 3,
        "placeholder": _("Wartungsanweisungen, Prüfpunkte…"),
    }),
    "responsible": forms.TextInput(attrs={
        "class": _INPUT_CLASS,
        "placeholder": _("z.B. QA-Abteilung"),
    }),
    "interval_days": forms.NumberInput(attrs={
        "class": _INPUT_CLASS,
        "placeholder": _("z.B. 365"),
        "min": 1,
    }),
}


class MaintenancePlanCreateForm(forms.ModelForm):
    class Meta:
        model = MaintenancePlan
        fields = _PLAN_FIELDS
        widgets = _PLAN_WIDGETS


class MaintenancePlanUpdateForm(forms.ModelForm):
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
        model = MaintenancePlan
        fields = _PLAN_FIELDS + ["change_reason"]
        widgets = _PLAN_WIDGETS


class MaintenanceRecordForm(forms.ModelForm):
    class Meta:
        model = MaintenanceRecord
        fields = ["performed_at", "performed_by", "notes"]
        widgets = {
            "performed_at": forms.DateInput(attrs={
                "type": "date",
                "class": _INPUT_CLASS,
            }),
            "performed_by": forms.Select(attrs={"class": _INPUT_CLASS}),
            "notes": forms.Textarea(attrs={
                "class": _INPUT_CLASS,
                "rows": 3,
                "placeholder": _("Befunde, Besonderheiten…"),
            }),
        }
