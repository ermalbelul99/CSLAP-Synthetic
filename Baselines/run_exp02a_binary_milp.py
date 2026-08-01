r"""
EXP-02a runner for the BINARY formulation solved by branch-and-bound (Gurobi).

The manuscript states that the binary model of Section 3.3, with variables
``x_ps`` and ``z_os``, stalls on the flat objective and that its certified bound
collapses to the trivial observation that every order visits at least one
station. Tables 5 and 8 carried no row for it, so the claim rested on a single
legacy run on one non-benchmark instance. This runner produces the evidence on
the same 29 exp02a instances, under the same per-size budgets as every other
method, from the same LPT warm start.

Model: ``Baselines/milp_gurobi_synthetic.run_milp_gurobi`` (binary x, continuous
z in [0,1], the linking constraint, capacity and workload rows).

Recorded per instance: visits, the Gurobi dual bound, whether the returned
layout differs at all from the warm start, feasibility counts, and wall clock.
``status`` distinguishes a genuine solve from the ways this formulation fails at
scale (BUILD_FAIL covers out-of-memory or a model too large to construct).

Usage (env savoye2023, from the CSLAP-Synthetic root):
    python Baselines/run_exp02a_binary_milp.py --sizes 50 500
    python Baselines/run_exp02a_binary_milp.py --aggregate
Append-only and restartable: completed (size, seed) pairs are skipped.
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
import time
import traceback

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _HERE)
sys.path.insert(0, _ROOT)

import pandas as pd  # noqa: E402

from milp_gurobi_synthetic import read_data, run_milp_gurobi  # noqa: E402

INSTANCE_DIR = os.path.join(_ROOT, "exp02a_instances")
OUT_CSV = os.path.join(_ROOT, "exp02a_results", "exp02a_binary_milp.csv")

# The budgets Table 5 prints, identical for every method.
BUDGET = {50: 120, 500: 300, 1000: 600, 2000: 1200}

FIELDS = [
    "size_n", "instance_seed", "status", "visits", "warm_start_visits",
    "improved_on_warm_start", "best_bound", "num_orders", "bound_is_trivial",
    "time_s", "budget_s", "cap_broken", "wl_broken", "max_workload",
    "workload_std_dev", "num_skus", "num_stations", "note",
]


def lpt_start(products, stations, prod_lines):
    """LPT warm start: the shared feasible seed given to every method."""
    sids = [s["STATION_ID"] for s in stations]
    caps = {s["STATION_ID"]: s["CAPACITY"] for s in stations}
    tcaps = {s["STATION_ID"]: s["TIME_CAPACITY"] for s in stations}
    speeds = {s["STATION_ID"]: s["SPEED"] for s in stations}
    avg_speed = (sum(speeds.values()) / len(speeds)) if speeds else 1.0

    assigned, cnt, load = {}, {s: 0 for s in sids}, {s: 0.0 for s in sids}
    for p in sorted(products, key=lambda q: prod_lines.get(q, 0) / avg_speed,
                    reverse=True):
        w = prod_lines.get(p, 0)
        best = None
        for sid in sids:
            if cnt[sid] >= caps[sid]:
                continue
            cand = load[sid] + w / (speeds[sid] or 1.0)
            if cand <= tcaps[sid] and (best is None or cand < best[1]):
                best = (sid, cand)
        if best is None:  # capacity exhausted: fall back to least loaded
            open_s = [s for s in sids if cnt[s] < caps[s]] or sids
            best = (min(open_s, key=lambda s: load[s]), 0.0)
        sid = best[0]
        assigned[p] = sid
        cnt[sid] += 1
        load[sid] += w / (speeds[sid] or 1.0)
    return assigned


def count_visits(assignment, order_prods):
    """Station visits of the real order stream under an assignment."""
    return sum(len({assignment[p] for p in prods if p in assignment})
               for prods in order_prods.values())


def append_row(row: dict) -> None:
    new = not os.path.exists(OUT_CSV)
    with open(OUT_CSV, "a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerow(row)


def done_keys() -> set:
    if not os.path.exists(OUT_CSV):
        return set()
    d = pd.read_csv(OUT_CSV)
    return {(int(r.size_n), int(r.instance_seed)) for r in d.itertuples()}


def aggregate() -> None:
    d = pd.read_csv(OUT_CSV)
    ok = d[d["status"] == "OK"]
    rows = []
    for size, g in ok.groupby("size_n"):
        rows.append({
            "size_n": size, "n": len(g),
            "mean_visits": round(g["visits"].mean(), 1),
            "mean_warm_start": round(g["warm_start_visits"].mean(), 1),
            "n_improved_on_warm_start": int(g["improved_on_warm_start"].sum()),
            "mean_bound": round(g["best_bound"].mean(), 1),
            "n_bound_trivial": int(g["bound_is_trivial"].sum()),
            "mean_time_s": round(g["time_s"].mean(), 1),
            "wl_viol_frac": round((g["wl_broken"] > 0).mean(), 3),
        })
    agg = pd.DataFrame(rows)
    p = os.path.join(_ROOT, "exp02a_results", "exp02a_binary_milp_agg.csv")
    agg.to_csv(p, index=False)
    print(agg.to_string(index=False))
    print(f"\nwrote {p}")
    for st, n in d["status"].value_counts().items():
        print(f"  status {st}: {n}")


def main() -> None:
    ap = argparse.ArgumentParser(description="EXP-02a binary MILP (Gurobi)")
    ap.add_argument("--sizes", nargs="+", type=int, default=[50, 500, 1000, 2000])
    ap.add_argument("--aggregate", action="store_true")
    args = ap.parse_args()

    if args.aggregate:
        aggregate()
        return

    done = done_keys()
    pat = re.compile(r"syn_(\d+)sku_seed(\d+)")
    for d in sorted(os.listdir(INSTANCE_DIR)):
        m = pat.fullmatch(d)
        if not m:
            continue
        size, seed = int(m.group(1)), int(m.group(2))
        if size not in args.sizes or (size, seed) in done:
            continue
        budget = BUDGET[size]
        prefix = f"syn_{size}sku"
        print(f"=== {d} (budget {budget}s) ===", flush=True)

        base = {"size_n": size, "instance_seed": seed, "budget_s": budget}
        try:
            op, st, pr, pl = read_data(prefix, os.path.join(INSTANCE_DIR, d))
            warm = lpt_start(pr, st, pl)
            warm_visits = count_visits(warm, op)

            t0 = time.time()
            (assignment, visits, elapsed, max_wl, wl_std,
             cap_b, wl_b, bound) = run_milp_gurobi(
                op, st, pr, pl, time_limit=budget, verbosity=0,
                warm_start_assignment=warm)
            elapsed = elapsed if elapsed else time.time() - t0

            # Recount on the raw orders rather than trusting the model objective.
            recounted = count_visits(assignment, op) if assignment else None
            n_orders = len(op)
            row = dict(base,
                       status="OK",
                       visits=recounted if recounted is not None else visits,
                       warm_start_visits=warm_visits,
                       improved_on_warm_start=int(
                           (recounted or visits) < warm_visits),
                       best_bound=(round(bound, 1) if bound is not None else ""),
                       num_orders=n_orders,
                       bound_is_trivial=int(
                           bound is not None and bound <= n_orders + 1e-6),
                       time_s=round(elapsed, 1),
                       cap_broken=cap_b, wl_broken=wl_b,
                       max_workload=round(max_wl, 1),
                       workload_std_dev=round(wl_std, 3),
                       num_skus=len(pr), num_stations=len(st), note="")
        except MemoryError:
            traceback.print_exc()
            row = dict(base, status="BUILD_FAIL", visits="", warm_start_visits="",
                       improved_on_warm_start="", best_bound="", num_orders="",
                       bound_is_trivial="", time_s="", cap_broken="",
                       wl_broken="", max_workload="", workload_std_dev="",
                       num_skus="", num_stations="", note="MemoryError")
        except Exception as exc:  # noqa: BLE001 -- record and continue
            traceback.print_exc()
            row = dict(base, status=f"FAIL:{type(exc).__name__}", visits="",
                       warm_start_visits="", improved_on_warm_start="",
                       best_bound="", num_orders="", bound_is_trivial="",
                       time_s="", cap_broken="", wl_broken="", max_workload="",
                       workload_std_dev="", num_skus="", num_stations="",
                       note=str(exc)[:200])
        append_row(row)
        print(f"    -> {row['status']} visits={row['visits']} "
              f"warm={row['warm_start_visits']} bound={row['best_bound']}",
              flush=True)


if __name__ == "__main__":
    main()
