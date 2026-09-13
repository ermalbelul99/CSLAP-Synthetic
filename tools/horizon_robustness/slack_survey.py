"""Solver-free upper bounds on the required slack of the declared uncertainty set.

The reference (incumbent) layout is always storage- and fixed-feasible, so the
slack IT requires is a valid UPPER bound on delta_min for that model:

    eta_ref(t, n, arm) = max(0, max_s [ max_{q in U} r_s(x_ref, q) - b_s ])
    delta_min(t, n, arm) <= eta_ref(t, n, arm).

Consequences, both of which are conclusions about the MODEL, not about a solver:

* If eta_ref <= delta, a feasible layout demonstrably exists at that tolerance,
  so a solver returning no incumbent there is a solver failure, not infeasibility.
* If eta_ref > delta, nothing is proven: some other layout may still need less.
  Only a certified lower bound can establish infeasibility.

This module imports no optimizer and reads no future window: every quantity
comes from the historical prefix and the frozen snapshot.
"""

from __future__ import annotations

import argparse
from fractions import Fraction
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from Baselines.horizon_robustness.orders import complete_window  # noqa: E402
from Baselines.horizon_robustness.protocol import (  # noqa: E402
    ContractError, canonical_json, eligible, horizon_grid)
from Baselines.horizon_robustness.reference import build_reference  # noqa: E402
from Baselines.horizon_robustness.runner import _load_dataset  # noqa: E402
from Baselines.horizon_robustness.uncertainty import build_training_problem  # noqa: E402
from Baselines.horizon_robustness.validation import validate_assignment  # noqa: E402

ARMS = ("NOM", "TIGHT", "HIST", "HIST+ACT")
DEFAULT_DELTA = "0.01"


def datasets():
    names = sorted(p.name for p in (ROOT / "exp02a_instances").iterdir() if p.is_dir())
    return names + ["BERNER"]


def survey_dataset(name, *, delta=DEFAULT_DELTA, nu="0.01", tightening="0.5", max_origins=1):
    started = time.time()
    demand = _load_dataset(name, ROOT)
    catalogue, orders = demand.catalogue, demand.orders
    first = 7 * len(orders) // 10
    rows = []
    for j in range(max_origins):
        origin = first + j * 2 * catalogue.p
        if not 0 < origin <= len(orders):
            continue
        history = complete_window(orders, 0, origin)
        reference = build_reference(catalogue, history)
        total_history_lines = sum(reference.historical_counts)
        for n in horizon_grid(catalogue.p):
            reason = eligible(origin, n, len(orders))
            for arm in ARMS:
                row = dict(dataset_id=name, kind=catalogue.kind, catalogue_size=catalogue.p,
                           stations=catalogue.s, orders=len(orders), origin=origin, n=n,
                           horizon_multiple=str(Fraction(n, catalogue.p)), arm=arm,
                           delta=delta, nu=nu, eligibility=reason,
                           scenarios=None, inactive_products=None,
                           mean_lines_per_order=round(total_history_lines / origin, 4),
                           expected_block_lines=None, reference_eta=None,
                           reference_eta_exact=None, reference_feasible_at_delta=None,
                           smallest_grid_delta_admitting_reference=None,
                           noise_scale_pp=None)
                if reason is None:
                    try:
                        problem = build_training_problem(catalogue, history, n, arm, delta, nu,
                                                         tightening, reference=reference)
                        certificate = validate_assignment(problem, reference.assignment)
                        eta = Fraction(certificate["minimum_required_slack_exact"])
                        row.update(
                            scenarios=len(problem.scenarios),
                            inactive_products=sum(certificate["inactive_counts"]),
                            reference_eta=float(eta), reference_eta_exact=str(eta),
                            reference_feasible_at_delta=eta <= Fraction(delta),
                            smallest_grid_delta_admitting_reference=next(
                                (g for g in ("0", "0.0025", "0.005", "0.01", "0.02", "0.05")
                                 if eta <= Fraction(g)), None))
                        # Multinomial share noise at this block size, for interpretation only.
                        block_lines = total_history_lines * n / origin
                        share = 1.0 / catalogue.s
                        row["expected_block_lines"] = round(block_lines, 1)
                        row["noise_scale_pp"] = round(
                            100 * (share * (1 - share) / block_lines) ** 0.5, 4) if block_lines else None
                    except ContractError as exc:
                        row["eligibility"] = exc.code
                rows.append(row)
    return rows, round(time.time() - started, 2)


def cross_arm_slack(campaign_directory, *, root=ROOT):
    """Free, solver-less delta_min upper bounds from layouts a campaign returned.

    Any structurally feasible layout bounds delta_min from above for EVERY arm,
    not only the arm that produced it. So a NOM layout scored against the HIST
    envelope gives a valid upper bound on the HIST model's delta_min even where
    the HIST solve itself returned no incumbent. No solver is called.
    """
    from Baselines.horizon_robustness_analysis.analysis import load_campaign

    campaign = load_campaign(campaign_directory)
    demands, references, rows = {}, {}, []
    for entry in campaign["entries"]:
        row, record = entry["row"], entry["record"]
        if record is None or record.get("status") not in ("COMPLETE", "DIAGNOSTIC_COMPLETE"):
            continue
        assignment = tuple((record.get("solve_result") or {}).get("assignment") or ())
        if not assignment:
            continue
        if row["dataset_id"] not in demands:
            demands[row["dataset_id"]] = _load_dataset(row["dataset_id"], root)
        demand = demands[row["dataset_id"]]
        history = complete_window(demand.orders, 0, row["origin"])
        key = (row["dataset_id"], row["origin"])
        if key not in references:
            references[key] = build_reference(demand.catalogue, history)
        for target_arm in ARMS:
            problem = build_training_problem(demand.catalogue, history, row["n"], target_arm,
                                             row["delta"], row["nu"], row["tightening"],
                                             reference=references[key])
            certificate = validate_assignment(problem, assignment)
            eta = Fraction(certificate["minimum_required_slack_exact"])
            rows.append(dict(
                dataset_id=row["dataset_id"], catalogue_size=(21874 if row["dataset_id"] == "BERNER"
                                                              else demand.catalogue.p),
                origin=row["origin"], n=row["n"], source_arm=row["arm"], target_arm=target_arm,
                seed=row["seed"], delta=row["delta"], nu=row["nu"],
                layout_from_status=record["status"],
                eta_upper_bound=float(eta), eta_upper_bound_exact=str(eta),
                meets_declared_delta=eta <= Fraction(row["delta"]),
                structurally_valid=certificate["structural_valid"],
                bound_kind="upper_bound_from_a_feasible_layout_never_an_infeasibility_proof"))
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--datasets", nargs="+", default=None)
    parser.add_argument("--delta", default=DEFAULT_DELTA)
    parser.add_argument("--max-origins", type=int, default=1)
    parser.add_argument("--output", default="reports/horizon_robustness_results/tables/slack_survey.csv")
    parser.add_argument("--campaign", help="also emit cross-arm upper bounds from this campaign's layouts")
    args = parser.parse_args(argv)

    selected = args.datasets or datasets()
    rows, timings = [], {}
    for name in selected:
        produced, seconds = survey_dataset(name, delta=args.delta, max_origins=args.max_origins)
        rows.extend(produced)
        timings[name] = seconds
        feasible = sum(1 for r in produced if r["reference_feasible_at_delta"])
        print(f"{name:<24} rows={len(produced):<3} reference-feasible at delta={args.delta}: "
              f"{feasible}/{len(produced)}  ({seconds}s)", flush=True)

    from Baselines.horizon_robustness_analysis.analysis import write_csv
    if args.campaign:
        cross = cross_arm_slack(args.campaign)
        cross_summary = write_csv(cross, ROOT / args.output.replace(".csv", "_cross_arm.csv"))
        print(f"cross-arm bounds from {args.campaign}: {len(cross)} rows -> {cross_summary['path']}",
              flush=True)
    summary = write_csv(rows, ROOT / args.output)
    (ROOT / args.output).with_suffix(".meta.json").write_text(canonical_json(
        dict(delta=args.delta, max_origins=args.max_origins, datasets=selected,
             load_seconds=timings, rows=len(rows), table=summary,
             method="reference-layout upper bound on delta_min; no optimizer imported",
             interpretation=("eta_ref <= delta proves a feasible layout exists; "
                             "eta_ref > delta proves nothing on its own"))), encoding="utf-8")
    print(canonical_json(dict(rows=len(rows), table=summary["path"], sha256=summary["sha256"])))
    print("SLACK SURVEY COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
