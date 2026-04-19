from django import forms
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import User

from .constants import CalibrationResult, CalibrationStatus
from .models import CalibrationRecord, TestEquipment

_INPUT_CLASS = "form-input"
_FILTER_INPUT_CLASS = "filter-toolbar__inline-input"


class TestEquipmentForm(forms.ModelForm):
    class Meta:
        model = TestEquipment
        fields = [
            "name", "serial_number", "manufacturer", "location",
            "calibration_interval_days", "tolerance", "asset", "responsible",
        ]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": _INPUT_CLASS,
                "placeholder": _("z.B. Thermometer TH-01"),
                "autofocus": True,
            }),
            "serial_number": forms.TextInput(attrs={
                "class": _INPUT_CLASS,
                "placeholder": _("z.B. SN-2024-00123"),
            }),
            "manufacturer": forms.TextInput(attrs={
                "class": _INPUT_CLASS,
                "placeholder": _("z.B. Testo"),
            }),
            "location": forms.TextInput(attrs={
                "class": _INPUT_CLASS,
                "placeholder": _("z.B. Halle 3, Raum 12"),
            }),
            "calibration_interval_days": forms.NumberInput(attrs={
                "class": _INPUT_CLASS,
                "placeholder": _("z.B. 365"),
            }),
            "tolerance": forms.TextInput(attrs={
                "class": _INPUT_CLASS,
                "placeholder": _("z.B. ±0,1°C"),
            }),
            "asset": forms.Select(attrs={"class": _INPUT_CLASS}),
            "responsible": forms.Select(attrs={"class": _INPUT_CLASS}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["responsible"].queryset = User.objects.filter(
            is_active=True
        ).order_by("username")
        self.fields["responsible"].required = False
        self.fields["asset"].required = False


class TestEquipmentFilterForm(forms.Form):
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
        choices=[("", _("Alle Status"))] + CalibrationStatus.CHOICES,
        widget=forms.Select(attrs={"class": _FILTER_INPUT_CLASS}),
    )
    location = forms.ChoiceField(
        required=False,
        label=_("Standort"),
        choices=[("", _("Alle"))],
        widget=forms.Select(attrs={"class": _FILTER_INPUT_CLASS}),
    )
    responsible = forms.ModelChoiceField(
        required=False,
        label=_("Verantwortlich"),
        queryset=None,
        empty_label=_("Alle"),
        widget=forms.Select(attrs={"class": _FILTER_INPUT_CLASS}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["responsible"].queryset = User.objects.filter(
            is_active=True
        ).order_by("username")
        locations = (
            TestEquipment.objects
            .exclude(location="")
            .order_by("location")
            .values_list("location", flat=True)
            .distinct()
        )
        self.fields["location"].choices = (
            [("", _("Alle"))] + [(loc, loc) for loc in locations]
        )


class CalibrationRecordForm(forms.ModelForm):
    class Meta:
        model = CalibrationRecord
        fields = [
            "calibrated_at", "result", "performed_by", "certificate_number",
            "next_due_override",
            "external_lab", "sent_at", "returned_at",
            "notes",
        ]
        widgets = {
            "calibrated_at": forms.DateInput(
                attrs={"type": "date", "class": _INPUT_CLASS},
                format="%Y-%m-%d",
            ),
            "result": forms.Select(attrs={"class": _INPUT_CLASS}),
            "performed_by": forms.Select(attrs={"class": _INPUT_CLASS}),
            "certificate_number": forms.TextInput(attrs={
                "class": _INPUT_CLASS,
                "placeholder": _("z.B. CAL-2024-0042"),
            }),
            "next_due_override": forms.DateInput(
                attrs={"type": "date", "class": _INPUT_CLASS},
                format="%Y-%m-%d",
            ),
            "external_lab": forms.TextInput(attrs={
                "class": _INPUT_CLASS,
                "placeholder": _("z.B. DAkkS-Labor München GmbH"),
            }),
            "sent_at": forms.DateInput(
                attrs={"type": "date", "class": _INPUT_CLASS},
                format="%Y-%m-%d",
            ),
            "returned_at": forms.DateInput(
                attrs={"type": "date", "class": _INPUT_CLASS},
                format="%Y-%m-%d",
            ),
            "notes": forms.Textarea(attrs={
                "class": _INPUT_CLASS,
                "rows": 3,
                "placeholder": _("Optionale Notizen…"),
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["performed_by"].queryset = User.objects.filter(
            is_active=True
        ).order_by("username")
        self.fields["performed_by"].required = False
        # Add empty choice for result since it's optional until calibrated_at is set
        self.fields["result"].required = False
        self.fields["result"].choices = [("", "---------")] + list(
            CalibrationResult.CHOICES
        )

    def clean(self):
        cleaned_data = super().clean()
        calibrated_at = cleaned_data.get("calibrated_at")
        sent_at = cleaned_data.get("sent_at")
        result = cleaned_data.get("result")

        # At least one date must be provided
        if not calibrated_at and not sent_at:
            raise forms.ValidationError(
                _("Mindestens eines der Felder 'Kalibriert am' oder 'Eingesendet am' muss ausgefüllt sein.")
            )
        # Result is required when a calibration date is set
        if calibrated_at and not result:
            self.add_error("result", _("Ergebnis ist erforderlich wenn ein Kalibrierungsdatum angegeben wird."))

        return cleaned_data


class CalibrationRecordCompleteForm(forms.ModelForm):
    """Form for completing an open AT_LAB record with calibration result."""

    class Meta:
        model = CalibrationRecord
        fields = [
            "calibrated_at", "result", "performed_by", "certificate_number",
            "returned_at", "next_due_override", "notes",
        ]
        widgets = {
            "calibrated_at": forms.DateInput(
                attrs={"type": "date", "class": _INPUT_CLASS},
                format="%Y-%m-%d",
            ),
            "result": forms.Select(attrs={"class": _INPUT_CLASS}),
            "performed_by": forms.Select(attrs={"class": _INPUT_CLASS}),
            "certificate_number": forms.TextInput(attrs={
                "class": _INPUT_CLASS,
                "placeholder": _("z.B. CAL-2024-0042"),
            }),
            "returned_at": forms.DateInput(
                attrs={"type": "date", "class": _INPUT_CLASS},
                format="%Y-%m-%d",
            ),
            "next_due_override": forms.DateInput(
                attrs={"type": "date", "class": _INPUT_CLASS},
                format="%Y-%m-%d",
            ),
            "notes": forms.Textarea(attrs={
                "class": _INPUT_CLASS,
                "rows": 3,
                "placeholder": _("Optionale Notizen…"),
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["performed_by"].queryset = User.objects.filter(
            is_active=True
        ).order_by("username")
        self.fields["performed_by"].required = False
        self.fields["result"].choices = [("", "---------")] + list(
            CalibrationResult.CHOICES
        )

    def clean(self):
        cleaned_data = super().clean()
        calibrated_at = cleaned_data.get("calibrated_at")
        result = cleaned_data.get("result")

        if not calibrated_at:
            self.add_error("calibrated_at", _("Kalibrierungsdatum ist erforderlich."))
        if not result:
            self.add_error("result", _("Ergebnis ist erforderlich."))

        return cleaned_data
