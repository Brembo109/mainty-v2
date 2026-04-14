# Backup & Restore

## Backup manuell erstellen

```bash
bash scripts/backup.sh
```

## Cron-Job einrichten (täglich 03:00 Uhr)

```bash
crontab -e
```

Eintrag hinzufügen (Pfad anpassen):

```cron
0 3 * * * cd /opt/mainty-v2 && bash scripts/backup.sh >> /var/log/mainty-backup.log 2>&1
```

## Konfiguration

In `.env` (Werte nach Bedarf anpassen):

```
BACKUP_DIR=/var/backups/mainty
BACKUP_RETENTION_DAYS=30
```

| Variable               | Standard                   | Beschreibung                                 |
|------------------------|----------------------------|----------------------------------------------|
| `BACKUP_DIR`           | `/backup`                  | Zielverzeichnis für Dump-Dateien             |
| `BACKUP_RETENTION_DAYS`| `30`                       | Dumps älter als N Tage werden gelöscht       |
| `COMPOSE_FILE`         | `docker-compose.prod.yml`  | Docker-Compose-Datei (optional überschreibbar) |

## Datenbank wiederherstellen

```bash
bash scripts/restore.sh /var/backups/mainty/mainty-20260414-030000.sql.gz
```

Der Restore-Prozess:
1. Prüft Gzip-Integrität der Backup-Datei
2. Zeigt eine Warnung und wartet 5 Sekunden (Ctrl-C zum Abbrechen)
3. Stoppt den Web-Container
4. Wischt das öffentliche Datenbankschema
5. Spielt den Dump ein
6. Startet den Web-Container wieder

**Erwartete Downtime:** 1–3 Minuten.
**Datenverlust:** Alles seit dem Backup-Zeitstempel (max. 24 h bei täglichem Backup).

## Auf NAS umstellen

1. NAS-Share auf dem Server mounten (NFS oder SMB):
   ```bash
   # Beispiel NFS
   mount -t nfs nas-server:/mainty /mnt/nas/mainty-backups
   ```
2. In `.env` anpassen:
   ```
   BACKUP_DIR=/mnt/nas/mainty-backups
   ```
3. Kein weiterer Eingriff nötig — das Skript schreibt in den angegebenen Pfad.
