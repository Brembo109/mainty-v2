# UI Table Consistency — Design Spec

**Date:** 2026-04-08  
**Status:** Approved  
**Scope:** Template-only changes, no model or view modifications

---

## Problem

After several feature additions, table UI across modules has accumulated three concrete inconsistencies that create an "unfinished" feel:

1. Action buttons in list tables use text links ("Bearbeiten"), while the newly added admin edit/delete buttons in detail-view record tables use icon buttons — two visual patterns for the same interaction type.
2. Days-remaining spans inherit their color from the parent `<td>` for danger/warning states, but use explicit `text-status-*` classes for the green state — inconsistent technique within the same template. The contracts module correctly uses explicit spans for all states.
3. Secondary-info table cells (Anlage, Verantwortlich, Zugewiesen) use `text-sm` in Maintenance and Qualification but `text-xs` in Tasks — same semantic role, different size.

---

## Approach

Single sweep — one commit, template files only. All three fixes applied together for an immediately coherent result.

---

## Change 1: List View Action Buttons → Icons

**Files:** `_plan_table.html`, `_cycle_table.html`, `_task_table.html`, `_equipment_table.html`

Replace the text link `"Bearbeiten"` in each list table's action column with the same icon button pattern already used in the detail-view record tables:

```html
<a href="{% url '...' %}"
   class="inline-flex items-center justify-center w-7 h-7 rounded text-content-tertiary hover:text-content-primary hover:bg-surface-card transition-colors"
   title="{% trans 'Bearbeiten' %}">
  <svg class="w-3.5 h-3.5" ...><!-- pencil icon --></svg>
</a>
```

Column width: reduce from `w-20` to `w-10` since the icon needs less space than text.

---

## Change 2: Days-Remaining Spans — Always Explicit Color

**Files:** `_plan_table.html`, `_cycle_table.html`, `_task_table.html`, `_equipment_table.html`

All days-remaining `<span>` elements get an explicit color class. No state inherits color from the parent TD. Reference pattern from contracts:

| State | Class |
|---|---|
| Overdue (`< 0`) | `text-status-danger` |
| Warning zone | `text-status-warning` |
| Green zone | `text-status-success` |

Additionally, `_equipment_table.html` (calibration list) is missing the green zone entirely — it is added here with the same threshold used in the detail view (≤ 30 days warning, green for 31–90 days).

The parent `<td>` color class on the date cell is kept for the date itself (good for visual hierarchy: date in muted color, days-count in status color).

---

## Change 3: Secondary Cells → `text-xs` Everywhere

**Files:** `_plan_table.html`, `_cycle_table.html`

The Anlage column in Maintenance and Qualification changes from `text-sm text-content-secondary` to `text-xs text-content-secondary`. Tasks and Calibration are already correct.

---

## Files Touched

| File | Changes |
|---|---|
| `templates/maintenance/partials/_plan_table.html` | Action icon, days colors, Anlage text-xs |
| `templates/qualification/partials/_cycle_table.html` | Action icon, days colors, Anlage text-xs |
| `templates/tasks/partials/_task_table.html` | Action icon, days colors |
| `templates/calibration/partials/_equipment_table.html` | Action icon, days colors + green zone |

No Python files, no migrations, no model changes.

---

## Out of Scope

- Form label typography (not reported as a pain point)
- Badge border consistency (not reported as a pain point)
- Detail-page card padding variations
- Any changes to list filter UI
