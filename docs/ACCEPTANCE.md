# October 2 update: minimal interface and responsibility-aware AI

Current navigation: Overview, Work, Reports and Manage (members: Overview, Work and More). The new workbook supplies background knowledge: 43 jobs and 6 reviews. New tasks/notes/photos queue analysis when a provider is configured. Members may confirm category/related work; managers may also confirm priority and ownership. Advanced fields, filters, history and additional registers are collapsed. This update supersedes older navigation and manual-only analysis descriptions below.

Validation: 23 backend tests, desktop/mobile browser workflow, five JavaScript syntax checks and six Android Java syntax checks. AI responses in tests are controlled fixtures. Real-model accuracy and Android compilation/device behavior remain unverified.

# Team acceptance checklist

Use a separate test data directory first. Record the date, tester, device/browser and result for each item. All four people should use their own accounts.

## Isuru

- [ ] Finish first-run setup and activate Pasan, Wathsala and Thilakshana with unique passwords.
- [ ] Create a task with a deadline, priority, checklist, required evidence and supporting member.
- [ ] Keep the dashboard open while the member uploads a photo; confirm the view updates without a page reload.
- [ ] Return a submission with a reason, then approve the corrected version. Confirm both submissions and approval timestamps remain in the timeline.
- [ ] Reopen the approved task with a correction reason. Confirm the previous approved content remains in history.
- [ ] Reassign a task and change its deadline. Confirm old assignment/deadline details remain visible in history.
- [ ] Set a daily test schedule, restart the server, and confirm there is only one task for each occurrence.
- [ ] Check catch-up after an outage, pauses/resume, a month-end occurrence, and Tuesday/Friday purchase checks.
- [ ] Confirm “weekly × 4” maintenance remains unconfigured until you decide its meaning.
- [ ] Configure temperature/RH limits according to your department’s procedure, then confirm a test out-of-range reading is flagged.
- [ ] Acknowledge a backup handover separately from recording the verification outcome.
- [ ] Generate a report covering work that began earlier but received updates this week. Check unique tasks, approval states and source links.
- [ ] Edit and finalize the report; change a source task afterward and confirm the finalized report stays unchanged. Download Excel and print to PDF.
- [ ] Create and review a purchase, leave request, roster item, handover, project, maintenance template and knowledge article.
- [ ] Disable a test account and confirm its active session loses access.
- [ ] Back up, restore into a new empty folder, and verify a task, original photo, timeline and report.

## Pasan

- [ ] Sign in and see your assignment. Confirm Wathsala’s unrelated assignment is unavailable.
- [ ] Acknowledge it, add progress, record a blocker/help request, and complete its checklist.
- [ ] Attach Before/After photos with captions plus a signed document if required.
- [ ] Submit for review, respond to a returned item, and check the manager’s approval.
- [ ] Record an unplanned issue and link a repeated fault to the earlier task/equipment.
- [ ] For a purchase-check occurrence, submit “No purchase requests this cycle” when appropriate and verify manager review.

## Wathsala

- [ ] Update a task shared with you as a supporting member.
- [ ] Confirm you cannot change assignments, another person’s unrelated task, or manager settings.
- [ ] Create a documentation task and attach PDF/Office evidence; verify only authorized users can download it.
- [ ] Submit a leave request and check that another member cannot read the private request.
- [ ] Inspect a report’s source task and distinguish submission from manager verification.

## Thilakshana

- [ ] Record actual temperature/RH readings with follow-up, then have Isuru review them.
- [ ] Create a backup handover including systems, dates, media references and missing items. Confirm receipt and verification are separate.
- [ ] Link a fault to an equipment record and view its repeated-fault history.
- [ ] Record printer/vendor follow-up and link its task evidence.

## All Android users — blocked until APK/device preparation

- [ ] Build and install the native app using `ANDROID.md`; record the APK build version and phone model.
- [ ] Connect over trusted local HTTPS and sign in.
- [ ] Take a camera photo, select gallery images and a document, add captions, preview and remove an unneeded photo.
- [ ] Turn off connectivity. Save an incomplete draft and another complete activity with photos. Restart the app and confirm both remain.
- [ ] Reconnect and sync twice; confirm one task/update/upload per queued operation.
- [ ] Change the same task on the web while the phone is offline; verify the conflict does not overwrite either version silently.
- [ ] Test failed uploads and retries, expired sessions, account disablement and task reassignment.
- [ ] Test notification permission and background delays; understand that closed-app push is not guaranteed.
- [ ] Attempt sign-out with unsynced work and verify the explicit keep/discard behavior.

## Optional AI trial — untested with a real model

- [ ] Configure an approved local model or explicitly approved external provider.
- [ ] Run a photo job and verify provider/model/time/status are recorded.
- [ ] Compare observations, assumptions, missing details and priority reasoning with actual evidence.
- [ ] Confirm no suggestion changes the task until a manager accepts an allowed field.
- [ ] Change the source before accepting and confirm stale acceptance is rejected.
- [ ] Disable AI and confirm normal tracking, uploads and factual reports still work.
