# Asset Extended Fields — Design Spec

**Date:** 2026-04-06  
**Status:** Approved

## Summary

Extend the `Asset` model with 6 new fields covering device identification, department affiliation, service provider, and user responsibilities (Verantwortlicher + Stellvertreter). All changes land in a single migration. Form and filter UI are updated accordingly.

## Approach

All 6 fields added to `Asset` in one migration (`0002_asset_extended_fields`). User FK fields use `null=True` at the DB level (migration safety on existing data) but `blank=False` in the form (GMP-enforced required input). `on_delete=SET_NULL` ensures assets survive user deletion.

## Section 1: Model

### `apps/assets/constants.py` — new `Department` class

```python
class Department:
    HERSTELLUNG = "herstellung"
    QUALITAETSKONTROLLE = "qualitaetskontrolle"
    PROZESSENTWICKLUNG = "prozessentwicklung"

    CHOICES = [
        (HERSTELLUNG, _("Herstellung")),
        (QUALITAETSKONTROLLE, _("Qualitätskontrolle")),
        (PROZESSENTWICKLUNG, _("Prozessentwicklung")),
    ]

    BADGE_CLASS = {
        HERSTELLUNG: "badge-neutral",
        QUALITAETSKONTROLLE: "badge-neutral",
        PROZESSENTWICKLUNG: "badge-neutral",
    }
```

### `apps/assets/models.py` — 6 new fields on `Asset`

```python
from django.conf import settings

# Simple string fields
device_code = models.CharField(
    max_length=50,
    verbose_name=_("Gerätekürzel"),
)
inventory_number = models.CharField(
    max_length=100,
    verbose_name=_("Inventarnummer"),
)
service_provider = models.CharField(
    max_length=255,
    blank=True,
    verbose_name=_("Servicedienstleister"),
)
department = models.CharField(
    max_length=30,
    choices=Department.CHOICES,
    verbose_name=_("Zugehörigkeit"),
    db_index=True,
)

# Responsibility FKs
responsible = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    null=True,
    on_delete=models.SET_NULL,
    related_name="responsible_assets",
    verbose_name=_("Verantwortlicher"),
)
deputy = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    null=True,
    on_delete=models.SET_NULL,
    related_name="deputy_assets",
    verbose_name=_("Stellvertreter"),
)
```

Note: `blank=False` (default) on all fields except `service_provider`. `null=True` only on the FKs for migration safety.

### Migration

`apps/assets/migrations/0002_asset_extended_fields.py` — generated via `makemigrations`.

## Section 2: Form & Filter

### `apps/assets/forms.py` — `AssetForm`

Add all 6 fields to `Meta.fields`. Add widgets:

```python
"device_code": forms.TextInput(attrs={"class": _INPUT_CLASS, "placeholder": _("z.B. AKL-01")}),
"inventory_number": forms.TextInput(attrs={"class": _INPUT_CLASS, "placeholder": _("z.B. INV-2024-0042")}),
"service_provider": forms.TextInput(attrs={"class": _INPUT_CLASS, "placeholder": _("z.B. Siemens Service GmbH")}),
"department": forms.Select(attrs={"class": _INPUT_CLASS}),
"responsible": forms.Select(attrs={"class": _INPUT_CLASS}),
"deputy": forms.Select(attrs={"class": _INPUT_CLASS}),
```

Override `__init__` to set the queryset for the FK fields:

```python
def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    from apps.accounts.models import User
    active_users = User.objects.filter(is_active=True).order_by("username")
    self.fields["responsible"].queryset = active_users
    self.fields["deputy"].queryset = active_users
```

### `apps/assets/forms.py` — `AssetFilterForm`

Add 2 new filter fields:

```python
department = forms.ChoiceField(
    required=False,
    choices=[("", _("Alle Bereiche"))] + Department.CHOICES,
    widget=forms.Select(attrs={"class": _INPUT_CLASS}),
)
responsible = forms.ModelChoiceField(
    required=False,
    queryset=None,  # set in __init__
    empty_label=_("Alle Verantwortlichen"),
    widget=forms.Select(attrs={"class": _INPUT_CLASS}),
)

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    from apps.accounts.models import User
    self.fields["responsible"].queryset = User.objects.filter(is_active=True).order_by("username")
```

### `apps/assets/views.py` — `_apply_filters()`

Add to the filter function:

```python
if cd.get("department"):
    qs = qs.filter(department=cd["department"])
if cd.get("responsible"):
    qs = qs.filter(responsible=cd["responsible"])
```

### `apps/assets/views.py` — querysets

- `AssetListView.get_queryset()`: add `.select_related("responsible")` to the existing `Asset.objects.all()` call
- `AssetDetailView`: add `get_queryset()` override:
  ```python
  def get_queryset(self):
      return super().get_queryset().select_related("responsible", "deputy")
  ```

## Section 3: Templates

### `templates/assets/asset_form.html`

Add two new field groups after the existing fields:

**Group: Identifikation**
- Gerätekürzel (`device_code`)
- Inventarnummer (`inventory_number`)
- Zugehörigkeit (`department`)
- Servicedienstleister (`service_provider`) — labeled as optional

**Group: Verantwortlichkeiten**
- Verantwortlicher (`responsible`)
- Stellvertreter (`deputy`)

### `templates/assets/asset_list.html` and `partials/_asset_table.html`

- Name-Spalte: append device_code in muted text — `Autoklav A1 · AKL-01`
- New column: Zugehörigkeit (badge)
- New column: Verantwortlicher (username)
- Filter bar: add Zugehörigkeit and Verantwortlicher dropdowns

### `templates/assets/asset_detail.html`

New info section **Stammdaten** with all 6 new fields displayed as label/value pairs, consistent with existing detail sections.

## Out of Scope

- Editing department choices via UI (hardcoded in constants)
- History of responsibility changes (covered by existing AuditedModel)
- Filtering by deputy
