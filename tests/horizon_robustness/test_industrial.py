"""Shared-loader integration on small in-memory fixtures, no empirical solves."""

from collections import Counter
from contextlib import redirect_stdout
from copy import deepcopy
from dataclasses import replace
import io
import unittest
from unittest.mock import patch

import pandas as pd

import data_loader_industrial
from Baselines.horizon_robustness.industrial import (
    FIXED_POLICY, SNAPSHOT_POLICY, audit_article_payload, catalogue_from_article, demand_from_article,
)
from Baselines.horizon_robustness.orders import line_counts, load_industrial
from Baselines.horizon_robustness.protocol import ContractError, INDUSTRIAL_SOURCE
from Baselines.horizon_robustness.reference import build_reference, slot_assignment
from Baselines.horizon_robustness.schema import Order, SourceFile


def fixture_rows():
    rows = []
    for order in range(1, 7):
        for product in "abcdefk":
            station = "01.01" if product in "abc" else "01.GE4" if product in "def" else "01.30"
            rows.append(dict(PRODUCT=product, ORDER=order, STATION=station))
        if order <= 5:
            rows.append(dict(PRODUCT="j", ORDER=order, STATION="01.30"))
    rows.extend([
        dict(PRODUCT="d", ORDER=1, STATION="01.E4"),  # Same pair after reconciliation.
        dict(PRODUCT="g", ORDER=1, STATION="01.30"),
        dict(PRODUCT="h", ORDER=99, STATION="01.31"),  # Fixed-only station absent from large orders.
        dict(PRODUCT="i", ORDER=100, STATION="01.30"),
        dict(PRODUCT="x", ORDER=1, STATION="01.Z2"),
        dict(PRODUCT="x", ORDER=101, STATION="01.15"),  # Exclude both x observations after reconciliation.
        dict(PRODUCT="y", ORDER=102, STATION="01.GED"),
        dict(PRODUCT="z", ORDER=103, STATION="01.Z8"),
        dict(PRODUCT=None, ORDER=104, STATION="01.01"),
    ])
    rows.append(dict(rows[0]))  # Original triple duplicate removed by shared loader.
    return rows


class IndustrialTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch.object(data_loader_industrial.pd, "read_csv", return_value=pd.DataFrame(fixture_rows())):
            with redirect_stdout(io.StringIO()):
                cls.payload = data_loader_industrial.load_industrial_data("in_memory_fixture")
        cls.source = SourceFile(INDUSTRIAL_SOURCE, "0" * 64, 0)
        cls.catalogue = catalogue_from_article(cls.payload, cls.source)
        cls.data = demand_from_article(cls.payload, cls.catalogue)

    def test_exact_shared_partition_and_full_capacity(self):
        catalogue = self.catalogue
        self.assertEqual(catalogue.product_ids, tuple("abcdefghijk"))
        self.assertEqual(catalogue.station_ids, ("01.01", "01.30", "01.31", "01.E4"))
        self.assertEqual(catalogue.capacities, (3, 4, 1, 3))
        fixed = {catalogue.product_ids[p]: catalogue.station_ids[s] for p, s in catalogue.exogenous_fixed}
        self.assertEqual(fixed, self.payload["static_assignment"])
        self.assertEqual(set(fixed), set("ghij"))
        self.assertEqual(set(self.payload["pr_solver"]), set("abcdefk"))
        catalogue.check_storage(catalogue.known_reference, catalogue.exogenous_fixed)
        self.assertEqual(dict(catalogue.audit)["fixed_policy"], FIXED_POLICY)
        self.assertEqual(dict(catalogue.audit)["snapshot_policy"], SNAPSHOT_POLICY)

    def test_global_reconciliation_precedes_exclusions_and_alias(self):
        catalogue = self.catalogue
        self.assertTrue(set("xyz").isdisjoint(catalogue.product_ids))
        self.assertTrue({"01.Z2", "01.Z8", "01.15", "01.GED", "01.GE4"}.isdisjoint(catalogue.station_ids))
        self.assertEqual(tuple(o.order_id for o in self.data.orders), ("1", "2", "3", "4", "5", "6", "99", "100"))

    def test_small_orders_and_fixed_only_station_survive(self):
        self.assertNotIn("01.31", {s["STATION_ID"] for s in self.payload["st_full"]})
        self.assertIn("01.31", self.catalogue.station_ids)
        self.assertEqual(dict(self.catalogue.audit)["included_fixed_only_stations_missing_from_legacy_st_full"], '["01.31"]')
        self.assertEqual(len(self.data.orders[-2].support), 1)
        self.assertEqual(self.data.orders[-2].support, (self.catalogue.product_ids.index("h"),))

    def test_pair_counts_match_pl_full_not_reconciled_duplicate_lists(self):
        measured = dict(zip(self.catalogue.product_ids, line_counts(self.data.orders, self.catalogue.p)))
        self.assertEqual(measured, self.payload["pl_full"])
        self.assertEqual(measured["d"], 6)
        raw_lists = sum(map(len, self.payload["op_full"].values()))
        self.assertEqual(raw_lists - sum(measured.values()), 1)
        self.assertEqual(dict(self.data.audit)["duplicate_product_order_rows_removed"], "1")
        audit = audit_article_payload(self.payload, self.catalogue)
        self.assertEqual(audit["duplicate_entries_in_large_orders"], 1)
        self.assertEqual(audit["products_whose_freeze_classification_differs_under_distinct_order_rule"], 0)
        self.assertTrue(audit["shared_order_keys_match_numeric_chronology"])

    def test_freeze_mask_not_reestimated_from_prefix(self):
        first = build_reference(self.catalogue, self.data.orders[:1])
        later = build_reference(self.catalogue, self.data.orders[:6])
        self.assertEqual(first.fixed, self.catalogue.exogenous_fixed)
        self.assertEqual(later.fixed, first.fixed)
        # These items have <=5 historical large orders but were not frozen in
        # the assumed article snapshot. Do not silently shrink its decision pool.
        self.assertTrue(set("defk").isdisjoint(self.catalogue.product_ids[p] for p, s in first.fixed))
        self.assertIn("not_prospective_evidence", first.provenance)

    def test_known_zero_history_products_still_get_reserved_slots_and_future_work(self):
        reference = build_reference(self.catalogue, self.data.orders[:6])
        h, i = (self.catalogue.product_ids.index(p) for p in "hi")
        self.assertEqual(reference.inactive, (h, i))
        self.assertEqual(len(reference.assignment), self.catalogue.p)
        self.assertEqual(len(set(slot_assignment(self.catalogue, reference.assignment, reference))), self.catalogue.p)
        counts = line_counts(self.data.orders[6:], self.catalogue.p)
        loads = Counter()
        for p, value in enumerate(counts):
            loads[reference.assignment[p]] += value
        self.assertEqual(sum(loads.values()), 2)
        self.assertEqual(loads[self.catalogue.station_ids.index("01.31")], 1)
        self.assertEqual(loads[self.catalogue.station_ids.index("01.30")], 1)
        # Excluded stations contribute neither work nor phantom shares.
        self.assertEqual(sum(loads[s] / 2 for s in range(self.catalogue.s)), 1)

    def test_future_mutation_holds_snapshot_not_reconstruction_fixed(self):
        history = self.data.orders[:6]
        original = history + (Order("999", 999, ((0, 1),)),)
        changed = history + (Order("999", 999, ((10, 500),), ((10, 0),)),)
        self.assertEqual(build_reference(self.catalogue, original[:6]), build_reference(self.catalogue, changed[:6]))
        self.assertNotEqual(original[-1], changed[-1])

    def test_snapshot_and_stream_corruption_fail(self):
        for corrupt in ("missing_fixed", "overlap", "excluded_station", "wrong_capacity", "bad_pool", "wrong_frequency", "unknown_product"):
            payload = deepcopy(self.payload)
            if corrupt == "missing_fixed":
                del payload["static_assignment"]["h"]
            elif corrupt == "overlap":
                payload["static_assignment"]["a"] = "01.01"
            elif corrupt == "excluded_station":
                payload["static_assignment"]["h"] = "01.GED"
            elif corrupt == "wrong_capacity":
                payload["st_full"][0]["CAPACITY"] += 1
            elif corrupt == "bad_pool":
                payload["pr_solver"].pop()
            elif corrupt == "wrong_frequency":
                payload["pl_full"]["d"] += 1
            else:
                payload["op_full"][1].append("unknown")
            with self.subTest(corrupt=corrupt), self.assertRaises(ContractError):
                catalogue = catalogue_from_article(payload, self.source)
                demand_from_article(payload, catalogue)

    def test_default_entry_uses_shared_payload_and_rejects_conflicting_override(self):
        with patch("Baselines.horizon_robustness.industrial.read_article_payload", return_value=(self.payload, self.source, "fixture")) as reader:
            self.assertEqual(load_industrial(), self.data)
            reader.assert_called_once()
            with self.assertRaisesRegex(ContractError, "override conflicts"):
                load_industrial(geometry={"wrong": 11})

    def test_full_pipeline_scores_new_demand_on_frozen_products(self):
        from Baselines.horizon_robustness.metrics import evaluate_layout
        from Baselines.horizon_robustness.uncertainty import build_training_problem

        problem = build_training_problem(self.catalogue, self.data.orders[:6], 2)
        result = evaluate_layout(problem, problem.reference.assignment, self.data.orders[6:])
        self.assertEqual(result["total_lines"], 2)
        self.assertEqual(sum(result["fixed_station_line_counts"]), 2)
        self.assertEqual(result["visit_count"], 2)
        self.assertFalse(result["joint_pass"])
        s = self.catalogue.station_ids.index("01.31")
        self.assertEqual(result["stations"][s]["target_exact"], "0")
        self.assertEqual(result["stations"][s]["share_exact"], "1/2")
        self.assertEqual(result["stations"][s]["cap_exact"], "1/100")

    def test_duplicate_threshold_crossing_preserves_article_mask(self):
        rows = fixture_rows() + [dict(PRODUCT="j", ORDER=1, STATION="01.01")]
        with patch.object(data_loader_industrial.pd, "read_csv", return_value=pd.DataFrame(rows)):
            with redirect_stdout(io.StringIO()):
                payload = data_loader_industrial.load_industrial_data("threshold_fixture")
        catalogue = catalogue_from_article(payload, self.source)
        self.assertNotIn("j", payload["static_assignment"])
        self.assertIn("j", payload["warm_start_assignment"])
        self.assertEqual(payload["pl_full"]["j"], 5)
        audit = audit_article_payload(payload, catalogue)
        self.assertEqual(audit["products_whose_freeze_classification_differs_under_distinct_order_rule"], 1)

    def test_shared_reconciliation_repairs_early_whitespace_station_row(self):
        from Baselines.horizon_robustness.catalogue import retained_industrial_rows

        blank = dict(PRODUCT="d", ORDER=0, STATION=" ")
        self.assertEqual(list(retained_industrial_rows([blank])), [])
        with patch.object(data_loader_industrial.pd, "read_csv", return_value=pd.DataFrame(fixture_rows() + [blank])):
            with redirect_stdout(io.StringIO()):
                payload = data_loader_industrial.load_industrial_data("whitespace_fixture")
        catalogue = catalogue_from_article(payload, self.source)
        data = demand_from_article(payload, catalogue)
        self.assertEqual(data.orders[0].order_id, "0")
        self.assertEqual(data.orders[0].lines, ((catalogue.product_ids.index("d"), 1),))
        self.assertEqual(payload["pl_full"]["d"], 7)
        self.assertNotIn(" ", catalogue.station_ids)


if __name__ == "__main__":
    unittest.main()
