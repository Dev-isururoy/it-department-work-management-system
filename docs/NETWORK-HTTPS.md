# Connect company PCs and phones

The supplied default binds only to `127.0.0.1`. Nothing was opened to your LAN or the public internet during development.

## Recommended local HTTPS deployment

1. Give the server a stable private address or DHCP reservation. Choose an internal DNS name, for example `kelun-it.local`, and make company devices resolve it to that address. Use a company DNS name if `.local` conflicts with mDNS on your network.
2. Install [Caddy](https://caddyserver.com/docs/install) on the server. Copy `deployment/Caddyfile.example` to a real `Caddyfile` and replace the hostname with your internal name.
3. Keep the API bound to loopback. Set these values in `.env`:

   ```dotenv
   HOST=127.0.0.1
   ALLOWED_HOSTS=localhost,127.0.0.1,kelun-it.local
   PUBLIC_ORIGIN=https://kelun-it.local
   COOKIE_SECURE=true
   ```

4. Start the Python application and then run `caddy run --config Caddyfile --adapter caddyfile` in Caddy’s folder. For unattended hosting, install Caddy and the application as services or scheduled tasks under dedicated accounts.
5. Caddy’s `tls internal` issues certificates from its own local CA. Install only the CA’s **root certificate**, never its private key, in the trusted certificate store on approved company PCs and Android phones. The certificate must match the server hostname. Caddy stores its CA under its data directory; consult `caddy environ` for that service account’s data location. On Windows it is usually under the account’s application-data folder; on a standard Linux service it is under `/var/lib/caddy/.local/share/caddy/pki/authorities/local/root.crt`.
6. Allow inbound TCP 443 in the server firewall for the company subnet only. Do not add a router port-forward. Check that Wi-Fi client isolation does not prevent phones reaching the server.
7. Open `https://kelun-it.local` in a PC browser and in a phone browser. Verify the certificate is trusted. In the Android app, enter the same URL in **Server settings / sign in again**.

The release Android app permits HTTPS and trusts Android’s system and user-installed CA stores. Certificate verification stays enabled. A debug build allows HTTP for development testing. Never use a debug HTTP connection for real credentials on an untrusted network.

For Windows unattended startup without extra service software, create a Task Scheduler task that runs the project’s `.venv\Scripts\python.exe` with arguments `-m backend.run`, starts in the project folder, runs under the chosen service account, triggers at startup, and restarts on failure. Confirm that this account can read `.env` and write the data directory. Keep the application independent of a user’s open terminal. This service configuration was not deployed here.

## Development phone connection

For a short test on an isolated trusted LAN, set `HOST=0.0.0.0`, add the private server IP to `ALLOWED_HOSTS`, set `PUBLIC_ORIGIN=http://PRIVATE_IP:8000`, keep `COOKIE_SECURE=false`, and allow port 8000 only from that LAN. Use the debug APK. Switch back to loopback plus HTTPS for operational deployment.

On an Android emulator on the server, the host is normally `10.0.2.2`; add it to allowed hosts for debug testing. A physical phone must use the server’s LAN address, not `127.0.0.1`.

## Remote access later

Use the company’s approved VPN so remote devices resolve and reach the same internal HTTPS name. No public forwarding, tunnel, or external messaging service is configured by this project.

## Connectivity behavior

- Web: server events reconnect automatically. Open task dialogs preserve the displayed version; stale writes produce a conflict rather than overwriting newer changes. Close and reopen the task to load the new version.
- Android: drafts and queued evidence are local until synced. Foreground sync runs on request and periodically on the home screen. Android’s network-constrained background job requests periodic execution at 15-minute intervals; Doze, battery policies, force-stop, reboot, vendor restrictions, and permissions can delay or prevent it.
- Notifications are local notifications created after authenticated polling. There is no FCM server or guaranteed closed-app push. Open the app and use **Sync now** when prompt delivery matters. A periodic job is rescheduled on app launch.

Local TLS guidance follows [Caddy’s service and local-HTTPS documentation](https://caddyserver.com/docs/running). Background-job limits follow [Android JobScheduler documentation](https://developer.android.com/reference/android/app/job/JobInfo.Builder#setPeriodic(long)). Neither HTTPS across your network nor phone delivery has been tested in this environment.
