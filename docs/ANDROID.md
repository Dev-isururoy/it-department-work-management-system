# Native Android application

## Status

The `android/` folder is a native Java Android application, not a mobile website wrapper. It contains camera/gallery/document selection, authenticated networking, Keystore encryption, persistent drafts, an idempotent sync queue, conflict review, and network-constrained background polling.

**No APK was built successfully on the delivery computer. No emulator or physical device was available.** Six Java sources passed syntax parsing. This establishes parseable source only; it does not establish successful compilation, Android API correctness, camera behavior, encryption behavior, or offline operation on a device.

Build attempts:

- The Gradle 8.11.1 wrapper downloaded its distribution with the pinned SHA-256 checksum and ran `--version` successfully.
- `:app:assembleDebug --no-daemon` failed because the installed 32-bit Java 8 runtime could not reserve the 2 GB heap.
- A diagnostic retry with a 512 MB heap reached dependency resolution and failed because the Android plugin requires a newer JVM. The plugin’s documented toolchain is JDK 17. No Android SDK, build tools, `adb`, emulator, or JDK compiler was detected.

## Exact build steps on a prepared Windows computer

1. Install [Android Studio](https://developer.android.com/studio). In SDK Manager install **Android SDK Platform 35**, **Build-Tools 35.0.0**, and **Android SDK Platform-Tools**. Install an emulator image if testing without a phone.
2. Open the `android` folder as the Android Studio project. Set **Gradle JDK** to a 64-bit JDK 17 (or a compatible Android Studio bundled JDK). The project pins Android Gradle Plugin **8.9.2** and Gradle **8.11.1**.
3. Let Android Studio create `local.properties` pointing to the installed SDK. For command-line use, the file has the form:

   ```properties
   sdk.dir=C\:\\Users\\YOUR_USER\\AppData\\Local\\Android\\Sdk
   ```

4. Open a terminal with JDK 17 configured as `JAVA_HOME` and its `bin` directory on PATH. Verify `java -version` and `javac -version` both report the chosen JDK.
5. From the `android` folder:

   ```powershell
   .\gradlew.bat :app:assembleDebug :app:lintDebug --no-daemon
   ```

6. Only after a successful build, the test APK is at `android/app/build/outputs/apk/debug/app-debug.apk`.
7. Connect an authorized test phone with USB debugging enabled, then run:

   ```powershell
   adb devices
   adb install -r app\build\outputs\apk\debug\app-debug.apk
   ```

The first build needs internet to download Gradle, the Android plugin, and SDK components. Gradle’s wrapper is included, including its binary JAR and distribution checksum. No JavaScript bridge or cloud mobile framework is required.

For release distribution, build a signed release APK with your company’s signing key in Android Studio. Keep that key outside source control and back it up. Release builds require HTTPS. Do not distribute a debug APK as the final company release.

The toolchain choice follows [Android’s AGP 8.9 compatibility table](https://developer.android.com/build/releases/agp-8-9-0-release-notes) and [JDK guidance](https://developer.android.com/build/jdks).

## Use

1. Open the app and enter the company server URL, username, and individual password.
2. Tap **Sync now** to retrieve assignments. The home page shows cached work and counts for today, overdue work, new assignments, and returned work.
3. Open an assignment to acknowledge it or record progress. Use **Record work** for unplanned activity.
4. Enter title, location/equipment, issue, action, status, and optional completion/test details. Checklist items from assigned work are available.
5. Take multiple photos or select gallery images/documents. Add captions and Before/After/Evidence labels. Preview or remove local images before queueing.
6. **Save draft** allows incomplete fields. **Save & queue synchronization** requires title and action taken. Drafts and photos are stored in the app’s private directory; content and the session token are encrypted with an Android Keystore AES-GCM key.
7. Queued work persists across process restarts. Stable retry keys cover creation, progress, each attachment, and submission. Stale versions stop with **Conflict**. Load the current server record, compare it with your notes, and prepare a reviewed correction. Completed/submitted/cancelled server records must first be returned or reopened where appropriate.
8. Submit only after actual work and results have been recorded. Manager review occurs in the web interface.

## Connectivity, notifications, and logout

- Offline drafts do not update the web dashboard until successfully synced.
- Manual sync and foreground home polling are implemented. The background JobScheduler requests 15-minute execution while network is available. This is best-effort polling, not guaranteed push. A force-stopped app will not receive updates until opened again; reboot and vendor battery policies can also delay it.
- Android 13+ requires notification permission. Denying it does not prevent tracking and sync.
- Sign-out warns about pending work and offers keeping the account or explicitly discarding local drafts. Session revocation currently requires a connection. Failed sign-out preserves local data. A session expires after 12 hours; sign in with the same server/account to resume saved work.
- Switching server/account is blocked while drafts from another account/server remain. Remove synced local copies or resolve/discard pending work first.
- Device storage encryption, screen lock, and company mobile-device policies still apply. App backup is disabled; uninstalling or clearing app data destroys unsynced local drafts.

## Device acceptance: still required

- Build and lint successfully; install on your actual phone models.
- Take and select several images, rotate the screen, leave the app during camera capture, and verify captions and files remain attached to the correct draft.
- Disable Wi-Fi, save incomplete and complete drafts, force-stop/reopen, then reconnect. Confirm no lost drafts or duplicate tasks/photos.
- Interrupt connectivity during each sync stage. Retry after a lost response. Confirm idempotency on the server.
- Edit the same task on the web during offline mobile work. Confirm the app preserves the local copy and requires conflict review.
- Test TLS using the company CA; reject an untrusted or mismatched certificate.
- Deny notification permission and exercise Doze/background limits. Test sign-out with pending work and expired sessions.
- Check large images, insufficient storage, session expiry, a disabled account, and reassignment while offline.

These checks are intentionally unmarked until performed on a real build/device.
