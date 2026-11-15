import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import helper
from core import DEFAULT, validate


class Regressions(unittest.TestCase):
    def test_empty_address_names_the_field(self):
        for field, label in [
            ("subnet", "Subnet"),
            ("server", "Mac IPv4"),
            ("start", "Pool start"),
            ("end", "Pool end"),
        ]:
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, label):
                validate(dict(DEFAULT, interface="en5", **{field: ""}))

    def test_missing_adapter_has_actionable_error(self):
        with patch.object(helper, "interfaces", return_value=[]):
            with self.assertRaisesRegex(ValueError, "Connect the adapter"):
                helper.selected_interface("en5")

    def test_invalid_command_types_do_not_reach_handlers(self):
        for request in (None, [], {"op": []}, {"op": None}):
            with self.subTest(request=request), self.assertRaisesRegex(
                ValueError, "Invalid command"
            ):
                helper.dispatch(request)

    def test_stopping_waiting_service_is_recorded(self):
        with patch.object(helper, "ARMED", True), patch.object(
            helper, "CHILD", None
        ), patch.object(helper, "event") as event:
            helper.stop()
            self.assertFalse(helper.running())
            event.assert_called_once_with("stop", {})

    def test_observation_keeps_known_hostname(self):
        db = sqlite3.connect(":memory:")
        raw = "? (192.168.50.2) at 0a:0b:0c:0d:0e:0f on en5"
        with patch.object(helper, "DB", db), patch.object(
            helper, "resolve_name", return_value="sensor.local"
        ):
            helper.discovered(raw, "en5", [])
        with patch.object(helper, "DB", db), patch.object(
            helper, "resolve_name", return_value=""
        ):
            rows = helper.discovered(raw, "en5", [])
        self.assertEqual(rows[0]["hostname"], "sensor.local")
        db.close()


class PersistentDHCP(unittest.TestCase):
    def test_bootpd_survives_transient_link_loss(self):
        config = dict(DEFAULT, interface="en5")
        process = Mock(pid=123)
        process.poll.return_value = None
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "bootpd.plist").write_text("test")
            with patch.object(helper, "BASE", base), patch.object(
                helper, "CHILD", None
            ), patch.object(helper, "ARMED", False), patch.object(
                helper, "config", return_value=config
            ), patch.object(
                helper, "check", return_value=config
            ), patch.object(
                helper, "selected_interface", return_value={"active": True}
            ), patch.object(
                helper.socket, "socket"
            ), patch.object(
                helper.subprocess, "Popen", return_value=process
            ) as spawn, patch.object(
                helper.time, "sleep"
            ), patch.object(
                helper, "event"
            ):
                self.assertTrue(helper.handle_start({})["running"])
                arguments = spawn.call_args.args[0]
                self.assertIn("-P", arguments)
                self.assertEqual(arguments[arguments.index("-i") + 1], "en5")
