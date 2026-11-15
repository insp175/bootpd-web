import argparse
import json
import os
from pathlib import Path
import plistlib
import shutil
import signal
import socket
import struct
import subprocess
import time

ROOT = Path('/Library/BootpdPanel')
DATA = Path('/var/db/bootpd-panel')
SOCKET = Path('/var/run/bootpd-panel.sock')
LABEL = 'local.bootpd-web.helper'
JOB = Path('/Library/LaunchDaemons') / (LABEL + '.plist')


def broker_stop():
    if not SOCKET.exists():
        return None
    with socket.socket(socket.AF_UNIX) as peer:
        peer.settimeout(10)
        try:
            peer.connect(str(SOCKET))
        except (ConnectionRefusedError, FileNotFoundError):
            return None
        pid = struct.unpack('i', peer.getsockopt(0, 2, 4))[0]
        command = subprocess.check_output(['/bin/ps', '-p', str(pid), '-o', 'uid=,command='], text=True).strip()
        if not command.startswith('0 ') or '/Library/BootpdPanel/helper.py' not in command:
            raise ValueError('The helper socket belongs to an unexpected process')
        peer.sendall(b'{"op":"stop"}\n')
        response = json.loads(peer.makefile('rb').readline(16384))
        if not response.get('ok'):
            raise ValueError('Could not stop DHCP safely')
        return pid


def stop_service():
    pid = broker_stop()
    subprocess.run(['/bin/launchctl', 'bootout', 'system/' + LABEL], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
            for _ in range(50):
                time.sleep(0.1)
                os.kill(pid, 0)
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    if SOCKET.exists():
        SOCKET.unlink()


def install(stage, uid):
    if uid <= 0:
        raise ValueError('A regular user ID is required')
    if stage.parent != Path('/Library') or not stage.name.startswith('BootpdWeb-stage-') or stage.is_symlink():
        raise ValueError('Invalid staging directory')
    stop_service()
    previous = ROOT.with_name('BootpdPanel.previous')
    if previous.exists():
        shutil.rmtree(previous)
    if ROOT.exists():
        ROOT.rename(previous)
    try:
        stage.rename(ROOT)
        DATA.mkdir(mode=0o700, exist_ok=True)
        job = dict(Label=LABEL, ProgramArguments=[str(ROOT / 'runtime/bin/python3'), '-I', str(ROOT / 'helper.py'), '--uid', str(uid)], RunAtLoad=True, KeepAlive=False, ProcessType='Background', StandardOutPath=str(DATA / 'helper.log'), StandardErrorPath=str(DATA / 'helper.log'), WorkingDirectory=str(ROOT), Umask=0o077, ExitTimeOut=15)
        JOB.write_bytes(plistlib.dumps(job))
        os.chown(JOB, 0, 0)
        os.chmod(JOB, 0o644)
        subprocess.run(['/bin/launchctl', 'bootstrap', 'system', str(JOB)], check=True)
    except Exception:
        if ROOT.exists():
            shutil.rmtree(ROOT)
        if previous.exists():
            previous.rename(ROOT)
        raise
    if previous.exists():
        shutil.rmtree(previous)


def uninstall(remove_data):
    stop_service()
    JOB.unlink(missing_ok=True)
    if ROOT.exists():
        shutil.rmtree(ROOT)
    if remove_data and DATA.exists():
        shutil.rmtree(DATA)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=['install', 'stop', 'uninstall'])
    parser.add_argument('--stage', type=Path)
    parser.add_argument('--uid', type=int)
    parser.add_argument('--remove-data', action='store_true')
    args = parser.parse_args()
    if os.geteuid() != 0:
        raise SystemExit('Administrator authorization is required')
    if args.operation == 'install':
        if args.stage is None or args.uid is None:
            raise SystemExit('Missing install parameters')
        install(args.stage, args.uid)
    elif args.operation == 'stop':
        stop_service()
    else:
        uninstall(args.remove_data)


if __name__ == '__main__':
    main()
