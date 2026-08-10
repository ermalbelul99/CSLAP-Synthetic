"""EXP-02a-S: threshold-sensitivity sweep of the CSLAP clustering heuristic.

The heuristic (``heuristic_synthetic.heuristic_cslap``) hard-codes four
auto-scaled thresholds that were never justified empirically:

    MIN_FREQ_PREPROC = max(2, N // 100)     product frequency floor  (P*)
    MIN_FREQ         = max(2, N // 50)      pair co-occurrence floor
    RATIO_TO_KEEP    = 0.1                  pair support ratio floor
    MNOPPC           = max(5, min(15, N//20))  community size limit

This runner perturbs them ONE AT A TIME (plus two corners) over the 29 retained
EXP-02a instances and records both the objective (visits) and the STRUCTURAL
diagnostics of the pipeline (|P*|, kept pairs, correlated communities, assigned
products, largest community), so the write-up can state whether the reported
heuristic numbers are an artefact of an arbitrary threshold choice.

Design contract (the load-bearing decisions)
--------------------------------------------
S0  The baseline is NOT re-tuned. ``heuristic_cslap`` gained keyword-only
    overrides that default to None => the historical formulas => the `base`
    config here is bit-for-bit the cached EXP-02a "Heuristic" row (Gate 0).
S1  Multipliers {0.5, 0.75, 1.5, 2.0} apply to the POST-CLAMP EFFECTIVE base
    value of the instance size (compute max(2, N//100) etc. FIRST, then scale),
    rounded with Python's round() (half-to-even), floored at 1 for the two
    frequency thresholds and at 2 for MNOPPC (MNOPPC also drives
    ``range(step=MNOPPC)``, so it must stay >= 1; 2 keeps a community meaningful).
    RATIO_TO_KEEP is a ratio, not a count: it uses the DIRECT values
    {0.05, 0.075, 0.15, 0.2} under the same x0.5/x0.75/x1.5/x2 labels.
S2  Hard per-size wall-clock caps (BINDING, user directive): 120 s (N=50),
    300 s (N=500), 600 s (N=1000), 1200 s (N=2000). Loose configs blow up the
    O(|pairs|^2)-ish greedy expansion, so a run MUST be killable. Every run
    therefore executes in a CHILD PROCESS created with the multiprocessing
    "spawn" context (the only Windows-safe context) and is killed on expiry.
    Chosen over a subprocess+temp-JSON worker because it needs no temp files at
    all -- this tree is OneDrive-synced, and a JSON file per run would be 551
    sync events. The child loads the instance CSVs itself (only a small metrics
    dict crosses the queue, never the order dictionaries).
S3  Feasibility of the RESULT is read exactly as run_exp02a_multiseed reads it:
    the cap_broken / wl_broken counters returned by heuristic_cslap itself,
    i.e. per-station |products| > CAPACITY and workload > TIME_CAPACITY (the
    T_s the instance CSVs define). No re-implementation, no second convention.
S4  Statuses refine, not replace, success: PARTIAL_ASSIGN (n_assigned < N) and
    DEGENERATE (n_pairs_kept == 0) rows STILL carry their metrics; they are
    warnings about how to read those metrics. PARTIAL_ASSIGN wins when both
    hold, because losing products invalidates the visit count (DEGENERATE stays
    recoverable from the n_pairs_kept column). TIMEOUT/ERROR carry NaN metrics.
S5  Restartable + OneDrive-safe: one row is appended the moment a run finishes;
    on restart the (size_n, instance_seed, config_id) keys already present are
    skipped. No file is ever rewritten in place.

Outputs (under --out-dir)
-------------------------
exp02a_sensitivity.csv      one row per (instance, config); append-only.
exp02a_sensitivity_agg.csv  one row per (config_id, size_n); written by
                            --aggregate. pct_delta_visits_vs_base is PAIRED per
                            instance against the base row of the SAME instance.

Reproduce
---------
cd CSLAP-Synthetic
python Baselines/run_exp02a_sensitivity.py --dry-run          # show the grid
python Baselines/run_exp02a_sensitivity.py --configs base     # Gate 0
python Baselines/run_exp02a_sensitivity.py                    # full sweep
python Baselines/run_exp02a_sensitivity.py --aggregate
"""

from __future__ import annotations

import argparse
import csv
import multiprocessing as mp
import os
import queue as _queue
import re
import sys
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

# NOTE: scipy is imported INSIDE _t_ci, not here. Every run spawns a child that
# re-imports this module; scipy is needed only by --aggregate, so keeping it out
# of module scope saves ~1-2 s of import time on each of the 551 child processes.

# --------------------------------------------------------------------------- #
#  PATH WIRING (same convention as run_exp02a_multiseed)                      #
# --------------------------------------------------------------------------- #
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))                  # Baselines/
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

# ONLY the heuristic is imported: milp_synthetic is deliberately NOT imported
# here (it installs the Hexaly license as an import side effect and would be
# re-executed in every spawned child).
import heuristic_synthetic  # noqa: E402

# Per-run CSV columns (order is contractual).
_COLS: Tuple[str, ...] = (
    "size_n", "instance_seed", "config_id", "hash_seed",
    "min_freq_preproc", "min_freq", "ratio_to_keep", "mnoppc",
    "visits", "time_s", "cap_broken", "wl_broken",
    "n_pstar", "n_pairs_kept", "n_corr_communities", "n_assigned",
    "community_size_max", "status",
)

# The heuristic groups products through Python sets keyed by product identifiers,
# so its greedy tie-breaks follow set iteration order, which CPython randomises
# per process unless PYTHONHASHSEED is fixed. Measured on syn_50sku_seed1004,
# unseeded repeats of one identical run return 6,643 / 6,622 / 6,622 visits,
# while PYTHONHASHSEED=0 returns 6,622 every time. Every run therefore pins the
# seed: threshold effects are compared at a fixed tie-break order, and repeating
# the base configuration across seeds measures the tie-break noise itself.
_DEFAULT_HASH_SEED: int = 0

# S2: hard per-size wall-clock caps in seconds (BINDING).
_TIME_CAPS: Dict[int, float] = {50: 120.0, 500: 300.0, 1000: 600.0, 2000: 1200.0}
_TIME_CAP_FALLBACK: float = 1200.0

# S1: the four perturbation levels and their config-id labels.
_MULTS: Tuple[Tuple[float, str], ...] = (
    (0.5, "x0.5"), (0.75, "x0.75"), (1.5, "x1.5"), (2.0, "x2"),
)
# RATIO_TO_KEEP is a ratio: direct values, same labels.
_RATIO_VALUES: Dict[str, float] = {
    "x0.5": 0.05, "x0.75": 0.075, "x1.5": 0.15, "x2": 0.2,
}
_MULT_BY_LABEL: Dict[str, float] = {lab: m for m, lab in _MULTS}
_FAMILIES: Tuple[str, ...] = ("preproc", "minfreq", "ratio", "mnoppc")
# Threshold key touched by each one-at-a-time family.
_FAMILY_KEY: Dict[str, str] = {
    "preproc": "min_freq_preproc", "minfreq": "min_freq",
    "ratio": "ratio_to_keep", "mnoppc": "mnoppc",
}

_INST_RE = re.compile(r"^syn_(\d+)sku_seed(\d+)$")


def all_config_ids() -> List[str]:
    """The 19 configs: base + 16 one-at-a-time + 2 corners (order is stable)."""
    ids: List[str] = ["base"]
    for fam in _FAMILIES:
        ids.extend(f"{fam}_{lab}" for _m, lab in _MULTS)
    ids.extend(["corner_loose", "corner_tight"])
    return ids


# --------------------------------------------------------------------------- #
#  CONFIG GRID                                                                #
# --------------------------------------------------------------------------- #
def base_params(size_n: int) -> Dict[str, Any]:
    """The POST-CLAMP effective base thresholds for an instance of N SKUs.

    Mirrors heuristic_synthetic.heuristic_cslap exactly; multipliers are applied
    to THESE values (S1), never to the unclamped N//k expressions.
    """
    return {
        "min_freq_preproc": max(2, size_n // 100),
        "min_freq": max(2, size_n // 50),
        "ratio_to_keep": 0.1,
        "mnoppc": max(5, min(15, size_n // 20)),
    }


def _scale_count(base_value: int, mult: float, floor: int) -> int:
    """Scale an integer threshold: round() then clamp to `floor` (S1)."""
    return int(max(floor, int(round(base_value * mult))))


def _apply(params: Dict[str, Any], key: str, label: str, mult: float) -> None:
    """Perturb ONE threshold in place, scaling its post-clamp base value (S1)."""
    if key == "ratio_to_keep":
        params[key] = _RATIO_VALUES[label]          # direct value, not a scale
    else:
        floor = 2 if key == "mnoppc" else 1
        params[key] = _scale_count(int(params[key]), mult, floor)


def effective_params(config_id: str, size_n: int) -> Dict[str, Any]:
    """The four thresholds actually handed to the heuristic for this config."""
    params = base_params(size_n)
    if config_id == "base":
        return params
    if config_id in ("corner_loose", "corner_tight"):
        mult, label = (0.5, "x0.5") if config_id == "corner_loose" else (2.0, "x2")
        for key in ("min_freq_preproc", "min_freq", "mnoppc", "ratio_to_keep"):
            _apply(params, key, label, mult)
        return params
    family, _, label = config_id.rpartition("_")
    if family not in _FAMILY_KEY or label not in _MULT_BY_LABEL:
        raise ValueError(f"unknown config_id: {config_id}")
    _apply(params, _FAMILY_KEY[family], label, _MULT_BY_LABEL[label])
    return params


def print_dry_run(sizes: Sequence[int], config_ids: Sequence[str]) -> None:
    """Print the config grid per size WITHOUT running anything."""
    for size_n in sizes:
        print(f"\n=== N = {size_n} (cap {time_cap(size_n):.0f}s) ===")
        print(f"{'config_id':<16}{'min_freq_preproc':>18}{'min_freq':>10}"
              f"{'ratio_to_keep':>15}{'mnoppc':>8}")
        print("-" * 67)
        for cid in config_ids:
            p = effective_params(cid, size_n)
            print(f"{cid:<16}{p['min_freq_preproc']:>18d}{p['min_freq']:>10d}"
                  f"{p['ratio_to_keep']:>15g}{p['mnoppc']:>8d}")
    print()


def time_cap(size_n: int) -> float:
    """Hard wall-clock cap for one run at this size (S2)."""
    return _TIME_CAPS.get(size_n, _TIME_CAP_FALLBACK)


# --------------------------------------------------------------------------- #
#  INSTANCE DISCOVERY                                                         #
# --------------------------------------------------------------------------- #
def discover_instances(
    instance_dir: str, sizes: Optional[Sequence[int]] = None,
) -> List[Tuple[int, int, str, str]]:
    """Find the retained EXP-02a instances: [(size_n, seed, inst_dir, prefix)].

    An instance counts only when all three generator CSVs are present (the
    sweep never generates data: it reuses the EXACT instances the cached
    EXP-02a rows were computed on).
    """
    out: List[Tuple[int, int, str, str]] = []
    if not os.path.isdir(instance_dir):
        return out
    for name in sorted(os.listdir(instance_dir)):
        m = _INST_RE.match(name)
        if not m:
            continue
        size_n, seed = int(m.group(1)), int(m.group(2))
        if sizes is not None and size_n not in sizes:
            continue
        inst_dir = os.path.join(instance_dir, name)
        prefix = f"syn_{size_n}sku"
        csvs = [os.path.join(inst_dir, f"{prefix}_{k}.csv")
                for k in ("orders", "stations", "products")]
        if not all(os.path.exists(p) for p in csvs):
            print(f"[warn] {name}: missing CSV(s) -> skipped", file=sys.stderr)
            continue
        out.append((size_n, seed, inst_dir, prefix))
    out.sort(key=lambda t: (t[0], t[1]))
    return out


# --------------------------------------------------------------------------- #
#  CHILD-PROCESS RUNNER (S2)                                                  #
# --------------------------------------------------------------------------- #
def _child_entry(inst_dir: str, prefix: str, params: Dict[str, Any],
                 out_q: "mp.Queue") -> None:
    """Load the instance, run the heuristic once, push a small metrics dict.

    Runs in a spawned child so the parent can KILL it on the wall-clock cap.
    The instance is loaded HERE (not pickled across) to keep the queue payload
    tiny. Never raises across the process boundary: failures are reported as
    {"ok": False, "error": ...}.
    """
    try:
        op, st, pr, pl, odf = heuristic_synthetic.read_data(prefix, inst_dir)
        diag: Dict[str, Any] = {}
        # `params` is passed straight through as keyword arguments, so a caller
        # can drive any of the heuristic's knobs (placement rule, workload
        # tolerance, ...) without this module needing to know about them. The
        # four threshold keys this campaign uses are simply the default case.
        result = heuristic_synthetic.heuristic_cslap(
            op, st, pr, pl, odf, diag=diag, **params
        )
        # 7-tuple: (assignment, visits, elapsed, max_wl, wl_std, cap_b, wl_b)
        _assignment, visits, elapsed, _max_wl, _wl_std, cap_broken, wl_broken = result
        out_q.put({
            "ok": True,
            "visits": float(visits),
            "time_s": float(elapsed),
            "cap_broken": float(cap_broken),
            "wl_broken": float(wl_broken),
            # Busiest station's realised load. run_exp02a_sensitivity ignores it
            # (its metrics dict is built key by key); EXP-02c divides it by T_s to
            # get a CONTINUOUS overload response, so that a threshold's effect on
            # visits is never read without its effect on feasibility beside it.
            "max_wl": float(_max_wl),
            "n_products": int(len(pr)),
            # Whole diag travels: callers that record extra diagnostics (swap
            # counts, overload before/after) get them without this module having
            # to enumerate them. Non-numeric entries are dropped by run_one.
            "diag": dict(diag),
        })
    except Exception as exc:  # noqa: BLE001 - must never crash the campaign
        out_q.put({"ok": False, "error": f"{type(exc).__name__}: {exc}"})


def run_one(
    inst_dir: str, prefix: str, params: Dict[str, Any], cap_s: float,
    hash_seed: int = _DEFAULT_HASH_SEED,
) -> Tuple[str, Dict[str, Any]]:
    """Run one (instance, config) under a hard wall-clock cap.

    ``hash_seed`` is exported as PYTHONHASHSEED before the child is spawned. The
    spawn context launches a fresh interpreter that inherits this environment,
    so the child's set iteration order, and with it the heuristic's tie-breaking,
    is reproducible.

    Returns (status, metrics). status is OK / PARTIAL_ASSIGN / DEGENERATE
    (all three carry real metrics, S4) or TIMEOUT / ERROR (NaN metrics).
    """
    nan_metrics: Dict[str, Any] = {
        "visits": float("nan"), "time_s": float("nan"),
        "cap_broken": float("nan"), "wl_broken": float("nan"),
        "max_wl": float("nan"),
        "n_pstar": float("nan"), "n_pairs_kept": float("nan"),
        "n_corr_communities": float("nan"), "n_assigned": float("nan"),
        "community_size_max": float("nan"),
    }

    ctx = mp.get_context("spawn")          # Windows-safe context
    out_q: "mp.Queue" = ctx.Queue()
    prev_seed = os.environ.get("PYTHONHASHSEED")
    os.environ["PYTHONHASHSEED"] = str(int(hash_seed))
    try:
        proc = ctx.Process(target=_child_entry,
                           args=(inst_dir, prefix, params, out_q), daemon=True)
        proc.start()
    finally:
        if prev_seed is None:
            os.environ.pop("PYTHONHASHSEED", None)
        else:
            os.environ["PYTHONHASHSEED"] = prev_seed

    # Poll instead of a single blocking get(cap_s): a child that DIES without
    # delivering (MemoryError, hard kill) must not burn the whole cap and must
    # not be mislabelled TIMEOUT. Liveness is checked every 0.5 s.
    deadline = time.time() + cap_s
    payload: Optional[Dict[str, Any]] = None
    crashed = False
    try:
        while True:
            try:
                payload = out_q.get(timeout=0.5)
                break
            except _queue.Empty:
                pass
            if not proc.is_alive():
                # Exited: drain a late message (queue feeder race), else crash.
                try:
                    payload = out_q.get(timeout=1.0)
                except _queue.Empty:
                    crashed = True
                break
            if time.time() >= deadline:
                break
    finally:
        proc.join(timeout=5.0)
        if proc.is_alive():
            proc.terminate()
            proc.join(timeout=5.0)
        out_q.close()

    if payload is None:
        if crashed:
            print(f"  [ERROR] child died without a result "
                  f"(exitcode={proc.exitcode})", file=sys.stderr)
            return "ERROR", dict(nan_metrics)
        return "TIMEOUT", dict(nan_metrics)
    if not payload.get("ok", False):
        print(f"  [ERROR] {payload.get('error', 'unknown')}", file=sys.stderr)
        return "ERROR", dict(nan_metrics)

    diag = payload.get("diag", {}) or {}
    metrics: Dict[str, Any] = {
        "visits": payload["visits"], "time_s": payload["time_s"],
        "cap_broken": payload["cap_broken"], "wl_broken": payload["wl_broken"],
        # Not in this campaign's _COLS, so append_row drops it; EXP-02c reads it.
        "max_wl": float(payload.get("max_wl", float("nan"))),
    }
    for key in ("n_pstar", "n_pairs_kept", "n_corr_communities", "n_assigned",
                "community_size_max"):
        val = diag.get(key)
        metrics[key] = float("nan") if val is None else float(val)
    # Any further numeric diagnostics the heuristic reported (e.g. n_swaps,
    # n_overloaded_before/after). Keys already handled above are not overwritten.
    for key, val in diag.items():
        if key in metrics or isinstance(val, str):
            continue
        try:
            metrics[key] = float(val)
        except (TypeError, ValueError):
            continue

    # S4: refine OK. PARTIAL_ASSIGN first (it invalidates the visit count);
    # DEGENERATE stays recoverable from the n_pairs_kept column.
    n_products = float(payload.get("n_products", float("nan")))
    status = "OK"
    if np.isfinite(metrics["n_assigned"]) and np.isfinite(n_products) \
            and metrics["n_assigned"] < n_products:
        status = "PARTIAL_ASSIGN"
    elif metrics["n_pairs_kept"] == 0:
        status = "DEGENERATE"
    return status, metrics


# --------------------------------------------------------------------------- #
#  PER-RUN CSV (restartable append, S5)                                       #
# --------------------------------------------------------------------------- #
def _results_path(out_dir: str) -> str:
    return os.path.join(out_dir, "exp02a_sensitivity.csv")


def load_done_keys(out_dir: str) -> set:
    """Set of (size_n, instance_seed, config_id, hash_seed) already recorded."""
    path = _results_path(out_dir)
    done: set = set()
    if not os.path.exists(path):
        return done
    try:
        prev = pd.read_csv(path)
    except Exception:  # noqa: BLE001 - corrupt/partial file: re-run everything
        return done
    if "hash_seed" not in prev.columns:
        # Rows written before the tie-break seed was pinned are not comparable
        # with seeded rows; ignore them so the sweep regenerates cleanly.
        return done
    for _, row in prev.iterrows():
        try:
            done.add((int(row["size_n"]), int(row["instance_seed"]),
                      str(row["config_id"]), int(row["hash_seed"])))
        except (KeyError, ValueError, TypeError):
            continue
    return done


def append_row(out_dir: str, row: Dict[str, Any]) -> None:
    """Append exactly one row, writing the header once (OneDrive-safe)."""
    path = _results_path(out_dir)
    write_header = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(_COLS))
        if write_header:
            writer.writeheader()
        writer.writerow({c: row.get(c, "") for c in _COLS})


# --------------------------------------------------------------------------- #
#  SWEEP                                                                      #
# --------------------------------------------------------------------------- #
def sweep(
    instances: Sequence[Tuple[int, int, str, str]],
    config_ids: Sequence[str],
    out_dir: str,
    done_keys: set,
    hash_seeds: Sequence[int] = (_DEFAULT_HASH_SEED,),
    noise_seeds: Sequence[int] = (),
) -> None:
    """Run every (instance, config, seed) not already recorded, appending as we go.

    Every configuration runs at each seed in ``hash_seeds``. ``noise_seeds`` adds
    extra repeats of the base configuration only; those repeats measure the
    tie-break noise floor against which a threshold effect has to be read.
    """
    plan: List[Tuple[str, int]] = [(cid, hs) for cid in config_ids
                                   for hs in hash_seeds]
    if "base" in config_ids:
        plan += [("base", hs) for hs in noise_seeds if hs not in hash_seeds]
    total = len(instances) * len(plan)
    idx = 0
    t0 = time.time()
    for size_n, seed, inst_dir, prefix in instances:
        cap_s = time_cap(size_n)
        for cid, hseed in plan:
            idx += 1
            key = (size_n, seed, cid, hseed)
            if key in done_keys:
                print(f"[{idx}/{total}] skip N={size_n} seed={seed} {cid} "
                      f"h={hseed} (done)")
                continue
            params = effective_params(cid, size_n)
            print(f"[{idx}/{total}] N={size_n} seed={seed} {cid} h={hseed} "
                  f"pre={params['min_freq_preproc']} mf={params['min_freq']} "
                  f"ratio={params['ratio_to_keep']:g} mn={params['mnoppc']} "
                  f"(cap {cap_s:.0f}s)")
            w0 = time.time()
            status, metrics = run_one(inst_dir, prefix, params, cap_s, hseed)
            print(f"    -> {status} visits={metrics['visits']} "
                  f"wall={time.time() - w0:.1f}s")
            row: Dict[str, Any] = {
                "size_n": size_n, "instance_seed": seed, "config_id": cid,
                "hash_seed": hseed,
                "min_freq_preproc": params["min_freq_preproc"],
                "min_freq": params["min_freq"],
                "ratio_to_keep": params["ratio_to_keep"],
                "mnoppc": params["mnoppc"],
                "status": status,
            }
            row.update(metrics)
            append_row(out_dir, row)
            done_keys.add(key)
    print(f"[done] sweep wall-clock {time.time() - t0:.1f}s -> "
          f"{_results_path(out_dir)}")


# --------------------------------------------------------------------------- #
#  AGGREGATION                                                                #
# --------------------------------------------------------------------------- #
def _t_ci(values: Sequence[float], conf: float = 0.95) -> Tuple[float, float, float, int]:
    """(mean, ci_lo, ci_hi, n) two-sided t-interval; NaN bounds when n < 2."""
    from scipy import stats  # local: keeps scipy out of the spawned children
    arr = np.asarray([v for v in values if np.isfinite(v)], dtype=float)
    n = int(arr.size)
    if n == 0:
        return float("nan"), float("nan"), float("nan"), 0
    mean = float(np.mean(arr))
    if n < 2:
        return mean, float("nan"), float("nan"), n
    std = float(np.std(arr, ddof=1))
    half = float(stats.t.ppf(0.5 + conf / 2.0, n - 1)) * std / np.sqrt(n)
    return mean, mean - half, mean + half, n


def aggregate(out_dir: str) -> pd.DataFrame:
    """Build exp02a_sensitivity_agg.csv: one row per (config_id, size_n).

    pct_delta_visits_vs_base is PAIRED: for each instance the config's visits
    are compared to the base-config visits of the SAME instance, and the mean
    (+/- 95% t-CI when at least 5 instances pair up) is reported. Unpaired
    instances (base or config missing/NaN) simply drop out of the delta.
    """
    path = _results_path(out_dir)
    if not os.path.exists(path):
        raise FileNotFoundError(f"no results to aggregate: {path}")
    df = pd.read_csv(path)
    df["visits"] = pd.to_numeric(df["visits"], errors="coerce")
    df["wl_broken"] = pd.to_numeric(df["wl_broken"], errors="coerce")
    df["n_pairs_kept"] = pd.to_numeric(df["n_pairs_kept"], errors="coerce")

    base = df[df["config_id"] == "base"]
    # Pair within the SAME tie-break seed: a config is compared to the base run
    # that shares its instance AND its hash seed, so a delta never mixes a
    # threshold effect with a change of set iteration order.
    base_visits: Dict[Tuple[int, int, int], float] = {}
    for _, r in base.iterrows():
        v = float(r["visits"])
        if np.isfinite(v) and v > 0:
            base_visits[(int(r["size_n"]), int(r["instance_seed"]),
                         int(r["hash_seed"]))] = v

    # Noise floor: per-instance spread of the base configuration across seeds,
    # expressed as a percentage of that instance's mean.
    noise: Dict[int, float] = {}
    for size_n, sub_b in base.groupby("size_n"):
        spreads = []
        for _seed, g in sub_b.groupby("instance_seed"):
            vals = g["visits"].to_numpy(dtype=float)
            vals = vals[np.isfinite(vals)]
            if vals.size >= 2 and vals.mean() > 0:
                spreads.append(100.0 * float(np.std(vals, ddof=1)) / float(vals.mean()))
        noise[int(size_n)] = float(np.mean(spreads)) if spreads else float("nan")

    rows: List[Dict[str, Any]] = []
    for (cid, size_n), sub in df.groupby(["config_id", "size_n"], sort=False):
        visits = sub["visits"].tolist()
        deltas: List[float] = []
        for _, r in sub.iterrows():
            b = base_visits.get((int(r["size_n"]), int(r["instance_seed"]),
                                 int(r["hash_seed"])))
            v = float(r["visits"])
            if b is not None and np.isfinite(v):
                deltas.append(100.0 * (v - b) / b)
        mean_visits, _, _, k_runs = _t_ci(visits)
        mean_d, lo, hi, k_paired = _t_ci(deltas)
        if k_paired < 5:  # CI only when it is informative
            lo = hi = float("nan")
        wlb = [w for w in sub["wl_broken"].tolist() if np.isfinite(w)]
        statuses = sub["status"].astype(str).tolist()
        rows.append({
            "config_id": cid,
            "size_n": int(size_n),
            "K": k_runs,
            "k_paired": k_paired,
            "mean_visits": mean_visits,
            "mean_pct_delta_visits_vs_base": mean_d,
            "pct_delta_ci95_lo": lo,
            "pct_delta_ci95_hi": hi,
            "ci_informative": bool(k_paired >= 5),
            "base_tiebreak_noise_pct": noise.get(int(size_n), float("nan")),
            "frac_instances_wl_broken": (
                float(np.mean([1.0 if w > 0 else 0.0 for w in wlb]))
                if wlb else float("nan")),
            "mean_n_pairs_kept": float(
                np.nanmean(sub["n_pairs_kept"].to_numpy(dtype=float)))
            if sub["n_pairs_kept"].notna().any() else float("nan"),
            "n_rows": int(len(sub)),
            "n_ok": statuses.count("OK"),
            "n_partial_assign": statuses.count("PARTIAL_ASSIGN"),
            "n_degenerate": statuses.count("DEGENERATE"),
            "n_timeout": statuses.count("TIMEOUT"),
            "n_error": statuses.count("ERROR"),
        })

    agg = pd.DataFrame(rows).sort_values(["size_n", "config_id"])
    out_path = os.path.join(out_dir, "exp02a_sensitivity_agg.csv")
    agg.to_csv(out_path, index=False)
    print(f"[agg] {len(agg)} rows -> {out_path}")
    return agg


# --------------------------------------------------------------------------- #
#  CLI / MAIN                                                                 #
# --------------------------------------------------------------------------- #
def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="EXP-02a-S: threshold-sensitivity sweep of the CSLAP "
                    "clustering heuristic over the retained EXP-02a instances.")
    p.add_argument("--sizes", nargs="+", type=int, default=None,
                   help="Restrict to these instance sizes (default: all found).")
    p.add_argument("--configs", nargs="+", type=str, default=None,
                   help="Restrict to these config ids (default: all 19).")
    p.add_argument("--dry-run", action="store_true",
                   help="Print the config grid per size and exit (no runs).")
    p.add_argument("--aggregate", action="store_true",
                   help="Aggregate the existing results CSV and exit.")
    p.add_argument("--hash-seeds", nargs="+", type=int, default=[0],
                   help="PYTHONHASHSEED value(s) every config runs under "
                        "(default: 0). Pins the heuristic's tie-breaking.")
    p.add_argument("--noise-seeds", nargs="+", type=int, default=[1, 2, 3, 4],
                   help="Extra seeds run for the BASE config only; they measure "
                        "the tie-break noise floor (default: 1 2 3 4).")
    p.add_argument("--out-dir", type=str, default="exp02a_results")
    p.add_argument("--instance-dir", type=str, default="exp02a_instances")
    return p.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    known = all_config_ids()
    config_ids = known if args.configs is None else list(args.configs)
    unknown = [c for c in config_ids if c not in known]
    if unknown:
        raise ValueError(f"unknown config id(s): {unknown}; known: {known}")

    if args.aggregate:
        aggregate(args.out_dir)
        return 0

    instances = discover_instances(args.instance_dir, args.sizes)
    if args.dry_run:
        sizes = args.sizes if args.sizes else sorted({i[0] for i in instances})
        if not sizes:
            sizes = sorted(_TIME_CAPS)
        print(f"[dry-run] {len(config_ids)} configs x {len(instances)} instances "
              f"= {len(config_ids) * len(instances)} runs")
        print_dry_run(sizes, config_ids)
        return 0

    if not instances:
        print(f"[error] no instances under {args.instance_dir}", file=sys.stderr)
        return 1
    os.makedirs(args.out_dir, exist_ok=True)

    done_keys = load_done_keys(args.out_dir)
    if done_keys:
        print(f"[restart] {len(done_keys)} (size,seed,config) rows present "
              f"-> will skip them.")
    print(f"[plan] {len(instances)} instances x {len(config_ids)} configs "
          f"= {len(instances) * len(config_ids)} runs")

    sweep(instances, config_ids, args.out_dir, done_keys,
          hash_seeds=args.hash_seeds, noise_seeds=args.noise_seeds)
    return 0


if __name__ == "__main__":
    sys.exit(main())
