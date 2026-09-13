"""Predeclared minimum-slack diagnostics on the ORIGINAL rational model.

Cases, caps and stopping rules are fixed in CAMPAIGN_PREDECLARATION.md section
7.3c before any solve runs. CPLEX only: it is the sole backend returning a bound
with stated provenance. No future window is read.

Upper bound  = independently recomputed required slack of the returned layout,
               accepted only if that layout passed independent validation.
Witnesses    = every returned layout, native result and certificate are saved in
               the JSON record so each bound can be replayed. The six runs of
               10 September 2026 predate this and saved summaries only; their
               bounds are logged results, not independently replayable ones.
Lower bound  = solver bound, used only with recorded provenance and > 0.
An interval straddling the declared delta is UNRESOLVED, with no direction.
"""
import sys, time
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from Baselines.horizon_robustness.orders import complete_window
from Baselines.horizon_robustness.protocol import canonical_json, digest
from Baselines.horizon_robustness.runner import _load_dataset
from Baselines.horizon_robustness.uncertainty import build_training_problem
from Baselines.horizon_robustness.validation import validate_assignment

OUT = ROOT / "reports" / "horizon_robustness_results" / "diagnostics"
DECLARED_DELTA = Fraction("0.01")

# (dataset, horizons, cap seconds) - predeclared, not chosen from outcomes.
CASES = (("syn_50sku_seed1001", (25, 50, 100), 900),
         ("syn_500sku_seed1001", (250, 500, 1000), 1200))


def main():
    from Baselines.horizon_robustness import cplex_backend

    rows, charged = [], 0
    for dataset, horizons, cap in CASES:
        demand = _load_dataset(dataset, ROOT)
        origin = 7 * len(demand.orders) // 10
        history = complete_window(demand.orders, 0, origin)
        for n in horizons:
            problem = build_training_problem(demand.catalogue, history, n, "HIST", "0.01", "0.01", "0.5")
            equivalent = build_training_problem(demand.catalogue, history, n, "HIST+ACT", "0.01", "0.01", "0.5")
            deduplicated = equivalent.model_hash == problem.model_hash
            t0 = time.time()
            result = cplex_backend.solve(problem, seed=11, threads=1, time_limit=cap, solve_mode="min_slack")
            charged += cap
            row = dict(dataset_id=dataset, catalogue_size=demand.catalogue.p, origin=origin, n=n,
                       arm="HIST", also_covers_hist_act=deduplicated, cap_seconds=cap,
                       declared_delta=float(DECLARED_DELTA), status=result.status.value,
                       native_status=result.native_status, bound_provenance=result.bound_provenance,
                       build_seconds=result.build_seconds, solve_seconds=result.solve_seconds,
                       wall_seconds=round(time.time() - t0, 1), model_hash=problem.model_hash)
            upper = None
            witness = None
            if result.assignment is not None:
                certificate = validate_assignment(problem, result.assignment,
                                                  objective=result.objective, solve_mode="min_slack",
                                                  min_slack=result.objective, history=history)
                # The layout, the full native result and the full certificate are
                # retained so the bound can be REPLAYED independently later. A
                # summary alone certifies only its own bytes, not the mathematics.
                witness = dict(assignment=list(result.assignment),
                               layout_hash=digest(tuple(result.assignment)),
                               solve_result=result.to_dict(), certificate=certificate)
                row.update(layout_valid=certificate["valid"],
                           solver_reported_objective=result.objective,
                           layout_hash=witness["layout_hash"])
                # An upper bound is only meaningful from a layout that passed
                # structural and row validation in min_slack mode.
                if certificate["valid"]:
                    upper = Fraction(certificate["minimum_required_slack_exact"])
                    row.update(eta_upper_bound=float(upper), eta_upper_bound_exact=str(upper))
                else:
                    row.update(eta_upper_bound=None, eta_upper_bound_exact=None,
                               upper_bound_rejected="layout failed independent validation")
            lower = result.bound if (result.bound_provenance not in (None, "unavailable")
                                     and result.bound is not None and result.bound > 0) else None
            row["eta_lower_bound"] = lower
            if upper is not None and lower is not None and Fraction(str(lower)) > upper + Fraction(1, 10**9):
                row["bound_inconsistency"] = "lower bound exceeds validated upper bound"
                verdict = "INCONSISTENT_BOUNDS"
            elif upper is not None and lower is not None:
                if Fraction(str(lower)) > DECLARED_DELTA:
                    verdict = "DECLARED_DELTA_PROVEN_UNATTAINABLE"
                elif upper <= DECLARED_DELTA:
                    verdict = "DECLARED_DELTA_ATTAINABLE"
                else:
                    verdict = "UNRESOLVED"          # interval straddles delta
            elif upper is not None:
                verdict = "DECLARED_DELTA_ATTAINABLE" if upper <= DECLARED_DELTA else "UNRESOLVED"
            else:
                verdict = "UNRESOLVED"
            row["witness"] = witness
            row["verdict"] = verdict
            row["interval_straddles_declared_delta"] = (
                upper is not None and lower is not None
                and Fraction(str(lower)) <= DECLARED_DELTA < upper)
            rows.append(row)
            print(canonical_json({k: v for k, v in row.items() if k != "witness"}), flush=True)

    # CSV keeps the summary; the JSON record keeps the witnesses.
    summary_rows = [{k: v for k, v in r.items() if k != "witness"} for r in rows]
    record = dict(kind="predeclared_min_slack_diagnostic", model="original_rational_model",
                  backend="cplex", future_data_used=False, charged_native_seconds=charged,
                  generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), rows=rows)
    record["record_hash"] = digest(record)
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"min_slack_{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}.json"
    path.write_text(canonical_json(record), encoding="utf-8")
    from Baselines.horizon_robustness_analysis.analysis import write_csv
    table = write_csv(summary_rows, ROOT / "reports/horizon_robustness_results/tables/min_slack_diagnostic_cplex.csv")
    print(canonical_json(dict(cases=len(rows), charged_native_seconds=charged,
                              record=str(path), table=table["path"])))
    print("MIN SLACK DIAGNOSTIC COMPLETE")


main()
