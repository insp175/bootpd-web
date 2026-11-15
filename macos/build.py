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
VERSION = '0.1.0'


def command(*args):
    subprocess.run([str(x) for x in args], check=True)


def runtime(arch, cache):
    meta = json.loads((PROJECT / 'macos/runtime.json').read_text())[arch]
    archive = cache / (arch + '.tar.gz')
    if not archive.exists():
        urllib.request.urlretrieve(meta['url'], archive)
    if hashlib.sha256(archive.read_bytes()).hexdigest() != meta['sha256']:
        raise ValueError('Runtime checksum mismatch: ' + arch)
    return archive


def sign_bundle(bundle):
    for path in bundle.rglob('*'):
        if not path.is_file() or path.is_symlink():
            continue
        with path.open('rb') as stream:
            magic = stream.read(4)
        if magic in (b'\xcf\xfa\xed\xfe', b'\xfe\xed\xfa\xcf', b'\xca\xfe\xba\xbe'):
            subprocess.run(['/usr/bin/codesign', '--force', '--sign', '-', str(path)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    command('/usr/bin/codesign', '--force', '--deep', '--sign', '-', bundle)


def build(arch, destination, cache):
    label = 'AppleSilicon' if arch == 'aarch64' else 'Intel'
    folder = destination / ('Bootpd-Web-macOS-' + label)
    if folder.exists():
        shutil.rmtree(folder)
    bundle = folder / 'Bootpd Web.app'
    contents = bundle / 'Contents'
    payload = contents / 'Resources/payload'
    payload.mkdir(parents=True)
    (contents / 'MacOS').mkdir()
    with tarfile.open(runtime(arch, cache)) as archive:
        for item in archive.getmembers():
            target = (payload / item.name).resolve()
            if not target.is_relative_to(payload.resolve()):
                raise ValueError('Unsafe archive path')
        archive.extractall(payload)
    (payload / 'python').rename(payload / 'runtime')
    for name in ('app.py', 'core.py', 'helper.py'):
        shutil.copy2(PROJECT / name, payload / name)
    shutil.copy2(PROJECT / 'macos/service.py', payload / 'service.py')
    shutil.copytree(PROJECT / 'static', payload / 'static')
    for pattern in ('__pycache__',):
        for path in payload.rglob(pattern):
            shutil.rmtree(path)
    version = hashlib.sha256()
    for path in sorted(payload.rglob('*.py')):
        version.update(path.relative_to(payload).as_posix().encode())
        version.update(path.read_bytes())
    (payload / 'version.txt').write_text(VERSION + '-' + version.hexdigest() + '\n')
    info = dict(CFBundleExecutable='BootpdWeb', CFBundleIdentifier='local.bootpd-web.app', CFBundleName='Bootpd Web', CFBundleDisplayName='Bootpd Web', CFBundlePackageType='APPL', CFBundleShortVersionString=VERSION, CFBundleVersion='1', LSMinimumSystemVersion='12.0', NSHighResolutionCapable=True, NSAppleEventsUsageDescription='Install, update, stop or remove the Bootpd Web helper with administrator authorization.')
    (contents / 'Info.plist').write_bytes(plistlib.dumps(info))
    target = ('arm64' if arch == 'aarch64' else 'x86_64') + '-apple-macosx12.0'
    sdk = os.environ.get('MACOS_SDK', subprocess.check_output(['/usr/bin/xcrun', '--show-sdk-path'], text=True).strip())
    command('/usr/bin/xcrun', 'swiftc', '-O', '-sdk', sdk, '-target', target, '-module-cache-path', cache / 'swift-modules', '-framework', 'AppKit', PROJECT / 'macos/Launcher.swift', '-o', contents / 'MacOS/BootpdWeb')
    shutil.copy2(PROJECT / 'docs/QUICKSTART.md', folder / 'README.md')
    shutil.copy2(PROJECT / 'THIRD_PARTY.md', folder / 'THIRD_PARTY.md')
    sign_bundle(bundle)
    command('/usr/bin/codesign', '--verify', '--deep', '--strict', bundle)
    output = destination / (folder.name + '.zip')
    output.unlink(missing_ok=True)
    command('/usr/bin/ditto', '-c', '-k', '--sequesterRsrc', '--keepParent', folder, output)
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    (destination / (output.name + '.sha256')).write_text(digest + '  ' + output.name + '\n')
    print(str(output), digest, flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--arch', choices=['aarch64', 'x86_64', 'all'], default='all')
    parser.add_argument('--output', type=Path, default=PROJECT / 'dist')
    parser.add_argument('--cache', type=Path, default=PROJECT / '.build-cache')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    args.cache.mkdir(parents=True, exist_ok=True)
    for arch in (('aarch64', 'x86_64') if args.arch == 'all' else (args.arch,)):
        build(arch, args.output, args.cache)


if __name__ == '__main__':
    main()
