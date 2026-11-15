import ipaddress
import json
from pathlib import Path
import subprocess

BINARY = Path(__file__).resolve().parent / "networkctl"


def execute(operation, device, *args, snapshot=None):
    result = subprocess.run(
        [str(BINARY), operation, device, *args],
        input=json.dumps(snapshot) if snapshot is not None else None,
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode:
        raise ValueError(result.stderr.strip() or "Ethernet configuration failed")
    return json.loads(result.stdout) if operation == "snapshot" else None


def snapshot(device):
    return execute("snapshot", device)


def apply(config):
    mask = str(ipaddress.IPv4Network(config["subnet"]).netmask)
    execute("apply", config["interface"], config["server"], mask)


def restore(saved):
    execute("restore", saved["interface"], snapshot=saved)
