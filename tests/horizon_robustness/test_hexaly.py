"""S2 tiny unit solves and failure controls; never read empirical instances."""

from collections import Counter
from dataclasses import asdict, replace
from fractions import Fraction
from itertools import product
import inspect
import json
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from Baselines.horizon_robustness import hexaly_backend as backend
from Baselines.horizon_robustness.protocol import ContractError, digest
from Baselines.horizon_robustness.schema import (CatalogueManifest, Order, ReferenceState,
                                              Scenario, SolveResult, SolveStatus, TrainingProblem)
from Baselines.horizon_robustness.validation import validate_assignment


def fixture(vectors=None, assignment=(0, 1, 0, 1, 0), capacities=(3, 2),
            n=2, arm="HIST+ACT", delta="0.4", nu="0.2", fixed=(), allowed=()):
    if vectors is None:
        vectors = [(3, 1, 0, 0, 0), (1, 1, 0, 0, 0),
                   (0, 0, 3, 1, 0), (0, 0, 1, 1, 0)] * 2
    orders = tuple(Order(f"ORD_{i+1}", i+1, tuple((p, c) for p, c in enumerate(v) if c))
                   for i, v in enumerate(vectors))
    catalogue = CatalogueManifest("s2_tiny_unit_fixture", "fixture", tuple(f"P{p}" for p in range(len(assignment))),
                                  tuple(f"S{s}" for s in range(len(capacities))), capacities,
                                  exogenous_fixed=fixed, allowed_stations=allowed)
    counts = tuple(sum(v[p] for v in vectors) for p in range(len(assignment)))
    station_counts = tuple(sum(counts[p] for p in range(len(assignment)) if assignment[p] == s)
                           for s in range(len(capacities)))
    reference = ReferenceState(assignment, fixed, counts, station_counts, len(orders),
                               digest([asdict(o) for o in orders]), "hand_worked_s2_fixture")
    scenarios = []
    for start in range(len(orders) % n, len(orders), n):
        block = tuple(sum(vectors[i][p] for i in range(start, start+n)) for p in range(len(assignment)))
        scenarios.append(Scenario(tuple((p, c) for p, c in enumerate(block) if c), sum(block), start, start+n))
    scenarios.append(Scenario(tuple((p, c) for p, c in enumerate(counts) if c), sum(counts), 0, len(orders), "history"))
    supports = tuple(sorted(Counter(order.support for order in orders).items()))
    return TrainingProblem(catalogue, reference, n, tuple(scenarios), supports, arm=arm, delta=delta, nu=nu), orders


def enumerate_exact(problem, solve_mode="visits"):
    """Exhaustive independent rational oracle for these <=5-product fixtures."""
    catalogue, reference = problem.catalogue, problem.reference
    targets = tuple(Fraction(c, sum(reference.historical_counts)) for c in reference.station_line_counts)
    delta = Fraction(problem.delta)
    if problem.arm == "TIGHT":
        delta *= 1 - Fraction(problem.tightening)
    caps = tuple(min(Fraction(1), b+delta) for b in targets)
    inactive = {p for p, c in enumerate(reference.historical_counts) if c == 0}
    nu = Fraction(problem.nu) if problem.arm == "HIST+ACT" and inactive else Fraction(0)
    nominal = (tuple((p, c) for p, c in enumerate(reference.historical_counts) if c), sum(reference.historical_counts))
    scenarios = (nominal,) if problem.arm in ("NOM", "TIGHT") else tuple((v.counts, v.total_lines) for v in problem.scenarios)
    feasible = {}
    for assignment in product(range(catalogue.s), repeat=catalogue.p):
        if tuple(assignment.count(s) for s in range(catalogue.s)) != catalogue.capacities:
            continue
        if any(assignment[p] != s for p, s in reference.fixed):
            continue
        if catalogue.allowed_stations and any(s not in catalogue.allowed_stations[p] for p, s in enumerate(assignment)):
            continue
        worst = [Fraction(0)] * catalogue.s
        for counts, total in scenarios:
            for s in range(catalogue.s):
                a = Fraction(sum(c for p, c in counts if assignment[p] == s), total)
                h = int(any(assignment[p] == s for p in inactive))
                worst[s] = max(worst[s], a, (1-nu)*a + nu*h)
        if solve_mode == "min_slack":
            feasible[assignment] = max(Fraction(0), max(a-b for a, b in zip(worst, targets)))
        elif all(a <= cap for a, cap in zip(worst, caps)):
            feasible[assignment] = Fraction(sum(weight * len({assignment[p] for p in support})
                                                for support, weight in problem.weighted_supports))
    optimum = min(feasible.values()) if feasible else None
    return optimum, feasible


class NativeSolveTests(unittest.TestCase):
    def check_result(self, problem, orders, result, solve_mode="visits"):
        optimum, feasible = enumerate_exact(problem, solve_mode)
        self.assertIsNotNone(optimum)
        self.assertIn(result.status, (SolveStatus.FEASIBLE, SolveStatus.OPTIMAL_WITHIN_TOLERANCE), dict(result.audit))
        self.assertIn(result.assignment, feasible)
        self.assertAlmostEqual(result.objective, float(optimum), delta=1e-8)
        checked = validate_assignment(problem, result.assignment, objective=result.objective,
                                      solve_mode=solve_mode,
                                      min_slack=result.objective if solve_mode == "min_slack" else None,
                                      history=orders)
        self.assertTrue(checked["valid"], checked["violations"])
        audit = dict(result.audit)
        self.assertTrue(json.loads(audit["validation"])["valid"])
        if solve_mode == "visits":
            # The cap rows must reach the native model as INTEGER expressions,
            # which is what keeps Hexaly's float feasibility tolerance from
            # admitting a layout that violates the exact share ceiling.
            self.assertEqual(audit["row_formulation"], "exact_integer_counts_v3")
            built, total = audit["integer_typed_rows"].split("/")
            self.assertEqual(built, total)
            self.assertGreater(int(total), 0)
        else:
            self.assertEqual(audit["row_formulation"], "rational_shares_original_model")
        self.assertEqual(audit["weighted_order_count"], str(len(orders)))
        self.assertEqual(audit["weighted_support_count"], str(len(problem.weighted_supports)))
        self.assertEqual(audit["set_decisions"], str(problem.catalogue.s))
        self.assertEqual(result.representation, "whole_catalogue_set_partition")
        self.assertEqual(result.input_hash, problem.input_hash)
        self.assertEqual(result.model_hash, problem.model_hash)
        self.assertTrue(result.backend_version.startswith("13."), result.backend_version)
        self.assertGreaterEqual(result.build_seconds, 0)
        self.assertGreaterEqual(result.solve_seconds, 0)
        self.assertEqual(result.seed, 11)
        self.assertEqual(result.threads, 1)
        self.assertEqual(result.time_limit, 5)
        slots = json.loads(audit["slot_assignment"])
        self.assertEqual(len(set(slots)), problem.catalogue.p)
        if result.bound is not None:
            self.assertLessEqual(result.bound, float(optimum)+1e-8)
            self.assertEqual(result.bound_provenance, "Hexaly_HxSolution.get_objective_bound(0)")
        if result.gap is not None:
            self.assertGreaterEqual(result.gap, 0)
        self.assertEqual(SolveResult.from_dict(json.loads(json.dumps(result.to_dict(), allow_nan=False))), result)

    def test_all_four_arms_match_exact_enumeration(self):
        measured = {}
        for arm in ("NOM", "TIGHT", "HIST", "HIST+ACT"):
            with self.subTest(arm=arm):
                problem, orders = fixture(arm=arm)
                before = problem.to_dict()
                result = backend.solve(problem, time_limit=5)
                self.check_result(problem, orders, result)
                self.assertEqual(problem.to_dict(), before)
                self.assertEqual(len(result.assignment), 5)  # Inactive SKU still owns a slot.
                measured[arm] = result.objective
        # The independent enumeration above is the oracle.  The robust arms
        # retain a feasible 12-visit layout; do not turn this summary into a
        # competing, stale hand calculation.
        self.assertEqual(measured, {"NOM": 8, "TIGHT": 8, "HIST": 12, "HIST+ACT": 12})

    def test_min_slack_all_four_arms_match_enumeration(self):
        for arm in ("NOM", "TIGHT", "HIST", "HIST+ACT"):
            with self.subTest(arm=arm):
                problem, orders = fixture(arm=arm, delta="0")
                result = backend.solve(problem, time_limit=5, solve_mode="min_slack")
                self.check_result(problem, orders, result, "min_slack")
                self.assertEqual(dict(result.audit)["slack_formulation"], "eliminated_epigraph_maximum")
                self.assertEqual(problem.delta, "0")

    def test_fixed_inactive_infeasibility_and_positive_minimum_slack(self):
        problem, orders = fixture(vectors=[(1, 1, 2, 0)] * 6, assignment=(0, 0, 1, 1),
                                   capacities=(2, 2), delta="0.01", nu="0.2",
                                   fixed=((0, 0), (1, 0), (2, 1), (3, 1)))
        self.assertIsNone(enumerate_exact(problem)[0])
        rejected = backend.solve(problem, time_limit=5)
        self.assertIn(rejected.status, (SolveStatus.PROVEN_INFEASIBLE, SolveStatus.NO_INCUMBENT_LIMIT), dict(rejected.audit))
        self.assertIsNone(rejected.assignment)
        self.assertIsNone(rejected.objective)
        self.assertIsNone(rejected.gap)
        if rejected.status == SolveStatus.PROVEN_INFEASIBLE:
            self.assertIn("INCONSISTENT", rejected.native_status)
            self.assertIn("infeasibility_provenance", dict(rejected.audit))
        slack = backend.solve(problem, time_limit=5, solve_mode="min_slack")
        self.check_result(problem, orders, slack, "min_slack")
        self.assertAlmostEqual(slack.objective, 0.1, delta=1e-8)
        self.assertFalse(json.loads(dict(slack.audit)["validation"])["original_policy_feasible_exact"])

    def test_fixed_and_movable_share_one_touch_and_fixed_only_orders_count(self):
        problem, orders = fixture(vectors=[(1, 1, 0, 0), (0, 0, 1, 0)] * 3,
                                   assignment=(0, 0, 1, 1), capacities=(2, 2),
                                   delta="1", fixed=((0, 0), (2, 1), (3, 1)))
        result = backend.solve(problem, time_limit=5)
        self.check_result(problem, orders, result)
        self.assertEqual(result.objective, 6)
        self.assertEqual(result.assignment, (0, 0, 1, 1))

    def test_forbidden_station_and_training_fixed_mask(self):
        problem, orders = fixture(arm="NOM", allowed=((0,), (0, 1), (0, 1), (1,), (0, 1)))
        problem = replace(problem, reference=replace(problem.reference, fixed=((0, 0), (3, 1))))
        result = backend.solve(problem, time_limit=5)
        self.check_result(problem, orders, result)
        self.assertEqual(result.assignment[0], 0)
        self.assertEqual(result.assignment[3], 1)

    def test_activation_zero_empty_inactive_and_endpoint_one(self):
        for vectors, assignment, capacities, nu in (
                ([(1, 1)] * 6, (0, 1), (1, 1), "1"),
                ([(1, 0)] * 6, (0, 1), (1, 1), "0"),
                ([(1, 0)] * 6, (0, 0), (2,), "1")):
            with self.subTest(assignment=assignment, nu=nu):
                problem, orders = fixture(vectors=vectors, assignment=assignment, capacities=capacities,
                                           delta="0", nu=nu)
                self.check_result(problem, orders, backend.solve(problem, time_limit=5))

    def test_zero_target_inactive_fixed_station_diagnostic(self):
        problem, orders = fixture(vectors=[(1, 0)] * 6, assignment=(0, 1), capacities=(1, 1),
                                   delta="0.01", nu="0.2", fixed=((0, 0), (1, 1)))
        result = backend.solve(problem, time_limit=5, solve_mode="min_slack")
        self.check_result(problem, orders, result, "min_slack")
        self.assertAlmostEqual(result.objective, 0.2, delta=1e-8)

    def test_diagnostic_omits_unused_visit_expressions_and_integer_weights(self):
        problem, _ = fixture()
        weight = 2**62
        reference = replace(problem.reference, origin=weight,
                            historical_counts=(weight, weight, weight, weight, 0),
                            station_line_counts=(2*weight, 2*weight))
        huge = TrainingProblem(problem.catalogue, reference, 1, (),
                               (((0, 1, 2, 3), weight),), arm="NOM")
        # There are only five products. The conceptual repeated support weight
        # exceeds the visit objective's native range, but is not a coefficient
        # in the minimum-slack model and must not be constructed there.
        result = backend.solve(huge, solve_mode="min_slack", time_limit=5)
        self.assertIn(result.status, (SolveStatus.FEASIBLE, SolveStatus.OPTIMAL_WITHIN_TOLERANCE), dict(result.audit))
        self.assertAlmostEqual(result.objective, 0, delta=1e-8)
        self.assertTrue(validate_assignment(huge, result.assignment, solve_mode="min_slack", min_slack=result.objective)["valid"])


class FakeCollection(list):
    def add(self, item):
        self.append(item)


def fake_native(partition=((0, 2, 4), (1, 3)), objective=16, status="FEASIBLE", bound=8, gap=0.5):
    """Inject only the native boundary; the real independent validator still runs."""
    stations = tuple(SimpleNamespace(value=FakeCollection()) for _ in partition)
    native_objective = SimpleNamespace(value=objective)
    status_value = {"INCONSISTENT": 0, "INFEASIBLE": 1, "FEASIBLE": 2, "OPTIMAL": 3}.get(status, 99)
    solution = SimpleNamespace(status=SimpleNamespace(name=status, value=status_value),
                               get_objective_bound=MagicMock(return_value=bound),
                               get_objective_gap=MagicMock(return_value=gap))
    optimizer = MagicMock()
    optimizer.__enter__.return_value = optimizer
    optimizer.solution = solution

    def finish():
        for station, products in zip(stations, partition):
            station.value[:] = products

    optimizer.solve.side_effect = finish
    module = SimpleNamespace(version=SimpleNamespace(version="13.0.fake"),
                             HexalyOptimizer=MagicMock(return_value=optimizer))
    built = (stations, native_objective, {"test_native_boundary": "true"})
    return module, built, optimizer


class FailureControlTests(unittest.TestCase):
    def call_fake(self, problem=None, **native):
        if problem is None:
            problem, _ = fixture()
        module, built, optimizer = fake_native(**native)
        with patch.object(backend, "_load_hexaly", return_value=module), \
                patch.object(backend, "_build_model", return_value=built):
            result = backend.solve(problem, time_limit=0)
        optimizer.__exit__.assert_called_once()
        json.dumps(result.to_dict(), allow_nan=False)
        return result

    def test_invalid_api_inputs_fail_before_loading_native_code(self):
        problem, _ = fixture()
        cases = [dict(seed=-1), dict(seed=True), dict(seed=2**31), dict(threads=0),
                 dict(threads=1.5), dict(time_limit=-1), dict(time_limit=float("nan")),
                 dict(time_limit=float("inf")), dict(time_limit=True), dict(time_limit=0.5),
                 dict(time_limit=2**31), dict(solve_mode="other"), dict(log_output="yes"),
                 dict(warm_start=(0, 1)), dict(warm_start=(0, 0, 0, 0, 0)),
                 dict(warm_start=(0, 1, 0, -1, 0)), dict(warm_start=[0, 1, 0, 1, 0])]
        with patch.object(backend, "_load_hexaly", side_effect=AssertionError("bad API reached native code")):
            for options in cases:
                with self.subTest(options=options), self.assertRaises(ContractError):
                    backend.solve(problem, **options)
            with self.assertRaises(ContractError):
                backend.solve(None)

    def test_infeasible_candidate_is_not_a_proof_and_unknown_status_fails(self):
        result = self.call_fake(status="INFEASIBLE", objective=float("nan"), bound=float("inf"), gap=float("inf"))
        self.assertEqual(result.status, SolveStatus.NO_INCUMBENT_LIMIT)
        self.assertIsNone(result.assignment)
        self.assertIsNone(result.objective)
        self.assertIsNone(result.bound)
        self.assertIsNone(result.gap)
        self.assertIn("INFEASIBLE", result.native_status)
        unknown = self.call_fake(status="NEW_UNRECOGNIZED_STATUS")
        self.assertEqual(unknown.status, SolveStatus.SOLVER_ERROR)
        self.assertIsNone(unknown.assignment)

    def test_inconsistent_is_native_proof_with_null_nonfinite_bounds(self):
        result = self.call_fake(status="INCONSISTENT", bound=float("inf"))
        self.assertEqual(result.status, SolveStatus.PROVEN_INFEASIBLE)
        self.assertIsNone(result.assignment)
        self.assertIsNone(result.bound)
        self.assertIn("native_INCONSISTENT", dict(result.audit)["infeasibility_provenance"])

    def test_full_feasible_native_incumbent_is_independently_validated(self):
        result = self.call_fake()
        self.assertEqual(result.status, SolveStatus.FEASIBLE)
        self.assertEqual(result.assignment, (0, 1, 0, 1, 0))
        self.assertEqual(result.objective, 16)
        self.assertEqual(result.bound, 8)
        self.assertEqual(result.gap, 0.5)
        self.assertTrue(json.loads(dict(result.audit)["validation"])["valid"])

    def test_objective_omission_and_robust_cap_failure_reject_native_success(self):
        wrong_objective = self.call_fake(objective=8)
        self.assertEqual(wrong_objective.status, SolveStatus.NUMERICAL_ISSUE)
        self.assertIsNone(wrong_objective.assignment)
        checked = json.loads(dict(wrong_objective.audit)["validation"])
        self.assertEqual(checked["actual_objective"], 16)
        self.assertFalse(checked["valid"])
        overload = self.call_fake(partition=((0, 1, 4), (2, 3)), objective=8)
        self.assertEqual(overload.status, SolveStatus.NUMERICAL_ISSUE)
        self.assertIsNone(overload.assignment)
        self.assertFalse(json.loads(dict(overload.audit)["validation"])["model_feasible"])

    def test_duplicate_missing_unknown_and_moved_fixed_native_members_rejected(self):
        for partition in (((0, 2, 4), (1, 4)), ((0, 2), (1, 3)), ((0, 2, 5), (1, 3))):
            with self.subTest(partition=partition):
                result = self.call_fake(partition=partition)
                self.assertEqual(result.status, SolveStatus.NUMERICAL_ISSUE)
                self.assertIsNone(result.assignment)
                self.assertIn("native_partition", dict(result.audit))
        problem, _ = fixture(fixed=((0, 0),))
        moved = self.call_fake(problem, partition=((1, 2, 4), (0, 3)))
        self.assertEqual(moved.status, SolveStatus.NUMERICAL_ISSUE)
        self.assertIsNone(moved.assignment)

    def test_missing_nonfinite_and_sentinel_bounds_do_not_become_fake_certificates(self):
        for bound in (None, float("inf"), -float("inf"), float("nan"), -(2**63), 2**63-1):
            with self.subTest(bound=bound):
                result = self.call_fake(status="OPTIMAL", bound=bound, gap=0)
                self.assertEqual(result.status, SolveStatus.OPTIMAL_WITHIN_TOLERANCE)
                self.assertIsNone(result.bound)
                self.assertIsNone(result.gap)
                self.assertEqual(result.bound_provenance, "unavailable")
        inconsistent_bound = self.call_fake(bound=17)
        self.assertEqual(inconsistent_bound.status, SolveStatus.NUMERICAL_ISSUE)
        self.assertIsNone(inconsistent_bound.assignment)
        self.assertIsNone(inconsistent_bound.bound)
        self.assertEqual(dict(inconsistent_bound.audit)["get_objective_bound_raw"], "17")

    def test_nonfinite_objectives_and_gaps_are_not_serialized_as_numbers(self):
        for objective in (float("nan"), float("inf")):
            result = self.call_fake(objective=objective)
            self.assertEqual(result.status, SolveStatus.NUMERICAL_ISSUE)
            self.assertIsNone(result.assignment)
        for gap in (float("inf"), float("nan"), -1):
            result = self.call_fake(gap=gap)
            self.assertEqual(result.status, SolveStatus.FEASIBLE)
            self.assertIsNone(result.gap)

    def test_loose_eta_native_incumbent_is_accepted_but_small_eta_rejected(self):
        problem, _ = fixture(delta="0")
        module, built, optimizer = fake_native(objective=0.2, bound=0, gap=0.2)
        with patch.object(backend, "_load_hexaly", return_value=module), \
                patch.object(backend, "_build_model", return_value=built):
            result = backend.solve(problem, time_limit=0, solve_mode="min_slack")
            self.assertEqual(result.status, SolveStatus.FEASIBLE)
            checked = json.loads(dict(result.audit)["validation"])
            self.assertLess(checked["minimum_required_slack"], 0.2)
            self.assertEqual(result.objective, 0.2)
            built[1].value = 0
            failed = backend.solve(problem, time_limit=0, solve_mode="min_slack")
            self.assertEqual(failed.status, SolveStatus.NUMERICAL_ISSUE)
            self.assertIsNone(failed.assignment)

    def test_unavailable_library_native_error_and_memory_failure_are_honest(self):
        problem, _ = fixture()
        with patch.object(backend, "_load_hexaly", side_effect=ImportError("unit library unavailable")):
            result = backend.solve(problem, time_limit=0)
        self.assertEqual(result.status, SolveStatus.SOLVER_ERROR)
        self.assertEqual(result.backend_version, "unavailable")
        self.assertIn("import", result.native_status)
        for error, expected in ((RuntimeError("unit solve error"), SolveStatus.SOLVER_ERROR),
                                (MemoryError("unit resource exhaustion"), SolveStatus.RESOURCE_LIMIT)):
            module, built, optimizer = fake_native()
            optimizer.solve.side_effect = error
            with patch.object(backend, "_load_hexaly", return_value=module), \
                    patch.object(backend, "_build_model", return_value=built):
                result = backend.solve(problem, time_limit=0)
            self.assertEqual(result.status, expected)
            self.assertIsNone(result.assignment)
            self.assertEqual(dict(result.audit)["error_phase"], "solve")
            optimizer.__exit__.assert_called_once()

    def test_optional_bound_api_failure_is_retained(self):
        problem, _ = fixture()
        module, built, optimizer = fake_native()
        optimizer.solution.get_objective_bound.side_effect = RuntimeError("bound unavailable")
        with patch.object(backend, "_load_hexaly", return_value=module), \
                patch.object(backend, "_build_model", return_value=built):
            result = backend.solve(problem, time_limit=0)
        self.assertEqual(result.status, SolveStatus.FEASIBLE)
        self.assertIsNone(result.bound)
        self.assertIsNone(result.gap)
        self.assertIn("bound unavailable", dict(result.audit)["get_objective_bound_error"])

    def test_integer_objective_overflow_fails_instead_of_truncating_supports(self):
        problem, _ = fixture()
        weight = 2**62
        reference = replace(problem.reference, origin=weight,
                            historical_counts=(weight, weight, weight, weight, 0),
                            station_line_counts=(2*weight, 2*weight))
        huge = TrainingProblem(problem.catalogue, reference, 1, (), (((0, 1, 2, 3), weight),), arm="NOM")
        with patch.object(backend, "_load_hexaly", side_effect=AssertionError("integer overflow reached native code")):
            with self.assertRaises(ContractError):
                backend.solve(huge, time_limit=0)

    def test_module_uses_no_legacy_solver_or_future_data_entrypoint(self):
        source = inspect.getsource(backend)
        self.assertNotIn("milp_binary_hexaly", source)
        self.assertNotIn("read_csv", source)
        self.assertNotIn("load_industrial", source)
        self.assertEqual(tuple(inspect.signature(backend.solve).parameters),
                         ("problem", "seed", "threads", "time_limit", "solve_mode", "warm_start", "log_output"))


if __name__ == "__main__":
    unittest.main()
