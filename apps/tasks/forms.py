from django import forms
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import User
from apps.assets.models import Asset
from .constants import TaskPriority, TaskStatus
from .models import Task

_INPUT_CLASS = "form-input"
_FILTER_INPUT_CLASS = "filter-toolbar__inline-input"

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
    assets = forms.ModelMultipleChoiceField(
        queryset=Asset.objects.order_by("name"),
        required=False,
        label=_("Anlagen"),
        widget=forms.CheckboxSelectMultiple(),
    )

    class Meta:
        model = Task
        fields = ["title", "description", "assigned_to", "due_date", "priority", "status"]
        widgets = {k: v for k, v in _TASK_WIDGETS.items() if k != "asset"}


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


class TaskFilterForm(forms.Form):
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
        choices=[("", _("Alle Status"))] + TaskStatus.CHOICES,
        widget=forms.Select(attrs={"class": _FILTER_INPUT_CLASS}),
    )
    priority = forms.ChoiceField(
        required=False,
        label=_("Priorität"),
        choices=[("", _("Alle Prioritäten"))] + TaskPriority.CHOICES,
        widget=forms.Select(attrs={"class": _FILTER_INPUT_CLASS}),
    )
    assigned_to = forms.ModelChoiceField(
        required=False,
        label=_("Zugewiesen"),
        queryset=None,
        empty_label=_("Alle Benutzer"),
        widget=forms.Select(attrs={"class": _FILTER_INPUT_CLASS}),
    )
    asset = forms.ModelChoiceField(
        required=False,
        label=_("Anlage"),
        queryset=None,
        empty_label=_("Alle Anlagen"),
        widget=forms.Select(attrs={"class": _FILTER_INPUT_CLASS}),
    )
    overdue = forms.ChoiceField(
        required=False,
        label=_("Überfällig"),
        choices=[
            ("", _("Alle")),
            ("yes", _("Ja")),
            ("no", _("Nein")),
        ],
        widget=forms.Select(attrs={"class": _FILTER_INPUT_CLASS}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assigned_to"].queryset = User.objects.filter(
            is_active=True
        ).order_by("username")
        self.fields["asset"].queryset = Asset.objects.order_by("name")
