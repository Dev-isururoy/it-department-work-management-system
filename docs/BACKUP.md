# Backup, restore, and archival

## Backup on Windows

1. Stop the application with Ctrl+C or stop its service. This avoids a database/file race while original attachments are being copied.
2. In the project folder, run:

   ```powershell
   .\.venv\Scripts\python.exe scripts/backup.py create backups\kelun-2026-10-01.zip --server-stopped
   ```

   Choose a new filename for each backup. The command refuses to overwrite an existing backup. It takes a SQLite backup, checks database integrity, checks every referenced original attachment against its saved SHA-256 hash, copies thumbnails, and includes a manifest of file hashes.
3. Store a protected copy on approved separate storage. The ZIP is not encrypted; use encrypted company storage and access controls. Preserve `.env`, Caddy’s CA state, and any Android signing key separately. Do not send these secrets to third parties.
4. Restart the application.

The `--server-stopped` flag is an operator assertion, not automatic process detection. Do not use it while the application is receiving writes.

## Restore safely

1. Stop the application.
2. Restore into a new empty directory:

   ```powershell
   .\.venv\Scripts\python.exe scripts/backup.py restore backups\kelun-2026-10-01.zip C:\KelunRestoredData
   ```

3. The command validates manifest hashes and paths, checks the restored SQLite database, and revokes all restored sessions.
4. Set `DATA_DIR=C:/KelunRestoredData` in `.env`, then restart the same compatible application version. Users sign in again with their existing individual passwords.
5. Verify a known task, its timeline, an original attachment, a thumbnail, a schedule, and a finalized report. Check the restore with your team before replacing your backup rotation.

The automated restore test verifies task recovery, attachment bytes and thumbnails, session revocation, and refusal to overwrite non-empty directories. Restoring a real company backup still needs a periodic user acceptance exercise.

## Docker

Stop the app before making a consistent archive:

```sh
docker compose stop app
docker compose run --rm --no-deps app python scripts/backup.py create /data/backup-2026-10-01.zip --server-stopped
docker compose cp app:/data/backup-2026-10-01.zip ./backups/backup-2026-10-01.zip
docker compose start app
```

Create the local `backups` folder before copying. Never use `docker compose down -v` for a routine update. To restore, use a new volume or directory and the same restore command; do not write over an in-use database. Docker commands have not been exercised on this host.

## Retention and archival

Set the department’s retention review age under **Settings**, or leave it blank. Review eligible completed/cancelled tasks with:

```powershell
.\.venv\Scripts\python.exe scripts/manage.py retention-review
```

The command only lists candidates. Managers archive records in the application with a reason. Task history remains append-only, attachments are retained, and archived tasks remain available through the archive view and exports. Ordinary users cannot delete history. Administrators with direct filesystem/database access can alter files, so protect and back up the server; the system is not a tamper-proof regulatory archive.
