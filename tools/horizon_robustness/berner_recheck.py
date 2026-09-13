"""Bounded BERNER recheck of the exact integer-count row formulation.

Re-solves the industrial case that the float formulation left as
NUMERICAL_ISSUE, at the same 1800 s cap, and records whether the returned
layout passes the UNCHANGED independent exact validator at its unchanged 1e-8
model tolerance. This verifies a numerical representation, not a scientific
comparison, and reads no future window.
"""
import json, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from Baselines.horizon_robustness.orders import complete_window, load_industrial
from Baselines.horizon_robustness.protocol import canonical_json, digest
from Baselines.horizon_robustness.uncertainty import ROW_FORMULATION, build_training_problem, integer_cap_rows
from Baselines.horizon_robustness.validation import validate_assignment

OUT = ROOT / "reports" / "horizon_robustness_results" / "diagnostics"


def main():
    arm = sys.argv[1] if len(sys.argv) > 1 else "HIST+ACT"
    cap = int(sys.argv[2]) if len(sys.argv) > 2 else 1800
    t0 = time.time()
    demand = load_industrial(ROOT)
    origin = 7 * len(demand.orders) // 10
    history = complete_window(demand.orders, 0, origin)
    problem = build_training_problem(demand.catalogue, history, demand.catalogue.p, arm,
                                     "0.01", "0.01", "0.5")
    rows, nu = integer_cap_rows(problem)
    load_seconds = time.time() - t0
    print(f"loaded+built in {load_seconds:.1f}s; rows={len(rows)} effective_nu={nu} "
          f"max_left_side={max(r['maximum_left_side'] for r in rows)}", flush=True)

    from Baselines.horizon_robustness import hexaly_backend
    result = hexaly_backend.solve(problem, seed=11, threads=1, time_limit=cap, solve_mode="visits")
    audit = dict(result.audit)
    record = dict(
        kind="numerical_formulation_recheck", dataset_id="BERNER", arm=arm,
        origin=origin, n=problem.n, delta="0.01", nu="0.01", time_limit=cap,
        row_formulation=audit.get("row_formulation"),
        integer_typed_rows=audit.get("integer_typed_rows"),
        finite_row_count=audit.get("finite_row_count"),
        status=result.status.value, native_status=result.native_status,
        objective=result.objective, bound=result.bound,
        build_seconds=result.build_seconds, solve_seconds=result.solve_seconds,
        input_hash=problem.input_hash, model_hash=problem.model_hash,
        load_and_build_seconds=round(load_seconds, 1), future_data_used=False)
    if result.assignment is not None:
        certificate = validate_assignment(problem, result.assignment, objective=result.objective,
                                          solve_mode="visits", history=history)
        record.update(
            exact_validation_valid=certificate["valid"],
            exact_violations=certificate["violations"][:5],
            model_feasible=certificate["model_feasible"],
            model_feasible_exact=certificate["model_feasible_exact"],
            maximum_model_residual_exact=certificate["maximum_model_residual_exact"],
            maximum_model_excess_exact=certificate["maximum_model_excess_exact"],
            minimum_required_slack_exact=certificate["minimum_required_slack_exact"],
            layout_hash=digest(result.assignment))
    else:
        record.update(exact_validation_valid=None,
                      note="no incumbent returned; the recheck is inconclusive, not a failure of the formulation")
    record["record_hash"] = digest(record)
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"berner_recheck_{arm.replace('+', '')}_{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}.json"
    path.write_text(canonical_json(record), encoding="utf-8")
    print(canonical_json({k: v for k, v in record.items() if k != "exact_violations"}))
    print("BERNER RECHECK COMPLETE")


main()
