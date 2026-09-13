"""Hand-worked software fixtures only; no empirical or commercial-solver runs."""

from dataclasses import replace
from fractions import Fraction
import itertools
import json
import unittest

from Baselines.horizon_robustness.orders import complete_window, history_hash
from Baselines.horizon_robustness.protocol import ContractError, Protocol
from Baselines.horizon_robustness.reference import build_reference
from Baselines.horizon_robustness.schema import CatalogueManifest, Order, TrainingProblem
from Baselines.horizon_robustness.uncertainty import (
    build_training_problem, historical_activation_diagnostics, make_scenarios,
    minimum_slack_for_assignment, worst_shares,
)


def orders(*lines):
    return tuple(Order(f"ORD_{i + 1}", i + 1, tuple(line)) for i, line in enumerate(lines))


def dense_shares(scenario, p):
    counts = dict(scenario.counts)
    return tuple(Fraction(counts.get(i, 0), scenario.total_lines) for i in range(p))


class UncertaintyTest(unittest.TestCase):
    def setUp(self):
        self.catalogue = CatalogueManifest(
            "uncertainty-unit", "fixture", ("a", "b", "c", "d"), ("s0", "s1"), (2, 2),
            known_reference=(0, 1, 0, 1))
        self.history = orders(
            ((0, 2),), ((1, 1),), ((0, 1),), ((1, 2),), ((0, 1), (1, 1)), ((1, 2),))

    def test_exact_right_aligned_indices_and_whole_history_remainder(self):
        history = orders(*(((0, i),) for i in range(1, 8)))
        scenarios = make_scenarios(history, 4, 2)
        self.assertEqual(tuple((v.start, v.stop, v.label) for v in scenarios),
                         ((1, 3, "block"), (3, 5, "block"), (5, 7, "block"), (0, 7, "history")))
        self.assertEqual(tuple(v.counts for v in scenarios),
                         (((0, 5),), ((0, 9),), ((0, 13),), ((0, 28),)))
        self.assertEqual(tuple(v.total_lines for v in scenarios), (5, 9, 13, 28))
        covered = [i for v in scenarios[:-1] for i in range(v.start, v.stop)]
        self.assertEqual(covered, list(range(1, 7)))

    def test_scenarios_conserve_lines_and_full_catalogue_shares(self):
        problem = build_training_problem(self.catalogue, self.history, 2)
        self.assertEqual(problem.reference.historical_counts, (4, 6, 0, 0))
        self.assertEqual(problem.reference.inactive, (2, 3))
        self.assertEqual(problem.reference.assignment, (0, 1, 0, 1))
        for scenario in problem.scenarios:
            shares = dense_shares(scenario, self.catalogue.p)
            self.assertEqual(sum(shares), 1)
            self.assertEqual(shares[2:], (0, 0))
            station_shares = [sum(shares[p] for p, s in enumerate(problem.reference.assignment) if s == station)
                              for station in range(self.catalogue.s)]
            self.assertEqual(sum(station_shares), 1)
        self.assertEqual(problem.scenarios[-1], problem.nominal_scenario)
        self.assertEqual(TrainingProblem.from_dict(json.loads(json.dumps(problem.to_dict()))), problem)

    def test_insufficient_history_is_explicit_for_every_arm(self):
        for length in (0, 1, 4, 5):
            history = self.history[:length]
            with self.subTest(length=length), self.assertRaisesRegex(ContractError, "INSUFFICIENT_HISTORY"):
                make_scenarios(history, 4, 2)
            for arm in ("NOM", "TIGHT", "HIST", "HIST+ACT"):
                with self.subTest(length=length, arm=arm), self.assertRaisesRegex(ContractError, "INSUFFICIENT_HISTORY"):
                    build_training_problem(self.catalogue, history, 2, arm=arm)
        self.assertEqual(len(make_scenarios(self.history, 4, 2)), 4)
        self.assertEqual(len(make_scenarios(self.history[:3], 4, 1)), 4)

    def test_invalid_histories_and_horizons_are_rejected_without_repair(self):
        for p, n in ((0, 2), (-1, 2), (True, 2), (4.0, 2), (4, 0), (4, -2), (4, True), (4, 1.5)):
            for function in (make_scenarios, historical_activation_diagnostics):
                with self.subTest(p=p, n=n, function=function.__name__), self.assertRaises(ContractError):
                    function(self.history, p, n)
        invalid = (list(self.history), self.history[::-1], (object(),),
                   (self.history[0], self.history[0], self.history[2]),
                   (self.history[0], replace(self.history[1], order_id="ORD_1"), self.history[2]))
        for history in invalid:
            for function in (make_scenarios, historical_activation_diagnostics):
                with self.subTest(history=history, function=function.__name__), self.assertRaises(ContractError):
                    function(history, 4, 1)
        unknown = self.history[:-1] + (replace(self.history[-1], lines=((4, 1),)),)
        for function in (make_scenarios, historical_activation_diagnostics):
            with self.assertRaisesRegex(ContractError, "OUT_OF_CATALOGUE"):
                function(unknown, 4, 2)

    def test_every_support_and_order_weight_survives_including_small_fixed_orders(self):
        catalogue = replace(self.catalogue, exogenous_fixed=((0, 0),))
        history = orders(((0, 20), (1, 1)), ((0, 1), (1, 7)), ((2, 1),),
                         ((1, 1), (2, 1)), ((0, 2),), ((0, 1), (1, 1), (2, 1)), ((3, 1),))
        problem = build_training_problem(catalogue, history, 2)
        self.assertEqual(problem.weighted_supports,
                         (((0,), 1), ((0, 1), 2), ((0, 1, 2), 1), ((1, 2), 1), ((2,), 1), ((3,), 1)))
        self.assertEqual(sum(w for support, w in problem.weighted_supports), 7)
        direct_visits = sum(len({problem.reference.assignment[p] for p, count in o.lines}) for o in history)
        weighted_visits = sum(w * len({problem.reference.assignment[p] for p in support})
                              for support, w in problem.weighted_supports)
        self.assertEqual(weighted_visits, direct_visits)
        self.assertEqual(problem.reference.historical_counts, (24, 10, 3, 1))
        self.assertEqual(problem.reference.fixed, ((0, 0),))

    def test_pooled_target_is_line_weighted_and_includes_leading_remainder(self):
        history = orders(((0, 100),), *((((0, 1),), ((1, 1),)) * 3))
        problem = build_training_problem(self.catalogue, history, 2)
        self.assertEqual(problem.reference.historical_counts, (103, 3, 0, 0))
        self.assertEqual(problem.reference.b, (103 / 106, 3 / 106))
        self.assertEqual(problem.scenarios[0].counts, ((0, 1), (1, 1)))
        self.assertNotAlmostEqual(problem.reference.b[0], 0.5)
        self.assertEqual(problem.weighted_supports, (((0,), 4), ((1,), 3)))
        self.assertEqual(worst_shares(replace(problem, arm="HIST"), (0, 1, 0, 1)), (103 / 106, 0.5))

    def test_reference_reuse_matches_exact_prefix_and_rejects_stale_metadata(self):
        reference = build_reference(self.catalogue, self.history)
        problem = build_training_problem(self.catalogue, self.history, 2, reference=reference)
        self.assertIs(problem.reference, reference)
        bad = (replace(reference, origin=5), replace(reference, history_hash="0" * 64),
               replace(reference, historical_counts=(5, 5, 0, 0)), object())
        for value in bad:
            with self.subTest(value=value), self.assertRaises(ContractError):
                build_training_problem(self.catalogue, self.history, 2, reference=value)
        changed_observations = (replace(self.history[0], observations=((0, 1),)),) + self.history[1:]
        with self.assertRaisesRegex(ContractError, "exact historical prefix"):
            build_training_problem(self.catalogue, changed_observations, 2, reference=reference)

    def test_known_finite_counterpart_and_nu_endpoints(self):
        assignment = (0, 1, 0, 1)
        problem = build_training_problem(self.catalogue, self.history, 2, nu="0.25")
        # Block shares for station 0 are 2/3, 1/3, 1/4; pooled share is 2/5.
        self.assertEqual(worst_shares(problem, assignment), (0.75, 0.8125))
        self.assertEqual(worst_shares(replace(problem, nu="0"), assignment), (2 / 3, 0.75))
        self.assertEqual(worst_shares(replace(problem, nu="1"), assignment), (1.0, 1.0))
        hist = replace(problem, arm="HIST")
        self.assertEqual(worst_shares(hist, assignment), worst_shares(replace(problem, nu="0"), assignment))
        self.assertEqual(hist.model_hash, replace(problem, nu="0").model_hash)
        self.assertGreater(sum(worst_shares(problem, assignment)), 1)

    def test_station_without_inactive_product_keeps_unperturbed_endpoint(self):
        problem = build_training_problem(self.catalogue, self.history, 2, nu="0.25")
        assignment = (0, 0, 1, 1)
        self.assertEqual(worst_shares(problem, assignment), (1.0, 0.25))
        self.assertEqual(worst_shares(replace(problem, nu="1"), assignment), (1.0, 1.0))

    def test_empty_inactive_set_reduces_to_history_even_at_nu_one(self):
        history = orders(*(tuple((p, p + 1) for p in range(4)) for _ in range(6)))
        problem = build_training_problem(self.catalogue, history, 2, nu="1")
        hist = replace(problem, arm="HIST")
        self.assertEqual(problem.reference.inactive, ())
        self.assertEqual(problem.effective_nu, 0)
        self.assertEqual(problem.model_hash, hist.model_hash)
        self.assertEqual(worst_shares(problem, problem.reference.assignment), (0.4, 0.6))

    def test_mixture_conservation_and_endpoint_vertex_enumeration(self):
        assignments = [a for a in itertools.product(range(2), repeat=4) if a.count(0) == 2]
        for nu_text in ("0", "0.01", "0.5", "1"):
            problem = build_training_problem(self.catalogue, self.history, 2, nu=nu_text)
            nu = Fraction(nu_text)
            qs = [dense_shares(scenario, 4) for scenario in problem.scenarios]
            mixtures = []
            # Vertex activation and a convex mixture provide explicit feasible q.
            for q in qs + [tuple((a + b) / 2 for a, b in zip(qs[0], qs[-1]))]:
                for a in (Fraction(0), nu / 2, nu):
                    for activated in problem.reference.inactive:
                        mixed = tuple((1 - a) * value + (a if p == activated else 0)
                                      for p, value in enumerate(q))
                        self.assertEqual(sum(mixed), 1)
                        self.assertTrue(all(value >= 0 for value in mixed))
                        mixtures.append(mixed)
            for assignment in assignments:
                expected = tuple(float(max(sum(q[p] for p in range(4) if assignment[p] == s)
                                           for q in mixtures)) for s in range(2))
                with self.subTest(nu=nu_text, assignment=assignment):
                    self.assertEqual(worst_shares(problem, assignment), expected)

    def test_fixed_inactive_zero_target_station_can_force_overload(self):
        catalogue = replace(self.catalogue, known_reference=(0, 0, 1, 1), exogenous_fixed=((2, 1), (3, 1)))
        problem = build_training_problem(catalogue, self.history, 2, nu="0.02")
        self.assertEqual(problem.reference.b, (1, 0))
        self.assertEqual(problem.scoring_caps, (1, 0.01))
        self.assertEqual(worst_shares(problem, problem.reference.assignment), (1, 0.02))
        self.assertEqual(minimum_slack_for_assignment(problem, problem.reference.assignment), 0.02)
        with self.assertRaises(ContractError):
            worst_shares(problem, (0, 1, 0, 1))

    def test_fixed_h_equals_station_specific_tightened_caps(self):
        layouts = ((0, 1, 0, 1), (0, 0, 1, 1))
        feasible = []
        for assignment in layouts:
            catalogue = replace(self.catalogue, known_reference=assignment,
                                exogenous_fixed=tuple((p, assignment[p]) for p in (2, 3)))
            for nu_text, delta in itertools.product(("0", "0.01", "0.25", "0.9"), ("0", "0.01", "0.3", "1")):
                problem = build_training_problem(catalogue, self.history, 2, nu=nu_text, delta=delta)
                nu = Fraction(nu_text)
                caps = problem.rational_caps()
                h = tuple(int(any(assignment[p] == s for p in (2, 3))) for s in range(2))
                tightened = tuple(min(u, (u - nu * present) / (1 - nu)) for u, present in zip(caps, h))
                reduced = all(sum(Fraction(count, scenario.total_lines) for p, count in scenario.counts
                                  if assignment[p] == s) <= tightened[s]
                              for scenario in problem.scenarios for s in range(2))
                counterpart = all(value <= float(cap) for value, cap in zip(worst_shares(problem, assignment), caps))
                self.assertEqual(reduced, counterpart)
                feasible.append(reduced)
        self.assertIn(True, feasible)
        self.assertIn(False, feasible)

    def test_minimum_slack_is_absolute_allowance_not_remaining_cap_excess(self):
        problem = build_training_problem(self.catalogue, self.history, 2, nu="0.25", delta="0.5")
        before = problem.to_dict()
        # max(3/4 - 2/5, 13/16 - 3/5) = 7/20.
        self.assertEqual(minimum_slack_for_assignment(problem, problem.reference.assignment), 0.35)
        for delta in ("0", "0.01", "1"):
            self.assertEqual(minimum_slack_for_assignment(replace(problem, delta=delta), problem.reference.assignment), 0.35)
        self.assertEqual(problem.to_dict(), before)
        nominal = replace(problem, arm="NOM")
        self.assertEqual(minimum_slack_for_assignment(nominal, nominal.reference.assignment), 0)
        tight = replace(nominal, arm="TIGHT", tightening="1")
        self.assertEqual(minimum_slack_for_assignment(tight, tight.reference.assignment), 0)

    def test_slack_retains_sub_float_residuals(self):
        history = orders(*(((0, 1), (1, 1)) for _ in range(3)))
        problem = build_training_problem(self.catalogue, history, 1, nu="0.00000000000000000001")
        self.assertEqual(worst_shares(problem, problem.reference.assignment), (0.5, 0.5))
        self.assertEqual(minimum_slack_for_assignment(problem, problem.reference.assignment), 5e-21)

    def test_proportional_line_scaling_preserves_envelope_and_slack(self):
        problem = build_training_problem(self.catalogue, self.history, 2)
        scaled_history = tuple(replace(o, lines=tuple((p, 1234567 * count) for p, count in o.lines))
                               for o in self.history)
        scaled = build_training_problem(self.catalogue, scaled_history, 2)
        self.assertEqual(scaled.reference.b, problem.reference.b)
        self.assertEqual(scaled.scoring_caps, problem.scoring_caps)
        self.assertEqual(scaled.weighted_supports, problem.weighted_supports)
        self.assertEqual(worst_shares(scaled, scaled.reference.assignment),
                         worst_shares(problem, problem.reference.assignment))
        self.assertEqual(minimum_slack_for_assignment(scaled, scaled.reference.assignment),
                         minimum_slack_for_assignment(problem, problem.reference.assignment))

    def test_one_and_three_station_catalogues(self):
        single = CatalogueManifest("single-unit", "fixture", ("a", "b"), ("s0",), (2,))
        history = orders(*(((0, 1),) for _ in range(3)))
        for nu in ("0", "0.01", "1"):
            problem = build_training_problem(single, history, 1, nu=nu)
            self.assertEqual(worst_shares(problem, (0, 0)), (1,))
            self.assertEqual(minimum_slack_for_assignment(problem, (0, 0)), 0)
        triple = CatalogueManifest("triple-unit", "fixture", tuple("abcdef"), ("s0", "s1", "s2"),
                                   (2, 2, 2), known_reference=(0, 1, 2, 0, 1, 2))
        history = orders(((0, 2), (1, 1)), ((1, 2), (2, 1)), ((0, 1), (2, 2)))
        problem = build_training_problem(triple, history, 1, nu="0.25")
        self.assertEqual(worst_shares(problem, problem.reference.assignment), (0.75, 0.75, 0.75))
        self.assertEqual(minimum_slack_for_assignment(problem, problem.reference.assignment), 5 / 12)

    def test_assignment_contracts_include_all_zero_demand_products(self):
        problem = build_training_problem(self.catalogue, self.history, 2)
        for assignment in ((0, 1), (0, 1, 0, None), (0, 1, 0, 2), (0, 0, 0, 1), [0, 1, 0, 1]):
            for function in (worst_shares, minimum_slack_for_assignment):
                with self.subTest(assignment=assignment, function=function.__name__), self.assertRaises(ContractError):
                    function(problem, assignment)

    def test_arms_horizons_and_stress_share_scoring_caps_without_tuning(self):
        reference = build_reference(self.catalogue, self.history)
        problems = [build_training_problem(self.catalogue, self.history, n, arm=arm, reference=reference)
                    for n, arm in itertools.product((1, 2), ("NOM", "TIGHT", "HIST", "HIST+ACT"))]
        for problem in problems:
            self.assertIs(problem.reference, reference)
            self.assertEqual(problem.scoring_caps, (0.41, 0.61))
            self.assertEqual(problem.weighted_supports, problems[0].weighted_supports)
        for arm in ("NOM", "TIGHT"):
            matching = [problem for problem in problems if problem.arm == arm]
            self.assertEqual(matching[0].model_hash, matching[1].model_hash)
            self.assertNotEqual(matching[0].input_hash, matching[1].input_hash)
            self.assertEqual(worst_shares(matching[0], reference.assignment), reference.b)
        tight = next(problem for problem in problems if problem.arm == "TIGHT")
        self.assertEqual(tight.optimization_caps, (0.405, 0.605))
        self.assertEqual(replace(tight, tightening="0").model_hash, problems[0].model_hash)
        robust = problems[-1]
        stressed = replace(robust, nu="0.2")
        relaxed = replace(robust, delta="0.2")
        self.assertEqual(stressed.scoring_caps, robust.scoring_caps)
        self.assertNotEqual(stressed.model_hash, robust.model_hash)
        self.assertEqual(worst_shares(relaxed, reference.assignment), worst_shares(robust, reference.assignment))
        self.assertEqual(relaxed.effective_nu, robust.effective_nu)
        self.assertEqual(relaxed.scenarios, robust.scenarios)
        self.assertNotEqual(relaxed.scoring_caps, robust.scoring_caps)
        self.assertEqual((robust.delta, robust.nu), ("0.01", "0.01"))

    def test_invalid_policy_parameters_fail_instead_of_being_clipped_or_fitted(self):
        for name in ("delta", "nu", "tightening"):
            for value in ("-0.1", "1.1", "NaN", "Infinity", 0.01):
                with self.subTest(name=name, value=value), self.assertRaises(ContractError):
                    build_training_problem(self.catalogue, self.history, 2, **{name: value})

    def test_historical_diagnostics_use_only_eligible_same_grid_cuts_and_prefix_zeros(self):
        history = orders(((3, 1),), *(((0, 1),) for _ in range(6)),
                         ((0, 1), (1, 3)), ((1, 1),), ((1, 1), (2, 2)), ((0, 2),))
        diagnostics = historical_activation_diagnostics(history, 5, 2)
        self.assertEqual(tuple((v["cut"], v["next_start"], v["next_stop"]) for v in diagnostics),
                         ((7, 7, 9), (9, 9, 11)))
        self.assertEqual(tuple(v["prior_complete_blocks"] for v in diagnostics), (3, 4))
        self.assertEqual(diagnostics[0]["inactive_products"], [1, 2, 4])
        self.assertEqual(diagnostics[1]["inactive_products"], [2, 4])
        self.assertEqual(diagnostics[0]["activated_products"], [1])
        self.assertEqual(diagnostics[1]["activated_products"], [2])
        self.assertEqual(tuple(v["activation_lines"] for v in diagnostics), (4, 2))
        self.assertEqual(tuple(v["activation_mass"] for v in diagnostics), (0.8, 0.4))
        for record in diagnostics:
            self.assertTrue(record["exceeds_primary_nu"])
            self.assertEqual(record["product_count"], 5)
            self.assertTrue(record["sparse_history"])
            self.assertEqual(record["nu_exceedances"], {nu: True for nu in Protocol().nus})
        self.assertEqual(json.loads(json.dumps(diagnostics, allow_nan=False)), list(diagnostics))

    def test_diagnostics_no_eligible_cuts_zero_activation_and_empty_inactive_set(self):
        for length in (0, 1, 5, 6, 7):
            history = orders(*(((0, 1),) for _ in range(length)))
            self.assertEqual(historical_activation_diagnostics(history, 4, 2), ())
        history = orders(*(((0, 1),) for _ in range(8)))
        record, = historical_activation_diagnostics(history, 4, 2)
        self.assertEqual(record["inactive_products"], [1, 2, 3])
        self.assertEqual(record["activated_products"], [])
        self.assertEqual(record["activation_mass"], 0)
        self.assertFalse(record["exceeds_primary_nu"])
        self.assertFalse(any(record["nu_exceedances"].values()))
        complete = orders(*(tuple((p, 1) for p in range(4)) for _ in range(8)))
        record, = historical_activation_diagnostics(complete, 4, 2)
        self.assertEqual(record["inactive_products"], [])
        self.assertEqual(record["activation_lines"], 0)

    def test_diagnostic_grid_comparisons_are_strict_exact_and_do_not_tune(self):
        history = orders(*(((0, 1),) for _ in range(6)), ((0, 98), (2, 1)), ((0, 1),))
        record, = historical_activation_diagnostics(history, 4, 2)
        self.assertEqual(record["activation_mass"], 0.01)
        self.assertFalse(record["exceeds_primary_nu"])
        self.assertTrue(record["nu_exceedances"]["0.005"])
        self.assertFalse(record["nu_exceedances"]["0.01"])
        problem = build_training_problem(self.catalogue, history, 2)
        excessive = orders(*(((0, 1),) for _ in range(6)), ((2, 99),), ((2, 1),))
        excessive_record, = historical_activation_diagnostics(excessive, 4, 2)
        self.assertTrue(excessive_record["exceeds_primary_nu"])
        unchanged_policy = build_training_problem(self.catalogue, excessive, 2)
        self.assertEqual((problem.delta, problem.nu), (unchanged_policy.delta, unchanged_policy.nu))

    def test_future_demand_and_station_mutations_cannot_change_training_or_diagnostics(self):
        history = orders(*(((0, 1), (1, 2)) for _ in range(8)))
        future_a = history + (Order("ORD_9", 9, ((2, 100),), ((2, 0),)),)
        future_b = history + (Order("ORD_9", 9, ((3, 10000),), ((3, 1),)),)
        prefix_a = complete_window(future_a, 0, 8)
        prefix_b = complete_window(future_b, 0, 8)
        problem_a = build_training_problem(self.catalogue, prefix_a, 2)
        problem_b = build_training_problem(self.catalogue, prefix_b, 2)
        self.assertEqual(problem_a, problem_b)
        self.assertEqual(problem_a.input_hash, problem_b.input_hash)
        self.assertEqual(problem_a.model_hash, problem_b.model_hash)
        self.assertEqual(historical_activation_diagnostics(prefix_a, 4, 2),
                         historical_activation_diagnostics(prefix_b, 4, 2))
        self.assertEqual(problem_a.reference.history_hash, history_hash(history))
        # A genuine historical change must remain visible to the leakage control.
        changed = (replace(history[0], lines=((0, 10),)),) + history[1:]
        self.assertNotEqual(problem_a.input_hash, build_training_problem(self.catalogue, changed, 2).input_hash)

    def test_later_inside_history_mutations_do_not_change_earlier_diagnostics(self):
        history = orders(*(((0, 1),) for _ in range(12)))
        changed = history[:8] + tuple(replace(o, lines=((1, 5),), observations=((1, 1),)) for o in history[8:])
        before = historical_activation_diagnostics(history, 4, 2)
        after = historical_activation_diagnostics(changed, 4, 2)
        self.assertEqual(before[0], after[0])
        self.assertNotEqual(before[1]["activation_mass"], after[1]["activation_mass"])

    def test_diagnostic_boundaries_across_remainders_and_sparse_evidence_threshold(self):
        for length, n in itertools.product(range(1, 25), range(1, 6)):
            history = orders(*(((0, 1),) for _ in range(length)))
            diagnostics = historical_activation_diagnostics(history, 2, n)
            self.assertEqual(len(diagnostics), max(0, length // n - 3))
            for record in diagnostics:
                self.assertGreaterEqual(record["cut"] // n, 3)
                self.assertEqual((length - record["cut"]) % n, 0)
                self.assertLessEqual(record["next_stop"], length)
                self.assertEqual(record["next_stop"] - record["next_start"], n)
                self.assertEqual(record["sparse_history"], record["cut"] // n < 10)


if __name__ == "__main__":
    unittest.main()
