# Application downloads

Choose **one** ZIP:

| Mac | Package |
| --- | --- |
| Apple Silicon (M-series) | `Bootpd-Web-macOS-AppleSilicon.zip` |
| Intel | `Bootpd-Web-macOS-Intel.zip` |

Each ZIP contains **Bootpd Web.app**, a short README and third-party license information. Python is included. No Terminal commands, Homebrew or Xcode are needed to use the app.

## First launch on macOS

**Bootpd Web is a community project. The downloadable apps are ad-hoc signed, without an Apple Developer ID certificate or Apple notarization.** macOS may block the first launch because it cannot verify the developer.

If you trust this download and want to allow this app:

1. Unzip the package, move **Bootpd Web.app** to **Applications** and try opening it once.
2. Dismiss the warning, then open **Apple menu > System Settings > Privacy & Security**.
3. Scroll down to **Security**, find the message about **Bootpd Web** and click **Open Anyway**.
4. Authenticate if requested, then click **Open** in the confirmation dialog.

The exception applies to this app; you do not need to disable Gatekeeper or use Terminal commands. If **Open Anyway** is missing, try opening the app again and return to this settings page. A managed Mac may prevent exceptions. Permission to launch the app is separate from the administrator approval required to install its helper.

See [Apple's instructions for opening an unnotarized app](https://support.apple.com/en-us/102445).

Unzip, move the app to Applications, open it and choose **Open Web Panel**. Approve the macOS administrator prompt. In the browser, choose Ethernet, enter the desired IP/subnet/pool, and choose **Save and apply Ethernet IP**.

The built-in bootpd executable is not replaced. NAT and Internet Sharing are not enabled. **Stop Services** and **Uninstall** are available in the native window. The latter restores backed-up Ethernet settings before removing the helper.

Requires macOS 12+. These pre-release packages are ad-hoc signed and not notarized; macOS may require **Privacy & Security > Open Anyway** for first launch. Do not disable Gatekeeper. Intel has not been tested on physical Intel hardware.

SHA-256 checksums are provided alongside the ZIPs. When publishing, attach the two ZIPs and their checksum files to a GitHub release rather than committing the embedded runtime binaries to Git history.

Downloads: https://github.com/insp175/bootpd-web/releases/tag/v0.2.0

## License review

The v0.2.0 ZIPs were repackaged with supplemental native-library notices. Preserve the included licenses folder and THIRD_PARTY.md when redistributing. See the [notices](../Source/THIRD_PARTY.md) and [review](../Source/docs/COMPLIANCE.md). Bootpd Web is independent of Apple Inc.; references to macOS identify compatibility, not endorsement.
