# Development

## Layout

| Path | Responsibility |
| --- | --- |
| `app.py` | Unprivileged loopback HTTP server |
| `helper.py` | Fixed DHCP, discovery, history and network operations |
| `core.py` | Configuration validation and lease/ARP parsers |
| `network.py` | Restricted calls to the native IPv4 configuration tool |
| `static/` | English web interface, theme and local session handling |
| `macos/Launcher.swift` | Native application window and service lifecycle UI |
| `macos/Network.swift` | SystemConfiguration IPv4 snapshot, apply and restore |
| `macos/service.py` | launchd installation, update rollback and removal |
| `macos/build.py` | Checksum-pinned, self-contained app builds |
| `tests/` | Automated validation and regression tests |

## Privileges

The web server runs as the logged-in user and listens only on 127.0.0.1, using a dynamically allocated port in the app. The complete generated URL includes a random session token. HTTP API requests require that token and the exact Host and Origin. No CORS access is enabled.

The helper runs as root through the launchd job `local.bootpd-web.helper`. Its Unix socket `/var/run/bootpd-panel.sock` has mode 0600 and belongs to the designated user. Other processes of that user and root share access; the socket is not an isolation boundary between applications of the same account.

The broker accepts a fixed command table. It does not accept shell strings, arbitrary executable paths or arbitrary file paths. Shell quoting in the native launcher is limited to known installer actions and the app's own resource path. Installation prompts use the system authorization window; passwords are not read or stored by the app.

The app installs its own runtime and helper under `/Library/BootpdPanel`. Root-executed files are root-owned and not writable by ordinary users. The native network tool changes only the IPv4 protocol of the selected enabled Ethernet service in the active network location. Restores verify both service ID and interface.

## Persistent files

| Location | Contents |
| --- | --- |
| `/var/db/bootpd-panel/settings.json` | Saved panel configuration |
| `/var/db/bootpd-panel/bootpd.plist` | Dedicated bootpd configuration |
| `/var/db/bootpd-panel/network/enN.json` | Original Ethernet IPv4 snapshot |
| `/var/db/bootpd-panel/backups/` | Prior settings and plist copies |
| `/var/db/bootpd-panel/history.sqlite3` | Activity and observations |
| `/var/db/bootpd-panel/bootpd.log` | bootpd diagnostics |
| `/var/db/bootpd-panel/helper.log` | Helper diagnostics |
| `~/Library/Application Support/Bootpd Web/web.log` | Local web server diagnostics |

Application configuration, network backups and history are root-only. The original `/etc/bootpd.plist` is copied once when present but never changed. `/var/db/dhcpd_leases` is read without modification and may contain leases from other bootpd instances using the same subnet.

IPv4 snapshots preserve the original configuration method, addresses, mask, router and client identifier. DNS and IPv6 settings are not changed. Applying a manual address does not configure a default router. The first snapshot is preserved until explicitly restored or uninstalled. If saving fails, the helper restores the previous configuration and previous panel files.

Activity is capped at 10,000 events, with 200 returned to the UI. Device observations expire after 30 days, with up to 500 returned per interface. Backup files and diagnostic logs are not automatically rotated.

## DHCP and discovery

An enabled DHCP service without an active cable waits without spawning bootpd. The monitor checks for the link every three seconds. Once the link and configured IP are available, bootpd is launched only on that interface. Stop cancels either the pending state or the owned child process.

A start failure after connection is recorded in Activity; the service does not silently retry forever. The interface must still be physically present to configure or enable it. Disconnecting a USB adapter is different from unplugging its Ethernet cable.

Discovery probes only the saved /24 to /30 subnet with up to eight concurrent ping processes, a fixed source IP and a bound interface. It is independent of DHCP and rate-limited to one launch per 55 seconds. Browser timers can be throttled in background tabs. An empty result does not prove the network has no devices.

## Service lifecycle

The application manages its launchd job, not unrelated processes. Before stopping the job it asks its helper to stop the owned bootpd child. An older manually started helper must be stopped manually before moving to the app-managed service.

An installation stages a root-owned payload, preserves the previous program and job definition, and restores both if job bootstrap fails. Uninstall restores saved Ethernet configurations before deleting the helper. If restoration fails, uninstall reports the failure instead of deleting the recovery data.

## Testing and building

```sh
python3 -m unittest discover -s tests -v
python3 macos/build.py --arch aarch64
python3 macos/build.py --arch x86_64
```

Build artifacts go to `dist/`; downloaded runtimes and compiler cache go to `.build-cache/`. Both directories are ignored by Git.

To select an installed SDK explicitly:

```sh
MACOS_SDK=/path/to/MacOSX.sdk python3 macos/build.py
```

Do not add live configuration, device history, packet captures, tokens, credentials or build caches to the source repository. The old `install.sh` path was removed; the supported user-facing installation is the native app.
