import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core import DEFAULT, validate, plist_config, parse_leases
import helper


class Validation(unittest.TestCase):

    def setUp(self):
        self.c = dict(DEFAULT, interface="en7")

    def test_valid_and_no_router(self):
        p = plist_config(self.c)
        self.assertEqual(p["dhcp_enabled"], ["en7"])
        self.assertEqual(p["Subnets"][0]["dhcp_router"], [])
        self.assertFalse(p["relay_enabled"])

    def test_bad_inputs(self):
        for update in [
            dict(interface="en0;id"),
            dict(subnet="192.168.50.1/24"),
            dict(subnet="8.8.8.0/24"),
            dict(server="192.168.50.120"),
            dict(start="192.168.50.0"),
            dict(end="192.168.51.2"),
            dict(lease=True),
            dict(lease=1),
            dict(start="192.168.50.220"),
        ]:
            with self.subTest(update=update), self.assertRaises(ValueError):
                validate(dict(self.c, **update))

    def test_lease_formats_and_malformed(self):
        raw = "{\nname=<script>alert(1)</script>\nip_address=192.168.50.100\nhw_address=1,a:b:0:01:fe:ff\nlease=0x70000000\n}\n{\nip_address=oops\nlease=1\n}"
        rows = parse_leases(raw)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["mac"], "0a:0b:00:01:fe:ff")
        self.assertEqual(rows[0]["expiry"], 1879048192)

    def test_clear_arp_scope(self):
        with patch.object(
            helper, "interfaces", return_value=[{"id": "en5"}]
        ), patch.object(helper, "run") as run, patch.object(helper, "event"):
            helper.dispatch({"op": "clear_arp", "interface": "en5"})
            run.assert_called_once_with(["/usr/sbin/arp", "-d", "-i", "en5", "-a"])
            with self.assertRaises(ValueError):
                helper.dispatch({"op": "clear_arp", "interface": "en0;id"})

    def test_arp_filter_and_normalization(self):
        from core import parse_arp

        raw = "? (192.168.50.2) at a:b:c:d:e:f on en5 ifscope [ethernet]\n? (192.168.50.3) at ff:ff:ff:ff:ff:ff on en5\n? (192.168.50.4) at a:b:c:d:e:1 on en0"
        self.assertEqual(
            parse_arp(raw, "en5"), [{"ip": "192.168.50.2", "mac": "0a:0b:0c:0d:0e:0f"}]
        )

    @patch.object(
        helper, "interfaces", return_value=[dict(id="en7", active=True, addresses=[])]
    )
    @patch.object(helper, "config", return_value=dict(DEFAULT, interface="en5"))
    def test_scan_limits_and_cooldown(self, config_mock, ports_mock):
        with patch.object(
            helper, "check", return_value=dict(self.c, subnet="192.168.0.0/16")
        ):
            with self.assertRaises(ValueError):
                helper.start_scan()
        with patch.object(helper, "check", return_value=self.c), patch.dict(
            helper.SCAN, {"running": True}
        ), patch.object(helper.threading, "Thread") as thread:
            helper.start_scan()
            thread.assert_not_called()

    def test_clear_history_preserves_other_tables(self):
        import sqlite3

        db = sqlite3.connect(":memory:")
        db.execute("CREATE TABLE events(id INTEGER, payload TEXT)")
        db.execute("INSERT INTO events VALUES(1, 'test')")
        db.execute("CREATE TABLE devices(ip TEXT)")
        db.execute("INSERT INTO devices VALUES('192.168.50.10')")
        with patch.object(helper, "DB", db):
            self.assertTrue(helper.dispatch({"op": "clear_history"})["cleared"])
        self.assertEqual(db.execute("SELECT COUNT(*) FROM events").fetchone()[0], 0)
        self.assertEqual(db.execute("SELECT COUNT(*) FROM devices").fetchone()[0], 1)
        db.close()

    def test_unknown_command(self):
        with self.assertRaises(ValueError):
            helper.dispatch({"op": "shell", "command": "id"})

    def test_interface_address_required(self):
        with patch.object(
            helper,
            "interfaces",
            return_value=[dict(id="en7", active=True, addresses=[])],
        ):
            with self.assertRaises(ValueError):
                helper.check(self.c)

    def test_save_creates_backup(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            (base / "backups").mkdir()
            with patch.object(helper, "BASE", base), patch.object(
                helper, "check", side_effect=lambda c, **kw: validate(c)
            ), patch.object(helper.network, "snapshot", return_value={}), patch.object(
                helper.network, "apply"
            ), patch.object(
                helper, "event"
            ), patch.object(
                helper, "running", return_value=False
            ):
                helper.dispatch({"op": "save", "config": self.c})
                helper.dispatch({"op": "save", "config": dict(self.c, lease=7200)})
                self.assertEqual(len(list((base / "backups").iterdir())), 2)
                self.assertEqual(
                    json.loads((base / "settings.json").read_text())["lease"], 7200
                )

    def test_running_config_cannot_change(self):
        with patch.object(helper, "running", return_value=True):
            with self.assertRaises(ValueError):
                helper.dispatch({"op": "save", "config": self.c})


if __name__ == "__main__":
    unittest.main()
