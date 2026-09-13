import dataclasses
import itertools
import unittest

from Baselines.horizon_robustness.orders import aggregate_orders, complete_window
from Baselines.horizon_robustness.protocol import INDUSTRIAL_SOURCE
from Baselines.horizon_robustness.reference import (
    build_reference, historical_preferences, minimum_preference_assignment, slot_assignment,
)
from Baselines.horizon_robustness.schema import CatalogueManifest, Order, SourceFile


class ReferenceTest(unittest.TestCase):
    def setUp(self):
        self.catalogue = CatalogueManifest("unit", "fixture", ("1", "2", "3", "4"), ("s0", "s1"), (2, 2))
        self.history = (Order("1", 1, ((0, 8), (1, 1))), Order("2", 2, ((1, 1),)))

    def test_lpt_assigns_zeros_fills_slots_and_uses_pooled_shares(self):
        reference = build_reference(self.catalogue, self.history)
        self.catalogue.check_storage(reference.assignment)
        self.assertEqual(reference.assignment, (0, 1, 1, 0))
        self.assertEqual(reference.historical_counts, (8, 2, 0, 0))
        self.assertEqual(reference.b, (0.8, 0.2))
        self.assertNotAlmostEqual(reference.b[0], (8 / 9 + 0) / 2)
        self.assertEqual(len(set(slot_assignment(self.catalogue, reference.assignment))), 4)

    def test_future_mutation_cannot_change_historical_reference(self):
        future_a = self.history + (Order("3", 3, ((2, 100),), ((2, 0),)),)
        future_b = self.history + (Order("3", 3, ((3, 1000),), ((3, 1),)),)
        self.assertEqual(build_reference(self.catalogue, complete_window(future_a, 0, 2)),
                         build_reference(self.catalogue, complete_window(future_b, 0, 2)))

    def test_minimum_reassignment_lexicographic_matches_enumeration(self):
        possibilities = [a for a in itertools.product(range(2), repeat=4) if a.count(0) == 2]
        for raw in itertools.product((None, 0, 1), repeat=4):
            preferences = {p: s for p, s in enumerate(raw) if s is not None}
            expected = min(possibilities, key=lambda a: (sum(a[p] != s for p, s in preferences.items()), a))
            self.assertEqual(minimum_preference_assignment(self.catalogue, preferences), expected)

    def test_minimum_reassignment_respects_genuine_fixed_items(self):
        catalogue = dataclasses.replace(self.catalogue, exogenous_fixed=((0, 1),))
        result = minimum_preference_assignment(catalogue, {0: 0, 1: 0, 2: 0, 3: 0})
        self.assertEqual(result, (1, 0, 0, 1))
        catalogue.check_storage(result, catalogue.exogenous_fixed)

    def test_last_historical_preference_not_last_future_station(self):
        history = (Order("1", 1, ((0, 1),), ((0, 1),)), Order("2", 2, ((0, 1),), ((0, 0), (0, 1))))
        self.assertEqual(historical_preferences(history), {0: 0})

    def test_industrial_freezing_includes_zeros_but_keeps_full_catalogue(self):
        catalogue = CatalogueManifest("berner", "industrial", tuple(str(p) for p in range(8)),
                                      ("01.E4", "01.01"), (4, 4),
                                      (SourceFile(INDUSTRIAL_SOURCE, "0" * 64, 0),),
                                      known_reference=(0, 0, 0, 0, 1, 1, 1, 1),
                                      geometry_provenance="assumed_exogenous", roster_provenance="assumed_exogenous")
        history = (Order("1", 1, tuple((p, 1) for p in range(6))),)
        reference = build_reference(catalogue, history)
        self.assertEqual(reference.fixed, ((0, 0), (1, 0), (2, 0), (3, 0), (6, 1), (7, 1)))
        self.assertEqual(len(reference.assignment), 8)
        self.assertEqual(reference.inactive, (6, 7))

    def test_fixed_products_reserve_their_individual_slot_labels(self):
        catalogue = dataclasses.replace(self.catalogue, exogenous_fixed=((1, 0),), known_reference=(0, 0, 1, 1))
        reference = build_reference(catalogue, self.history)
        old_slots = slot_assignment(catalogue, reference.assignment)
        changed = slot_assignment(catalogue, (1, 0, 0, 1), reference)
        self.assertEqual(changed[1], old_slots[1])
        self.assertEqual(len(set(changed)), 4)


if __name__ == "__main__":
    unittest.main()
