# Asset Extended Fields Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the Asset model with 6 new fields: Gerätekürzel, Inventarnummer, Servicedienstleister, Zugehörigkeit (department dropdown), Verantwortlicher (User FK), and Stellvertreter (User FK).

**Architecture:** All 6 fields land in one migration (`0002_asset_extended_fields`). User FKs are `null=True` at DB level (migration-safe) but `blank=False` in forms (GMP-enforced). `on_delete=SET_NULL` preserves assets when a user is deleted. Department choices are defined as a `Department` class in `apps/assets/constants.py`, following the existing `AssetStatus` pattern.

**Tech Stack:** Django 5, PostgreSQL, HTMX, Tailwind CSS, Django TestCase

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `apps/assets/constants.py` | Modify | Add `Department` class with choices |
| `apps/assets/models.py` | Modify | Add 6 new fields to `Asset` |
| `apps/assets/migrations/0002_asset_extended_fields.py` | Create | Generated migration |
| `apps/assets/forms.py` | Modify | Add new fields to `AssetForm` and `AssetFilterForm` |
| `apps/assets/views.py` | Modify | Add `select_related`, extend `_apply_filters` |
| `apps/assets/tests.py` | Create | Tests for model fields, form validation, filter logic |
| `templates/assets/asset_form.html` | Modify | Add new fields in two groups |
| `templates/assets/partials/_asset_table.html` | Modify | Add Zugehörigkeit and Verantwortlicher columns |
| `templates/assets/asset_list.html` | Modify | Add department and responsible filter inputs |
| `templates/assets/asset_detail.html` | Modify | Add Stammdaten section with all 6 new fields |

---

## Task 1: Model, Constants, Migration

**Files:**
- Modify: `apps/assets/constants.py`
- Modify: `apps/assets/models.py`
- Create: `apps/assets/migrations/0002_asset_extended_fields.py`
- Create: `apps/assets/tests.py`

- [ ] **Step 1: Write failing tests**

Create `apps/assets/tests.py`:

```python
from django.test import TestCase

from apps.accounts.models import User
from apps.assets.constants import Department
from apps.assets.models import Asset


def make_user(username):
    return User.objects.create_user(username=username, password="pass")


def make_asset(**kwargs):
    defaults = {
        "name": "Autoklav A1",
        "serial_number": "SN-001",
        "location": "Halle 3",
        "device_code": "AKL-01",
        "inventory_number": "INV-2024-001",
        "department": Department.HERSTELLUNG,
    }
    defaults.update(kwargs)
    return Asset.objects.create(**defaults)


class AssetDepartmentFieldTest(TestCase):
    def test_department_choices_exist(self):
        self.assertEqual(len(Department.CHOICES), 3)
        values = [c[0] for c in Department.CHOICES]
        self.assertIn("herstellung", values)
        self.assertIn("qualitaetskontrolle", values)
        self.assertIn("prozessentwicklung", values)

    def test_asset_stores_department(self):
        asset = make_asset(department=Department.QUALITAETSKONTROLLE)
        asset.refresh_from_db()
        self.assertEqual(asset.department, Department.QUALITAETSKONTROLLE)


class AssetIdentificationFieldsTest(TestCase):
    def test_device_code_and_inventory_number_stored(self):
        asset = make_asset(device_code="AKL-99", inventory_number="INV-9999")
        asset.refresh_from_db()
        self.assertEqual(asset.device_code, "AKL-99")
        self.assertEqual(asset.inventory_number, "INV-9999")

    def test_service_provider_optional(self):
        asset = make_asset(service_provider="")
        asset.refresh_from_db()
        self.assertEqual(asset.service_provider, "")

    def test_service_provider_stored(self):
        asset = make_asset(service_provider="Siemens GmbH")
        asset.refresh_from_db()
        self.assertEqual(asset.service_provider, "Siemens GmbH")


class AssetResponsibilityFieldsTest(TestCase):
    def test_responsible_and_deputy_stored(self):
        responsible = make_user("responsible_user")
        deputy = make_user("deputy_user")
        asset = make_asset(responsible=responsible, deputy=deputy)
        asset.refresh_from_db()
        self.assertEqual(asset.responsible, responsible)
        self.assertEqual(asset.deputy, deputy)

    def test_responsible_set_null_on_user_delete(self):
        responsible = make_user("to_delete")
        asset = make_asset(responsible=responsible)
        responsible.delete()
        asset.refresh_from_db()
        self.assertIsNone(asset.responsible)

    def test_deputy_set_null_on_user_delete(self):
        deputy = make_user("deputy_to_delete")
        asset = make_asset(deputy=deputy)
        deputy.delete()
        asset.refresh_from_db()
        self.assertIsNone(asset.deputy)

    def test_responsible_and_deputy_can_be_null(self):
        asset = make_asset(responsible=None, deputy=None)
        asset.refresh_from_db()
        self.assertIsNone(asset.responsible)
        self.assertIsNone(asset.deputy)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
docker compose exec web python manage.py test apps.assets.tests -v 2
```

Expected: FAIL — `django.db.utils.OperationalError` or `AttributeError` (fields don't exist yet)

- [ ] **Step 3: Add `Department` class to `apps/assets/constants.py`**

Append after the `AssetStatus` class:

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
```

- [ ] **Step 4: Add 6 new fields to `apps/assets/models.py`**

Add `from django.conf import settings` to the imports.
Import `Department` from `.constants`.
Add the following fields to the `Asset` class after the existing `manufacturer` field:

```python
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
    db_index=True,
    verbose_name=_("Zugehörigkeit"),
)
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

- [ ] **Step 5: Generate and apply migration**

```bash
docker compose exec web python manage.py makemigrations assets --name asset_extended_fields
docker compose exec web python manage.py migrate
```

Expected: `Applying assets.0002_asset_extended_fields... OK`

- [ ] **Step 6: Run tests to verify they pass**

```bash
docker compose exec web python manage.py test apps.assets.tests -v 2
```

Expected: OK (9 tests pass)

- [ ] **Step 7: Commit**

```bash
git add apps/assets/constants.py apps/assets/models.py apps/assets/migrations/0002_asset_extended_fields.py apps/assets/tests.py
git commit -m "feat: add extended fields to Asset model (department, device_code, responsibilities)"
```

---

## Task 2: Forms

**Files:**
- Modify: `apps/assets/forms.py`
- Modify: `apps/assets/tests.py`

- [ ] **Step 1: Write failing tests**

Append to `apps/assets/tests.py`:

```python
from django.test import TestCase

from apps.assets.constants import Department
from apps.assets.forms import AssetFilterForm, AssetForm
from apps.assets.models import Asset


class AssetFormValidationTest(TestCase):
    def setUp(self):
        from apps.accounts.models import User
        self.responsible = User.objects.create_user(username="resp", password="pass")
        self.deputy = User.objects.create_user(username="dep", password="pass")

    def _valid_data(self, **overrides):
        data = {
            "name": "Autoklav A1",
            "serial_number": "SN-001",
            "location": "Halle 3",
            "manufacturer": "",
            "status": "free",
            "device_code": "AKL-01",
            "inventory_number": "INV-001",
            "service_provider": "",
            "department": Department.HERSTELLUNG,
            "responsible": self.responsible.pk,
            "deputy": self.deputy.pk,
        }
        data.update(overrides)
        return data

    def test_valid_form(self):
        form = AssetForm(data=self._valid_data())
        self.assertTrue(form.is_valid(), form.errors)

    def test_device_code_required(self):
        form = AssetForm(data=self._valid_data(device_code=""))
        self.assertFalse(form.is_valid())
        self.assertIn("device_code", form.errors)

    def test_inventory_number_required(self):
        form = AssetForm(data=self._valid_data(inventory_number=""))
        self.assertFalse(form.is_valid())
        self.assertIn("inventory_number", form.errors)

    def test_department_required(self):
        form = AssetForm(data=self._valid_data(department=""))
        self.assertFalse(form.is_valid())
        self.assertIn("department", form.errors)

    def test_responsible_required(self):
        form = AssetForm(data=self._valid_data(responsible=""))
        self.assertFalse(form.is_valid())
        self.assertIn("responsible", form.errors)

    def test_deputy_required(self):
        form = AssetForm(data=self._valid_data(deputy=""))
        self.assertFalse(form.is_valid())
        self.assertIn("deputy", form.errors)

    def test_service_provider_optional(self):
        form = AssetForm(data=self._valid_data(service_provider=""))
        self.assertTrue(form.is_valid(), form.errors)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
docker compose exec web python manage.py test apps.assets.tests.AssetFormValidationTest -v 2
```

Expected: FAIL — `KeyError` or `AssertionError` (new fields not in form yet)

- [ ] **Step 3: Update `apps/assets/forms.py`**

Replace the entire file with:

```python
from django import forms
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import User
from .constants import AssetStatus, Department
from .models import Asset

_INPUT_CLASS = "form-input"


class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = [
            "name", "serial_number", "location", "manufacturer", "status",
            "device_code", "inventory_number", "service_provider", "department",
            "responsible", "deputy",
        ]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": _INPUT_CLASS,
                "placeholder": _("z.B. Autoklav A1"),
                "autofocus": True,
            }),
            "location": forms.TextInput(attrs={
                "class": _INPUT_CLASS,
                "placeholder": _("z.B. Halle 3, Raum 12"),
            }),
            "serial_number": forms.TextInput(attrs={
                "class": _INPUT_CLASS,
                "placeholder": _("z.B. SN-2024-00123"),
            }),
            "manufacturer": forms.TextInput(attrs={
                "class": _INPUT_CLASS,
                "placeholder": _("z.B. Siemens"),
            }),
            "status": forms.Select(attrs={"class": _INPUT_CLASS}),
            "device_code": forms.TextInput(attrs={
                "class": _INPUT_CLASS,
                "placeholder": _("z.B. AKL-01"),
            }),
            "inventory_number": forms.TextInput(attrs={
                "class": _INPUT_CLASS,
                "placeholder": _("z.B. INV-2024-0042"),
            }),
            "service_provider": forms.TextInput(attrs={
                "class": _INPUT_CLASS,
                "placeholder": _("z.B. Siemens Service GmbH"),
            }),
            "department": forms.Select(attrs={"class": _INPUT_CLASS}),
            "responsible": forms.Select(attrs={"class": _INPUT_CLASS}),
            "deputy": forms.Select(attrs={"class": _INPUT_CLASS}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        active_users = User.objects.filter(is_active=True).order_by("username")
        self.fields["responsible"].queryset = active_users
        self.fields["deputy"].queryset = active_users


class AssetFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        label=_("Suche"),
        widget=forms.TextInput(attrs={
            "class": _INPUT_CLASS,
            "placeholder": _("Name oder Seriennummer…"),
            "autocomplete": "off",
        }),
    )
    status = forms.ChoiceField(
        required=False,
        label=_("Status"),
        choices=[("", _("Alle Status"))] + AssetStatus.CHOICES,
        widget=forms.Select(attrs={"class": _INPUT_CLASS}),
    )
    location = forms.CharField(
        required=False,
        label=_("Standort"),
        widget=forms.TextInput(attrs={
            "class": _INPUT_CLASS,
            "placeholder": _("Standort…"),
            "autocomplete": "off",
        }),
    )
    department = forms.ChoiceField(
        required=False,
        label=_("Zugehörigkeit"),
        choices=[("", _("Alle Bereiche"))] + Department.CHOICES,
        widget=forms.Select(attrs={"class": _INPUT_CLASS}),
    )
    responsible = forms.ModelChoiceField(
        required=False,
        label=_("Verantwortlicher"),
        queryset=None,
        empty_label=_("Alle Verantwortlichen"),
        widget=forms.Select(attrs={"class": _INPUT_CLASS}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["responsible"].queryset = User.objects.filter(
            is_active=True
        ).order_by("username")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
docker compose exec web python manage.py test apps.assets.tests.AssetFormValidationTest -v 2
```

Expected: OK (7 tests pass)

- [ ] **Step 5: Commit**

```bash
git add apps/assets/forms.py apps/assets/tests.py
git commit -m "feat: add new fields to AssetForm and department/responsible filters to AssetFilterForm"
```

---

## Task 3: Views

**Files:**
- Modify: `apps/assets/views.py`
- Modify: `apps/assets/tests.py`

- [ ] **Step 1: Write failing tests**

Append to `apps/assets/tests.py`:

```python
from django.test import TestCase, Client
from django.urls import reverse

from apps.accounts.models import User
from apps.assets.constants import Department
from apps.assets.models import Asset


class AssetFilterViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="viewer", password="pass")
        self.client.force_login(self.user)  # AssetListView only requires LoginRequiredMixin

        self.responsible = User.objects.create_user(username="resp", password="pass")
        self.deputy = User.objects.create_user(username="dep", password="pass")

        self.asset_h = Asset.objects.create(
            name="Anlage Herstellung",
            serial_number="SN-H01",
            location="Halle 1",
            device_code="H-01",
            inventory_number="INV-H01",
            department=Department.HERSTELLUNG,
            responsible=self.responsible,
            deputy=self.deputy,
        )
        self.asset_q = Asset.objects.create(
            name="Anlage QK",
            serial_number="SN-Q01",
            location="Halle 2",
            device_code="Q-01",
            inventory_number="INV-Q01",
            department=Department.QUALITAETSKONTROLLE,
            responsible=self.responsible,
            deputy=self.deputy,
        )

    def test_filter_by_department(self):
        response = self.client.get(
            reverse("assets:list"),
            {"department": Department.HERSTELLUNG},
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Anlage Herstellung")
        self.assertNotContains(response, "Anlage QK")

    def test_filter_by_responsible(self):
        other_resp = User.objects.create_user(username="other_resp", password="pass")
        Asset.objects.create(
            name="Anlage Andere",
            serial_number="SN-A01",
            location="Halle 3",
            device_code="A-01",
            inventory_number="INV-A01",
            department=Department.PROZESSENTWICKLUNG,
            responsible=other_resp,
            deputy=self.deputy,
        )
        response = self.client.get(
            reverse("assets:list"),
            {"responsible": self.responsible.pk},
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Anlage Herstellung")
        self.assertContains(response, "Anlage QK")
        self.assertNotContains(response, "Anlage Andere")
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
docker compose exec web python manage.py test apps.assets.tests.AssetFilterViewTest -v 2
```

Expected: FAIL — filter returns all assets (filter logic not updated yet)

- [ ] **Step 3: Update `apps/assets/views.py`**

**3a.** In `AssetListView.get_queryset()`, change `Asset.objects.all()` to:
```python
return _apply_filters(
    Asset.objects.select_related("responsible").all(),
    self._filter_form(),
)
```

**3b.** Add `get_queryset()` to `AssetDetailView`:
```python
def get_queryset(self):
    return super().get_queryset().select_related("responsible", "deputy")
```

**3c.** In `_apply_filters()`, append after the existing `location` filter:
```python
if cd.get("department"):
    qs = qs.filter(department=cd["department"])
if cd.get("responsible"):
    qs = qs.filter(responsible=cd["responsible"])
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
docker compose exec web python manage.py test apps.assets.tests.AssetFilterViewTest -v 2
```

Expected: OK (2 tests pass)

- [ ] **Step 5: Run full test suite**

```bash
docker compose exec web python manage.py test apps.assets -v 2
```

Expected: OK (all tests pass)

- [ ] **Step 6: Commit**

```bash
git add apps/assets/views.py apps/assets/tests.py
git commit -m "feat: extend asset list filter with department and responsible, add select_related"
```

---

## Task 4: Templates

**Files:**
- Modify: `templates/assets/asset_form.html`
- Modify: `templates/assets/asset_list.html`
- Modify: `templates/assets/partials/_asset_table.html`
- Modify: `templates/assets/asset_detail.html`

No automated tests for templates — verified visually via the running app.

- [ ] **Step 1: Update `templates/assets/asset_form.html`**

Insert the following two field groups between the `{# Status #}` block and the `{# Submit row #}` div (i.e., before `</div>` that closes `<div class="space-y-5">`):

```html
          {# ── Identifikation ──────────────────────────────────────── #}
          <div class="pt-2 border-t border-border">
            <p class="text-2xs text-content-tertiary uppercase tracking-wider font-medium mb-4">
              {% trans "Identifikation" %}
            </p>
            <div class="space-y-5">

              {# Gerätekürzel #}
              <div>
                <label class="text-2xs text-content-tertiary uppercase tracking-wider font-medium block mb-1.5">
                  {{ form.device_code.label }} <span class="text-status-danger">*</span>
                </label>
                {{ form.device_code }}
                {% if form.device_code.errors %}
                  <p class="mt-1 text-xs text-status-danger">{{ form.device_code.errors.0 }}</p>
                {% endif %}
              </div>

              {# Inventarnummer #}
              <div>
                <label class="text-2xs text-content-tertiary uppercase tracking-wider font-medium block mb-1.5">
                  {{ form.inventory_number.label }} <span class="text-status-danger">*</span>
                </label>
                {{ form.inventory_number }}
                {% if form.inventory_number.errors %}
                  <p class="mt-1 text-xs text-status-danger">{{ form.inventory_number.errors.0 }}</p>
                {% endif %}
              </div>

              {# Zugehörigkeit #}
              <div>
                <label class="text-2xs text-content-tertiary uppercase tracking-wider font-medium block mb-1.5">
                  {{ form.department.label }} <span class="text-status-danger">*</span>
                </label>
                {{ form.department }}
                {% if form.department.errors %}
                  <p class="mt-1 text-xs text-status-danger">{{ form.department.errors.0 }}</p>
                {% endif %}
              </div>

              {# Servicedienstleister #}
              <div>
                <label class="text-2xs text-content-tertiary uppercase tracking-wider font-medium block mb-1.5">
                  {{ form.service_provider.label }}
                  <span class="text-content-tertiary font-normal ml-1">{% trans "(optional)" %}</span>
                </label>
                {{ form.service_provider }}
                {% if form.service_provider.errors %}
                  <p class="mt-1 text-xs text-status-danger">{{ form.service_provider.errors.0 }}</p>
                {% endif %}
              </div>

            </div>
          </div>

          {# ── Verantwortlichkeiten ─────────────────────────────────── #}
          <div class="pt-2 border-t border-border">
            <p class="text-2xs text-content-tertiary uppercase tracking-wider font-medium mb-4">
              {% trans "Verantwortlichkeiten" %}
            </p>
            <div class="space-y-5">

              {# Verantwortlicher #}
              <div>
                <label class="text-2xs text-content-tertiary uppercase tracking-wider font-medium block mb-1.5">
                  {{ form.responsible.label }} <span class="text-status-danger">*</span>
                </label>
                {{ form.responsible }}
                {% if form.responsible.errors %}
                  <p class="mt-1 text-xs text-status-danger">{{ form.responsible.errors.0 }}</p>
                {% endif %}
              </div>

              {# Stellvertreter #}
              <div>
                <label class="text-2xs text-content-tertiary uppercase tracking-wider font-medium block mb-1.5">
                  {{ form.deputy.label }} <span class="text-status-danger">*</span>
                </label>
                {{ form.deputy }}
                {% if form.deputy.errors %}
                  <p class="mt-1 text-xs text-status-danger">{{ form.deputy.errors.0 }}</p>
                {% endif %}
              </div>

            </div>
          </div>
```

- [ ] **Step 2: Update `templates/assets/asset_list.html` — filter bar**

In the filter bar, add two new filter inputs after the existing `location` filter div and before the `<button type="submit"...>`:

```html
    <div class="flex flex-col gap-1">
      <label class="text-2xs text-content-tertiary uppercase tracking-wider font-medium">{{ filter_form.department.label }}</label>
      {{ filter_form.department }}
    </div>
    <div class="flex flex-col gap-1 min-w-40">
      <label class="text-2xs text-content-tertiary uppercase tracking-wider font-medium">{{ filter_form.responsible.label }}</label>
      {{ filter_form.responsible }}
    </div>
```

Also add `department` and `responsible` to the HTMX trigger so dropdown changes trigger a live filter. Change the existing `hx-trigger` attribute from:
```
hx-trigger="change, keyup changed delay:400ms from:[name=q], keyup changed delay:400ms from:[name=location]"
```
to:
```
hx-trigger="change, keyup changed delay:400ms from:[name=q], keyup changed delay:400ms from:[name=location]"
```
(No change needed — `change` already covers selects. The dropdowns fire on `change`.)

- [ ] **Step 3: Update `templates/assets/partials/_asset_table.html`**

**3a.** In `<thead>`, add two new `<th>` elements after `{% trans "Status" %}` and before `{% trans "Geändert am" %}`:

```html
        <th class="hidden lg:table-cell">{% trans "Zugehörigkeit" %}</th>
        <th class="hidden lg:table-cell">{% trans "Verantwortlicher" %}</th>
```

**3b.** In the Name `<td>`, append the device_code in muted text:

```html
        <td class="font-medium">
          <a href="{% url 'assets:detail' asset.pk %}"
             class="hover:text-content-primary transition-colors">
            {{ asset.name }}
          </a>
          {% if asset.device_code %}
            <span class="text-content-tertiary text-xs ml-1">· {{ asset.device_code }}</span>
          {% endif %}
        </td>
```

**3c.** Add two new `<td>` elements after the Status badge `<td>` and before the Updated at `<td>`:

```html
        {# Department #}
        <td class="hidden lg:table-cell">
          <span class="badge badge-neutral">{{ asset.get_department_display }}</span>
        </td>

        {# Responsible #}
        <td class="text-sm text-content-secondary hidden lg:table-cell">
          {{ asset.responsible.username|default:"—" }}
        </td>
```

- [ ] **Step 4: Update `templates/assets/asset_detail.html`**

Add a new **Stammdaten** section inside the main info card (`<div class="lg:col-span-2 card p-6 space-y-5">`), after the closing `</dl>` of the existing fields and before the closing `</div>` of the card:

```html
      {# Stammdaten #}
      <div class="pt-4 border-t border-border">
        <h3 class="text-2xs text-content-tertiary uppercase tracking-wider font-medium mb-4">
          {% trans "Stammdaten" %}
        </h3>
        <dl class="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-4">

          <div>
            <dt class="text-2xs text-content-tertiary uppercase tracking-wider font-medium mb-1">
              {% trans "Gerätekürzel" %}
            </dt>
            <dd class="text-sm text-content-primary font-mono">{{ asset.device_code }}</dd>
          </div>

          <div>
            <dt class="text-2xs text-content-tertiary uppercase tracking-wider font-medium mb-1">
              {% trans "Inventarnummer" %}
            </dt>
            <dd class="text-sm text-content-primary font-mono">{{ asset.inventory_number }}</dd>
          </div>

          <div>
            <dt class="text-2xs text-content-tertiary uppercase tracking-wider font-medium mb-1">
              {% trans "Zugehörigkeit" %}
            </dt>
            <dd><span class="badge badge-neutral">{{ asset.get_department_display }}</span></dd>
          </div>

          {% if asset.service_provider %}
          <div>
            <dt class="text-2xs text-content-tertiary uppercase tracking-wider font-medium mb-1">
              {% trans "Servicedienstleister" %}
            </dt>
            <dd class="text-sm text-content-primary">{{ asset.service_provider }}</dd>
          </div>
          {% endif %}

          <div>
            <dt class="text-2xs text-content-tertiary uppercase tracking-wider font-medium mb-1">
              {% trans "Verantwortlicher" %}
            </dt>
            <dd class="text-sm text-content-primary">
              {{ asset.responsible.username|default:"—" }}
            </dd>
          </div>

          <div>
            <dt class="text-2xs text-content-tertiary uppercase tracking-wider font-medium mb-1">
              {% trans "Stellvertreter" %}
            </dt>
            <dd class="text-sm text-content-primary">
              {{ asset.deputy.username|default:"—" }}
            </dd>
          </div>

        </dl>
      </div>
```

- [ ] **Step 5: Run full test suite to verify nothing broke**

```bash
docker compose exec web python manage.py test apps.assets -v 2
```

Expected: OK (all tests pass)

- [ ] **Step 6: Verify visually**

Open http://localhost:8000. Check:
1. Create a new asset — form shows Identifikation and Verantwortlichkeiten sections
2. Asset list shows Gerätekürzel next to name, Zugehörigkeit badge, Verantwortlicher column
3. Filter by Zugehörigkeit works, filter by Verantwortlicher works
4. Asset detail shows Stammdaten section with all 6 new fields

- [ ] **Step 7: Commit**

```bash
git add templates/assets/asset_form.html templates/assets/asset_list.html templates/assets/partials/_asset_table.html templates/assets/asset_detail.html
git commit -m "feat: update asset templates with new fields, filter inputs, and detail section"
```
