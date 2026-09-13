"""Controls for exploratory revision 2: the two-sided workload rule.

Two things must hold at once. First, the upper-only study must be untouched:
every existing hash, manifest row and certificate has to reproduce
byte-for-byte, which is what the pinned constants below check. Second, the
two-sided rule must be exactly what it claims: integer lower rows that agree
with the exact validator on EVERY layout of a small fixture, a scorer that fails
a downside breach, and a runner that carries the rule into identities.

Hand-worked fixtures only. The one native solve here is a tiny CPLEX run.
"""

from fractions import Fraction
import itertools
import unittest

from Baselines.horizon_robustness import runner
from Baselines.horizon_robustness.metrics import evaluate_layout
from Baselines.horizon_robustness.protocol import ContractError, Protocol
from Baselines.horizon_robustness.schema import CatalogueManifest, Order, OrderedDemand, TrainingProblem
from Baselines.horizon_robustness.uncertainty import build_training_problem, integer_cap_rows
from Baselines.horizon_robustness.validation import validate_assignment

# Pinned BEFORE the `rule` field existed (10 Sep 2026 code), for the fixture in
# HashStabilityTests. If any of these moves, some completed campaign can no
# longer be revalidated and the change must be treated as a version break.
PINNED = {
    "NOM": ("56d9cd687c33ee2dc523d1ae8909eb1a8cb60b783ebaa04cfe9b1ca8a4fe15e1",
            "39f06c4114d6f39a182133ba1098bda9c3e2688f18176760b342fa129cab833e"),
    "TIGHT": ("3f9748d89fbf6f21722dec2a6ba092ef9b26de6263c71e60ca0ae7049fcf2447",
              "077aede2efc092cc6e61d5d6ef277472cc0adffa2f0cb4d96927d01ca4d4327f"),
    "HIST": ("3810def9515fc87fbb5e8d40e5d497c0bc51d74ae3d325a74cc7da94cf02801e",
             "049c74d3bed8939bf86fa64b5dc2c1160e9effd18b9dd5c168fc4863380ec6cf"),
    "HIST+ACT": ("d958ee470152075dce7ae121718fe94260a3396fe5b48efa9195778eee591a38",
                 "049c74d3bed8939bf86fa64b5dc2c1160e9effd18b9dd5c168fc4863380ec6cf"),
}


def orders(*lines):
    return tuple(Order(f"ORD_{i + 1}", i + 1, tuple(line)) for i, line in enumerate(lines))


def fixture():
    catalogue = CatalogueManifest("integer-rows-unit", "fixture", ("a", "b", "c", "d"),
                                  ("s0", "s1"), (2, 2), known_reference=(0, 1, 0, 1))
    history = orders(((1, 1), (2, 1)), ((0, 2), (1, 1)), ((0, 1),),
                     ((2, 2), (3, 2)), ((1, 1), (2, 1), (3, 1)), ((2, 2),))
    return catalogue, history


def sparse_fixture():
    """Product d never ordered: Z_H = {3}, so activation rows exist."""
    catalogue = CatalogueManifest("integer-activation-unit", "fixture", ("a", "b", "c", "d"),
                                  ("s0", "s1"), (2, 2), known_reference=(0, 1, 0, 1))
    history = orders(((0, 2), (1, 2), (2, 2)), ((0, 2), (1, 1)), ((0, 2), (2, 2)),
                     ((0, 1), (1, 2), (2, 1)), ((0, 2), (1, 2), (2, 1)), ((0, 2),))
    return catalogue, history


def layouts(catalogue, fixed=()):
    fixed = dict(fixed)
    for candidate in itertools.product(range(catalogue.s), repeat=catalogue.p):
        occupancy = [0] * catalogue.s
        for station in candidate:
            occupancy[station] += 1
        if tuple(occupancy) == tuple(catalogue.capacities) and all(candidate[p] == s for p, s in fixed.items()):
            yield candidate


def satisfies_integer_rows(problem, assignment):
    """Evaluate every integer row, honouring its sense, as a backend would."""
    rows, _ = integer_cap_rows(problem)
    inactive = set(problem.reference.inactive)
    for row in rows:
        scenario = problem.effective_scenarios[row["scenario"]]
        station = row["station"]
        left = row["multiplier"] * sum(count for p, count in scenario.counts if assignment[p] == station)
        if row["activation_coefficient"]:
            left += row["activation_coefficient"] * int(any(assignment[p] == station for p in inactive))
        if row.get("all_inactive_coefficient"):
            # g_s: every inactive product at this station (activation mass trapped).
            left += row["all_inactive_coefficient"] * int(bool(inactive) and all(assignment[p] == station for p in inactive))
        if row["sense"] == ">=" and left < row["threshold"]:
            return False
        if row["sense"] == "<=" and left > row["threshold"]:
            return False
    return True


def two_inactive_fixture():
    """Products c and d never ordered: Z_H = {2, 3}, so g_s can be 0 or 1."""
    catalogue = CatalogueManifest("integer-activation-two", "fixture", ("a", "b", "c", "d"),
                                  ("s0", "s1"), (2, 2), known_reference=(0, 1, 0, 1))
    history = orders(((0, 2), (1, 2)), ((0, 2), (1, 1)), ((0, 3),),
                     ((0, 1), (1, 2)), ((0, 2), (1, 2)), ((1, 2),))
    return catalogue, history


def reviewer_fixture():
    """The 13 Sep 2026 independent review's counterexample: product d inactive,
    layout (0,1,1,0) puts it at station 0 together with product a."""
    catalogue = CatalogueManifest("independent-edge", "fixture", ("a", "b", "c", "d"),
                                  ("s0", "s1"), (2, 2), known_reference=(0, 1, 1, 0))
    history = tuple(Order(str(i), i, ((0, 18), (1, 1), (2, 1))) for i in range(1, 7))
    return catalogue, history


def vertex_envelopes(problem, assignment):
    """Independent oracle: enumerate every vertex of the uncertainty set directly.

    Vertices are each scenario's share vector q_k and, for each inactive product
    p, the activated vector (1-nu) q_k + nu e_p with all activation mass on p.
    A station share is linear in q, so its extremes over the set are attained
    at these vertices. Shares nothing with the validator or the row builder.
    """
    from Baselines.horizon_robustness.protocol import ACTIVATION_ARMS
    inactive = problem.reference.inactive
    nu = Fraction(problem.nu) if problem.arm in ACTIVATION_ARMS and inactive else Fraction(0)
    count = problem.catalogue.s
    lowest, highest = [Fraction(1)] * count, [Fraction(0)] * count
    for scenario in problem.effective_scenarios:
        q = [Fraction(0)] * problem.catalogue.p
        for p, c in scenario.counts:
            q[p] = Fraction(c, scenario.total_lines)
        vertices = [q]
        for p in inactive:
            v = [(1 - nu) * value for value in q]
            v[p] += nu
            vertices.append(v)
        for v in vertices:
            shares = [Fraction(0)] * count
            for p, value in enumerate(v):
                shares[assignment[p]] += value
            for s in range(count):
                lowest[s] = min(lowest[s], shares[s])
                highest[s] = max(highest[s], shares[s])
    return tuple(lowest), tuple(highest)


class LowerEnvelopeOracleTests(unittest.TestCase):
    """The lowest attainable share must come from the uncertainty set's vertices.

    Before 13 Sep 2026 the drained endpoint (1-nu) A_sk was used unconditionally,
    which is wrong when every inactive product sits at the station: the mass
    then cannot avoid it. The oracle here enumerates vertices directly.
    """

    def test_reviewer_counterexample_layout_is_accepted(self):
        catalogue, history = reviewer_fixture()
        problem = build_training_problem(catalogue, history, 2, "HIST+ACT", "0.01", "0.05", "0.5",
                                         rule="two_sided")
        layout = catalogue.known_reference
        certificate = validate_assignment(problem, layout)
        self.assertEqual(certificate["lowest_scenario_envelope_exact"], ["9/10", "19/200"])
        self.assertEqual(certificate["worst_scenario_envelope_exact"], ["181/200", "1/10"])
        self.assertTrue(certificate["model_feasible_exact"], certificate["violations"])
        self.assertTrue(satisfies_integer_rows(problem, layout))
        self.assertEqual(vertex_envelopes(problem, layout), (
            (Fraction(9, 10), Fraction(19, 200)), (Fraction(181, 200), Fraction(1, 10))))

    def test_trapped_station_is_not_drained(self):
        catalogue, history = two_inactive_fixture()
        problem = build_training_problem(catalogue, history, 2, "HIST+ACT", "0.3", "0.2", "0.5",
                                         rule="two_sided")
        nu = Fraction("0.2")
        for assignment in layouts(catalogue, problem.reference.fixed):
            certificate = validate_assignment(problem, assignment)
            lowest = tuple(Fraction(v) for v in certificate["lowest_scenario_envelope_exact"])
            where = {assignment[2], assignment[3]}
            for s in range(catalogue.s):
                base = min(Fraction(sum(c for p, c in sc.counts if assignment[p] == s), sc.total_lines)
                           for sc in problem.effective_scenarios)
                expected = base if where == {s} else (1 - nu) * base
                self.assertEqual(lowest[s], expected, (assignment, s))

    def test_vertex_oracle_agrees_with_validator_and_rows_on_every_layout(self):
        for name, (catalogue, history) in (("one", sparse_fixture()), ("two", two_inactive_fixture()),
                                           ("reviewer", reviewer_fixture())):
            for nu in ("0.01", "0.05", "0.3"):
                for delta in ("0.02", "0.1", "0.3"):
                    problem = build_training_problem(catalogue, history, 2, "HIST+ACT", delta, nu, "0.5",
                                                     rule="two_sided")
                    for assignment in layouts(catalogue, problem.reference.fixed):
                        with self.subTest(fixture=name, nu=nu, delta=delta, layout=assignment):
                            certificate = validate_assignment(problem, assignment)
                            lowest, highest = vertex_envelopes(problem, assignment)
                            self.assertEqual(tuple(Fraction(v) for v in certificate["lowest_scenario_envelope_exact"]), lowest)
                            self.assertEqual(tuple(Fraction(v) for v in certificate["worst_scenario_envelope_exact"]), highest)
                            floors, caps = problem.rational_floors(True), problem.rational_caps(True)
                            exact = all(f <= lo and hi <= cap for f, lo, hi, cap in zip(floors, lowest, highest, caps))
                            self.assertEqual(certificate["model_feasible_exact"], exact)
                            self.assertEqual(satisfies_integer_rows(problem, assignment), exact)

    def test_helper_matches_validator_on_every_layout(self):
        from Baselines.horizon_robustness.uncertainty import minimum_slack_for_assignment
        for catalogue, history in (sparse_fixture(), two_inactive_fixture(), reviewer_fixture()):
            problem = build_training_problem(catalogue, history, 2, "HIST+ACT", "0.05", "0.05", "0.5",
                                             rule="two_sided")
            for assignment in layouts(catalogue, problem.reference.fixed):
                expected = float(Fraction(validate_assignment(problem, assignment)["minimum_required_slack_exact"]))
                self.assertEqual(minimum_slack_for_assignment(problem, assignment), expected, str(assignment))

    def test_helper_covers_the_lower_excursion(self):
        # Six products on three stations; reference shares (0.4, 0.3, 0.3); the
        # layout (1,1,0,2,0,2) gives (0.2, 0.4, 0.4): upward 0.1, downward 0.2.
        from Baselines.horizon_robustness.uncertainty import minimum_slack_for_assignment
        catalogue = CatalogueManifest("independent-slack", "fixture", tuple("abcdef"), ("s0", "s1", "s2"),
                                      (2, 2, 2), known_reference=(0, 0, 1, 1, 2, 2))
        history = tuple(Order(str(i), i, ((0, 2), (1, 2), (2, 1), (3, 2), (4, 1), (5, 2))) for i in range(1, 7))
        upper = build_training_problem(catalogue, history, 2, "NOM", "0.25", "0", "0.5")
        two = build_training_problem(catalogue, history, 2, "NOM", "0.25", "0", "0.5", rule="two_sided")
        self.assertEqual(minimum_slack_for_assignment(upper, (1, 1, 0, 2, 0, 2)), 0.1)
        self.assertEqual(minimum_slack_for_assignment(two, (1, 1, 0, 2, 0, 2)), 0.2)
        self.assertEqual(validate_assignment(two, (1, 1, 0, 2, 0, 2))["minimum_required_slack_exact"], "1/5")


class TightenedScenarioArmTests(unittest.TestCase):
    """HIST+ACT-T (revision 3): HIST+ACT's uncertainty set, TIGHT's reduced band.

    The arm completes the two-by-two of the held-out factorial: scenarios and
    activation on, reserved margin on. Its scoring band is the declared one; only
    the optimisation band is tightened, exactly as for TIGHT.
    """

    def test_model_is_hist_act_with_a_tightened_optimisation_band(self):
        catalogue, history = sparse_fixture()
        tightened = build_training_problem(catalogue, history, 2, "HIST+ACT-T", "0.2", "0.05", "0.5", rule="two_sided")
        plain = build_training_problem(catalogue, history, 2, "HIST+ACT", "0.2", "0.05", "0.5", rule="two_sided")
        tight = build_training_problem(catalogue, history, 2, "TIGHT", "0.2", "0.05", "0.5", rule="two_sided")
        self.assertEqual(tightened.effective_scenarios, plain.effective_scenarios)
        self.assertEqual(tightened.effective_nu, plain.effective_nu)
        self.assertGreater(tightened.effective_nu, 0.0)
        # Optimisation band halves; scoring band is the declared one.
        self.assertEqual(tightened.rational_caps(True), tight.rational_caps(True))
        self.assertEqual(tightened.rational_floors(True), tight.rational_floors(True))
        self.assertEqual(tightened.rational_caps(), plain.rational_caps())
        self.assertEqual(tightened.rational_floors(), plain.rational_floors())
        self.assertNotEqual(tightened.model_hash, plain.model_hash)
        self.assertNotEqual(tightened.model_hash, tight.model_hash)
        self.assertNotEqual(tightened.input_hash, plain.input_hash)

    def test_rows_validator_and_oracle_agree_and_nest_inside_hist_act(self):
        catalogue, history = sparse_fixture()
        accepted = {}
        for arm in ("HIST+ACT", "HIST+ACT-T"):
            problem = build_training_problem(catalogue, history, 2, arm, "0.3", "0.05", "0.5", rule="two_sided")
            accepted[arm] = set()
            for assignment in layouts(catalogue, problem.reference.fixed):
                certificate = validate_assignment(problem, assignment)
                lowest, highest = vertex_envelopes(problem, assignment)
                self.assertEqual(tuple(Fraction(v) for v in certificate["lowest_scenario_envelope_exact"]), lowest)
                self.assertEqual(tuple(Fraction(v) for v in certificate["worst_scenario_envelope_exact"]), highest)
                self.assertEqual(certificate["model_feasible_exact"], satisfies_integer_rows(problem, assignment))
                if certificate["model_feasible_exact"]:
                    accepted[arm].add(assignment)
        self.assertTrue(accepted["HIST+ACT-T"] <= accepted["HIST+ACT"])
        self.assertTrue(accepted["HIST+ACT"], "fixture must accept something")

    def test_unknown_arm_still_refused(self):
        catalogue, history = fixture()
        with self.assertRaises(ContractError):
            build_training_problem(catalogue, history, 2, "TIGHT-ACT", "0.35", "0.01", "0.5")


class HoldoutStageTests(unittest.TestCase):
    """The held-out deployment origin and the holdout quote (revision 3)."""

    def test_holdout_origin_is_the_end_of_the_furthest_scored_future(self):
        from Baselines.horizon_robustness.protocol import eligible, holdout_origin, horizon_grid, origins
        self.assertEqual(holdout_origin(284862, 21874), 199403 + 43748)
        self.assertEqual(holdout_origin(284862, 21874), origins(284862, 21874)[0] + horizon_grid(21874)[-1])
        self.assertIsNone(eligible(243151, 21874, 284862))
        self.assertEqual(eligible(243151, 43748, 284862), "INSUFFICIENT_FUTURE")
        with self.assertRaises(ContractError):
            holdout_origin(100, 40)

    def _demand(self, count):
        from Baselines.horizon_robustness.schema import OrderedDemand
        catalogue = CatalogueManifest("syn_50sku_seed1001", "fixture", ("a", "b", "c", "d"), ("x", "y"), (2, 2))
        history = tuple(Order(f"O{i}", i, tuple(sorted(((i % 4, 1), ((i + 1) % 4, 1))))) for i in range(count))
        return OrderedDemand(catalogue, history)

    def test_holdout_quote_uses_the_deployment_origin_and_the_focal_horizon_only(self):
        from Baselines.horizon_robustness import runner
        meta = dict(backend="hexaly", interpreter="fixture", python="fixture",
                    packages={"hexaly": "fake"}, implementation_hash="fixture")
        demand = self._demand(90)                      # P = 4: first origin 63, deployment origin 71
        manifest = runner.quote(("syn_50sku_seed1001",), loader=lambda *_: demand, metadata=meta,
                                stage="holdout", arms=("NOM", "TIGHT", "HIST+ACT", "HIST+ACT-T"),
                                seeds=(11, 22, 33), delta="0.02", rule="two_sided", horizons=(4,))
        rows = manifest["rows"]
        self.assertEqual(len(rows), 12)
        self.assertEqual({r["origin"] for r in rows}, {71})
        self.assertEqual({r["n"] for r in rows}, {4})
        self.assertEqual({r["stage"] for r in rows}, {"holdout"})
        self.assertEqual({r["rule"] for r in rows}, {"two_sided"})
        self.assertEqual({r["eligibility"] for r in rows}, {None})
        self.assertEqual(manifest["config"]["horizons"], [4])
        self.assertEqual(manifest["unique_solve_count"], 12)
        # A screen quote must not grow a horizons key: existing manifests rebuild byte-identically.
        screen = runner.quote(("syn_50sku_seed1001",), loader=lambda *_: demand, metadata=meta, stage="screen")
        self.assertNotIn("horizons", screen["config"])
        with self.assertRaises(ContractError):
            runner.quote(("syn_50sku_seed1001",), loader=lambda *_: demand, metadata=meta, stage="screen", horizons=(4,))
        with self.assertRaises(ContractError):
            runner.quote(("syn_50sku_seed1001",), loader=lambda *_: demand, metadata=meta, stage="holdout",
                         delta="0.02", rule="two_sided", horizons=(3,))
        with self.assertRaises(ContractError):
            runner.quote(("syn_50sku_seed1001",), loader=lambda *_: demand, metadata=meta, stage="holdout",
                         delta="0.02", rule="two_sided", max_origins=2)

    def test_holdout_quote_marks_a_too_long_horizon_ineligible_rather_than_dropping_it(self):
        from Baselines.horizon_robustness import runner
        meta = dict(backend="hexaly", interpreter="fixture", python="fixture",
                    packages={"hexaly": "fake"}, implementation_hash="fixture")
        demand = self._demand(90)
        manifest = runner.quote(("syn_50sku_seed1001",), loader=lambda *_: demand, metadata=meta,
                                stage="holdout", arms=("NOM",), delta="0.02", rule="two_sided")
        by_n = {r["n"]: r["eligibility"] for r in manifest["rows"]}
        self.assertEqual(by_n, {2: None, 4: None, 8: None} if 71 + 8 <= 90 else by_n)
        self.assertEqual(sorted(by_n), [2, 4, 8])


class HashStabilityTests(unittest.TestCase):
    def test_upper_only_hashes_are_byte_identical_to_the_pinned_values(self):
        catalogue, history = fixture()
        for arm, (input_hash, model_hash) in PINNED.items():
            with self.subTest(arm=arm):
                problem = build_training_problem(catalogue, history, 2, arm, "0.01", "0.01", "0.5")
                self.assertEqual(problem.input_hash, input_hash)
                self.assertEqual(problem.model_hash, model_hash)
                self.assertNotIn("rule", problem.to_dict())
                self.assertEqual(TrainingProblem.from_dict(problem.to_dict()).input_hash, input_hash)

    def test_two_sided_problem_has_its_own_identity(self):
        catalogue, history = fixture()
        upper = build_training_problem(catalogue, history, 2, "HIST", "0.02", "0.01", "0.5")
        two = build_training_problem(catalogue, history, 2, "HIST", "0.02", "0.01", "0.5", rule="two_sided")
        self.assertEqual(two.to_dict()["rule"], "two_sided")
        self.assertNotEqual(two.input_hash, upper.input_hash)
        self.assertNotEqual(two.model_hash, upper.model_hash)
        self.assertEqual(TrainingProblem.from_dict(two.to_dict()).model_hash, two.model_hash)
        self.assertTrue(two.two_sided)
        self.assertIsNone(upper.rational_floors())
        self.assertEqual(len(two.rational_floors()), catalogue.s)

    def test_unknown_rule_is_refused(self):
        catalogue, history = fixture()
        with self.assertRaisesRegex(ContractError, "unknown workload rule"):
            build_training_problem(catalogue, history, 2, "HIST", rule="lower_only")

    def test_protocol_grid_carries_the_new_settings(self):
        policy = Protocol()
        self.assertIn("0.03", policy.deltas)
        self.assertEqual(policy.two_sided_delta, "0.02")
        self.assertEqual(policy.rules, ("upper_only", "two_sided"))


class FloorTests(unittest.TestCase):
    def test_floors_are_clipped_at_zero_like_caps_at_one(self):
        catalogue, history = fixture()
        problem = build_training_problem(catalogue, history, 2, "HIST", "1", "0.01", "0.5", rule="two_sided")
        self.assertEqual(problem.rational_floors(), (Fraction(0), Fraction(0)))
        self.assertEqual(problem.rational_caps(), (Fraction(1), Fraction(1)))
        rows, _ = integer_cap_rows(problem)
        self.assertTrue(all(r["threshold"] == 0 for r in rows if r["sense"] == ">="))

    def test_tight_floor_uses_the_reduced_delta_in_optimization_only(self):
        catalogue, history = fixture()
        problem = build_training_problem(catalogue, history, 2, "TIGHT", "0.05", "0.01", "0.5", rule="two_sided")
        b = Fraction(problem.reference.station_line_counts[0], problem.reference.total_lines)
        self.assertEqual(problem.rational_floors()[0], max(Fraction(0), b - Fraction("0.05")))
        self.assertEqual(problem.rational_floors(True)[0], max(Fraction(0), b - Fraction("0.025")))

    def test_lower_rows_exist_only_under_the_two_sided_rule(self):
        catalogue, history = sparse_fixture()
        upper = build_training_problem(catalogue, history, 2, "HIST+ACT", "0.05", "0.01", "0.5")
        two = build_training_problem(catalogue, history, 2, "HIST+ACT", "0.05", "0.01", "0.5", rule="two_sided")
        self.assertEqual({r["sense"] for r, _ in [(x, 0) for x in integer_cap_rows(upper)[0]]}, {"<="})
        kinds = {r["kind"] for r in integer_cap_rows(two)[0]}
        self.assertEqual(kinds, {"base", "activation", "lower_base", "lower_activation"})
        for row in integer_cap_rows(two)[0]:
            if row["sense"] == ">=":
                self.assertEqual(row["activation_coefficient"], 0)   # activation mass sits elsewhere

    def test_lower_thresholds_are_exact_ceilings(self):
        catalogue, history = fixture()
        problem = build_training_problem(catalogue, history, 2, "HIST", "0.01", "0.01", "0.5", rule="two_sided")
        floors = problem.rational_floors(optimization=True)
        for row in integer_cap_rows(problem)[0]:
            if row["kind"] == "lower_base":
                exact = floors[row["station"]] * problem.effective_scenarios[row["scenario"]].total_lines
                self.assertGreaterEqual(Fraction(row["threshold"]), exact)
                self.assertLess(Fraction(row["threshold"]) - 1, exact)


class EquivalenceTests(unittest.TestCase):
    """Integer rows and the exact validator must agree on EVERY layout."""

    def check(self, catalogue, history, **kwargs):
        problem = build_training_problem(catalogue, history, 2, rule="two_sided", **kwargs)
        accepted = set()
        for assignment in layouts(catalogue, problem.reference.fixed):
            exact = validate_assignment(problem, assignment)["model_feasible_exact"]
            self.assertEqual(exact, satisfies_integer_rows(problem, assignment), f"{kwargs} {assignment}")
            if exact:
                accepted.add(assignment)
        return problem, accepted

    def test_all_arms_agree_with_the_validator(self):
        catalogue, history = fixture()
        for arm in ("NOM", "TIGHT", "HIST", "HIST+ACT"):
            with self.subTest(arm=arm):
                self.check(catalogue, history, arm=arm, delta="0.2", nu="0.01", tightening="0.5")

    def test_two_sided_accepts_a_subset_of_upper_only(self):
        catalogue, history = fixture()
        for delta in ("0.05", "0.2", "0.35"):
            with self.subTest(delta=delta):
                two, accepted_two = self.check(catalogue, history, arm="HIST", delta=delta, nu="0.01", tightening="0.5")
                upper = build_training_problem(catalogue, history, 2, "HIST", delta, "0.01", "0.5")
                accepted_upper = {a for a in layouts(catalogue, upper.reference.fixed)
                                  if validate_assignment(upper, a)["model_feasible_exact"]}
                self.assertTrue(accepted_two <= accepted_upper)
        # At a wide enough slack both rules accept something, so the subset
        # relation above is not vacuous.
        _, accepted = self.check(catalogue, history, arm="HIST", delta="0.35", nu="0.01", tightening="0.5")
        self.assertTrue(accepted)

    def test_activation_lower_rows_agree_and_nest_in_nu(self):
        catalogue, history = sparse_fixture()
        accepted = {}
        for nu in ("0", "0.01", "0.05", "1"):
            with self.subTest(nu=nu):
                _, accepted[nu] = self.check(catalogue, history, arm="HIST+ACT", delta="0.3", nu=nu, tightening="0.5")
        self.assertTrue(accepted["0"], "fixture must accept something at nu = 0")
        for a, b in (("0", "0.01"), ("0.01", "0.05"), ("0.05", "1")):
            self.assertTrue(accepted[b] <= accepted[a], f"raising nu {a}->{b} admitted a new layout")
        # nu = 1: every station's lowest share is 0, so any positive floor kills it.
        problem = build_training_problem(catalogue, history, 2, "HIST+ACT", "0.05", "1", "0.5", rule="two_sided")
        floors = problem.rational_floors(True)
        if any(f > 0 for f in floors):
            self.assertEqual(accepted["1"], set())

    def test_zero_slack_two_sided_agrees(self):
        catalogue, history = fixture()
        self.check(catalogue, history, arm="HIST", delta="0", nu="0.01", tightening="0.5")


class ScoringTests(unittest.TestCase):
    def test_downside_breach_fails_only_the_two_sided_rule(self):
        catalogue, history = fixture()
        upper = build_training_problem(catalogue, history, 2, "NOM", "0.05", "0.01", "0.5")
        two = build_training_problem(catalogue, history, 2, "NOM", "0.05", "0.01", "0.5", rule="two_sided")
        # A future that starves station s1: every line lands on products at s0
        # under the reference layout (0,1,0,1): products 0 and 2 sit at s0.
        future = orders(((0, 3), (2, 3)), ((0, 2),))
        reference = upper.reference.assignment
        up = evaluate_layout(upper, reference, future)
        down = evaluate_layout(two, reference, future)
        self.assertEqual(up["rule"], "upper_only")
        self.assertEqual(down["rule"], "two_sided")
        # s1 share is 0, far below its floor; s0 share is 1, above its cap: both rules fail on s0.
        self.assertFalse(up["joint_pass"])
        self.assertFalse(down["joint_pass"])
        self.assertGreater(down["floor_violation_count"], 0)
        self.assertGreater(down["violation_count"], up["violation_count"])
        self.assertIn("floors", down)
        self.assertNotIn("floors", up)
        self.assertGreaterEqual(down["worst_excess_percentage_points"], up["worst_excess_percentage_points"])

    def test_two_sided_pass_requires_both_sides(self):
        catalogue, history = fixture()
        two = build_training_problem(catalogue, history, 2, "NOM", "0.5", "0.01", "0.5", rule="two_sided")
        reference = two.reference.assignment
        # Balanced future: shares equal the targets exactly -> passes both sides.
        balanced = tuple(Order(f"F{i}", 100 + i, ((0, 1), (1, 1))) for i in range(2))
        evaluation = evaluate_layout(two, reference, balanced)
        self.assertTrue(all(s["floor"] is not None for s in evaluation["stations"]))
        self.assertEqual(evaluation["floor_violation_count"], 0)
        self.assertTrue(evaluation["joint_pass"])


class MinSlackTests(unittest.TestCase):
    def test_required_slack_covers_the_downside(self):
        catalogue, history = fixture()
        upper = build_training_problem(catalogue, history, 2, "HIST", "0.01", "0.01", "0.5")
        two = build_training_problem(catalogue, history, 2, "HIST", "0.01", "0.01", "0.5", rule="two_sided")
        for assignment in layouts(catalogue, two.reference.fixed):
            u = Fraction(validate_assignment(upper, assignment)["minimum_required_slack_exact"])
            t = Fraction(validate_assignment(two, assignment)["minimum_required_slack_exact"])
            self.assertGreaterEqual(t, u, str(assignment))
        # min_slack certification: eta equal to the two-sided requirement is valid.
        assignment = two.reference.assignment
        eta = Fraction(validate_assignment(two, assignment)["minimum_required_slack_exact"])
        certificate = validate_assignment(two, assignment, solve_mode="min_slack", min_slack=eta)
        self.assertTrue(certificate["valid"], certificate["violations"])
        self.assertEqual(certificate["rule"], "two_sided")


class RunnerTests(unittest.TestCase):
    META = dict(backend="hexaly", interpreter="fixture", python="fixture",
                packages={"hexaly": "fake"}, implementation_hash="fixture")

    def demand(self, count=40):
        catalogue = CatalogueManifest("syn_50sku_seed1001", "fixture", ("a", "b", "c", "d"), ("x", "y"), (2, 2))
        orders_ = tuple(Order(f"O{i}", i, tuple(sorted(((i % 4, 1), ((i + 1) % 4, 1))))) for i in range(count))
        return OrderedDemand(catalogue, orders_)

    def test_default_quote_carries_no_rule_key_anywhere(self):
        data = self.demand()
        manifest = runner.quote(("syn_50sku_seed1001",), loader=lambda *_: data, metadata=self.META,
                                stage="screen")
        self.assertNotIn("rule", manifest["config"])
        self.assertTrue(all("rule" not in row for row in manifest["rows"]))

    def test_two_sided_quote_requires_its_primary_delta_and_carries_the_rule(self):
        data = self.demand()
        with self.assertRaisesRegex(ContractError, "primary stages require primary parameters"):
            runner.quote(("syn_50sku_seed1001",), loader=lambda *_: data, metadata=self.META,
                         stage="screen", rule="two_sided")            # delta defaults to 0.01
        manifest = runner.quote(("syn_50sku_seed1001",), loader=lambda *_: data, metadata=self.META,
                                stage="screen", rule="two_sided", delta="0.02")
        self.assertEqual(manifest["config"]["rule"], "two_sided")
        self.assertTrue(all(row["rule"] == "two_sided" for row in manifest["rows"]))
        sensitivity = runner.quote(("syn_50sku_seed1001",), loader=lambda *_: data, metadata=self.META,
                                   stage="sensitivity", sensitivity="delta", rule="two_sided", delta="0.03")
        self.assertEqual(sensitivity["config"]["delta"], "0.03")
        upper = runner.quote(("syn_50sku_seed1001",), loader=lambda *_: data, metadata=self.META,
                             stage="sensitivity", sensitivity="delta", delta="0.02")
        self.assertNotEqual({r["case_id"] for r in manifest["rows"]}, {r["case_id"] for r in upper["rows"]})


class CplexTwoSidedTests(unittest.TestCase):
    def test_two_sided_solve_is_validated_two_sided_and_never_beats_upper_only(self):
        from Baselines.horizon_robustness import cplex_backend
        catalogue, history = fixture()
        upper = build_training_problem(catalogue, history, 2, "HIST", "0.35", "0.01", "0.5")
        two = build_training_problem(catalogue, history, 2, "HIST", "0.35", "0.01", "0.5", rule="two_sided")
        best_upper = min(validate_assignment(upper, a)["actual_visit_count"]
                         for a in layouts(catalogue, upper.reference.fixed)
                         if validate_assignment(upper, a)["model_feasible_exact"])
        best_two = min(validate_assignment(two, a)["actual_visit_count"]
                       for a in layouts(catalogue, two.reference.fixed)
                       if validate_assignment(two, a)["model_feasible_exact"])
        self.assertGreaterEqual(best_two, best_upper)
        result = cplex_backend.solve(two, seed=11, threads=1, time_limit=5)
        self.assertIn(result.status.value, ("FEASIBLE", "OPTIMAL_WITHIN_TOLERANCE"), dict(result.audit))
        certificate = validate_assignment(two, result.assignment, objective=result.objective, history=history)
        self.assertTrue(certificate["valid"], certificate["violations"])
        self.assertEqual(certificate["rule"], "two_sided")
        self.assertEqual(result.objective, best_two)

    def test_trapped_activation_is_admitted_natively(self):
        from Baselines.horizon_robustness import cplex_backend
        catalogue, history = reviewer_fixture()
        problem = build_training_problem(catalogue, history, 2, "HIST+ACT", "0.01", "0.05", "0.5",
                                         rule="two_sided")
        feasible = {a: validate_assignment(problem, a)["actual_visit_count"]
                    for a in layouts(catalogue, problem.reference.fixed)
                    if validate_assignment(problem, a)["model_feasible_exact"]}
        self.assertIn((0, 1, 1, 0), feasible)
        result = cplex_backend.solve(problem, seed=11, threads=1, time_limit=5)
        self.assertIn(result.status.value, ("FEASIBLE", "OPTIMAL_WITHIN_TOLERANCE"), dict(result.audit))
        self.assertIn(result.assignment, feasible)
        self.assertEqual(result.objective, min(feasible.values()))
        self.assertEqual(dict(result.audit)["row_formulation"], "exact_integer_counts_v3")

    def test_min_slack_with_activation_matches_enumeration_on_both_sides(self):
        from Baselines.horizon_robustness import cplex_backend
        for catalogue, history in (sparse_fixture(), two_inactive_fixture()):
            problem = build_training_problem(catalogue, history, 2, "HIST+ACT", "0.01", "0.05", "0.5",
                                             rule="two_sided")
            best = min(Fraction(validate_assignment(problem, a)["minimum_required_slack_exact"])
                       for a in layouts(catalogue, problem.reference.fixed))
            result = cplex_backend.solve(problem, seed=11, threads=1, time_limit=5, solve_mode="min_slack")
            self.assertIn(result.status.value, ("FEASIBLE", "OPTIMAL_WITHIN_TOLERANCE"), dict(result.audit))
            self.assertAlmostEqual(result.objective, float(best), delta=1e-7)
            certificate = validate_assignment(problem, result.assignment, objective=result.objective,
                                              solve_mode="min_slack", min_slack=result.objective)
            self.assertTrue(certificate["valid"], certificate["violations"])

    def test_tightened_scenario_arm_solves_natively_and_matches_enumeration(self):
        from Baselines.horizon_robustness import cplex_backend
        catalogue, history = sparse_fixture()
        problem = build_training_problem(catalogue, history, 2, "HIST+ACT-T", "0.3", "0.05", "0.5", rule="two_sided")
        feasible = {a: validate_assignment(problem, a)["actual_visit_count"]
                    for a in layouts(catalogue, problem.reference.fixed)
                    if validate_assignment(problem, a)["model_feasible_exact"]}
        self.assertTrue(feasible)
        result = cplex_backend.solve(problem, seed=11, threads=1, time_limit=5)
        self.assertIn(result.status.value, ("FEASIBLE", "OPTIMAL_WITHIN_TOLERANCE"), dict(result.audit))
        self.assertIn(result.assignment, feasible)
        self.assertEqual(result.objective, min(feasible.values()))
        certificate = validate_assignment(problem, result.assignment, objective=result.objective, history=history)
        self.assertTrue(certificate["valid"], certificate["violations"])


if __name__ == "__main__":
    unittest.main()
