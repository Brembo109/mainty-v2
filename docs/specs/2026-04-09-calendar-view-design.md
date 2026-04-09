# Kalenderansicht — Design Spec

**Datum:** 2026-04-09  
**Status:** Approved  

---

## Überblick

Neue eigenständige Seite in mainty, die Fälligkeitstermine aus allen 5 Modulen in einer Kombinations-Kalenderansicht (Monatsraster + Tagesdetail) darstellt. Implementiert mit Pure Django + HTMX — keine neuen JS-Abhängigkeiten.

---

## Layout

Zweigeteilte Seite:

- **Links:** Monatsraster (7×6 Grid), navigierbar per Prev/Next/Heute
- **Rechts:** Tagesdetail-Panel — erscheint beim Klick auf einen Tag, listet alle Fälligkeiten dieses Tages

Mobile: Tagesdetail klappt unterhalb des Rasters.

---

## Datenquellen

Alle 5 Module werden aggregiert. Kein neues Model, kein JSON-Endpoint — die View baut serverseitig ein Dict `{date: [events]}` für den angezeigten Monat.

| Quelle | Feld | Farbe |
|---|---|---|
| `MaintenancePlan` | `.next_due` (Property) | rot (`text-status-danger`) |
| `QualificationCycle` | `.next_due` (Property) | amber (`text-status-warning`) |
| `Task` | `.due_date` | grün (`text-status-success`) |
| `TestEquipment` | `.next_due` (nur wenn Status nicht `NEVER` oder `AT_LAB`) | blau |
| `Contract` | `.end_date` | lila |

---

## Filter

Checkboxes im Seiten-Header — ein Toggle pro Typ (Wartung, Qualifizierung, Aufgaben, Kalibrierung, Verträge). Werden als Query-Parameter `?types=maintenance,qualification,…` mit jedem HTMX-Request mitgeschickt. Grid und Day-Partial filtern anhand dieser Parameter.

Standardmäßig alle 5 Typen aktiv.

---

## URLs & Views

Alle im `core`-App (Namespace `core:`).

| URL | View | HTMX-Target |
|---|---|---|
| `/calendar/` | `CalendarView` | — (Vollseite) |
| `/calendar/?month=2026-05&types=…` | `CalendarView` | `#calendar-grid` |
| `/calendar/day/?date=2026-04-15&types=…` | `CalendarDayView` | `#calendar-day` |

`CalendarView` rendert die Hauptseite. Bei HTMX-Request (Header `HX-Request`) gibt sie nur `_calendar_grid.html` zurück.  
`CalendarDayView` gibt immer nur `_calendar_day.html` zurück.

---

## Templates

```
templates/core/
├── calendar.html                  # Hauptseite (Layout-Shell)
└── partials/
    ├── _calendar_grid.html        # Monatsraster (HTMX-swappable)
    └── _calendar_day.html         # Tagesdetail (HTMX-swappable)
```

### `calendar.html`
- Enthält Filter-Checkboxes im Header
- Zwei Spalten: `#calendar-grid` + `#calendar-day`
- Prev/Next/Heute-Buttons mit `hx-get` auf `CalendarView`, `hx-target="#calendar-grid"`

### `_calendar_grid.html`
- 7-Spalten-Grid (Mo–So)
- Jeder Tag: Datum-Zahl + farbige Dots (ein Dot pro vorhandener Event-Kategorie, max. 5)
- Heute: weiß/invertiert hervorgehoben
- Tage mit Events: `hx-get` auf `CalendarDayView`, `hx-target="#calendar-day"`
- Tage ohne Events: kein Klick-Handler

### `_calendar_day.html`
- Überschrift: Datum des gewählten Tags
- Liste aller Events (nach Typ gruppiert oder chronologisch)
- Jeder Eintrag: Typ-Farbmarker + Name + Link zur Detailseite des Objekts
- Empty-State wenn kein Tag gewählt

---

## Navigation

- **Prev/Next:** `?month=YYYY-MM` Query-Parameter, HTMX-Swap von `#calendar-grid`
- **Heute:** `?month=<aktueller Monat>`, setzt auch den Tag auf heute → beide Partials werden geladen
- Der aktuelle Monat wird aus `request.GET.get("month")` geparst, Fallback auf `date.today()`

---

## Sidebar

Neuer Eintrag "Kalender" in `templates/partials/sidebar.html`, positioniert zwischen Dashboard und Anlagen.

---

## Nicht enthalten

- Wochenansicht (YAGNI — Monatsansicht reicht für den Pilot)
- Drag & Drop
- Erstellen von Events aus dem Kalender heraus
- FullCalendar.js oder andere externe Bibliotheken
