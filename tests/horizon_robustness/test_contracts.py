import dataclasses
import json
from pathlib import Path
import unittest

from Baselines.horizon_robustness.protocol import (
    ContractError, Protocol, allowed_source, digest, eligible, horizon_grid,
    origins, time_cap,
)
from Baselines.horizon_robustness.schema import (
    CatalogueManifest, Order, OrderedDemand, ReferenceState, Scenario, SolveResult,
    SolveStatus, SourceFile, TrainingProblem,
)


class ContractsTest(unittest.TestCase):
    def setUp(self):
        self.catalogue = CatalogueManifest("unit", "fixture", ("a", "b", "c", "d"), ("s0", "s1"), (2, 2))
        self.reference = ReferenceState((0, 1, 0, 1), (), (6, 6, 0, 0), (6, 6), 6, digest("history"), "fixture")
        self.history = Scenario(((0, 6), (1, 6)), 12, 0, 6, "history")
        self.problem = TrainingProblem(self.catalogue, self.reference, 2, (self.history,), (((0, 1), 6),))

    def test_allowlist_accepts_only_original_instance_files(self):
        self.assertEqual(allowed_source("exp02a_instances/syn_50sku_seed1001/syn_50sku_orders.csv"),
                         "exp02a_instances/syn_50sku_seed1001/syn_50sku_orders.csv")
        for path in ("data/instances/iscf/a.csv", "Heuristic_Connex_Set_Project/data/BERNER_DATED.csv",
                     "exp02a_instances/syn_50sku_seed9999/syn_50sku_orders.csv",
                     "exp02a_instances/syn_50sku_seed1001/syn_500sku_orders.csv", "../secrets.csv"):
            with self.subTest(path=path), self.assertRaises(ContractError):
                allowed_source(path)

    def test_full_occupancy_and_zero_products_survive_roundtrip(self):
        restored = TrainingProblem.from_dict(json.loads(json.dumps(self.problem.to_dict())))
        self.assertEqual(restored, self.problem)
        self.assertEqual(restored.reference.inactive, (2, 3))
        self.assertEqual(restored.catalogue.p, 4)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            restored.n = 3
        with self.assertRaises(TypeError):
            restored.reference.assignment[0] = 1

    def test_capacity_bad_ids_and_mutable_structures_fail(self):
        for changes in ({"capacities": (1, 2)}, {"product_ids": ("a", "a", "c", "d")},
                        {"capacities": [2, 2]}, {"allowed_stations": ((0,), (), (0,), (1,))}):
            with self.subTest(changes=changes), self.assertRaises(ContractError):
                dataclasses.replace(self.catalogue, **changes)
        with self.assertRaises(ContractError):
            self.catalogue.check_storage((0, 0, 0, 1))
        with self.assertRaises(ContractError):
            self.catalogue.check_storage((0, 0, 1, 1), ((9, 0),))
        with self.assertRaises(ContractError):
            dataclasses.replace(self.catalogue, exogenous_fixed=((0, 0), (1, 0), (2, 0)))

    def test_order_data_rejects_unknown_products_and_key_collisions(self):
        with self.assertRaisesRegex(ContractError, "OUT_OF_CATALOGUE"):
            OrderedDemand(self.catalogue, (Order("ORD_1", 1, ((4, 1),)),))
        with self.assertRaises(ContractError):
            OrderedDemand(self.catalogue, (Order("ORD_1", 1, ((0, 1),)), Order("001", 1, ((1, 1),))))
        with self.assertRaises(ContractError):
            Order("ORD_1", 1, ((0, 1), (0, 2)))

    def test_decimal_policy_exact_and_separate(self):
        nominal = dataclasses.replace(self.problem, arm="NOM")
        tight = dataclasses.replace(self.problem, arm="TIGHT")
        self.assertEqual(nominal.scoring_caps, (0.51, 0.51))
        self.assertEqual(tight.optimization_caps, (0.505, 0.505))
        self.assertEqual(tight.scoring_caps, nominal.scoring_caps)
        self.assertEqual(dataclasses.replace(nominal, n=5).model_hash, nominal.model_hash)
        self.assertNotEqual(dataclasses.replace(self.problem, nu="0.02").model_hash, self.problem.model_hash)
        self.assertEqual(dataclasses.replace(self.problem, arm="HIST").model_hash,
                         dataclasses.replace(self.problem, nu="0").model_hash)

    def test_missing_supports_future_scenarios_and_bad_shares_fail(self):
        with self.assertRaises(ContractError):
            dataclasses.replace(self.problem, weighted_supports=(((0, 1), 5),))
        with self.assertRaises(ContractError):
            dataclasses.replace(self.problem, weighted_supports=([(0, 1), 6],))
        with self.assertRaises(ContractError):
            dataclasses.replace(self.problem, scenarios=(Scenario(((0, 1),), 1, 6, 8),))
        for value in ("NaN", "Infinity", "-0.1", "1.1"):
            with self.subTest(value=value), self.assertRaises(ContractError):
                dataclasses.replace(self.problem, delta=value)

    def test_cache_preserves_exact_activation_decimal(self):
        near = dataclasses.replace(self.problem, nu="0.0100000000000000001")
        base = dataclasses.replace(self.problem, nu="0.01")
        self.assertEqual(near.effective_nu, base.effective_nu)
        self.assertNotEqual(near.model_hash, base.model_hash)

    def test_protocol_grids_resources_and_eligibility(self):
        configured = Protocol.from_dict(json.loads(Path("configs/horizon_robustness/protocol.json").read_text()))
        self.assertEqual(configured, Protocol())
        self.assertEqual(horizon_grid(50), (25, 50, 100))
        self.assertEqual(horizon_grid(21874), (10937, 21874, 43748))
        self.assertEqual(origins(2000, 50), (1400, 1500))
        self.assertEqual(eligible(10, 4, 30), "INSUFFICIENT_HISTORY")
        self.assertEqual(eligible(12, 4, 15), "INSUFFICIENT_FUTURE")
        self.assertIsNone(eligible(12, 4, 16))
        self.assertEqual(time_cap(2000), 1200)
        self.assertEqual(configured.fingerprint, Protocol.from_dict(configured.to_dict()).fingerprint)

    def test_status_bound_roundtrip_never_invents_certificate(self):
        result = SolveResult("cplex", "test", SolveStatus.NO_INCUMBENT_LIMIT, "time limit",
                             self.problem.input_hash, self.problem.model_hash, 11, 1, 1)
        self.assertIsNone(result.bound)
        self.assertEqual(SolveResult.from_dict(json.loads(json.dumps(result.to_dict()))), result)
        with self.assertRaises(ContractError):
            dataclasses.replace(result, bound=float("inf"))

    def test_source_manifest_and_fixed_integrity(self):
        with self.assertRaises(ContractError):
            dataclasses.replace(self.catalogue, kind="industrial")
        with self.assertRaises(ContractError):
            SourceFile("data/instances/iscf/fixture.csv", "0" * 64, 1)
        with self.assertRaises(ContractError):
            dataclasses.replace(self.problem, reference=dataclasses.replace(self.reference, station_line_counts=(7, 5)))


if __name__ == "__main__":
    unittest.main()
