import argparse
import ipaddress
import json
import os
from pathlib import Path
import plistlib
import re
import signal
import socket
import socketserver
import sqlite3
import subprocess
import threading
import time
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import network
from core import DEFAULT, validate, plist_config, parse_leases, parse_arp

BASE = Path("/var/db/bootpd-panel")
SOCKET = "/var/run/bootpd-panel.sock"
LOCK = threading.RLock()
CHILD = None
ARMED = False
UID = None
DB = None


def run(args):
    p = subprocess.run(
        args,
        capture_output=True,
        text=True,
        timeout=8,
        env={"PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "LC_ALL": "C"},
    )
    if p.returncode:
        raise ValueError(p.stderr.strip() or p.stdout.strip() or "Command failed")
    return p.stdout


def interfaces():
    raw = run(["/usr/sbin/networksetup", "-listallhardwareports"])
    result = []
    for block in raw.split("\n\n"):
        fields = dict(
            (line.split(": ", 1) for line in block.splitlines() if ": " in line)
        )
        (name, dev) = (fields.get("Hardware Port", ""), fields.get("Device", ""))
        if not dev.startswith("en") or any(
            (w in name.lower() for w in ("wi-fi", "wi fi", "airport", "bluetooth"))
        ):
            continue
        if not re.fullmatch("en[0-9]+", dev):
            continue
        info = run(["/sbin/ifconfig", dev])
        addresses = re.findall(
            "inet (\\d+\\.\\d+\\.\\d+\\.\\d+) netmask (0x[0-9a-f]+)", info
        )
        result.append(
            dict(
                id=dev,
                name=name,
                active="status: active" in info,
                addresses=[
                    dict(ip=a, mask=str(ipaddress.IPv4Address(int(m, 16))))
                    for (a, m) in addresses
                ],
            )
        )
    return result


def atomic(path, data):
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "wb") as f:
        os.chmod(tmp, 0o600)
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def config():
    p = BASE / "settings.json"
    return json.loads(p.read_text()) if p.exists() else dict(DEFAULT)


def event(kind, payload):
    DB.execute(
        "INSERT INTO events(ts,kind,payload) VALUES(?,?,?)",
        (int(time.time()), kind, json.dumps(payload, ensure_ascii=False)),
    )
    DB.execute(
        "DELETE FROM events WHERE id NOT IN (SELECT id FROM events ORDER BY id DESC LIMIT 10000)"
    )
    DB.commit()


def running():
    return ARMED or (CHILD is not None and CHILD.poll() is None)


def stop():
    global CHILD, ARMED
    was_armed = ARMED
    ARMED = False
    was_running = CHILD is not None and CHILD.poll() is None
    if was_running:
        CHILD.terminate()
        try:
            CHILD.wait(timeout=5)
        except subprocess.TimeoutExpired:
            CHILD.kill()
            CHILD.wait()
    if was_running or was_armed:
        event("stop", {})
    CHILD = None


def selected_interface(device):
    port = next((item for item in interfaces() if item["id"] == device), None)
    if port is None:
        raise ValueError(
            "Ethernet adapter unavailable. Connect the adapter and try again."
        )
    return port


def check(c, require_address=True):
    c = validate(c)
    found = selected_interface(c["interface"])
    net = ipaddress.IPv4Network(c["subnet"])
    if (
        require_address
        and found["active"]
        and not any(
            (
                a["ip"] == c["server"] and a["mask"] == str(net.netmask)
                for a in found["addresses"]
            )
        )
    ):
        raise ValueError(
            "Ethernet IP settings changed. Stop DHCP and save settings to apply them again."
        )
    raw = run(["/sbin/ifconfig", "-a"])
    current = ""
    for line in raw.splitlines():
        if line and (not line[0].isspace()):
            current = line.split(":")[0]
        m = re.search("inet (\\S+) netmask (0x[0-9a-f]+)", line)
        if m and current != c["interface"]:
            other = ipaddress.IPv4Network(
                (m[1], str(ipaddress.IPv4Address(int(m[2], 16)))), strict=False
            )
            if net.overlaps(other):
                raise ValueError("Subnet overlaps interface " + current)
    return c


SCAN = {"running": False, "last_started": 0, "last_finished": 0, "error": ""}


def start_scan():
    c = check(config())
    if not selected_interface(c["interface"])["active"]:
        raise ValueError("Discovery is waiting for an Ethernet cable connection")
    net = ipaddress.IPv4Network(c["subnet"])
    if net.num_addresses > 256:
        raise ValueError(
            "Active discovery requires a /24 to /30 subnet (up to 254 hosts)"
        )
    if SCAN["running"] or time.time() - SCAN["last_started"] < 55:
        return dict(SCAN)
    SCAN.update(running=True, last_started=int(time.time()), error="")

    def worker():
        from concurrent.futures import ThreadPoolExecutor

        def probe(ip):
            try:
                subprocess.run(
                    [
                        "/sbin/ping",
                        "-n",
                        "-c",
                        "1",
                        "-W",
                        "500",
                        "-b",
                        c["interface"],
                        "-S",
                        c["server"],
                        str(ip),
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=2,
                )
            except subprocess.TimeoutExpired:
                pass

        try:
            with ThreadPoolExecutor(max_workers=8) as pool:
                list(
                    pool.map(
                        probe, [ip for ip in net.hosts() if str(ip) != c["server"]]
                    )
                )
        except Exception as e:
            SCAN["error"] = str(e)
        finally:
            with LOCK:
                SCAN.update(running=False, last_finished=int(time.time()))

    threading.Thread(target=worker, daemon=True).start()
    return dict(SCAN)


NAME_CACHE = {}


def resolve_name(ip, now):
    cached = NAME_CACHE.get(ip)
    if cached and now - cached[0] < 300:
        return cached[1]
    try:
        result = subprocess.run(
            ["/usr/bin/dscacheutil", "-q", "host", "-a", "ip_address", ip],
            capture_output=True,
            text=True,
            timeout=0.1,
        )
        name = next(
            (
                line.split(":", 1)[1].strip()[:255]
                for line in result.stdout.splitlines()
                if line.startswith("name:")
            ),
            "",
        )
    except subprocess.TimeoutExpired:
        name = ""
    if len(NAME_CACHE) >= 4096:
        NAME_CACHE.pop(next(iter(NAME_CACHE)))
    NAME_CACHE[ip] = (now, name)
    return name


def discovered(raw, dev, leases):
    DB.execute(
        "CREATE TABLE IF NOT EXISTS devices(interface TEXT, ip TEXT, mac TEXT, hostname TEXT, last_seen INTEGER, PRIMARY KEY(interface,ip,mac))"
    )
    now = int(time.time())
    names = {x["ip"]: x["hostname"] for x in leases if x["hostname"]}
    rows = parse_arp(raw, dev)
    for row in rows:
        ip = row["ip"]
        name = names.get(ip, "")
        if not name and len(rows) <= 64:
            name = resolve_name(ip, now)
        DB.execute(
            "INSERT INTO devices VALUES(?,?,?,?,?) ON CONFLICT(interface,ip,mac) DO UPDATE SET hostname=CASE WHEN excluded.hostname != '' THEN excluded.hostname ELSE devices.hostname END,last_seen=excluded.last_seen",
            (dev, ip, row["mac"], name, now),
        )
    DB.execute("DELETE FROM devices WHERE last_seen < ?", (now - 30 * 86400,))
    DB.commit()
    current = {(r["ip"], r["mac"]) for r in rows}
    return [
        dict(
            ip=r[0],
            mac=r[1],
            hostname=r[2],
            last_seen=r[3],
            cached=(r[0], r[1]) in current,
        )
        for r in DB.execute(
            "SELECT ip,mac,hostname,last_seen FROM devices WHERE interface=? ORDER BY last_seen DESC LIMIT 500",
            (dev,),
        )
    ]


def handle_scan(req):
    return start_scan()


def handle_status(req):
    c = config()
    leases = []
    try:
        leases = parse_leases(Path("/var/db/dhcpd_leases").read_text(errors="replace"))
    except FileNotFoundError:
        pass
    try:
        net = ipaddress.IPv4Network(c["subnet"])
        leases = [x for x in leases if ipaddress.IPv4Address(x["ip"]) in net]
    except ValueError:
        leases = []
    arp = run(["/usr/sbin/arp", "-an"])
    devices = discovered(arp, c["interface"], leases)
    neighbours = {(x["ip"], x["mac"]) for x in parse_arp(arp, c["interface"])}
    for x in leases:
        x["status"] = "expired" if x["expiry"] <= time.time() else "leased"
        x["arp_seen"] = (x["ip"], x["mac"]) in neighbours
    history = [
        dict(id=r[0], ts=r[1], kind=r[2], data=json.loads(r[3]))
        for r in DB.execute(
            "SELECT id,ts,kind,payload FROM events ORDER BY id DESC LIMIT 200"
        )
    ]
    ports = interfaces()
    selected = next((i for i in ports if i["id"] == c["interface"]), None)
    link = bool(selected and selected["active"])
    backups = (
        [p.stem for p in (BASE / "network").glob("en*.json")]
        if (BASE / "network").exists()
        else []
    )
    return dict(
        capabilities=sorted(COMMANDS),
        link_active=link,
        network_backups=backups,
        running=running(),
        pid=CHILD.pid if CHILD is not None and CHILD.poll() is None else None,
        config=c,
        interfaces=ports,
        leases=leases,
        scan=dict(SCAN),
        discovered=devices,
        history=history,
        backups=sorted((p.name for p in (BASE / "backups").iterdir())),
    )


def handle_clear_discovered(req):
    op = req["op"]
    dev = req.get("interface")
    if not isinstance(dev, str) or dev not in [i["id"] for i in interfaces()]:
        raise ValueError("Select an available Ethernet interface")
    run(["/usr/sbin/arp", "-d", "-i", dev, "-a"])
    if op == "clear_discovered":
        DB.execute(
            "CREATE TABLE IF NOT EXISTS devices(interface TEXT, ip TEXT, mac TEXT, hostname TEXT, last_seen INTEGER, PRIMARY KEY(interface,ip,mac))"
        )
        DB.execute("DELETE FROM devices WHERE interface=?", (dev,))
        DB.commit()
        NAME_CACHE.clear()
    event(op, {"interface": dev})
    return {"cleared": True, "interface": dev}


def handle_save(req):
    if running() or SCAN["running"]:
        raise ValueError(
            "Stop DHCP and wait for discovery before changing configuration"
        )
    c = check(req.get("config"), require_address=False)
    stamp = str(time.time_ns())
    for name in ("settings.json", "bootpd.plist"):
        p = BASE / name
        if p.exists():
            atomic(BASE / "backups" / (stamp + "-" + name), p.read_bytes())
    previous = network.snapshot(c["interface"])
    directory = BASE / "network"
    directory.mkdir(mode=0o700, exist_ok=True)
    backup = directory / (c["interface"] + ".json")
    if not backup.exists():
        atomic(backup, json.dumps(previous).encode())
    original_files = {
        name: (BASE / name).read_bytes() if (BASE / name).exists() else None
        for name in ("bootpd.plist", "settings.json")
    }
    try:
        network.apply(c)
        atomic(BASE / "bootpd.plist", plistlib.dumps(plist_config(c)))
        atomic(BASE / "settings.json", json.dumps(c).encode())
    except Exception:
        for name, content in original_files.items():
            if content is None:
                (BASE / name).unlink(missing_ok=True)
            else:
                atomic(BASE / name, content)
        network.restore(previous)
        raise
    event("save", c)
    return {"saved": True}


def handle_start(req):
    global CHILD, ARMED
    if running():
        return {"running": True}
    c = check(config())
    if not (BASE / "bootpd.plist").exists():
        raise ValueError("Save configuration first")
    if not selected_interface(c["interface"])["active"]:
        ARMED = True
        event("waiting_link", {"interface": c["interface"]})
        return {"running": True, "waiting": True}
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.bind(("0.0.0.0", 67))
    except OSError:
        raise ValueError(
            "UDP 67 is busy: disable Internet Sharing or another DHCP server"
        )
    finally:
        probe.close()
    with open(BASE / "bootpd.log", "ab") as log:
        CHILD = subprocess.Popen(
            [
                "/usr/libexec/bootpd",
                "-d",
                "-P",
                "-i",
                c["interface"],
                "-f",
                str(BASE / "bootpd.plist"),
            ],
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=log,
            close_fds=True,
            env={"PATH": "/usr/bin:/bin:/usr/sbin:/sbin"},
        )
    time.sleep(0.8)
    if not running():
        raise ValueError("bootpd exited: see /var/db/bootpd-panel/bootpd.log")
    event("start", {"pid": CHILD.pid})
    return {"running": True}


def handle_stop(req):
    stop()
    return {"running": False}


def handle_restore_network(req):
    if running() or SCAN["running"]:
        raise ValueError("Stop DHCP and wait for discovery before restoring Ethernet")
    dev = req.get("interface")
    if dev not in [i["id"] for i in interfaces()]:
        raise ValueError("Select an available Ethernet interface")
    path = BASE / "network" / (dev + ".json")
    if not path.exists():
        raise ValueError("No saved Ethernet settings for this interface")
    network.restore(json.loads(path.read_text()))
    path.unlink()
    event("restore_network", {"interface": dev})
    return {"restored": True}


def handle_clear_history(req):
    DB.execute("DELETE FROM events")
    DB.commit()
    return {"cleared": True}


COMMANDS = {
    "clear_history": handle_clear_history,
    "restore_network": handle_restore_network,
    "scan": handle_scan,
    "status": handle_status,
    "clear_discovered": handle_clear_discovered,
    "clear_arp": handle_clear_discovered,
    "save": handle_save,
    "start": handle_start,
    "stop": handle_stop,
}


def dispatch(req):
    if not isinstance(req, dict) or not isinstance(req.get("op"), str):
        raise ValueError("Invalid command")
    handler = COMMANDS.get(req["op"])
    if handler is None:
        raise ValueError("Unknown operation")
    return handler(req)


def monitor():
    global ARMED
    previous = {}
    while True:
        try:
            with LOCK:
                if ARMED and any(
                    i["id"] == config()["interface"] and i["active"]
                    for i in interfaces()
                ):
                    ARMED = False
                    try:
                        handle_start({"op": "start"})
                    except Exception as error:
                        event("start_failed", {"error": str(error)})
                if running():
                    c = config()
                    net = ipaddress.IPv4Network(c["subnet"])
                    rows = parse_leases(
                        Path("/var/db/dhcpd_leases").read_text(errors="replace")
                    )
                    for row in rows:
                        if ipaddress.IPv4Address(row["ip"]) not in net:
                            continue
                        key = row["mac"] + "/" + row["ip"]
                        signature = json.dumps(row, sort_keys=True)
                        if previous.get(key) != signature:
                            event(
                                (
                                    "lease_observed"
                                    if key not in previous
                                    else "lease_changed"
                                ),
                                row,
                            )
                            previous[key] = signature
        except (OSError, ValueError):
            pass
        time.sleep(3)


class Handler(socketserver.StreamRequestHandler):

    def handle(self):
        self.request.settimeout(5)
        try:
            line = self.rfile.readline(16385)
            if len(line) > 16384:
                raise ValueError("Request too large")
            req = json.loads(line)
            if not isinstance(req, dict):
                raise ValueError("Invalid request")
            with LOCK:
                result = dispatch(req)
            response = {"ok": True, "result": result}
        except Exception as e:
            response = {"ok": False, "error": str(e)}
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode() + b"\n")


def main():
    global UID, DB
    parser = argparse.ArgumentParser()
    parser.add_argument("--uid", type=int, required=True)
    UID = parser.parse_args().uid
    if os.geteuid() != 0 or UID <= 0:
        raise SystemExit("Root privileges and a regular user UID are required")
    import fcntl

    os.umask(0o077)
    BASE.mkdir(mode=0o700, exist_ok=True)
    (BASE / "backups").mkdir(mode=0o700, exist_ok=True)
    instance_lock = open(BASE / "helper.lock", "a")
    try:
        fcntl.flock(instance_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise SystemExit("Helper is already running")
    original = Path("/etc/bootpd.plist")
    if original.exists() and (
        not (BASE / "backups" / "original-system.plist").exists()
    ):
        atomic(BASE / "backups" / "original-system.plist", original.read_bytes())
    DB = sqlite3.connect(BASE / "history.sqlite3", check_same_thread=False)
    DB.execute(
        "CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY, ts INTEGER, kind TEXT, payload TEXT)"
    )
    if os.path.lexists(SOCKET):
        s = socket.socket(socket.AF_UNIX)
        try:
            s.connect(SOCKET)
        except ConnectionRefusedError:
            os.unlink(SOCKET)
        else:
            raise SystemExit("Helper is already running")
        finally:
            s.close()
    server = socketserver.UnixStreamServer(SOCKET, Handler)
    os.chown(SOCKET, UID, -1)
    os.chmod(SOCKET, 0o600)

    def shutdown(*_):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, shutdown)
    threading.Thread(target=monitor, daemon=True).start()
    try:
        server.serve_forever(poll_interval=0.3)
    except KeyboardInterrupt:
        pass
    finally:
        with LOCK:
            stop()
        server.server_close()
        os.unlink(SOCKET)


if __name__ == "__main__":
    main()
