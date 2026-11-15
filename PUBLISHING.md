# Release maintenance

Source code is in `Source/`. Ready-to-run packages are distributed as GitHub release assets, separately from the source archive.

For the next release, run the tests and build both macOS architectures, verify SHA-256 checksums, then attach the architecture ZIPs, Application.zip, Source.zip and SHA256SUMS.txt to the matching GitHub tag. Update download links only to published assets. Do not commit bundled runtime binaries or live configuration to Git history.

0.2.0 is an early pre-release: Apple Silicon allocation, automatic renewal, update and full uninstall were checked locally. Intel hardware validation, DHCP release and Apple notarization remain outstanding.
