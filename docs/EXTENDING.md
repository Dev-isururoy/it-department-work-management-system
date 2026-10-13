# Architecture and extension guide

## Layout

```text
backend/                  FastAPI application, permissions, business logic
  migrations/             Numbered SQL migrations
  seeds/                   Editable responsibility seed JSON
  store.py                 SQLite transactions, records, history, notifications
  security.py              Argon2id hashing, opaque sessions, authorization helpers
  tasks.py                 Task creation, version checks, review transitions
  scheduler.py             Recurrence matching and idempotent occurrence generation
  registers.py             Typed operational-register field catalogue and controls
  reports.py               Period reconstruction, snapshots, CSV/Excel exports
  ai.py, providers.py      Durable AI jobs and optional provider adapters
web/                      Browser modules, semantic forms, responsive CSS
android/                  Native Android Gradle project
scripts/                  Setup, integrity, retention, backup/restore utilities
tests/                    Persistent API workflows and real browser checks
deployment/               Local HTTPS and Linux service examples
docs/                     Installation, acceptance, limitations, feature checklist
```

## Stack rationale

FastAPI provides one typed HTTP API for both clients. Python’s SQLite driver keeps local deployment small and portable. SQLite uses WAL mode and a write transaction around each API operation. The application serves its own browser files, so there is one origin, no frontend build server, and no CDN dependencies. Vanilla JavaScript modules and CSS reduce installation and upgrade overhead for a four-person department. Android uses native platform screens, HttpURLConnection, Keystore, AtomicFile, camera intents, the document picker, and JobScheduler.

This deliberately targets one local application process and a small team. Larger installations should measure data/query volume and migrate to a multi-process job service and server database when justified. Do not simply add application workers without reviewing scheduler and provider-job claiming semantics.

## Data model

- `users`: individual identity, role, disabled state, Argon2id hash. Passwords never enter history snapshots.
- `sessions`: SHA-256 hashes of random bearer/cookie secrets with 12-hour expiry. Logout revokes the session; account edits revoke that account’s sessions.
- `documents`: versioned JSON records by kind, with creation/update metadata and soft archival. Task fields are validated by dedicated models. Register fields are defined and validated centrally.
- `history`: append-only snapshots, actor, action, reason and timestamp. SQL triggers reject updates/deletes through ordinary application connections.
- `occurrences`: unique `(schedule_id, day)` keys preserve once-per-occurrence generation across restarts.
- `idempotency`: actor, key, method/path/body fingerprint, and saved response. A reused key with different content fails.
- `notifications`: authenticated recipient, text, timestamp, read state and optional unique dedupe key.
- `settings` and `schema_migrations`: persisted department settings and applied schema versions.

Original attachments have random server filenames; original client names are sanitized metadata. SHA-256, server upload time, optional work time, unverified EXIF timestamps, uploader, phase/caption, and task version are recorded. Small JPEG thumbnails are separate from originals. Downloads require access to the associated task.

## Permissions and review

All sensitive actions check the authenticated role on the API. Members can update only tasks they own or support. Members create their own unplanned work. Managers control assignment, deadlines, review, corrections, archive, account management and settings. Private leave records are visible to the author and managers. Shared operational registers are readable by the team; edits are restricted to authors/managers, with manager-only decisions and reviewed-record protections.

Members submit; managers approve or return. Pending submissions are locked until returned/withdrawn. Approved/cancelled records require a documented reopen before correction. Every action creates a new snapshot. This is operational review history, not a cryptographic electronic-signature system.

## Adding a register

1. Add a field catalogue in `registers.py` using the existing text, date, number, choice, user, task, equipment and checkbox controls.
2. Specify shared/private and manager controls, then add domain validation. Do not rely on disabled browser fields for permissions.
3. Add tests for authorized creation, invalid input, unauthorized changes, reviewed corrections, archival, and history.
4. The browser generates the register form and list from the catalogue. Add a custom view when the workflow becomes too complex for a simple register.

Project milestones, purchase line items, and maintenance instructions currently use structured record fields plus editable text lists. Normalize them into child-record tables when richer dependencies, financial totals, or individual milestone approvals are needed.

## Adding a migration

Add a new file such as `002_description.sql`; never edit an already deployed migration. Test it on an empty database and on a restored previous-version backup. Keep SQL idempotent where practical, use explicit transaction boundaries for multi-statement transformations, and preserve prior records. Document any irreversible change. The application records successful migration names and skips them thereafter.

## Adding an AI provider

Implement `AIProvider.analyze(system, content, images)` in `providers.py` and register it in the provider factory. Keep the adapter side-effect free. Preserve explicit external-data opt-in, permission checks, source snapshots, output validation, status tracking, human acceptance and stale-version rejection. Test the provider contract with deterministic fixtures, then test the actual configured model separately.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
node tests/check_frontend.cjs
```

For browser testing, install Playwright as a development dependency (`npm install --no-save playwright`) and its Chromium (`npx playwright install chromium`), then run:

```powershell
.\.venv\Scripts\python.exe tests/run_browser.py
```

The browser runner starts an isolated server on a free loopback port, uses a unique directory under `test-results/`, creates random test credentials, exercises the real API, and stops that server afterward. All fixture tasks are labelled TEST ONLY. If using an existing Chrome installation, set `CHROME_PATH` to its executable. `PLAYWRIGHT_MODULE` can point to an already installed Playwright package.

Optional Java syntax checks require `tree-sitter` and `tree-sitter-java` in the development environment, then `python tests/check_android_syntax.py`. This is not a substitute for Gradle compilation, lint, and device testing.

## Official references checked

- [FastAPI deployment concepts](https://fastapi.tiangolo.com/deployment/concepts/)
- [FastAPI containers](https://fastapi.tiangolo.com/deployment/docker/)
- [Android AGP 8.9 compatibility](https://developer.android.com/build/releases/agp-8-9-0-release-notes)
- [Android Keystore API](https://developer.android.com/reference/android/security/keystore/KeyGenParameterSpec)
- [Android periodic job behavior](https://developer.android.com/reference/android/app/job/JobInfo.Builder#setPeriodic(long))
- [Ollama chat API](https://docs.ollama.com/api/chat)
- [Caddy local HTTPS and service deployment](https://caddyserver.com/docs/running)

Versions are pinned in the delivered requirement files and Gradle configuration. Upgrade deliberately and rerun the relevant checks. Optional dependencies retain their upstream licenses; the included Gradle wrapper is distributed under Gradle’s Apache 2.0 license.
