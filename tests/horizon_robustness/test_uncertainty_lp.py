"""Driver-written independent LP for the historical/activation uncertainty set."""

from dataclasses import replace
from fractions import Fraction
import itertools
import unittest

from scipy.optimize import linprog

from Baselines.horizon_robustness.schema import CatalogueManifest, Order
from Baselines.horizon_robustness.uncertainty import build_training_problem, worst_shares


class UncertaintyLPTest(unittest.TestCase):
    def test_finite_counterpart_matches_independent_mixture_weight_lp(self):
        catalogue = CatalogueManifest("lp-unit", "fixture", tuple("abcd"), ("s0", "s1"),
                                      (2, 2), known_reference=(0, 1, 0, 1))
        history = tuple(Order(str(i + 1), i + 1, line) for i, line in enumerate(
            (((0, 2),), ((1, 1),), ((0, 1),), ((1, 2),), ((0, 1), (1, 1)), ((1, 2),))))
        for complete in (False, True):
            prefix = history if not complete else tuple(replace(o, lines=o.lines + ((2, 1), (3, 2))) for o in history)
            for nu in ("0", "0.01", "0.25", "1"):
                problem = build_training_problem(catalogue, prefix, 2, nu=nu)
                vertices = [dict(v.counts) for v in problem.scenarios]
                zeros = problem.reference.inactive
                # Separate mass weights: q = sum_k lambda_k q_k + sum_z mu_z e_z;
                # sum(lambda)+sum(mu)=1, sum(mu)<=nu, lambda,mu>=0. This LP
                # never uses h_s or the closed-form endpoint expressions.
                dimension = len(vertices) + len(zeros)
                activation_row = [0] * len(vertices) + [1] * len(zeros)
                for assignment in itertools.product(range(2), repeat=4):
                    if assignment.count(0) != 2:
                        continue
                    actual = worst_shares(problem, assignment)
                    for station in range(2):
                        coefficients = [float(sum(Fraction(count, scenario.total_lines)
                                                  for p, count in scenario.counts if assignment[p] == station))
                                        for scenario in problem.scenarios]
                        coefficients.extend(float(assignment[p] == station) for p in zeros)
                        result = linprog([-v for v in coefficients], A_ub=[activation_row],
                                         b_ub=[float(nu) if zeros else 0], A_eq=[[1] * dimension], b_eq=[1],
                                         bounds=(0, None), method="highs")
                        with self.subTest(complete=complete, nu=nu, assignment=assignment, station=station):
                            self.assertTrue(result.success, result.message)
                            self.assertAlmostEqual(actual[station], -result.fun, places=12)
                            self.assertAlmostEqual(sum(result.x), 1, places=12)


if __name__ == "__main__":
    unittest.main()
