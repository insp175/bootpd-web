# Review and validation

The review started from the current installed application. Python, native service source and web assets were compared with the workspace before cleanup; they matched. Working preferences, history, leases, runtime credentials and local diagnostic captures were not copied into the source package.

## Changes made during preparation

- Removed the obsolete standalone installer, redundant lookups and unused imports.
- Replaced opaque numeric permission modes with explicit octal modes.
- Added a single-instance file lock for the helper.
- Added explicit adapter lookup errors instead of iterator failures after disconnection.
- Added field-specific errors for empty network addresses.
- Recorded stopping an enabled service even when it was still waiting for a cable.
- Bound discovery probes to the selected Ethernet interface as well as source IP.
- Preserved previously resolved hostnames when a later lookup returns no name.
- Removed PID-based forced termination from service management.
- Restored the prior launchd job definition when an update fails.
- Avoided opening a new web-server session on repeated clicks of Open Web Panel.
- Reset the web-server SIGTERM handler so the native app can stop its own child reliably.
- Kept management errors visible during automatic refresh and serialized status updates around commands.
- Kept source files in English and free of explanatory code comments and docstrings. Functional interpreter directives are not needed in the application payload.

## Automated coverage

Tests cover address and pool validation, empty fields, ARP filtering, lease parsing, selected interface scope, disconnected adapters, waiting without a cable, stop behavior, IPv4 backups, rollback, restoration, activity clearing, Host/Origin/token enforcement, static path restrictions, demo restrictions and installer rollback.

Both architectures are compiled and checked with codesign. The Apple Silicon bundled runtime and local HTTP API are smoke-tested. Tests use isolated fixtures for network changes and uninstallation; they do not alter the Mac's live Ethernet settings or erase its activity history.

## Limits

A review cannot certify that code has no defects or identify authorship from stylistic traits. This preparation addresses concrete structural and behavioral findings rather than attempting to hide provenance.

The release is ad-hoc signed and not notarized. Intel is cross-compiled. A successful bootpd process launch is not proof of successful DHCP exchange. Initial DHCP allocation was confirmed with an iPhone 15 over USB-C Ethernet after enabling bootpd persistent mode. Renewal, release and broader discovery coverage remain release-validation work. Backup and log rotation are manual. Discovery scans one saved subnet and cannot find every possible unknown static IP.

## Candidate validation result

- 32 Python tests passed from the clean Source folder.
- Both native architectures compiled; codesign strict/deep verification passed for both bundles.
- Apple Silicon embedded Python, loopback HTTP and authenticated demo API passed; clean SIGTERM exit completed within five seconds.
- Browser fixture passed adapter selection, save, waiting without a cable, stop, activity clearing, light/dark switching and checkbox alignment. The fixture mocks the helper and native confirmation, so no live network preferences were changed.
- No upload was made and the currently installed application was left untouched by this preparation.

## Final preparation after the live DHCP test

A clean server-side reset was followed by enabling DHCP before cable connection. The iPhone 15 then received a new one-hour lease from the configured pool, and two ICMP probes succeeded. The same first pool address being reused is expected. This validates allocation and the waiting-to-connected transition, not renewal/release or every hardware combination.

The final cleanup separated payload preparation, version metadata, native compilation and archiving. Installer job generation is separate from transactional installation. The bootpd command still includes `-P`; a regression test covers that requirement. No additional DHCP packet-processing behavior was changed during this final cleanup.

## Upgrade, renewal and removal validation

The prepared build was installed over the previous app. A launchd unload/bootstrap race was reproduced, rolled back successfully, and fixed by waiting for complete job removal before bootstrapping its replacement. A regression test covers this wait. The corrected upgrade then succeeded on the Mac.

For renewal, the server temporarily issued a 120-second lease to the iPhone 15. With the same server process and uninterrupted cable, the expiry advanced by 60 seconds after 59 seconds of observation. This confirms automatic renewal. The normal 3600-second setting was restored afterwards.

The user selected Uninstall with full data removal. Verification found no application, installed helper, launchd plist, broker socket or app/helper processes. Ethernet configuration matched the pre-removal snapshot. The app data directory was removed as selected; the system bootpd executable and shared DHCP lease database remained. Retaining app data on uninstall is covered by automated tests but was not the physical test selected.

## 0.2.1 expired lease clearing

Regression coverage verifies active lease preservation, the expiry boundary, renewed and reassigned addresses, persistence after reopening the database, repeat clearing, subnet scope and unchanged shared lease file contents. The complete regression suite and JavaScript syntax check passed. The updated Desktop app and helper are provided for local user validation before publishing a new application release.
