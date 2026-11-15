# Third-party components

The downloadable application bundles CPython 3.12.16 from Astral's python-build-standalone release 20261110.

- Project: https://github.com/astral-sh/python-build-standalone
- Distribution documentation: https://docs.astral.sh/python-build-standalone/
- Exact URLs and SHA-256 checksums: macos/runtime.json in the source repository.
- CPython and bundled library license texts are included inside the runtime distribution (inside Bootpd Web.app/Contents/Resources/payload/runtime).

CPython uses the Python Software Foundation License. Other included runtime components retain their own licenses. The app invokes Apple's system bootpd and networking tools; those tools are not redistributed in this repository.
