"""Industrial probe: does the community bound's clamp at 15 cost visits on the real site?

Why
---
EXP-02c, re-run on the repaired B4ter heuristic, found the community bound has
an interior optimum tracking the station slot capacity, beta* ~ 0.4-0.6 * zeta,
with corr(beta*, zeta) = 0.947 against corr(beta*, N) = -0.085.

The published Table 6 heuristic row ran at beta = 15 -- the clamp in
beta = max(5, min(15, N//20)) -- and `community_size_max` in
results_industrial_heuristic_final.csv confirms 15 was binding. This site's
per-station slot capacity is mean 897 / median 242 (min 2, max 6374), so
beta/zeta sits around 0.02-0.06, one to two orders of magnitude below the band
that was optimal on the synthetic geometries.

THE TESTED RANGE WAS zeta IN [20, 100]. Every beta here is an extrapolation
well beyond it and must be reported as a probe, not as a calibrated setting.
The point is to find out whether the effect is worth pursuing at all, not to
claim a tuned value.

What it does
------------
Calls run_industrial_heuristic_alone.py once per beta, each writing its own
--out and --per-station-out so nothing touches the published artifacts. beta=15
is included as a regression gate: it must reproduce
results_industrial_heuristic_final.csv (1,050,514 visits) exactly.

Usage
-----
    python run_industrial_beta_probe.py --dry-run
    python run_industrial_beta_probe.py
    python run_industrial_beta_probe.py --betas 15 100 250 350 500
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from typing import List, Optional, Sequence

import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(BASE_DIR, "industrial_beta_probe")
PUBLISHED = os.path.join(BASE_DIR, "results_industrial_heuristic_final.csv")
_DEFAULT_BETAS = (15, 100, 250, 350)


def run_one(beta: int, log_dir: str) -> int:
    out = os.path.join("industrial_beta_probe", f"beta{beta}.csv")
    ps = os.path.join("industrial_beta_probe", f"beta{beta}_per_station.csv")
    log = os.path.join(log_dir, f"industrial_beta{beta}.log")
    cmd = [
        sys.executable, "run_industrial_heuristic_alone.py",
        "--mnoppc", str(beta),
        "--out", out,
        "--per-station-out", ps,
    ]
    print(f"[run] beta={beta}  -> {out}", flush=True)
    t0 = time.time()
    with open(log, "w", encoding="utf-8") as fh:
        rc = subprocess.call(cmd, cwd=BASE_DIR, stdout=fh, stderr=subprocess.STDOUT)
    print(f"      rc={rc}  wall={time.time() - t0:.0f}s  log={log}", flush=True)
    return rc


def report(betas: Sequence[int]) -> int:
    rows = []
    for b in betas:
        p = os.path.join(OUT_DIR, f"beta{b}.csv")
        if not os.path.isfile(p):
            continue
        r = pd.read_csv(p).iloc[0].to_dict()
        r["beta"] = b
        rows.append(r)
    if not rows:
        print("no probe results found", file=sys.stderr)
        return 2

    df = pd.DataFrame(rows).sort_values("beta")
    base = df[df.beta == 15]
    ref = float(base.visits.iloc[0]) if len(base) else float(df.visits.iloc[0])

    print("\n" + "=" * 86)
    print("Industrial heuristic vs the community bound (published row ran at beta=15)")
    print("=" * 86)
    print(f"{'beta':>6}{'visits':>14}{'vs beta=15':>12}{'max WL':>12}"
          f"{'util SD':>10}{'comm max':>10}{'time s':>9}")
    print("-" * 86)
    for _, r in df.iterrows():
        d = 100.0 * (r.visits - ref) / ref
        print(f"{int(r.beta):>6}{r.visits:>14,.0f}{d:>+11.2f}%"
              f"{r.max_workload:>12,.0f}{r.utilization_std_dev:>10.2f}"
              f"{int(r.community_size_max):>10}{r.time:>9.0f}")

    if os.path.isfile(PUBLISHED) and len(base):
        pub = float(pd.read_csv(PUBLISHED).visits.iloc[0])
        got = float(base.visits.iloc[0])
        ok = abs(pub - got) < 0.5
        print(f"\n[gate] beta=15 vs published {pub:,.0f}: got {got:,.0f} -> "
              f"{'MATCH' if ok else 'MISMATCH -- probe is not comparable'}")
        if not ok:
            return 1

    print("\nNegative = fewer visits than the published setting.")
    print("Feasibility is judged per station against the site's +10% tolerance:")
    print("  python Baselines/report_industrial_deviation.py --tolerance 0.10")
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--betas", nargs="+", type=int, default=list(_DEFAULT_BETAS))
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--report", action="store_true")
    args = p.parse_args(argv)

    betas: List[int] = sorted(set(args.betas))
    if args.report:
        return report(betas)

    print(f"betas: {betas}")
    print(f"out  : {OUT_DIR}")
    print("each run reloads the 77 MB order file and takes ~5-6 min "
          f"-> ~{6 * len(betas)} min total\n")
    if args.dry_run:
        return 0

    os.makedirs(OUT_DIR, exist_ok=True)
    log_dir = os.path.join(BASE_DIR, "logs")
    os.makedirs(log_dir, exist_ok=True)

    for b in betas:
        if run_one(b, log_dir) != 0:
            print(f"[abort] beta={b} failed; see its log", file=sys.stderr)
            return 1
    return report(betas)


if __name__ == "__main__":
    raise SystemExit(main())
