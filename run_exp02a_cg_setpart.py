r"""
EXP-02a benchmark runner for the aggregated set-partitioning CG (CPLEX).

Runs ``Baselines/cg_setpart_cplex.py`` on every instance directory under
``exp02a_instances/`` with the SAME protocol for every instance of a size
class (identical solver flags and seed; only the wall-clock budget is keyed by
size, and it never exceeds the Hexaly reference mean of exp02a v3):

=======  =========
size N   budget s
=======  =========
50       120
500      300
1000     600
2000     1200
=======  =========

These are the budgets printed in the manuscript's Table 5 and they are binding:
every method compared in that table must run under the same per-size cap. The
500-SKU entry was 600 s in the first campaign, which did not match the table;
it is 300 s here so the published protocol and the runs agree.

Appends one row per instance to ``exp02a_results/exp02a_cg_setpart.csv``.
Usage (CPLEX venv):
    python run_exp02a_cg_setpart.py --sizes 50 500 1000 2000
``--sizes`` lets the four size groups run as parallel processes.
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
import time
import traceback
from typing import List

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "Baselines"))

import cg_setpart_cplex as CG  # noqa: E402

INSTANCE_DIR = os.path.join(_HERE, "exp02a_instances")
RESULT_CSV = os.path.join(_HERE, "exp02a_results", "exp02a_cg_setpart.csv")
BUDGET = {50: 120, 500: 300, 1000: 600, 2000: 1200}
FIELDS = [
    "size_n", "instance_seed", "method", "status", "visits", "time_s",
    "best_bound", "max_workload", "workload_std_dev", "cap_broken",
    "wl_broken", "num_orders", "num_skus", "num_stations", "budget_s",
]


def append_row(row: dict) -> None:
    """Append one result row (writes the header on first use)."""
    new = not os.path.exists(RESULT_CSV)
    with open(RESULT_CSV, "a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerow(row)


def main() -> None:
    """Run the CG set-partitioning solver over the selected size groups."""
    ap = argparse.ArgumentParser(description="EXP-02a CG-SetPart runner")
    ap.add_argument("--sizes", nargs="+", type=int,
                    default=[50, 500, 1000, 2000])
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    dirs = sorted(os.listdir(INSTANCE_DIR))
    pat = re.compile(r"syn_(\d+)sku_seed(\d+)")
    for d in dirs:
        m = pat.fullmatch(d)
        if not m:
            continue
        size, iseed = int(m.group(1)), int(m.group(2))
        if size not in args.sizes:
            continue
        prefix = f"syn_{size}sku"
        data_dir = os.path.join(INSTANCE_DIR, d)
        budget = BUDGET[size]
        print(f"=== {d} (budget {budget}s) ===", flush=True)
        try:
            op, st, pr, pl = CG.read_data(prefix, data_dir)
            t0 = time.time()
            (assignment, visits, elapsed, util_var, max_util,
             cap_broken, wl_broken, bound) = CG.run_cg_setpart(
                op, st, pr, pl, time_limit=budget, seed=args.seed,
            )
            row = {
                "size_n": size, "instance_seed": iseed, "method": "CG-SetPart",
                "status": "OK", "visits": visits, "time_s": round(elapsed, 2),
                "best_bound": (round(bound, 1) if bound is not None else ""),
                "max_workload": max_util,
                "workload_std_dev": (util_var ** 0.5 if util_var is not None else ""),
                "cap_broken": cap_broken, "wl_broken": wl_broken,
                "num_orders": len(op), "num_skus": len(pr),
                "num_stations": len(st), "budget_s": budget,
            }
        except Exception as exc:  # noqa: BLE001 -- record failure, keep going
            traceback.print_exc()
            row = {
                "size_n": size, "instance_seed": iseed, "method": "CG-SetPart",
                "status": f"FAIL:{type(exc).__name__}", "visits": "",
                "time_s": "", "best_bound": "", "max_workload": "",
                "workload_std_dev": "", "cap_broken": "", "wl_broken": "",
                "num_orders": "", "num_skus": "", "num_stations": "",
                "budget_s": budget,
            }
        append_row(row)
        print(f"    -> {row['status']} visits={row['visits']} "
              f"LB={row['best_bound']} wl_broken={row['wl_broken']}", flush=True)


if __name__ == "__main__":
    main()
