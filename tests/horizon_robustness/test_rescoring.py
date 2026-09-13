"""Cross-horizon rescoring controls. No optimizer and no campaign are launched.

Stage F re-scores layouts that are ALREADY frozen. These controls state what it
must produce, and what it must refuse.
"""

from pathlib import Path
import tempfile
import unittest

from Baselines.horizon_robustness import runner
from Baselines.horizon_robustness.protocol import ContractError, canonical_json, digest
from Baselines.horizon_robustness.schema import CatalogueManifest, Order, OrderedDemand
from Baselines.horizon_robustness_analysis import analysis, rescoring

DATASET = "syn_50sku_seed1001"
META = dict(backend="hexaly", interpreter="fixture", python="fixture",
            packages={"hexaly": "fake"}, implementation_hash="fixture")


def demand(count=90):
    catalogue = CatalogueManifest(DATASET, "fixture", ("a", "b", "c", "d"), ("x", "y"), (2, 2))
    orders = tuple(Order(f"O{i}", i, tuple(sorted(((i % 4, 1), ((i + 1) % 4, 1)))))
                   for i in range(count))
    return OrderedDemand(catalogue, orders)


class RescoringTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name) / "camp"
        (self.directory / "cases").mkdir(parents=True)
        self.data = demand()
        self.manifest = runner.quote((DATASET,), loader=lambda *_: self.data, metadata=META,
                                     stage="screen", arms=("NOM",))
        (self.directory / "manifest.json").write_text(canonical_json(self.manifest), encoding="utf-8")

    def _publish(self, row, assignment):
        record = dict(case=row, status="COMPLETE",
                      solve_result=dict(assignment=list(assignment), objective=1.0,
                                        native_status="F", status="FEASIBLE", bound=None, gap=None,
                                        bound_provenance="unavailable", build_seconds=0.1,
                                        solve_seconds=0.1, backend="hexaly", backend_version="fake",
                                        input_hash=row["input_hash"], model_hash=row["model_hash"],
                                        seed=row["seed"], threads=1, time_limit=row["time_limit"],
                                        representation="", solve_mode="visits", audit=()),
                      validation=dict(valid=True), evaluation=None, reference_evaluation=None)
        record["artifact_hash"] = digest({k: v for k, v in record.items() if k != "artifact_hash"})
        (self.directory / "cases" / f"{row['case_id']}.json").write_text(
            canonical_json(record), encoding="utf-8")
        (self.directory / "cases" / f"{row['case_id']}.frozen.json").write_text(canonical_json(
            dict(case_id=row["case_id"], input_hash=row["input_hash"],
                 assignment=list(assignment), layout_hash=digest(tuple(assignment)),
                 validation=dict(valid=True))), encoding="utf-8")

    def _eligible_rows(self):
        return [r for r in self.manifest["rows"] if r["eligibility"] is None]

    def test_secondary_records_cover_the_other_declared_horizons_only(self):
        rows = self._eligible_rows()
        self.assertTrue(rows)
        assignment = (0, 0, 1, 1)
        for row in rows:
            self._publish(row, assignment)
        produced = rescoring.score_campaign(self.directory, loader=lambda *_: self.data)
        self.assertTrue(produced)
        for record in produced:
            self.assertNotEqual(record["trained_n"], record["scored_n"])
            if record["status"] == "COMPLETE":
                self.assertEqual(record["evaluation"]["evaluation_kind"], "secondary_cross_horizon")
                self.assertFalse(record["evaluation"]["primary_same_horizon"])
                self.assertTrue(record["evaluation"]["future_boundaries"]["stream_adjacency_verified"])
                self.assertEqual(record["evaluation"]["order_count"], record["scored_n"])

    def test_rerun_reuses_artifacts_and_never_rewrites_them(self):
        for row in self._eligible_rows():
            self._publish(row, (0, 0, 1, 1))
        first = rescoring.score_campaign(self.directory, loader=lambda *_: self.data)
        stamps = {p: p.stat().st_mtime_ns
                  for p in (self.directory / rescoring.ARTIFACT_DIR).glob("*.json")}
        second = rescoring.score_campaign(self.directory, loader=lambda *_: self.data)
        self.assertEqual(digest(first), digest(second))
        self.assertEqual(stamps, {p: p.stat().st_mtime_ns
                                  for p in (self.directory / rescoring.ARTIFACT_DIR).glob("*.json")})

    def test_a_horizon_without_a_complete_future_is_recorded_not_skipped(self):
        for row in self._eligible_rows():
            self._publish(row, (0, 0, 1, 1))
        # Ask for a horizon far beyond the fixture stream.
        produced = rescoring.score_campaign(self.directory, loader=lambda *_: self.data,
                                            horizons=(4, 10_000))
        statuses = {r["status"] for r in produced}
        self.assertIn("INSUFFICIENT_FUTURE", statuses)
        for record in produced:
            if record["status"] == "INSUFFICIENT_FUTURE":
                self.assertIsNone(record["evaluation"])

    def test_tampered_frozen_layout_is_refused(self):
        rows = self._eligible_rows()
        self._publish(rows[0], (0, 0, 1, 1))
        path = self.directory / "cases" / f"{rows[0]['case_id']}.frozen.json"
        certificate = analysis._read(path)
        certificate["assignment"] = [1, 1, 0, 0]          # hash no longer matches
        path.write_text(canonical_json(certificate), encoding="utf-8")
        with self.assertRaisesRegex(ContractError, "CORRUPT_ARTIFACT"):
            rescoring.score_campaign(self.directory, loader=lambda *_: self.data)

    def test_unscored_case_produces_no_secondary_record(self):
        rows = self._eligible_rows()
        row = rows[0]
        record = dict(case=row, status="NO_INCUMBENT_LIMIT", solve_result=None, validation=None,
                      evaluation=None, reference_evaluation=None)
        record["artifact_hash"] = digest({k: v for k, v in record.items() if k != "artifact_hash"})
        (self.directory / "cases" / f"{row['case_id']}.json").write_text(
            canonical_json(record), encoding="utf-8")
        produced = rescoring.score_campaign(self.directory, loader=lambda *_: self.data)
        self.assertEqual(produced, [])

    def test_secondary_records_carry_the_rule_of_their_manifest_row(self):
        for row in self._eligible_rows():
            self.assertNotIn("rule", row, "upper-only manifests carry no rule key")
            self._publish(row, (0, 0, 1, 1))
        produced = rescoring.score_campaign(self.directory, loader=lambda *_: self.data)
        self.assertTrue(produced)
        self.assertEqual({r["rule"] for r in produced}, {"upper_only"})
        loaded = rescoring.load_cross_horizon(self.directory)
        self.assertEqual({r["rule"] for r in loaded}, {"upper_only"})
        self.assertEqual({r["rule"] for r in analysis.cross_horizon_table(loaded)}, {"upper_only"})

    def test_two_sided_manifest_rows_stamp_two_sided_secondary_records(self):
        manifest = runner.quote((DATASET,), loader=lambda *_: self.data, metadata=META,
                                stage="screen", arms=("NOM",), delta="0.02", rule="two_sided")
        directory = Path(self.temporary.name) / "two"
        (directory / "cases").mkdir(parents=True)
        (directory / "manifest.json").write_text(canonical_json(manifest), encoding="utf-8")
        self.manifest, self.directory = manifest, directory
        rows = self._eligible_rows()
        self.assertTrue(rows)
        for row in rows:
            self.assertEqual(row["rule"], "two_sided")
            self._publish(row, (0, 0, 1, 1))
        produced = rescoring.score_campaign(directory, loader=lambda *_: self.data)
        self.assertTrue(produced)
        self.assertEqual({r["rule"] for r in produced}, {"two_sided"})
        complete = [r for r in rescoring.load_cross_horizon(directory) if r["status"] == "COMPLETE"]
        self.assertTrue(complete)
        for row in analysis.cross_horizon_table(complete):
            self.assertEqual(row["rule"], "two_sided")
            self.assertIsNotNone(row["floor_violation_count"])
            self.assertEqual(row["violation_count"],
                             row["cap_violation_count"] + row["floor_violation_count"])

    def test_cross_horizon_table_marks_the_same_horizon_column(self):
        for row in self._eligible_rows():
            self._publish(row, (0, 0, 1, 1))
        records = rescoring.score_campaign(self.directory, loader=lambda *_: self.data)
        complete = [r for r in records if r["status"] == "COMPLETE"]
        table = analysis.cross_horizon_table(complete)
        self.assertEqual(len(table), len(complete))
        self.assertTrue(all(entry["same_horizon"] is False for entry in table))
        self.assertTrue(all(entry["evaluation_kind"] == "secondary_cross_horizon" for entry in table))


if __name__ == "__main__":
    unittest.main()
