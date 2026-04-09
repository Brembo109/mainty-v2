# Kalenderansicht Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `/calendar/` page to mainty showing all 5 module due dates in a month-grid + day-detail layout, navigable by month and filterable by event type.

**Architecture:** Pure Django + HTMX — no new JS dependencies. A `calendar_utils.py` helper builds `{date: [events]}` from all 5 sources. `CalendarView` renders the full page or just the grid partial on HTMX nav requests. `CalendarDayView` returns the day-detail partial on day click.

**Tech Stack:** Django 5.1, HTMX 1.9, Python `calendar` stdlib, Tailwind CSS (existing design tokens)

---

## File Map

| Action | Path | Responsibility |
|---|---|---|
| Create | `apps/core/calendar_utils.py` | Aggregate events from all 5 sources into `{date: [event_dict]}` |
| Create | `apps/core/tests/__init__.py` | Empty — makes tests a package |
| Create | `apps/core/tests/test_calendar.py` | Tests for utils + views |
| Modify | `apps/core/views.py` | Add `_parse_month`, `CalendarView`, `CalendarDayView` |
| Modify | `apps/core/urls.py` | Add `calendar/` and `calendar/day/` URL patterns |
| Create | `templates/core/calendar.html` | Page shell: filter bar + two-column layout |
| Create | `templates/core/partials/_calendar_grid.html` | Month grid (HTMX-swappable) |
| Create | `templates/core/partials/_calendar_day.html` | Day-detail panel (HTMX-swappable) |
| Modify | `templates/partials/sidebar.html` | Add "Kalender" nav item between Dashboard and Betrieb section |

---

## Task 1: Data aggregation helper

**Files:**
- Create: `apps/core/calendar_utils.py`
- Create: `apps/core/tests/__init__.py`
- Create: `apps/core/tests/test_calendar.py`

- [ ] **Step 1: Create empty test package**

```bash
mkdir -p apps/core/tests
touch apps/core/tests/__init__.py
```

- [ ] **Step 2: Write failing tests for `build_month_events`**

Create `apps/core/tests/test_calendar.py`:

```python
import pytest
from datetime import date
from apps.core.calendar_utils import build_month_events, ALL_TYPES


@pytest.mark.django_db
def test_build_month_events_returns_dict():
    result = build_month_events(2026, 4, ALL_TYPES)
    assert isinstance(result, dict)
    for key in result:
        assert isinstance(key, date)
    for value in result.values():
        assert isinstance(value, list)
        for event in value:
            assert "type" in event
            assert "label" in event
            assert "url" in event
            assert "dot_color" in event


@pytest.mark.django_db
def test_build_month_events_empty_types():
    result = build_month_events(2026, 4, [])
    assert result == {}


@pytest.mark.django_db
def test_build_month_events_only_includes_requested_month(db):
    from apps.tasks.models import Task
    from apps.assets.models import Asset
    from apps.accounts.models import User
    # Task in target month
    task_in = Task.objects.create(
        title="In month",
        due_date=date(2026, 4, 15),
        status="open",
        priority="medium",
        change_reason="test",
    )
    # Task outside target month
    task_out = Task.objects.create(
        title="Out of month",
        due_date=date(2026, 5, 1),
        status="open",
        priority="medium",
        change_reason="test",
    )
    result = build_month_events(2026, 4, ["task"])
    all_labels = [e["label"] for events in result.values() for e in events]
    assert "In month" in all_labels
    assert "Out of month" not in all_labels


@pytest.mark.django_db
def test_build_month_events_done_tasks_excluded():
    from apps.tasks.models import Task
    Task.objects.create(
        title="Done task",
        due_date=date(2026, 4, 10),
        status="done",
        priority="medium",
        change_reason="test",
    )
    result = build_month_events(2026, 4, ["task"])
    all_labels = [e["label"] for events in result.values() for e in events]
    assert "Done task" not in all_labels


@pytest.mark.django_db
def test_build_month_events_calibration_skips_at_lab_and_never(db):
    from apps.calibration.models import TestEquipment, CalibrationRecord
    # Equipment with no records → status NEVER → excluded
    eq = TestEquipment.objects.create(
        name="Waage",
        serial_number="SN-001",
        calibration_interval_days=365,
    )
    result = build_month_events(2026, 4, ["calibration"])
    all_labels = [e["label"] for events in result.values() for e in events]
    assert "Waage" not in all_labels
```

- [ ] **Step 3: Run tests to confirm they fail**

```bash
docker compose exec web pytest apps/core/tests/test_calendar.py -v
```

Expected: `ImportError` or `ModuleNotFoundError` for `calendar_utils`

- [ ] **Step 4: Implement `calendar_utils.py`**

Create `apps/core/calendar_utils.py`:

```python
import calendar
from collections import defaultdict
from datetime import date, timedelta

from django.urls import reverse
from django.db.models import Max

ALL_TYPES = ["maintenance", "qualification", "task", "calibration", "contract"]

# Per-type visual config
_TYPE_CONFIG = {
    "maintenance": {"dot_color": "bg-status-danger", "text_color": "text-status-danger"},
    "qualification": {"dot_color": "bg-status-warning", "text_color": "text-status-warning"},
    "task": {"dot_color": "bg-status-success", "text_color": "text-status-success"},
    "calibration": {"dot_color": "bg-blue-400", "text_color": "text-blue-400"},
    "contract": {"dot_color": "bg-purple-400", "text_color": "text-purple-400"},
}


def build_month_events(year: int, month: int, types: list) -> dict:
    """
    Returns {date: [event_dict]} for all matching events in the given month.

    event_dict keys: type, label, url, dot_color, text_color
    """
    if not types:
        return {}

    from apps.maintenance.models import MaintenancePlan
    from apps.qualification.models import QualificationCycle
    from apps.tasks.models import Task
    from apps.calibration.models import TestEquipment
    from apps.calibration.constants import CalibrationStatus
    from apps.contracts.models import Contract

    first_day = date(year, month, 1)
    last_day = date(year, month, calendar.monthrange(year, month)[1])
    events = defaultdict(list)

    if "maintenance" in types:
        plans = MaintenancePlan.objects.select_related("asset").annotate(
            last_performed_at=Max("records__performed_at")
        )
        for plan in plans:
            nd = plan.next_due
            if first_day <= nd <= last_day:
                events[nd].append({
                    "type": "maintenance",
                    "label": str(plan),
                    "url": reverse("maintenance:detail", args=[plan.pk]),
                    **_TYPE_CONFIG["maintenance"],
                })

    if "qualification" in types:
        cycles = QualificationCycle.objects.select_related("asset").annotate(
            last_signed_at=Max("signatures__signed_at")
        )
        for cycle in cycles:
            nd = cycle.next_due
            if first_day <= nd <= last_day:
                events[nd].append({
                    "type": "qualification",
                    "label": str(cycle),
                    "url": reverse("qualification:detail", args=[cycle.pk]),
                    **_TYPE_CONFIG["qualification"],
                })

    if "task" in types:
        tasks = Task.objects.filter(
            due_date__year=year,
            due_date__month=month,
        ).exclude(status="done")
        for task in tasks:
            events[task.due_date].append({
                "type": "task",
                "label": task.title,
                "url": reverse("tasks:detail", args=[task.pk]),
                **_TYPE_CONFIG["task"],
            })

    if "calibration" in types:
        equipment_list = TestEquipment.objects.prefetch_related("records")
        for eq in equipment_list:
            if eq.status in (CalibrationStatus.AT_LAB, CalibrationStatus.NEVER):
                continue
            nd = eq.next_due
            if nd is not None and first_day <= nd <= last_day:
                events[nd].append({
                    "type": "calibration",
                    "label": eq.name,
                    "url": reverse("calibration:detail", args=[eq.pk]),
                    **_TYPE_CONFIG["calibration"],
                })

    if "contract" in types:
        contracts = Contract.objects.filter(
            end_date__year=year,
            end_date__month=month,
        )
        for contract in contracts:
            events[contract.end_date].append({
                "type": "contract",
                "label": contract.title,
                "url": reverse("contracts:detail", args=[contract.pk]),
                **_TYPE_CONFIG["contract"],
            })

    return dict(events)


def build_day_events(target_date: date, types: list) -> list:
    """Returns list of event_dicts for a single date."""
    return build_month_events(target_date.year, target_date.month, types).get(
        target_date, []
    )
```

- [ ] **Step 5: Run tests — expect them to pass**

```bash
docker compose exec web pytest apps/core/tests/test_calendar.py -v
```

Expected: all 5 tests PASS

- [ ] **Step 6: Commit**

```bash
git add apps/core/calendar_utils.py apps/core/tests/__init__.py apps/core/tests/test_calendar.py
git commit -m "feat: calendar_utils — aggregate month events from all 5 sources"
```

---

## Task 2: Views

**Files:**
- Modify: `apps/core/views.py` (append at end)
- Modify: `apps/core/tests/test_calendar.py` (add view tests)

- [ ] **Step 1: Write failing view tests**

Append to `apps/core/tests/test_calendar.py`:

```python
@pytest.mark.django_db
def test_calendar_view_get_full_page(client):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.create_user(
        username="testuser", password="testpass123", role="User"
    )
    client.force_login(user)
    response = client.get("/calendar/")
    assert response.status_code == 200
    assert b"calendar-grid" in response.content


@pytest.mark.django_db
def test_calendar_view_htmx_returns_partial(client):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.create_user(
        username="testuser2", password="testpass123", role="User"
    )
    client.force_login(user)
    response = client.get(
        "/calendar/?month=2026-05",
        HTTP_HX_REQUEST="true",
    )
    assert response.status_code == 200
    # Partial does not contain the full page shell
    assert b"<!DOCTYPE" not in response.content


@pytest.mark.django_db
def test_calendar_day_view_returns_partial(client):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.create_user(
        username="testuser3", password="testpass123", role="User"
    )
    client.force_login(user)
    response = client.get("/calendar/day/?date=2026-04-15")
    assert response.status_code == 200
    assert b"calendar-day" in response.content


@pytest.mark.django_db
def test_calendar_view_redirects_unauthenticated(client):
    response = client.get("/calendar/")
    assert response.status_code == 302
    assert "/accounts/login/" in response["Location"]
```

- [ ] **Step 2: Run tests — expect failure**

```bash
docker compose exec web pytest apps/core/tests/test_calendar.py::test_calendar_view_get_full_page -v
```

Expected: `404` because URL not registered yet

- [ ] **Step 3: Add views to `apps/core/views.py`**

Append at the end of `apps/core/views.py`:

```python
import calendar as _calendar
from apps.core.calendar_utils import build_month_events, build_day_events, ALL_TYPES


def _parse_month(month_str):
    """Parse 'YYYY-MM' string; fall back to today's month."""
    if month_str:
        try:
            year, month = month_str.split("-")
            return int(year), int(month)
        except (ValueError, AttributeError):
            pass
    today = date.today()
    return today.year, today.month


class CalendarView(LoginRequiredMixin, View):
    def get(self, request):
        year, month = _parse_month(request.GET.get("month"))
        types = request.GET.getlist("types") or ALL_TYPES

        first_day = date(year, month, 1)
        cal = _calendar.Calendar(firstweekday=0)  # Monday first
        weeks = cal.monthdatescalendar(year, month)
        events_by_date = build_month_events(year, month, types)

        # Build dots dict: {date: {type: dot_color}} — unique type per day
        dots_by_date = {}
        for d, evts in events_by_date.items():
            seen = {}
            for e in evts:
                if e["type"] not in seen:
                    seen[e["type"]] = e["dot_color"]
            dots_by_date[d] = seen

        today = date.today()
        # Prev/next month strings for HTMX nav links
        if month == 1:
            prev_month = f"{year - 1}-12"
        else:
            prev_month = f"{year}-{month - 1:02d}"
        if month == 12:
            next_month = f"{year + 1}-01"
        else:
            next_month = f"{year}-{month + 1:02d}"

        ctx = {
            "year": year,
            "month": month,
            "first_day": first_day,
            "weeks": weeks,
            "events_by_date": events_by_date,
            "dots_by_date": dots_by_date,
            "today": today,
            "selected_types": types,
            "all_types": ALL_TYPES,
            "prev_month": prev_month,
            "next_month": next_month,
        }

        if request.headers.get("HX-Request"):
            return render(request, "core/partials/_calendar_grid.html", ctx)
        return render(request, "core/calendar.html", ctx)


class CalendarDayView(LoginRequiredMixin, View):
    def get(self, request):
        date_str = request.GET.get("date", "")
        types = request.GET.getlist("types") or ALL_TYPES
        selected_date = None
        day_events = []

        if date_str:
            try:
                selected_date = date.fromisoformat(date_str)
                day_events = build_day_events(selected_date, types)
            except ValueError:
                pass

        return render(request, "core/partials/_calendar_day.html", {
            "selected_date": selected_date,
            "day_events": day_events,
        })
```

- [ ] **Step 4: Register URLs in `apps/core/urls.py`**

Replace the contents of `apps/core/urls.py` with:

```python
from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.index, name="index"),
    path("calendar/", views.CalendarView.as_view(), name="calendar"),
    path("calendar/day/", views.CalendarDayView.as_view(), name="calendar-day"),
    path("settings/", views.SettingsView.as_view(), name="settings"),
    path("settings/test-email/", views.SendTestEmailView.as_view(), name="settings-test-email"),
]
```

- [ ] **Step 5: Run all view tests**

```bash
docker compose exec web pytest apps/core/tests/test_calendar.py -v
```

Expected: all 9 tests PASS

- [ ] **Step 6: Commit**

```bash
git add apps/core/views.py apps/core/urls.py apps/core/tests/test_calendar.py
git commit -m "feat: CalendarView and CalendarDayView — month grid + day detail HTMX views"
```

---

## Task 3: Sidebar link

**Files:**
- Modify: `templates/partials/sidebar.html`

- [ ] **Step 1: Add Kalender nav item**

In `templates/partials/sidebar.html`, insert the following block directly after the Dashboard `<a>` tag (before the `{# Betrieb section header #}` `<div>`):

```html
  {# Calendar #}
  <a href="{% url 'core:calendar' %}"
     class="nav-item {% if request.resolver_match.app_name == 'core' and request.resolver_match.url_name == 'calendar' %}active{% endif %}">
    <svg class="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
      <path stroke-linecap="round" stroke-linejoin="round"
        d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 0 1 2.25-2.25h13.5A2.25 2.25 0 0 1 21 7.5v11.25m-18 0A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75m-18 0v-7.5A2.25 2.25 0 0 1 5.25 9h13.5A2.25 2.25 0 0 1 21 11.25v7.5" />
    </svg>
    <span>{% trans "Kalender" %}</span>
  </a>
```

- [ ] **Step 2: Smoke test — visit the calendar page**

```bash
docker compose exec web python manage.py check
```

Expected: `System check identified no issues.`

- [ ] **Step 3: Commit**

```bash
git add templates/partials/sidebar.html
git commit -m "feat: add Kalender nav item to sidebar"
```

---

## Task 4: Templates

**Files:**
- Create: `templates/core/partials/_calendar_grid.html`
- Create: `templates/core/partials/_calendar_day.html`
- Create: `templates/core/calendar.html`

- [ ] **Step 1: Create partials directory**

```bash
mkdir -p templates/core/partials
```

- [ ] **Step 2: Create `_calendar_grid.html`**

Create `templates/core/partials/_calendar_grid.html`:

```html
{% load i18n %}
<div id="calendar-grid">
  {# Month navigation header #}
  <div class="flex items-center justify-between mb-4">
    <button
      hx-get="{% url 'core:calendar' %}?month={{ prev_month }}{% for t in selected_types %}&types={{ t }}{% endfor %}"
      hx-target="#calendar-grid"
      hx-swap="outerHTML"
      class="p-1.5 rounded hover:bg-surface-elevated text-content-secondary hover:text-content-primary transition-colors"
      title="{% trans "Vorheriger Monat" %}">
      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5 8.25 12l7.5-7.5"/>
      </svg>
    </button>

    <span class="text-sm font-semibold text-content-primary">
      {{ first_day|date:"F Y" }}
    </span>

    <button
      hx-get="{% url 'core:calendar' %}?month={{ next_month }}{% for t in selected_types %}&types={{ t }}{% endfor %}"
      hx-target="#calendar-grid"
      hx-swap="outerHTML"
      class="p-1.5 rounded hover:bg-surface-elevated text-content-secondary hover:text-content-primary transition-colors"
      title="{% trans "Nächster Monat" %}">
      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5"/>
      </svg>
    </button>
  </div>

  {# Weekday headers Mo–So #}
  <div class="grid grid-cols-7 mb-1">
    {% for day in "MDMDFS S"|make_list %}{% endfor %}
    {% with days="Mo,Di,Mi,Do,Fr,Sa,So" %}
    {% for day in days|split:"," %}
    <div class="text-center text-2xs font-medium text-content-tertiary py-1">{{ day }}</div>
    {% endfor %}
    {% endwith %}
  </div>

  {# Calendar grid #}
  <div class="grid grid-cols-7 gap-px">
    {% for week in weeks %}
      {% for day in week %}
        {% with is_today=day|date:"Y-m-d" == today|date:"Y-m-d" %}
        {% with is_current_month=day.month == month %}
        {% with day_dots=dots_by_date|get_item:day %}
        {% if day_dots %}
        <button
          hx-get="{% url 'core:calendar-day' %}?date={{ day|date:'Y-m-d' }}{% for t in selected_types %}&types={{ t }}{% endfor %}"
          hx-target="#calendar-day"
          hx-swap="innerHTML"
          class="aspect-square flex flex-col items-center justify-start pt-1 rounded text-xs transition-colors hover:bg-surface-elevated cursor-pointer
            {% if is_today %}bg-content-primary text-surface font-bold{% elif is_current_month %}text-content-primary{% else %}text-content-tertiary{% endif %}">
          <span>{{ day.day }}</span>
          <div class="flex gap-0.5 mt-0.5 flex-wrap justify-center">
            {% for type, color in day_dots.items %}
            <span class="w-1 h-1 rounded-full {{ color }} {% if is_today %}opacity-60{% endif %}"></span>
            {% endfor %}
          </div>
        </button>
        {% else %}
        <div class="aspect-square flex items-center justify-center rounded text-xs
            {% if is_today %}bg-content-primary text-surface font-bold{% elif is_current_month %}text-content-primary{% else %}text-content-tertiary{% endif %}">
          {{ day.day }}
        </div>
        {% endif %}
        {% endwith %}
        {% endwith %}
        {% endwith %}
      {% endfor %}
    {% endfor %}
  </div>

  {# Heute button #}
  <div class="mt-3">
    <button
      hx-get="{% url 'core:calendar' %}?month={{ today|date:'Y-m' }}{% for t in selected_types %}&types={{ t }}{% endfor %}"
      hx-target="#calendar-grid"
      hx-swap="outerHTML"
      class="text-xs text-content-secondary hover:text-content-primary transition-colors px-2 py-1 rounded hover:bg-surface-elevated">
      {% trans "Heute" %}
    </button>
  </div>
</div>
```

**Note on template filter:** The `|get_item:day` filter is not built-in. Add a custom template filter (see Step 3 below). The weekday header loop also uses a simpler hardcoded approach — use a context variable `weekday_names` from the view instead (see Step 4).

- [ ] **Step 3: Add `get_item` template filter**

Create `apps/core/templatetags/calendar_tags.py`:

```python
from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Allow dict[key] access in templates: {{ mydict|get_item:somevar }}"""
    return dictionary.get(key)
```

Create `apps/core/templatetags/__init__.py` (empty file if not present):

```bash
mkdir -p apps/core/templatetags
touch apps/core/templatetags/__init__.py
```

- [ ] **Step 4: Simplify grid template using `get_item` and context weekday names**

Update `CalendarView.get()` in `apps/core/views.py` — add `weekday_names` to context:

```python
ctx = {
    ...
    "weekday_names": ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"],
}
```

Then replace the weekday header block in `_calendar_grid.html` with:

```html
  {# Weekday headers #}
  <div class="grid grid-cols-7 mb-1">
    {% for name in weekday_names %}
    <div class="text-center text-2xs font-medium text-content-tertiary py-1">{{ name }}</div>
    {% endfor %}
  </div>
```

And update the dots lookup to use the filter (add `{% load calendar_tags %}` at top of template):

```html
{% load i18n calendar_tags %}
...
{% with day_dots=dots_by_date|get_item:day %}
```

- [ ] **Step 5: Create `_calendar_day.html`**

Create `templates/core/partials/_calendar_day.html`:

```html
{% load i18n %}
<div id="calendar-day">
  {% if selected_date %}
  <h3 class="text-sm font-semibold text-content-primary mb-3">
    {{ selected_date|date:"l, j. F Y" }}
  </h3>

  {% if day_events %}
  <ul class="space-y-2">
    {% for event in day_events %}
    <li>
      <a href="{{ event.url }}"
         class="flex items-start gap-2 p-2 rounded hover:bg-surface-elevated transition-colors group">
        <span class="mt-1.5 w-2 h-2 rounded-full shrink-0 {{ event.dot_color }}"></span>
        <div>
          <p class="text-xs font-medium text-content-primary group-hover:text-content-primary leading-snug">
            {{ event.label }}
          </p>
          <p class="text-2xs text-content-tertiary mt-0.5">
            {% if event.type == "maintenance" %}{% trans "Wartung" %}
            {% elif event.type == "qualification" %}{% trans "Qualifizierung" %}
            {% elif event.type == "task" %}{% trans "Aufgabe" %}
            {% elif event.type == "calibration" %}{% trans "Kalibrierung" %}
            {% elif event.type == "contract" %}{% trans "Vertrag" %}
            {% endif %}
          </p>
        </div>
        <svg class="w-3.5 h-3.5 ml-auto text-content-tertiary group-hover:text-content-secondary shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5"/>
        </svg>
      </a>
    </li>
    {% endfor %}
  </ul>
  {% else %}
  <p class="text-xs text-content-tertiary">{% trans "Keine Fälligkeiten an diesem Tag." %}</p>
  {% endif %}

  {% else %}
  <p class="text-xs text-content-tertiary">{% trans "Tag auswählen, um Details zu sehen." %}</p>
  {% endif %}
</div>
```

- [ ] **Step 6: Create `calendar.html` (page shell)**

Create `templates/core/calendar.html`:

```html
{% extends "base.html" %}
{% load i18n calendar_tags %}

{% block title %}{% trans "Kalender" %}{% endblock %}

{% block content %}
<div class="p-6 max-w-5xl mx-auto">

  {# Page header + filter bar #}
  <div class="flex flex-col sm:flex-row sm:items-center gap-4 mb-6">
    <h1 class="text-lg font-semibold text-content-primary">{% trans "Kalender" %}</h1>

    {# Type filter checkboxes #}
    <div class="flex flex-wrap gap-2 sm:ml-auto" id="calendar-filters">
      {% with type_labels="maintenance:Wartung,qualification:Qualifizierung,task:Aufgaben,calibration:Kalibrierung,contract:Verträge" %}
      {% for pair in type_labels|split:"," %}
      {% with parts=pair|split:":" %}
      {% with type_key=parts.0 type_label=parts.1 %}
      <label class="flex items-center gap-1.5 cursor-pointer">
        <input type="checkbox"
               name="types"
               value="{{ type_key }}"
               {% if type_key in selected_types %}checked{% endif %}
               class="sr-only peer"
               onchange="applyFilters()">
        <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs border border-border
                     peer-checked:border-transparent
                     {% if type_key == 'maintenance' %}peer-checked:bg-status-danger/20 peer-checked:text-status-danger
                     {% elif type_key == 'qualification' %}peer-checked:bg-status-warning/20 peer-checked:text-status-warning
                     {% elif type_key == 'task' %}peer-checked:bg-status-success/20 peer-checked:text-status-success
                     {% elif type_key == 'calibration' %}peer-checked:bg-blue-400/20 peer-checked:text-blue-400
                     {% elif type_key == 'contract' %}peer-checked:bg-purple-400/20 peer-checked:text-purple-400
                     {% endif %}
                     text-content-secondary transition-colors">
          <span class="w-1.5 h-1.5 rounded-full
                       {% if type_key == 'maintenance' %}bg-status-danger
                       {% elif type_key == 'qualification' %}bg-status-warning
                       {% elif type_key == 'task' %}bg-status-success
                       {% elif type_key == 'calibration' %}bg-blue-400
                       {% elif type_key == 'contract' %}bg-purple-400
                       {% endif %}"></span>
          {{ type_label }}
        </span>
      </label>
      {% endwith %}
      {% endwith %}
      {% endfor %}
      {% endwith %}
    </div>
  </div>

  {# Two-column layout: grid + day detail #}
  <div class="flex flex-col lg:flex-row gap-6">
    {# Calendar grid — left column #}
    <div class="lg:w-80 shrink-0 bg-surface-elevated rounded-lg border border-border p-4">
      {% include "core/partials/_calendar_grid.html" %}
    </div>

    {# Day detail — right column #}
    <div class="flex-1 bg-surface-elevated rounded-lg border border-border p-4">
      {% include "core/partials/_calendar_day.html" %}
    </div>
  </div>
</div>

<script>
function applyFilters() {
  const checked = [...document.querySelectorAll('#calendar-filters input[name="types"]:checked')]
    .map(cb => cb.value);
  const params = new URLSearchParams();
  const month = new URLSearchParams(window.location.search).get('month');
  if (month) params.set('month', month);
  checked.forEach(t => params.append('types', t));

  htmx.ajax('GET', '{% url "core:calendar" %}?' + params.toString(), {
    target: '#calendar-grid',
    swap: 'outerHTML',
  });
}
</script>
{% endblock %}
```

**Note:** The `|split` filter is also non-standard. Add it to `calendar_tags.py`:

```python
@register.filter
def split(value, delimiter=","):
    return value.split(delimiter)
```

- [ ] **Step 7: Run full test suite**

```bash
docker compose exec web pytest apps/core/tests/test_calendar.py -v
```

Expected: all tests PASS

- [ ] **Step 8: Manual smoke test**

Open `http://localhost:8000/calendar/` in the browser.

Verify:
- Month grid renders with weekday headers
- Kalender appears in sidebar, highlights correctly
- Prev/Next buttons navigate months (HTMX swap)
- Days with events show colored dots
- Clicking a day loads the day detail panel on the right
- Each event in the panel links to the correct detail page
- Filter checkboxes update the grid

- [ ] **Step 9: Commit**

```bash
git add templates/core/calendar.html templates/core/partials/_calendar_grid.html templates/core/partials/_calendar_day.html apps/core/templatetags/
git commit -m "feat: calendar view templates — month grid, day detail, filter bar"
```
