# Bootpd Web

A local web interface for the built-in macOS bootpd DHCP server, with Ethernet device discovery.

## Download

Download **one ZIP** for your Mac. It includes the application, Python runtime and a short README.

- [Download for Apple Silicon (M-series)](https://github.com/insp175/bootpd-web/releases/download/v0.1.0/Bootpd-Web-macOS-AppleSilicon.zip)
- [Download for Intel](https://github.com/insp175/bootpd-web/releases/download/v0.1.0/Bootpd-Web-macOS-Intel.zip)
- [Release notes and checksums](https://github.com/insp175/bootpd-web/releases/tag/v0.1.0)

Requires macOS 12 or later. No Python, Homebrew, Xcode or Terminal setup is needed to use the app.

## Start

1. Unzip the download and drag **Bootpd Web.app** to **Applications**.
2. Open the app and click **Open Web Panel**.
3. Approve the macOS administrator prompt to install the helper. Your browser opens automatically.
4. Select your Ethernet adapter. In macOS Network settings, give it a manual IPv4 address and mask, then save the matching settings in the panel.
5. Click **Start DHCP** to distribute addresses, or **Scan now** to discover devices without DHCP.

Example: Mac IP `192.168.50.1`, subnet `192.168.50.0/24`, mask `255.255.255.0`, pool `192.168.50.100` to `192.168.50.200`.

Use a separate Ethernet network with no other DHCP server. Keep static IP addresses outside the DHCP pool. This app does not enable NAT or Internet Sharing. An active Ethernet cable is required. Discovery supports /24 to /30 subnets.

Python and all app dependencies are included. No Terminal commands, pip, Homebrew or Xcode are required to use the downloaded app.

## Stop and remove

- **Stop DHCP** in the browser stops address distribution but keeps discovery available.
- **Stop Services** in the app stops DHCP, the helper and this app's web panel. Settings stay saved. Click Open Web Panel to restart.
- **Uninstall** in the app removes its helper service and moves the app to Trash. You can also choose to delete settings, backups and observation history. The system bootpd and shared DHCP lease database are preserved.

Closing the browser does not stop DHCP. Quitting the app closes its web server; use Stop Services first if you want the helper stopped too. The installed helper starts at login-independent system startup; DHCP does not start automatically.

## macOS security notice

This initial release is ad-hoc signed, not signed with an Apple Developer ID or notarized. macOS may block its first launch. After checking the source and download, use **System Settings > Privacy & Security > Open Anyway** if macOS offers that option. Do not disable Gatekeeper. Managed Macs may require administrator approval or a notarized build.

Requires macOS 12 or later. Choose AppleSilicon for M-series Macs or Intel for Intel Macs. AppleSilicon is tested locally; the Intel build is cross-compiled and has not been run on an Intel Mac. DHCP packet exchange requires a separate test network and is not certified for production use.

## Troubleshooting

If the helper is unavailable, click **Install / Update Helper**. If a saved browser link stops working, click Open Web Panel for a fresh session. Use only the local link opened by the app; do not expose it over the Internet.

ARP cache entries are observations, not proof of current reachability. Devices can reappear immediately after clearing ARP. Hostnames are optional.

Repository: https://github.com/insp175/bootpd-web

## Source and development

The source is available in this repository. [Development instructions](docs/DEVELOPMENT.md) cover the HTTP API, privilege boundary, backups and tests. Native launcher and service lifecycle code live in `macos/`.

Build on macOS with Command Line Tools and Python 3.9+:

```sh
python3 macos/build.py
```

The builder downloads checksum-pinned Python runtimes, compiles the native launcher and creates both ZIP files under `dist/`. Set `MACOS_SDK` to select a compatible installed SDK if needed.

This is an early release. Apple Silicon launch and bundled-runtime tests are performed locally. Intel is cross-compiled; actual DHCP exchange and discovery require validation on your own isolated Ethernet segment. No automatic restart of DHCP is enabled.

## License

MIT for project code. Bundled Python and other components retain their own licenses; see [THIRD_PARTY.md](THIRD_PARTY.md).
