import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "service", Path(__file__).resolve().parents[1] / "macos/service.py"
)
service = importlib.util.module_from_spec(spec)
spec.loader.exec_module(service)


class ServiceTests(unittest.TestCase):
    def test_install_rejects_user_owned_staging_location(self):
        with self.assertRaises(ValueError):
            service.install(Path("/tmp/BootpdWeb-stage-test"), 501)

    def test_uninstall_preserves_data_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "helper"
            data = base / "data"
            job = base / "helper.plist"
            root.mkdir()
            data.mkdir()
            job.write_text("test")
            with patch.object(service, "ROOT", root), patch.object(
                service, "DATA", data
            ), patch.object(service, "JOB", job), patch.object(
                service, "stop_service"
            ) as stop:
                service.uninstall(False)
                stop.assert_called_once()
                self.assertFalse(root.exists())
                self.assertFalse(job.exists())
                self.assertTrue(data.exists())

    def test_uninstall_can_remove_app_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "helper"
            data = base / "data"
            root.mkdir()
            data.mkdir()
            with patch.object(service, "ROOT", root), patch.object(
                service, "DATA", data
            ), patch.object(service, "JOB", base / "job"), patch.object(
                service, "stop_service"
            ):
                service.uninstall(True)
                self.assertFalse(data.exists())


class InstallRollback(unittest.TestCase):
    def test_failed_bootstrap_restores_previous_program_and_job(self):
        import subprocess
        from unittest.mock import Mock

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "helper"
            root.mkdir()
            (root / "old.py").write_text("old")
            job = base / "helper.plist"
            job.write_bytes(b"original job")
            stage = Mock()
            stage.parent = Path("/Library")
            stage.name = "BootpdWeb-stage-test"
            stage.is_symlink.return_value = False
            stage.is_dir.return_value = True
            stage.rename.side_effect = lambda target: target.mkdir()
            with patch.object(service, "ROOT", root), patch.object(
                service, "DATA", base / "data"
            ), patch.object(service, "JOB", job), patch.object(
                service, "stop_service"
            ), patch.object(
                service.os, "chown"
            ), patch.object(
                service.subprocess,
                "run",
                side_effect=[
                    subprocess.CalledProcessError(1, "bootstrap"),
                    subprocess.CompletedProcess([], 0),
                ],
            ):
                with self.assertRaises(subprocess.CalledProcessError):
                    service.install(stage, 501)
            self.assertEqual(job.read_bytes(), b"original job")
            self.assertTrue((root / "old.py").exists())


class StopServiceWait(unittest.TestCase):
    def test_update_waits_until_launchd_unloads_old_job(self):
        import subprocess

        responses = [
            subprocess.CompletedProcess([], 0),
            subprocess.CompletedProcess([], 0),
            subprocess.CompletedProcess([], 0),
            subprocess.CompletedProcess([], 1),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(
                service, "SOCKET", Path(tmp) / "helper.sock"
            ), patch.object(service, "broker_stop", return_value=False), patch.object(
                service.subprocess, "run", side_effect=responses
            ) as run, patch.object(
                service.time, "sleep"
            ) as sleep:
                service.stop_service()
                self.assertEqual(run.call_count, 4)
                sleep.assert_called_once_with(0.1)
