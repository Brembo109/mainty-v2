from django import forms
from django.utils.translation import gettext_lazy as _

from apps.assets.models import Asset

from .constants import MaintenanceStatus
from .models import MaintenancePlan, MaintenanceRecord

_INPUT_CLASS = "form-input"
_FILTER_INPUT_CLASS = "filter-toolbar__inline-input"

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


class MaintenancePlanFilterForm(forms.Form):
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
            (MaintenanceStatus.OVERDUE, _("Überfällig")),
            (MaintenanceStatus.DUE_SOON, _("Fällig bald")),
            (MaintenanceStatus.OK, _("OK")),
        ],
        widget=forms.Select(attrs={"class": _FILTER_INPUT_CLASS}),
    )
    asset = forms.ModelChoiceField(
        required=False,
        label=_("Anlage"),
        queryset=None,
        empty_label=_("Alle Anlagen"),
        widget=forms.Select(attrs={"class": _FILTER_INPUT_CLASS}),
    )
    responsible = forms.ChoiceField(
        required=False,
        label=_("Verantwortlich"),
        choices=[("", _("Alle"))],
        widget=forms.Select(attrs={"class": _FILTER_INPUT_CLASS}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["asset"].queryset = Asset.objects.order_by("name")
        responsibles = (
            MaintenancePlan.objects
            .exclude(responsible="")
            .order_by("responsible")
            .values_list("responsible", flat=True)
            .distinct()
        )
        self.fields["responsible"].choices = (
            [("", _("Alle"))] + [(r, r) for r in responsibles]
        )


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
