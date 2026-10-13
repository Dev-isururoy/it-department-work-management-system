# Kelun IT Work Manager

Operational work tracking for **Kelun Life Sciences (Pvt) Ltd.**

## Start here

From PowerShell in this folder:

```powershell
.\start.ps1
```

Then open [http://127.0.0.1:8000](http://127.0.0.1:8000). Use the private setup key printed by the launcher to create Isuru’s account. Activate Pasan, Wathsala and Thilakshana under **People & accounts**, each with a unique password. No default passwords or production sample tasks are shipped.

After installation, `./start-local.ps1` starts the server quietly and `./stop-local.ps1` stops that background process. The standard `start.ps1` runs in the foreground.

On this development computer, dependencies are already installed. To start directly:

```powershell
.\.venv\Scripts\python.exe scripts/manage.py setup-key
.\.venv\Scripts\python.exe -m backend.run
```

**Current delivery:** web and backend implemented and tested locally; native Android source delivered, with APK compilation blocked by missing JDK 17/Android SDK; real-model AI, company HTTPS, LAN phones, and Android device behavior remain untested. Read the feature checklist and test report before operational rollout.

## Included

- Persistent task assignment, individual accounts, server-side permissions, progress, evidence, checklists, blockers, reviews, corrections and change history.
- Minimal Overview / Work / Reports / Manage navigation, simple work entry, live refresh and list/board/calendar. Additional registers are under Manage.
- 51 editable responsibility defaults; configurable recurring schedules with deduplicated occurrences and outage catch-up.
- Factual reports with source links, editable versions, finalized snapshots, printable PDF through the browser, Excel and CSV exports.
- Automatic responsibility-aware analysis after tasks, notes and photos, using 43 jobs and 6 manager reviews from the new workbook. People confirm suggested categories, assignments, priority and related work. A real model still needs connecting.
- Native Android source with encrypted drafts, camera/gallery/documents, offline queue, conflict review and best-effort notification polling.
- Portable Python deployment, optional Docker configuration, migrations, backup/restore scripts, HTTPS guidance and a team acceptance checklist.

## Guides

| Guide | Purpose |
|---|---|
| [Installation](docs/INSTALLATION.md) | Windows/Linux/Docker, first run, start/stop/update |
| [Phone connection & HTTPS](docs/NETWORK-HTTPS.md) | Internal DNS, local certificates, firewall, VPN, connectivity |
| [Android build & limits](docs/ANDROID.md) | Exact build steps and device validation |
| [AI setup](docs/AI.md) | Optional providers, hardware, data handling and acceptance |
| [Backup & restore](docs/BACKUP.md) | Consistent backups, safe restore, archival |
| [Feature completion](docs/FEATURE-CHECKLIST.md) | Requested scope, implementation and limitations |
| [Test results](docs/TEST-RESULTS.md) | What passed and what remains unverified |
| [Team acceptance](docs/ACCEPTANCE.md) | Checks for Isuru, Pasan, Wathsala and Thilakshana |
| [Extension guide](docs/EXTENDING.md) | Architecture, modules, migrations and tests |

## Architecture

Python/FastAPI serves the web interface and authenticated API. SQLite stores records and immutable history snapshots; original files are retained on disk with authenticated downloads and thumbnails. One application process runs recurrence and AI jobs. Browser files have no build step or CDN dependency. The native Android application uses the same API.

The supplied workbook was read as reference data. The pasted request governs implementation. Ambiguous maintenance frequency “weekly × 4” remains unconfigured. No schedules or reading limits are presented as regulatory requirements. In-app review events are not qualified electronic signatures or a claim of pharmaceutical regulatory compliance.
