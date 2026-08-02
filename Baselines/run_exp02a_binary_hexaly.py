r"""
EXP-02a runner: binary formulation vs set-variable reformulation, same engine.

Produces the evidence for the reformulation claim of Section 3.4. Both models are
solved by Hexaly from the same LPT warm start under the same per-size budget, so
the only thing that differs is how the decision is represented. The set-variable
numbers already exist in ``exp02a_results_rerun/exp02a_per_instance.csv``; this
runner fills in the binary column.

Recorded per instance: the model objective, visits recounted on the raw orders,
how many products the search moved off the warm start, feasibility counts and
wall clock. ``status`` separates a genuine solve from a build failure, which is
itself a result at the larger sizes.

Usage (env savoye2023, from the CSLAP-Synthetic root):
    python Baselines/run_exp02a_binary_hexaly.py --sizes 50 500 1000 2000
    python Baselines/run_exp02a_binary_hexaly.py --compare
Append-only and restartable: finished (size, seed) pairs are skipped.
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

from milp_gurobi_synthetic import read_data  # noqa: E402  (plain CSV reader)
from milp_binary_hexaly import run_milp_binary_hexaly  # noqa: E402
from milp_synthetic import run_milp_hexaly  # noqa: E402  (set-variable twin)

INSTANCE_DIR = os.path.join(_ROOT, "exp02a_instances")
OUT_CSV = os.path.join(_ROOT, "exp02a_results", "exp02a_binary_hexaly.csv")
# Same harness, set-variable decisions: the on-machine control for the
# comparison, so both columns come from identical hardware.
OUT_CSV_SETVAR = os.path.join(_ROOT, "exp02a_results",
                              "exp02a_setvar_hexaly_localmachine.csv")
REF_CSV = os.path.join(_ROOT, "exp02a_results_rerun", "exp02a_per_instance.csv")

BUDGET = {50: 120, 500: 300, 1000: 600, 2000: 1200}

FIELDS = [
    "size_n", "instance_seed", "status", "visits", "model_obj",
    "warm_start_visits", "products_moved", "improved_on_warm_start",
    "time_s", "budget_s", "cap_broken", "wl_broken", "max_workload",
    "workload_std_dev", "num_skus", "num_stations", "num_orders", "note",
]


def lpt_start(products, stations, prod_lines):
    """The shared LPT seed; reproduces exp02a_results/exp02a_feasible_start.csv."""
    sids = [s["STATION_ID"] for s in stations]
    caps = {s["STATION_ID"]: s["CAPACITY"] for s in stations}
    tcaps = {s["STATION_ID"]: s["TIME_CAPACITY"] for s in stations}
    speeds = {s["STATION_ID"]: s["SPEED"] for s in stations}
    avg = (sum(speeds.values()) / len(speeds)) if speeds else 1.0
    assigned, cnt, load = {}, {s: 0 for s in sids}, {s: 0.0 for s in sids}
    for p in sorted(products, key=lambda q: prod_lines.get(q, 0) / avg,
                    reverse=True):
        w = prod_lines.get(p, 0)
        best = None
        for sid in sids:
            if cnt[sid] >= caps[sid]:
                continue
            cand = load[sid] + w / (speeds[sid] or 1.0)
            if cand <= tcaps[sid] and (best is None or cand < best[1]):
                best = (sid, cand)
        if best is None:
            open_s = [s for s in sids if cnt[s] < caps[s]] or sids
            best = (min(open_s, key=lambda s: load[s]), 0.0)
        sid = best[0]
        assigned[p] = sid
        cnt[sid] += 1
        load[sid] += w / (speeds[sid] or 1.0)
    return assigned


def count_visits(assignment, order_prods):
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


def compare() -> None:
    """Pair the binary column against the set-variable reference."""
    from scipy import stats
    b = pd.read_csv(OUT_CSV)
    b = b[b["status"] == "OK"][["size_n", "instance_seed", "visits",
                                "time_s", "wl_broken"]]
    b = b.rename(columns={"visits": "binary", "wl_broken": "bin_wl"})
    r = pd.read_csv(REF_CSV)
    r = r[(r["status"] == "OK") & (r["method"] == "Hexaly")]
    r = r[["size_n", "instance_seed", "visits"]].rename(
        columns={"visits": "setvar"})
    m = b.merge(r, on=["size_n", "instance_seed"])
    m["gap_pct"] = 100.0 * (m["binary"] - m["setvar"]) / m["setvar"]

    rows = []
    for size, g in m.groupby("size_n"):
        d = g["binary"].values - g["setvar"].values
        try:
            p = stats.wilcoxon(g["binary"], g["setvar"], mode="exact").pvalue
        except ValueError:
            p = float("nan")
        rows.append({
            "size_n": size, "n": len(g),
            "binary_mean": round(g["binary"].mean(), 1),
            "setvar_mean": round(g["setvar"].mean(), 1),
            "mean_gap_pct": round(g["gap_pct"].mean(), 2),
            "binary_wins": int((d < 0).sum()),
            "wilcoxon_p": round(float(p), 5) if p == p else "",
            "bin_wl_viol": int((g["bin_wl"] > 0).sum()),
        })
    out = pd.DataFrame(rows)
    p = os.path.join(_ROOT, "exp02a_results", "exp02a_binary_vs_setvar.csv")
    out.to_csv(p, index=False)
    pd.set_option("display.width", 200)
    print(out.to_string(index=False))
    print(f"\nwrote {p}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Binary vs set-variable, Hexaly")
    ap.add_argument("--sizes", nargs="+", type=int,
                    default=[50, 500, 1000, 2000])
    ap.add_argument("--compare", action="store_true")
    ap.add_argument("--model", choices=["binary", "setvar"], default="binary",
                    help="which decision representation to run")
    ap.add_argument("--tag", default="",
                    help="suffix for the output file, e.g. --tag server16core; "
                         "use a distinct tag per machine so results from "
                         "different hardware never mix")
    ap.add_argument("--fresh", action="store_true",
                    help="ignore any existing rows and re-run every instance")
    args = ap.parse_args()

    if args.compare:
        compare()
        return

    global OUT_CSV
    if args.model == "setvar":
        OUT_CSV = OUT_CSV_SETVAR
    if args.tag:
        root, ext = os.path.splitext(OUT_CSV)
        OUT_CSV = f"{root}_{args.tag}{ext}"

    done = set() if args.fresh else done_keys()
    print(f"model={args.model}  sizes={args.sizes}")
    print(f"output -> {OUT_CSV}")
    if done:
        print(f"{len(done)} instance(s) already recorded there and will be "
              f"SKIPPED. Use --fresh to redo them, or --tag <name> to write a "
              f"separate file.")
    planned = 0
    for _d in sorted(os.listdir(INSTANCE_DIR)):
        _m = re.fullmatch(r"syn_(\d+)sku_seed(\d+)", _d)
        if _m and int(_m.group(1)) in args.sizes                 and (int(_m.group(1)), int(_m.group(2))) not in done:
            planned += 1
    print(f"{planned} instance(s) to run.", flush=True)
    if planned == 0:
        print("Nothing to do. Every requested instance is already in the "
              "output file above.")
        return
    pat = re.compile(r"syn_(\d+)sku_seed(\d+)")
    for d in sorted(os.listdir(INSTANCE_DIR)):
        m = pat.fullmatch(d)
        if not m:
            continue
        size, seed = int(m.group(1)), int(m.group(2))
        if size not in args.sizes or (size, seed) in done:
            continue
        budget = BUDGET[size]
        print(f"=== {d} (budget {budget}s) ===", flush=True)
        base = {"size_n": size, "instance_seed": seed, "budget_s": budget}
        try:
            op, st, pr, pl = read_data(f"syn_{size}sku",
                                       os.path.join(INSTANCE_DIR, d))
            warm = lpt_start(pr, st, pl)
            wv = count_visits(warm, op)
            t0 = time.time()
            if args.model == "binary":
                (a, obj, el, mw, ws, cb, wb, moved) = run_milp_binary_hexaly(
                    op, st, pr, pl, time_limit=budget, verbosity=0,
                    warm_start_assignment=warm)
            else:
                (a, obj, el, mw, ws, cb, wb) = run_milp_hexaly(
                    op, st, pr, pl, time_limit=budget, verbosity=0,
                    warm_start_assignment=warm)
                moved = sum(1 for q, sx in a.items() if warm.get(q) != sx)
            recounted = count_visits(a, op)
            row = dict(base, status="OK", visits=recounted, model_obj=obj,
                       warm_start_visits=wv, products_moved=moved,
                       improved_on_warm_start=int(recounted < wv),
                       time_s=round(el, 1), cap_broken=cb, wl_broken=wb,
                       max_workload=round(mw, 1),
                       workload_std_dev=round(ws, 3),
                       num_skus=len(pr), num_stations=len(st),
                       num_orders=len(op), note="")
        except MemoryError:
            traceback.print_exc()
            row = dict(base, status="BUILD_FAIL", visits="", model_obj="",
                       warm_start_visits="", products_moved="",
                       improved_on_warm_start="", time_s="", cap_broken="",
                       wl_broken="", max_workload="", workload_std_dev="",
                       num_skus="", num_stations="", num_orders="",
                       note="MemoryError")
        except Exception as exc:  # noqa: BLE001 -- record and continue
            traceback.print_exc()
            row = dict(base, status=f"FAIL:{type(exc).__name__}", visits="",
                       model_obj="", warm_start_visits="", products_moved="",
                       improved_on_warm_start="", time_s="", cap_broken="",
                       wl_broken="", max_workload="", workload_std_dev="",
                       num_skus="", num_stations="", num_orders="",
                       note=str(exc)[:200])
        append_row(row)
        print(f"    -> {row['status']} visits={row['visits']} "
              f"warm={row['warm_start_visits']} moved={row['products_moved']}",
              flush=True)


if __name__ == "__main__":
    main()
