# October 2 update: minimal interface and responsibility-aware AI

Current navigation: Overview, Work, Reports and Manage (members: Overview, Work and More). The new workbook supplies background knowledge: 43 jobs and 6 reviews. New tasks/notes/photos queue analysis when a provider is configured. Members may confirm category/related work; managers may also confirm priority and ownership. Advanced fields, filters, history and additional registers are collapsed. This update supersedes older navigation and manual-only analysis descriptions below.

Validation: 23 backend tests, desktop/mobile browser workflow, five JavaScript syntax checks and six Android Java syntax checks. AI responses in tests are controlled fixtures. Real-model accuracy and Android compilation/device behavior remain unverified.

# Feature completion checklist

Status key: **Tested** = implemented with the specified automated or browser coverage; **Implemented** = source/interface exists but this particular behavior has not been exercised end to end; **Blocked** = external tool/device/service prevents validation; **Optional** = deliberately not included. Tests apply to local development fixtures, not your production environment.

## 1. Working approach and delivery

- **Tested:** empty workspace inspected; actual persistent application created; workbook reference read without executing embedded instructions; no simulated production records.
- **Implemented:** organized backend/web/Android/deployment/docs; maintainable local stack; version locks; official documentation references; free core operation without mandatory cloud, analytics or subscription.
- **Implemented:** this checklist, test results, complete source, beginner guides, source bundle, extension guide, user acceptance checklist.
- **Blocked:** a successfully built APK and device-tested mobile application; JDK 17, Android SDK and a test device/emulator are unavailable here.

## 2. Hosting and shared architecture

- **Tested:** shared authenticated API, persistent users/tasks/updates/reviews/registers/reports, original attachment storage, SQLite schema initialization and restart persistence.
- **Tested:** live dashboard changes through server events after member upload/submission; browser clients use the same database/API.
- **Implemented:** automatic event-stream reconnect and refresh, Android configurable URL, native authenticated API, encrypted draft/cache storage.
- **Implemented:** core application has no internet dependency after installation; environment configuration, `.env.example`, numbered migrations, safe-upgrade instructions, health endpoint and one-command local start.
- **Tested:** backup/restore recovers records and referenced original/thumbnail files; restored sessions are revoked.
- **Implemented, untested deployment:** Windows/Linux launchers, Docker/Compose, Linux service and Caddy local-HTTPS examples; internal-PC/phone connection and VPN guidance. No public access was enabled.
- **Optional:** no installable PWA; native Android source is supplied as requested.

## 3. Users and permissions

- **Tested:** Isuru manager and Pasan/Wathsala/Thilakshana member accounts; first-run setup; unique passwords required to activate members; no known defaults.
- **Tested:** Argon2id hashes, opaque revocable sessions, login throttling, backend role/ownership checks, unauthorized cross-member task edits and settings denied.
- **Implemented:** adding/editing/disabling users, session revocation on account edits, protection against removing the last active manager.
- **Tested:** assignment to a member, acknowledgement, progress, supporting-member updates, unplanned work, blockers/help requests, evidence submission and review.
- **Implemented:** manager self-assignment, all-department visibility, reassignment, deadlines/priority/checklist/evidence, responsibility/schedule/settings/equipment/category/template management, history and workload views.
- **Tested:** manager approves/returns/reopens; members cannot approve or silently edit submitted/approved work. Cancellation and archive transitions are implemented.

## 4. Responsibility mapping

- **Tested:** 51 editable templates seeded, covering all supplied responsibilities for all four people; named defaults can be edited/reassigned.
- **Implemented:** Pasan’s clock/equipment time checks, three access-management areas, purchases/checks, vendors, CCTV/network/access-control/access-points/clocks/eQMS/PABX.
- **Implemented:** Wathsala’s SOP review, monthly audit trails, risk/change/deviation/CAPA documents, ERP documentation.
- **Implemented:** Thilakshana’s assets, ERP uploads, monthly waste/periodic/printer checks, daily server-room readings, weekly backup collection, printer/vendor/CCTV/network/telephone/HRIS support.
- **Implemented:** Isuru’s manual/Veeam/archive/restoration backups, maintenance coordination, purchasing, vendors/CCTV/network/server/security/BMS/SOP/roster responsibilities and all listed reviews.
- **Implemented:** only supplied frequency labels are seeded. Start dates, weekdays for general weekly work and due times require manager configuration. Monthly/daily/weekly/Tue-Fri defaults are visible. No unknown frequency is silently made active.
- **Implemented:** “weekly × 4” maintenance note is preserved and flagged; its schedule remains unconfigured. One owner plus optional supporters prevents multiple owners on one task. Responsibility ownership does not restrict reassignment.

## 5. Tasks and activity recording

- **Tested:** unique task numbers; title/description/category/department/location/equipment, owner/supporters, creator/assigner, created/due/work dates, priority/status persisted.
- **Implemented:** all four priorities, all seven statuses; overdue is calculated separately; impact/complexity context, checklist, evidence, notes/comments, blockers, completion summary, test results and review history.
- **Implemented:** vendor/purchase/project links, parent/subtask links and repeated/related-issue links; validation of linked records.
- **Tested:** assignment acknowledgement, reassignment and corrections retain history, submissions and approvals have separate timestamps, stale versions produce conflicts, retries do not duplicate updates.
- **Implemented:** start/finish timestamps and optional effort; due/date/member/category/location/equipment/status/priority filters; fast text search; saved web drafts.
- **Implemented, device untested:** native quick entry, incomplete drafts, cached assignments, pending sync, photos and offline recording.

## 6. Recurring work

- **Tested:** separate occurrences, unique schedule/day keys, restart deduplication and outage catch-up; selected weekdays and month-end date matching.
- **Implemented:** daily, weekly, monthly and selected-weekday schedules; start/due time/pause/owner edits; Asia/Colombo default and configurable timezone; historical occurrences retained.
- **Implemented:** paused schedules catch up on resume; scheduler scans at most 400 days per schedule per pass, repeating every 10 seconds; missed work stays incomplete and overdue.
- **Tested:** N/A requires a reason and goes to review. Purchase checks include the explicit “No purchase requests this cycle” action.
- **Tested:** historical reports label backfilled missed occurrences and exclude later completion from that past period.

## 7. Review and evidence

- **Tested:** submission separate from approval; return reason required; approved records locked until reasoned reopening; previous approved content remains in timeline snapshots.
- **Implemented:** review defaults for specifically listed responsibilities; configurable review requirement on schedules/tasks; attachments can include signed company documents.
- **Implemented:** authenticated actor and timestamps for review events; no qualified-signature or regulatory-compliance claim.

## 8. Photos, documents and live updates

- **Tested:** authorized image upload and authenticated original/thumbnail download, unauthorized download denial, size/type validation, bad image rejection and idempotent repeated upload.
- **Implemented:** multiple before/after/evidence images, captions, preview/remove/retry UI; uploading/uploaded/failed/pending states; originals, hashes, server upload time, optional work time, unverified photo metadata, task/version association.
- **Implemented:** PDF, XLSX, DOCX, UTF-8 text and CSV uploads; macro-enabled Office files rejected; safe download disposition and generated storage filenames. These additional file types need a representative company-file acceptance check.
- **Tested:** manager browser refreshes after the server receives member changes. AI-disabled uploads work normally.
- **Implemented, device untested:** native camera, gallery, document selection, previews and upload retry.

## 9. Offline Android

- **Implemented, device untested:** Keystore-encrypted session/drafts/photos/cache; atomic draft writes; local restart persistence; pending sync; connectivity/manual polling; idempotent stages and stable per-photo keys.
- **Implemented, device untested:** conflict preservation with current-server comparison and explicit reviewed correction; no blind version overwrite; server/account isolation for pending work.
- **Implemented, device untested:** sign-out warns about unsynced work; explicit discard; connected session revocation; account expiry/re-login behavior documented. Dashboard updates only after synchronization.
- **Blocked validation:** offline/restart/network interruption tests on an installed native app and secure storage behavior require a successful Android build and device.

## 10. AI assistant

- **Tested with fixture:** provider adapter invocation, durable queued/processing/ready state, provider/model/duration, original task unchanged until explicit acceptance, manager-only acceptance and preserved history.
- **Tested:** unconfigured AI returns unavailable; normal work/reporting remains usable.
- **Implemented:** local Ollama and explicitly opted-in HTTPS external provider interface; image+notes analysis, title/description/action/category/owner/priority suggestions, rationale/missing details/next actions/report summary.
- **Implemented:** authorized related-equipment/issue context for repeated faults; period report snapshots for ongoing/overdue/blocker context; observations separated from assumptions by provider instruction; no invented-success claims in application output.
- **Implemented:** original snapshots, labelled suggestions, limited accepted fields, no autonomous assign/approve/close/delete/permission actions, stale-source rejection, retryable failures and permission rechecks.
- **Implemented:** untrusted evidence instruction, no tool access for model, explicit external transmission setting, secrets outside source control, no fabricated analysis when no model exists.
- **Blocked validation:** real local/external vision model quality and performance; no provider credentials/model/hardware were configured. Acceptance and costs/limits are documented.

## 11. Manager dashboard and member views

- **Tested in browser:** responsive manager/member dashboard, today/overdue/review/high-priority counts, task lists, recent progress/photos, account/inbox controls, mobile-width layout.
- **Implemented:** waiting reasons, upcoming schedules, missing/overdue routine tasks, team workload with complexity/blockers, project task progress and AI suggestions ready for review.
- **Implemented:** list, board and due-date calendar, all requested filter dimensions; empty/error/offline/loading states and reconnect indicator.
- **Implemented, device untested:** native today/overdue/new/returned counts, record-work action and draft/upload queue. Counts are not employee rankings.

## 12. Reports

- **Tested:** custom/weekly/monthly date ranges through inclusive dates, one row per task, earlier work with current updates, historical state reconstruction, submission vs approval distinction, source snapshot versions and links.
- **Implemented:** completed/awaiting-review/ongoing/blocked/routine/priority/next-plan/member-contribution/management-decision sections; professional editable summary and No. / Work Scope / Activity / Status table.
- **Tested:** factual generation without AI, draft edits/version history, finalization and immutable snapshot despite later task changes, Excel download and CSV record export.
- **Tested in Chrome:** printable report saved as PDF; final PDF text and page count inspected. PDF export uses browser **Print / Save as PDF**, not a server PDF engine. Very large reports still need a company acceptance check.
- **Implemented, real-model untested:** AI report wording draft, human-reviewed acceptance.

## 13. Equipment and operational registers

- **Tested in browser:** equipment creation with asset ID/name/type/owner; backend unique-asset validation.
- **Implemented:** department/location/serial/notes; linked tasks provide fault/maintenance/evidence history; repeated issues can link to the same asset or related task.
- **Optional:** QR code generation is not included. Equipment identifiers and task links work without QR codes.
- **Implemented:** backup systems/dates/media/missing items/handing person, separate manager receipt and verification, linked-task documents. No large backup-file storage requirement.
- **Tested:** members cannot invent receipt acknowledgement; temperature/RH numbers and configured-limit flags validated; impossible RH values rejected.
- **Implemented:** reading date/units/follow-up/manager review and limit snapshots; no invented acceptable limits.
- **Implemented:** purchase reference/description/requester/items/cost/currency/owner/linked evidence, all requested workflow states plus returned/cancelled; manager controls progression and submitted-request corrections.
- **Implemented:** vendor contact/task/equipment/ticket/last-contact/promised-response/next-follow-up/outcome records.
- **Limits:** purchase items and milestones use editable text lists, not full procurement or project-accounting engines. Attach register evidence through its linked task.

## 14. Further management

- **Implemented:** projects/milestones, preventive-maintenance templates, roster/date records, leave requests/manager decisions, handover notes/covering person, searchable knowledge articles linked to resolved work.
- **Tested:** supporting-member task updates and private leave visibility; other register workflows need team acceptance with company examples.
- **Implemented:** assignment/deadline/overdue/correction/review notifications in-app with read state, deduplicated deadline notices, Android periodic polling/local notifications.
- **Blocked device validation:** actual Android notifications/background behavior. No reliable closed-app push is promised. No email or third-party messaging is configured.

## 15. Security and reliability

- **Tested:** backend authorization, ownership, Argon2id, session revocation, login failure throttling, structured validation errors, stale-write rejection, CSRF/origin rejection, authenticated attachments and immutable history triggers.
- **Implemented:** host validation, HttpOnly/SameSite cookies, optional Secure cookies for HTTPS, content security policy, MIME sniffing protection, frame denial, sanitized filenames, request/upload limits, secret-free event history, minimal operational logs.
- **Tested:** health, durable transactions, duplicate prevention, restored data/files and session reset.
- **Implemented:** retention review setting/command, deliberate soft archive, no automatic history destruction; deployment/security guidance and no compliance claims.
- **Limits:** SQLite/filesystem administrators can alter underlying files; backups are not encrypted ZIPs; host access controls and company backup storage protections are required. This is not a certified or externally penetration-tested product.

## 16. Design

- **Tested visually:** “Kelun IT Work Manager” text identity, responsive web layout, readable status/priority badges, large controls, contrast, empty/error/connection feedback and search.
- **Implemented:** native large-control forms and draft states; no invented official logo.
- **Tested:** fixture records labelled TEST ONLY and stored outside production data.

## 17–18. Acceptance and delivery

- See `TEST-RESULTS.md` for exact run results and acceptance-test mapping.
- See `ACCEPTANCE.md` for each team member’s checks.
- Source, migrations, editable seeds, deployment files, environment example, installation/network/AI/backup/extension guides are included.
- Runnable local application, company deployment and device-tested Android are explicitly distinguished. Native build/device tests, real-model validation, and company-network rollout remain external completion steps.
