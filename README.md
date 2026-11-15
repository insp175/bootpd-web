# Bootpd Web

A local web interface for the built-in macOS bootpd DHCP server, with Ethernet device discovery.

## First launch on macOS

**Bootpd Web is a community project. The downloadable apps are ad-hoc signed, without an Apple Developer ID certificate or Apple notarization.** macOS may block the first launch because it cannot verify the developer.

If you trust this download and want to allow this app:

1. Unzip the package, move **Bootpd Web.app** to **Applications** and try opening it once.
2. Dismiss the warning, then open **Apple menu > System Settings > Privacy & Security**.
3. Scroll down to **Security**, find the message about **Bootpd Web** and click **Open Anyway**.
4. Authenticate if requested, then click **Open** in the confirmation dialog.

The exception applies to this app; you do not need to disable Gatekeeper or use Terminal commands. If **Open Anyway** is missing, try opening the app again and return to this settings page. A managed Mac may prevent exceptions. Permission to launch the app is separate from the administrator approval required to install its helper.

See [Apple's instructions for opening an unnotarized app](https://support.apple.com/en-us/102445).

## Folders

- **[Application](Application/README.md)**: ready-to-run macOS packages, with Python included. Pick the Apple Silicon or Intel ZIP.
- **[Source](Source/README.md)**: complete source code, native launcher, tests, runtime checksums and build instructions.

The separately downloadable `Application.zip` contains both ready-to-run architecture packages. `Source.zip` contains only the project sources. No Terminal setup is required to use an application package.

## Downloads

- [Apple Silicon app](https://github.com/insp175/bootpd-web/releases/download/v0.2.0/Bootpd-Web-macOS-AppleSilicon.zip)
- [Intel app](https://github.com/insp175/bootpd-web/releases/download/v0.2.0/Bootpd-Web-macOS-Intel.zip)
- [Application folder, both architectures](https://github.com/insp175/bootpd-web/releases/download/v0.2.0/Application.zip)
- [Source folder](https://github.com/insp175/bootpd-web/releases/download/v0.2.0/Source.zip)
- [Release notes and checksums](https://github.com/insp175/bootpd-web/releases/tag/v0.2.0)

## Quick start

1. Unzip the package for your Mac and move **Bootpd Web.app** to Applications.
2. Open it, choose **Open Web Panel** and approve helper installation.
3. Select Ethernet and use **Save and apply Ethernet IP** to configure its address and mask.
4. Enable DHCP or run device discovery. DHCP can wait for a cable; discovery needs a live connection.

**Stop Services** stops the app's services. **Uninstall** also restores backed-up Ethernet settings and removes its helper; deleting saved data is optional.

## Candidate status

Version 0.2.0 is available as a pre-release. These apps are ad-hoc signed and not notarized. Apple Silicon is smoke-tested; Intel is cross-compiled. Initial DHCP allocation and ping were confirmed with an iPhone 15 over USB-C Ethernet. Automatic renewal, upgrade, full uninstall and Ethernet restoration were also verified. DHCP release and Intel execution still need validation. See the [review](Source/docs/REVIEW.md) and [publishing notes](PUBLISHING.md).

Project code uses the [MIT license](Source/LICENSE). Bundled runtimes retain their original licenses.

## Licenses and affiliation

Bootpd Web is an independent project, not affiliated with or endorsed by Apple Inc. Apple, Mac, macOS and iPhone are trademarks of Apple Inc., registered in the U.S. and other countries and regions.

See the [third-party notices](Source/THIRD_PARTY.md) and [license and distribution review](Source/docs/COMPLIANCE.md). The v0.2.0 downloads were repackaged to include the supplemental native-library notices. Application behavior is unchanged.

## Next version in validation

The main branch includes **Clear expired leases** for version 0.2.1, currently undergoing local validation. It clears expired entries from this panel for the saved subnet while preserving the shared macOS lease database and active leases. Renewed leases reappear. The published application downloads above remain version 0.2.0 until validation is complete.
