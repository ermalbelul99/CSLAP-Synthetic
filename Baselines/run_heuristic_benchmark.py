"""Benchmark the clustering heuristic over the 29 EXP-02a instances.

Runs the heuristic under each Step-4 placement rule and records, per instance,
the visit count together with the feasibility it was obtained at. Its two jobs:

  1. Select the placement rule. The decision order is feasibility first
     (a layout that breaks the workload cap is not a candidate at any visit
     count), mean visit gap second.
  2. Produce the Table 5 heuristic rows for the selected rule, paired against the
     set-variable reference in
     exp02a_results/final_formulation_analysis_perinstance.csv, which is the
     artifact that reproduces the published Gap column exactly.

Reuses the spawned-child + wall-clock cap + PYTHONHASHSEED pinning machinery of
run_exp02a_sensitivity (`run_one`), so tie-breaks are reproducible and a
pathological configuration can never hang the campaign.

Reproduce
---------
cd CSLAP-Synthetic
python Baselines/run_heuristic_benchmark.py --dry-run
python Baselines/run_heuristic_benchmark.py
python Baselines/run_heuristic_benchmark.py --report
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from typing import Any, Dict, List, Optional, Sequence

import numpy as np
import pandas as pd

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from run_exp02a_sensitivity import discover_instances, run_one, time_cap  # noqa: E402

_MODES: Dict[str, Dict[str, Any]] = {
    "balance":    {"placement": "balance", "repair": True},
    "preference": {"placement": "preference", "repair": True},
    # Diagnostic only: what workload-aware placement leaves for the repair to do.
    "balance_norepair":    {"placement": "balance", "repair": False},
    "preference_norepair": {"placement": "preference", "repair": False},
}
_DEFAULT_MODES = ("balance", "preference")

_COLS = (
    "size_n", "instance_seed", "mode", "placement", "repair", "hash_seed",
    "visits", "time_s", "cap_broken", "wl_broken", "max_wl",
    "n_assigned", "n_pstar", "n_pairs_kept", "n_corr_communities",
    "community_size_max", "n_swaps", "n_overloaded_before", "n_overloaded_after",
    "status",
)

_REF = os.path.join(os.path.dirname(_THIS_DIR), "exp02a_results",
                    "final_formulation_analysis_perinstance.csv")


def _results_path(out_dir: str) -> str:
    return os.path.join(out_dir, "heuristic_benchmark.csv")


def load_done(out_dir: str) -> set:
    path = _results_path(out_dir)
    if not os.path.exists(path):
        return set()
    try:
        prev = pd.read_csv(path)
    except Exception:  # noqa: BLE001
        return set()
    return {(int(r["size_n"]), int(r["instance_seed"]), str(r["mode"]))
            for _, r in prev.iterrows()}


def append_row(out_dir: str, row: Dict[str, Any]) -> None:
    path = _results_path(out_dir)
    write_header = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(_COLS))
        if write_header:
            w.writeheader()
        w.writerow({c: row.get(c, "") for c in _COLS})


def report(out_dir: str) -> None:
    """Rule selection table + the Table 5 rows for whichever rule wins."""
    df = pd.read_csv(_results_path(out_dir))
    df = df[df["status"] == "OK"]
    for c in ("visits", "wl_broken", "cap_broken", "n_swaps", "time_s"):
        df[c] = pd.to_numeric(df[c], errors="coerce")

    print("=== rule selection (feasibility first, then visits) ===")
    rows = []
    for mode, g in df.groupby("mode"):
        rows.append({
            "mode": mode,
            "instances": len(g),
            "pct_feasible": 100.0 * float(((g.wl_broken == 0) & (g.cap_broken == 0)).mean()),
            "mean_swaps": float(g.n_swaps.mean()),
            "mean_time_s": float(g.time_s.mean()),
        })
    sel = pd.DataFrame(rows).sort_values("mode")
    print(sel.to_string(index=False))

    if not os.path.exists(_REF):
        print(f"\n[warn] reference {_REF} missing; Table 5 rows skipped")
        return
    ref = (pd.read_csv(_REF)[["size_n", "instance_seed", "setvar"]]
           .dropna().drop_duplicates(["size_n", "instance_seed"]))

    from scipy import stats
    for mode in sorted(df["mode"].unique()):
        g = df[df["mode"] == mode].merge(ref, on=["size_n", "instance_seed"])
        if g.empty:
            continue
        print(f"\n=== Table 5 rows: mode={mode} ===")
        print(f"{'N':>6}{'K':>4}{'visits':>12}{'interval':>26}{'gap':>9}"
              f"{'WL viol':>9}{'time s':>8}{'swaps':>7}")
        for n, gg in g.groupby("size_n"):
            v = gg.visits.to_numpy(float)
            K = len(v)
            mu = v.mean()
            if n <= 1000 and K > 1:
                hw = stats.t.ppf(.975, K - 1) * v.std(ddof=1) / np.sqrt(K)
                lo, hi = mu - hw, mu + hw
            else:
                lo, hi = v.min(), v.max()
            gap = 100.0 * np.mean((gg.visits - gg.setvar) / gg.setvar)
            wl = 100.0 * float((gg.wl_broken > 0).mean())
            print(f"{n:>6}{K:>4}{mu:>12,.0f}"
                  f"{f'[{lo:,.0f}, {hi:,.0f}]':>26}{gap:>+8.1f}%"
                  f"{wl:>8.0f}%{gg.time_s.mean():>8.1f}{gg.n_swaps.mean():>7.1f}")


def main(argv: Optional[Sequence[str]] = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--instance-dir", type=str, default="exp02a_instances")
    p.add_argument("--out-dir", type=str, default="exp02a_results_repaired")
    p.add_argument("--sizes", nargs="+", type=int, default=None)
    p.add_argument("--modes", nargs="+", type=str, default=list(_DEFAULT_MODES))
    p.add_argument("--hash-seed", type=int, default=0)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--report", action="store_true")
    args = p.parse_args(argv)

    if args.report:
        report(args.out_dir)
        return 0

    bad = [m for m in args.modes if m not in _MODES]
    if bad:
        raise ValueError(f"unknown mode(s) {bad}; known: {sorted(_MODES)}")

    instances = discover_instances(args.instance_dir, args.sizes)
    if not instances:
        print(f"[error] no instances under {args.instance_dir}", file=sys.stderr)
        return 1
    if args.dry_run:
        print(f"[dry-run] {len(instances)} instances x {len(args.modes)} modes "
              f"= {len(instances) * len(args.modes)} runs")
        for m in args.modes:
            print(f"  {m}: {_MODES[m]}")
        return 0

    os.makedirs(args.out_dir, exist_ok=True)
    done = load_done(args.out_dir)
    total = len(instances) * len(args.modes)
    idx = 0
    for size_n, seed, inst_dir, prefix in instances:
        for mode in args.modes:
            idx += 1
            if (size_n, seed, mode) in done:
                print(f"[{idx}/{total}] skip N={size_n} seed={seed} {mode} (done)")
                continue
            params = dict(_MODES[mode])
            print(f"[{idx}/{total}] N={size_n} seed={seed} {mode}")
            status, m = run_one(inst_dir, prefix, params, time_cap(size_n),
                                args.hash_seed)
            print(f"    -> {status} visits={m['visits']} wl={m['wl_broken']} "
                  f"swaps={m.get('n_swaps')}")
            row = {
                "size_n": size_n, "instance_seed": seed, "mode": mode,
                "placement": params["placement"], "repair": params["repair"],
                "hash_seed": args.hash_seed, "status": status,
            }
            row.update(m)
            append_row(args.out_dir, row)
            done.add((size_n, seed, mode))
    print(f"[done] -> {_results_path(args.out_dir)}")
    report(args.out_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
