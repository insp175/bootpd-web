# 0.2.1

Added Clear expired leases to the DHCP table. It persistently clears expired entries from this panel for the saved subnet, without rewriting the shared macOS lease database. Active leases remain visible; renewed leases reappear. The installed helper must be updated using Install / Update Helper. Clearing one expired lease was confirmed in the installed application; no DHCP restart or network change was required. Native-library license notices and first-launch instructions are included.

# 0.2.0 - local release candidate

- Native macOS app with a bundled Python runtime and system-authorized helper installation.
- DHCP can be enabled before an Ethernet cable is connected, with an explicit waiting state.
- Ethernet IP and mask are applied from the panel; original IPv4 settings can be restored.
- Device discovery works independently of DHCP within the saved subnet.
- Separate controls clear ARP, device observations or activity history.
- English interface with remembered light/dark theme and sun/moon icons.
- Corrected form field/button name collisions, checkbox alignment, adapter-disconnection errors and error messages disappearing during refresh.
- Serialized status refreshes around management commands.
- Discovery probes are bound to the selected interface.
- Update rollback restores the previous program and launchd job; service management no longer kills processes by an inspected PID.
- Application launch disables bytecode writes inside the signed bundle.

- Enabled bootpd persistent mode so transient loss of an interface during cable reconnection does not terminate DHCP.

A real DHCP allocation was confirmed locally with an iPhone 15 connected through USB-C Ethernet. Automatic renewal was also verified with a temporary 120-second lease. DHCP release remains to be validated.

This is an early pre-release. It is not notarized. Intel execution and DHCP release still need hardware validation.

- Fixed an actual launchd upgrade race by waiting for the old job to unload completely before bootstrap.
- Upgrade, automatic lease renewal, full uninstall and Ethernet restoration were verified locally.
