"""Two tiny four-product native IPC checks, not empirical study runs."""
from pathlib import Path
import sys
import tempfile
import unittest

from Baselines.horizon_robustness import runner
from tests.horizon_robustness.test_runner import DATASET, demand


class NativeRunnerTests(unittest.TestCase):
    def _check(self, backend):
        data = demand()
        metadata = runner.runtime_metadata(backend)
        manifest = runner.quote((DATASET,), backend=backend, arms=("NOM",),
                                loader=lambda *_: data, metadata=metadata)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = runner.run(manifest, approved_manifest_hash=manifest["manifest_hash"],
                root=root, output=root / runner.DEFAULT_OUTPUT / "native_fixture",
                solver_budget_seconds=5, wall_cutoff_seconds=30, loader=lambda *_: data, metadata=metadata)
            self.assertEqual(result[0]["status"], "COMPLETE", result[0])
            self.assertTrue(result[0]["validation"]["valid"])
            self.assertTrue(result[0]["validation"]["history_checked"])
            self.assertTrue(result[0]["evaluation"]["future_boundaries"]["stream_adjacency_verified"])
            self.assertEqual(result[0]["solve_result"]["backend"], backend)
            self.assertEqual(len(result[0]["solve_result"]["assignment"]), 4)

    def test_cplex_four_product_child(self):
        self._check("cplex")

    def test_hexaly_four_product_child(self):
        self._check("hexaly")

    def test_real_watchdog_terminates_its_own_sleeping_process_tree(self):
        from Baselines.horizon_robustness.execution import execute
        script = ("import subprocess,sys,time; p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(5)'],"
                  "creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0)); print(p.pid,flush=True); time.sleep(5)")
        with tempfile.TemporaryDirectory() as directory:
            result = execute([sys.executable, "-c", script], cwd=directory, attempt_dir=directory,
                             deadline_seconds=0.5, memory_limit_bytes=1024**3)
            self.assertEqual(result["status"], "TIMEOUT")
            self.assertFalse(runner._live_attempt(result))
            child_id = Path(result["stdout_path"]).read_text().strip()
            self.assertTrue(child_id.isdigit(), result)
            self.assertFalse(runner.psutil.pid_exists(int(child_id)))


if __name__ == "__main__":
    unittest.main()
