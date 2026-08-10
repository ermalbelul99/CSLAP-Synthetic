"""Re-run ONLY the industrial heuristic row of Table 6, after the ratio-denominator fix.

Why this exists
---------------
The pair-support ratio of ``heuristic_synthetic.heuristic_cslap`` used to divide
the co-occurrence count by the LEXICOGRAPHICALLY FIRST endpoint's frequency,
while the article describes it as a fraction of the MORE FREQUENT endpoint's own
demand. The code now matches the article (``ratio_denominator="max"``), so every
published heuristic number has to be regenerated.

``run_benchmarks_industrial.py`` would also re-run Hexaly, Gurobi and the two
column generations under a 10-hour budget. Only the heuristic changed, so this
script loads the industrial instance through the SAME loader, calls the heuristic
with the SAME (default) thresholds, and evaluates it with the SAME
``evaluate_full_metrics`` the campaign used - reusing the functions rather than
reimplementing them - and writes a one-row CSV that can be diffed against the
cached row.

Provenance of the row being replaced
------------------------------------
Table 6 reports the heuristic at 1,016,003 visits / 94.36 s / max WL 11,919 /
util. sd 37.09, which is the row in ``results_industrial_benchmark_36.csv``
(time_limit 36,000 s = the 10-hour budget of the table's caption).
``results_industrial_benchmark.csv`` holds a DIFFERENT, older 72,000 s campaign
(1,012,329 visits); it is not the table's source. The heuristic itself has no
time budget - it returns in ~94 s - so the budget only labels the campaign.

Reproduce
---------
cd CSLAP-Synthetic
python run_industrial_heuristic_alone.py
python run_industrial_heuristic_alone.py --ratio-denominator first   # pre-fix check
"""

from __future__ import annotations

import argparse
import os
import sys
import time

import numpy as np
import pandas as pd

# The heuristic groups products through Python sets, so its greedy tie-breaks
# follow set iteration order, which CPython randomises per process. Two unpinned
# runs of this script returned 1,014,600 and 1,014,784 visits with 10 and 9
# stations over cap: the industrial row is NOT reproducible unless the seed is
# fixed. PYTHONHASHSEED is read at interpreter start-up, so it cannot be set from
# inside a running process; re-exec once with it in the environment.
if os.environ.get("PYTHONHASHSEED") != "0":
    os.environ["PYTHONHASHSEED"] = "0"
    os.execv(sys.executable, [sys.executable] + sys.argv)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
for _p in (BASE_DIR, os.path.join(BASE_DIR, "Baselines")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from data_loader_industrial import load_industrial_data          # noqa: E402
from heuristic_synthetic import heuristic_cslap                  # noqa: E402
# Same function run_benchmarks_industrial uses; it lives in its own module so this
# import does not drag in gurobipy / Hexaly, which the heuristic does not need.
from industrial_metrics import evaluate_full_metrics             # noqa: E402

_CACHED = os.path.join(BASE_DIR, "results_industrial_benchmark_36.csv")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data_path", type=str,
                   default="Heuristic_Connex_Set_Project/data/BERNER_ORDER_LINES_09-12.csv")
    p.add_argument("--ratio-denominator", type=str, default="max",
                   choices=("max", "first"))
    p.add_argument("--placement", type=str, default="preference",
                   choices=("balance", "preference"))
    # st_solver's TIME_CAPACITY is each station's RAW legacy load, and the site's
    # stated tolerance is +10% over it (Table 6, and
    # Baselines/report_industrial_deviation.py --tolerance 0.10). The synthetic
    # generator instead folds its 10% slack into TIME_CAPACITY, hence 0.0 there.
    p.add_argument("--wl-tolerance", type=float, default=0.10)
    p.add_argument("--no-repair", action="store_true")
    # Community bound beta. None => heuristic_cslap's own max(5, min(15, N//20)),
    # i.e. 15 here, which is what the published Table 6 row was run with; the
    # row is bit-identical whenever this flag is omitted. EXP-02c (repaired)
    # found beta* ~ 0.4-0.6 * zeta over zeta in [20, 100], and this site's
    # per-station slot capacity has mean 897 / median 242, far outside that
    # range -- so this flag exists to probe whether the clamp at 15 leaves
    # visits on the table industrially. Any value here is an extrapolation
    # beyond the tested range and must be reported as such.
    p.add_argument("--mnoppc", type=int, default=None,
                   help="community size bound beta (default: auto-scaled, =15)")
    p.add_argument("--out", type=str,
                   default="results_industrial_heuristic_ratiofix.csv")
    # Figure 11 is drawn from this file, and the Table 6 row from --out, so both
    # come from one and the same run. It keeps its historical name by default; a
    # parameter probe should redirect it so it cannot clobber the figure's data.
    p.add_argument("--per-station-out", type=str,
                   default="results_industrial_heuristic_per_station.csv")
    args = p.parse_args(argv)

    print(f"[load] {args.data_path}")
    data = load_industrial_data(args.data_path)

    num_orders = len(data["op_full"])
    num_skus = len(data["pr_solver"]) + len(data["static_assignment"])
    num_stations = len(data["st_full"])
    print(f"[load] orders={num_orders} skus={num_skus} stations={num_stations}")

    # ---- Give the heuristic the constraint it is actually judged on ----------
    # The industrial pipeline optimises in `pl_solver` units but reports in
    # `pl_full` units, and the two disagree per product (ratio 1.03-2.63, mean
    # 1.35) and per station (a station's solver capacity covers only 56-77% of
    # its true load). A repair that targets the solver-unit ceiling therefore
    # lands on its boundary there and overshoots the real tolerance: measured at
    # +16.7% on the worst station with 10 of 24 outside +10%.
    #
    # So the workload view handed to the heuristic is rebuilt in evaluation
    # units: each station's budget is what the +10% tolerance leaves for MOVABLE
    # products once the statically fixed ones are paid for,
    #
    #     T_s  <-  (1 + tol) * legacy_full(s)  -  static_load(s),
    #
    # with the tolerance already inside, so the heuristic runs at wl_tolerance=0.
    # Nothing about the objective changes; only the constraint becomes the true one.
    speeds = {s["STATION_ID"]: s["SPEED"] for s in data["st_full"]}
    pl_full = data["pl_full"]

    def _loads(assign):
        out = {s["STATION_ID"]: 0.0 for s in data["st_full"]}
        for p, sid in assign.items():
            if sid in out:
                sp = speeds.get(sid, 1.0) or 1.0
                out[sid] += pl_full.get(p, 0) / sp
        return out

    legacy_assign = dict(data["warm_start_assignment"])
    legacy_assign.update(data["static_assignment"])
    legacy_full = _loads(legacy_assign)
    static_load = _loads(data["static_assignment"])

    st_budget = []
    for s in data["st_solver"]:
        sid = s["STATION_ID"]
        budget = (1.0 + args.wl_tolerance) * legacy_full.get(sid, 0.0) \
            - static_load.get(sid, 0.0)
        st_budget.append({**s, "TIME_CAPACITY": max(budget, 0.0)})
    pl_eval = {p: pl_full.get(p, 0) for p in data["pr_solver"]}

    print(f"[run] heuristic, placement={args.placement}, "
          f"tolerance={args.wl_tolerance} folded into per-station budgets, "
          f"repair={not args.no_repair}, "
          f"beta={args.mnoppc if args.mnoppc is not None else 'auto(15)'}")
    beta_kw = {} if args.mnoppc is None else {"mnoppc": args.mnoppc}
    diag: dict = {}
    t0 = time.time()
    assignment, _v, elapsed, _mw, _sd, _cb, _wb = heuristic_cslap(
        data["op_solver"], st_budget, data["pr_solver"],
        pl_eval, data["odf_solver"],
        ratio_denominator=args.ratio_denominator,
        placement=args.placement, wl_tolerance=0.0,
        repair=not args.no_repair, diag=diag, **beta_kw,
    )
    visits, max_wl, wl_std, cap_b, wl_b = evaluate_full_metrics(
        assignment, data["static_assignment"],
        data["op_full"], data["st_full"], data["pl_full"],
    )
    print(f"[run] wall={time.time() - t0:.1f}s (solver-reported {elapsed:.2f}s)")

    row = {
        "Method": "Heuristic",
        "visits": visits,
        "time": elapsed,
        "max_workload": max_wl,
        "utilization_std_dev": wl_std,
        "cap_broken": cap_b,
        "wl_broken": wl_b,
        "num_orders": num_orders,
        "num_skus": num_skus,
        "num_stations": num_stations,
        "ratio_denominator": args.ratio_denominator,
        "placement": args.placement,
        "wl_tolerance": args.wl_tolerance,
        "mnoppc": args.mnoppc if args.mnoppc is not None else 15,
        "n_swaps": diag.get("n_swaps"),
        "n_overloaded_before": diag.get("n_overloaded_before"),
        "n_overloaded_after": diag.get("n_overloaded_after"),
        "n_pairs_kept": diag.get("n_pairs_kept"),
        "n_pstar": diag.get("n_pstar"),
        "community_size_max": diag.get("community_size_max"),
    }
    out_path = os.path.join(BASE_DIR, args.out)
    pd.DataFrame([row]).to_csv(out_path, index=False)
    print(f"[out] {out_path}")

    # Per-station load under the legacy and the heuristic layout, on the FULL
    # product base. Figure 11 is drawn from this file, so the figure and the
    # Table 6 row come from one and the same run.
    # Two quantities per station, and they are NOT interchangeable: the raw line
    # count, and the workload TIME_CAPACITY is expressed in, which is lines
    # divided by that station's calibrated speed. Speeds differ by orders of
    # magnitude on this site, so a raw line count must never be compared against
    # TIME_CAPACITY. Utilisation below uses the speed-adjusted load, exactly as
    # evaluate_full_metrics does.
    st_full, pl_full = data["st_full"], data["pl_full"]
    speeds = {s["STATION_ID"]: s["SPEED"] for s in st_full}

    legacy_assignment = dict(data["warm_start_assignment"])
    legacy_assignment.update(data["static_assignment"])
    new_assignment = dict(assignment)
    new_assignment.update(data["static_assignment"])

    def per_station_loads(assign):
        lines = {s["STATION_ID"]: 0.0 for s in st_full}
        load = {s["STATION_ID"]: 0.0 for s in st_full}
        for p, sid in assign.items():
            if sid not in lines:
                continue
            q = pl_full.get(p, 0)
            lines[sid] += q
            sp = speeds.get(sid, 1.0)
            load[sid] += q / sp if sp > 0 else 0.0
        return lines, load

    lines_o, load_o = per_station_loads(legacy_assignment)
    lines_n, load_n = per_station_loads(new_assignment)

    per_station = pd.DataFrame([{
        "STATION_ID": s["STATION_ID"],
        "SPEED": s["SPEED"],
        "TIME_CAPACITY": s["TIME_CAPACITY"],
        "lines_original": lines_o[s["STATION_ID"]],
        "lines_heuristic": lines_n[s["STATION_ID"]],
        "load_original": load_o[s["STATION_ID"]],
        "load_heuristic": load_n[s["STATION_ID"]],
    } for s in st_full])
    per_station["util_original"] = 100.0 * per_station["load_original"] / per_station["TIME_CAPACITY"]
    per_station["util_heuristic"] = 100.0 * per_station["load_heuristic"] / per_station["TIME_CAPACITY"]
    per_station["pct_change"] = 100.0 * (
        per_station["lines_heuristic"] - per_station["lines_original"]
    ) / per_station["lines_original"].replace(0, np.nan)
    ps_path = os.path.join(BASE_DIR, args.per_station_out)
    per_station.to_csv(ps_path, index=False)
    print(f"[out] {ps_path}")

    if os.path.exists(_CACHED):
        cached = pd.read_csv(_CACHED)
        cached = cached[cached["Method"] == "Heuristic"]
        if len(cached):
            c = cached.iloc[0]
            print("\n  field                 cached (Table 6)        new")
            print("  " + "-" * 56)
            for field, fmt in (("visits", "{:>14,.0f}"), ("time", "{:>14.2f}"),
                               ("max_workload", "{:>14.1f}"),
                               ("utilization_std_dev", "{:>14.2f}"),
                               ("wl_broken", "{:>14.0f}")):
                print(f"  {field:<20s}" + fmt.format(float(c[field]))
                      + "  " + fmt.format(float(row[field])))
            dv = 100.0 * (visits - float(c["visits"])) / float(c["visits"])
            print(f"\n  visit change vs the published row: {dv:+.3f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
