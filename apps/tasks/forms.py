from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Task

_INPUT_CLASS = "form-input"

_TASK_FIELDS = ["title", "description", "asset", "assigned_to", "due_date", "priority", "status"]

_TASK_WIDGETS = {
    "title": forms.TextInput(attrs={
        "class": _INPUT_CLASS,
        "placeholder": _("z.B. Kalibrierprotokoll nachreichen"),
        "autofocus": True,
    }),
    "description": forms.Textarea(attrs={
        "class": _INPUT_CLASS,
        "rows": 3,
        "placeholder": _("Detaillierte Beschreibung der Aufgabe…"),
    }),
    "asset": forms.Select(attrs={"class": _INPUT_CLASS}),
    "assigned_to": forms.Select(attrs={"class": _INPUT_CLASS}),
    "due_date": forms.DateInput(attrs={"type": "date", "class": _INPUT_CLASS}),
    "priority": forms.Select(attrs={"class": _INPUT_CLASS}),
    "status": forms.Select(attrs={"class": _INPUT_CLASS}),
}


class TaskCreateForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = _TASK_FIELDS
        widgets = _TASK_WIDGETS


class TaskUpdateForm(forms.ModelForm):
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
        model = Task
        fields = _TASK_FIELDS + ["change_reason"]
        widgets = _TASK_WIDGETS
