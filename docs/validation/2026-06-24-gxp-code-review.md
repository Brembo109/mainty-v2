# GxP Code- & Dokumentations-Review — mainty-v2

**Zweck:** Kriteriengetriebene Review zur Vorbereitung der Computer-System-Validierung (CSV) und des 24/7-Betriebs.
**Repository:** `Brembo109/mainty-v2` · Django 5.1 · PostgreSQL 16 · HTMX · Tailwind · Docker
**Regelwerk:** EU GMP Annex 11 + 21 CFR Part 11 (im Zweifel Part 11) · GAMP-5 Kat. 5 · ALCOA+
**Review-Datum:** 2026-06-24
**Methodik:** Statische Code-Review gegen das Review-Briefing; jeder Befund mit verifizierter `Datei:Zeile`-Evidenz. Wo die Code-Logik vom Briefing abweicht, wurde sie empirisch nachgestellt (siehe Anhang A).

> **Hinweis zur Klassifizierung:** Dieses Dokument ist eine *Code-Review*, kein Validierungsdokument. Es ersetzt keine URS, Risikoanalyse oder IQ/OQ/PQ-Protokolle (siehe Durchlauf 6).

---

## 0. Executive Summary

### Befund-Bilanz

| Severity | Anzahl | Befunde |
|---|---|---|
| **Kritisch** | 5 | F1.2, F2.1, F4.3, F5.1, (F2.5 grenzwertig) |
| **Hoch** | 16 | F1.1, F1.3, F1.4, F1.5, F1.6, F2.2, F2.3, F2.4, F2.5, F2.6, F3.1, F3.7, F4.1, F4.2, F4.4, F4.5, F5.2, F6.1 |
| **Mittel** | 8 | F2.8, F3.2, F3.4, F3.5, F4.6, F4.7, F5.3, F1.8 |
| **Niedrig** | 2 | F1.7, F4.8 |

### Top-Prioritäten vor Produktivgang

1. **Manipulationssicherheit des Audit-Trails auf DB-Ebene** (F1.2) — Hash-Kette + append-only Grants. Der App-Admin ist gesperrt (verifiziert), aber direkter DB-Zugriff bleibt offen.
2. **E-Signatur auf die Anlagen-Freigabe (Gesperrt → Frei)** (F2.1) + vollständige Part-11-Manifestation in allen lesbaren Ausgaben (F2.5).
3. **Getesteter Restore mit nachgewiesenem RTO/RPO** (F4.3); Healthchecks für `web`/`nginx` (F4.1); Migrationen vom Container-Start entkoppeln (F4.2).
4. **Testabdeckung + CI** für audit/qualification/contracts/maintenance/calibration (F5.1, F5.2).
5. **URS + Traceability-Matrix** als Fundament der Validierung (F6.1).

### Korrekturen am Briefing (Mehrwert der Verifikation)

Zwei der im Briefing vorab erwarteten Befunde halten der Code-Prüfung in dieser Form **nicht** stand:

- **Audit-Vollständigkeit bei Out-of-band-Änderungen (F1.1):** Das Briefing erwartet, dass UPDATEs außerhalb des Request-Kontexts *nicht protokolliert* werden (`leeres changes → if not changes: return`). **Das ist nicht korrekt.** Ein leerer Snapshot erzeugt in `_compute_changes` einen Diff über *alle* Felder (jeweils `[None, neuer_Wert]`), der Eintrag wird also **geschrieben** — jedoch **ohne Actor** und mit **inhaltlich falschem Diff**. Empirisch nachgestellt (Anhang A). Befund bleibt real, aber Mechanismus und Severity ändern sich (Hoch statt Kritisch).
- **Bulk-Umgehung (F1.3):** Im **Produktionscode existiert aktuell kein** `update()`/`bulk_create`/`bulk_update`/QuerySet-`delete()` auf einem `AuditedModel` (einziger Treffer: Testcode `notifications/tests.py`). Das Risiko ist **latent/architektonisch** (kein Guardrail), nicht aktiv ausgenutzt → Hoch statt Kritisch.

---

## Durchlauf 1 — Audit-Trail & Datenintegrität

### F1.2 — Keine Manipulationssicherheit des Audit-Trails auf DB-Ebene
```
[Kritisch] apps/audit/models.py:9-71, apps/audit/migrations/0001_initial.py — Audit-Log mutierbar, keine Hash-Kette
  Regulatorischer Bezug: Part 11 §11.10(c)(e); Annex 11 §9; ALCOA+ Original/Enduring
  Ist:  AuditLog besitzt KEIN Hash-, Vorgänger-Hash- oder Sequenzfeld; keine DB-Constraints/
        Trigger; der App-DB-User hat volles UPDATE/DELETE auf audit_auditlog. Der Django-Admin
        ist korrekt gesperrt (admin.py:18-24: has_add/change/delete_permission=False, alle Felder
        readonly — VERIFIZIERT), aber direkter DB-Zugriff (psql, kompromittierter App-User,
        Backup-Manipulation) kann Einträge spurlos ändern/löschen.
  Soll: Nachträgliche Änderung/Löschung/Lücke ist erkennbar (Tamper-Evidence) und/oder technisch
        unterbunden (append-only).
  Empfehlung: (1) prev_hash + row_hash (SHA-256 über kanonisierte Felder inkl. prev_hash) beim
        INSERT setzen; periodischer Ketten-Verifikationsjob. (2) Separater DB-Rolle nur mit
        INSERT/SELECT auf audit_auditlog (REVOKE UPDATE, DELETE) bzw. BEFORE UPDATE/DELETE-Trigger,
        der RAISE EXCEPTION wirft. (3) Sequenznummer zur Lückenerkennung.
```

### F1.1 — Out-of-band-Änderungen ohne Attribution und mit falschem Diff
```
[Hoch] apps/audit/signals.py:85-126 — Management-Command/Shell/Daten-Migration: Snapshot übersprungen
  Regulatorischer Bezug: ALCOA+ Attributable & Accurate; Annex 11 §9
  Ist:  _pre_save_handler legt den Vorher-Snapshot nur an, wenn get_current_user() ≠ None
        (signals.py:91). Außerhalb eines Requests (Management-Command, Shell, Daten-Migration,
        künftige Celery-Tasks) ist der Snapshot {}. _post_save_handler FEUERT TROTZDEM (Signale
        sind global registriert) und schreibt einen AuditLog — aber:
          • actor=None, actor_username="" → keine Attribution (middleware.py:27-28 bezeichnet dies
            ausdrücklich als "system action");
          • bei UPDATE wird wegen leerem Snapshot JEDES Feld als [None, neuer_Wert] protokolliert →
            der Diff ist sachlich falsch (suggeriert, alle Werte seien neu gesetzt worden).
        ⇒ Die im Briefing vermutete Folge "wird bei UPDATE nicht protokolliert" trifft NICHT zu
          (empirisch nachgestellt, Anhang A). Real ist: protokolliert, aber unattribuiert + inkorrekt.
  Soll: Out-of-band-Änderungen werden korrekt attribuiert (technischer System-Actor) UND mit
        korrektem Vorher/Nachher-Diff erfasst — oder organisatorisch unterbunden.
  Empfehlung: Bedingung `and get_current_user() is not None` in _pre_save_handler entfernen, damit
        der Snapshot IMMER gezogen wird; Management-Commands über einen Kontextmanager laufen lassen,
        der einen dedizierten "system"-User in den Thread-Local setzt; Daten-Migrationen, die
        AuditedModels ändern, unter Change Control (F4.2) stellen.
```

### F1.3 — Bulk-Operationen umgehen Signale (latentes Risiko)
```
[Hoch] (architektonisch; einziger Treffer in Testcode: apps/notifications/tests.py:128) — kein Guardrail
  Regulatorischer Bezug: ALCOA+ Complete; Annex 11 §9
  Ist:  Der gesamte Audit-Trail hängt an Instanz-Signalen (pre/post_save, post_delete). QuerySet-
        Operationen (.update(), .bulk_create(), .bulk_update(), QuerySet.delete()) umgehen diese
        vollständig. Codebasis-Sweep: KEIN solcher Aufruf auf einem AuditedModel im Produktionscode;
        einziger Treffer MaintenancePlan.objects.filter(...).update(...) liegt in Testcode. Es fehlt
        jedoch jeder technische Schutz, der solche Pfade künftig verhindert.
  Soll: Bulk-Schreibpfade auf AuditedModels sind ausgeschlossen oder explizit auditiert.
  Empfehlung: Custom Manager/QuerySet auf AuditedModel, der bulk-Writes blockt oder protokolliert;
        CI-Test/Lint-Regel, die .update()/bulk_* auf AuditedModel-Subklassen verbietet; Coding-SOP.
```

### F1.4 — „Änderungsgrund" nicht durchgängig erzwungen
```
[Hoch] tasks/models.py:44, maintenance/models.py:36-40, qualification/models.py:48-51 — change_reason lückenhaft
  Regulatorischer Bezug: Annex 11 §9 / Data Integrity ("Warum" einer Änderung); ALCOA+ Complete
  Ist:  change_reason existiert nur auf Task, MaintenancePlan, QualificationCycle — jeweils
        blank=True (DB-seitig optional). Erzwungen wird es ausschließlich in drei Update-Formularen
        (required=True), d.h. über Shell/Command/künftige API umgehbar. Es FEHLT vollständig bei den
        sicherheitskritischsten Änderungen: Asset-Statuswechsel, Kalibrier-Ergebnis, Wartungs-
        Durchführung, Vertrag. Im AuditLog erscheint der Grund nur als gewöhnliches Feld im Diff
        (sofern das Modell ihn hat); er ist nicht als eigene, jedem Eintrag fest zugeordnete Größe
        modelliert und wird bei Folgeänderungen im Modellfeld überschrieben.
  Soll: Für hoch-kritische Änderungen ist ein Grund verpflichtend und mit dem konkreten Audit-Eintrag
        verknüpft.
  Empfehlung: change_reason auf alle GMP-kritischen Schreibpfade ausweiten und serverseitig (nicht
        nur im Formular) erzwingen; als dediziertes Feld in AuditLog.changes übernehmen.
```

### F1.5 — Kein Audit-Trail-Review-Workflow
```
[Hoch] apps/audit/views.py:21-139 — nur Liste + Export, kein "geprüft"-Status
  Regulatorischer Bezug: Annex 11 §9 (regelmäßige Audit-Trail-Reviews); Data Integrity
  Ist:  Es existieren AuditLogListView (Filter/Anzeige) und AuditLogExportView (CSV/XLSX). Es gibt
        KEINEN Mechanismus, mit dem ein Reviewer Einträge oder Zeiträume als „geprüft" markiert
        (Wer/Wann/Kommentar). AuditLog hat keine reviewed_by/reviewed_at-Felder.
  Soll: Dokumentierter Review-Workflow (Reviewer markiert geprüfte Einträge/Perioden mit Zeitstempel).
  Empfehlung: AuditReview-Modell (period_from/to, reviewed_by, reviewed_at, comment) + View; flankiert
        durch SOP Audit-Trail-Review (F6.1).
```

### F1.6 — CASCADE-Löschketten auf GMP-Records
```
[Hoch] qualification/models.py:21,175 · maintenance/models.py:15,97 · calibration/models.py:130 · contracts/models.py:101
  Regulatorischer Bezug: ALCOA+ Enduring/Complete
  Ist:  on_delete=CASCADE auf Asset→QualificationCycle, Asset→Qualification, Asset→MaintenancePlan,
        MaintenancePlan→MaintenanceRecord, TestEquipment→CalibrationRecord, Contract→ContractRenewal.
        Das Löschen eines Parent-Records entfernt physisch alle abhängigen GMP-Records. Per Instanz-
        .delete() würde post_delete feuern; per QuerySet-.delete() nicht (vgl. F1.3). Es gibt keinen
        Soft-Delete für diese Records. POSITIV: QualificationSignature→Cycle ist korrekt PROTECT
        (qualification/models.py:109).
  Soll: GMP-Records sind nicht physisch löschbar; Außerbetriebnahme statt Löschung; kritische Parent-
        FKs auf PROTECT.
  Empfehlung: PROTECT statt CASCADE für GMP-relevante Parent-Beziehungen; generisches Soft-Delete-
        Pattern (is_active/decommissioned + Default-Manager-Filter) für Wartung/Qualifizierung/
        Kalibrierung/Verträge analog zu Asset.OUT_OF_SERVICE.
```

### F1.7 — Zeitintegrität (konform)
```
[Niedrig] mainty/settings/base.py:102-104 — USE_TZ korrekt; offen nur NTP-Dokumentation
  Ist:  USE_TZ=True, TIME_ZONE="Europe/Berlin"; Speicherung in UTC; AuditLog.timestamp=auto_now_add.
        Konform. Offen ist allein die (prozessuale) Dokumentation der Host-Zeitsynchronisation (NTP).
  Empfehlung: NTP-Sync des Hosts in IQ/Betriebs-SOP dokumentieren (siehe F6.1).
```

### F1.8 — Retention/Archiv-Konzept
```
[Mittel] (kein Code-Artefakt) — mehrjährige Aufbewahrung/Lesbarkeit nicht konzipiert
  Regulatorischer Bezug: Annex 11 §17; ALCOA+ Available/Enduring
  Ist:  Nur BACKUP_RETENTION_DAYS=30 (technische Backup-Rotation). Kein Konzept für GMP-Aufbewahrungs-
        fristen der Audit-/Signaturdaten über Jahre, kein Archiv-/Lesbarkeitsnachweis.
  Empfehlung: Daten-Retention- & Archivierungs-Policy (F6.1) inkl. Lesbarkeit der Exporte über die
        gesamte Aufbewahrungsfrist.
```

---

## Durchlauf 2 — Elektronische Signaturen & Part-11-Manifestation

### F2.1 — Anlagen-Freigabe (Gesperrt → Frei) ohne E-Signatur
```
[Kritisch] apps/assets/views.py:102-116 (AssetUpdateView) · apps/assets/constants.py:4-13 — Freigabe ohne Re-Auth
  Regulatorischer Bezug: Part 11 §11.10(b)/§11.50/§11.200; Annex 11 §14
  Ist:  Der Statuswechsel (free/locked/out_of_service) ist ein gewöhnliches Feld im AssetForm und wird
        über die generische AssetUpdateView (nur WriteAccessMixin = Admin|User) gespeichert. Die GMP-
        Freigabe Gesperrt→Frei erfolgt damit OHNE Re-Authentifizierung, OHNE Signatur, OHNE
        Bedeutungsangabe und OHNE Vier-Augen-Prinzip. Erfasst wird nur der generische Audit-Eintrag.
        Anmerkung: Da WriteAccessMixin auch die Rolle "User" zulässt, kann jeder Nicht-Viewer freigeben.
  Soll: Die Freigabe ist eine signaturpflichtige Aktion (Re-Auth, Bedeutung, unveränderlicher
        Signaturdatensatz, Manifestation).
  Empfehlung: Dedizierte Freigabe-View mit Re-Auth + AssetReleaseSignature-Modell nach dem Muster von
        QualificationSignature (immutable save/delete, PROTECT, Username-Snapshot, IP). Statuswechsel
        zu FREE (und ggf. LOCKED) nur über diesen signierten Pfad zulassen.
```

### F2.5 — Part-11-Manifestation (§11.50) unvollständig
```
[Hoch] templates/qualification/cycle_detail.html:91-123 (Signaturprotokoll) — Uhrzeit fehlt in der Ausgabe
  Regulatorischer Bezug: Part 11 §11.50(a)(b) — gedruckter Name + Datum/ZEIT + Bedeutung gemeinsam
  Ist:  Das Signaturprotokoll zeigt Name (signed_by_username ✓), Bedeutung (meaning ✓) und Datum.
        Das angezeigte Datum ist signed_at — ein DateField OHNE Uhrzeit. signed_at wird beim Signieren
        serverseitig auf date.today() gesetzt (qualification/views.py, also nicht frei rückdatierbar),
        enthält aber keine Uhrzeit. Der präzise Signaturzeitpunkt EXISTIERT unveränderlich
        (QualificationSignature.created_at = DateTimeField auto_now_add, models.py:138), wird in der
        Manifestation jedoch NICHT angezeigt. Es gibt keine separate Druck-/PDF-Ausgabe; die Detail-
        seite IST die menschenlesbare Ausgabe.
  Soll: Jede menschenlesbare Ausgabe einer signierten Aufzeichnung zeigt Name + Datum UND Uhrzeit +
        Bedeutung gemeinsam.
  Empfehlung: created_at (mit Uhrzeit, Zeitzone) in der Manifestation anzeigen; signed_at/created_at
        klar als „Bezugsdatum" vs. „Signaturzeitpunkt" trennen. (Briefing stuft Manifestation als
        Kritisch/präskriptiv ein; hier Hoch, da der unveränderliche Zeitstempel bereits erfasst ist und
        nur die Anzeige fehlt — Remediation gering, gemeinsam mit F2.1 umsetzen.)
```

### F2.4 — Qualification-Stufenmodell ohne Signatur
```
[Hoch] apps/qualification/models.py:161-247 (Qualification) — nur completed_by/completed_on, keine Re-Auth
  Regulatorischer Bezug: Part 11 §11.10(b)/§11.100
  Ist:  Es existieren ZWEI parallele Modelle: das ältere QualificationCycle (mit signaturpflichtigem
        Pfad, s.u.) und das neuere Stufenmodell Qualification (QP/DQ/IQ/OQ/PQ/QB + RQ). Letzteres erfasst
        Abschlüsse nur über completed_by/completed_by_username/completed_on — OHNE Re-Authentifizierung
        und OHNE Signatur. Der Abschluss einer Qualifizierungsstufe ist damit nicht signiert.
  Soll: Stufenabschlüsse sind re-auth-signaturpflichtig.
  Empfehlung: Signaturpfad (analog QualificationSignature) auf Qualification-Abschlüsse legen; Strategie
        zur Konsolidierung der beiden Qualifizierungsmodelle festlegen (Doppelmodell ist selbst ein
        Risiko für Konsistenz/Traceability).
```

### F2.2 — Kalibrier-Ergebnis ohne Signatur
```
[Hoch] apps/calibration/views.py:215-246 (CalibrationRecordCompleteView), models.py:127ff (result) — kein Re-Auth
  Regulatorischer Bezug: Part 11 §11.50/§11.100
  Ist:  Das Kalibrier-Ergebnis (result, performed_by) wird ohne Re-Authentifizierung/Signatur erfasst;
        kein Signaturprotokoll im equipment_detail-Template.
  Soll: Ergebnis (pass/fail/bedingt) ist re-auth-signaturpflichtig und manifestiert.
  Empfehlung: Signaturpfad analog QualificationSignature.
```

### F2.3 — Wartungs-Durchführungsnachweis ohne Signatur
```
[Hoch] apps/maintenance/views.py:147-160 (MaintenanceRecordCreateView), models.py:94ff (performed_by) — kein Re-Auth
  Regulatorischer Bezug: Part 11 §11.50/§11.100
  Ist:  Der Durchführungsnachweis (performed_by/performed_at/notes) wird ohne Signatur erfasst.
  Soll/Empfehlung: Re-Auth-Signatur + Manifestation analog QualificationSignature.
```

### F2.6 — Kein Dual Control / Vier-Augen-Prinzip
```
[Hoch] qualification/views.py:179-221 · calibration/models.py:146 · maintenance/models.py:104 · assets/views.py:102
  Regulatorischer Bezug: Annex 11 §2; GMP-Funktionstrennung "durchgeführt von" vs. "geprüft/freigegeben von"
  Ist:  Nirgends ist eine getrennte Zweit-Signatur erzwungen. Ein einzelner Admin signiert; performed_by
        ist überall nur eine Einzelperson. Self-Approval ist möglich (derselbe Nutzer kann erstellen und
        freigeben/signieren).
  Soll: Für Anlagenfreigaben getrennte Signaturen „durchgeführt von" ≠ „freigegeben von".
  Empfehlung: Zweit-Signatur-Feld/-Workflow; Signierer ≠ Ersteller technisch erzwingen (siehe F3.1).
```

### F2.8 — Signaturkomponenten / Verhalten bei Passwort-Reset
```
[Mittel] apps/qualification/views.py:193-206 — Re-Auth = nur Passwort
  Regulatorischer Bezug: Part 11 §11.200(a)
  Ist:  Re-Auth via authenticate(username=request.user.username, password=…). An die eindeutige User-ID
        gebunden (gut), aber Einkomponenten (Passwort). Verhalten bei Passwort-Reset/-Ablauf nicht
        dokumentiert.
  Soll: Mind. zwei Komponenten bzw. dokumentierte Bindung an die eindeutige ID; Reset/Ablauf-Verhalten
        beschrieben.
  Empfehlung: Dokumentation; optional zweite Komponente (z.B. bei besonders kritischen Freigaben).
```

### Positiv (Durchlauf 2)
- **QualificationSignature** ist ein vorbildliches Part-11-Muster: `save()`/`delete()` werfen bei vorhandener pk (immutable, models.py:148-158), `on_delete=PROTECT` (Record-Linking §11.70), Username-Snapshot, IP, Bedeutung, Re-Auth über `authenticate()`. **Empfehlung: dieses Muster auf F2.1–F2.4 übertragen.**

---

## Durchlauf 3 — Zugriffskontrolle & Konten-Lebenszyklus

### F3.1 — Funktionstrennung: Benutzerverwaltung und Freigabe in einer Rolle
```
[Hoch] apps/accounts/constants.py (Role) · accounts/views.py (User*-Views: Admin) · qualification/views.py:182 (Sign: Admin)
  Regulatorischer Bezug: Part 11 §11.10(d)/(g); Annex 11 §2
  Ist:  Rollen sind Admin/User/Viewer. Die Rolle Admin kann SOWOHL Benutzer anlegen/ändern/Rollen
        vergeben ALS AUCH Qualifizierungen signieren (QualificationSignView verlangt Role.ADMIN). Es gibt
        keine getrennte QA/Reviewer-Rolle und keine Verhinderung von Self-Approval.
  Soll: Wer Identitäten verwaltet, darf nicht zugleich eigene Qualifizierungen freigeben.
  Empfehlung: Dedizierte QA/Reviewer-Rolle; Signaturrechte daran binden; Signierer ≠ Ersteller erzwingen.
```

### F3.7 — Benutzerverwaltungs-Aktionen nicht im Audit-Trail
```
[Hoch] apps/accounts/models.py:7 (User(AbstractUser) — KEIN AuditedModel) · accounts/views.py (Create/Update/Toggle/Password)
  Regulatorischer Bezug: Part 11 §11.10(e)(k); Annex 11 §12
  Ist:  Das User-Modell erbt NICHT von AuditedModel. Damit werden sicherheitsrelevante Konto-Lebenszyklus-
        Ereignisse NICHT im Audit-Trail erfasst: Benutzer anlegen/ändern, Aktivieren/Deaktivieren,
        Rollen-(Group-)Zuweisung, Admin-Passwort-Reset. Login/Logout/Failed-Login werden zwar protokolliert
        (signals.py:169-198), die Konto-Verwaltung selbst jedoch nicht.
  Soll: Alle Konto-Lebenszyklus- und Berechtigungsänderungen sind attribuiert und auditiert.
  Empfehlung: Konto-/Rollenänderungen explizit in den Audit-Trail schreiben (dedizierte Audit-Hooks in den
        User-Views bzw. m2m_changed für Group-Mitgliedschaft), da das generische Signal-Pattern für
        Nicht-AuditedModels nicht greift.
```

### F3.2 — Hard-Delete von Nutzern weiterhin möglich
```
[Mittel] apps/accounts/views.py:267-286 (UserDeleteView) — Löschung nur bei vorhandenen actor-Einträgen blockiert
  Regulatorischer Bezug: Part 11 §11.10(d); ALCOA+ Attributable/Enduring
  Ist:  POSITIV: Deaktivieren existiert (UserToggleActiveView, is_active=False); Löschung wird mit HTTP 409
        verhindert, falls AuditLog.actor==Nutzer existiert. ABER: Nutzer OHNE eigene Audit-Einträge können
        weiterhin hart gelöscht werden. (Signatur-/Audit-Bezüge bleiben durch Username-Snapshots + SET_NULL
        lesbar, aber der Grundsatz „Deaktivieren statt Löschen" ist nicht durchgängig.)
  Soll: Ausgeschiedene Nutzer werden deaktiviert, nicht gelöscht.
  Empfehlung: Hard-Delete entfernen bzw. ausschließlich Deaktivierung anbieten.
```

### F3.4 — Keine Passwort-Historie/Wiederverwendungssperre
```
[Mittel] mainty/settings/base.py:89-94 (AUTH_PASSWORD_VALIDATORS) — keine History-Validierung
  Regulatorischer Bezug: Part 11 §11.300(b)
  Ist:  Vier Standard-Validatoren (Similarity, MinLength, CommonPassword, Numeric). POSITIV:
        Passwort-Ablauf ist umgesetzt (PASSWORD_EXPIRY_DAYS=90 via PasswordExpiryMiddleware,
        accounts/middleware.py). KEINE Sperre gegen Wiederverwendung früherer Passwörter.
  Empfehlung: Custom PasswordHistoryValidator + PasswordHistory-Modell.
```

### F3.5 — Periodische Zugriffs-Rezertifizierung fehlt
```
[Mittel] (kein Code-Artefakt) — Annex 11 §12
  Ist:  Kein Report/Mechanismus zur regelmäßigen Überprüfung der Berechtigungen.
  Empfehlung: Rezertifizierungs-Report (aktive Nutzer × Rollen × letzte Anmeldung) + SOP Periodic Review.
```

### Positiv (Durchlauf 3) — Kriterien weitgehend erfüllt
- **F3.3 Authority Checks (§11.10(g)) — erfüllt:** Alle schreibenden Views sind konsistent geschützt: `WriteAccessMixin` (Admin|User) bzw. `RoleRequiredMixin(Admin)`; `has_role` definiert in accounts/models.py:52. Einzige offene Stelle ist der bewusst unauthentifizierte Health-Endpoint (akzeptabel). *Anmerkung:* Da `WriteAccessMixin` die Rolle „User" einschließt, dürfen auch Nicht-Admins die meisten Records inkl. **Asset-Status** ändern — relevant für F2.1.
- **F3.6 Session/Lockout — erfüllt:** `SESSION_COOKIE_AGE=3600`, `SESSION_EXPIRE_AT_BROWSER_CLOSE=True`, `HTTPONLY`; django-axes 5 Versuche/15 min, `RESET_ON_SUCCESS`, per-Username; Produktion: `SESSION_COOKIE_SECURE`/`CSRF_COOKIE_SECURE`/HSTS/`X_FRAME_OPTIONS=DENY`. Passwort-Ablauf 90 Tage erzwungen.
- **Eindeutige IDs:** `User(AbstractUser)` mit eindeutigem Username; keine technischen Sammelkonten. (Ausschluss generischer Konten bleibt per SOP zu regeln — F6.1.)

---

## Durchlauf 4 — 24/7-Resilienz & Betrieb

### F4.3 — Kein getesteter Restore mit nachgewiesenem RTO/RPO
```
[Kritisch] scripts/restore.sh · docs/backup.md — Restore nie nachweislich erprobt
  Regulatorischer Bezug: Annex 11 §7.2/§16; DR
  Ist:  restore.sh ist robust (gunzip -t Integritätsprüfung, Schema-Wipe, ON_ERROR_STOP=1, Web-Restart).
        RTO/RPO sind in docs/backup.md dokumentiert (Downtime 1–3 min, Datenverlust max. 24 h). ES FEHLT
        jedoch jeder Nachweis einer erfolgreichen Wiederherstellung und ein automatisierter, periodischer
        Restore-Test.
  Soll: Periodisch automatisierter Restore-Test mit dokumentiertem, gemessenem RTO/RPO.
  Empfehlung: Geplanter Restore-Test in Staging (z.B. wöchentlich), Ergebnis-Protokollierung; RTO/RPO
        validieren statt nur behaupten; in SOP Backup & Restore (F6.1) verankern.
```

### F4.1 — Healthchecks für `web` und `nginx` fehlen
```
[Hoch] docker-compose.prod.yml:8-12 (nur db) · apps/core/health.py · mainty/urls.py — hängender Gunicorn unentdeckt
  Regulatorischer Bezug: Annex 11 §10/§16 (Betriebskontrolle/Verfügbarkeit)
  Ist:  Nur der db-Service hat einen Healthcheck (pg_isready). web (gunicorn, Zeile 19) und nginx
        (Zeilen 30-39) haben KEINEN. Ein hängender Gunicorn bleibt damit unentdeckt. POSITIV: Liveness-
        (/healthz/) und Readiness-Views (/readyz/, prüft DB + Cache, 503 bei Fehler) existieren und sind
        in urls.py verdrahtet.
  Soll: web und nginx haben Compose-Healthchecks.
  Empfehlung: web-Healthcheck gegen /readyz/ (curl, erwarte 200); nginx-Healthcheck; Restart-Policy nutzen.
```

### F4.2 — Migrationen an den Container-Start gekoppelt
```
[Hoch] docker-entrypoint.sh:14-15 — migrate --noinput beim Start
  Regulatorischer Bezug: Annex 11 §10 (Change Control)
  Ist:  Der Entrypoint führt unbedingt `python manage.py migrate --noinput` bei jedem Container-Start aus.
        Bei mehreren web-Replicas droht ein Race; zudem läuft ein Schema-Change damit außerhalb der
        Change-Control.
  Soll: Schema-Migrationen sind vom App-Start entkoppelt und stehen unter Change-Control.
  Empfehlung: migrate aus dem Entrypoint herauslösen; dedizierter, einmaliger Migrations-Job/-Schritt im
        Deployment, freigegeben unter Change Control (F6.1).
```

### F4.4 — Backup-Integrität: keine Verschlüsselung/Off-Site/Prüfsumme bei Erstellung
```
[Hoch] scripts/backup.sh — gzip + Rotation, aber ohne Verschlüsselung/Off-Site/Checksumme
  Regulatorischer Bezug: Annex 11 §7.2
  Ist:  backup.sh erzeugt gzip-Dumps mit Retention (30 Tage). KEINE Verschlüsselung at rest, KEINE
        Off-Site-/immutable Kopie (lokal /var/backups/mainty; NAS nur manuell in docs/backup.md), KEINE
        Prüfsumme/gunzip -t direkt nach Erstellung (Verifikation erfolgt erst beim Restore).
  Soll: Verifizierte, verschlüsselte, off-site/immutable gesicherte Backups.
  Empfehlung: SHA-256 + gunzip -t direkt nach dem Dump; Verschlüsselung (GPG/age); automatische
        Off-Site-/immutable Replikation (z.B. Object-Lock-Bucket).
```

### F4.5 — `send_reminders`: keine Fehler-Alarmierung; cron-basiert
```
[Hoch] apps/core/management/commands/send_reminders.py · README (cron → docker compose exec) — Fehlschlag bleibt stumm
  Regulatorischer Bezug: Annex 11 §1 (Risikomanagement); GMP-Erinnerungen sind betrieblich relevant
  Ist:  Geplant via cron/`docker compose exec`. POSITIV: once-per-day-Guard über ReminderLog. ABER: kein
        try/except, kein mail_admins/Alert bei Fehlschlag — ein fehlgeschlagener Job (SMTP down, Exception)
        = verpasste GMP-Erinnerung, ggf. 24 h unbemerkt.
  Soll: Robuster Scheduler mit Fehler-Alarmierung.
  Empfehlung: Fehler abfangen + mail_admins/Alert; Dead-Man's-Switch (z.B. healthchecks.io) oder systemd-
        Timer mit OnFailure-Benachrichtigung statt nacktem cron.
```

### F4.6 — Observability/Alerting unzureichend
```
[Mittel] mainty/settings/* (kein LOGGING-Dict) · production.py:24 (ADMINS gesetzt, aber nicht verdrahtet)
  Regulatorischer Bezug: Annex 11 §1/§13
  Ist:  Kein LOGGING-Dict (nur Django-Defaults, Konsole). ADMINS wird geparst, aber KEIN AdminEmailHandler/
        mail_admins verdrahtet; kein Sentry/zentrale Aggregation; keine Alerts für App-down/DB-down/Disk-
        voll/Backup-Fehler/Zertifikatsablauf.
  Empfehlung: LOGGING mit Rotation + AdminEmailHandler; zentrale Log-Aggregation; Infrastruktur-Alerts.
```

### F4.7 — SPOF/Failover
```
[Mittel] docker-compose.prod.yml — Einzel-DB ohne Standby
  Ist:  Kein DB-Standby/Failover dokumentiert oder konfiguriert.
  Empfehlung: DB-Standby/Replikation bzw. dokumentiertes, getestetes Failover (DR-Plan, F6.1).
```

### F4.8 — Secrets & Gunicorn-Härtung
```
[Niedrig] docker-compose.prod.yml:19 (gunicorn ohne --max-requests) · .env-Handling
  Ist:  Secrets via .env/django-environ (korrekt, nicht hartkodiert; .env gitignored). Gunicorn läuft mit
        --workers 3 --timeout 120, OHNE --max-requests/--max-requests-jitter (Memory-Leak-Mitigation fehlt).
        SECRET_KEY-Rotation nicht dokumentiert.
  Empfehlung: --max-requests 1000 --max-requests-jitter 100 ergänzen; SECRET_KEY-Rotationsverfahren
        dokumentieren.
```

---

## Durchlauf 5 — Testabdeckung GMP-kritischer Apps

### F5.1 — Keine Tests für audit/qualification/contracts/maintenance/calibration
```
[Kritisch] apps/{audit,qualification,contracts,maintenance,calibration} — 0 Testdateien (verifiziert)
  Regulatorischer Bezug: GAMP-5 Kat. 5 (funktionaler Testnachweis); Validierung
  Ist:  Tests existieren nur für accounts (33), assets (20), core (46), notifications (18), tasks (10).
        Die fünf GMP-kritischsten Apps haben KEINE Tests. Nicht getestet sind u.a.: Audit-Vollständigkeit
        je CRUD/Login/Failed-Login, Bulk-/Command-Pfade (F1.1/F1.3), Signatur-Unveränderlichkeit und
        Re-Auth-Fehlschlag, Berechnungslogik (next_due/status/Warnschwellen), Statusübergänge.
  Soll: Funktionaler Testnachweis für die validierungsrelevante Logik mit Traceability.
  Empfehlung (priorisiert): (1) Audit — genau ein korrekter Eintrag je CRUD; Login/Logout/Failed;
        Out-of-band-Verhalten (F1.1) als Regressionstest. (2) Signatur — QualificationSignature nicht
        update-/löschbar; Re-Auth mit falschem Passwort scheitert; Manifestationsfelder. (3)
        Berechnungslogik next_due/status inkl. Grenzfälle (nie signiert/überfällig/Intervallgrenze).
        (4) Statusübergänge Asset Frei/Gesperrt/Außer Betrieb mit Berechtigungs- + Audit-Prüfung.
```

### F5.2 — Keine CI-Pipeline
```
[Hoch] .github/workflows fehlt vollständig (verifiziert); kein gitlab-ci/Jenkins/tox/pre-commit
  Regulatorischer Bezug: GAMP-5 (Configuration Management); Annex 11 §10
  Ist:  Keinerlei CI. Tests laufen nicht automatisiert; kein makemigrations --check; kein Lint; kein
        Dependency-/Security-Scan; keine getaggten „validierten Stände".
  Soll: CI mit Tests, makemigrations --check, Lint, Dependency-/Security-Scan; getaggte Releases.
  Empfehlung: GitHub-Actions-Workflow (pytest, makemigrations --check --dry-run, ruff/flake8, pip-audit);
        Release-Tags als validierter Stand unter Change Control.
```

### F5.3 — Test-Settings & Coverage
```
[Mittel] pytest.ini — Tests gegen development-Settings, kein Coverage-Gate
  Ist:  DJANGO_SETTINGS_MODULE=mainty.settings.development für Tests; kein dediziertes settings/test.py;
        keine conftest.py; keine Coverage-Konfiguration/-Schwelle.
  Empfehlung: settings/test.py (schnell/deterministisch); Coverage-Messung + Mindestschwelle in CI.
```

---

## Durchlauf 6 — Dokumentation & Validierungsartefakte

### F6.1 — Validierungsdokumentation weitgehend abwesend
```
[Hoch] docs/ — vorhandene Dokumente sind Feature-Designs, keine Validierungsartefakte
  Regulatorischer Bezug: GAMP-5 Kat. 5; Annex 11 §4 (Validierung); §1 (Risikomanagement)
  Ist:  docs/specs/* sind Feature-Design-/Implementierungspläne (UI-Tabellen, Kalenderansicht) — bestätigt
        durch Lektüre. docs/backup.md ist eine Betriebsanleitung. README beschreibt Features/Setup. Es
        FEHLEN die für eine Kat.-5-Validierung erforderlichen Artefakte.
  Soll/Empfehlung — folgende Artefakte erstellen und versionieren:
```
| Artefakt | Status | Nachweis/Lücke |
|---|---|---|
| User Requirements Specification (URS) | **Fehlt** | Anforderungen nur implizit im README |
| Funktionale Risikoanalyse (ICH Q9) | **Fehlt** | — |
| Funktions-/Design-Spezifikation | **Teilweise** | nur Feature-Designs (docs/specs), nicht anforderungsbezogen |
| Traceability-Matrix (Anforderung→Spez→Test) | **Fehlt** | — |
| IQ/OQ/PQ **für das System selbst** | **Fehlt** | NICHT mit der App-Funktion „Qualifizierung" verwechseln |
| SOP Audit-Trail-Review | **Fehlt** | Code-Lücke siehe F1.5 |
| SOP Backup & Restore (inkl. getestetem RTO/RPO) | **Teilweise** | docs/backup.md vorhanden; Nachweis fehlt (F4.3) |
| Disaster-Recovery-/Business-Continuity-Plan | **Fehlt** | — |
| SOP Change Control & Release | **Fehlt** | relevant für F4.2/F5.2 |
| SOP Incident-/Abweichungsmanagement | **Fehlt** | — |
| SOP Benutzerverwaltung (Provisionierung/Review/Deaktivierung) | **Fehlt** | Code teilweise vorhanden (F3.2/F3.5/F3.7) |
| SOP Periodic Review | **Fehlt** | — |
| Daten-Retention- & Archivierungs-Policy | **Teilweise** | nur BACKUP_RETENTION_DAYS (F1.8) |

---

## Anhang A — Empirische Verifikation der Audit-Änderungslogik (zu F1.1)

Nachstellung der reinen Logik aus `apps/audit/signals.py` (`_compute_changes`) für einen Out-of-band-UPDATE,
bei dem `_pre_save_handler` den Snapshot übersprungen hat (`old_data = {}`):

```python
def _compute_changes(old_data, new_data):
    return {k: [old_data.get(k), v] for k, v in new_data.items() if old_data.get(k) != v}

_compute_changes({}, {'id': 7, 'name': 'Pump A', 'status': 'free', 'serial': None})
# → {'id': [None, 7], 'name': [None, 'Pump A'], 'status': [None, 'free']}
# changes ist NICHT leer → `if not changes: return` greift NICHT → Eintrag WIRD geschrieben,
#   aber mit actor=None/actor_username="" und einem Diff, der jedes Feld als neu (old=None) ausweist.
```

**Schlussfolgerung:** Die Briefing-Annahme „UPDATE wird nicht protokolliert" ist falsch; der reale Mangel ist
fehlende Attribution + inkorrekter Diff (siehe F1.1).

---

## Anhang B — Verifizierte Stärken (für die Validierungsakte)

- Audit-Admin vollständig gesperrt (kein Add/Change/Delete, alle Felder readonly) — `apps/audit/admin.py:18-24`.
- Unveränderliche E-Signatur mit PROTECT, Username-Snapshot, IP, Bedeutung, Re-Auth — `apps/qualification/models.py:104-158`, `views.py:179-221`.
- Konsistente Authority-Checks auf allen Schreib-Views — `apps/accounts/mixins.py`, `models.py:52`.
- Härtung Session/Lockout/Passwort-Ablauf — `mainty/settings/base.py:89-145`, `production.py`, `apps/accounts/middleware.py`.
- Zeitintegrität (USE_TZ, UTC) — `mainty/settings/base.py:102-104`.
- Liveness/Readiness-Endpunkte + robuste Backup-/Restore-Skripte (gunzip -t, ON_ERROR_STOP) — `apps/core/health.py`, `scripts/`.
```
