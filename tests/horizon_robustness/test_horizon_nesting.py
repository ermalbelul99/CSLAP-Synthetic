"""Independent arithmetic check of nested right-aligned uncertainty evidence."""

from fractions import Fraction
import unittest

from Baselines.horizon_robustness.schema import Order
from Baselines.horizon_robustness.uncertainty import make_scenarios


class HorizonNestingTest(unittest.TestCase):
    def test_coarse_vertices_are_line_weighted_combinations_of_fine_vertices(self):
        for length in (36, 37, 47, 48, 49):
            history = tuple(Order(str(i), i, tuple(sorted(((i % 6, i % 7 + 1),
                                                         ((i + 1) % 6, i % 3 + 1)))))
                            for i in range(1, length + 1))
            for small, large in ((3, 6), (6, 12), (3, 12)):
                fine = make_scenarios(history, 6, small)
                coarse = make_scenarios(history, 6, large)
                lookup = {v.start: v for v in fine[:-1]}
                self.assertEqual(fine[-1], coarse[-1])
                for vertex in coarse[:-1]:
                    members = [lookup[start] for start in range(vertex.start, vertex.stop, small)]
                    total = sum(v.total_lines for v in members)
                    self.assertEqual(total, vertex.total_lines)
                    weights = [Fraction(v.total_lines, total) for v in members]
                    self.assertEqual(sum(weights), 1)
                    for product in range(6):
                        mixture = sum(weight * Fraction(dict(member.counts).get(product, 0), member.total_lines)
                                      for weight, member in zip(weights, members))
                        self.assertEqual(mixture, Fraction(dict(vertex.counts).get(product, 0), total))

    def test_non_multiple_horizons_need_not_have_nested_hulls(self):
        history = tuple(Order(str(i + 1), i + 1, ((i, 1),)) for i in range(12))
        fine = make_scenarios(history, 12, 2)
        coarse = make_scenarios(history, 12, 3)
        # Every fine vertex, including pooled history, has q_2 == q_3.
        # All convex combinations inherit that linear equality.
        for vertex in fine:
            self.assertEqual(dict(vertex.counts).get(2, 0), dict(vertex.counts).get(3, 0))
        # The first 3-order block violates it, hence lies outside the fine hull.
        self.assertNotEqual(dict(coarse[0].counts).get(2, 0), dict(coarse[0].counts).get(3, 0))


if __name__ == "__main__":
    unittest.main()
