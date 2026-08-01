r"""
Industrial run of the BINARY formulation with Hexaly (Company A / BERNER).

Companion to the synthetic sweep in ``Baselines/run_exp02a_binary_hexaly.py``.
Together they justify the reformulation claim of Section 3.4 with a controlled
comparison instead of an assertion: the set-variable model and this one are
solved by the same engine, on the same inputs, from the same warm start, under
the same budget, and differ only in how the decision is represented.

Protocol is taken verbatim from ``run_benchmarks_industrial.py`` so the result
is directly comparable with the 917,465 visits reported for the set-variable
MILP in Table 8:

  * the same ``load_industrial_data`` preprocessing (pruning, station speeds,
    per-station caps);
  * the same solver inputs ``op_solver, st_solver, pr_solver, pl_solver``;
  * the same warm start, the layout the site operates today;
  * the same full evaluation, counting visits on ALL orders with the statically
    fixed products merged back in.

Usage (env with Hexaly, from the CSLAP-Synthetic root):
    python run_industrial_binary_hexaly.py --time_limit 36000

Writes results_industrial_binary_hexaly.csv and the assignment JSON. Expect the
full ten hours; the model carries roughly 383,400 boolean decision variables
against the set-variable model's 24 set variables.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import defaultdict

import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "Baselines"))

from data_loader_industrial import load_industrial_data  # noqa: E402
from milp_binary_hexaly import run_milp_binary_hexaly  # noqa: E402


def evaluate_full_metrics(partial_assignment, static_assignment, op_full,
                          st_full, pl_full):
    """Verbatim copy of run_benchmarks_industrial.evaluate_full_metrics."""
    final_assignment = partial_assignment.copy()
    final_assignment.update(static_assignment)
    total_visits = 0
    for _o, prods in op_full.items():
        visited = set()
        for p in prods:
            if p in final_assignment:
                visited.add(final_assignment[p])
        total_visits += len(visited)
    station_counts = defaultdict(int)
    station_actions = defaultdict(float)
    speeds = {s["STATION_ID"]: s["SPEED"] for s in st_full}
    caps = {s["STATION_ID"]: s["CAPACITY"] for s in st_full}
    time_caps = {s["STATION_ID"]: s["TIME_CAPACITY"] for s in st_full}
    for p, sid in final_assignment.items():
        station_counts[sid] += 1
        qty = pl_full.get(p, 0)
        station_actions[sid] += qty / speeds.get(sid, 1.0) if speeds.get(sid, 1.0) > 0 else 0
    station_ids = [s["STATION_ID"] for s in st_full]
    cap_broken = sum(1 for sid in station_ids if station_counts[sid] > caps.get(sid, 0))
    wl_broken = sum(1 for sid in station_ids
                    if station_actions[sid] > time_caps.get(sid, 0.0) + 1e-5)
    actual = [station_actions[sid] for sid in station_ids]
    max_workload = float(np.max(actual)) if actual else 0.0
    utilization_pcts = []
    for sid in station_ids:
        mc = time_caps.get(sid, 0.0)
        utilization_pcts.append((station_actions[sid] / mc) * 100.0 if mc > 0 else 0.0)
    utilization_std_dev = float(np.std(utilization_pcts)) if utilization_pcts else 0.0
    return total_visits, max_workload, utilization_std_dev, cap_broken, wl_broken


def main() -> None:
    ap = argparse.ArgumentParser(description="Industrial binary-formulation run")
    ap.add_argument("--data_path", type=str,
                    default="Heuristic_Connex_Set_Project/data/BERNER_ORDER_LINES_09-12.csv")
    ap.add_argument("--time_limit", type=int, default=36000)
    ap.add_argument("--verbosity", type=int, default=1)
    args = ap.parse_args()

    data = load_industrial_data(args.data_path)
    op_solver = data["op_solver"]
    st_solver = data["st_solver"]
    pr_solver = data["pr_solver"]
    pl_solver = data["pl_solver"]
    warm = data["warm_start_assignment"]
    static_assignment = data["static_assignment"]
    op_full, st_full, pl_full = data["op_full"], data["st_full"], data["pl_full"]

    n_bool = len(pr_solver) * len(st_solver)
    print(f"Industrial BINARY/Hexaly: {len(pr_solver)} movable SKUs, "
          f"{len(st_solver)} active stations, {len(op_solver)} solver orders, "
          f"tl={args.time_limit}s", flush=True)
    print(f"  model carries {n_bool:,} boolean decision variables "
          f"(the set-variable model carries {len(st_solver)})", flush=True)

    t0 = time.time()
    (assignment, model_obj, elapsed, _mw, _ws, _cb, _wb, moved) = \
        run_milp_binary_hexaly(
            op_solver, st_solver, pr_solver, pl_solver,
            time_limit=args.time_limit, verbosity=args.verbosity,
            warm_start_assignment=warm,
        )
    total_elapsed = time.time() - t0

    visits, max_wl, util_std, cap_b, wl_b = evaluate_full_metrics(
        assignment, static_assignment, op_full, st_full, pl_full)

    print(f"FULL evaluation: visits={visits} max_wl={max_wl:.0f} "
          f"util_std={util_std:.2f} cap_broken={cap_b} wl_broken={wl_b} "
          f"solver_obj={model_obj} moved={moved} time={total_elapsed:.0f}s",
          flush=True)

    out = {
        "Method": "Binary MILP (Hexaly)",
        "visits": visits,
        "solver_obj": model_obj,
        "products_moved_off_warm_start": moved,
        "time": round(total_elapsed, 1),
        "time_limit": args.time_limit,
        "max_workload": round(max_wl, 1),
        "utilization_std_dev": round(util_std, 3),
        "cap_broken": cap_b,
        "wl_broken": wl_b,
        "n_bool_vars": n_bool,
        "num_orders": len(op_full),
        "num_skus": len(pr_solver) + len(static_assignment),
        "num_stations": len(st_full),
    }
    pd.DataFrame([out]).to_csv(
        os.path.join(BASE_DIR, "results_industrial_binary_hexaly.csv"),
        index=False)
    with open(os.path.join(BASE_DIR,
                           "industrial_binary_hexaly_assignment.json"), "w") as fh:
        json.dump(assignment, fh)
    print("saved results_industrial_binary_hexaly.csv + assignment JSON",
          flush=True)


if __name__ == "__main__":
    main()
