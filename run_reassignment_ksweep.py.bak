"""
Limited-Reassignment k-sweep on the industrial instance (Company A).

Re-solves the set-variable MILP (Hexaly) under a series of relocation caps k, where
k bounds the number of solver-active products allowed to leave their legacy station.
Produces a visits-vs-k curve to characterise the trade-off between re-slotting effort
and throughput gain (addresses CAOR referee concern 4.1 / R3 p.33).

All sweep points share a single per-run wall-clock budget so the curve is internally
consistent. The canonical full-optimization result (917,465 visits, 10h budget) is the
asymptotic reference reported separately in the manuscript.

Output: results_reassignment_ksweep.csv (written incrementally, restartable-friendly).
"""

import os
import sys
import time
import argparse
import numpy as np
import pandas as pd
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "Baselines"))

from data_loader_industrial import load_industrial_data
from milp_synthetic import run_milp_hexaly


def evaluate_full_metrics(partial_assignment, static_assignment, op_full, st_full, pl_full):
    """Full-base metrics (solver-assigned products + statically fixed low-freq products).
    Inlined from run_benchmarks_industrial.py to avoid importing Gurobi/dotenv dependencies."""
    if partial_assignment is None:
        return "-", "-", "-", "-", "-"

    final_assignment = partial_assignment.copy()
    final_assignment.update(static_assignment)

    total_visits = 0
    for o, prods in op_full.items():
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
    wl_broken = sum(1 for sid in station_ids if station_actions[sid] > time_caps.get(sid, 0.0) + 1e-5)

    actual_workloads = [station_actions[sid] for sid in station_ids]
    max_workload = float(np.max(actual_workloads)) if actual_workloads else 0.0

    utilization_pcts = []
    for sid in station_ids:
        max_cap = time_caps.get(sid, 0.0)
        utilization_pcts.append((station_actions[sid] / max_cap) * 100.0 if max_cap > 0 else 0.0)
    utilization_std_dev = float(np.std(utilization_pcts)) if utilization_pcts else 0.0

    return total_visits, max_workload, utilization_std_dev, cap_broken, wl_broken


def count_moves(assignment, original_assignment):
    """Number of solver products whose station differs from their legacy station."""
    if assignment is None:
        return None
    moves = 0
    for p, s0 in original_assignment.items():
        if p in assignment and assignment[p] != s0:
            moves += 1
    return moves


def main():
    parser = argparse.ArgumentParser(description="Limited-reassignment k-sweep (industrial, Hexaly)")
    parser.add_argument("--data_path", type=str,
                        default="Heuristic_Connex_Set_Project/data/BERNER_ORDER_LINES_09-12.csv")
    parser.add_argument("--k-grid", type=int, nargs="+",
                        default=[250, 500, 1000, 2000, 5000, 10000])
    parser.add_argument("--time-limit", type=int, default=3600,
                        help="Per-run wall-clock budget in seconds (default 1h).")
    parser.add_argument("--include-unrestricted", action="store_true",
                        help="Also run one unrestricted point (k = all solver products) at the same budget.")
    parser.add_argument("--out", type=str,
                        default=os.path.join(BASE_DIR, "results_reassignment_ksweep.csv"))
    args = parser.parse_args()

    print("=" * 70)
    print("Limited-Reassignment k-sweep | Industrial instance (Company A)")
    print("=" * 70)

    data = load_industrial_data(os.path.join(BASE_DIR, args.data_path)
                                if not os.path.isabs(args.data_path) else args.data_path)
    op_solver = data["op_solver"]
    st_solver = data["st_solver"]
    pr_solver = data["pr_solver"]
    pl_solver = data["pl_solver"]
    warm = data["warm_start_assignment"]          # legacy station s'(p) per solver product
    static_assignment = data["static_assignment"]
    op_full = data["op_full"]
    st_full = data["st_full"]
    pl_full = data["pl_full"]

    n_solver = len(pr_solver)
    n_orders_full = len(op_full)
    print(f"Solver-active products: {n_solver} | full orders: {n_orders_full} | "
          f"active stations: {len(st_solver)}")

    # Baseline (legacy layout, k = 0): evaluate the original assignment directly.
    base_visits, base_maxwl, base_util, base_capb, base_wlb = evaluate_full_metrics(
        warm, static_assignment, op_full, st_full, pl_full
    )
    print(f"Legacy baseline (k=0): visits={base_visits}")

    rows = []

    def write_row(k, assignment, visits, max_wl, util_std, cap_b, wl_b, elapsed, label):
        moves = count_moves(assignment, warm) if assignment is not None else 0
        mean_vpo = (visits / n_orders_full) if (visits not in (None, "-")) else None
        red = (base_visits - visits) if (visits not in (None, "-")) else None
        rows.append({
            "k": k,
            "label": label,
            "total_visits": visits,
            "mean_visits_per_order": mean_vpo,
            "reduction_vs_legacy": red,
            "moves_used": moves,
            "pct_catalog_moved": round(100.0 * moves / n_solver, 3) if moves is not None else None,
            "max_workload": max_wl,
            "utilization_std_dev": util_std,
            "cap_broken": cap_b,
            "wl_broken": wl_b,
            "time_s": round(elapsed, 1),
            "time_limit_s": args.time_limit,
            "n_solver_products": n_solver,
            "n_orders_full": n_orders_full,
        })
        pd.DataFrame(rows).to_csv(args.out, index=False)
        print(f"  [checkpoint] k={k} ({label}): visits={visits}, moves={moves}, "
              f"reduction={red} -> saved {args.out}")

    # k = 0 anchor (legacy layout)
    write_row(0, warm, base_visits, base_maxwl, base_util, base_capb, base_wlb, 0.0, "legacy_k0")

    grid = [k for k in args.k_grid if k < n_solver]
    if args.include_unrestricted:
        grid.append(n_solver)

    for k in grid:
        label = "unrestricted" if k >= n_solver else f"k{k}"
        print(f"\n--- Solving restricted MILP: k={k} ({label}), budget={args.time_limit}s ---")
        t0 = time.time()
        res = run_milp_hexaly(
            op_solver, st_solver, pr_solver, pl_solver,
            time_limit=args.time_limit,
            warm_start_assignment=warm,
            max_reassignments=k,
            original_assignment=warm,
        )
        elapsed = time.time() - t0
        assignment = res[0]
        visits, max_wl, util_std, cap_b, wl_b = evaluate_full_metrics(
            assignment, static_assignment, op_full, st_full, pl_full
        )
        write_row(k, assignment, visits, max_wl, util_std, cap_b, wl_b, elapsed, label)

    print("\n[Done] k-sweep complete.")
    print(pd.DataFrame(rows)[["k", "label", "total_visits", "reduction_vs_legacy",
                              "moves_used", "pct_catalog_moved", "time_s"]].to_string(index=False))


if __name__ == "__main__":
    main()
