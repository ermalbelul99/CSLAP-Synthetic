from collections import Counter
import dataclasses
import unittest

from Baselines.horizon_robustness.catalogue import (
    industrial_catalogue_from_roster, industrial_roster, retained_industrial_rows,
    synthetic_product_id,
)
from Baselines.horizon_robustness.orders import (
    aggregate_orders, chronology_key, complete_window, line_counts, weighted_supports,
)
from Baselines.horizon_robustness.protocol import ContractError, INDUSTRIAL_SOURCE
from Baselines.horizon_robustness.schema import CatalogueManifest, SourceFile


class DataTest(unittest.TestCase):
    def setUp(self):
        self.catalogue = CatalogueManifest("unit", "fixture", ("1", "2", "3", "4"), ("1", "2"), (2, 2))

    def test_numeric_sequence_groups_whole_orders_and_keeps_zeros(self):
        rows = [dict(ORDER=o, PRODUCT=p) for o, p in (("ORD_10", "PROD_1"), ("ORD_2", "PROD_2"),
                ("ORD_1", "PROD_1"), ("ORD_2", "PROD_1"))]
        data = aggregate_orders(rows, self.catalogue)
        self.assertEqual(tuple(o.order_id for o in data.orders), ("ORD_1", "ORD_2", "ORD_10"))
        self.assertEqual(line_counts(complete_window(data.orders, 0, 2), 4), (2, 1, 0, 0))
        self.assertEqual(data.orders[1].support, (0, 1))
        self.assertEqual(data.catalogue.product_ids, ("1", "2", "3", "4"))

    def test_synthetic_lines_not_quantities_or_station_labels(self):
        rows = [dict(ORDER="ORD_1", PRODUCT="PROD_1", QTY="999", STATION="random"),
                dict(ORDER="ORD_1", PRODUCT="PROD_1", QTY="1", STATION="different")]
        data = aggregate_orders(rows, self.catalogue)
        self.assertEqual(data.orders[0].lines, ((0, 2),))
        self.assertEqual(weighted_supports(data.orders), (((0,), 1),))
        self.assertEqual(data.orders[0].observations, ())

    def test_bad_numeric_keys_and_unknown_sku_fail(self):
        for order in ("1.2", "ORD_A", "", "2026-01-02"):
            with self.subTest(order=order), self.assertRaises(ContractError):
                chronology_key(order)
        with self.assertRaises(ContractError):
            aggregate_orders([dict(ORDER="ORD_1", PRODUCT="PROD_1"), dict(ORDER="001", PRODUCT="PROD_2")], self.catalogue)
        with self.assertRaisesRegex(ContractError, "OUT_OF_CATALOGUE"):
            aggregate_orders([dict(ORDER="ORD_1", PRODUCT="PROD_5")], self.catalogue)

    def test_berner_alias_filter_and_dedup(self):
        rows = [dict(ORDER="10", PRODUCT="a", STATION="01.GE4"),
                dict(ORDER="10", PRODUCT="a", STATION="01.E4"),
                dict(ORDER="10", PRODUCT="a", STATION="01.01"),
                dict(ORDER="2", PRODUCT="b", STATION="01.01"),
                dict(ORDER="1", PRODUCT="x", STATION="01.Z8"),
                dict(ORDER="3", PRODUCT="", STATION="01.01")]
        catalogue = CatalogueManifest("unit", "fixture", ("a", "b", "c", "d"), ("01.01", "01.E4"), (2, 2))
        audit = Counter()
        data = aggregate_orders(retained_industrial_rows(rows, audit), catalogue, industrial=True)
        self.assertEqual(tuple(o.order_id for o in data.orders), ("2", "10"))
        self.assertEqual(line_counts(data.orders, 4), (1, 1, 0, 0))
        self.assertEqual(data.orders[1].observations, ((0, 0), (0, 1)))
        self.assertEqual(audit["excluded_station_rows"], 1)
        self.assertEqual(audit["null_rows_removed"], 1)

    def test_ambiguous_geometry_not_silently_inferred(self):
        rows = [dict(ORDER="1", PRODUCT="a", STATION="s0"),
                dict(ORDER="9", PRODUCT="a", STATION="s1"),
                dict(ORDER="2", PRODUCT="b", STATION="s1")]
        products, stations, memberships, audit = industrial_roster(rows)
        source = SourceFile(INDUSTRIAL_SOURCE, "0" * 64, 0)
        with self.assertRaisesRegex(ContractError, "MISSING_GEOMETRY"):
            industrial_catalogue_from_roster(products, stations, memberships, source)
        catalogue = industrial_catalogue_from_roster(products, stations, memberships, source, {"s0": 1, "s1": 1})
        self.assertEqual(catalogue.known_reference, ())
        self.assertEqual(catalogue.geometry_provenance, "assumed_exogenous")
        self.assertEqual(audit["products_with_ambiguous_station"], 1)

    def test_unambiguous_geometry_is_explicit_assumption_not_future_reference(self):
        rows = [dict(ORDER="100", PRODUCT="a", STATION="s0"), dict(ORDER="200", PRODUCT="b", STATION="s1")]
        products, stations, memberships, audit = industrial_roster(rows)
        catalogue = industrial_catalogue_from_roster(products, stations, memberships, SourceFile(INDUSTRIAL_SOURCE, "0" * 64, 0))
        self.assertEqual(catalogue.capacities, (1, 1))
        self.assertEqual(catalogue.known_reference, ())
        self.assertEqual(catalogue.roster_provenance, "assumed_exogenous")


if __name__ == "__main__":
    unittest.main()
