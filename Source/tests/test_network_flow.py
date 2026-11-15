import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import helper
from core import DEFAULT


class EthernetFlow(unittest.TestCase):
    def setUp(self):
        self.c = dict(DEFAULT, interface="en7")

    def test_check_accepts_disconnected_interface(self):
        with patch.object(
            helper,
            "interfaces",
            return_value=[dict(id="en7", active=False, addresses=[])],
        ), patch.object(helper, "run", return_value=""):
            self.assertEqual(helper.check(self.c), self.c)

    def test_start_arms_without_cable_or_process(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "bootpd.plist").write_text("test")
            with patch.object(helper, "BASE", base), patch.object(
                helper, "config", return_value=self.c
            ), patch.object(helper, "check", return_value=self.c), patch.object(
                helper, "interfaces", return_value=[dict(id="en7", active=False)]
            ), patch.object(
                helper, "event"
            ), patch.object(
                helper, "CHILD", None
            ), patch.object(
                helper, "ARMED", False
            ), patch.object(
                helper.subprocess, "Popen"
            ) as spawn:
                self.assertTrue(helper.handle_start({})["waiting"])
                self.assertTrue(helper.running())
                spawn.assert_not_called()
                helper.stop()
                self.assertFalse(helper.running())

    def test_save_applies_ip_and_preserves_first_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "backups").mkdir()
            original = dict(interface="en7", config={"ConfigMethod": "DHCP"})
            with patch.object(helper, "BASE", base), patch.object(
                helper, "running", return_value=False
            ), patch.object(
                helper, "check", side_effect=lambda c, **kw: c
            ), patch.object(
                helper, "event"
            ), patch.object(
                helper.network, "snapshot", return_value=original
            ), patch.object(
                helper.network, "apply"
            ) as apply:
                helper.handle_save({"config": self.c})
                apply.assert_called_once_with(self.c)
                self.assertEqual(
                    json.loads((base / "network/en7.json").read_text()), original
                )
                with patch.object(
                    helper.network,
                    "snapshot",
                    return_value={"config": {"ConfigMethod": "Manual"}},
                ):
                    helper.handle_save({"config": self.c})
                self.assertEqual(
                    json.loads((base / "network/en7.json").read_text()), original
                )

    def test_apply_failure_rolls_back(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "backups").mkdir()
            with patch.object(helper, "BASE", base), patch.object(
                helper, "running", return_value=False
            ), patch.object(helper, "check", return_value=self.c), patch.object(
                helper.network,
                "snapshot",
                return_value={"config": {"ConfigMethod": "DHCP"}},
            ) as snapshot, patch.object(
                helper.network, "apply", side_effect=ValueError("failed")
            ), patch.object(
                helper.network, "restore"
            ) as restore:
                with self.assertRaises(ValueError):
                    helper.handle_save({"config": self.c})
                restore.assert_called_once_with(snapshot.return_value)
                self.assertFalse((base / "settings.json").exists())

    def test_restore_uses_saved_interface_configuration(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "network").mkdir()
            saved = dict(
                interface="en7",
                service_id="service",
                enabled=True,
                config={"ConfigMethod": "DHCP"},
            )
            path = base / "network/en7.json"
            path.write_text(json.dumps(saved))
            with patch.object(helper, "BASE", base), patch.object(
                helper, "running", return_value=False
            ), patch.object(
                helper, "interfaces", return_value=[{"id": "en7"}]
            ), patch.object(
                helper, "event"
            ), patch.object(
                helper.network, "restore"
            ) as restore:
                helper.handle_restore_network({"interface": "en7"})
                restore.assert_called_once_with(saved)
                self.assertFalse(path.exists())
