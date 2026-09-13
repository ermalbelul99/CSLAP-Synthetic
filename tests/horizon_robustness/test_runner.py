"""Runner fixture controls: no empirical optimizer is launched."""
from dataclasses import replace
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from Baselines.horizon_robustness import runner
from Baselines.horizon_robustness.protocol import ContractError, digest
from Baselines.horizon_robustness.schema import CatalogueManifest, Order, OrderedDemand, SolveResult, SolveStatus, TrainingProblem
from Baselines.horizon_robustness.uncertainty import build_training_problem

DATASET = "syn_50sku_seed1001"
META = dict(backend="hexaly", interpreter="fixture", python="fixture", packages={"hexaly": "fake"}, implementation_hash="fixture")


def demand(count=40):
    catalogue = CatalogueManifest(DATASET, "fixture", ("a", "b", "c", "d"), ("x", "y"), (2, 2))
    orders = tuple(Order(f"O{i}", i, tuple(sorted(((i % 4, 1), ((i + 1) % 4, 1))))) for i in range(count))
    return OrderedDemand(catalogue, orders)


def quote(data=None, **kwargs):
    data = demand() if data is None else data
    return runner.quote((DATASET,), loader=lambda *_: data, metadata=META, arms=("NOM",), **kwargs)


class FixtureExecutor:
    def __init__(self, mutate=None, error=None):
        self.calls = []
        self.mutate, self.error = mutate, error

    def __call__(self, command, **kwargs):
        self.calls.append((command, kwargs))
        if self.error:
            raise self.error
        request = runner._json(command[-2])
        problem = TrainingProblem.from_dict(request["problem"])
        options = request["options"]
        value = sum(weight * len({problem.reference.assignment[p] for p in support})
                    for support, weight in problem.weighted_supports)
        result = SolveResult("hexaly", "fake", SolveStatus.FEASIBLE, "fixture",
                             problem.input_hash, problem.model_hash, options["seed"], options["threads"],
                             options["time_limit"], problem.reference.assignment, value,
                             solve_mode=options["solve_mode"])
        envelope = dict(result=result.to_dict(), request_hash=digest(request), runtime=request["runtime"])
        if self.mutate:
            self.mutate(envelope)
        runner._write_new(Path(command[-1]), envelope)
        return dict(status="EXITED", returncode=0, elapsed_seconds=0.001, peak_rss_bytes=100)


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.output = self.root / runner.DEFAULT_OUTPUT / "fixture"

    def run_case(self, manifest=None, data=None, executor=None, **kwargs):
        manifest = quote() if manifest is None else manifest
        return runner.run(manifest, approved_manifest_hash=manifest["manifest_hash"], root=self.root,
                          output=self.output, solver_budget_seconds=kwargs.pop("solver_budget_seconds", 1000),
                          wall_cutoff_seconds=kwargs.pop("wall_cutoff_seconds", 60),
                          loader=lambda *_: demand() if data is None else data, metadata=META,
                          executor=FixtureExecutor() if executor is None else executor, **kwargs)

    def test_pilot_is_one_horizon_and_screen_reuses_nominal_model(self):
        pilot = quote()
        self.assertEqual((len(pilot["rows"]), pilot["unique_solve_count"], pilot["solver_seconds"]), (1, 1, 5))
        self.assertEqual(pilot["rows"][0]["n"], 4)
        screen = quote(stage="screen")
        self.assertEqual((len(screen["rows"]), screen["unique_solve_count"], screen["reused_row_count"]), (3, 1, 2))
        self.assertEqual(len({r["expected_result"] for r in screen["rows"]}), 3)

    def test_declared_industrial_selector_maps_to_adapter_catalogue_id(self):
        data = demand()
        data = OrderedDemand(replace(data.catalogue, dataset_id="berner"), data.orders)
        manifest = runner.quote(("BERNER",), loader=lambda *_: data, metadata=META)
        self.assertEqual({r["dataset_id"] for r in manifest["rows"]}, {"BERNER"})
        with self.assertRaisesRegex(ContractError, "another dataset"):
            runner.quote((DATASET,), loader=lambda *_: data, metadata=META)

    def test_core_and_named_sensitivity_configuration(self):
        core = quote(stage="core")
        self.assertEqual(len(core["rows"]), 18)
        self.assertEqual({r["seed"] for r in core["rows"]}, {11, 22, 33})
        sensitivity = quote(stage="sensitivity", sensitivity="delta", delta="0.02")
        self.assertEqual(sensitivity["config"]["delta"], "0.02")
        with self.assertRaises(ContractError):
            quote(stage="sensitivity", sensitivity="delta", delta="0.02", nu="0.02")

    def test_empty_origin_eligibility_records_are_persisted(self):
        for count in (0, 1):
            sparse = quote(demand(count))
            self.assertEqual(sparse["rows"][0]["eligibility"], "INSUFFICIENT_HISTORY")
        data = demand(8)
        manifest = quote(data)
        self.assertEqual(len(manifest["rows"]), 1)
        result = self.run_case(manifest, data=data, executor=lambda *_a, **_k: self.fail("ineligible solve"))
        self.assertEqual(result[0]["status"], "INSUFFICIENT_HISTORY")
        self.assertTrue((self.output / result[0]["case"]["expected_result"]).exists())

    def test_file_ipc_and_durable_layout_before_scoring(self):
        executor = FixtureExecutor()
        actual = runner.evaluate_layout
        def score(problem, layout, future):
            frozen = list(self.output.glob("cases/*.frozen.json"))
            self.assertEqual(len(frozen), 1)
            self.assertEqual(runner._json(frozen[0])["layout_hash"], digest(layout))
            return actual(problem, layout, future)
        with patch.object(runner, "evaluate_layout", score):
            result = self.run_case(executor=executor)
        self.assertEqual(result[0]["status"], "COMPLETE")
        command, options = executor.calls[0]
        self.assertLess(sum(map(len, command)), 3000)
        self.assertTrue(Path(command[-2]).exists())
        request = runner._json(command[-2])
        self.assertEqual(set(request), {"problem", "input_hash", "runtime", "options"})
        self.assertNotIn("future", request["problem"])
        self.assertGreater(options["deadline_seconds"], 5)

    def test_reuse_scores_every_horizon_and_resume_keeps_final_evaluations(self):
        executor = FixtureExecutor()
        manifest = quote(stage="screen")
        first = self.run_case(manifest, executor=executor)
        self.assertEqual(len(executor.calls), 1)
        self.assertEqual([v["evaluation"]["order_count"] for v in first], [2, 4, 8])
        self.assertEqual(len({v["evaluation"]["future_hash"] for v in first}), 3)
        for v in first:
            self.assertTrue(v["evaluation"]["future_boundaries"]["stream_adjacency_verified"])
            self.assertEqual(v["evaluation"]["targets_exact"], v["reference_evaluation"]["targets_exact"])
        again = self.run_case(manifest, executor=lambda *_a, **_k: self.fail("duplicate native solve"))
        self.assertEqual(digest(first), digest(again))

    def test_scoring_error_is_durable_and_explicit_retry_is_score_only(self):
        executor = FixtureExecutor()
        with patch.object(runner, "evaluate_layout", side_effect=RuntimeError("fixture score error")):
            failed = self.run_case(executor=executor)
        self.assertEqual(failed[0]["status"], "SCORING_FAILED")
        old_path = self.output / failed[0]["case"]["expected_result"]
        before = old_path.read_bytes()
        retry = self.run_case(executor=lambda *_a, **_k: self.fail("score retry solved again"), retry_id="score1", retry_reason="repair scorer")
        self.assertEqual(retry[0]["status"], "COMPLETE")
        self.assertEqual(before, old_path.read_bytes())

    def test_interrupt_after_freeze_resumes_without_solving(self):
        actual = runner._write_new
        def interrupt(path, value):
            if path.parent.name == "cases" and path.name.endswith(".json") and not path.name.endswith(".frozen.json"):
                raise KeyboardInterrupt()
            return actual(path, value)
        with patch.object(runner, "_write_new", interrupt), self.assertRaises(KeyboardInterrupt):
            self.run_case()
        self.assertEqual(len(list(self.output.glob("cases/*.frozen.json"))), 1)
        result = self.run_case(executor=lambda *_a, **_k: self.fail("resume re-solved"))
        self.assertEqual(result[0]["status"], "COMPLETE")

    def test_native_provenance_mismatch_is_rejected(self):
        def mutate(envelope):
            envelope["result"]["seed"] = 22
        result = self.run_case(executor=FixtureExecutor(mutate=mutate))
        self.assertEqual(result[0]["status"], "SOLVER_ERROR")
        self.assertIsNone(result[0]["evaluation"])

    def test_objective_and_layout_invalid_candidate_not_scored(self):
        def mutate(envelope):
            envelope["result"]["assignment"] = [0, 0, 0, 0]
        with patch.object(runner, "evaluate_layout", side_effect=AssertionError("must not score invalid")):
            result = self.run_case(executor=FixtureExecutor(mutate=mutate))
        self.assertEqual(result[0]["status"], "REJECTED_CANDIDATE")
        self.assertFalse(result[0]["accepted_training_solution"])
        self.assertIsNotNone(result[0]["solve_result"])

    def test_launch_exception_is_saved_and_never_automatically_retried(self):
        first = self.run_case(executor=FixtureExecutor(error=OSError("fixture launch failure")))
        self.assertEqual(first[0]["status"], "SOLVER_ERROR")
        second = self.run_case(executor=lambda *_a, **_k: self.fail("automatic retry"))
        self.assertEqual(digest(first), digest(second))
        retry = self.run_case(retry_id="retry1", retry_reason="fixture recovery")
        self.assertEqual(retry[0]["status"], "COMPLETE")

    def test_failed_child_keeps_a_bounded_log_excerpt_in_its_terminal_record(self):
        """A campaign audit must diagnose a failed attempt from JSON alone.

        The pilot of 2026-09-10 lost every solve to WORKER_INPUT_CHANGED, whose
        only trace was the raw stderr file. The immutable terminal record now
        carries a bounded excerpt as well.
        """
        def failing(command, **kwargs):
            directory = Path(kwargs["attempt_dir"])
            (directory / "stderr.txt").write_text("x" * 9000 + "WORKER_INPUT_CHANGED: boom", encoding="utf-8")
            (directory / "stdout.txt").write_text("partial stdout", encoding="utf-8")
            return dict(status="PROCESS_ERROR", returncode=1, elapsed_seconds=0.01, peak_rss_bytes=10)

        result = self.run_case(executor=failing)
        self.assertEqual(result[0]["status"], "PROCESS_ERROR")
        self.assertIsNone(result[0]["solve_result"])
        terminal = runner._json(next(self.output.glob("solves/*/attempts/primary/terminal.json")))
        excerpt = terminal["child_log_tail"]
        self.assertIn("WORKER_INPUT_CHANGED: boom", excerpt["stderr"])
        self.assertEqual(len(excerpt["stderr"]), 4000)
        self.assertEqual(excerpt["stdout"], "partial stdout")

    def test_successful_attempt_carries_no_log_excerpt(self):
        """Negative control: the excerpt must not appear on a returned solve."""
        self.run_case()
        terminal = runner._json(next(self.output.glob("solves/*/attempts/primary/terminal.json")))
        self.assertIsNotNone(terminal["solve_result"])
        self.assertNotIn("child_log_tail", terminal)

    def test_self_hashed_tampering_and_approval_mismatch_are_rejected(self):
        for field, value in (("expected_result", "../../escape.json"), ("n", 99), ("dataset_id", "iscf")):
            with self.subTest(field=field):
                manifest = quote()
                manifest["rows"][0][field] = value
                manifest["manifest_hash"] = digest({k: v for k, v in manifest.items() if k != "manifest_hash"})
                with self.assertRaisesRegex(ContractError, "QUOTE_STALE"):
                    self.run_case(manifest)
        manifest = quote()
        with self.assertRaisesRegex(ContractError, "MANIFEST_CHANGED"):
            runner.run(manifest, approved_manifest_hash="wrong", solver_budget_seconds=10, wall_cutoff_seconds=10)

    def test_invalid_resources_and_grids_are_rejected(self):
        for value in (float("nan"), float("inf"), -1, True):
            with self.subTest(value=value), self.assertRaises(ContractError):
                self.run_case(solver_budget_seconds=value)
        for options in ({"delta": "0.1"}, {"seeds": (999,)}, {"threads": 2}, {"memory_limit_bytes": float("nan")}, {"build_allowance_seconds": -1}):
            with self.subTest(options=options), self.assertRaises(ContractError):
                quote(**options)
        with self.assertRaises(ContractError):
            self.run_case(solver_budget_seconds=0)

    def test_sources_and_runtime_changes_invalidate_quote(self):
        manifest = quote()
        changed = replace(demand().catalogue, audit=(("changed", "metadata"),))
        with self.assertRaisesRegex(ContractError, "QUOTE_STALE"):
            self.run_case(manifest, data=OrderedDemand(changed, demand().orders))
        manifest["runtime"]["python"] = "changed"
        manifest["manifest_hash"] = digest({k: v for k, v in manifest.items() if k != "manifest_hash"})
        with self.assertRaisesRegex(ContractError, "QUOTE_STALE"):
            self.run_case(manifest)

    def test_min_slack_cache_distinguishes_target_even_if_caps_clip(self):
        data = demand()
        problem = build_training_problem(data.catalogue, data.orders[:28], 4, "NOM", delta="1")
        other_ref = replace(problem.reference, station_line_counts=(27, 29))
        # Structural reference consistency is checked by schema: alter the
        # product counts as well so assignment implies the new target exactly.
        counts = list(problem.reference.historical_counts)
        a = next(p for p, s in enumerate(problem.reference.assignment) if s == 0)
        b = next(p for p, s in enumerate(problem.reference.assignment) if s == 1)
        counts[a] -= 1; counts[b] += 1
        other_ref = replace(other_ref, historical_counts=tuple(counts))
        other = replace(problem, reference=other_ref)
        # NOM q changes here too; exact b inclusion is additionally explicit in
        # the key payload, independently checked by spying on digest below.
        captured = []
        original = runner.digest
        def capture(value):
            captured.append(value)
            return original(value)
        with patch.object(runner, "digest", capture):
            key = runner.solve_identity(other, backend="hexaly", backend_version="fake", implementation_hash="a", solve_mode="min_slack")
        self.assertEqual(captured[-1]["exact_b"], ["27/56", "29/56"])
        self.assertNotEqual(key, runner.solve_identity(problem, backend="hexaly", backend_version="fake", implementation_hash="a", solve_mode="min_slack"))

    def test_identity_contains_mode_version_start_and_implementation(self):
        data = demand()
        problem = build_training_problem(data.catalogue, data.orders[:28], 4, "NOM")
        options = dict(backend="hexaly", backend_version="fake", implementation_hash="a")
        baseline = runner.solve_identity(problem, **options)
        for changes in ({"backend_version": "b"}, {"implementation_hash": "b"}, {"solve_mode": "min_slack"}, {"seed": 22}, {"warm_start": tuple(1-s for s in problem.reference.assignment)}):
            self.assertNotEqual(baseline, runner.solve_identity(problem, **{**options, **changes}))

    def test_atomic_publish_never_replaces_existing_or_exposes_partial(self):
        target = self.root / "artifact.json"
        runner._write_new(target, {"a": 1})
        with self.assertRaisesRegex(ContractError, "IMMUTABLE_ARTIFACT"):
            runner._write_new(target, {"a": 2})
        self.assertEqual(runner._json(target), {"a": 1})
        self.assertEqual(list(self.root.glob("*.partial-*")), [])
        bom_path = self.root / "powershell-utf8.json"
        bom_path.write_text('{"a":1}', encoding="utf-8-sig")
        self.assertEqual(runner._json(bom_path), {"a": 1})

    def test_kernel_lock_and_live_child_block_duplicate_work(self):
        with runner._campaign_lock(self.output):
            with self.assertRaisesRegex(ContractError, "LIVE_CAMPAIGN"):
                with runner._campaign_lock(self.output):
                    self.fail("second lock")
        marker = self.output / "solves/x/attempts/primary/child.json"
        runner._write_new(marker, dict(pid=os.getpid(), create_time=runner.psutil.Process().create_time()))
        with self.assertRaisesRegex(ContractError, "LIVE_ATTEMPT"):
            self.run_case()

    def test_reused_pid_is_not_live_identity(self):
        self.assertFalse(runner._live_attempt(dict(pid=os.getpid(), create_time=1)))

    def test_corrupt_child_marker_blocks_new_native_work(self):
        marker = self.output / "solves/x/attempts/primary/child.json"
        runner._write_new(marker, {"pid": os.getpid(), "create_time": "unknown"})
        with self.assertRaisesRegex(ContractError, "CORRUPT_ARTIFACT"):
            self.run_case()

    def test_interrupted_unknown_launch_requires_manual_audit_before_retry(self):
        manifest = quote()
        base = self.output / "solves" / manifest["rows"][0]["solve_key"] / "attempts/primary"
        runner._write_new(base / "request.json", {"interrupted": True})
        result = self.run_case(manifest, executor=lambda *_a, **_k: self.fail("relaunched unknown attempt"))
        self.assertEqual(result[0]["status"], "INTERRUPTED")
        with self.assertRaisesRegex(ContractError, "UNKNOWN_ATTEMPT_OWNER"):
            self.run_case(manifest, retry_id="retry1", retry_reason="not sufficient by itself")

    def test_native_infeasibility_contradiction_remains_explicit(self):
        def mutate(envelope):
            envelope["result"].update(status="PROVEN_INFEASIBLE", assignment=None, objective=None)
        result = self.run_case(executor=FixtureExecutor(mutate=mutate))
        self.assertEqual(result[0]["native_contradiction"]["kind"], "NATIVE_INFEASIBILITY_CONTRADICTION")

    def test_supervisor_applies_deadline_to_whole_campaign_and_keeps_denominator(self):
        manifest = quote(stage="screen")
        def cutoff(command, **options):
            self.assertEqual(command[-3], "campaign")
            self.assertEqual(options["deadline_seconds"], 10)
            self.assertEqual(options["memory_limit_bytes"], manifest["config"]["memory_limit_bytes"])
            return dict(status="TIMEOUT", returncode=-9, elapsed_seconds=10, peak_rss_bytes=200)
        result = runner.supervised_run(manifest, approved_manifest_hash=manifest["manifest_hash"],
            root=self.root, output=self.output, solver_budget_seconds=5, wall_cutoff_seconds=10, executor=cutoff)
        self.assertEqual(len(result), 3)
        self.assertEqual({r["status"] for r in result}, {"WALL_CUTOFF"})
        terminal = list(self.output.glob("supervision/*/terminal.json"))
        self.assertEqual(len(terminal), 1)
        self.assertEqual(len(runner._json(terminal[0])["cases"]), 3)

    def test_corrupt_completed_record_is_not_silently_reused(self):
        result = self.run_case()
        path = self.output / result[0]["case"]["expected_result"]
        # Deliberate corruption is confined to a temporary test artifact.
        record = runner._json(path)
        record["status"] = "tampered"
        path.write_text(json.dumps(record))
        with self.assertRaisesRegex(ContractError, "CORRUPT_ARTIFACT"):
            self.run_case(executor=lambda *_a, **_k: self.fail("launched over corrupt case"))

    def test_malformed_native_json_keeps_failure(self):
        def malformed(command, **kwargs):
            Path(command[-1]).write_text("partial native result")
            return dict(status="EXITED", returncode=0)
        result = self.run_case(executor=malformed)
        self.assertEqual(result[0]["status"], "SOLVER_ERROR")
        self.assertIsNone(result[0]["evaluation"])

    def test_output_escape_and_invalid_retry_are_rejected(self):
        with self.assertRaisesRegex(ContractError, "OUTPUT_NOT_ALLOWED"):
            runner._output_root(self.root.parent, self.root)
        for options in ({"retry_id": "../escape", "retry_reason": "x"}, {"retry_id": "retry"}, {"retry_reason": "x"}):
            with self.subTest(options=options), self.assertRaises(ContractError):
                self.run_case(**options)

    def test_min_slack_is_a_diagnostic_and_does_not_reset_scoring_caps(self):
        manifest = quote(stage="sensitivity", sensitivity="min_slack", solve_mode="min_slack")
        executor = FixtureExecutor(mutate=lambda value: value["result"].update(objective=0))
        result = self.run_case(manifest, executor=executor)
        self.assertTrue(all(v["status"] == "DIAGNOSTIC_COMPLETE" for v in result))
        self.assertTrue(all(v["evaluation"]["delta"] == "0.01" for v in result))


if __name__ == "__main__":
    unittest.main()
