# Backup & Restore

## Run a manual backup

```bash
bash scripts/backup.sh
```

## Schedule daily backups (cron)

```bash
crontab -e
```

Add the following entry (adjust the path):

```cron
0 3 * * * cd /opt/mainty-v2 && bash scripts/backup.sh >> /var/log/mainty-backup.log 2>&1
```

## Configuration

In `.env` (adjust values as needed):

```
BACKUP_DIR=/var/backups/mainty
BACKUP_RETENTION_DAYS=30
```

| Variable                | Default                    | Description                                      |
|-------------------------|----------------------------|--------------------------------------------------|
| `BACKUP_DIR`            | `/var/backups/mainty`      | Directory where dump files are written           |
| `BACKUP_RETENTION_DAYS` | `30`                       | Dumps older than N days are automatically deleted |
| `COMPOSE_FILE`          | `docker-compose.prod.yml`  | Docker Compose file (optional override)          |

## Restore the database

```bash
bash scripts/restore.sh /var/backups/mainty/mainty-20260414-030000.sql.gz
```

The restore process:
1. Displays a warning and waits 5 seconds (press Ctrl-C to abort)
2. Verifies gzip integrity of the backup file
3. Stops the web container
4. Wipes the public database schema
5. Restores the dump
6. Restarts the web container

**Expected downtime:** 1–3 minutes.  
**Data loss:** Everything since the backup timestamp (max. 24 h with daily backups).

## Switching to NAS storage

1. Mount the NAS share on the server (NFS or SMB):
   ```bash
   # NFS example
   mount -t nfs nas-server:/mainty /mnt/nas/mainty-backups
   ```
2. Update `.env`:
   ```
   BACKUP_DIR=/mnt/nas/mainty-backups
   ```
3. No further changes needed — the script writes to the configured path.
