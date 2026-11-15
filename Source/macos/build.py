import argparse
import hashlib
import json
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import tarfile
import urllib.request

PROJECT = Path(__file__).resolve().parents[1]
VERSION = "0.2.0"


def command(*args):
    subprocess.run([str(x) for x in args], check=True)


def runtime(arch, cache):
    meta = json.loads((PROJECT / "macos/runtime.json").read_text())[arch]
    archive = cache / (arch + ".tar.gz")
    if not archive.exists():
        urllib.request.urlretrieve(meta["url"], archive)
    if hashlib.sha256(archive.read_bytes()).hexdigest() != meta["sha256"]:
        raise ValueError("Runtime checksum mismatch: " + arch)
    return archive


def sign_bundle(bundle):
    for path in bundle.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        with path.open("rb") as stream:
            magic = stream.read(4)
        if magic in (b"\xcf\xfa\xed\xfe", b"\xfe\xed\xfa\xcf", b"\xca\xfe\xba\xbe"):
            subprocess.run(
                ["/usr/bin/codesign", "--force", "--sign", "-", str(path)],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
    command("/usr/bin/codesign", "--force", "--deep", "--sign", "-", bundle)


def prepare_payload(archive_path, payload):
    with tarfile.open(archive_path) as archive:
        for item in archive.getmembers():
            target = (payload / item.name).resolve()
            if not target.is_relative_to(payload.resolve()):
                raise ValueError("Unsafe archive path")
        archive.extractall(payload)
    (payload / "python").rename(payload / "runtime")
    for name in ("app.py", "core.py", "helper.py", "network.py"):
        shutil.copy2(PROJECT / name, payload / name)
    shutil.copy2(PROJECT / "macos/service.py", payload / "service.py")
    shutil.copytree(PROJECT / "static", payload / "static")
    for path in payload.rglob("__pycache__"):
        shutil.rmtree(path)


def write_version(payload):
    version = hashlib.sha256()
    for path in sorted(PROJECT.rglob("*")):
        if (
            path.is_file()
            and path.suffix in (".py", ".swift", ".js", ".css", ".html")
            and not any(
                part in ("dist", ".build-cache", "__pycache__", ".git")
                for part in path.relative_to(PROJECT).parts
            )
        ):
            version.update(path.relative_to(PROJECT).as_posix().encode())
            version.update(path.read_bytes())
    (payload / "version.txt").write_text(VERSION + "-" + version.hexdigest() + "\n")


def write_bundle_info(contents):
    info = dict(
        CFBundleExecutable="BootpdWeb",
        CFBundleIdentifier="local.bootpd-web.app",
        CFBundleName="Bootpd Web",
        CFBundleDisplayName="Bootpd Web",
        CFBundlePackageType="APPL",
        CFBundleShortVersionString=VERSION,
        CFBundleVersion="1",
        LSMinimumSystemVersion="12.0",
        NSHighResolutionCapable=True,
        NSAppleEventsUsageDescription="Install, update, stop or remove the Bootpd Web helper with administrator authorization.",
    )
    (contents / "Info.plist").write_bytes(plistlib.dumps(info))


def compile_native(arch, contents, payload, cache):
    target = ("arm64" if arch == "aarch64" else "x86_64") + "-apple-macosx12.0"
    sdk = (
        os.environ.get("MACOS_SDK")
        or subprocess.check_output(
            ["/usr/bin/xcrun", "--show-sdk-path"], text=True
        ).strip()
    )
    compiler = [
        "/usr/bin/xcrun",
        "swiftc",
        "-O",
        "-sdk",
        sdk,
        "-target",
        target,
        "-module-cache-path",
        cache / "swift-modules",
    ]
    for name, framework, output in (
        ("Launcher.swift", "AppKit", contents / "MacOS/BootpdWeb"),
        ("Network.swift", "SystemConfiguration", payload / "networkctl"),
    ):
        command(
            *compiler, "-framework", framework, PROJECT / "macos" / name, "-o", output
        )


def archive_application(folder, destination):
    output = destination / (folder.name + ".zip")
    output.unlink(missing_ok=True)
    command(
        "/usr/bin/ditto", "-c", "-k", "--sequesterRsrc", "--keepParent", folder, output
    )
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    (destination / (output.name + ".sha256")).write_text(
        digest + "  " + output.name + "\n"
    )
    print(str(output), digest, flush=True)


def build(arch, destination, cache):
    label = "AppleSilicon" if arch == "aarch64" else "Intel"
    folder = destination / ("Bootpd-Web-macOS-" + label)
    if folder.exists():
        shutil.rmtree(folder)
    bundle = folder / "Bootpd Web.app"
    contents = bundle / "Contents"
    payload = contents / "Resources/payload"
    payload.mkdir(parents=True)
    (contents / "MacOS").mkdir()
    prepare_payload(runtime(arch, cache), payload)
    write_version(payload)
    write_bundle_info(contents)
    compile_native(arch, contents, payload, cache)
    for source, name in (
        ("docs/QUICKSTART.md", "README.md"),
        ("THIRD_PARTY.md", "THIRD_PARTY.md"),
        ("LICENSE", "LICENSE"),
    ):
        shutil.copy2(PROJECT / source, folder / name)
    sign_bundle(bundle)
    command("/usr/bin/codesign", "--verify", "--deep", "--strict", bundle)
    archive_application(folder, destination)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--arch", choices=["aarch64", "x86_64", "all"], default="all")
    parser.add_argument("--output", type=Path, default=PROJECT / "dist")
    parser.add_argument("--cache", type=Path, default=PROJECT / ".build-cache")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    args.cache.mkdir(parents=True, exist_ok=True)
    for arch in ("aarch64", "x86_64") if args.arch == "all" else (args.arch,):
        build(arch, args.output, args.cache)


if __name__ == "__main__":
    main()
