# Application downloads

Choose **one** ZIP:

| Mac | Package |
| --- | --- |
| Apple Silicon (M-series) | `Bootpd-Web-macOS-AppleSilicon.zip` |
| Intel | `Bootpd-Web-macOS-Intel.zip` |

Each ZIP contains **Bootpd Web.app**, a short README and third-party license information. Python is included. No Terminal commands, Homebrew or Xcode are needed to use the app.

Unzip, move the app to Applications, open it and choose **Open Web Panel**. Approve the macOS administrator prompt. In the browser, choose Ethernet, enter the desired IP/subnet/pool, and choose **Save and apply Ethernet IP**.

The built-in bootpd executable is not replaced. NAT and Internet Sharing are not enabled. **Stop Services** and **Uninstall** are available in the native window. The latter restores backed-up Ethernet settings before removing the helper.

Requires macOS 12+. These pre-release packages are ad-hoc signed and not notarized; macOS may require **Privacy & Security > Open Anyway** for first launch. Do not disable Gatekeeper. Intel has not been tested on physical Intel hardware.

SHA-256 checksums are provided alongside the ZIPs. When publishing, attach the two ZIPs and their checksum files to a GitHub release rather than committing the embedded runtime binaries to Git history.

Downloads: https://github.com/insp175/bootpd-web/releases/tag/v0.2.0
