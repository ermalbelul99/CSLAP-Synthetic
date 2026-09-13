"""Watchdog tests use mocked children; no native solver is launched."""
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from Baselines.horizon_robustness import execution
from Baselines.horizon_robustness.protocol import ContractError


class Child:
    pid = 999999
    def __init__(self, code=0):
        self.code, self.killed = code, False
    def poll(self):
        return self.code
    def kill(self):
        self.killed, self.code = True, -9
    def wait(self, timeout=None):
        return self.code


class ExecutionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)

    def execute(self, child=None, **kwargs):
        child = Child() if child is None else child
        return execution.execute(["python", "request.json"], cwd=self.directory,
            attempt_dir=self.directory, deadline_seconds=kwargs.pop("deadline_seconds", 1),
            memory_limit_bytes=kwargs.pop("memory_limit_bytes", 100),
            popen=kwargs.pop("popen", lambda *a, **k: child), **kwargs)

    def test_exit_and_native_nonzero_keep_separate_status(self):
        with patch.object(execution, "_identity", return_value=dict(pid=999999, create_time=1)), patch.object(execution, "_tree", return_value=[]):
            result = self.execute(Child(7))
        self.assertEqual((result["status"], result["returncode"]), ("PROCESS_ERROR", 7))
        self.assertEqual(json.loads((self.directory / "child.json").read_text())["create_time"], 1)
        self.assertEqual(list(self.directory.glob("*.partial-*")), [])

    def test_child_that_exits_before_identity_capture_is_not_launch_failure(self):
        with patch.object(execution, "_identity", side_effect=execution.psutil.NoSuchProcess(999999)):
            result = self.execute()
        self.assertEqual(result["status"], "EXITED")
        self.assertTrue(json.loads((self.directory / "child.json").read_text())["already_exited"])

    def test_launch_exception_record(self):
        def launch(*args, **kwargs):
            raise OSError("fixture")
        result = self.execute(popen=launch)
        self.assertEqual(result["status"], "LAUNCH_ERROR")
        self.assertIsNone(result["pid"])

    def test_invalid_limits_and_command_are_rejected_before_launch(self):
        for value in (0, -1, True, float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=value), self.assertRaises(ContractError):
                self.execute(deadline_seconds=value)
        with self.assertRaises(ContractError):
            execution.execute([], cwd=self.directory, attempt_dir=self.directory, deadline_seconds=1, memory_limit_bytes=1)

    def test_existing_child_artifact_prevents_launch(self):
        (self.directory / "child.json").write_text("corrupt fixture")
        result = self.execute(popen=lambda *a, **k: self.fail("launched despite existing identity"))
        self.assertEqual(result["status"], "PROCESS_ERROR")
        self.assertEqual((self.directory / "child.json").read_text(), "corrupt fixture")

    def test_existing_log_is_not_overwritten(self):
        (self.directory / "stdout.txt").write_text("old")
        result = self.execute(popen=lambda *a, **k: self.fail("launched despite existing log"))
        self.assertEqual(result["status"], "PROCESS_ERROR")
        self.assertEqual((self.directory / "stdout.txt").read_text(), "old")

    def test_identity_publication_failure_cleans_up_live_child(self):
        child = Child(None)
        with patch.object(execution, "_identity", return_value=dict(pid=999999, create_time=1)), patch.object(execution, "_publish", side_effect=OSError("disk failure")), patch.object(execution, "_terminate") as cleanup:
            result = self.execute(child)
        self.assertEqual(result["status"], "PROCESS_ERROR")
        self.assertTrue(child.killed)
        cleanup.assert_called()

    def test_monitoring_error_cleans_up_child(self):
        child = Child(None)
        with patch.object(execution, "_identity", return_value=dict(pid=999999, create_time=1)), patch.object(execution, "_tree", side_effect=execution.psutil.AccessDenied(999999)), patch.object(execution, "_terminate"):
            result = self.execute(child)
        self.assertEqual(result["status"], "PROCESS_ERROR")
        self.assertTrue(child.killed)

    def test_timeout_terminates_and_records_peak(self):
        child = Child(None)
        with patch.object(execution, "_identity", return_value=dict(pid=999999, create_time=1)), patch.object(execution, "_tree", return_value=[]), patch.object(execution.time, "monotonic", side_effect=[0, 2, 2]), patch.object(execution, "_terminate", side_effect=lambda *a: child.kill()):
            result = self.execute(child)
        self.assertEqual(result["status"], "TIMEOUT")
        self.assertEqual(result["elapsed_seconds"], 2)
        self.assertTrue(child.killed)

    def test_memory_tracks_root_plus_children_and_terminates(self):
        child = Child(None)
        members = [SimpleNamespace(pid=i, create_time=lambda: 1, memory_info=lambda: SimpleNamespace(rss=60)) for i in (1, 2)]
        with patch.object(execution, "_identity", return_value=dict(pid=999999, create_time=1)), patch.object(execution, "_tree", return_value=members), patch.object(execution, "_terminate", side_effect=lambda *a: child.kill()):
            result = self.execute(child)
        self.assertEqual(result["status"], "MEMORY_LIMIT")
        self.assertEqual(result["peak_rss_bytes"], 120)

    def test_reused_pid_is_not_terminated(self):
        with patch.object(execution.psutil, "Process", return_value=SimpleNamespace(create_time=lambda: 2)), patch.object(execution.psutil, "wait_procs", return_value=([], [])) as waited:
            execution._terminate(dict(pid=123, create_time=1))
        self.assertEqual(waited.call_args_list[0].args[0], [])

    def test_hidden_shell_free_launch_and_file_logs(self):
        def launch(command, **kwargs):
            self.assertFalse(kwargs["shell"])
            self.assertEqual(kwargs["creationflags"], getattr(execution.subprocess, "CREATE_NO_WINDOW", 0))
            self.assertTrue(hasattr(kwargs["stdout"], "write"))
            kwargs["stdout"].write(b"native diagnostics are not JSON\n")
            return Child()
        with patch.object(execution, "_identity", side_effect=execution.psutil.NoSuchProcess(999999)):
            result = self.execute(popen=launch)
        self.assertEqual(result["status"], "EXITED")
        self.assertIn("diagnostics", Path(result["stdout_path"]).read_text())


if __name__ == "__main__":
    unittest.main()
