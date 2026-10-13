# Install and run Kelun IT Work Manager

## What is delivered

The web application and shared API run on one company computer. SQLite stores records; original attachments live beside it. The native Android project connects to the same API. Core tracking needs no internet after dependencies are installed.

This delivery is a runnable local application. It is not yet a company-wide deployment. The Android APK build is blocked on this computer: it has a 32-bit Java 8 runtime, no detected JDK 17, and no Android SDK/device. See `ANDROID.md` for the build and device acceptance steps.

## Hardware and software

- Practical starting point for four users: a supported 64-bit Windows or Linux machine, 2 CPU cores, 4 GB RAM, and an SSD. These are planning estimates, not measured capacity guarantees.
- Python 3.12 or later. The tested interpreter is Python 3.12 on Windows.
- Allow disk space for original photos, documents, logs, and several backup copies. File uploads default to 20 MB each; decoded images are limited to 25 megapixels.
- Chrome, Edge, or another modern browser. No Node.js installation is needed to run the web application.
- Keep the server awake during working hours. SQLite and its files must be on a local disk, not a network share.
- AI is optional and has separate hardware requirements.

## Windows: first start

1. Keep the project together in a folder such as `C:\IT Department work management system`.
2. Install 64-bit Python from [python.org](https://www.python.org/downloads/windows/) if needed. Include it in PATH.
3. Open PowerShell in the project folder and run:

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\start.ps1
   ```

   The first run creates a virtual environment, installs locked dependencies, copies `.env.example` to `.env`, and prints a private first-run setup key. Internet is needed for the initial dependency download.

   On the current development computer, the virtual environment already exists. You can start without downloading again:

   ```powershell
   .\.venv\Scripts\python.exe scripts/manage.py setup-key
   .\.venv\Scripts\python.exe -m backend.run
   ```

   If Python is installed outside PATH, pass its full path: `./start.ps1 -Python 'C:\path\to\python.exe'`.

4. Open [the local application](http://127.0.0.1:8000). Enter the setup key, choose Isuru’s username, and set a unique password with at least 12 characters.
5. Sign in. Open **People & accounts**. Set distinct passwords for Pasan, Wathsala, and Thilakshana, and activate their accounts. They have no initial passwords and cannot sign in until activated. Share each password privately.
6. Test one assignment before adding real records. Test fixtures from automated checks are stored separately under `test-results/`, not in the production data directory.

The setup key is stored in `data/.setup-key`; it only authorizes the initial setup. Protect this folder with Windows permissions. After setup, the endpoint refuses further setup requests. No known manager password is shipped.

## Start, stop, and restart

- Start: `./start.ps1`, or `./.venv/Scripts/python.exe -m backend.run` after installation.
- Stop: press **Ctrl+C** in the server terminal. Wait for shutdown before copying files or restoring backups.
- Restart: run the same start command. Data remains on disk.
- Optional quiet Windows launch after installation: `./start-local.ps1`. It prints the first-run setup key and starts a hidden local process. Stop that process with `./stop-local.ps1`. The quiet launcher writes operational logs to `data/local-server-error.log` and records its own process ID; the stop script checks the process identity before stopping it. Prefer the foreground launcher or a managed service for graceful routine shutdown.
- Check health: open [health status](http://127.0.0.1:8000/api/health).
- Check the database: `./.venv/Scripts/python.exe scripts/manage.py check`.

Run one application process. Its background loop checks recurring schedules, notifications, and optional AI jobs. The web dashboard uses a reconnecting server event stream and refreshes after server changes. Uploading while offline cannot update the dashboard until synchronization succeeds.

## Linux

```sh
sh start.sh
```

For an operating-system service, use the sample `deployment/kelun.service`, adjust the paths and user, and enable it through the host’s normal service management process. Keep the data directory writable only by the service account and authorized administrators.

## Docker option

With Docker Engine and Compose installed:

```sh
docker compose up --build -d
docker compose exec app python scripts/manage.py setup-key
```

Open the local application and finish setup. Stop with `docker compose stop`; restart with `docker compose start`. Persistent data is in the named `kelun-data` volume. Do not remove that volume when updating. Docker deployment files are supplied but were not executed here because Docker is unavailable on this computer.

## Safe updates

1. Stop the server and create a verified backup as described in `BACKUP.md`.
2. Keep a copy of the previous source release. Preserve `.env`, the data directory, local CA certificates, and any Android signing key.
3. Replace application source files and install `requirements-lock.txt` into the virtual environment.
4. Start the new version. Numbered database migrations run once, with their applied versions recorded in SQLite.
5. Check `/api/health`, sign in, open a task and an attachment, and test a member update.
6. If an update fails, stop it. Restore the old source and restore the matching database-and-files backup into a new empty data directory. Point `DATA_DIR` to that directory. Do not try to run old source on a newly migrated database without verifying compatibility.

Migrations should be reviewed and tested against a backup before future production upgrades. The initial migration is idempotent. Future migration authors must use safe transaction boundaries; see `EXTENDING.md`.

## Offline installation

On a connected computer with the same Python/platform, prepare a wheel folder:

```powershell
python -m pip download -r requirements-lock.txt -d wheels
```

Transfer source, Python’s installer, and the wheel folder to the local server. Install with `./.venv/Scripts/python.exe -m pip install --no-index --find-links wheels -r requirements-lock.txt`. Start using `python -m backend.run` so the launcher does not attempt online installation.

## Configuration

Copy `.env.example` to `.env`. Restart after changing environment settings. Use an absolute `DATA_DIR` for a service. The initial business timezone is Asia/Colombo and can be changed under **Settings**. Thresholds remain empty until your department configures them. Retention is a review age; it never deletes records automatically.

Server logs contain startup/shutdown and error class information. Access logging is disabled to avoid leaking URL/session context. The database contains a separate append-only activity history. Backups contain sensitive company data; control their access.
