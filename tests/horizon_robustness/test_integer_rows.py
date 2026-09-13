"""Equivalence controls for the exact integer-count restatement of the caps.

The restatement exists to stop a solver's float feasibility tolerance from
admitting a layout that violates the true share ceiling. It must not move the
feasible set by even one layout, so the central control here enumerates EVERY
storage-feasible layout of a small fixture and requires the integer rows and the
independent exact validator to agree on all of them.

Hand-worked fixtures only. No empirical data and no commercial solver run here.
"""

from fractions import Fraction
import itertools
import unittest
from unittest.mock import PropertyMock, patch

from Baselines.horizon_robustness.orders import complete_window
from Baselines.horizon_robustness.protocol import ContractError
from Baselines.horizon_robustness.schema import CatalogueManifest, Order, Scenario, TrainingProblem
from Baselines.horizon_robustness.uncertainty import build_training_problem, integer_cap_rows
from Baselines.horizon_robustness.validation import validate_assignment


def orders(*lines):
    return tuple(Order(f"ORD_{i + 1}", i + 1, tuple(line)) for i, line in enumerate(lines))


def satisfies_integer_rows(problem, assignment):
    """Evaluate the integer rows directly, exactly as a backend would build them."""
    rows, _ = integer_cap_rows(problem)
    inactive = set(problem.reference.inactive)
    for row in rows:
        scenario = problem.effective_scenarios[row["scenario"]]
        station = row["station"]
        left = row["multiplier"] * sum(count for p, count in scenario.counts
                                       if assignment[p] == station)
        if row["activation_coefficient"]:
            left += row["activation_coefficient"] * int(
                any(assignment[p] == station for p in inactive))
        if left > row["threshold"]:
            return False
    return True


def layouts(catalogue, fixed=()):
    """Every complete assignment that respects capacities and fixed products."""
    fixed = dict(fixed)
    for candidate in itertools.product(range(catalogue.s), repeat=catalogue.p):
        occupancy = [0] * catalogue.s
        for station in candidate:
            occupancy[station] += 1
        if tuple(occupancy) != tuple(catalogue.capacities):
            continue
        if any(candidate[p] != s for p, s in fixed.items()):
            continue
        yield candidate


class EquivalenceTests(unittest.TestCase):
    def setUp(self):
        self.catalogue = CatalogueManifest(
            "integer-rows-unit", "fixture", ("a", "b", "c", "d"), ("s0", "s1"), (2, 2),
            known_reference=(0, 1, 0, 1))
        # Chosen so the layout enumeration below is genuinely mixed: one of the
        # six storage-feasible layouts satisfies the robust rows and five do not.
        self.history = orders(
            ((1, 1), (2, 1)), ((0, 2), (1, 1)), ((0, 1),),
            ((2, 2), (3, 2)), ((1, 1), (2, 1), (3, 1)), ((2, 2),))

    def check_equivalence(self, problem, *, expect_some_feasible=True, expect_some_infeasible=True):
        feasible = infeasible = 0
        for assignment in layouts(self.catalogue, problem.reference.fixed):
            exact = validate_assignment(problem, assignment)["model_feasible_exact"]
            integer = satisfies_integer_rows(problem, assignment)
            self.assertEqual(exact, integer,
                             f"layout {assignment}: exact={exact} integer={integer}")
            feasible += bool(exact)
            infeasible += not exact
        if expect_some_feasible:
            self.assertGreater(feasible, 0, "fixture proves nothing if nothing is feasible")
        if expect_some_infeasible:
            self.assertGreater(infeasible, 0, "fixture proves nothing if nothing is rejected")
        return feasible, infeasible

    def problem(self, *, arm="HIST", delta="0.01", nu="0.01", n=2):
        return build_training_problem(self.catalogue, self.history, n, arm, delta, nu, "0.5")

    def test_all_four_arms_agree_with_the_exact_validator_on_every_layout(self):
        for arm in ("NOM", "TIGHT", "HIST", "HIST+ACT"):
            with self.subTest(arm=arm):
                self.check_equivalence(self.problem(arm=arm, delta="0.05"))

    def test_zero_slack_agrees(self):
        """delta = 0 makes every threshold exactly floor(b_s T_k)."""
        self.check_equivalence(self.problem(arm="HIST", delta="0"))

    def test_clipped_cap_agrees_and_is_trivially_satisfied(self):
        """delta = 1 clips every ceiling to 1, so no layout may be rejected."""
        problem = self.problem(arm="HIST", delta="1")
        rows, _ = integer_cap_rows(problem)
        for row in rows:
            scenario = problem.effective_scenarios[row["scenario"]]
            self.assertEqual(row["threshold"], scenario.total_lines * row["multiplier"]
                             if row["multiplier"] else row["threshold"])
        self.check_equivalence(problem, expect_some_infeasible=False)

    def test_thresholds_are_exact_floors_not_rounded_values(self):
        problem = self.problem(arm="HIST", delta="0.01")
        caps = problem.rational_caps(optimization=True)
        rows, _ = integer_cap_rows(problem)
        for row in rows:
            scenario = problem.effective_scenarios[row["scenario"]]
            exact = caps[row["station"]] * scenario.total_lines
            self.assertEqual(row["threshold"], int(exact.numerator // exact.denominator))
            self.assertLessEqual(Fraction(row["threshold"]), exact)
            self.assertGreater(Fraction(row["threshold"]) + 1, exact)


class ActivationTests(unittest.TestCase):
    """Fixtures whose inactive set is NON-empty, so activation rows exist."""

    def setUp(self):
        # Product 'd' is never ordered, so Z_H = {3} and activation rows exist.
        # Mixed by construction: one of six layouts satisfies the robust rows.
        self.catalogue = CatalogueManifest(
            "integer-activation-unit", "fixture", ("a", "b", "c", "d"), ("s0", "s1"), (2, 2),
            known_reference=(0, 1, 0, 1))
        self.history = orders(
            ((0, 2), (1, 2), (2, 2)), ((0, 2), (1, 1)), ((0, 2), (2, 2)),
            ((0, 1), (1, 2), (2, 1)), ((0, 2), (1, 2), (2, 1)), ((0, 2),))

    def problem(self, nu, delta="0.05"):
        return build_training_problem(self.catalogue, self.history, 2, "HIST+ACT", delta, nu, "0.5")

    def test_inactive_set_is_actually_non_empty(self):
        problem = self.problem("0.01")
        self.assertEqual(problem.reference.inactive, (3,))
        rows, effective = integer_cap_rows(problem)
        self.assertEqual(effective, Fraction(1, 100))
        self.assertTrue(any(r["kind"] == "activation" for r in rows))

    def test_activation_rows_agree_with_the_exact_validator(self):
        """Equivalence at every nu, plus the monotonicity nu implies.

        A larger activation budget can only shrink the feasible set, so the
        accepted layouts must be nested as nu grows. That is a stronger control
        than demanding a mixed outcome at every single nu, and it does not break
        when a large nu legitimately admits nothing.
        """
        accepted = {}
        for nu in ("0", "0.0025", "0.01", "0.05"):
            with self.subTest(nu=nu):
                problem = self.problem(nu)
                keep = set()
                for assignment in layouts(self.catalogue, problem.reference.fixed):
                    exact = validate_assignment(problem, assignment)["model_feasible_exact"]
                    self.assertEqual(exact, satisfies_integer_rows(problem, assignment),
                                     f"nu={nu} layout={assignment}")
                    if exact:
                        keep.add(assignment)
                accepted[nu] = keep
        self.assertTrue(accepted["0"], "fixture must accept something at nu = 0")
        self.assertTrue(any(len(v) < len(accepted["0"]) for v in accepted.values()),
                        "fixture must also reject something, or it proves nothing")
        for smaller, larger in (("0", "0.0025"), ("0.0025", "0.01"), ("0.01", "0.05")):
            self.assertTrue(accepted[larger] <= accepted[smaller],
                            f"raising nu from {smaller} to {larger} admitted a new layout")

    def test_nu_zero_produces_no_activation_row(self):
        rows, effective = integer_cap_rows(self.problem("0"))
        self.assertEqual(effective, Fraction(0))
        self.assertEqual([r for r in rows if r["kind"] == "activation"], [])

    def test_nu_one_forces_the_inactive_station_below_a_sub_unit_ceiling(self):
        """At nu = 1 all future mass may activate, so h_s must vanish unless u_s = 1."""
        problem = self.problem("1", delta="0.05")
        rows, effective = integer_cap_rows(problem)
        self.assertEqual(effective, Fraction(1))
        activation = [r for r in rows if r["kind"] == "activation"]
        self.assertTrue(activation)
        for row in activation:
            scenario = problem.effective_scenarios[row["scenario"]]
            self.assertEqual(row["multiplier"], 0)              # (M-N) = 0
            self.assertEqual(row["activation_coefficient"], scenario.total_lines)
        for assignment in layouts(self.catalogue, problem.reference.fixed):
            exact = validate_assignment(problem, assignment)["model_feasible_exact"]
            self.assertEqual(exact, satisfies_integer_rows(problem, assignment), str(assignment))

    def test_empty_inactive_set_collapses_activation_to_the_base_rows(self):
        """With Z_H empty, HIST+ACT must reduce exactly to HIST at every nu."""
        catalogue = CatalogueManifest(
            "integer-dense-unit", "fixture", ("a", "b", "c", "d"), ("s0", "s1"), (2, 2),
            known_reference=(0, 1, 0, 1))
        history = orders(((0, 1), (1, 1)), ((2, 1), (3, 1)), ((0, 1), (2, 1)),
                         ((1, 1), (3, 1)), ((0, 1), (3, 1)), ((1, 1), (2, 1)))
        activated = build_training_problem(catalogue, history, 2, "HIST+ACT", "0.05", "0.05", "0.5")
        historical = build_training_problem(catalogue, history, 2, "HIST", "0.05", "0.05", "0.5")
        self.assertEqual(activated.reference.inactive, ())
        self.assertEqual(integer_cap_rows(activated)[0], integer_cap_rows(historical)[0])
        self.assertEqual(activated.model_hash, historical.model_hash)


class RangeSafetyTests(unittest.TestCase):
    def test_row_reports_its_own_worst_case_left_side(self):
        catalogue = CatalogueManifest(
            "integer-range-unit", "fixture", ("a", "b", "c", "d"), ("s0", "s1"), (2, 2),
            known_reference=(0, 1, 0, 1))
        history = orders(((0, 5),), ((1, 3),), ((0, 2),), ((1, 4),), ((0, 1),), ((1, 6),))
        problem = build_training_problem(catalogue, history, 2, "HIST", "0.01", "0.01", "0.5")
        rows, _ = integer_cap_rows(problem)
        for row in rows:
            scenario = problem.effective_scenarios[row["scenario"]]
            worst = row["multiplier"] * scenario.total_lines + row["activation_coefficient"]
            self.assertLessEqual(worst, row["maximum_left_side"])
            self.assertLess(row["maximum_left_side"], 2 ** 63)

    def test_overflowing_scenario_is_refused_not_silently_emitted(self):
        """A row whose left side could not fit int64 must raise, not be emitted."""
        catalogue = CatalogueManifest(
            "integer-overflow-unit", "fixture", ("a", "b", "c", "d"), ("s0", "s1"), (2, 2),
            known_reference=(0, 1, 0, 1))
        history = orders(((0, 1), (1, 1)), ((2, 1),), ((0, 1),), ((1, 1), (2, 1)),
                         ((0, 1),), ((1, 1), (2, 1)))
        problem = build_training_problem(catalogue, history, 2, "HIST+ACT", "0.01", "0.01", "0.5")
        enormous = (Scenario(counts=((0, 2 ** 62),), total_lines=2 ** 62, start=0, stop=1),)
        with patch.object(type(problem), "effective_scenarios",
                          new_callable=PropertyMock, return_value=enormous):
            with self.assertRaisesRegex(ContractError, "NUMERICAL_RANGE"):
                integer_cap_rows(problem)

    def test_a_representable_scenario_is_accepted(self):
        """Positive control: the guard must not reject an ordinary large model."""
        catalogue = CatalogueManifest(
            "integer-large-unit", "fixture", ("a", "b", "c", "d"), ("s0", "s1"), (2, 2),
            known_reference=(0, 1, 0, 1))
        history = orders(((0, 1), (1, 1)), ((2, 1),), ((0, 1),), ((1, 1), (2, 1)),
                         ((0, 1),), ((1, 1), (2, 1)))
        problem = build_training_problem(catalogue, history, 2, "HIST+ACT", "0.01", "0.01", "0.5")
        big = (Scenario(counts=((0, 10 ** 12),), total_lines=10 ** 12, start=0, stop=1),)
        with patch.object(type(problem), "effective_scenarios",
                          new_callable=PropertyMock, return_value=big):
            rows, _ = integer_cap_rows(problem)
        self.assertTrue(rows)
        self.assertTrue(all(row["maximum_left_side"] < 2 ** 63 for row in rows))


if __name__ == "__main__":
    unittest.main()
