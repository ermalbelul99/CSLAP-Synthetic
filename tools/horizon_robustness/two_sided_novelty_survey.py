"""Re-score the two-sided BERNER cases under the repaired code: novelty both ways.

The stored evaluations of exploratory revision 2 counted departures from the
modelled uncertainty set in the UPWARD direction only (``station_novelty_count``).
The 13 September 2026 review asked for the downward direction as well: stations
whose realized future share fell below the lowest share the uncertainty set
allowed are direct witnesses that the future left the modelled set, whether or
not a floor broke. This tool rebuilds each two-sided BERNER case exactly as the
runner did, re-scores the frozen layout and the incumbent with the current
``metrics.evaluate_layout``, and writes one row per case with both directions.
It also asserts that every field the stored evaluation carries is reproduced,
so the survey doubles as a regression check on the industrial models.

No optimizer, no new future: the futures are the ones already scored. Output:
``tables/two_sided_novelty_survey.csv``.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from Baselines.horizon_robustness.metrics import evaluate_layout            # noqa: E402
from Baselines.horizon_robustness.orders import complete_window              # noqa: E402
from Baselines.horizon_robustness.protocol import ContractError, canonical_json  # noqa: E402
from Baselines.horizon_robustness.runner import _load_dataset                # noqa: E402
from Baselines.horizon_robustness.uncertainty import build_training_problem  # noqa: E402

RESULTS = ROOT / "reports" / "horizon_robustness_results"
CAMPAIGNS = RESULTS / "campaigns"
OUT = RESULTS / "tables" / "two_sided_novelty_survey.csv"
COMPARED = ("joint_pass", "violation_count", "cap_violation_count", "floor_violation_count",
            "worst_excess_percentage_points_exact", "maximum_residual_exact", "borderline",
            "mean_visits_exact", "station_novelty_count", "layout_hash", "future_hash")


def _read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default="BERNER")
    args = parser.parse_args(argv)
    started = time.time()
    loaded, rows, mismatches = {}, [], 0
    for manifest_path in sorted(CAMPAIGNS.glob("*/manifest.json")):
        directory = manifest_path.parent
        if (directory / "SUPERSEDED.md").exists():
            continue
        manifest = _read(manifest_path)
        for row in manifest["rows"]:
            if row.get("rule") != "two_sided" or row["dataset_id"] != args.dataset or row["eligibility"]:
                continue
            case_path = directory / "cases" / f"{row['case_id']}.json"
            frozen_path = directory / "cases" / f"{row['case_id']}.frozen.json"
            if not case_path.exists() or not frozen_path.exists():
                continue
            case, frozen = _read(case_path), _read(frozen_path)
            if case.get("status") != "COMPLETE":
                continue
            if args.dataset not in loaded:
                loaded[args.dataset] = _load_dataset(args.dataset, ROOT)
            demand = loaded[args.dataset]
            history = complete_window(demand.orders, 0, row["origin"])
            problem = build_training_problem(demand.catalogue, history, row["n"], row["arm"], row["delta"],
                                             row["nu"], row["tightening"], rule="two_sided")
            if problem.input_hash != row["input_hash"]:
                raise ContractError("REBUILT_INPUT_CHANGED", f"{directory.name} {row['case_id'][:12]}")
            future = complete_window(demand.orders, row["origin"], row["origin"] + row["n"])
            for kind, layout in (("optimised", tuple(frozen["assignment"])),
                                 ("incumbent", problem.reference.assignment)):
                stored = case["evaluation" if kind == "optimised" else "reference_evaluation"]
                live = evaluate_layout(problem, layout, future)
                for field in COMPARED:
                    if field in stored and canonical_json(stored[field]) != canonical_json(live.get(field)):
                        mismatches += 1
                        print(f"MISMATCH {directory.name} {row['case_id'][:12]} {kind} {field}: "
                              f"stored={stored[field]} live={live.get(field)}")
                stations = live["stations"]
                rows.append(dict(
                    campaign=directory.name, dataset_id=row["dataset_id"], origin=row["origin"], n=row["n"],
                    arm=row["arm"], delta=row["delta"], nu=row["nu"], tightening=row["tightening"],
                    rule="two_sided", layout=kind, joint_pass=live["joint_pass"],
                    cap_violation_count=live["cap_violation_count"],
                    floor_violation_count=live["floor_violation_count"],
                    worst_excess_pp=live["worst_excess_percentage_points"],
                    stations_above_worst_scenario=live["station_novelty_count"],
                    stations_below_lowest_scenario=live["station_novelty_count_lower"],
                    maximum_novelty_excess=live["maximum_novelty_excess"],
                    maximum_novelty_shortfall=live["maximum_novelty_shortfall"],
                    stations_outside_modelled_set=sum(1 for s in stations
                                                      if s["beyond_worst_scenario"] or s["below_lowest_scenario"]),
                    station_count=len(stations),
                    activation_mass=live["activation_mass"], effective_nu=live["effective_nu"],
                    stored_fields_reproduced=all(
                        field not in stored or canonical_json(stored[field]) == canonical_json(live.get(field))
                        for field in COMPARED)))
                print(json.dumps({k: rows[-1][k] for k in ("campaign", "n", "arm", "layout", "joint_pass",
                                                             "stations_above_worst_scenario",
                                                             "stations_below_lowest_scenario",
                                                             "stations_outside_modelled_set")}))
    if not rows:
        print("NO TWO-SIDED CASES FOUND", file=sys.stderr)
        return 1
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps(dict(rows=len(rows), mismatches=mismatches, path=str(OUT),
                          elapsed_seconds=round(time.time() - started, 1))))
    print("TWO-SIDED NOVELTY SURVEY COMPLETE" + ("" if not mismatches else " WITH MISMATCHES"))
    return 1 if mismatches else 0


if __name__ == "__main__":
    raise SystemExit(main())
