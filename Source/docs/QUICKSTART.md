# Bootpd Web

A local web interface for the built-in macOS bootpd DHCP server, with Ethernet device discovery.

## Start

1. Unzip the download and drag **Bootpd Web.app** to **Applications**.
2. Open the app and click **Open Web Panel**.
3. Approve the macOS administrator prompt to install the helper. Your browser opens automatically.
4. Select your Ethernet adapter. Enter the Mac IPv4 address and subnet in the panel, then click **Save and apply Ethernet IP**. The app applies the address and mask and backs up the previous Ethernet settings.
5. Click **Start DHCP** to distribute addresses, or **Scan now** to discover devices without DHCP.

Example: Mac IP `192.168.50.1`, subnet `192.168.50.0/24`, mask `255.255.255.0`, pool `192.168.50.100` to `192.168.50.200`.

Use a separate Ethernet network with no other DHCP server. Keep static IP addresses outside the DHCP pool. This app does not enable NAT or Internet Sharing. You can save settings and enable DHCP without a cable. The panel shows **Waiting for connection** and starts serving after the cable is connected. Active discovery requires a connected cable. Discovery supports /24 to /30 subnets.

Python and all app dependencies are included. No Terminal commands, pip, Homebrew or Xcode are required to use the downloaded app.

## Stop and remove

- **Restore previous Ethernet settings** in the panel restores the selected adapter's original IPv4 configuration. Stop DHCP first.
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
