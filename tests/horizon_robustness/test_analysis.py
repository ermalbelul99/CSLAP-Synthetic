"""Analysis-layer controls on synthetic campaign artifacts.

No campaign is executed here. Every fixture is a hand-built artifact tree, so
each control states an outcome the analysis code must produce or refuse.
"""

import json
from pathlib import Path
import tempfile
import unittest

from Baselines.horizon_robustness.protocol import ContractError, canonical_json, digest
from Baselines.horizon_robustness_analysis import analysis


def _row(**overrides):
    row = dict(stage="screen", dataset_id="syn_50sku_seed1001", catalogue_hash="c",
               source_files=[{"path": "exp02a_instances/syn_50sku_seed1001/syn_50sku_orders.csv",
                              "sha256": "s", "size_bytes": 1}],
               source_hash="sh", history_hash="hh", input_hash="ih", model_hash="mh",
               origin=100, n=50, arm="NOM", delta="0.01", nu="0.01", tightening="0.5",
               seed=11, backend="hexaly", solve_mode="visits", threads=1, time_limit=120,
               eligibility=None, solve_key="k" * 64)
    row.update(overrides)
    row["case_id"] = digest(row)
    row["expected_result"] = f"cases/{row['case_id']}.json"
    return row


def _evaluation(*, joint_pass, worst_pp, mean_visits, violations=0, activation=0.0):
    return dict(joint_pass=joint_pass, violation_count=violations,
                worst_excess_percentage_points=worst_pp,
                worst_excess_percentage_points_exact=str(worst_pp),
                positive_excess_sum=worst_pp / 100.0, maximum_residual=worst_pp / 100.0,
                borderline=False, mean_visits=mean_visits, mean_visits_exact=str(mean_visits),
                visit_count=int(mean_visits * 50), historical_mean_visits=4.0,
                historical_visit_count=400, total_lines=500, order_count=50,
                activation_mass=activation, activation_mass_exact=str(activation),
                effective_nu=0.01, inactive_product_count=3, realized_inactive_product_count=1,
                active_product_fraction=0.9, horizon_per_product=1.0, station_novelty_count=0,
                maximum_novelty_excess=0.0, novel_support_order_count=0,
                effective_total_allowance=0.02, layout_hash="lh", future_hash="fh",
                evaluation_kind="primary_same_horizon", stations=[],
                future_boundaries=dict(stream_adjacency_verified=True, start=100, stop=150),
                assignment=[0, 0, 1, 1])


class CampaignFixture(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name) / "camp"
        (self.directory / "cases").mkdir(parents=True)

    def build(self, rows, records, *, runtime=None, directory=None):
        directory = self.directory if directory is None else directory
        (directory / "cases").mkdir(parents=True, exist_ok=True)
        manifest = dict(revision="horizon-cslap-1.0", artifact_schema=2, kind="dry_quote",
                        config=dict(stage="screen"), runtime=runtime or {}, rows=rows,
                        unique_solve_count=len(rows), reused_row_count=0,
                        solver_seconds=sum(r["time_limit"] for r in rows))
        manifest["manifest_hash"] = digest(manifest)
        (directory / "manifest.json").write_text(canonical_json(manifest), encoding="utf-8")
        for row, record in zip(rows, records):
            if record is None:
                continue
            record = dict(record, case=row)
            record["artifact_hash"] = digest({k: v for k, v in record.items() if k != "artifact_hash"})
            (directory / "cases" / f"{row['case_id']}.json").write_text(
                canonical_json(record), encoding="utf-8")
            if record["status"] in analysis.SCORED_STATUSES:
                (directory / "cases" / f"{row['case_id']}.frozen.json").write_text(
                    canonical_json(dict(case_id=row["case_id"])), encoding="utf-8")
        return manifest


class MissingResultTests(CampaignFixture):
    def test_missing_allocation_never_becomes_a_zero_valued_observation(self):
        rows = [_row(arm="NOM"), _row(arm="HIST+ACT")]
        records = [dict(status="COMPLETE", solve_result=dict(assignment=[0, 0, 1, 1], objective=390.0,
                                                             native_status="FEASIBLE", status="FEASIBLE",
                                                             bound=None, gap=None,
                                                             bound_provenance="unavailable",
                                                             build_seconds=1.0, solve_seconds=120.0),
                        validation=dict(valid=True, model_feasible=True, actual_visit_count=390),
                        evaluation=_evaluation(joint_pass=False, worst_pp=2.0, mean_visits=3.8, violations=2),
                        reference_evaluation=_evaluation(joint_pass=True, worst_pp=0.0, mean_visits=4.34),
                        accepted_training_solution=True),
                   dict(status="NO_INCUMBENT_LIMIT", solve_result=dict(assignment=None, objective=None,
                                                                       native_status="LIMIT", status="NO_INCUMBENT_LIMIT",
                                                                       bound=None, gap=None,
                                                                       bound_provenance="unavailable",
                                                                       build_seconds=2.0, solve_seconds=120.0),
                        validation=None, evaluation=None, reference_evaluation=None)]
        self.build(rows, records)
        frame = analysis.case_frame(analysis.load_campaign(self.directory))
        unallocated = next(r for r in frame if r["arm"] == "HIST+ACT")
        for metric in ("joint_pass", "mean_visits", "worst_excess_pp", "violation_count"):
            self.assertIsNone(unallocated[metric], metric)
        self.assertFalse(unallocated["allocation_returned"])
        self.assertEqual(unallocated["status"], "NO_INCUMBENT_LIMIT")
        totals = analysis.campaign_totals(frame)
        self.assertEqual(totals["authorized_rows"], 2)
        self.assertEqual(totals["accounting_complete"], 1)
        self.assertEqual(totals["no_allocation"], 1)
        self.assertEqual(totals["scored"], 1)

    def test_row_with_no_case_file_is_reported_not_dropped(self):
        rows = [_row(arm="NOM"), _row(arm="HIST")]
        self.build(rows, [None, None])
        frame = analysis.case_frame(analysis.load_campaign(self.directory))
        self.assertEqual(len(frame), 2)
        self.assertEqual({r["record_source"] for r in frame}, {"missing"})
        self.assertEqual({r["status"] for r in frame}, {"MISSING_RECORD"})
        self.assertEqual(analysis.campaign_totals(frame)["no_record"], 2)

    def test_ineligible_rows_keep_their_own_bin_and_denominator(self):
        rows = [_row(arm="NOM", n=100, eligibility="INSUFFICIENT_FUTURE")]
        self.build(rows, [dict(status="INSUFFICIENT_FUTURE", solve_result=None, validation=None,
                               evaluation=None, reference_evaluation=None)])
        frame = analysis.case_frame(analysis.load_campaign(self.directory))
        totals = analysis.campaign_totals(frame)
        self.assertEqual((totals["ineligible"], totals["authorized_rows"]), (1, 1))
        self.assertEqual(totals["accounting_complete"], 1)


class TamperTests(CampaignFixture):
    def test_edited_case_artifact_is_refused(self):
        rows = [_row()]
        self.build(rows, [dict(status="COMPLETE", solve_result=dict(assignment=[0, 0, 1, 1]),
                               validation=dict(valid=True), evaluation=_evaluation(
                                   joint_pass=True, worst_pp=0.0, mean_visits=3.0),
                               reference_evaluation=None)])
        path = self.directory / "cases" / f"{rows[0]['case_id']}.json"
        record = json.loads(path.read_text(encoding="utf-8"))
        record["evaluation"]["joint_pass"] = False          # flip a headline result
        path.write_text(canonical_json(record), encoding="utf-8")
        with self.assertRaisesRegex(ContractError, "certificate"):
            analysis.load_campaign(self.directory)

    def test_edited_manifest_is_refused(self):
        rows = [_row()]
        manifest = self.build(rows, [None])
        manifest["rows"][0]["delta"] = "0.05"
        (self.directory / "manifest.json").write_text(canonical_json(manifest), encoding="utf-8")
        with self.assertRaisesRegex(ContractError, "MANIFEST_CHANGED"):
            analysis.load_campaign(self.directory)


class PairingTests(CampaignFixture):
    def _scored(self, arm, joint, pp, visits):
        return dict(status="COMPLETE",
                    solve_result=dict(assignment=[0, 0, 1, 1], objective=1.0, native_status="F",
                                      status="FEASIBLE", bound=None, gap=None,
                                      bound_provenance="unavailable", build_seconds=1.0,
                                      solve_seconds=10.0),
                    validation=dict(valid=True, model_feasible=True, actual_visit_count=1),
                    evaluation=_evaluation(joint_pass=joint, worst_pp=pp, mean_visits=visits),
                    reference_evaluation=_evaluation(joint_pass=True, worst_pp=0.0, mean_visits=4.3),
                    accepted_training_solution=True)

    def test_pairs_form_only_inside_one_matched_cell(self):
        rows = [_row(arm="NOM"), _row(arm="HIST+ACT"), _row(arm="NOM", n=100), _row(arm="HIST+ACT", n=100)]
        records = [self._scored("NOM", False, 2.0, 3.8), self._scored("HIST+ACT", True, 0.0, 4.1),
                   self._scored("NOM", False, 1.0, 3.9), self._scored("HIST+ACT", True, 0.0, 4.2)]
        self.build(rows, records)
        frame = analysis.case_frame(analysis.load_campaign(self.directory))
        pairs = analysis.paired_rows(frame, baselines=("NOM",))
        self.assertEqual(len(pairs), 2)                        # one per horizon, never crossed
        self.assertEqual({p["n"] for p in pairs}, {50, 100})
        for pair in pairs:
            self.assertTrue(pair["both_scored"])
            self.assertAlmostEqual(pair["worst_excess_pp_diff"], -2.0 if pair["n"] == 50 else -1.0)
            self.assertGreater(pair["mean_visits_diff"], 0)    # protection costs visits
            self.assertGreater(pair["visit_cost_pct"], 0)

    def test_pair_needs_both_members_scored(self):
        rows = [_row(arm="NOM"), _row(arm="HIST+ACT")]
        records = [self._scored("NOM", False, 2.0, 3.8),
                   dict(status="REJECTED_CANDIDATE", solve_result=dict(assignment=[0, 0, 1, 1]),
                        validation=dict(valid=False), evaluation=None, reference_evaluation=None)]
        self.build(rows, records)
        frame = analysis.case_frame(analysis.load_campaign(self.directory))
        pair = analysis.paired_rows(frame, baselines=("NOM",))[0]
        self.assertFalse(pair["both_scored"])
        self.assertIsNone(pair["worst_excess_pp_diff"])
        self.assertEqual(pair["arm_status"], "REJECTED_CANDIDATE")

    def test_instance_is_the_unit_so_seeds_are_not_extra_futures(self):
        rows, records = [], []
        for seed in (11, 22, 33):
            rows.append(_row(arm="NOM", seed=seed))
            records.append(self._scored("NOM", False, 2.0, 3.8))
            rows.append(_row(arm="HIST+ACT", seed=seed))
            records.append(self._scored("HIST+ACT", True, 0.0, 4.1))
        self.build(rows, records)
        frame = analysis.case_frame(analysis.load_campaign(self.directory))
        instances = analysis.instance_summary(frame)
        nominal = next(i for i in instances if i["arm"] == "NOM")
        self.assertEqual((nominal["cells"], nominal["distinct_seeds"]), (3, 3))
        stratum = analysis.stratum_summary(instances)
        for entry in stratum:
            # three seeds of one dataset are ONE instance, never three.
            self.assertEqual(entry["instances"], 1)
            self.assertEqual(entry["total_cells"], 3)
        paired = analysis.paired_stratum_summary(analysis.paired_rows(frame, baselines=("NOM",)))
        self.assertEqual([p["paired_instances"] for p in paired], [1])


class FrontierTests(CampaignFixture):
    def test_frontier_retains_infeasible_and_unresolved_cases(self):
        rows = [_row(arm="HIST+ACT", delta=value) for value in ("0", "0.01", "0.05")]
        records = [
            dict(status="NO_INCUMBENT_LIMIT",
                 solve_result=dict(assignment=None, status="NO_INCUMBENT_LIMIT", native_status="LIMIT",
                                   objective=None, bound=None, gap=None, bound_provenance="unavailable",
                                   build_seconds=1.0, solve_seconds=120.0),
                 validation=None, evaluation=None, reference_evaluation=None),
            dict(status="COMPLETE",
                 solve_result=dict(assignment=[0, 0, 1, 1], status="FEASIBLE", native_status="F",
                                   objective=1.0, bound=None, gap=None, bound_provenance="unavailable",
                                   build_seconds=1.0, solve_seconds=10.0),
                 validation=dict(valid=True, model_feasible=True, actual_visit_count=1,
                                 minimum_required_slack=0.007),
                 evaluation=_evaluation(joint_pass=True, worst_pp=0.0, mean_visits=4.1),
                 reference_evaluation=None, accepted_training_solution=True),
            dict(status="REJECTED_CANDIDATE",
                 solve_result=dict(assignment=[0, 0, 1, 1], status="PROVEN_INFEASIBLE",
                                   native_status="INCONSISTENT", objective=None, bound=None, gap=None,
                                   bound_provenance="unavailable", build_seconds=1.0, solve_seconds=3.0),
                 validation=dict(valid=False), evaluation=None, reference_evaluation=None)]
        self.build(rows, records)
        frame = analysis.case_frame(analysis.load_campaign(self.directory))
        frontier = analysis.frontier_table(frame, "delta")
        self.assertEqual(len(frontier), 3)                    # nothing filtered away
        by_value = {f["value"]: f for f in frontier}
        self.assertEqual(by_value["0"]["no_allocation"], 1)
        self.assertEqual(by_value["0"]["no_incumbent"], 1)
        self.assertEqual(by_value["0"]["scored_cells"], 0)
        self.assertEqual(by_value["0.05"]["rejected_candidates"], 1)
        self.assertEqual(by_value["0.05"]["proven_infeasible"], 1)
        self.assertEqual(by_value["0.01"]["joint_pass"], 1)
        self.assertEqual(sum(f["cells"] for f in frontier), 3)

    def test_min_slack_bounds_separate_resolved_from_unresolved(self):
        rows = [_row(solve_mode="min_slack", arm="HIST+ACT", seed=seed) for seed in (11, 22, 33)]
        records = [
            dict(status="DIAGNOSTIC_COMPLETE",
                 solve_result=dict(assignment=[0, 0, 1, 1], status="FEASIBLE", native_status="F",
                                   objective=0.02, bound=0.015, gap=0.25,
                                   bound_provenance="native_lower_bound", build_seconds=1.0,
                                   solve_seconds=10.0),
                 validation=dict(valid=True, model_feasible=True, actual_visit_count=1,
                                 minimum_required_slack=0.02),
                 evaluation=None, reference_evaluation=None),
            dict(status="DIAGNOSTIC_COMPLETE",
                 solve_result=dict(assignment=[0, 0, 1, 1], status="FEASIBLE", native_status="F",
                                   objective=0.03, bound=None, gap=None,
                                   bound_provenance="unavailable", build_seconds=1.0, solve_seconds=10.0),
                 validation=dict(valid=True, model_feasible=True, actual_visit_count=1,
                                 minimum_required_slack=0.03),
                 evaluation=None, reference_evaluation=None),
            dict(status="NO_INCUMBENT_LIMIT",
                 solve_result=dict(assignment=None, status="NO_INCUMBENT_LIMIT", native_status="LIMIT",
                                   objective=None, bound=None, gap=None, bound_provenance="unavailable",
                                   build_seconds=1.0, solve_seconds=120.0),
                 validation=None, evaluation=None, reference_evaluation=None)]
        self.build(rows, records)
        frame = analysis.case_frame(analysis.load_campaign(self.directory))
        table = {r["seed"]: r for r in analysis.min_slack_table(frame)}
        self.assertEqual(table[11]["resolution"], "BOUNDED")
        self.assertEqual(table[11]["eta_lower_bound"], 0.015)
        self.assertTrue(table[11]["exceeds_declared_delta"])          # 0.015 > declared 0.01
        self.assertEqual(table[22]["resolution"], "UPPER_BOUND_ONLY")
        self.assertIsNone(table[22]["eta_lower_bound"])
        self.assertIsNone(table[22]["exceeds_declared_delta"])
        self.assertEqual(table[33]["resolution"], "UNRESOLVED")       # a limit proves nothing
        self.assertIsNone(table[33]["eta_upper_bound"])

    def test_ineligible_cell_survives_instance_summary_with_its_reason(self):
        """Skipping ineligible rows would delete a whole (dataset, n) combination."""
        rows = [_row(arm="NOM", n=100, eligibility="INSUFFICIENT_FUTURE"), _row(arm="NOM", n=50)]
        self.build(rows, [dict(status="INSUFFICIENT_FUTURE", solve_result=None, validation=None,
                               evaluation=None, reference_evaluation=None),
                          dict(status="COMPLETE",
                               solve_result=dict(assignment=[0, 0, 1, 1], objective=1.0,
                                                 native_status="F", status="FEASIBLE", bound=None,
                                                 gap=None, bound_provenance="unavailable",
                                                 build_seconds=1.0, solve_seconds=1.0),
                               validation=dict(valid=True, model_feasible=True, actual_visit_count=1),
                               evaluation=_evaluation(joint_pass=True, worst_pp=0.0, mean_visits=3.0),
                               reference_evaluation=None, accepted_training_solution=True)])
        frame = analysis.case_frame(analysis.load_campaign(self.directory))
        summary = {r["n"]: r for r in analysis.instance_summary(frame)}
        self.assertEqual(sorted(summary), [50, 100])
        self.assertEqual(summary[100]["ineligible_cells"], 1)
        self.assertEqual(summary[100]["scored_cells"], 0)
        self.assertEqual(summary[100]["eligibility_reasons"], "INSUFFICIENT_FUTURE")
        self.assertEqual(summary[50]["ineligible_cells"], 0)

    def test_zero_lower_bound_is_not_reported_as_bounded(self):
        """eta >= 0 by construction, so a bound of 0 restricts nothing."""
        rows = [_row(solve_mode="min_slack", arm="HIST", seed=11)]
        self.build(rows, [dict(status="DIAGNOSTIC_COMPLETE",
                               solve_result=dict(assignment=[0, 0, 1, 1], status="FEASIBLE",
                                                 native_status="F", objective=0.02, bound=0.0,
                                                 gap=1.0,
                                                 bound_provenance="Hexaly_HxSolution.get_objective_bound(0)",
                                                 build_seconds=1.0, solve_seconds=1.0),
                               validation=dict(valid=True, model_feasible=True, actual_visit_count=1,
                                               minimum_required_slack=0.02),
                               evaluation=None, reference_evaluation=None)])
        frame = analysis.case_frame(analysis.load_campaign(self.directory))
        entry = analysis.min_slack_table(frame)[0]
        self.assertEqual(entry["resolution"], "UPPER_BOUND_ONLY")
        self.assertEqual(entry["eta_upper_bound"], 0.02)
        self.assertFalse(entry["exceeds_declared_delta"])


class StationTableTests(CampaignFixture):
    def test_missing_publication_alias_is_refused(self):
        rows = [_row(dataset_id="BERNER")]
        evaluation = _evaluation(joint_pass=True, worst_pp=0.0, mean_visits=1.0)
        evaluation["stations"] = [dict(station_index=0, station_id="01.E4", occupancy=2, capacity=2,
                                       target=0.5, cap=0.51, share=0.49, residual=-0.02,
                                       positive_excess=0.0, decrease=0.01, implied_lower_bound=0.0,
                                       historical_share=0.5, fixed_share=0.1,
                                       fixed_historical_share=0.1, inactive_count=0,
                                       inactive_share=0.0, worst_share=0.5, novelty_residual=-0.01,
                                       beyond_worst_scenario=False, feasible=True, borderline=False,
                                       cap_relative_to_target=1.02)]
        self.build(rows, [dict(status="COMPLETE", solve_result=dict(assignment=[0, 0, 1, 1]),
                               validation=dict(valid=True), evaluation=evaluation,
                               reference_evaluation=None)])
        campaign = analysis.load_campaign(self.directory)
        with self.assertRaisesRegex(ContractError, "alias"):
            analysis.station_table(campaign, aliases={"01.30": "S_3"})
        table = analysis.station_table(campaign, aliases={"01.E4": "S_7"})
        self.assertEqual(table[0]["station"], "S_7")
        self.assertNotIn("01.E4", canonical_json(table))       # no site code survives


class HorizonLabelTests(unittest.TestCase):
    def test_half_horizon_is_not_collapsed_to_zero(self):
        """Integer division would report n = P/2 as multiple 0, merging strata."""
        self.assertEqual(analysis.horizon_multiple(25, 50), "1/2")
        self.assertEqual(analysis.horizon_multiple(50, 50), "1")
        self.assertEqual(analysis.horizon_multiple(100, 50), "2")
        self.assertEqual(analysis.horizon_multiple(10937, 21874), "1/2")
        self.assertIsNone(analysis.horizon_multiple(50, None))


class LeanLoadingTests(CampaignFixture):
    def test_lean_verifies_the_full_record_before_releasing_arrays(self):
        """The certificate must be checked against the complete record."""
        rows = [_row()]
        self.build(rows, [dict(status="COMPLETE",
                               solve_result=dict(assignment=[0, 0, 1, 1], objective=1.0,
                                                 native_status="F", status="FEASIBLE", bound=None,
                                                 gap=None, bound_provenance="unavailable",
                                                 build_seconds=1.0, solve_seconds=1.0),
                               validation=dict(valid=True, model_feasible=True, actual_visit_count=1),
                               evaluation=_evaluation(joint_pass=True, worst_pp=0.0, mean_visits=3.0),
                               reference_evaluation=None, accepted_training_solution=True)])
        lean = analysis.load_campaign(self.directory, lean=True)
        full = analysis.load_campaign(self.directory)
        self.assertEqual(full["entries"][0]["record"]["evaluation"]["assignment"], [0, 0, 1, 1])
        self.assertIsInstance(lean["entries"][0]["record"]["evaluation"]["assignment"], str)
        # Every scalar a table reads survives the strip unchanged.
        lean_row = analysis.case_frame(lean)[0]
        full_row = analysis.case_frame(full)[0]
        for key in ("catalogue_size", "joint_pass", "mean_visits", "worst_excess_pp",
                    "violation_count", "status", "scored", "allocation_returned"):
            self.assertEqual(lean_row[key], full_row[key], key)

    def test_lean_still_rejects_a_tampered_record(self):
        rows = [_row()]
        self.build(rows, [dict(status="COMPLETE", solve_result=dict(assignment=[0, 0, 1, 1]),
                               validation=dict(valid=True),
                               evaluation=_evaluation(joint_pass=True, worst_pp=0.0, mean_visits=3.0),
                               reference_evaluation=None)])
        path = self.directory / "cases" / f"{rows[0]['case_id']}.json"
        record = json.loads(path.read_text(encoding="utf-8"))
        record["evaluation"]["mean_visits"] = 99.0
        path.write_text(canonical_json(record), encoding="utf-8")
        with self.assertRaisesRegex(ContractError, "certificate"):
            analysis.load_campaign(self.directory, lean=True)


class CrossCampaignIsolationTests(CampaignFixture):
    """Two campaigns must never be merged into one analysis cell.

    They can hold the same (dataset, origin, n, seed, parameter) cell under
    DIFFERENT implementation versions. Merging them mixes versions, and lets a
    later campaign's not-yet-executed row overwrite an earlier real result --
    which is exactly what happened before the campaign key was added.
    """

    def _two_campaigns(self):
        rows = [_row(arm="NOM"), _row(arm="HIST+ACT")]
        scored = dict(status="COMPLETE",
                      solve_result=dict(assignment=[0, 0, 1, 1], objective=1.0, native_status="F",
                                        status="FEASIBLE", bound=None, gap=None,
                                        bound_provenance="unavailable", build_seconds=1.0,
                                        solve_seconds=1.0),
                      validation=dict(valid=True, model_feasible=True, actual_visit_count=1),
                      evaluation=_evaluation(joint_pass=True, worst_pp=0.0, mean_visits=3.0),
                      reference_evaluation=None, accepted_training_solution=True)
        self.build(rows, [scored, scored])
        first = analysis.case_frame(analysis.load_campaign(self.directory))
        # A second campaign with the SAME cells but no results written yet.
        other = self.directory.parent / "later"
        (other / "cases").mkdir(parents=True)
        (other / "manifest.json").write_text(
            (self.directory / "manifest.json").read_text(encoding="utf-8"), encoding="utf-8")
        second = analysis.case_frame(analysis.load_campaign(other))
        return first + second

    def test_an_unexecuted_campaign_cannot_overwrite_a_scored_one(self):
        frame = self._two_campaigns()
        self.assertEqual({r["campaign"] for r in frame}, {"camp", "later"})
        pairs = analysis.paired_rows(frame, baselines=("NOM",))
        scored_pairs = [p for p in pairs if p["both_scored"]]
        self.assertEqual(len(scored_pairs), 1, "the executed campaign's pair must survive")
        self.assertEqual(scored_pairs[0]["campaign"], "camp")
        self.assertEqual(len(pairs), 2, "each campaign contributes its own cell")

    def test_instance_and_stratum_summaries_stay_separated_by_campaign(self):
        frame = self._two_campaigns()
        instances = analysis.instance_summary(frame)
        self.assertEqual({i["campaign"] for i in instances}, {"camp", "later"})
        for entry in instances:
            self.assertEqual(entry["cells"], 1, "campaigns must not be pooled into one cell count")
        strata = analysis.stratum_summary(instances)
        self.assertEqual({s["campaign"] for s in strata}, {"camp", "later"})
        paired = analysis.paired_stratum_summary(analysis.paired_rows(frame, baselines=("NOM",)))
        self.assertEqual([p["campaign"] for p in paired], ["camp"])
        self.assertEqual(paired[0]["paired_instances"], 1)


class MetricDirectionTests(CampaignFixture):
    """A paired difference is 'better' only in the metric's own good direction.

    joint_pass is a success indicator, so arm-minus-baseline > 0 is the good
    outcome; for violation counts and excess it is < 0. The earlier code counted
    every negative difference as better, which reversed joint_pass.
    """

    def _scored(self, joint, pp, visits):
        return dict(status="COMPLETE",
                    solve_result=dict(assignment=[0, 0, 1, 1], objective=1.0, native_status="F",
                                      status="FEASIBLE", bound=None, gap=None,
                                      bound_provenance="unavailable", build_seconds=1.0,
                                      solve_seconds=1.0),
                    validation=dict(valid=True, model_feasible=True, actual_visit_count=1),
                    evaluation=_evaluation(joint_pass=joint, worst_pp=pp, mean_visits=visits),
                    reference_evaluation=None, accepted_training_solution=True)

    def test_arm_that_passes_where_baseline_fails_is_counted_better(self):
        rows = [_row(arm="NOM"), _row(arm="HIST")]
        # NOM fails with 2 pp excess; HIST passes with 0 excess at more visits.
        self.build(rows, [self._scored(False, 2.0, 3.8), self._scored(True, 0.0, 4.1)])
        frame = analysis.case_frame(analysis.load_campaign(self.directory))
        summary = analysis.paired_stratum_summary(analysis.paired_rows(frame, baselines=("NOM",)))[0]
        self.assertEqual(summary["joint_pass_mean_diff"], 1.0)
        self.assertEqual(summary["joint_pass_instances_better"], 1)
        self.assertEqual(summary["joint_pass_instances_worse"], 0)
        self.assertEqual(summary["worst_excess_pp_instances_better"], 1)   # lower excess
        self.assertEqual(summary["mean_visits_instances_worse"], 1)        # more visits
        self.assertIsNone(summary["activation_mass_instances_better"])    # descriptive

    def test_old_sign_rule_would_have_reversed_joint_pass(self):
        """Negative control: the reversed rule must disagree with the fixed one."""
        rows = [_row(arm="NOM"), _row(arm="HIST")]
        self.build(rows, [self._scored(False, 2.0, 3.8), self._scored(True, 0.0, 4.1)])
        frame = analysis.case_frame(analysis.load_campaign(self.directory))
        pairs = analysis.paired_rows(frame, baselines=("NOM",))
        diff = pairs[0]["joint_pass_diff"]
        self.assertGreater(diff, 0)
        old_rule_better = diff < 0
        new_rule_better = diff * analysis.METRIC_DIRECTION["joint_pass"] > 0
        self.assertNotEqual(old_rule_better, new_rule_better)


class RuleColumnTests(CampaignFixture):
    """Every table row names its rule, so two-sided rows can never pass as upper-only.

    Exploratory revision 2 added a two-sided rule whose rows carry ``rule`` in
    the manifest; earlier manifests have no such key and are upper-only by
    construction. Both cases must label every derived table.
    """

    @staticmethod
    def _scored(stations=(), floors=None):
        evaluation = _evaluation(joint_pass=False, worst_pp=1.0, mean_visits=3.0, violations=1)
        evaluation.update(stations=list(stations))
        if floors is not None:
            evaluation.update(cap_violation_count=0, floor_violation_count=floors)
        return dict(status="COMPLETE",
                    solve_result=dict(assignment=[0, 0, 1, 1], objective=1.0, native_status="F",
                                      status="FEASIBLE", bound=None, gap=None,
                                      bound_provenance="unavailable", build_seconds=1.0,
                                      solve_seconds=1.0),
                    validation=dict(valid=True, model_feasible=True, actual_visit_count=1),
                    evaluation=evaluation, reference_evaluation=None,
                    accepted_training_solution=True)

    @staticmethod
    def _station(**overrides):
        station = dict(station_id="x", station_index=0, capacity=2, occupancy=2, target=0.5,
                       cap=0.52, share=0.47, residual=-0.05, positive_excess=0.0, decrease=0.03,
                       implied_lower_bound=0.48, historical_share=0.5, fixed_share=0.0,
                       fixed_historical_share=0.0, inactive_count=0, inactive_share=0.0,
                       worst_share=0.5, novelty_residual=0.0, beyond_worst_scenario=False,
                       feasible=False, borderline=False, cap_relative_to_target=0.02)
        station.update(overrides)
        return station

    def test_two_sided_rows_carry_the_rule_and_floor_fields_in_every_table(self):
        station = self._station(floor=0.48, floor_residual=0.01, below_floor=True)
        rows = [_row(arm="NOM", rule="two_sided", delta="0.02"),
                _row(arm="HIST", rule="two_sided", delta="0.02")]
        self.build(rows, [self._scored([station], floors=1), self._scored([station], floors=1)],
                   runtime=dict(implementation_hash="impl-two"))
        campaign = analysis.load_campaign(self.directory)
        frame = analysis.case_frame(campaign)
        self.assertEqual({r["rule"] for r in frame}, {"two_sided"})
        self.assertEqual({r["implementation_hash"] for r in frame}, {"impl-two"})
        self.assertEqual({r["floor_violation_count"] for r in frame}, {1})
        self.assertEqual({r["cap_violation_count"] for r in frame}, {0})
        tables = dict(status=analysis.status_table(frame),
                      resources=analysis.resource_table(frame),
                      frontier=analysis.frontier_table(frame, "delta"),
                      pooled=analysis.rule_frontier_table(frame, "delta"),
                      instances=analysis.instance_summary(frame),
                      stations=analysis.station_table(campaign))
        for name, table in tables.items():
            self.assertTrue(table, name)
            self.assertEqual({r["rule"] for r in table}, {"two_sided"}, name)
        self.assertEqual({r["below_floor"] for r in tables["stations"]}, {True})
        self.assertEqual({r["floor"] for r in tables["stations"]}, {0.48})

    def test_rows_without_a_rule_key_are_upper_only_and_floor_fields_stay_absent(self):
        rows = [_row(arm="NOM")]
        self.assertNotIn("rule", rows[0])
        self.build(rows, [self._scored([self._station()])])
        campaign = analysis.load_campaign(self.directory)
        frame = analysis.case_frame(campaign)
        self.assertEqual(frame[0]["rule"], "upper_only")
        self.assertIsNone(frame[0]["floor_violation_count"])
        self.assertEqual(analysis.status_table(frame)[0]["rule"], "upper_only")
        self.assertEqual(analysis.resource_table(frame)[0]["rule"], "upper_only")
        station = analysis.station_table(campaign)[0]
        self.assertEqual(station["rule"], "upper_only")
        self.assertIsNone(station["floor"])
        self.assertIsNone(station["below_floor"])

    def test_status_table_never_pools_two_campaigns_or_two_rules(self):
        rows = [_row(arm="NOM")]
        self.build(rows, [self._scored()])
        other = self.directory.parent / "two"
        self.build([_row(arm="NOM", rule="two_sided", delta="0.01")], [self._scored(floors=0)],
                   directory=other)
        frame = analysis.case_frame(analysis.load_campaign(self.directory))
        frame += analysis.case_frame(analysis.load_campaign(other))
        table = analysis.status_table(frame)
        self.assertEqual(len(table), 2)
        self.assertEqual({(r["campaign"], r["rule"], r["authorized_rows"]) for r in table},
                         {("camp", "upper_only", 1), ("two", "two_sided", 1)})


class RuleFrontierPoolingTests(CampaignFixture):
    """The pooled frontier merges campaigns only inside one (rule, implementation hash).

    Revision 2 ran each two-sided delta as its own campaign, so the predeclared
    side-by-side delta table must draw on several campaigns. It may do so only
    when they share rule and implementation version, and it must name what it
    merged; anything else stays on its own row.
    """

    def _campaign(self, name, *, rule, impl, delta):
        overrides = dict(arm="HIST", delta=delta)
        if rule != "upper_only":
            overrides["rule"] = rule
        rows = [_row(**overrides)]
        record = dict(status="COMPLETE",
                      solve_result=dict(assignment=[0, 0, 1, 1], objective=1.0, native_status="F",
                                        status="FEASIBLE", bound=None, gap=None,
                                        bound_provenance="unavailable", build_seconds=1.0,
                                        solve_seconds=1.0),
                      validation=dict(valid=True, model_feasible=True, actual_visit_count=1),
                      evaluation=_evaluation(joint_pass=True, worst_pp=0.0, mean_visits=3.0),
                      reference_evaluation=None, accepted_training_solution=True)
        directory = self.directory.parent / name
        self.build(rows, [record], runtime=dict(implementation_hash=impl), directory=directory)
        return analysis.case_frame(analysis.load_campaign(directory))

    def test_pooling_requires_same_rule_and_same_implementation(self):
        frame = []
        frame += self._campaign("a", rule="two_sided", impl="impl-two", delta="0.02")
        frame += self._campaign("b", rule="two_sided", impl="impl-two", delta="0.02")   # pools with a
        frame += self._campaign("c", rule="two_sided", impl="impl-two", delta="0.01")   # side by side
        frame += self._campaign("d", rule="two_sided", impl="impl-old", delta="0.02")   # other version
        frame += self._campaign("e", rule="upper_only", impl="impl-two", delta="0.02")  # other rule
        pooled = analysis.rule_frontier_table(frame, "delta")
        by = {(r["rule"], r["implementation_hash"], r["value"]): r for r in pooled}
        self.assertEqual(len(pooled), 4)
        merged = by[("two_sided", "impl-two", "0.02")]
        self.assertEqual((merged["cells"], merged["campaigns"], merged["campaign_count"]), (2, "a+b", 2))
        self.assertEqual(by[("two_sided", "impl-two", "0.01")]["cells"], 1)
        self.assertEqual(by[("two_sided", "impl-old", "0.02")]["campaigns"], "d")
        self.assertEqual(by[("upper_only", "impl-two", "0.02")]["campaigns"], "e")
        per_campaign = analysis.frontier_table(frame, "delta")
        self.assertEqual(len(per_campaign), 5, "the per-campaign frontier never pools")
        self.assertEqual({r["rule"] for r in per_campaign}, {"two_sided", "upper_only"})

    def test_pooled_rows_are_ordered_by_rule_then_numeric_value(self):
        frame = []
        frame += self._campaign("p", rule="two_sided", impl="impl", delta="0.03")
        frame += self._campaign("q", rule="two_sided", impl="impl", delta="0.005")
        frame += self._campaign("r", rule="two_sided", impl="impl", delta="0.02")
        values = [r["value"] for r in analysis.rule_frontier_table(frame, "delta")]
        self.assertEqual(values, ["0.005", "0.02", "0.03"])


class CrossHorizonIdentityTests(unittest.TestCase):
    def test_table_carries_campaign_and_relative_horizons(self):
        record = dict(campaign="screen_x", source_case_id="c", dataset_id="syn_500sku_seed1001",
                      catalogue_size=500, origin=100, arm="HIST", seed=11,
                      trained_n=500, scored_n=1000, evaluation=dict(
                          evaluation_kind="secondary_cross_horizon", layout_hash="l", future_hash="f",
                          joint_pass=True, violation_count=0, worst_excess_percentage_points=0.0,
                          positive_excess_sum=0.0, mean_visits=3.0, visit_count=3000,
                          activation_mass=0.0, station_novelty_count=0, active_product_fraction=1.0))
        row = analysis.cross_horizon_table([record])[0]
        self.assertEqual(row["campaign"], "screen_x")
        self.assertEqual((row["trained_multiple"], row["scored_multiple"]), ("1", "2"))


if __name__ == "__main__":
    unittest.main()
