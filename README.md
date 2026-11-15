# Bootpd Web

A local web interface for the built-in macOS bootpd DHCP server, with Ethernet device discovery.

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
