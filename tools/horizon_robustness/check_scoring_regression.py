"""Re-score stored layouts with the CURRENT code and compare with their records.

Every accepted case of the selected campaigns is rebuilt from the approved raw
orders exactly as the runner built it (prefix history, frozen layout, the next
n complete orders), evaluated with the current ``metrics.evaluate_layout`` for
both the returned layout and the incumbent, and compared field by field with
the immutable case record. A mismatch means the live scoring code no longer
reproduces a stored result, which is exactly what a behavioural regression in
upper-only or two-sided scoring would look like. No optimizer is used.

Datasets default to the small synthetic families so the check runs in minutes;
``--berner-cases K`` adds the first K BERNER cases of each campaign (each needs
a multi-minute industrial model build). Superseded campaigns are skipped.

Exit status 0 and the marker line ``SCORING REGRESSION CHECK PASSED`` only when
every compared field of every compared case agrees exactly.
"""
from __future__ import annotations

import argparse
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

CAMPAIGNS = ROOT / "reports" / "horizon_robustness_results" / "campaigns"
DEFAULT_DATASETS = ("syn_50sku_seed1001", "syn_500sku_seed1001", "syn_1000sku_seed1001")
# Fields compared exactly when present in the stored evaluation.
FIELDS = ("joint_pass", "violation_count", "cap_violation_count", "floor_violation_count",
          "worst_excess_percentage_points_exact", "maximum_residual_exact", "maximum_excess_exact",
          "borderline", "positive_excess_sum_exact", "mean_visits_exact", "visit_count",
          "activation_mass_exact", "effective_nu_exact", "station_novelty_count",
          "maximum_novelty_excess_exact", "layout_hash", "future_hash", "rule",
          "residuals_exact", "breaches_exact", "floors_exact", "floor_residuals_exact",
          "worst_scenario_envelope_exact", "station_shares_exact")


def _read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def check_campaign(directory, datasets, berner_cases, loaded):
    manifest = _read(directory / "manifest.json")
    compared, mismatches, berner_seen = 0, [], 0
    for row in manifest["rows"]:
        if row["eligibility"] or row["solve_mode"] != "visits":
            continue
        dataset = row["dataset_id"]
        if dataset == "BERNER":
            if berner_seen >= berner_cases:
                continue
        elif dataset not in datasets:
            continue
        case_path = directory / "cases" / f"{row['case_id']}.json"
        frozen_path = directory / "cases" / f"{row['case_id']}.frozen.json"
        if not case_path.exists() or not frozen_path.exists():
            continue
        case, frozen = _read(case_path), _read(frozen_path)
        if case.get("status") != "COMPLETE" or not case.get("evaluation"):
            continue
        if dataset == "BERNER":
            berner_seen += 1
        if dataset not in loaded:
            loaded[dataset] = _load_dataset(dataset, ROOT)
        demand = loaded[dataset]
        history = complete_window(demand.orders, 0, row["origin"])
        problem = build_training_problem(demand.catalogue, history, row["n"], row["arm"], row["delta"],
                                         row["nu"], row["tightening"], rule=row.get("rule", "upper_only"))
        if problem.input_hash != row["input_hash"]:
            raise ContractError("REBUILT_INPUT_CHANGED", f"{directory.name} {row['case_id'][:12]}")
        future = complete_window(demand.orders, row["origin"], row["origin"] + row["n"])
        for key, layout in (("evaluation", tuple(frozen["assignment"])),
                            ("reference_evaluation", problem.reference.assignment)):
            stored = case.get(key) or {}
            live = evaluate_layout(problem, layout, future)
            for field in FIELDS:
                if field in stored and canonical_json(stored[field]) != canonical_json(live.get(field)):
                    mismatches.append(dict(campaign=directory.name, case=row["case_id"][:12], dataset=dataset,
                                           arm=row["arm"], n=row["n"], record=key, field=field,
                                           stored=stored[field], live=live.get(field)))
            compared += 1
    return compared, mismatches


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--datasets", nargs="+", default=list(DEFAULT_DATASETS))
    parser.add_argument("--berner-cases", type=int, default=0)
    parser.add_argument("--campaign", action="append", help="restrict to these campaign directory names")
    args = parser.parse_args(argv)
    started = time.time()
    loaded, total, all_mismatches, summary = {}, 0, [], []
    for manifest in sorted(CAMPAIGNS.glob("*/manifest.json")):
        directory = manifest.parent
        if (directory / "SUPERSEDED.md").exists():
            continue
        if args.campaign and directory.name not in args.campaign:
            continue
        compared, mismatches = check_campaign(directory, set(args.datasets), args.berner_cases, loaded)
        summary.append(dict(campaign=directory.name, evaluations_compared=compared, mismatches=len(mismatches)))
        total += compared
        all_mismatches.extend(mismatches)
    for entry in summary:
        print(json.dumps(entry, sort_keys=True))
    for m in all_mismatches[:50]:
        print("MISMATCH " + json.dumps(m, sort_keys=True, default=str))
    print(json.dumps(dict(evaluations_compared=total, mismatches=len(all_mismatches),
                          elapsed_seconds=round(time.time() - started, 1)), sort_keys=True))
    if all_mismatches or total == 0:
        print("SCORING REGRESSION CHECK FAILED")
        return 1
    print("SCORING REGRESSION CHECK PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
