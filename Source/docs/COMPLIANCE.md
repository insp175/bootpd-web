# License and distribution review

Review date: 2026-11-16. Scope: the current public source tree, its build script and runtime pins, the Apple Silicon desktop copy, and both original v0.2.0 architecture ZIPs downloaded from GitHub.

This is a practical license and packaging review, not a legal opinion or a guarantee of non-infringement. The review found missing native-library notices in the original v0.2.0 ZIPs. The packaging correction adds these notices to the replacement downloads; application behavior is unchanged.

## Findings

| Area | Result |
| --- | --- |
| Project source | Root and Source MIT licenses agree. MIT covers project-authored material only; third-party licenses remain separate. |
| Python | CPython's installed license is present. The fuller upstream license and incorporated-code acknowledgements have now been retained in Source/licenses. |
| Native runtime libraries | The original ZIPs omitted notices from the matching Astral full archives. The corrected packages include the fourteen referenced license texts and inventory. |
| pip and vendored packages | License files and vendor.txt are retained in the runtime, even though the app does not invoke pip. THIRD_PARTY.md now includes source-availability links, including certifi's MPL-covered data. |
| Web dependencies and assets | No external JS framework, CDN dependency, downloaded web font, Apple logo or bundled Apple documentation was found in the reviewed app source. CSS selects installed system fonts; the theme SVGs contain basic geometric shapes. |
| macOS components | System tools and frameworks are invoked or dynamically linked, rather than redistributed. The macOS SDK and system bootpd binary are not packaged by the builder. |
| Names | DHCP, ARP, CIDR and bootpd describe protocols, notation or the executable being controlled. Apple/macOS/Mac references describe compatibility. Explicit independence and trademark attribution notices have been added. This is not a worldwide trademark clearance search for Bootpd Web. |
| GitHub usage | No obvious conflict with publishing a legitimate local network administration tool was identified. Operators must have permission to administer and probe the selected network. |
| First-launch permission | Instructions use Apple's documented per-app Open Anyway exception. They do not instruct users to disable Gatekeeper. Absence of notarization is disclosed. |
| Documentation | The reviewed guides explain this implementation and link to upstream documentation. No Apple manuals or substantial copied Apple documentation are bundled. Rights and terms for external websites remain with their owners. |

## Evidence and native licenses

Both architecture ZIPs were read without installing or running them. Their SHA-256 values were:

- Apple Silicon: 9f479fa100fec2174d5f8a6777fcb7915c0a21a09d0918c873d5a1835435d88c
- Intel: 8f083d75963da30f5e6fcaa6d9d70bc720c86771e8d3a9b740366991072bc72e

The corresponding Astral full archives were checked against the release's SHA256SUMS:

- cpython-3.12.16+20261110-aarch64-apple-darwin-pgo+lto-full.tar.zst: 4da072af9dbbc2557d3aabf51db553a19694f6ac61b5b7169749e4acfa5a052d
- cpython-3.12.16+20261110-x86_64-apple-darwin-pgo+lto-full.tar.zst: 00ec7774da05b9a3489f5022b8ae91567835adaf8b6288d60150316247b756ee

Their PYTHON.json metadata identifies the applicable extension-module license files. Fourteen referenced license texts were extracted unchanged; each text is identical across the two targets. See [the inventory](../licenses/runtime-inventory.json) for license identifiers, module associations, system/static links and file hashes.

The target metadata uses libedit, not GNU readline, and does not identify a bundled gdbm extension. A generic upstream license collection lists components for other builds too; it must not be treated as an inventory of these macOS targets.

The applicable native notices include PSF/historical Python terms, MIT, BSD, Apache-2.0, bzip2, Tcl, 0BSD, SQLite and zlib-related texts. This selection does not identify a requirement to relicense the independent project source under the GPL. The pip vendoring includes MPL-covered certificate data; its own notices and source availability must be preserved.

## Changes and remaining release work

- Added the fourteen native license texts and a traceable component inventory to Source/licenses.
- Expanded THIRD_PARTY.md with license scope, runtime packaging changes, pip/certifi source links, system-component distinctions, trademark attribution and a disclaimer of endorsement.
- Updated the builder to copy these licenses into the app payload and the surrounding download folder before signing and archiving.
- Added visible links and the open package finding to the repository and application guides.

The replacement architecture ZIPs include licenses both inside the app payload and alongside the app, while retaining pip's existing notices. Application.zip contains these corrected architecture packages; Source.zip contains the updated source, notices and builder. DHCP logic is unchanged. The interface label uses the official macOS capitalization, the package fingerprint is refreshed, and the resource signature is renewed after adding license files. Both architecture signatures and ZIP integrity are verified before uploading. Current archive hashes are provided in SHA256SUMS.txt rather than embedded in this document.

Keep all upstream copyright, license and NOTICE files when cleaning or minimizing code. The project's preference for comment-free source does not authorize removing third-party legal notices.

## Primary references

- [Apple trademark and copyright guidelines](https://www.apple.com/legal/intellectual-property/guidelinesfor3rdparties.html)
- [Xcode and Apple SDKs Agreement, including section 2.4 on macOS distribution](https://www.apple.com/legal/sla/docs/xcode.pdf)
- [Apple software license agreements](https://www.apple.com/legal/sla/)
- [Apple first-launch guidance](https://support.apple.com/en-us/102445)
- [Python 3.12 licensing](https://docs.python.org/3.12/license.html)
- [PSF trademark policy](https://www.python.org/psf/trademarks/)
- [Astral release 20261110](https://github.com/astral-sh/python-build-standalone/releases/tag/20261110)
- [Astral distribution metadata documentation](https://docs.astral.sh/python-build-standalone/distributions/)
- [Mozilla MPL distribution FAQ](https://www.mozilla.org/en-US/MPL/2.0/FAQ/)
- [GitHub Acceptable Use Policies](https://docs.github.com/en/site-policy/acceptable-use-policies/github-acceptable-use-policies)

## Limits

No exhaustive copyright-origin, patent, international trademark, export-control or jurisdiction-specific privacy assessment was performed. Public source inspection cannot establish exclusive ownership of every generated or contributed line. Network observations such as MAC addresses and hostnames may be personal information in some settings; operators remain responsible for authorization, retention and applicable law. Account-specific agreements and the exact Apple agreements accepted on a build machine also remain the distributor's responsibility. No Apple, GitHub or upstream approval is claimed.
