# mainty — Kompletter Neubau mit Vercel Dashboard Design

Erstelle eine vollständig neue Django-Webanwendung namens **mainty** — eine browserbasierte
Instandhaltungssoftware für den internen Einsatz (~20–50 User). Das Projekt wird von Grund
auf neu gebaut. Die gesamte Benutzeroberfläche orientiert sich am Design des Vercel
Dashboards: dunkler Hintergrund (#000 / #111), weiße Typografie, klare Karten mit subtilen
Borders (#333), minimale Schatten, monospaced Details, scharfe Tabellen ohne visuellen
Lärm. Kein Bootstrap. Eigenes CSS (oder Tailwind CSS) konsequent im Vercel-Stil.

---

## Tech-Stack

- Python 3.12, Django (aktuellste stabile Version)
- PostgreSQL
- HTMX (für reaktive UI ohne vollständiges JavaScript-Framework)
- Tailwind CSS (über django-tailwind oder CDN-Build) — konsequent dunkles Theme
- Docker Compose, Nginx (Reverse Proxy), Gunicorn
- Alle Konfiguration über Umgebungsvariablen (.env), keine Secrets im Code

---

## Module und Funktionen

### 1. assets — Anlagenverwaltung
- CRUD für Anlagen (Name, Standort, Seriennummer, Beschreibung, Status)
- Zuordnung von Serviceverträgen zu Anlagen
- Listenansicht mit Filter- und Suchfunktion
- Detailansicht mit zugehörigen Wartungsplänen, Qualifizierungszyklen und Verträgen

### 2. contracts — Serviceverträge
- CRUD für Serviceverträge (Lieferant, Vertragsnummer, Start-/Enddatum, Beschreibung)
- Dynamische Statusberechnung: aktiv / läuft aus (< 90 Tage) / abgelaufen
- Statusanzeige prominent in Listen- und Detailansicht (farbig, Vercel-Stil: grün/gelb/rot
  als subtile Badges)
- Zuordnung zu Anlagen

### 3. maintenance — Wartungspläne
- CRUD für Wartungspläne pro Anlage
- Konfigurierbare Intervalle (täglich / wöchentlich / monatlich / jährlich / custom in Tagen)
- Fälligkeitsdatum automatisch berechnet
- Status: offen / fällig / überfällig
- Aufgaben können als erledigt markiert werden (mit Pflichtfeld "Änderungsgrund" für
  GMP-relevante Aktionen)

### 4. qualification — Qualifizierungszyklen
- CRUD für Qualifizierungszyklen pro Anlage (IQ/OQ/PQ oder custom)
- Intervall und nächstes Fälligkeitsdatum
- Status: aktuell / fällig bald / abgelaufen
- Abzeichnen mit elektronischer Signatur (Re-Authentifizierung via Passwort-Eingabe,
  Signatur mit Name + Rolle + Datum + Bedeutung wird unveränderlich gespeichert)

### 5. tasks — Aufgabenverwaltung
- Aufgaben können manuell erstellt oder automatisch aus Wartungs-/Qualifizierungsplänen
  generiert werden
- Felder: Titel, Beschreibung, Fälligkeit, Priorität, Status, zugewiesener User,
  verknüpfte Anlage
- Listenansicht mit Filter nach Status, Priorität, Anlage, User
- Dashboard-Widget: "Meine offenen Aufgaben"

### 6. reminders — Benachrichtigungssystem
- Cron-basierte E-Mail-Benachrichtigungen via Django Management Commands:
  - `send_due_reminders` — täglich für fällige/überfällige Aufgaben
  - `send_digest_notifications --frequency daily` — tägliche Zusammenfassung
  - `send_digest_notifications --frequency weekly` — wöchentliche Zusammenfassung
  - Eskalation bei überfälligen Aufgaben
- Admin erhält Benachrichtigung wenn Reminder-Jobs still fehlschlagen
- SMTP-Konfiguration komplett über .env (Host, Port, TLS, User, Passwort, Absenderadresse)

### 7. accounts — Benutzerverwaltung
- Drei Rollen: Admin, User, Viewer (serverseitig erzwungen via RoleRequiredMixin)
- Admin: Vollzugriff inkl. Benutzerverwaltung
- User: Schreibzugriff auf operative Seiten
- Viewer: Nur Lesezugriff
- Passwort-Reset per E-Mail (Self-Service)
- Brute-Force-Schutz: django-axes, Konto-Sperrung nach 5 Fehlversuchen, Cooldown 15 min
- Session-Timeout: SESSION_COOKIE_AGE = 3600, SESSION_EXPIRE_AT_BROWSER_CLOSE = True
- Passwortrotation: Ablauf nach 90 Tagen mit Middleware-Erzwingung
- Passwort-Komplexitätsregeln aktiv
- Management Command `bootstrap_roles` initialisiert die drei Standardrollen
- Management Command `create_initial_admin` legt den ersten Admin-User an

### 8. audit — Audit-Trail
- Automatischer, zeitgestempelter Audit-Trail für alle CRUD-Aktionen auf GMP-relevanten
  Modellen (via Django Signals: pre_save / post_save)
- Gespeichert: User (Name + Rolle als Snapshot), Zeitstempel, Modell, Aktion,
  alte und neue Feldwerte
- Login / Logout / Fehllogin-Events werden ebenfalls geloggt
  (via Django auth signals: user_logged_in, user_logged_out, user_login_failed)
- Audit-Trail ist schreibgeschützt in der UI — kein Löschen, kein Bearbeiten
- Datenbankschutz: separater PostgreSQL-User ohne DELETE-Rechte auf die
  audit_auditlog-Tabelle
- Audit-Trail vollständig als CSV und XLSX exportierbar
- "Änderungsgrund" (change_reason) ist Pflichtfeld für alle kritischen Aktionen
  (Wartung abzeichnen, Qualifizierung freigeben)

### 9. Elektronische Signaturen (CFR 21 Part 11)
- Bei definierten GMP-relevanten Aktionen (Wartung als erledigt markieren,
  Qualifizierung freigeben): Modal mit Passwort-Re-Authentifizierung
- Gespeichert: Benutzername, Rolle, Zeitstempel, Bedeutung der Signatur
- Unveränderlich an den Datensatz gebunden, sichtbar in der Detailansicht

---

## Dashboard (Startseite nach Login)

Vercel-inspiriertes Übersichts-Dashboard mit:
- Kachelreihe: Anzahl offener Aufgaben / fällige Wartungen / ablaufende Verträge /
  überfällige Qualifizierungen — als Zahl + Status-Badge
- Tabelle "Meine offenen Aufgaben"
- Tabelle "Nächste Fälligkeiten" (Wartungen + Qualifizierungen, die in 30 Tagen fällig sind)
- Tabelle "Verträge die bald ablaufen" (< 90 Tage)

---

## Design-Vorgaben (Vercel Dashboard Stil)

- Hintergrundfarbe: #000000 oder #0a0a0a
- Kartenfarbe: #111111 mit Border #222222
- Text: #ffffff (primär), #888888 (sekundär/Labels)
- Akzentfarbe: #ffffff (Buttons primary), dezentes Blau nur für Links
- Status-Badges: Grün (#00c853 / subtil), Gelb (#ffd600 / subtil), Rot (#ff1744 / subtil) —
  immer als kleine, runde Chips mit leicht transparentem Hintergrund
- Tabellen: keine schweren Borders, nur subtile Trennlinien (#1a1a1a)
- Navigation: vertikale Sidebar links, Icons + Labels, aktiver State mit weißem
  Text und subtiler Hintergrundhervorhebung
- Typografie: Inter oder System-Font-Stack, klare Hierarchie
- Keine abgerundeten Mega-Buttons — scharfe oder minimal abgerundete Elemente (border-radius: 6px)
- HTMX für Inline-Updates (z.B. Status ändern, Aufgaben abhaken) ohne Seitenneuladen
- Keine externen Icon-Libraries außer einem einzigen leichtgewichtigen Set (z.B. Heroicons
  via SVG-Sprites)

---

## Deployment

- Docker Compose mit Services: web (Gunicorn), db (PostgreSQL), nginx
- Nginx als Reverse Proxy mit statischen Dateien
- `.env.example` mit allen Variablen dokumentiert
- Health-Check-Endpoint unter `/health/`
- Production Checklist in README

---

## Was bewusst NICHT enthalten ist

- Kein API-Layer / keine REST-API
- Keine Celery Task Queue (Cron via Management Commands)
- Keine Dokumentenverwaltung / File-Uploads

---

## Projektreihenfolge

Bitte in dieser Reihenfolge aufbauen:
1. Django-Projektstruktur + Docker Compose + PostgreSQL + Tailwind-Setup
2. accounts-Modul (Rollen, Login, Session-Timeout, Brute-Force-Schutz)
3. audit-Modul (Signals, Modell, Schreibschutz)
4. assets-Modul
5. contracts-Modul
6. maintenance-Modul
7. qualification-Modul + elektronische Signaturen
8. tasks-Modul
9. reminders-Modul
10. Dashboard
11. UI-Polish, Export-Funktionen, README

---

## Implementierungsstand

### ✅ Schritt 1 — Django-Projektstruktur + Docker + Tailwind (abgeschlossen)

- Django 5.1, Python 3.12, PostgreSQL 16, HTMX, Tailwind CSS (Standalone CLI v3)
- Split-Settings: `base.py` / `development.py` / `production.py`
- `apps/` Namespace für alle lokalen Apps
- Docker Compose (dev: web + db + mailhog, prod: web + db + nginx)
- Tailwind Standalone CLI, Vercel-Dark Design-Tokens, Basis-Komponenten (`.card`, `.btn-*`, `.badge-*`, `.data-table`, `.nav-item`)
- `base.html` mit fixierter Sidebar, Topbar, Flash-Messages, Sprachumschalter
- `apps/core`: Health-Check `/health/`, Dashboard-Platzhalter
- i18n: Deutsch (Standard) + Englisch, `LocaleMiddleware`
- pytest-django, `.gitignore`, `.gitattributes`, `.env.example`

**First-run:**
```bash
docker compose up --build
```

---

### ✅ Schritt 2 — accounts-Modul (abgeschlossen)

- Custom `User(AbstractUser)` mit `password_changed_at`-Feld (`AUTH_USER_MODEL = "accounts.User"`)
- **Rollen** via Django Groups: `Admin`, `User`, `Viewer` — `Role`-Konstanten, `set_role()`, `has_role()`, `RoleRequiredMixin`
- **Login/Logout** unter `/accounts/login/` — standalone Vercel-Dark-Layout, kein Sidebar
- **Brute-Force-Schutz**: `django-axes` — 5 Fehlversuche → 15 Min. Sperre (by username), generische Fehlermeldung (keine Info-Leakage)
- **Passwort-Rotation**: `PasswordExpiryMiddleware` — Weiterleitung nach 90 Tagen, konfigurierbar via `PASSWORD_EXPIRY_DAYS`
- **Passwort-Reset** per E-Mail (Self-Service), vollständiger Template-Satz
- **Management Commands**: `bootstrap_roles`, `create_initial_admin` (Env-Vars oder interaktiv)
- Django Admin mit Rollen-Spalte und `prefetch_related`

**First-run:**
```bash
docker compose run web python manage.py makemigrations accounts
docker compose restart web
docker compose run web python manage.py bootstrap_roles
docker compose run web python manage.py create_initial_admin
```

---

### ⬜ Schritt 3 — audit-Modul (ausstehend)
### ⬜ Schritt 4 — assets-Modul (ausstehend)
### ⬜ Schritt 5 — contracts-Modul (ausstehend)
### ⬜ Schritt 6 — maintenance-Modul (ausstehend)
### ⬜ Schritt 7 — qualification-Modul + elektronische Signaturen (ausstehend)
### ⬜ Schritt 8 — tasks-Modul (ausstehend)
### ⬜ Schritt 9 — reminders-Modul (ausstehend)
### ⬜ Schritt 10 — Dashboard (ausstehend)
### ⬜ Schritt 11 — UI-Polish, Export-Funktionen, README (ausstehend)
