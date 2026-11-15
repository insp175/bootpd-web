# Third-party components and notices

The project-authored source and documentation are offered under the MIT license in LICENSE. That license does not replace the licenses or notices of bundled third-party components, and does not grant rights to their trademarks.

## Bundled Python runtime

The application bundles CPython 3.12.16 from Astral's python-build-standalone release 20261110. Exact install-only archive URLs and SHA-256 checksums are in macos/runtime.json.

- Upstream project: https://github.com/astral-sh/python-build-standalone
- Exact release: https://github.com/astral-sh/python-build-standalone/releases/tag/20261110
- Distribution format: https://docs.astral.sh/python-build-standalone/distributions/
- Native component inventory and license file hashes: licenses/runtime-inventory.json
- Native runtime and incorporated-code license texts: licenses/LICENSE.*.txt

These license texts were extracted from the checksum-verified full CPython archives for the same release, Python version, target architectures and pgo+lto build profile. The referenced texts are identical for Apple Silicon and Intel. The full archive SHA-256 values are recorded in docs/COMPLIANCE.md. The inventory distinguishes bundled static libraries from dependencies provided by macOS; inclusion of a notice is not a claim that a system library is redistributed.

CPython includes PSF and historical license terms, plus acknowledgements for incorporated code. The runtime's native components include OpenSSL (Apache-2.0), libffi and Expat (MIT), mpdecimal (BSD-2-Clause), libuuid and libedit (BSD-3-Clause), bzip2, Tcl/Tk, liblzma (0BSD), SQLite and zlib-related notices. Preserve the complete upstream texts, including copyright notices and disclaimers.

No Python source patches are applied by this project. Packaging changes include moving the installation to payload/runtime, removing bytecode cache directories and applying local ad-hoc signatures to Mach-O files. Upstream stripping and build options are part of the selected Astral distribution.

## pip and its vendored components

The supplied runtime also contains pip 26.3 and the packages listed in runtime/lib/python3.12/site-packages/pip/_vendor/vendor.txt. These are bundled even though Bootpd Web does not invoke pip.

Their license files remain in pip/_vendor and pip-26.3.dist-info/licenses. This includes Apache, BSD, MIT and PSF terms, and the MPL-2.0 notice for certifi's Mozilla-derived certificate data. The MIT license for this project does not relicense those files.

Source for the pip distribution and its vendoring records: https://pypi.org/project/pip/26.3/#files and https://github.com/pypa/pip/tree/26.3/src/pip/_vendor.
Source for certifi 2026.10.23, including its MPL-covered certificate data: https://pypi.org/project/certifi/2026.10.23/#files.
MPL-2.0 terms: https://www.mozilla.org/MPL/2.0/.
These upstream source forms are available under their original licenses. Keep these source-availability references when redistributing the runtime.

## macOS system components

The app invokes the locally installed bootpd, launchctl, osascript and networking tools, and links to system frameworks. It does not redistribute Apple's bootpd executable, macOS frameworks, SDKs or manuals. Use requires a properly licensed installation of macOS on supported Apple hardware, and permission to administer the selected network.

## Trademarks and independence

Bootpd Web is an independent community project and is not affiliated with, sponsored, endorsed or certified by Apple Inc., the Python Software Foundation or Astral.

Apple, Mac, macOS and iPhone are trademarks of Apple Inc., registered in the U.S. and other countries and regions. Python is a trademark of the Python Software Foundation. Other names identify their respective products or owners. No rights to these marks are granted by the project license.

## Package notices

The application ZIPs include this document and a licenses folder alongside the app. The same native notices and inventory are inside Bootpd Web.app/Contents/Resources/payload/licenses, so they accompany the installed helper payload too. Existing runtime and pip license files are retained. Keep these notices when redistributing the application. See docs/COMPLIANCE.md for the review and packaging correction.
