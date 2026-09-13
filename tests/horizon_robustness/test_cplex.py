"""Tiny native CPLEX checks against separately enumerated exact layouts."""

from dataclasses import replace
from fractions import Fraction
import itertools
import json
import unittest
from unittest.mock import patch

from Baselines.horizon_robustness.cplex_backend import finite_native, normalize_status, solve
from Baselines.horizon_robustness.protocol import ContractError
from Baselines.horizon_robustness.schema import CatalogueManifest, Order, SolveResult, SolveStatus
from Baselines.horizon_robustness.uncertainty import build_training_problem
from Baselines.horizon_robustness.validation import validate_assignment


def fixture():
    catalogue = CatalogueManifest("cplex-unit", "fixture", tuple("abcdef"), ("s0", "s1"),
                                  (3, 3), known_reference=(0, 0, 0, 1, 1, 1))
    history = tuple(Order(str(i + 1), i + 1, line) for i, line in enumerate(
        (((0, 3), (3, 1)), ((1, 1), (4, 2)), ((0, 1), (3, 3)),
         ((1, 2), (4, 1)), ((0, 2), (4, 2)), ((1, 1), (3, 1)))))
    return build_training_problem(catalogue, history, 2), history


def enumerate_oracle(problem, mode="visits"):
    """No solver or uncertainty/validation helper decides feasibility here."""
    catalogue, reference = problem.catalogue, problem.reference
    feasible = []
    for assignment in itertools.product(range(catalogue.s), repeat=catalogue.p):
        if any(assignment.count(s) != cap for s, cap in enumerate(catalogue.capacities)):
            continue
        if any(assignment[p] != s for p, s in reference.fixed):
            continue
        if any(assignment[p] not in catalogue.eligible_stations(p) for p in range(catalogue.p)):
            continue
        delta = Fraction(problem.delta) * (1 - Fraction(problem.tightening) if problem.arm == "TIGHT" else 1)
        targets = [Fraction(c, reference.total_lines) for c in reference.station_line_counts]
        caps = [min(1, target + delta) for target in targets]
        scenarios = [(reference.historical_counts, reference.total_lines)] if problem.arm in ("NOM", "TIGHT") else [
            (tuple(dict(v.counts).get(p, 0) for p in range(catalogue.p)), v.total_lines) for v in problem.scenarios]
        zero_products = [p for p, c in enumerate(reference.historical_counts) if c == 0]
        nu = Fraction(problem.nu) if problem.arm == "HIST+ACT" and zero_products else Fraction(0)
        worst = [Fraction(0)] * catalogue.s
        for counts, total in scenarios:
            q = [Fraction(c, total) for c in counts]
            vectors = [q]
            for product in zero_products:
                vectors.append([(1 - nu) * value + (nu if p == product else 0) for p, value in enumerate(q)])
            for vector in vectors:
                for s in range(catalogue.s):
                    worst[s] = max(worst[s], sum(vector[p] for p in range(catalogue.p) if assignment[p] == s))
        eta = max(Fraction(0), max(v - target for v, target in zip(worst, targets)))
        if mode == "visits" and any(v > cap for v, cap in zip(worst, caps)):
            continue
        objective = sum(w * len({assignment[p] for p in support}) for support, w in problem.weighted_supports) if mode == "visits" else eta
        feasible.append((objective, assignment))
    return min(feasible) if feasible else None


class CplexTest(unittest.TestCase):
    def test_every_arm_agrees_with_exact_enumeration(self):
        problem, history = fixture()
        for arm, delta in itertools.product(("NOM", "TIGHT", "HIST", "HIST+ACT"), ("0.01", "0.5")):
            candidate = replace(problem, arm=arm, delta=delta)
            expected = enumerate_oracle(candidate)
            result = solve(candidate, time_limit=5)
            with self.subTest(arm=arm, delta=delta):
                if expected is None:
                    self.assertEqual(result.status, SolveStatus.PROVEN_INFEASIBLE, result.to_dict())
                    self.assertIsNone(result.assignment)
                else:
                    self.assertEqual(result.status, SolveStatus.OPTIMAL_WITHIN_TOLERANCE, result.to_dict())
                    self.assertEqual(result.objective, float(expected[0]))
                    self.assertTrue(validate_assignment(candidate, result.assignment, objective=result.objective, history=history)["valid"])
                    self.assertIsNotNone(result.bound)
                    self.assertAlmostEqual(result.bound, result.objective, places=8)
                self.assertEqual(SolveResult.from_dict(json.loads(json.dumps(result.to_dict()))), result)
                self.assertEqual(result.input_hash, candidate.input_hash)

    def test_minimum_slack_certificate_and_policy_immutability(self):
        problem, history = fixture()
        for arm in ("NOM", "TIGHT", "HIST", "HIST+ACT"):
            candidate = replace(problem, arm=arm)
            before = candidate.to_dict()
            expected = enumerate_oracle(candidate, "min_slack")
            result = solve(candidate, solve_mode="min_slack", time_limit=5)
            with self.subTest(arm=arm):
                self.assertEqual(result.status, SolveStatus.OPTIMAL_WITHIN_TOLERANCE, result.to_dict())
                self.assertAlmostEqual(result.objective, float(expected[0]), places=8)
                self.assertAlmostEqual(result.bound, float(expected[0]), places=8)
                self.assertTrue(validate_assignment(candidate, result.assignment, objective=result.objective,
                                                   solve_mode="min_slack", history=history)["valid"])
                self.assertEqual(candidate.to_dict(), before)

    def test_fixed_inactive_can_certify_infeasibility_and_positive_minimum_slack(self):
        cat = CatalogueManifest("fixed-zero", "fixture", ("a", "b"), ("s0", "s1"), (1, 1),
                                exogenous_fixed=((0, 0), (1, 1)), known_reference=(0, 1))
        history = tuple(Order(str(i), i, ((0, 1),)) for i in range(1, 4))
        problem = build_training_problem(cat, history, 1, nu="0.02", delta="0.01")
        infeasible = solve(problem, time_limit=5)
        self.assertEqual(infeasible.status, SolveStatus.PROVEN_INFEASIBLE, infeasible.to_dict())
        diagnostic = solve(problem, solve_mode="min_slack", time_limit=5)
        self.assertEqual(diagnostic.status, SolveStatus.OPTIMAL_WITHIN_TOLERANCE, diagnostic.to_dict())
        self.assertAlmostEqual(diagnostic.objective, 0.02, places=8)
        self.assertEqual(diagnostic.assignment, (0, 1))
        self.assertEqual(problem.delta, "0.01")

    def test_all_fixed_visits_and_same_station_touches_count(self):
        problem, history = fixture()
        cat = replace(problem.catalogue, exogenous_fixed=tuple(enumerate(problem.reference.assignment)))
        fixed_problem = build_training_problem(cat, history, 2, arm="NOM")
        result = solve(fixed_problem, time_limit=5)
        self.assertEqual(result.status, SolveStatus.OPTIMAL_WITHIN_TOLERANCE, result.to_dict())
        self.assertEqual(result.assignment, fixed_problem.reference.assignment)
        self.assertEqual(result.objective, enumerate_oracle(fixed_problem)[0])

    def test_compatibility_fixed_slots_and_warm_start(self):
        problem, history = fixture()
        cat = replace(problem.catalogue, exogenous_fixed=((0, 0),),
                      allowed_stations=((0,), (0, 1), (0, 1), (1,), (0, 1), (0, 1)))
        problem = build_training_problem(cat, history, 2, delta="0.5", arm="HIST+ACT")
        result = solve(problem, warm_start=problem.reference.assignment, time_limit=5)
        self.assertEqual(result.status, SolveStatus.OPTIMAL_WITHIN_TOLERANCE, result.to_dict())
        self.assertEqual(result.objective, enumerate_oracle(problem)[0])
        self.assertEqual(result.assignment[0], 0)
        self.assertEqual(result.assignment[3], 1)

    def test_honest_native_statuses_and_absent_bounds(self):
        for code in (108, 106, 132, 114):
            self.assertEqual(normalize_status(code, False), SolveStatus.NO_INCUMBENT_LIMIT)
        self.assertEqual(normalize_status(107, True), SolveStatus.FEASIBLE)
        self.assertEqual(normalize_status(103, False), SolveStatus.PROVEN_INFEASIBLE)
        self.assertEqual(normalize_status(119, False), SolveStatus.SOLVER_ERROR)
        self.assertEqual(normalize_status(112, False), SolveStatus.RESOURCE_LIMIT)
        self.assertEqual(normalize_status(115, True), SolveStatus.NUMERICAL_ISSUE)
        for value in (None, float("nan"), float("inf"), -float("inf"), 1e20, "bad"):
            self.assertIsNone(finite_native(value))
        self.assertEqual(finite_native(0), 0)

    def test_invalid_api_inputs_fail_before_native_solve(self):
        problem, history = fixture()
        for kwargs in (dict(seed=True), dict(seed=-1), dict(threads=0), dict(threads=1.5),
                       dict(time_limit=0), dict(time_limit=float("nan")), dict(solve_mode="unknown"),
                       dict(warm_start=(0, 1)), dict(log_output="yes")):
            with self.subTest(kwargs=kwargs), self.assertRaises(ContractError):
                solve(problem, **kwargs)

    def test_native_failure_is_not_relabelled_as_infeasible(self):
        problem, _ = fixture()
        with patch("docplex.mp.model.Model.solve", side_effect=RuntimeError("deliberate native failure control")):
            result = solve(replace(problem, arm="NOM"), time_limit=5)
        self.assertEqual(result.status, SolveStatus.SOLVER_ERROR)
        self.assertIsNone(result.assignment)
        self.assertIsNone(result.bound)
        self.assertIn("deliberate native failure", dict(result.audit)["exception_message"])


if __name__ == "__main__":
    unittest.main()
