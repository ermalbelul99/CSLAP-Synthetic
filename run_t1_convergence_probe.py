r"""T1 convergence probe: did the set-partitioning master price out, per size?

Settles one question a referee raised about the manuscript. Section 4.2.5 reports
a lower bound of ~3,312 against ~7,590 visits found at 50 SKUs, and Section 8
proposes dual stabilisation as the route to a tighter bound. That prescription is
only correct if pricing was still truncated when the run stopped:

* If the master **priced out** (converged), then LB = z_RMP = z_LP exactly, the
  remaining gap is a pure *integrality* gap, and dual stabilisation cannot close
  it -- stabilisation accelerates convergence to z_LP, it cannot raise z_LP. The
  route would then be cutting planes, branch-and-price, or a stronger master.
* If the master was **truncated** by its deadline, LB = z_RMP + |S|*min(0,rc_lb)
  sits below z_LP, the gap mixes integrality with unfinished pricing, and
  stabilisation is a defensible perspective.

This script re-runs the published CG on the published instances and records, per
instance: whether pricing converged, why the loop stopped, z_RMP at the last
master solve, the last pricing dual bound rc_lb, and the reported LB. Nothing in
the search changes: it calls the same ``run_cg_setpart`` with the same budgets
and seed as ``run_exp02a_cg_setpart.py``, and only passes a ``diag`` dict that
the solver fills in.

Run on the machine with the CPLEX licence, from the repo root, in the CPLEX venv:

    python run_t1_convergence_probe.py --sizes 50 500 2>&1 | tee t1_probe.log

Sizes 50 and 500 are the ones that decide the argument and cost about an hour in
total. Sizes 1000 and 2000 are optional confirmation (~3.5 h more) and are
expected to show large negative rc_lb, i.e. clearly truncated.

Outputs:
    exp02a_results/t1_convergence_probe.csv   one row per instance
    t1_probe.log                              full stdout if you use tee

Send both back. The CSV alone is enough to settle it.
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
import traceback
from typing import Dict, List

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "Baselines"))

import cg_setpart_cplex as CG  # noqa: E402

INSTANCE_DIR = os.path.join(_HERE, "exp02a_instances")
RESULT_CSV = os.path.join(_HERE, "exp02a_results", "t1_convergence_probe.csv")

# Identical to run_exp02a_cg_setpart.py -- the published protocol.
BUDGET = {50: 120, 500: 300, 1000: 600, 2000: 1200}

FIELDS = [
    "size_n", "instance_seed", "status",
    "converged", "stop_reason",
    "z_rmp_last", "rc_lb_last", "pricing_optimal_last", "best_lb",
    "visits", "gap_to_lb_pct",
    "n_stations", "iterations", "n_exact_pricing",
    "cg_deadline_s", "cg_loop_elapsed_s", "total_elapsed_s",
    "n_orders", "n_supports", "budget_s",
]


def append_row(row: dict) -> None:
    """Append one probe row, writing the header on first use."""
    os.makedirs(os.path.dirname(RESULT_CSV), exist_ok=True)
    new = not os.path.exists(RESULT_CSV)
    with open(RESULT_CSV, "a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerow(row)


def summarise(rows: List[dict]) -> None:
    """Print the per-size verdict the manuscript needs."""
    by_size: Dict[int, List[dict]] = {}
    for r in rows:
        if r.get("status") == "OK":
            by_size.setdefault(int(r["size_n"]), []).append(r)

    print("\n" + "=" * 72)
    print("PER-SIZE VERDICT")
    print("=" * 72)
    for size in sorted(by_size):
        rs = by_size[size]
        conv = [r for r in rs if r["converged"]]
        print(f"\n  N = {size}  ({len(rs)} instances)")
        print(f"    converged (priced out) : {len(conv)} / {len(rs)}")
        reasons: Dict[str, int] = {}
        for r in rs:
            reasons[r["stop_reason"]] = reasons.get(r["stop_reason"], 0) + 1
        print(f"    stop reasons           : {reasons}")
        gaps = [r["gap_to_lb_pct"] for r in rs if r["gap_to_lb_pct"] != ""]
        if gaps:
            print(f"    mean gap to LB         : {sum(gaps) / len(gaps):.1f}%")
        if len(conv) == len(rs):
            print("    => LB = z_RMP = z_LP. The gap is a PURE INTEGRALITY GAP.")
            print("       Dual stabilisation cannot close it. Rewrite the")
            print("       perspective towards cuts / branch-and-price.")
        elif not conv:
            print("    => pricing was TRUNCATED at every instance. LB sits")
            print("       below z_LP and stabilisation remains defensible.")
        else:
            print("    => MIXED. Report the split explicitly in the paper.")
    print("\n" + "=" * 72)


def main() -> None:
    """Re-run the published CG and record convergence diagnostics."""
    ap = argparse.ArgumentParser(description="T1 CG convergence probe")
    ap.add_argument("--sizes", nargs="+", type=int, default=[50, 500],
                    help="size classes to probe (default: 50 500)")
    ap.add_argument("--seed", type=int, default=42,
                    help="solver seed, must match the published runs")
    args = ap.parse_args()

    pat = re.compile(r"syn_(\d+)sku_seed(\d+)")
    collected: List[dict] = []

    for d in sorted(os.listdir(INSTANCE_DIR)):
        m = pat.fullmatch(d)
        if not m:
            continue
        size, iseed = int(m.group(1)), int(m.group(2))
        if size not in args.sizes:
            continue

        budget = BUDGET[size]
        data_dir = os.path.join(INSTANCE_DIR, d)
        print(f"\n=== {d} (budget {budget}s) ===", flush=True)

        diag: Dict[str, object] = {}
        try:
            op, st, pr, pl = CG.read_data(f"syn_{size}sku", data_dir)
            CG.run_cg_setpart(op, st, pr, pl, time_limit=budget,
                              seed=args.seed, verbose=True, diag=diag)

            lb, visits = diag.get("best_lb"), diag.get("visits")
            gap = ""
            if lb is not None and visits:
                gap = round((visits - lb) / visits * 100.0, 1)

            row = {
                "size_n": size, "instance_seed": iseed, "status": "OK",
                "converged": diag.get("converged"),
                "stop_reason": diag.get("stop_reason"),
                "z_rmp_last": _r(diag.get("z_rmp_last")),
                "rc_lb_last": _r(diag.get("rc_lb_last")),
                "pricing_optimal_last": diag.get("pricing_optimal_last"),
                "best_lb": _r(lb),
                "visits": visits,
                "gap_to_lb_pct": gap,
                "n_stations": diag.get("n_stations"),
                "iterations": diag.get("iterations"),
                "n_exact_pricing": diag.get("n_exact_pricing"),
                "cg_deadline_s": _r(diag.get("cg_deadline_s"), 1),
                "cg_loop_elapsed_s": _r(diag.get("cg_loop_elapsed_s"), 1),
                "total_elapsed_s": _r(diag.get("total_elapsed_s"), 1),
                "n_orders": diag.get("n_orders"),
                "n_supports": diag.get("n_supports"),
                "budget_s": budget,
            }
            print(f"    -> converged={row['converged']} "
                  f"stop={row['stop_reason']} z_RMP={row['z_rmp_last']} "
                  f"rc_lb={row['rc_lb_last']} LB={row['best_lb']} "
                  f"visits={row['visits']}", flush=True)
        except Exception as exc:  # noqa: BLE001 -- record and keep going
            traceback.print_exc()
            row = {f: "" for f in FIELDS}
            row.update({"size_n": size, "instance_seed": iseed,
                        "status": f"FAIL:{type(exc).__name__}",
                        "budget_s": budget})

        append_row(row)
        collected.append(row)

    summarise(collected)
    print(f"\nWrote {RESULT_CSV}")


def _r(v: object, nd: int = 1) -> object:
    """Round a float for the CSV, passing anything else through."""
    return round(v, nd) if isinstance(v, float) else v


if __name__ == "__main__":
    main()
