# Release maintenance

Source code is in Source/. Ready-to-run packages are GitHub release assets, separate from the source archive.

For each release, run the appropriate checks and build both architectures. Preserve the native license files and inventory in Source/licenses, pip's vendored notices, and the source-availability links in THIRD_PARTY.md. Include licenses inside the app payload and beside the app. Review the inventory again whenever the runtime changes; do not assume a new release has the same dependencies.

Verify ZIP integrity, both app signatures and SHA-256 checksums. Attach the architecture ZIPs, their checksum files, Application.zip, Source.zip and SHA256SUMS.txt. Update repository checksums and download links to the published assets. Download the assets again and compare hashes before removing temporary build files. Never commit runtime binaries or live settings to Git history.

The 2026-11-16 packaging correction retains the application version 0.2.0 and original release tag. Superseded assets were removed after the replacement downloads were verified; corrected assets use the original download names. The explicit Source.zip and current main branch contain the packaging correction; GitHub's automatic source archives for the original tag do not.

The release remains a pre-release: Apple Silicon allocation, automatic renewal, update and full uninstall were checked locally; physical Intel execution and DHCP release validation remain outstanding. These community builds are ad-hoc signed and not notarized. No Apple certification or endorsement is claimed.

## Version 0.2.1

Version 0.2.1 includes persistent clearing of expired panel leases. Its source archive is built from the source tree in the matching release tag. The Apple Silicon app includes the locally checked feature and helper; Intel uses the matching updated payload and retains the hardware-validation limitation. Native license texts and inventories remain bundled. Before publication, verify signatures and archive integrity; after publication, download all four ZIPs and verify SHA-256 again.
