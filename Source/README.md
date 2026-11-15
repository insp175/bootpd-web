# Bootpd Web

Local web control for the built-in macOS bootpd DHCP server, with Ethernet device discovery. Version 0.2.0, pre-release.

## Use the app

Ready-to-run downloads belong in the separate **Application** folder. Choose the Apple Silicon or Intel ZIP, unzip it and move **Bootpd Web.app** to Applications.

1. Open the app and choose **Open Web Panel**.
2. Approve the macOS administrator prompt to install its helper.
3. Select Ethernet, enter an IPv4 address, subnet and DHCP pool, then choose **Save and apply Ethernet IP**. The app applies the IP and mask and backs up the adapter's original IPv4 settings.
4. Choose **Start DHCP**, or **Scan now** to discover devices without DHCP.

No Terminal, Python, Homebrew or Xcode installation is needed to use a downloaded app. macOS 12 or later is required.

Example: Mac `192.168.50.1`, subnet `192.168.50.0/24`, pool `192.168.50.100` through `192.168.50.200`.

You can save settings and enable DHCP without a cable. The adapter itself must be present. The panel shows **Waiting for connection** until the link is active. Discovery requires a connected cable and supports /24 through /30 networks. Use a separate Ethernet segment without another DHCP server. NAT and Internet Sharing are never enabled.

## Stop, restore and uninstall

- **Stop DHCP** stops address distribution; discovery remains available.
- **Restore previous Ethernet settings** restores the original IPv4 configuration. Stop DHCP and wait for any scan to finish first.
- **Stop Services** in the native app stops its web panel, DHCP and helper. Settings are retained.
- **Uninstall** stops its services, restores backed-up Ethernet settings and moves the app to Trash. An optional checkbox also removes saved settings, backups and history.

The system bootpd executable and shared DHCP lease database are preserved. Closing the browser does not stop DHCP. Quitting the native app closes its web panel; it asks before leaving the helper running. The installed helper starts at system boot, but DHCP remains off until explicitly enabled.

## Device observations

The device list reads complete unicast ARP entries on the saved Ethernet. It includes static IP devices once they communicate with the Mac or respond to discovery. **Last observed** is the time an ARP entry was seen, not a live reachability check. Active discovery does not search arbitrary or unknown subnets. Names come from DHCP or system DNS when available.

ARP clearing, device observation clearing and activity clearing are separate actions. Activity clearing preserves leases, discovered devices and settings. New traffic can recreate ARP entries immediately.

The theme button switches between sun and moon icons; the selected theme is remembered.

## Build from source

Building requires macOS, Apple Command Line Tools and Python 3.9 or later:

```sh
python3 -m unittest discover -s tests -v
python3 macos/build.py
```

The builder downloads the exact Python runtimes in `macos/runtime.json`, verifies SHA-256 checksums and creates Apple Silicon and Intel ZIPs in `dist/`. No third-party Python packages are required by the application or builder. `MACOS_SDK` can select a compatible installed SDK.

See [development notes](docs/DEVELOPMENT.md), [review and validation](docs/REVIEW.md), [release notes](RELEASE_NOTES.md) and [third-party notices](THIRD_PARTY.md).

## Distribution status

These candidates are ad-hoc signed, not Apple Developer ID signed or notarized. macOS can block the first launch. After reviewing the source and download, use **System Settings > Privacy & Security > Open Anyway** if offered. Do not disable Gatekeeper. Managed Macs may require a notarized build. See the [first-launch instructions](../README.md#first-launch-on-macos) for the complete path to the permission and confirmation steps.

Apple Silicon is built and smoke-tested locally. Intel is cross-compiled and has not been run on an Intel Mac. Successful process startup is not evidence of successful DHCP packet exchange; live DHCP and discovery must be verified on an isolated Ethernet test segment before a production release.

## License

Project code: MIT. Bundled Python and other runtime components retain their original licenses; see [THIRD_PARTY.md](THIRD_PARTY.md).
