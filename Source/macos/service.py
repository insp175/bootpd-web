import argparse
import json
import os
from pathlib import Path
import plistlib
import shutil
import socket
import subprocess
import time

ROOT = Path("/Library/BootpdPanel")
DATA = Path("/var/db/bootpd-panel")
SOCKET = Path("/var/run/bootpd-panel.sock")
LABEL = "local.bootpd-web.helper"
JOB = Path("/Library/LaunchDaemons") / (LABEL + ".plist")


def broker_stop():
    if not SOCKET.exists():
        return None
    with socket.socket(socket.AF_UNIX) as peer:
        peer.settimeout(10)
        try:
            peer.connect(str(SOCKET))
        except (ConnectionRefusedError, FileNotFoundError):
            return None
        peer.sendall(b'{"op":"stop"}\n')
        response = json.loads(peer.makefile("rb").readline(16384))
        if not response.get("ok"):
            raise ValueError("Could not stop DHCP safely")
        return True


def stop_service():
    responding = broker_stop()
    loaded = (
        subprocess.run(
            ["/bin/launchctl", "print", "system/" + LABEL],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode
        == 0
    )
    if loaded:
        subprocess.run(["/bin/launchctl", "bootout", "system/" + LABEL], check=True)
        deadline = time.monotonic() + 20
        while (
            subprocess.run(
                ["/bin/launchctl", "print", "system/" + LABEL],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            ).returncode
            == 0
        ):
            if time.monotonic() >= deadline:
                raise RuntimeError(
                    "The previous helper is still stopping; retry the update shortly"
                )
            time.sleep(0.1)
    elif responding:
        raise ValueError(
            "Stop the manually started helper before installing the application service"
        )
    SOCKET.unlink(missing_ok=True)


def job_definition(uid):
    return dict(
        Label=LABEL,
        ProgramArguments=[
            str(ROOT / "runtime/bin/python3"),
            "-I",
            "-B",
            str(ROOT / "helper.py"),
            "--uid",
            str(uid),
        ],
        RunAtLoad=True,
        KeepAlive=False,
        ProcessType="Background",
        StandardOutPath=str(DATA / "helper.log"),
        StandardErrorPath=str(DATA / "helper.log"),
        WorkingDirectory=str(ROOT),
        Umask=0o077,
        ExitTimeOut=15,
    )


def install(stage, uid):
    if uid <= 0:
        raise ValueError("A regular user ID is required")
    if (
        stage.parent != Path("/Library")
        or not stage.name.startswith("BootpdWeb-stage-")
        or stage.is_symlink()
        or (not stage.is_dir())
    ):
        raise ValueError("Invalid staging directory")
    if ROOT.is_symlink():
        raise ValueError("Installation path must not be a symbolic link")
    original_job = JOB.read_bytes() if JOB.exists() else None
    stop_service()
    previous = ROOT.with_name("BootpdPanel.previous")
    if previous.exists():
        shutil.rmtree(previous)
    if ROOT.exists():
        ROOT.rename(previous)
    try:
        stage.rename(ROOT)
        DATA.mkdir(mode=0o700, exist_ok=True)
        job = job_definition(uid)
        JOB.write_bytes(plistlib.dumps(job))
        os.chown(JOB, 0, 0)
        os.chmod(JOB, 0o644)
        subprocess.run(["/bin/launchctl", "bootstrap", "system", str(JOB)], check=True)
    except Exception:
        if ROOT.exists():
            shutil.rmtree(ROOT)
        if previous.exists():
            previous.rename(ROOT)
        if original_job is None:
            JOB.unlink(missing_ok=True)
        else:
            JOB.write_bytes(original_job)
            os.chmod(JOB, 0o644)
            subprocess.run(
                ["/bin/launchctl", "bootstrap", "system", str(JOB)], check=True
            )
        raise
    if previous.exists():
        shutil.rmtree(previous)


def uninstall(remove_data):
    stop_service()
    backups = DATA / "network"
    if backups.exists():
        import sys

        sys.path.insert(0, str(ROOT))
        import network

        for path in backups.glob("en*.json"):
            network.restore(json.loads(path.read_text()))
            path.unlink()
    JOB.unlink(missing_ok=True)
    if ROOT.exists():
        shutil.rmtree(ROOT)
    if remove_data and DATA.exists():
        shutil.rmtree(DATA)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=["install", "stop", "uninstall"])
    parser.add_argument("--stage", type=Path)
    parser.add_argument("--uid", type=int)
    parser.add_argument("--remove-data", action="store_true")
    args = parser.parse_args()
    if os.geteuid() != 0:
        raise SystemExit("Administrator authorization is required")
    if args.operation == "install":
        if args.stage is None or args.uid is None:
            raise SystemExit("Missing install parameters")
        install(args.stage, args.uid)
    elif args.operation == "stop":
        stop_service()
    else:
        uninstall(args.remove_data)


if __name__ == "__main__":
    main()
