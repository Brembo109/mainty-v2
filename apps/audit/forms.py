from django import forms
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _

from .constants import Action
from .models import AuditLog

_INPUT_CLASS = "form-input"
_FILTER_INPUT_CLASS = "filter-toolbar__inline-input"


class AuditFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        label=_("Suche"),
        widget=forms.TextInput(attrs={
            "class": _FILTER_INPUT_CLASS,
            "autocomplete": "off",
        }),
    )
    action = forms.ChoiceField(
        required=False,
        label=_("Aktion"),
        choices=[("", _("Alle Aktionen"))] + Action.CHOICES,
        widget=forms.Select(attrs={"class": _FILTER_INPUT_CLASS}),
    )
    model = forms.ChoiceField(
        required=False,
        label=_("Objekttyp"),
        choices=[("", _("Alle"))],
        widget=forms.Select(attrs={"class": _FILTER_INPUT_CLASS}),
    )
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        model_ids = (
            AuditLog.objects
            .exclude(content_type__isnull=True)
            .values_list("content_type_id", flat=True)
            .distinct()
        )
        types = ContentType.objects.filter(id__in=list(model_ids)).order_by("model")
        self.fields["model"].choices = (
            [("", _("Alle"))]
            + [(str(t.id), f"{t.app_label}.{t.model}") for t in types]
        )
