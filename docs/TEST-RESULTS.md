# October 2 update: minimal interface and responsibility-aware AI

Current navigation: Overview, Work, Reports and Manage (members: Overview, Work and More). The new workbook supplies background knowledge: 43 jobs and 6 reviews. New tasks/notes/photos queue analysis when a provider is configured. Members may confirm category/related work; managers may also confirm priority and ownership. Advanced fields, filters, history and additional registers are collapsed. This update supersedes older navigation and manual-only analysis descriptions below.

Validation: 23 backend tests, desktop/mobile browser workflow, five JavaScript syntax checks and six Android Java syntax checks. AI responses in tests are controlled fixtures. Real-model accuracy and Android compilation/device behavior remain unverified.

# Test results and known limitations

Delivery verification date: **1 October 2026**, Asia/Colombo.

## Summary

| Check | Result | Scope |
|---|---|---|
| Persistent backend suite | **15 passed** | SQLite-backed API workflows and security/reliability cases |
| Real Chrome workflow | **Passed** | Separate manager/member browser sessions against a real isolated server |
| Frontend JavaScript parsing | **4 modules passed** | Browser modules parsed; browser run reported no uncaught exceptions |
| Native Android source syntax | **6 Java files passed** | Syntax parsing only, not Android compilation |
| Gradle wrapper | **Passed** | Pinned Gradle 8.11.1 download/checksum and `--version` |
| Android APK build | **Blocked / failed** | Host only has 32-bit Java 8; no JDK 17 or Android SDK detected |
| Android device/emulator tests | **Not run** | No built APK, emulator, or connected device |
| Real AI provider/model | **Not run** | No local model or external provider configured |
| Docker deployment | **Not run** | Docker unavailable on this host |
| Company LAN / HTTPS / VPN | **Not run** | Internal DNS, certificates, firewall policy and phones not supplied/configured |

The pytest run emits one upstream Starlette/httpx test-client deprecation warning. It does not fail the tests. No production data or user passwords were used. Browser fixtures are clearly labelled TEST ONLY and stored in separate directories under `test-results/`.

## Backend cases

1. First-run setup is required, is protected by a random server key, and cannot be repeated. Four named accounts and 51 responsibility templates exist. Passwords are Argon2id hashes.
2. Isuru assigns a task to Pasan; Wathsala cannot read/update it or modify manager settings. Pasan acknowledges it, records progress, completes its checklist and uploads an actual PNG.
3. Repeated upload requests with one key return the same attachment. Original bytes and thumbnail download succeed for an authorized user; an unrelated/unauthenticated user is denied.
4. Submission requires completion/evidence, separates member reporting from approval, and locks progress. Isuru returns, later approves, reopens and reassigns; historical approved snapshots are preserved. SQL history deletion fails.
5. Replayed task creation/progress returns one record/version. Reusing a key with different data fails. Stale versions produce a conflict.
6. Daily schedules catch up after a gap, create one task per occurrence across repeated runs, and preserve missed status. N/A requires a reason and review.
7. Reports include unique task rows, awaiting-review state, editable versions and finalized snapshots. Approval after finalization does not alter the snapshot. Excel and CSV endpoints produce readable data.
8. Unconfigured AI is explicitly unavailable while tracking works. Reading limits flag out-of-range values; RH outside 0–100 is rejected; a member cannot acknowledge receipt as manager.
9. Cross-origin write protection, invalid-image rejection, logout revocation, and repeated-login failure lockout are exercised.
10. Backup/restore recovers a task and exact original attachment bytes plus thumbnail, revokes restored sessions, and refuses a non-empty destination.
11. A task started before the period with meaningful progress during the period is included once. Later changes are absent from historical-period state.
12. A controlled AI response exercises provider calling and processing metadata. It leaves the task unchanged until explicit manager acceptance; member acceptance is forbidden and original content remains in history. This is a contract test, not a real-model quality test.
13. Supporting members can update shared tasks. Private leave requests are unavailable to unrelated members.
14. Unplanned member work retains manager review; invalid progress types/negative effort are rejected; records survive database initialization/restart.
15. Additional boundary coverage verifies monthly last-day behavior, selected weekdays, backfilled routine tasks in past-period reports, and member refusal when revising a purchase already submitted for manager review.

These descriptions group assertions; the automated suite contains 15 test functions, some of which cover several related assertions.

## Browser workflow

The browser runner used Chrome on Windows, a desktop viewport (1440×1000), and a mobile viewport (412×915). It:

- Completed first-run setup in the UI and activated the three member fixtures.
- Created an assignment through the manager UI.
- Signed Pasan in through a separate browser context, acknowledged the assignment, recorded progress/results, uploaded a real PNG with a caption, and submitted it.
- Kept the manager page open and confirmed it changed to **Submitted for Review** through the server event stream without reloading.
- Approved the submission as manager.
- Created, edited and finalized a factual report; generated a PDF through print rendering.
- Created an equipment record.
- Captured desktop/mobile screenshots and recorded no uncaught JavaScript exceptions.

The screenshots were visually reviewed. The generated PDF was checked for page count and expected task/approval/section text; the representative one-task finalized report occupies one A4 page. Screenshots and PDFs are test artifacts, not real company reports.

## Acceptance requirements mapping

| Requested acceptance | Evidence / remaining check |
|---|---|
| 1. Setup + four individual accounts | API tests and browser setup passed |
| 2. Correct assignment recipient | API permissions and separate member session passed |
| 3. Unauthorized edits/settings denied | API tests passed |
| 4. Member progress + photo | Real API and mobile-width browser passed |
| 5. Live dashboard update | Real event-stream browser check passed |
| 6. Submit / approve / return | API and browser checks passed |
| 7. Reassignment/correction history | API snapshot assertions passed |
| 8. Recurrence once per occurrence | API restart/catch-up checks passed |
| 9. Offline native drafts/restart/deduplication | Native source implemented; server retry/conflict contract passed; device test blocked |
| 10. AI suggestions separate until accepted | Controlled-provider contract test passed; real model untested |
| 11. AI disabled tracking | API and browser checks passed |
| 12. Correct reporting period/unique tasks/approval states | API historical/snapshot/Excel checks passed |
| 13. Authorized attachments only | API positive and negative checks passed |
| 14. Backup restores DB + files | Restore and exact-file checks passed |

## Known limits

- Native Android functionality is supplied as source and is **not yet built or device-tested**. Do not infer device behavior from Java syntax validation. Follow `ANDROID.md` and run the device acceptance checklist.
- No real vision model was run. AI service compatibility, model truthfulness, latency, memory use and external billing require an approved provider trial.
- Notifications use polling/local display. There is no implemented reliable closed-app push service. Android battery restrictions and force-stop can delay delivery.
- Web dialogs keep the version the user opened. If the server changes it, submission fails with a conflict; reopen and compare before retrying. The surrounding dashboard refreshes when the dialog closes.
- PDF export is browser printing. Representative output was checked; long reports and different printers need acceptance checks.
- Purchase items and project milestones are simple editable text lists. The optional equipment QR-code feature is not included.
- Register attachments use a linked task, preserving that task’s evidence permissions and review trail. Managers create/manage equipment; team members can record work against those assets.
- The scheduler backfills in 400-day batches. Paused schedules also catch up on resume. Review the start date before activating a historical schedule.
- SQLite is suitable for the intended small local team. Multi-server hosting, load limits and large histories have not been benchmarked. Use one application process.
- Core records work offline from the internet when clients can reach the local server. The browser is not an offline replacement for the native Android queue.
- Windows local startup was exercised. Service installation, Docker, LAN HTTPS and VPN deployment are supplied as configuration/instructions and remain untested in your company environment.
- No independent penetration test, regulatory qualification or electronic-signature certification has been performed or claimed.
