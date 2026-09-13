"""Hexaly under the two-sided rule: a tiny native solve, validated two-sided.

Runs in the Hexaly environment only. The fixture is small enough to enumerate,
so the returned objective is checked against the exact two-sided optimum, and
the integer lower rows must reach the native model as integer-typed rows just
as the upper rows do.
"""

from fractions import Fraction
import itertools
import json
import unittest

from Baselines.horizon_robustness.schema import CatalogueManifest, Order
from Baselines.horizon_robustness.uncertainty import build_training_problem
from Baselines.horizon_robustness.validation import validate_assignment


def orders(*lines):
    return tuple(Order(f"ORD_{i + 1}", i + 1, tuple(line)) for i, line in enumerate(lines))


def layouts(catalogue, fixed=()):
    fixed = dict(fixed)
    for candidate in itertools.product(range(catalogue.s), repeat=catalogue.p):
        occupancy = [0] * catalogue.s
        for station in candidate:
            occupancy[station] += 1
        if tuple(occupancy) == tuple(catalogue.capacities) and all(candidate[p] == s for p, s in fixed.items()):
            yield candidate


class HexalyTwoSidedTests(unittest.TestCase):
    def setUp(self):
        self.catalogue = CatalogueManifest("integer-rows-unit", "fixture", ("a", "b", "c", "d"),
                                           ("s0", "s1"), (2, 2), known_reference=(0, 1, 0, 1))
        self.history = orders(((1, 1), (2, 1)), ((0, 2), (1, 1)), ((0, 1),),
                              ((2, 2), (3, 2)), ((1, 1), (2, 1), (3, 1)), ((2, 2),))

    def test_two_sided_visits_solve_matches_enumeration_and_validates_two_sided(self):
        from Baselines.horizon_robustness import hexaly_backend
        problem = build_training_problem(self.catalogue, self.history, 2, "HIST", "0.35", "0.01", "0.5",
                                         rule="two_sided")
        feasible = {a: validate_assignment(problem, a)["actual_visit_count"]
                    for a in layouts(self.catalogue, problem.reference.fixed)
                    if validate_assignment(problem, a)["model_feasible_exact"]}
        self.assertTrue(feasible, "fixture must admit a two-sided feasible layout")
        result = hexaly_backend.solve(problem, seed=11, threads=1, time_limit=5)
        self.assertIn(result.status.value, ("FEASIBLE", "OPTIMAL_WITHIN_TOLERANCE"), dict(result.audit))
        self.assertIn(result.assignment, feasible)
        self.assertEqual(result.objective, min(feasible.values()))
        audit = dict(result.audit)
        self.assertEqual(audit["row_formulation"], "exact_integer_counts_v3")
        built, total = audit["integer_typed_rows"].split("/")
        self.assertEqual(built, total)
        # Lower rows doubled the row count relative to the upper-only model.
        upper = build_training_problem(self.catalogue, self.history, 2, "HIST", "0.35", "0.01", "0.5")
        upper_rows = int(dict(hexaly_backend.solve(upper, seed=11, threads=1, time_limit=2).audit)["finite_row_count"])
        self.assertEqual(int(audit["finite_row_count"]), 2 * upper_rows)
        certificate = json.loads(audit["validation"])
        self.assertTrue(certificate["valid"])
        self.assertEqual(certificate["rule"], "two_sided")

    def test_two_sided_min_slack_covers_both_sides(self):
        from Baselines.horizon_robustness import hexaly_backend
        problem = build_training_problem(self.catalogue, self.history, 2, "HIST", "0.01", "0.01", "0.5",
                                         rule="two_sided")
        best = min(Fraction(validate_assignment(problem, a)["minimum_required_slack_exact"])
                   for a in layouts(self.catalogue, problem.reference.fixed))
        result = hexaly_backend.solve(problem, seed=11, threads=1, time_limit=5, solve_mode="min_slack")
        self.assertIn(result.status.value, ("FEASIBLE", "OPTIMAL_WITHIN_TOLERANCE"), dict(result.audit))
        self.assertAlmostEqual(result.objective, float(best), delta=1e-8)
        certificate = validate_assignment(problem, result.assignment, objective=result.objective,
                                          solve_mode="min_slack", min_slack=result.objective)
        self.assertTrue(certificate["valid"], certificate["violations"])
        self.assertEqual(certificate["rule"], "two_sided")

    def test_trapped_activation_is_admitted_natively(self):
        from Baselines.horizon_robustness import hexaly_backend
        from tests.horizon_robustness.test_two_sided import reviewer_fixture
        catalogue, history = reviewer_fixture()
        problem = build_training_problem(catalogue, history, 2, "HIST+ACT", "0.01", "0.05", "0.5",
                                         rule="two_sided")
        feasible = {a: validate_assignment(problem, a)["actual_visit_count"]
                    for a in layouts(catalogue, problem.reference.fixed)
                    if validate_assignment(problem, a)["model_feasible_exact"]}
        self.assertIn((0, 1, 1, 0), feasible)
        result = hexaly_backend.solve(problem, seed=11, threads=1, time_limit=5)
        self.assertIn(result.status.value, ("FEASIBLE", "OPTIMAL_WITHIN_TOLERANCE"), dict(result.audit))
        self.assertIn(result.assignment, feasible)
        self.assertEqual(result.objective, min(feasible.values()))
        audit = dict(result.audit)
        self.assertEqual(audit["row_formulation"], "exact_integer_counts_v3")
        built, total = audit["integer_typed_rows"].split("/")
        self.assertEqual(built, total)

    def test_min_slack_with_activation_matches_enumeration_on_both_sides(self):
        from Baselines.horizon_robustness import hexaly_backend
        from tests.horizon_robustness.test_two_sided import sparse_fixture, two_inactive_fixture
        for catalogue, history in (sparse_fixture(), two_inactive_fixture()):
            problem = build_training_problem(catalogue, history, 2, "HIST+ACT", "0.01", "0.05", "0.5",
                                             rule="two_sided")
            best = min(Fraction(validate_assignment(problem, a)["minimum_required_slack_exact"])
                       for a in layouts(catalogue, problem.reference.fixed))
            result = hexaly_backend.solve(problem, seed=11, threads=1, time_limit=5, solve_mode="min_slack")
            self.assertIn(result.status.value, ("FEASIBLE", "OPTIMAL_WITHIN_TOLERANCE"), dict(result.audit))
            self.assertAlmostEqual(result.objective, float(best), delta=1e-7)
            certificate = validate_assignment(problem, result.assignment, objective=result.objective,
                                              solve_mode="min_slack", min_slack=result.objective)
            self.assertTrue(certificate["valid"], certificate["violations"])

    def test_tightened_scenario_arm_solves_natively_and_matches_enumeration(self):
        from Baselines.horizon_robustness import hexaly_backend
        from tests.horizon_robustness.test_two_sided import sparse_fixture
        catalogue, history = sparse_fixture()
        problem = build_training_problem(catalogue, history, 2, "HIST+ACT-T", "0.3", "0.05", "0.5", rule="two_sided")
        feasible = {a: validate_assignment(problem, a)["actual_visit_count"]
                    for a in layouts(catalogue, problem.reference.fixed)
                    if validate_assignment(problem, a)["model_feasible_exact"]}
        self.assertTrue(feasible)
        result = hexaly_backend.solve(problem, seed=11, threads=1, time_limit=5)
        self.assertIn(result.status.value, ("FEASIBLE", "OPTIMAL_WITHIN_TOLERANCE"), dict(result.audit))
        self.assertIn(result.assignment, feasible)
        self.assertEqual(result.objective, min(feasible.values()))


if __name__ == "__main__":
    unittest.main()
