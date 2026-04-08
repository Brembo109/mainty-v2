# UI Table Consistency Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Standardize list table action buttons, days-remaining color spans, and secondary cell text size across all four list-table partials.

**Architecture:** Pure template changes — no Python, no migrations, no model changes. All four list-table partials are updated in a single commit.

**Tech Stack:** Django templates, Tailwind CSS utility classes

---

## Files Modified

| File | Changes |
|---|---|
| `templates/maintenance/partials/_plan_table.html` | Action icon, days colors, Anlage text-xs |
| `templates/qualification/partials/_cycle_table.html` | Action icon, days colors, Anlage text-xs |
| `templates/tasks/partials/_task_table.html` | Action icon, days colors |
| `templates/calibration/partials/_equipment_table.html` | Action icon, days colors + green zone |

---

## Task 1: Action Buttons → Icons in All Four List Tables

Replace the text "Bearbeiten" link in each table's action column with a compact icon button. The icon is the same pencil SVG already used in the detail-view record tables. Column header width shrinks from `w-20` to `w-10`.

**Files:**
- Modify: `templates/maintenance/partials/_plan_table.html`
- Modify: `templates/qualification/partials/_cycle_table.html`
- Modify: `templates/tasks/partials/_task_table.html`
- Modify: `templates/calibration/partials/_equipment_table.html`

- [ ] **Step 1: Update `_plan_table.html` action column**

Change the `<th>` width and replace the text link:

Old `<th>`:
```html
<th class="w-20"></th>
```
New `<th>`:
```html
<th class="w-10"></th>
```

Old action `<td>`:
```html
        <td>
          {% if can_write %}
          <a href="{% url 'maintenance:update' plan.pk %}"
             class="text-xs text-content-tertiary hover:text-content-primary transition-colors px-2 py-1 rounded hover:bg-surface-card">
            {% trans "Bearbeiten" %}
          </a>
          {% endif %}
        </td>
```
New action `<td>`:
```html
        <td>
          {% if can_write %}
          <a href="{% url 'maintenance:update' plan.pk %}"
             class="inline-flex items-center justify-center w-7 h-7 rounded text-content-tertiary hover:text-content-primary hover:bg-surface-card transition-colors"
             title="{% trans 'Bearbeiten' %}">
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round"
                d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L10.582 16.07a4.5 4.5 0 0 1-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 0 1 1.13-1.897l8.932-8.931Zm0 0L19.5 7.125" />
            </svg>
          </a>
          {% endif %}
        </td>
```

- [ ] **Step 2: Update `_cycle_table.html` action column**

Old `<th>`:
```html
<th class="w-20"></th>
```
New `<th>`:
```html
<th class="w-10"></th>
```

Old action `<td>`:
```html
        <td>
          {% if can_write %}
          <a href="{% url 'qualification:update' cycle.pk %}"
             class="text-xs text-content-tertiary hover:text-content-primary transition-colors px-2 py-1 rounded hover:bg-surface-card">
            {% trans "Bearbeiten" %}
          </a>
          {% endif %}
        </td>
```
New action `<td>`:
```html
        <td>
          {% if can_write %}
          <a href="{% url 'qualification:update' cycle.pk %}"
             class="inline-flex items-center justify-center w-7 h-7 rounded text-content-tertiary hover:text-content-primary hover:bg-surface-card transition-colors"
             title="{% trans 'Bearbeiten' %}">
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round"
                d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L10.582 16.07a4.5 4.5 0 0 1-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 0 1 1.13-1.897l8.932-8.931Zm0 0L19.5 7.125" />
            </svg>
          </a>
          {% endif %}
        </td>
```

- [ ] **Step 3: Update `_task_table.html` action column**

Old `<th>`:
```html
<th class="w-20"></th>
```
New `<th>`:
```html
<th class="w-10"></th>
```

Old action `<td>`:
```html
        <td>
          {% if can_write %}
          <a href="{% url 'tasks:update' task.pk %}"
             class="text-xs text-content-tertiary hover:text-content-primary transition-colors px-2 py-1 rounded hover:bg-surface-card">
            {% trans "Bearbeiten" %}
          </a>
          {% endif %}
        </td>
```
New action `<td>`:
```html
        <td>
          {% if can_write %}
          <a href="{% url 'tasks:update' task.pk %}"
             class="inline-flex items-center justify-center w-7 h-7 rounded text-content-tertiary hover:text-content-primary hover:bg-surface-card transition-colors"
             title="{% trans 'Bearbeiten' %}">
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round"
                d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L10.582 16.07a4.5 4.5 0 0 1-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 0 1 1.13-1.897l8.932-8.931Zm0 0L19.5 7.125" />
            </svg>
          </a>
          {% endif %}
        </td>
```

- [ ] **Step 4: Update `_equipment_table.html` action column**

Old `<th>`:
```html
<th class="w-20"></th>
```
New `<th>`:
```html
<th class="w-10"></th>
```

Old action `<td>`:
```html
        <td>
          {% if can_write %}
          <a href="{% url 'calibration:update' eq.pk %}"
             class="text-xs text-content-tertiary hover:text-content-primary transition-colors px-2 py-1 rounded hover:bg-surface-card">
            {% trans "Bearbeiten" %}
          </a>
          {% endif %}
        </td>
```
New action `<td>`:
```html
        <td>
          {% if can_write %}
          <a href="{% url 'calibration:update' eq.pk %}"
             class="inline-flex items-center justify-center w-7 h-7 rounded text-content-tertiary hover:text-content-primary hover:bg-surface-card transition-colors"
             title="{% trans 'Bearbeiten' %}">
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round"
                d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L10.582 16.07a4.5 4.5 0 0 1-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 0 1 1.13-1.897l8.932-8.931Zm0 0L19.5 7.125" />
            </svg>
          </a>
          {% endif %}
        </td>
```

---

## Task 2: Days-Remaining Spans — Explicit Color on Every State

Every days-remaining `<span>` gets an explicit `text-status-*` class. No state should inherit color from the parent `<td>`. Additionally, `_equipment_table.html` gains a missing green zone (31–90 days).

**Files:**
- Modify: `templates/maintenance/partials/_plan_table.html`
- Modify: `templates/qualification/partials/_cycle_table.html`
- Modify: `templates/tasks/partials/_task_table.html`
- Modify: `templates/calibration/partials/_equipment_table.html`

- [ ] **Step 1: Fix `_plan_table.html` days-remaining spans**

Old:
```html
          {% if plan.days_until_due < 0 %}
            <span class="ml-1">({{ plan.days_until_due }}d)</span>
          {% elif plan.days_until_due <= 30 %}
            <span class="ml-1">({{ plan.days_until_due }}d)</span>
          {% elif plan.days_until_due <= 90 %}
            <span class="ml-1 text-status-success">({{ plan.days_until_due }}d)</span>
          {% endif %}
```
New:
```html
          {% if plan.days_until_due < 0 %}
            <span class="ml-1 text-status-danger">({{ plan.days_until_due }}d)</span>
          {% elif plan.days_until_due <= 30 %}
            <span class="ml-1 text-status-warning">({{ plan.days_until_due }}d)</span>
          {% elif plan.days_until_due <= 90 %}
            <span class="ml-1 text-status-success">({{ plan.days_until_due }}d)</span>
          {% endif %}
```

- [ ] **Step 2: Fix `_cycle_table.html` days-remaining spans**

Old:
```html
          {% if cycle.status != 'never_signed' %}
            {% if cycle.days_until_due < 0 %}
              <span class="ml-1">({{ cycle.days_until_due }}d)</span>
            {% elif cycle.days_until_due <= 60 %}
              <span class="ml-1">({{ cycle.days_until_due }}d)</span>
            {% elif cycle.days_until_due <= 120 %}
              <span class="ml-1 text-status-success">({{ cycle.days_until_due }}d)</span>
            {% endif %}
          {% endif %}
```
New:
```html
          {% if cycle.status != 'never_signed' %}
            {% if cycle.days_until_due < 0 %}
              <span class="ml-1 text-status-danger">({{ cycle.days_until_due }}d)</span>
            {% elif cycle.days_until_due <= 60 %}
              <span class="ml-1 text-status-warning">({{ cycle.days_until_due }}d)</span>
            {% elif cycle.days_until_due <= 120 %}
              <span class="ml-1 text-status-success">({{ cycle.days_until_due }}d)</span>
            {% endif %}
          {% endif %}
```

- [ ] **Step 3: Fix `_task_table.html` days-remaining spans**

Old (only the overdue span is missing its color class):
```html
          {% if task.due_date and task.status != 'done' %}
            {% if task.days_remaining < 0 %}
              <span class="ml-1">({{ task.days_remaining }}d)</span>
            {% elif task.days_remaining <= 7 %}
              <span class="ml-1 text-status-warning">({{ task.days_remaining }}d)</span>
            {% elif task.days_remaining <= 30 %}
              <span class="ml-1 text-status-success">({{ task.days_remaining }}d)</span>
            {% endif %}
          {% endif %}
```
New:
```html
          {% if task.due_date and task.status != 'done' %}
            {% if task.days_remaining < 0 %}
              <span class="ml-1 text-status-danger">({{ task.days_remaining }}d)</span>
            {% elif task.days_remaining <= 7 %}
              <span class="ml-1 text-status-warning">({{ task.days_remaining }}d)</span>
            {% elif task.days_remaining <= 30 %}
              <span class="ml-1 text-status-success">({{ task.days_remaining }}d)</span>
            {% endif %}
          {% endif %}
```

- [ ] **Step 4: Fix `_equipment_table.html` days-remaining spans + add green zone**

Old (inside the `{% elif eq.next_due %}` branch):
```html
            {% if eq.days_until_due is not None %}
              {% if eq.days_until_due < 0 %}
                <span class="ml-1 text-status-danger">({{ eq.days_until_due }}d)</span>
              {% elif eq.days_until_due <= 30 %}
                <span class="ml-1 text-status-warning">({{ eq.days_until_due }}d)</span>
              {% endif %}
            {% endif %}
```
New (danger and warning already have explicit colors; add green zone for 31–90 days):
```html
            {% if eq.days_until_due is not None %}
              {% if eq.days_until_due < 0 %}
                <span class="ml-1 text-status-danger">({{ eq.days_until_due }}d)</span>
              {% elif eq.days_until_due <= 30 %}
                <span class="ml-1 text-status-warning">({{ eq.days_until_due }}d)</span>
              {% elif eq.days_until_due <= 90 %}
                <span class="ml-1 text-status-success">({{ eq.days_until_due }}d)</span>
              {% endif %}
            {% endif %}
```

---

## Task 3: Secondary Cells → `text-xs`

The Anlage (asset) column in Maintenance and Qualification uses `text-sm` — change to `text-xs` to match Tasks and Calibration.

**Files:**
- Modify: `templates/maintenance/partials/_plan_table.html`
- Modify: `templates/qualification/partials/_cycle_table.html`

- [ ] **Step 1: Fix `_plan_table.html` asset cell**

Old:
```html
        <td class="text-sm text-content-secondary">
          <a href="{% url 'assets:detail' plan.asset.pk %}" class="hover:text-content-primary transition-colors">
            {{ plan.asset.name }}
          </a>
        </td>
```
New:
```html
        <td class="text-xs text-content-secondary">
          <a href="{% url 'assets:detail' plan.asset.pk %}" class="hover:text-content-primary transition-colors">
            {{ plan.asset.name }}
          </a>
        </td>
```

- [ ] **Step 2: Fix `_cycle_table.html` asset cell**

Old:
```html
        <td class="text-sm text-content-secondary">
          <a href="{% url 'assets:detail' cycle.asset.pk %}" class="hover:text-content-primary transition-colors">
            {{ cycle.asset.name }}
          </a>
        </td>
```
New:
```html
        <td class="text-xs text-content-secondary">
          <a href="{% url 'assets:detail' cycle.asset.pk %}" class="hover:text-content-primary transition-colors">
            {{ cycle.asset.name }}
          </a>
        </td>
```

---

## Task 4: Verify and Commit

- [ ] **Step 1: Run Django system check**

```bash
docker compose run --rm web python manage.py check
```
Expected output: `System check identified no issues (0 silenced).`
(The known axes W006 warning is acceptable — it is pre-existing and unrelated.)

- [ ] **Step 2: Commit**

```bash
git add \
  templates/maintenance/partials/_plan_table.html \
  templates/qualification/partials/_cycle_table.html \
  templates/tasks/partials/_task_table.html \
  templates/calibration/partials/_equipment_table.html

git commit -m "fix: standardize list table UI — icon buttons, explicit days colors, text-xs cells

- Replace text 'Bearbeiten' links with pencil icon buttons (w-7 h-7) in all
  four list tables; column width reduced from w-20 to w-10
- Add explicit text-status-* class to every days-remaining span so color
  is never inherited from parent TD (matches contracts pattern)
- Add missing green zone (31–90d) to calibration equipment list table
- Change Anlage cell from text-sm to text-xs in maintenance and qualification
  tables to match tasks and calibration

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

- [ ] **Step 3: Push**

```bash
git push origin main
```
