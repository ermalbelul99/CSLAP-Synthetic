r"""
Industrial (Company A / BERNER) run of the heterogeneous set-partitioning CG.

Reproduces the EXACT protocol of ``run_benchmarks_industrial.py`` (the table
``tab:industrial_21877sku``): same ``load_industrial_data`` preprocessing
(pruning, station speeds, per-station caps = current profile), same warm start
(the original industrial layout), same 10-hour wall-clock limit, and the SAME
full-evaluation function (visits on ALL orders, statically fixed SKUs merged
back, utilization-%% std dev on the full per-station time caps).

Usage (CPLEX venv):
    python run_industrial_cg_setpart.py --time_limit 36000
Writes results_industrial_cg_setpart.csv + the assignment JSON.
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
from cg_setpart_hetero_cplex import run_cg_setpart_hetero  # noqa: E402


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
    ap = argparse.ArgumentParser(description="Industrial CG-SetPart run")
    ap.add_argument("--data_path", type=str,
                    default="Heuristic_Connex_Set_Project/data/BERNER_ORDER_LINES_09-12.csv")
    ap.add_argument("--time_limit", type=int, default=36000)
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--slack", type=float, default=None,
                    help="Symmetric band shorthand: floor=(1-slack), "
                         "ceiling=(1+slack) x current workload.")
    ap.add_argument("--ceiling-frac", type=float, default=1.0,
                    help="Per-station workload ceiling as a fraction of current "
                         "workload (1.0 = never exceed current, Hexaly's cap).")
    ap.add_argument("--floor-frac", type=float, default=1.0,
                    help="Per-station workload floor as a fraction of current "
                         "(0.0 = free to reduce, matching Hexaly; 1.0 = pinned).")
    ap.add_argument("--op-cap-slack", type=float, default=0.10,
                    help="Site slack already baked into the input workload caps "
                         "(default 0.10). The full-evaluation feasibility judge "
                         "uses (1 + this) x each station's original cap.")
    ap.add_argument("--match-hexaly", action="store_true",
                    help="Use the EXACT inputs the set-variable MILP received in "
                         "run_benchmarks_industrial: unmodified st_solver caps and "
                         "solver-frequency workloads (pl_solver), floor 0, judged "
                         "on the raw full caps. The only apples-to-apples setup.")
    args = ap.parse_args()
    if args.slack is not None:
        args.floor_frac, args.ceiling_frac = 1.0 - args.slack, 1.0 + args.slack

    data = load_industrial_data(args.data_path)
    op_solver = data["op_solver"]
    st_solver = data["st_solver"]
    pr_solver = data["pr_solver"]
    pl_solver = data["pl_solver"]
    warm = data["warm_start_assignment"]
    static_assignment = data["static_assignment"]
    op_full, st_full, pl_full = data["op_full"], data["st_full"], data["pl_full"]
    speeds = {s["STATION_ID"]: s["SPEED"] for s in st_solver}

    if args.match_hexaly:
        # Byte-for-byte the MILP's problem: its own caps (st_solver), its own
        # solver-frequency workload basis (pl_solver), ceiling only (no floor),
        # judged on the raw full caps exactly as Hexaly was in the benchmark.
        st_solver_adj = [dict(s) for s in st_solver]  # keeps TIME_CAPACITY, no _LO
        wl_lines = {p: pl_solver.get(p, 0) for p in pr_solver}
        cur_full_wl = {s["STATION_ID"]: s["TIME_CAPACITY"] for s in st_solver}
        args.op_cap_slack = 0.0  # judge on raw full caps, identical to Hexaly
        print(f"Industrial CG-SetPart [MATCH-HEXALY]: {len(pr_solver)} SKUs, "
              f"{len(st_solver)} stations, {len(op_solver)} solver orders, "
              f"tl={args.time_limit}s, using the MILP's exact caps and pl_solver",
              flush=True)
    else:
        # Workload alignment: the final judge (evaluate_full_metrics) charges each
        # kept product its FULL order-line frequency against the full time caps.
        wl_lines = {p: pl_full.get(p, 0) for p in pr_solver}
        cur_full_wl = {s["STATION_ID"]: 0.0 for s in st_solver}
        for p in pr_solver:
            sid = warm.get(p)
            if sid in cur_full_wl and speeds.get(sid, 0) > 0:
                cur_full_wl[sid] += wl_lines[p] / speeds[sid]
        # Envelope: floor_frac x current <= W_s <= ceiling_frac x current.
        st_solver_adj = [
            dict(s,
                 TIME_CAPACITY=args.ceiling_frac * cur_full_wl[s["STATION_ID"]],
                 TIME_CAPACITY_LO=args.floor_frac * cur_full_wl[s["STATION_ID"]])
            for s in st_solver
        ]
        print(f"Industrial CG-SetPart: {len(pr_solver)} SKUs, {len(st_solver)} "
              f"stations, {len(op_solver)} solver orders, tl={args.time_limit}s, "
              f"workload envelope = current x [{args.floor_frac:.2f}, "
              f"{args.ceiling_frac:.2f}]", flush=True)

    t0 = time.time()
    (assignment, solver_visits, elapsed, _uv, _mw, _cb, _wb, bound) = \
        run_cg_setpart_hetero(
            op_solver, st_solver_adj, pr_solver, wl_lines,
            time_limit=args.time_limit, threads=args.threads,
            warm_start_assignment=warm, seed=args.seed,
        )
    total_elapsed = time.time() - t0

    # The operational workload cap already carries the +10% site slack, so the
    # feasibility judge uses (1 + op_cap_slack) x each station's original cap,
    # identical to the envelope every baseline (incl. MILP Hexaly) respected.
    st_full_op = [dict(s, TIME_CAPACITY=s["TIME_CAPACITY"] * (1.0 + args.op_cap_slack))
                  for s in st_full]
    visits, max_wl, util_std, cap_b, wl_b = evaluate_full_metrics(
        assignment, static_assignment, op_full, st_full_op, pl_full)

    # Per-station deviation of the kept-product workload vs the current layout
    # (the band-compliance profile; compare with Hexaly's realized -5.9..+9.6%).
    new_wl = {sid: 0.0 for sid in cur_full_wl}
    for p, sid in assignment.items():
        if sid in new_wl and speeds.get(sid, 0) > 0:
            new_wl[sid] += wl_lines.get(p, 0) / speeds[sid]
    devs = {sid: (100.0 * (new_wl[sid] - cur_full_wl[sid]) / cur_full_wl[sid]
                  if cur_full_wl[sid] > 0 else 0.0) for sid in cur_full_wl}
    dev_vals = np.array(list(devs.values()))
    lo_pct, hi_pct = 100.0 * (args.floor_frac - 1.0), 100.0 * (args.ceiling_frac - 1.0)
    in_band = int(np.sum((dev_vals >= lo_pct - 1e-6) & (dev_vals <= hi_pct + 1e-6)))
    print(f"FULL evaluation: visits={visits} max_wl={max_wl:.0f} "
          f"util_std={util_std:.2f} cap_broken={cap_b} wl_broken={wl_b} "
          f"solver_visits={solver_visits} LB={bound} time={total_elapsed:.0f}s",
          flush=True)
    print(f"envelope profile: dev min={dev_vals.min():+.2f}% max={dev_vals.max():+.2f}% "
          f"std={dev_vals.std():.2f}% | in-envelope {in_band}/{len(dev_vals)} "
          f"([{lo_pct:+.0f}%, {hi_pct:+.0f}%])", flush=True)

    if args.match_hexaly:
        tag, method_label = "_matchhexaly", "CG Set-Part. (CPLEX) [Hexaly caps]"
    else:
        env = f"_ceil{int(round(100*args.ceiling_frac))}_floor{int(round(100*args.floor_frac))}"
        tag = "" if (args.ceiling_frac == 1.0 and args.floor_frac == 1.0) else env
        method_label = f"CG Set-Part. (CPLEX) env[{args.floor_frac:.2f},{args.ceiling_frac:.2f}]"
    out = {
        "Method": method_label,
        "visits": visits, "solver_visits": solver_visits,
        "best_bound": bound, "time": round(total_elapsed, 1),
        "time_limit": args.time_limit,
        "floor_frac": args.floor_frac, "ceiling_frac": args.ceiling_frac,
        "max_workload": round(max_wl, 1),
        "utilization_std_dev": round(util_std, 3),
        "cap_broken": cap_b, "wl_broken": wl_b,
        "dev_min_pct": round(float(dev_vals.min()), 3),
        "dev_max_pct": round(float(dev_vals.max()), 3),
        "dev_std_pct": round(float(dev_vals.std()), 3),
        "stations_in_band": in_band,
        "num_orders": len(op_full),
        "num_skus": len(pr_solver) + len(static_assignment),
        "num_stations": len(st_full),
    }
    pd.DataFrame([out]).to_csv(
        os.path.join(BASE_DIR, f"results_industrial_cg_setpart{tag}.csv"), index=False)
    with open(os.path.join(BASE_DIR, f"industrial_cg_setpart_assignment{tag}.json"), "w") as fh:
        json.dump(assignment, fh)
    print(f"saved results_industrial_cg_setpart{tag}.csv + assignment JSON", flush=True)


if __name__ == "__main__":
    main()
