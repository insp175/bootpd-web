from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import helper
from core import DEFAULT
from leases import clear_expired, visible_leases


def lease(expiry, ip="192.168.50.100", mac="00:11:22:33:44:55"):
    return dict(ip=ip, mac=mac, hostname="client", expiry=expiry)


class LeaseClearing(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.addCleanup(self.db.close)

    def test_only_expired_entries_are_cleared(self):
        rows = [lease(99), lease(100, ip="192.168.50.101"), lease(101)]
        self.assertEqual(clear_expired(self.db, rows, 100), 2)
        self.assertEqual(visible_leases(self.db, rows, 100), [rows[2]])

    def test_renewed_and_reassigned_leases_reappear(self):
        clear_expired(self.db, [lease(99)], 100)
        for row in [lease(101), lease(100), lease(99, mac="00:11:22:33:44:66")]:
            with self.subTest(row=row):
                self.assertEqual(visible_leases(self.db, [row], 100), [row])

    def test_repeated_clear_is_idempotent(self):
        rows = [lease(99)]
        self.assertEqual(clear_expired(self.db, rows, 100), 1)
        self.assertEqual(clear_expired(self.db, rows, 100), 0)

    def test_clearing_persists_after_reopening_database(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "history.sqlite3"
            with sqlite3.connect(path) as db:
                clear_expired(db, [lease(99)], 100)
            with sqlite3.connect(path) as db:
                self.assertEqual(visible_leases(db, [lease(99)], 100), [])

    def test_handler_keeps_shared_database_and_other_subnet(self):
        raw = "{\nip_address=192.168.50.100\nhw_address=1,0:11:22:33:44:55\nlease=99\n}\n{\nip_address=192.168.90.100\nhw_address=1,0:11:22:33:44:55\nlease=99\n}\n"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "dhcpd_leases"
            path.write_text(raw)
            with patch.object(helper, "LEASE_FILE", path), patch.object(
                helper, "DB", self.db
            ), patch.object(helper, "config", return_value=DEFAULT), patch.object(
                helper.time, "time", return_value=100
            ), patch.object(helper, "event") as event:
                self.assertEqual(helper.dispatch({"op": "clear_expired_leases"}), {"cleared": 1})
                event.assert_called_once_with("clear_expired_leases", {"subnet": DEFAULT["subnet"], "count": 1})
            self.assertEqual(path.read_text(), raw)
            self.assertEqual(visible_leases(self.db, [lease(99, ip="192.168.90.100")], 100), [lease(99, ip="192.168.90.100")])

    def test_missing_shared_database_is_empty(self):
        with patch.object(helper, "LEASE_FILE", Path("/nonexistent/bootpd-test-leases")):
            self.assertEqual(helper.current_leases(DEFAULT), [])
