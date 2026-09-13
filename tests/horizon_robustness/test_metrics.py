"""Hand-worked M2 correctness fixtures only; no empirical data or solvers."""

from collections import Counter
from dataclasses import asdict, replace
from fractions import Fraction
import inspect
import json
import unittest
from unittest.mock import patch

from Baselines.horizon_robustness import metrics, validation
from Baselines.horizon_robustness.metrics import evaluate_layout, support_visit_count, visit_count
from Baselines.horizon_robustness.orders import aggregate_orders
from Baselines.horizon_robustness.protocol import ContractError, digest
from Baselines.horizon_robustness.reference import slot_assignment
from Baselines.horizon_robustness.schema import (CatalogueManifest, Order, ReferenceState,
                                              Scenario, SourceFile, TrainingProblem)
from Baselines.horizon_robustness.validation import validate_assignment


def orders_from_counts(vectors, start=1):
    return tuple(Order(f"ORD_{key}", key, tuple((p, count) for p, count in enumerate(vector) if count))
                 for key, vector in enumerate(vectors, start))


def fixture(vectors=None, assignment=(0, 0, 1, 1), capacities=(2, 2),
            n=1, delta="0.01", nu="0", arm="HIST", fixed=(), allowed=(), slots=()):
    if vectors is None:
        vectors = [(2, 1, 3, 0)] * 3
    history = orders_from_counts(vectors)
    catalogue = CatalogueManifest("m2_unit_fixture", "fixture",
                                  tuple(f"P{p}" for p in range(len(assignment))),
                                  tuple(f"S{s}" for s in range(len(capacities))), capacities,
                                  exogenous_fixed=fixed, allowed_stations=allowed, slot_ids=slots)
    counts = tuple(sum(vector[p] for vector in vectors) for p in range(len(assignment)))
    station_counts = tuple(sum(c for p, c in enumerate(counts) if assignment[p] == s)
                           for s in range(len(capacities)))
    reference = ReferenceState(assignment, fixed, counts, station_counts, len(history),
                               digest([asdict(o) for o in history]), "m2_hand_worked_unit_fixture")
    scenarios = []
    for start in range(len(history) % n, len(history), n):
        block = tuple(sum(vectors[i][p] for i in range(start, start + n)) for p in range(len(assignment)))
        scenarios.append(Scenario(tuple((p, c) for p, c in enumerate(block) if c), sum(block), start, start + n))
    scenarios.append(Scenario(tuple((p, c) for p, c in enumerate(counts) if c), sum(counts), 0, len(history), "history"))
    supports = tuple(sorted(Counter(o.support for o in history).items()))
    return TrainingProblem(catalogue, reference, n, tuple(scenarios), supports,
                           arm=arm, delta=delta, nu=nu), history


class EvaluationTests(unittest.TestCase):
    def test_scale_invariance_including_huge_exact_counts(self):
        problem, _ = fixture()
        base = evaluate_layout(problem, problem.reference.assignment, orders_from_counts([(3, 0, 2, 1)], 10))
        scaled = evaluate_layout(problem, problem.reference.assignment,
                                 orders_from_counts([(3 * 10**400, 0, 2 * 10**400, 10**400)], 10))
        for key in ("station_shares_exact", "residuals_exact", "joint_pass", "visit_count", "activation_mass_exact"):
            self.assertEqual(base[key], scaled[key])
        self.assertEqual(scaled["total_lines"], 6 * 10**400)
        json.dumps(scaled, allow_nan=False)

    def test_quantity_is_ignored_and_synthetic_multiplicity_is_workload(self):
        problem, _ = fixture()
        problem = replace(problem, catalogue=replace(problem.catalogue, product_ids=("0", "1", "2", "3")))
        rows = [dict(ORDER="ORD_10", PRODUCT=p, QUANTITY=q) for p, q in
                (("0", "100000"), ("0", "-12"), ("2", "NaN"))]
        first = aggregate_orders(rows, problem.catalogue).orders
        second = aggregate_orders([dict(row, QUANTITY="1", STATION="irrelevant") for row in rows], problem.catalogue).orders
        a = evaluate_layout(problem, problem.reference.assignment, first)
        b = evaluate_layout(problem, problem.reference.assignment, second)
        self.assertEqual(a, b)
        self.assertEqual(a["station_line_counts"], [2, 1])
        self.assertEqual(a["visit_count"], 2)
        self.assertEqual(a["station_shares_exact"], ["2/3", "1/3"])

    def test_industrial_pair_deduplication(self):
        problem, _ = fixture(vectors=[(1, 1, 1, 0)] * 3)
        source = SourceFile("Heuristic_Connex_Set_Project/data/BERNER_ORDER_LINES_09-12.csv", "a" * 64, 0)
        industrial = replace(problem.catalogue, kind="industrial", source_files=(source,))
        problem = replace(problem, catalogue=industrial)
        rows = [dict(ORDER="ORD_10", PRODUCT="P0", STATION="S0", QUANTITY="999"),
                dict(ORDER="ORD_10", PRODUCT="P0", STATION="S1", QUANTITY="1"),
                dict(ORDER="ORD_10", PRODUCT="P2", STATION="S1", QUANTITY="2")]
        future = aggregate_orders(rows, industrial, industrial=True).orders
        result = evaluate_layout(problem, problem.reference.assignment, future)
        self.assertEqual(result["total_lines"], 2)
        self.assertEqual(result["visit_count"], 2)
        with self.assertRaises(ContractError):
            evaluate_layout(problem, problem.reference.assignment, orders_from_counts([(2, 0, 1, 0)], 10))

    def test_retained_industrial_frozen_workload_and_excluded_zone_guard(self):
        problem, history = fixture(vectors=[(1, 1, 1, 1)] * 6, n=2,
                                   fixed=((0, 0), (2, 1), (3, 1)))
        source = SourceFile("Heuristic_Connex_Set_Project/data/BERNER_ORDER_LINES_09-12.csv", "a" * 64, 0)
        catalogue = replace(problem.catalogue, kind="industrial", source_files=(source,),
                            station_ids=("01.E4", "01.31"))
        problem = replace(problem, catalogue=catalogue)
        future = orders_from_counts([(0, 0, 1, 1), (1, 1, 1, 0)], 10)
        result = evaluate_layout(problem, problem.reference.assignment, future)
        self.assertEqual(result["station_ids"], ["01.E4", "01.31"])
        self.assertEqual(result["total_lines"], 5)
        self.assertEqual(result["station_line_counts"], [2, 3])
        self.assertEqual(result["fixed_station_line_counts"], [1, 3])
        self.assertEqual(result["visit_count"], 3)
        self.assertEqual(result["mean_visits_exact"], "3/2")
        self.assertEqual(result["station_shares_exact"], ["2/5", "3/5"])
        self.assertFalse(result["joint_pass"])
        self.assertTrue(validate_assignment(problem, problem.reference.assignment, history=history)["valid"])
        for excluded in ("01.Z8", "01.15", "01.GED"):
            with self.subTest(excluded=excluded):
                invalid = replace(problem, catalogue=replace(catalogue, station_ids=("01.E4", excluded)))
                certificate = validate_assignment(invalid, invalid.reference.assignment)
                self.assertFalse(certificate["valid"])
                self.assertTrue(any("excluded station" in v for v in certificate["violations"]))
                with self.assertRaises(ContractError):
                    evaluate_layout(invalid, invalid.reference.assignment, future)

    def test_full_fixed_workload_and_fully_static_station(self):
        problem, _ = fixture(fixed=((0, 0), (2, 1), (3, 1)))
        future = orders_from_counts([(1, 1, 18, 0)], 10)
        result = evaluate_layout(problem, problem.reference.assignment, future)
        self.assertEqual(result["total_lines"], 20)
        self.assertEqual(result["station_line_counts"], [2, 18])
        self.assertEqual(result["fixed_station_line_counts"], [1, 18])
        self.assertEqual(result["visit_count"], 2)
        self.assertEqual(result["historical_visit_count"], 6)
        self.assertEqual(result["stations"][1]["fixed_share_exact"], "9/10")
        self.assertFalse(result["joint_pass"])
        self.assertEqual(result["violation_count"], 1)
        self.assertEqual(sum(result["station_shares"]), 1)

    def test_exact_decimal_boundary_no_future_model_tolerance(self):
        problem, _ = fixture(vectors=[(1, 1)] * 3, assignment=(0, 1), capacities=(1, 1))
        assignment = problem.reference.assignment
        on = evaluate_layout(problem, assignment, orders_from_counts([(51, 49)], 10))
        above = evaluate_layout(problem, assignment, orders_from_counts([(510000001, 489999999)], 10))
        below = evaluate_layout(problem, assignment, orders_from_counts([(509999999, 490000001)], 10))
        self.assertTrue(on["joint_pass"])
        self.assertTrue(below["joint_pass"])
        self.assertFalse(above["joint_pass"])
        self.assertEqual(above["maximum_excess_exact"], "1/1000000000")
        self.assertTrue(above["stations"][0]["borderline"])
        self.assertEqual(above["future_feasibility_tolerance"], 0)
        self.assertTrue(above["validation"]["valid"])

    def test_rational_historical_target_not_rounded_float(self):
        problem, _ = fixture(vectors=[(1, 2)] * 3, assignment=(0, 1), capacities=(1, 1), delta="0")
        result = evaluate_layout(problem, (0, 1), orders_from_counts([(1, 2)], 10))
        self.assertEqual(result["caps_exact"], ["1/3", "2/3"])
        self.assertTrue(result["joint_pass"])
        self.assertEqual(result["residuals_exact"], ["0", "0"])

    def test_two_station_implied_lower_bound(self):
        problem, _ = fixture(vectors=[(4, 6)] * 3, assignment=(0, 1), capacities=(1, 1), delta="0.1")
        feasible = evaluate_layout(problem, (0, 1), orders_from_counts([(3, 7)], 10))
        self.assertEqual(feasible["implied_lower_bounds_exact"], ["3/10", "1/2"])
        self.assertTrue(feasible["joint_pass"])
        self.assertEqual(feasible["stations"][0]["lower_bound_distance_exact"], "0")
        failed = evaluate_layout(problem, (0, 1), orders_from_counts([(2, 8)], 10))
        self.assertFalse(failed["joint_pass"])
        self.assertEqual(failed["stations"][0]["lower_bound_distance_exact"], "-1/10")

    def test_many_station_upper_only_allows_asymmetric_decrease(self):
        problem, _ = fixture(vectors=[(4, 2, 2, 2)] * 3, assignment=(0, 1, 2, 3),
                             capacities=(1, 1, 1, 1), delta="0.1")
        result = evaluate_layout(problem, (0, 1, 2, 3), orders_from_counts([(1, 3, 3, 3)], 10))
        self.assertTrue(result["joint_pass"])
        self.assertEqual(result["implied_lower_bounds_exact"], ["1/10", "0", "0", "0"])
        self.assertEqual(result["stations"][0]["decrease_exact"], "3/10")

    def test_clipped_caps_zero_target_and_single_station(self):
        problem, _ = fixture(vectors=[(9, 1, 0)] * 3, assignment=(0, 1, 2), capacities=(1, 1, 1), delta="0.2")
        result = evaluate_layout(problem, (0, 1, 2), orders_from_counts([(5, 3, 2)], 10))
        self.assertEqual(result["caps_exact"], ["1", "3/10", "1/5"])
        self.assertEqual(result["implied_lower_bounds_exact"], ["1/2", "0", "0"])
        self.assertIsNone(result["stations"][2]["cap_relative_to_target"])
        self.assertEqual(result["effective_total_allowance_exact"], "1/2")
        one, _ = fixture(vectors=[(1, 0)] * 3, assignment=(0, 0), capacities=(2,), arm="HIST+ACT", nu="1")
        scored = evaluate_layout(one, (0, 0), orders_from_counts([(0, 10)], 10))
        self.assertEqual(scored["implied_lower_bounds_exact"], ["1"])
        self.assertEqual(scored["worst_scenario_envelope_exact"], ["1"])
        self.assertTrue(scored["joint_pass"])

    def test_activation_and_station_direction_novelty(self):
        problem, _ = fixture(arm="HIST+ACT", nu="0.1", delta="0.05")
        result = evaluate_layout(problem, problem.reference.assignment, orders_from_counts([(3, 0, 5, 2)], 10))
        self.assertEqual(result["worst_scenario_envelope_exact"], ["1/2", "11/20"])
        self.assertEqual(result["activation_mass_exact"], "1/5")
        self.assertTrue(result["activation_exceeds_budget"])
        self.assertEqual(result["novelty_residuals_exact"], ["-1/5", "3/20"])
        self.assertEqual(result["station_novelty_count"], 1)
        self.assertEqual(result["inactive_product_count"], 1)
        self.assertEqual(result["realized_inactive_product_count"], 1)
        self.assertEqual(result["novel_support_order_count"], 1)
        self.assertIn("not_certified", result["uncertainty_membership"])

    def test_no_activation_does_not_certify_active_mix(self):
        problem, _ = fixture(arm="HIST+ACT", nu="0.1", delta="0.1")
        result = evaluate_layout(problem, problem.reference.assignment, orders_from_counts([(9, 0, 1, 0)], 10))
        self.assertFalse(result["activation_exceeds_budget"])
        self.assertEqual(result["activation_mass_exact"], "0")
        self.assertGreater(result["maximum_novelty_excess"], 0)
        self.assertFalse(result["joint_pass"])

    def test_future_exact_length_and_explicit_cross_horizon(self):
        problem, _ = fixture(n=2, vectors=[(2, 1, 3, 0)] * 6)
        future = orders_from_counts([(2, 1, 3, 0)] * 3, 10)
        for invalid in ((), future[:1]):
            with self.assertRaises(ContractError) as caught:
                evaluate_layout(problem, problem.reference.assignment, invalid)
            self.assertEqual(caught.exception.code, "INSUFFICIENT_FUTURE")
        with self.assertRaises(ContractError):
            evaluate_layout(problem, problem.reference.assignment, future)
        result = evaluate_layout(problem, problem.reference.assignment, future, horizon=3)
        self.assertEqual(result["horizon"], 3)
        self.assertFalse(result["primary_same_horizon"])
        self.assertEqual(result["future_boundaries"]["start"], 6)
        self.assertEqual(result["future_boundaries"]["stop"], 9)
        self.assertEqual(result["future_boundaries"]["first_order_id"], "ORD_10")
        self.assertFalse(result["future_boundaries"]["stream_adjacency_verified"])
        for horizon in (True, 0, -1, 2.0, "2"):
            with self.subTest(horizon=horizon), self.assertRaises(ContractError):
                evaluate_layout(problem, problem.reference.assignment, future[:2], horizon=horizon)

    def test_empty_zero_duplicate_unordered_or_unknown_future_rejected(self):
        problem, _ = fixture()
        empty = Order("ORD_10", 10, ((0, 1),))
        object.__setattr__(empty, "lines", ())  # Deliberately corrupt a frozen input for a failing control.
        zero = Order("ORD_10", 10, ((0, 1),))
        object.__setattr__(zero, "lines", ((0, 0),))
        duplicate = orders_from_counts([(1, 0, 1, 0)], 10)[0]
        cases = ((empty,), (zero,), (duplicate, duplicate),
                 (replace(duplicate, order_id="ORD_20", chronology_key=20), duplicate),
                 (duplicate, replace(duplicate, chronology_key=21)),
                 (Order("ORD_10", 10, ((4, 1),)),))
        for future in cases:
            with self.subTest(future=future), self.assertRaises(ContractError):
                evaluate_layout(problem, problem.reference.assignment, future, horizon=len(future))

    def test_frozen_hashes_source_boundaries_and_fixed_slots(self):
        problem, _ = fixture(fixed=((1, 0),), slots=(("a", "b"), ("c", "d")))
        assignment = (1, 0, 0, 1)
        before = digest(problem.to_dict())
        first = evaluate_layout(problem, assignment, orders_from_counts([(1, 1, 1, 1)], 10))
        second = evaluate_layout(problem, assignment, orders_from_counts([(8, 1, 1, 1)], 10))
        self.assertEqual(first["layout_hash"], second["layout_hash"])
        self.assertEqual(before, digest(problem.to_dict()))
        self.assertEqual(first["slot_assignment"][1], slot_assignment(problem.catalogue, problem.reference.assignment)[1])
        self.assertEqual(len(set(first["slot_assignment"])), problem.catalogue.p)
        self.assertEqual(first["product_ids"], list(problem.catalogue.product_ids))
        self.assertNotEqual(first["future_hash"], second["future_hash"])
        self.assertEqual(first["history_hash"], problem.reference.history_hash)
        self.assertEqual(first["input_hash"], problem.input_hash)
        self.assertEqual(first["source_hash"], digest(first["source_files"]))
        self.assertEqual(json.loads(json.dumps(first, allow_nan=False)), first)

    def test_training_only_fixed_mask_reserves_incumbent_slot(self):
        problem, _ = fixture(slots=(("a", "b"), ("c", "d")))
        problem = replace(problem, reference=replace(problem.reference, fixed=((1, 0), (3, 1))))
        result = evaluate_layout(problem, (1, 0, 0, 1), orders_from_counts([(1, 1, 1, 1)], 10))
        base_slots = slot_assignment(problem.catalogue, problem.reference.assignment)
        for p in (1, 3):
            self.assertEqual(result["slot_assignment"][p], base_slots[p])
        moved = validate_assignment(problem, (0, 1, 1, 0))
        self.assertFalse(moved["valid"])
        self.assertTrue(any("fixed" in v for v in moved["violations"]))

    def test_layout_hash_precedes_future_order_access(self):
        problem, _ = fixture()
        events = []

        class ObservedFuture(tuple):
            def __iter__(self):
                events.append("future_access")
                return super().__iter__()

        def observed_digest(value):
            if isinstance(value, dict) and "slot_assignment" in value:
                events.append("layout_hash")
            return digest(value)

        future = ObservedFuture(orders_from_counts([(1, 1, 1, 1)], 10))
        with patch.object(metrics, "digest", side_effect=observed_digest):
            evaluate_layout(problem, problem.reference.assignment, future)
        self.assertEqual(events[0], "layout_hash")
        self.assertIn("future_access", events)

    def test_future_station_observations_cannot_change_metrics(self):
        problem, _ = fixture()
        future = orders_from_counts([(1, 1, 2, 1)], 10)
        observed = (replace(future[0], observations=((0, 1), (3, 0))),)
        a = evaluate_layout(problem, problem.reference.assignment, future)
        b = evaluate_layout(problem, problem.reference.assignment, observed)
        for key in ("layout_hash", "history_hash", "input_hash", "stations", "joint_pass", "validation"):
            self.assertEqual(a[key], b[key])
        self.assertNotEqual(a["future_hash"], b["future_hash"])

    def test_model_failure_reported_separately_from_future_failure(self):
        problem, _ = fixture(arm="HIST+ACT", nu="0.5")
        result = evaluate_layout(problem, problem.reference.assignment, orders_from_counts([(2, 1, 3, 0)], 10))
        self.assertTrue(result["joint_pass"])
        self.assertFalse(result["validation"]["valid"])
        self.assertTrue(result["allocation_returned"])
        self.assertIsNone(result["solver_status"])


    def test_upper_only_interior_layout_keeps_signed_residual_and_is_not_borderline(self):
        # Regression guard (13 Sep 2026): zeros standing in for absent floor
        # residuals had clipped maximum_residual at 0 and made every interior
        # upper-only layout "borderline".
        problem, _ = fixture(vectors=[(1, 1)] * 3, assignment=(0, 1), capacities=(1, 1), delta="0.1")
        result = evaluate_layout(problem, (0, 1), orders_from_counts([(5, 5)], 10))
        self.assertEqual(result["rule"], "upper_only")
        self.assertTrue(result["joint_pass"])
        self.assertEqual(result["maximum_residual_exact"], "-1/10")
        self.assertFalse(result["borderline"])
        self.assertEqual(result["breaches_exact"], result["residuals_exact"])
        self.assertIsNone(result["floor_violation_count"])
        self.assertIsNone(result["station_novelty_count_lower"])
        self.assertNotIn("floors", result)
        self.assertNotIn("maximum_novelty_shortfall", result)
        self.assertTrue(all(s["feasible"] and not s["borderline"] for s in result["stations"]))
        self.assertTrue(all(s["below_lowest_scenario"] is None for s in result["stations"]))

    def test_two_sided_lower_direction_novelty_is_reported(self):
        problem, _ = fixture(vectors=[(1, 1)] * 3, assignment=(0, 1), capacities=(1, 1), delta="0.1")
        two = replace(problem, rule="two_sided")
        starved = evaluate_layout(two, (0, 1), orders_from_counts([(9, 1)], 10))
        self.assertEqual(starved["rule"], "two_sided")
        # Station 1 fell to 10% against a modelled minimum of 50%: a downward
        # departure from the uncertainty set, and a floor breach at delta 0.1.
        self.assertEqual(starved["station_novelty_count_lower"], 1)
        self.assertEqual(starved["maximum_novelty_shortfall_exact"], "2/5")
        self.assertTrue(starved["stations"][1]["below_lowest_scenario"])
        self.assertFalse(starved["stations"][0]["below_lowest_scenario"])
        self.assertEqual(starved["floor_violation_count"], 1)
        balanced = evaluate_layout(two, (0, 1), orders_from_counts([(5, 5)], 10))
        self.assertEqual(balanced["station_novelty_count_lower"], 0)
        self.assertEqual(balanced["maximum_novelty_shortfall_exact"], "0")
        self.assertTrue(balanced["joint_pass"])
        self.assertFalse(balanced["borderline"])

    def test_tight_control_retains_original_future_caps(self):
        problem, _ = fixture(vectors=[(1, 1)] * 3, assignment=(0, 1), capacities=(1, 1), delta="0.1", arm="TIGHT")
        result = evaluate_layout(problem, (0, 1), orders_from_counts([(6, 4)], 10))
        self.assertTrue(result["joint_pass"])
        self.assertEqual(result["caps_exact"], ["3/5", "3/5"])
        self.assertEqual(result["validation"]["station_shares"][0]["cap_exact"], "11/20")


class ValidationTests(unittest.TestCase):
    def test_valid_complete_assignment_and_full_raw_history(self):
        problem, history = fixture(fixed=((0, 0),))
        result = validate_assignment(problem, problem.reference.assignment, objective=6, history=history)
        self.assertTrue(result["valid"], result["violations"])
        self.assertEqual(result["actual_objective"], 6)
        self.assertEqual(result["occupancy"], [2, 2])
        self.assertEqual(len(result["scenario_shares"]), 4)
        self.assertEqual(result["scenario_shares"][0]["shares_exact"], ["1/2", "1/2"])
        self.assertEqual(result["scenario_shares"][0]["fixed_station_line_counts"], [2, 0])
        self.assertTrue(result["history_checked"])
        self.assertEqual(json.loads(json.dumps(result, allow_nan=False)), result)

    def test_incomplete_duplicated_overfilled_and_wrong_assignments(self):
        problem, _ = fixture()
        bad = (None, (), (0, 0, 1), (0, 0, 1, 1, 1), (0, 0, 0, 1),
               (0, -1, 1, 1), (0, 2, 1, 1), (False, 0, 1, 1), (0.0, 0, 1, 1),
               [0, 0, 1, 1], ((0, 0), (1, 0), (1, 1), (3, 1)),
               {0: 0, 1: 0, 2: 1, 3: 1})
        for assignment in bad:
            with self.subTest(assignment=assignment):
                result = validate_assignment(problem, assignment)
                self.assertFalse(result["valid"])
                self.assertTrue(result["violations"])
                self.assertIsNone(result["actual_objective"])
                json.dumps(result, allow_nan=False)
                with self.assertRaises(ContractError):
                    evaluate_layout(problem, assignment, orders_from_counts([(1, 1, 1, 1)], 10))

    def test_forbidden_and_moved_fixed_rejected_independently_of_schema(self):
        problem, _ = fixture(fixed=((0, 0),), allowed=((0,), (0, 1), (0, 1), (0, 1)))
        with patch.object(CatalogueManifest, "check_storage", side_effect=AssertionError("must independently inspect")):
            result = validate_assignment(problem, (1, 0, 0, 1))
        self.assertFalse(result["valid"])
        self.assertTrue(any("forbidden" in text for text in result["violations"]))
        self.assertTrue(any("fixed" in text for text in result["violations"]))
        self.assertEqual(result["occupancy"], [2, 2])

    def test_exact_support_and_visit_count_helpers(self):
        orders = orders_from_counts([(9, 1, 0, 0), (1, 0, 1, 0), (2, 3, 0, 0)])
        assignment = (0, 0, 1, 1)
        supports = (((0, 1), 2), ((0, 2), 1))
        self.assertEqual(visit_count(orders, assignment), 4)
        self.assertEqual(support_visit_count(supports, assignment), 4)
        self.assertEqual(visit_count((), assignment), 0)
        self.assertEqual(support_visit_count((), assignment), 0)
        for bad in ((((0, 0), 1),), (((4,), 1),), (((0,), 1.5),), (((0,), 0),),
                    (((0,), True),), (((0,), 1), ((0,), 1))):
            with self.subTest(supports=bad), self.assertRaises(ContractError):
                support_visit_count(bad, assignment)

    def test_objective_omission_fixed_touches_and_nonfinite_values(self):
        problem, history = fixture(vectors=[(1, 0, 1, 0)] * 3, fixed=((2, 1),))
        self.assertTrue(validate_assignment(problem, problem.reference.assignment, objective=6, history=history)["valid"])
        for objective in (3, 2, 0, float("nan"), float("inf"), -float("inf"), True, "NaN"):
            with self.subTest(objective=objective):
                result = validate_assignment(problem, problem.reference.assignment, objective=objective, history=history)
                self.assertFalse(result["valid"])
                json.dumps(result, allow_nan=False)

    def test_raw_history_detects_support_truncation_with_preserved_weights(self):
        problem, history = fixture(vectors=[(1, 0, 1, 0), (0, 1, 0, 1)] * 3)
        # Each product still appears equally often; per-product totals alone cannot expose this omission.
        corrupted = replace(problem, weighted_supports=(((0, 1), 3), ((2, 3), 3)))
        result = validate_assignment(corrupted, problem.reference.assignment, objective=6, history=history)
        self.assertFalse(result["valid"])
        self.assertEqual(result["actual_objective"], 12)
        self.assertTrue(any("raw history supports" in v for v in result["violations"]))
        self.assertTrue(any("objective mismatch" in v for v in result["violations"]))
        unchecked = validate_assignment(corrupted, problem.reference.assignment)
        self.assertFalse(unchecked["history_checked"])
        self.assertIn("unverified", unchecked["history_audit"])

    def test_support_incidence_detects_dropped_fixed_and_inactive_product(self):
        problem, _ = fixture(fixed=((2, 1),))
        for supports in ((((0, 1), 3),), (((0, 1, 2, 3), 3),)):
            result = validate_assignment(replace(problem, weighted_supports=supports), problem.reference.assignment)
            self.assertFalse(result["valid"])
            self.assertTrue(any("support incidence" in v for v in result["violations"]))

    def test_raw_history_hash_count_and_scenario_audits(self):
        problem, history = fixture()
        bad_history = (replace(history[0], lines=((0, 3), (1, 1), (2, 3))),) + history[1:]
        result = validate_assignment(problem, problem.reference.assignment, history=bad_history)
        self.assertFalse(result["valid"])
        for word in ("hash mismatch", "product workload", "scenario"):
            self.assertTrue(any(word in v for v in result["violations"]))
        for raw in ((), history[:-1], (history[0], history[0], history[2])):
            self.assertFalse(validate_assignment(problem, problem.reference.assignment, history=raw)["valid"])

    def test_raw_history_catches_omitted_duplicate_and_wrong_scenarios(self):
        problem, history = fixture()
        for scenarios in (problem.scenarios[1:], problem.scenarios + (problem.scenarios[0],),
                          (replace(problem.scenarios[0], counts=((0, 3), (1, 1), (2, 2))),) + problem.scenarios[1:]):
            result = validate_assignment(replace(problem, scenarios=scenarios), problem.reference.assignment, history=history)
            self.assertFalse(result["valid"])
            self.assertTrue(any("scenario" in v for v in result["violations"]))

    def test_nominal_uses_pooled_history_and_robust_checks_every_scenario(self):
        problem, _ = fixture(vectors=[(9, 1), (1, 9), (1, 1)], assignment=(0, 1), capacities=(1, 1))
        robust = validate_assignment(problem, (0, 1))
        nominal = validate_assignment(replace(problem, arm="NOM"), (0, 1))
        self.assertFalse(robust["valid"])
        self.assertEqual(robust["maximum_model_excess_exact"], "39/100")
        self.assertEqual(robust["worst_scenario_envelope_exact"], ["9/10", "9/10"])
        self.assertTrue(nominal["valid"])
        self.assertEqual(len(nominal["scenario_shares"]), 1)
        self.assertEqual(nominal["scenario_shares"][0]["total_lines"], 22)

    def test_activation_envelope_endpoints_including_fixed_inactive(self):
        problem, _ = fixture(arm="HIST+ACT", nu="0.1", fixed=((3, 1),))
        result = validate_assignment(problem, problem.reference.assignment)
        self.assertFalse(result["valid"])
        self.assertEqual(result["inactive_counts"], [0, 1])
        self.assertEqual(result["scenario_shares"][0]["activation_shares_exact"], ["9/20", "11/20"])
        self.assertEqual(result["worst_scenario_envelope_exact"], ["1/2", "11/20"])
        self.assertEqual(result["maximum_model_excess_exact"], "1/25")
        endpoint = validate_assignment(replace(problem, nu="1"), problem.reference.assignment)
        self.assertEqual(endpoint["worst_scenario_envelope_exact"], ["1/2", "1"])
        zero = validate_assignment(replace(problem, nu="0"), problem.reference.assignment)
        hist = validate_assignment(replace(problem, arm="HIST"), problem.reference.assignment)
        self.assertEqual(zero["scenario_shares"], hist["scenario_shares"])

    def test_empty_inactive_set_disables_activation_exactly(self):
        problem, _ = fixture(vectors=[(1, 1, 1, 1)] * 3, arm="HIST+ACT", nu="1")
        result = validate_assignment(problem, problem.reference.assignment)
        hist = validate_assignment(replace(problem, arm="HIST"), problem.reference.assignment)
        self.assertEqual(result["effective_nu_exact"], "0")
        self.assertEqual(result["inactive_counts"], [0, 0])
        self.assertEqual(result["scenario_shares"], hist["scenario_shares"])
        self.assertTrue(result["valid"])

    def test_model_tolerance_is_absolute_and_reported_exactly(self):
        for extra, valid in ((1, True), (10, True), (11, False)):
            with self.subTest(extra=extra):
                problem, _ = fixture(vectors=[(500000000 + extra, 500000000 - extra),
                                              (500000000 - extra, 500000000 + extra),
                                              (500000000, 500000000)],
                                     assignment=(0, 1), capacities=(1, 1), delta="0")
                result = validate_assignment(problem, (0, 1))
                self.assertEqual(result["valid"], valid)
                self.assertFalse(result["model_feasible_exact"])
                self.assertEqual(result["maximum_model_excess_exact"], str(Fraction(extra, 10**9)))
                self.assertEqual(result["model_tolerance"], 1e-8)

    def test_min_slack_accepts_loose_incumbent_and_ignores_original_caps(self):
        problem, _ = fixture(arm="HIST+ACT", nu="0.1", fixed=((3, 1),))
        self.assertFalse(validate_assignment(problem, problem.reference.assignment)["valid"])
        for eta in ("0.05", "0.08", "2"):
            result = validate_assignment(problem, problem.reference.assignment, objective=float(eta),
                                         solve_mode="min_slack", min_slack=eta)
            self.assertTrue(result["valid"], result["violations"])
            self.assertEqual(result["minimum_required_slack_exact"], "1/20")
            self.assertEqual(result["actual_objective"], float(eta))
            self.assertFalse(result["original_policy_feasible_exact"])
        result = validate_assignment(problem, problem.reference.assignment, objective=0.08, solve_mode="min_slack")
        self.assertTrue(result["valid"])

    def test_unbounded_display_ratios_remain_json_serializable(self):
        problem, _ = fixture(vectors=[(1, 10**400)] * 3, assignment=(0, 1), capacities=(1, 1))
        result = evaluate_layout(problem, (0, 1), orders_from_counts([(1, 1)], 10))
        self.assertIsNone(result["stations"][0]["cap_relative_to_target"])
        self.assertIsNotNone(result["stations"][0]["cap_relative_to_target_exact"])
        json.dumps(result, allow_nan=False)
        diagnostic = validate_assignment(problem, (0, 1), solve_mode="min_slack", min_slack=10**400)
        self.assertTrue(diagnostic["valid"])
        self.assertEqual(diagnostic["actual_objective_exact"], str(10**400))
        json.dumps(diagnostic, allow_nan=False)

    def test_min_slack_failure_controls_and_numerical_policy(self):
        problem, _ = fixture(arm="HIST+ACT", nu="0.1")
        for eta, objective in (("0.049", 0.049), ("0.08", 0.05), ("-0.01", -0.01),
                               (None, None), ("NaN", None), (float("inf"), None)):
            with self.subTest(eta=eta, objective=objective):
                result = validate_assignment(problem, problem.reference.assignment, objective=objective,
                                             solve_mode="min_slack", min_slack=eta)
                self.assertFalse(result["valid"])
                json.dumps(result, allow_nan=False)
        almost = validate_assignment(problem, problem.reference.assignment, objective=0.049999999,
                                     solve_mode="min_slack")
        self.assertTrue(almost["valid"])
        self.assertFalse(almost["model_feasible_exact"])
        self.assertEqual(almost["maximum_model_excess_exact"], "1/1000000000")
        nominal = replace(problem, arm="NOM")
        lower_bound = validate_assignment(nominal, problem.reference.assignment, objective=-1e-9,
                                          solve_mode="min_slack")
        self.assertTrue(lower_bound["valid"])
        self.assertFalse(lower_bound["model_feasible_exact"])
        self.assertEqual(lower_bound["minimum_required_slack_exact"], "0")

    def test_invalid_objective_mode_returns_json_compatible_failure(self):
        problem, _ = fixture()
        for mode in ("unknown", None, float("nan"), float("inf")):
            with self.subTest(mode=mode):
                result = validate_assignment(problem, problem.reference.assignment, solve_mode=mode)
                self.assertFalse(result["valid"])
                self.assertIn("unknown solve_mode", result["violations"])
                json.dumps(result, allow_nan=False)

    def test_no_uncertainty_or_solver_oracle_and_no_target_reset(self):
        problem, _ = fixture()
        # Trap the convenient shared numerical properties as well as construction.
        with patch.object(TrainingProblem, "effective_scenarios", property(lambda self: self._oracle_trap)), \
                patch.object(TrainingProblem, "effective_nu", property(lambda self: self._oracle_trap)), \
                patch.object(TrainingProblem, "rational_caps", side_effect=AssertionError("independent recomputation required")), \
                patch("Baselines.horizon_robustness.reference.build_reference", side_effect=AssertionError("no resetting")):
            self.assertTrue(validate_assignment(problem, problem.reference.assignment)["valid"])
            result = evaluate_layout(problem, problem.reference.assignment, orders_from_counts([(1, 1, 2, 0)], 10))
            self.assertTrue(result["joint_pass"])
        for module in (metrics, validation):
            source = inspect.getsource(module)
            self.assertNotIn("from .uncertainty import", source)
            self.assertNotIn("import cplex", source)
            self.assertNotIn("import hexaly", source)


if __name__ == "__main__":
    unittest.main()
