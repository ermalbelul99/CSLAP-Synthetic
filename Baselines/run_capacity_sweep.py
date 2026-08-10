"""EXP-02c: does the community bound scale with STATION CAPACITY or with CATALOGUE SIZE?

Motivation
----------
EXP-02a (``run_exp02a_sensitivity.py``) established that of the heuristic's four
thresholds only the community bound beta moves the objective. It could not say
what beta should be indexed on, because its instances confound the two
candidates: the generator sets |S| = max(5, N//100), so zeta = floor(N/|S|) = 100
for every size at or above 500 SKUs, while beta = max(5, min(15, N//20))
saturates at 15 for every N >= 300. Over the whole reported family beta/zeta is
the constant 0.15.

The reviewer's open question - "MNOPPC independent of |S|" - is exactly this one.

Design
------
Instances (``make_capsweep_instances.py``): two catalogue sizes crossed with four
station counts, so the same zeta grid {100, 50, 25, 20} appears at both sizes,
with the order structure held identical across station counts at a fixed seed.

What the response actually looks like (measured before sizing the campaign)
--------------------------------------------------------------------------
A probe on syn_500sku_seed1001 (zeta=100) over beta in {5,15,30,50,100} returned
92,050 / 88,421 / 87,462 / 86,349 / 84,880 visits with the busiest station at
52,687 / 52,687 / 67,437 / 63,950 / 72,968 and 1 / 0 / 1 / 1 / 2 stations over
their cap. Visits fall MONOTONICALLY in beta all the way to beta = zeta, and
overload rises with it. This matches every point EXP-02a measured (halving beta
always cost visits, doubling it always saved them, at both 50 and 500 SKUs).

The community bound is therefore not a quality parameter with an interior
optimum. It is a pure exchange rate between station visits and workload
concentration, and an optimum exists only once feasibility is imposed. The
primary quantity of this experiment is consequently the FEASIBILITY FRONTIER

    beta_max(instance) = max { beta : max_overload_ratio <= 1 }

and the hypotheses are about what that frontier scales with:

H1 (capacity rule)  beta_max ~ zeta, i.e. beta_max/zeta constant across cells
H2 (catalogue rule) beta_max ~ N, i.e. beta_max constant within a catalogue size

Because the same zeta grid occurs at both catalogue sizes, the two make opposite
predictions on this family and one sweep separates them. Visits remain the
secondary response, reported at whatever beta each policy selects - never on its
own. ``analyze_capacity_sweep.py`` does the fitting; this file only measures.

Contract
--------
C0  beta sweeps an ABSOLUTE anchor grid, extended to beta <= zeta. A community
    larger than a station's slot capacity can never be placed whole, so beta >
    zeta only exercises the splitting branch. The grid is absolute rather than a
    multiplier of the nominal value precisely so that the alpha = beta/zeta
    collapse is testable rather than assumed, and it must REACH zeta in every
    cell: on a zeta=100 cell a grid stopping at 30 would sit entirely on the
    monotone part of the curve and could not locate the frontier at all.
    Runtime is flat in beta - the greedy expansion adds each product once, so its
    cost is ~ N x |pairs| regardless of the bound (measured: 22-33 s at N=500 and
    41-44 s at N=1000, across beta from 5 to 100) - so extending the grid upward
    is nearly free.
C1  Every other threshold stays at its nominal formula, and the pair-support
    ratio uses the corrected symmetric denominator (heuristic_synthetic's default
    ratio_denominator="max"). EXP-02c is a study of beta alone.
C2  Runs execute through ``run_exp02a_sensitivity.run_one``: a spawned child under
    a hard wall-clock cap with PYTHONHASHSEED pinned. That machinery is reused
    rather than reimplemented. The per-run CSV schema differs (cells are keyed by
    station count as well as size), so this file keeps its own small append /
    restart helper instead of contorting the EXP-02a module-level constants,
    which the cached EXP-02a campaign depends on.
C3  Feasibility is recorded as a CONTINUOUS response, max_overload_ratio =
    max_wl / T_s, beside the binary wl_broken counter. The workload cap is
    uniform across stations in this generator, so T_s is read once per instance
    from the stations CSV. Reporting delta-visits without it would rank beta
    settings on layouts the site cannot operate - the flaw this experiment exists
    to remove.
C4  Restartable and OneDrive-safe: one row appended the moment a run finishes;
    on restart, (size_n, n_stations, instance_seed, config_id, hash_seed) keys
    already present are skipped. No file is ever rewritten in place.
    Parallelism is by SHARD, not by thread pool: --shard i --num-shards K
    partitions whole instances and writes capsweep_shard{i}.csv, so concurrent
    workers never append to the same file and no locking is needed. The analysis
    reads every shard. Instances are dealt round-robin after sorting, so each
    shard gets a mix of sizes and cells and they finish at similar times.
C5  The tuning/test split is recorded per row but NEVER acted on here. Splitting
    at analysis time keeps the measurement identical for both halves.

Outputs (under --out-dir)
-------------------------
capsweep.csv        one row per (instance, beta, hash seed); append-only.

Reproduce
---------
cd CSLAP-Synthetic
python Baselines/make_capsweep_instances.py
python Baselines/run_capacity_sweep.py --dry-run
for i in 0 1 2 3 4; do
    python Baselines/run_capacity_sweep.py --shard $i --num-shards 5 &
done; wait
python Baselines/analyze_capacity_sweep.py
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

# C2: the spawn/timeout/hash-seed machinery is imported, not copied.
from run_exp02a_sensitivity import base_params, run_one, time_cap  # noqa: E402

_COLS: Tuple[str, ...] = (
    "size_n", "n_stations", "zeta", "instance_seed", "split",
    "config_id", "beta", "alpha", "hash_seed",
    "min_freq_preproc", "min_freq", "ratio_to_keep", "mnoppc",
    "visits", "time_s", "cap_broken", "wl_broken",
    "max_wl", "time_capacity", "max_overload_ratio",
    "n_pstar", "n_pairs_kept", "n_corr_communities", "n_assigned",
    "community_size_max", "status",
)

# C0: absolute beta anchors, clipped per instance to beta <= zeta. Denser between
# 10 and 30, where the nominal bound of 15 sits and where the frontier fell in the
# probe, and reaching 100 so the zeta=100 cells are swept to their own capacity.
_BETA_ANCHORS: Tuple[int, ...] = (
    2, 3, 5, 8, 10, 12, 15, 18, 20, 25, 30, 40, 50, 75, 100,
)

# The nominal bound of the published heuristic at every size in this family
# (max(5, min(15, N//20)) with N >= 500), kept explicit because the analysis
# reports it as the incumbent policy.
_NOMINAL_BETA: int = 15

# Seeds 2001-2005 tune, 2006-2010 test (C5).
_TUNING_SEEDS: frozenset = frozenset(range(2001, 2006))

# Extra tie-break seeds for the nominal bound, on two contrasting zeta cells.
_NOISE_SEEDS: Tuple[int, ...] = (1, 2)
_NOISE_CELLS: Tuple[Tuple[int, int], ...] = ((500, 5), (500, 25))

_INST_RE = re.compile(r"^syn_(\d+)sku_s(\d+)_seed(\d+)$")


def split_of(instance_seed: int) -> str:
    return "tuning" if instance_seed in _TUNING_SEEDS else "test"


def beta_grid(zeta: int) -> List[int]:
    """The beta levels exercised on an instance of slot capacity zeta (C0).

    Always includes zeta itself, so alpha = beta/zeta spans up to 1.0 in every
    cell and the four cells share a common alpha range.
    """
    return sorted({b for b in _BETA_ANCHORS if b <= zeta} | {int(zeta)})


def effective_params(size_n: int, beta: int, zeta: int) -> Dict[str, Any]:
    """Nominal thresholds with the community bound replaced by beta (C1).

    `zeta` only sets the nominal community bound, which this function then
    overwrites with `beta`; it is threaded through so the three filter
    thresholds still come from one shared definition.
    """
    params = base_params(size_n, zeta)
    params["mnoppc"] = int(beta)
    return params


# --------------------------------------------------------------------------- #
#  INSTANCE DISCOVERY                                                         #
# --------------------------------------------------------------------------- #
def discover_instances(
    instance_dir: str, sizes: Optional[Sequence[int]] = None,
) -> List[Dict[str, Any]]:
    """Find the EXP-02c instances, reading zeta and T_s from each stations CSV."""
    out: List[Dict[str, Any]] = []
    if not os.path.isdir(instance_dir):
        return out
    for name in sorted(os.listdir(instance_dir)):
        m = _INST_RE.match(name)
        if not m:
            continue
        size_n, n_stations, seed = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if sizes is not None and size_n not in sizes:
            continue
        inst_dir = os.path.join(instance_dir, name)
        prefix = f"syn_{size_n}sku"
        csvs = {k: os.path.join(inst_dir, f"{prefix}_{k}.csv")
                for k in ("orders", "stations", "products")}
        if not all(os.path.exists(p) for p in csvs.values()):
            print(f"[warn] {name}: missing CSV(s) -> skipped", file=sys.stderr)
            continue
        st = pd.read_csv(csvs["stations"], sep=";")
        # C3: uniform caps by construction; assert rather than assume.
        if st["TIME_CAPACITY"].nunique() != 1 or st["CAPACITY"].nunique() != 1:
            print(f"[warn] {name}: non-uniform station caps -> skipped", file=sys.stderr)
            continue
        out.append({
            "size_n": size_n, "n_stations": n_stations, "instance_seed": seed,
            "inst_dir": inst_dir, "prefix": prefix,
            "zeta": int(st["CAPACITY"].iloc[0]),
            "time_capacity": float(st["TIME_CAPACITY"].iloc[0]),
        })
    out.sort(key=lambda d: (d["size_n"], d["n_stations"], d["instance_seed"]))
    return out


# --------------------------------------------------------------------------- #
#  PER-RUN CSV (restartable append, C4)                                       #
# --------------------------------------------------------------------------- #
def _results_path(out_dir: str, shard: Optional[int] = None) -> str:
    if shard is None:
        return os.path.join(out_dir, "capsweep.csv")
    return os.path.join(out_dir, f"capsweep_shard{shard}.csv")


def load_done_keys(out_dir: str) -> set:
    """(size_n, n_stations, instance_seed, config_id, hash_seed) already recorded.

    Reads EVERY shard plus the unsharded file, so a restart with a different
    shard count still skips work that is already done.
    """
    import glob as _glob
    done: set = set()
    paths = [_results_path(out_dir)] + sorted(
        _glob.glob(os.path.join(out_dir, "capsweep_shard*.csv")))
    frames = []
    for path in paths:
        if not os.path.exists(path):
            continue
        try:
            frames.append(pd.read_csv(path))
        except Exception:  # noqa: BLE001 - corrupt/partial shard: re-run it
            continue
    if not frames:
        return done
    prev = pd.concat(frames, ignore_index=True)
    for _, row in prev.iterrows():
        try:
            done.add((int(row["size_n"]), int(row["n_stations"]),
                      int(row["instance_seed"]), str(row["config_id"]),
                      int(row["hash_seed"])))
        except (KeyError, ValueError, TypeError):
            continue
    return done


def append_row(out_dir: str, row: Dict[str, Any], shard: Optional[int] = None) -> None:
    """Append exactly one row, writing the header once (OneDrive-safe)."""
    path = _results_path(out_dir, shard)
    write_header = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(_COLS))
        if write_header:
            writer.writeheader()
        writer.writerow({c: row.get(c, "") for c in _COLS})


# --------------------------------------------------------------------------- #
#  PLAN + SWEEP                                                               #
# --------------------------------------------------------------------------- #
def plan_runs(instances: Sequence[Dict[str, Any]]) -> List[Tuple[Dict[str, Any], int, int]]:
    """[(instance, beta, hash_seed)] for the whole campaign."""
    runs: List[Tuple[Dict[str, Any], int, int]] = []
    for inst in instances:
        for beta in beta_grid(inst["zeta"]):
            runs.append((inst, beta, 0))
        cell = (inst["size_n"], inst["n_stations"])
        if cell in _NOISE_CELLS and _NOMINAL_BETA <= inst["zeta"]:
            for hs in _NOISE_SEEDS:
                runs.append((inst, _NOMINAL_BETA, hs))
    return runs


def sweep(instances: Sequence[Dict[str, Any]], out_dir: str, done_keys: set,
          shard: Optional[int] = None) -> None:
    runs = plan_runs(instances)
    total = len(runs)
    t0 = time.time()
    for idx, (inst, beta, hseed) in enumerate(runs, start=1):
        cid = f"beta{beta}"
        key = (inst["size_n"], inst["n_stations"], inst["instance_seed"], cid, hseed)
        if key in done_keys:
            print(f"[{idx}/{total}] skip N={inst['size_n']} S={inst['n_stations']} "
                  f"seed={inst['instance_seed']} {cid} h={hseed} (done)")
            continue
        params = effective_params(inst["size_n"], beta, inst["zeta"])
        cap_s = time_cap(inst["size_n"])
        print(f"[{idx}/{total}] N={inst['size_n']} S={inst['n_stations']} "
              f"zeta={inst['zeta']} seed={inst['instance_seed']} {cid} h={hseed} "
              f"(cap {cap_s:.0f}s)")
        w0 = time.time()
        status, metrics = run_one(inst["inst_dir"], inst["prefix"], params, cap_s, hseed)

        max_wl = float(metrics.get("max_wl", float("nan")))
        t_cap = inst["time_capacity"]
        overload = max_wl / t_cap if (np.isfinite(max_wl) and t_cap > 0) else float("nan")

        print(f"    -> {status} visits={metrics['visits']} "
              f"overload={overload:.3f} wall={time.time() - w0:.1f}s")

        row: Dict[str, Any] = {
            "size_n": inst["size_n"], "n_stations": inst["n_stations"],
            "zeta": inst["zeta"], "instance_seed": inst["instance_seed"],
            "split": split_of(inst["instance_seed"]),
            "config_id": cid, "beta": beta,
            "alpha": beta / inst["zeta"], "hash_seed": hseed,
            "min_freq_preproc": params["min_freq_preproc"],
            "min_freq": params["min_freq"],
            "ratio_to_keep": params["ratio_to_keep"],
            "mnoppc": params["mnoppc"],
            "time_capacity": t_cap,
            "max_overload_ratio": overload,
            "status": status,
        }
        row.update(metrics)
        append_row(out_dir, row, shard)
        done_keys.add(key)
    print(f"[done] sweep wall-clock {time.time() - t0:.1f}s -> "
          f"{_results_path(out_dir, shard)}")


# --------------------------------------------------------------------------- #
#  CLI / MAIN                                                                 #
# --------------------------------------------------------------------------- #
def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(
        description="EXP-02c: community-bound sweep across station capacities.")
    p.add_argument("--sizes", nargs="+", type=int, default=None)
    p.add_argument("--dry-run", action="store_true",
                   help="Print the campaign plan and exit (no runs).")
    p.add_argument("--out-dir", type=str, default="capsweep_results")
    p.add_argument("--instance-dir", type=str, default="capsweep_instances")
    p.add_argument("--shard", type=int, default=None,
                   help="This worker's index in [0, num_shards). Writes "
                        "capsweep_shard{i}.csv.")
    p.add_argument("--num-shards", type=int, default=1)
    args = p.parse_args(argv)

    instances = discover_instances(args.instance_dir, args.sizes)
    if not instances:
        print(f"[error] no instances under {args.instance_dir}; run "
              f"make_capsweep_instances.py first", file=sys.stderr)
        return 1

    if args.shard is not None:
        if not 0 <= args.shard < args.num_shards:
            raise ValueError(f"--shard must be in [0, {args.num_shards})")
        # Round-robin over the sorted list: every shard gets a mix of sizes and
        # cells, so the workers finish at comparable times.
        instances = instances[args.shard::args.num_shards]
        print(f"[shard {args.shard}/{args.num_shards}] {len(instances)} instances")

    runs = plan_runs(instances)
    if args.dry_run:
        print(f"[dry-run] {len(instances)} instances, {len(runs)} runs")
        seen = set()
        print(f"{'N':>6}{'|S|':>5}{'zeta':>6}  beta grid")
        print("-" * 46)
        for inst in instances:
            key = (inst["size_n"], inst["n_stations"])
            if key in seen:
                continue
            seen.add(key)
            print(f"{inst['size_n']:>6}{inst['n_stations']:>5}{inst['zeta']:>6}  "
                  f"{beta_grid(inst['zeta'])}")
        n_tune = sum(1 for i in instances if split_of(i["instance_seed"]) == "tuning")
        print(f"\nsplit: {n_tune} tuning / {len(instances) - n_tune} test instances")
        return 0

    os.makedirs(args.out_dir, exist_ok=True)
    done_keys = load_done_keys(args.out_dir)
    if done_keys:
        print(f"[restart] {len(done_keys)} rows present -> will skip them.")
    print(f"[plan] {len(instances)} instances -> {len(runs)} runs")
    sweep(instances, args.out_dir, done_keys, args.shard)
    return 0


if __name__ == "__main__":
    sys.exit(main())
