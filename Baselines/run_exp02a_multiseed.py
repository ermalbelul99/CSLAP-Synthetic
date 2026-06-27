"""EXP-02a: CSLAP multi-instance confidence intervals (REV 3 runner).

Replaces the single-run synthetic numbers in Chapter 3 Sec. 3.12 with
mean +/- 95% CI across multiple independently generated random CSLAP
instances per size. REV 1/2 ran the three license-free methods (GA, SA-C,
Heuristic). REV 3 ADDS the Hexaly set-variable MILP as a 4th method AND as the
per-instance AUTHORITATIVE reference (the golden CSLAP optimum).

This runner imports the Zhang generator and the four solvers directly and
DOES NOT modify any of them. Importing milp_synthetic also installs the Hexaly
license (its module-level side effect); milp_synthetic.py is left UNMODIFIED.

Design contract: c:/Users/ebelul/.../.claude/plans/run-experiment-exp02a.md
(REV 3 ADDENDUM + "REV 3 GAP FIXES" F0-F6).

REV 3 design notes (the load-bearing decisions)
-----------------------------------------------
F0  4th method = milp_synthetic.run_milp_hexaly (set decision variables: one
    model.set per station + model.partition + count<=cap + workload<=time_cap).
    Called as-is: no warm start, time_limit=tl, verbosity=0. R_Hexaly=1,
    solver_seed=-1, solver_probe=False.
F1  Hexaly's returned total_visits is a BOUND when OPTIMAL (milp_synthetic l.129),
    so the runner RECOMPUTES the reference visits from the returned assignment
    dict using the SAME order-station-visit formula as GA/SA/heur (see
    recompute_visits); a >1 mismatch vs the returned value is logged. The
    recomputed value is authoritative; the raw value is kept as audit only.
F2  run_milp_hexaly returns a len-9 tuple of Nones on infeasible/extract failure.
    The runner treats (visits None OR tuple-len != 7) as status=NO_SOLUTION with
    NaN metrics; such instances carry no Hexaly reference -> gaps are NaN there.
F3  Proven optimality is inferred from timing (Hexaly runs to its time_limit
    unless it proves optimality early): hexaly_optimal_inferred = elapsed <
    0.95*time_limit. hexaly_elapsed_s is recorded.
F5  Per-instance REFERENCE = Hexaly recomputed visits. rel_gap_to_hexaly =
    (visits - hexaly_ref)/hexaly_ref for every method; gap_label =
    optimality_gap if optimal-inferred else gap_to_best_feasible_budget. The
    Heuristic may show a NEGATIVE gap because it is workload-INFEASIBLE -- not an
    improvement; wl_broken is carried so the write-up flags it.
F6  INSTANCE REUSE (critical): the runner READS the RETAINED instance CSVs in
    exp02a_instances/syn_{N}sku_seed{s}/ and does NOT regenerate them when all
    three CSVs exist, so Hexaly solves the EXACT instances the cached GA/SA/heur
    rows used. Only missing instances are (re)generated (recorded regenerated=1).
N1  Each retained instance's three CSVs are sha256-hashed into hash_manifest_v3.txt
    at solve time; pairing of cached non-Hexaly rows to these files rests on the
    files being untouched since REV-2 (REV-2 stored no instance-data hash).

Key reported quantities
-----------------------
PRIMARY  : per (method x size) absolute mean visits +/- 95% t-interval, mean
           rel_gap_to_hexaly +/- CI (Hexaly's own ~0), and pairwise paired
           differences (Wilcoxon + paired-t), incl. Hexaly-vs-GA/SA-C/Heuristic.
SECONDARY: best_found(i) = min over {GA-main, SA, Heur, Hexaly} visits;
           rel_rank_pct (relative ranking, kept for REV-2 continuity).

Outputs (under --out-dir)
-------------------------
exp02a_per_instance.csv    : append-only base table; one row per (size,seed,
    method,solver_seed). REV-3 appends three Hexaly-only audit columns at the END
    (hexaly_returned_visits, hexaly_elapsed_s, hexaly_optimal_inferred); blank on
    non-Hexaly rows -> back-compatible with REV-2 rows.
exp02a_per_instance_v3.csv : JOINED view; every method row + the Hexaly-reference
    columns (hexaly_ref_visits, rel_gap_to_hexaly, gap_label) computed by joining
    on (size_n, instance_seed). CHOSEN over back-patching existing rows because a
    clean join keeps the append-only base file intact and is unambiguous.
exp02a_aggregated_v3.csv   : one row per (method x size); 4 methods x 4 sizes.
exp02a_pairwise_v3.csv     : one row per (size x pair); incl. Hexaly pairs.
hash_manifest.txt          : sha256 of the five reused sources + env versions.
hash_manifest_v3.txt       : sha256 of each retained instance's three CSVs (N1).

Restartability: per-instance rows are appended as they complete; on startup the
already-present (size, instance_seed, method, solver_seed) combos are skipped.
Because Hexaly rows are NEW keys (method="Hexaly"), a re-run over a directory
that already has GA/SA/heur rows executes ONLY the Hexaly solves. A fresh run
executes all four methods.

Reproduce
---------
cd CSLAP-Synthetic
python Baselines/run_exp02a_multiseed.py --sizes 50 500 1000 2000 \
  --k-per-size 12 10 4 3 --ga-seeds 20240612 \
  --ga-sideprobe-seeds 20240613 20240614 --sideprobe-size 50 --sideprobe-k 3 \
  --instance-seed-start 1001 --time-limits 120 300 600 900 --theta 0.7 \
  --out-dir exp02a_results --instance-dir exp02a_instances
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
import random
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

# --------------------------------------------------------------------------- #
#  PATH WIRING (compute from __file__; no run_benchmarks import)              #
# --------------------------------------------------------------------------- #
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))                  # Baselines/
_GEN_DIR = os.path.abspath(os.path.join(_THIS_DIR, "..", "Data_Generators"))

for _p in (_THIS_DIR, _GEN_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from synthetic_data_zhang import generate_synthetic_data_zhang  # noqa: E402
import ga_baseline  # noqa: E402
import sa_correlated  # noqa: E402
import heuristic_synthetic  # noqa: E402
# REV 3 (F0): Hexaly set-variable MILP -- the golden CSLAP method, added as a
# 4th method and the per-instance authoritative reference. Importing this module
# installs the Hexaly license (milp_synthetic.py line 14) as a side effect, so the
# import itself activates the solver; it is left UNMODIFIED.
import milp_synthetic  # noqa: E402

# Reused source files whose integrity we attest via sha256 (must stay unmodified).
# REV 3: milp_synthetic.py joins the attested set (it is reused, not modified).
_MANIFEST_FILES: Tuple[str, ...] = (
    os.path.join(_THIS_DIR, "ga_baseline.py"),
    os.path.join(_THIS_DIR, "sa_correlated.py"),
    os.path.join(_THIS_DIR, "heuristic_synthetic.py"),
    os.path.join(_THIS_DIR, "milp_synthetic.py"),
    os.path.join(_GEN_DIR, "synthetic_data_zhang.py"),
)

# Per-instance CSV columns (order is contractual).
# REV 3 appends, at the END (back-compatible read of REV-2 rows):
#   hexaly_returned_visits   : raw total_visits run_milp_hexaly returned (F1, audit only)
#   hexaly_elapsed_s         : Hexaly wall-clock for THIS instance solve (F3)
#   hexaly_optimal_inferred  : elapsed < 0.95*time_limit => proven-optimal early stop (F3)
# These are written on the Hexaly row only; non-Hexaly rows leave them blank.
_PER_INSTANCE_COLS: Tuple[str, ...] = (
    "size_n", "instance_seed", "method", "solver_seed", "solver_probe",
    "status", "visits", "time_s", "best_found_visits", "rel_rank_pct",
    "max_workload", "workload_std_dev", "cap_broken", "wl_broken",
    "num_orders", "num_itemsets", "num_skus", "num_stations",
    "hexaly_returned_visits", "hexaly_elapsed_s", "hexaly_optimal_inferred",
)

# REV 3 (M3): the existing license-free pairs PLUS Hexaly-vs-each-other-method.
# Hexaly is named first in each new pair so mean_diff = (Hexaly - other): GA/SA give
# POSITIVE diffs (they have more visits than the golden optimum); the heuristic can
# give a NEGATIVE diff because it is workload-INFEASIBLE (fewer visits is not better).
_PAIRS: Tuple[Tuple[str, str], ...] = (
    ("Heuristic", "SA-C"),
    ("Heuristic", "GA"),
    ("SA-C", "GA"),
    ("Hexaly", "GA"),
    ("Hexaly", "SA-C"),
    ("Hexaly", "Heuristic"),
)


# --------------------------------------------------------------------------- #
#  MANIFEST / ENVIRONMENT EVIDENCE                                            #
# --------------------------------------------------------------------------- #
def _sha256(path: str) -> str:
    """Return the hex sha256 of a file's bytes."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def write_hash_manifest(out_dir: str) -> None:
    """Write sha256 of the four reused sources + library versions + timestamp.

    Auto-evidence that the baselines and generator are unmodified
    (success criterion #4 of the plan).
    """
    os.makedirs(out_dir, exist_ok=True)
    lines: List[str] = []
    lines.append("# EXP-02a hash manifest (auto-evidence: reused sources unmodified)")
    lines.append(f"utc_timestamp = {datetime.now(timezone.utc).isoformat()}")
    lines.append(f"python = {sys.version.split()[0]}")
    lines.append(f"numpy = {np.__version__}")
    lines.append(f"pandas = {pd.__version__}")
    try:
        import scipy
        lines.append(f"scipy = {scipy.__version__}")
    except Exception:  # pragma: no cover - scipy is a hard dep here
        lines.append("scipy = UNKNOWN")
    lines.append("")
    lines.append("# sha256(file)")
    for path in _MANIFEST_FILES:
        try:
            digest = _sha256(path)
        except OSError as exc:
            digest = f"ERROR:{exc}"
        lines.append(f"{digest}  {os.path.basename(path)}")
    with open(os.path.join(out_dir, "hash_manifest.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


# --------------------------------------------------------------------------- #
#  REALIZED INSTANCE PARAMETERS                                               #
# --------------------------------------------------------------------------- #
def realized_params(
    df_orders: pd.DataFrame,
    df_stations: pd.DataFrame,
    size_n: int,
) -> Dict[str, float]:
    """Read realized (size-/seed-dependent) parameters from generator output.

    num_itemsets is a generation-internal latent that is NOT persisted to CSV
    by the generator, so it is reported as NaN (see module docstring / report).
    """
    return {
        "num_orders": float(df_orders["ORDER"].nunique()),
        "num_itemsets": float("nan"),  # not persisted by the generator
        "num_skus": float(size_n),
        "num_stations": float(len(df_stations)),
    }


# --------------------------------------------------------------------------- #
#  INSTANCE REUSE (F6) + INSTANCE-DATA HASHING (N1)                           #
# --------------------------------------------------------------------------- #
def _instance_csv_paths(inst_dir: str, prefix: str) -> Tuple[str, str, str]:
    """The three generator CSVs for a per-seed instance directory."""
    return (
        os.path.join(inst_dir, f"{prefix}_orders.csv"),
        os.path.join(inst_dir, f"{prefix}_stations.csv"),
        os.path.join(inst_dir, f"{prefix}_products.csv"),
    )


def ensure_instance(
    size_n: int, instance_seed: int, theta: float, instance_dir: str,
) -> Tuple[str, bool]:
    """Return the per-seed instance dir, REUSING retained CSVs when present (F6).

    CRITICAL (F6): for the Hexaly re-run the runner must solve the EXACT instances
    the cached GA/SA/heur rows were computed on. So if the per-seed dir already
    holds all three syn_{N}sku_{orders,stations,products}.csv files, we SKIP
    generation entirely and reuse them. We only call generate_synthetic_data_zhang
    when the dir or any of the three CSVs is missing.

    Returns (inst_dir, regenerated) where regenerated=True iff we (re)generated
    because files were absent.
    """
    prefix = f"syn_{size_n}sku"
    inst_dir = os.path.join(instance_dir, f"syn_{size_n}sku_seed{instance_seed}")
    os.makedirs(inst_dir, exist_ok=True)
    paths = _instance_csv_paths(inst_dir, prefix)

    if all(os.path.exists(p) for p in paths):
        # Reuse the retained instance verbatim -- no regeneration.
        return inst_dir, False

    # Missing -> generate deterministically from the seed (records regenerated).
    generate_synthetic_data_zhang(
        num_skus=size_n, theta=theta, seed=instance_seed, output_dir=inst_dir,
    )
    return inst_dir, True


def hash_instance_csvs(
    size_n: int, instance_seed: int, inst_dir: str,
) -> Dict[str, str]:
    """sha256 the three instance CSVs (N1: pairing-integrity evidence).

    REV-2 stored NO instance-data hash, so the soundness of pairing the cached
    GA/SA/heur rows to these files rests on the files being untouched since the
    REV-2 run. Hashing them now into hash_manifest_v3.txt makes any later drift
    detectable. Returns {basename: sha256-or-error}.
    """
    prefix = f"syn_{size_n}sku"
    out: Dict[str, str] = {}
    for p in _instance_csv_paths(inst_dir, prefix):
        try:
            out[os.path.basename(p)] = _sha256(p)
        except OSError as exc:
            out[os.path.basename(p)] = f"ERROR:{exc}"
    return out


def append_instance_hash_manifest(
    out_dir: str, size_n: int, instance_seed: int, inst_dir: str,
    regenerated: bool,
) -> None:
    """Append this instance's CSV hashes to hash_manifest_v3.txt (N1).

    Written incrementally so a partial run still leaves a usable manifest. The
    header is created on first write.
    """
    path = os.path.join(out_dir, "hash_manifest_v3.txt")
    write_header = not os.path.exists(path)
    digests = hash_instance_csvs(size_n, instance_seed, inst_dir)
    with open(path, "a", encoding="utf-8") as fh:
        if write_header:
            fh.write("# EXP-02a REV-3 instance-data hash manifest (N1).\n")
            fh.write("# Pairing of cached GA/SA/heur rows to these instances\n")
            fh.write("# rests on the files being UNTOUCHED since the REV-2 run\n")
            fh.write("# (REV-2 stored no instance-data hash). Columns:\n")
            fh.write("# size_n instance_seed regenerated basename sha256\n")
        for base, digest in digests.items():
            fh.write(f"{size_n} {instance_seed} {int(bool(regenerated))} "
                     f"{base} {digest}\n")


# --------------------------------------------------------------------------- #
#  SAFE SOLVER WRAPPER                                                        #
# --------------------------------------------------------------------------- #
def _safe_run(label: str, fn) -> Tuple[str, Dict[str, float]]:
    """Run a zero-arg callable returning a baseline 7-tuple; never raise.

    Returns (status, metrics). On failure status='ERROR' and all numeric
    metrics are NaN so the campaign continues.
    """
    nan_metrics: Dict[str, float] = {
        "visits": float("nan"), "time_s": float("nan"),
        "max_workload": float("nan"), "workload_std_dev": float("nan"),
        "cap_broken": float("nan"), "wl_broken": float("nan"),
    }
    try:
        result = fn()
        # 7-tuple: (state, visits, elapsed, max_wl, wl_std, cap_broken, wl_broken)
        _state, visits, elapsed, max_wl, wl_std, cap_broken, wl_broken = result
        return "OK", {
            "visits": float(visits),
            "time_s": float(elapsed),
            "max_workload": float(max_wl),
            "workload_std_dev": float(wl_std),
            "cap_broken": float(cap_broken),
            "wl_broken": float(wl_broken),
        }
    except Exception as exc:  # noqa: BLE001 - intentional broad catch per spec
        print(f"  [ERROR] {label} failed: {type(exc).__name__}: {exc}",
              file=sys.stderr)
        return "ERROR", nan_metrics


# --------------------------------------------------------------------------- #
#  HEXALY: AUTHORITATIVE VISIT RECOMPUTE (F1)                                 #
# --------------------------------------------------------------------------- #
def recompute_visits(
    assignment: Dict[str, Any], order_prods: Dict[Any, List[Any]]
) -> float:
    """Order-station visits from a product->station assignment (F1).

    Uses the EXACT formula the other methods use (ga_baseline.fitness and
    cg_synthetic.evaluate_assignment): for each order, count the DISTINCT
    stations among its products that are present in `assignment`, then sum
    over orders. Products not in `assignment` (unassigned / not modelled) are
    skipped, exactly as the baselines skip products absent from their state
    dict. This recomputed value -- not run_milp_hexaly's returned total_visits
    (which is a BOUND when OPTIMAL, milp_synthetic l.129) -- is the
    authoritative Hexaly reference.
    """
    total = 0
    for _o, prods in order_prods.items():
        visited = set()
        for p in prods:
            if p in assignment:
                visited.add(assignment[p])
        total += len(visited)
    return float(total)


# --------------------------------------------------------------------------- #
#  HEXALY: SAFE SOLVER WRAPPER (F0 + F2)                                      #
# --------------------------------------------------------------------------- #
def _safe_run_hexaly(
    label: str, fn, order_prods: Dict[Any, List[Any]], time_limit: float,
) -> Tuple[str, Dict[str, float], Dict[str, Any]]:
    """Run run_milp_hexaly (F0) and map it into the EXP-02a metric schema.

    run_milp_hexaly returns DIFFERENT shapes than GA/SA/heuristic:
      success  -> 7-tuple (assignment, total_visits, elapsed, max_wl, wl_std,
                  cap_broken, wl_broken)  -- note element[0] is the
                  product->station ASSIGNMENT, not a `state` placeholder.
      failure  -> 9-tuple of Nones (milp_synthetic l.159-163) on
                  infeasible / extraction error.

    F2: treat (returned visits is None) OR (tuple length != 7) as a clean
    NO_SOLUTION: NaN metrics, no reference, never raise. The instance then has
    no Hexaly reference -> gap columns are NaN for every method on it.

    F1: when feasible, RECOMPUTE visits from the returned assignment dict and
    use that as `visits`; keep the raw returned total_visits for the audit
    column and warn on a >1 discrepancy (bound-vs-incumbent symptom).

    F3: infer proven optimality from timing -- Hexaly runs to its time_limit
    unless it proves optimality and stops early.

    Returns (status, metrics, extra) where `extra` carries the audit/optimality
    fields written only on the Hexaly row.
    """
    nan_metrics: Dict[str, float] = {
        "visits": float("nan"), "time_s": float("nan"),
        "max_workload": float("nan"), "workload_std_dev": float("nan"),
        "cap_broken": float("nan"), "wl_broken": float("nan"),
    }
    nan_extra: Dict[str, Any] = {
        "hexaly_returned_visits": float("nan"),
        "hexaly_elapsed_s": float("nan"),
        "hexaly_optimal_inferred": "",
    }
    try:
        result = fn()
    except Exception as exc:  # noqa: BLE001 - intentional broad catch per spec
        print(f"  [ERROR] {label} raised: {type(exc).__name__}: {exc}",
              file=sys.stderr)
        return "ERROR", nan_metrics, nan_extra

    # F2: failure shapes -> NO_SOLUTION (len != 7, or visits-slot is None).
    if (not isinstance(result, tuple)) or len(result) != 7 or result[1] is None:
        print(f"  [NO_SOLUTION] {label}: Hexaly returned no feasible solution "
              f"(len={len(result) if isinstance(result, tuple) else 'n/a'}).",
              file=sys.stderr)
        # We still know roughly how long it ran if the failure tuple carried
        # elapsed in slot 2 (it does, len-9 path), purely for diagnostics.
        elapsed = float("nan")
        if isinstance(result, tuple) and len(result) >= 3 \
                and result[2] is not None:
            try:
                elapsed = float(result[2])
            except (TypeError, ValueError):
                elapsed = float("nan")
        no_sol_extra = dict(nan_extra)
        no_sol_extra["hexaly_elapsed_s"] = elapsed
        return "NO_SOLUTION", nan_metrics, no_sol_extra

    # Success 7-tuple. element[0] is the product->station assignment dict.
    assignment, returned_visits, elapsed, max_wl, wl_std, cap_broken, wl_broken \
        = result
    if not isinstance(assignment, dict):
        assignment = {}

    # F1: authoritative reference = recompute from the assignment.
    visits = recompute_visits(assignment, order_prods)
    try:
        returned_visits_f = float(returned_visits)
    except (TypeError, ValueError):
        returned_visits_f = float("nan")
    if np.isfinite(returned_visits_f) and abs(visits - returned_visits_f) > 1.0:
        print(f"  [WARN] {label}: recomputed visits={visits:.0f} differs from "
              f"Hexaly-returned={returned_visits_f:.0f} by "
              f"{abs(visits - returned_visits_f):.0f} (>1). Using recomputed "
              f"value (returned is a bound when OPTIMAL).", file=sys.stderr)

    try:
        elapsed_f = float(elapsed)
    except (TypeError, ValueError):
        elapsed_f = float("nan")
    # F3: proven-optimal iff it stopped meaningfully before the budget.
    optimal_inferred = bool(np.isfinite(elapsed_f) and time_limit > 0
                            and elapsed_f < 0.95 * time_limit)

    metrics: Dict[str, float] = {
        "visits": visits,
        "time_s": elapsed_f,
        "max_workload": float(max_wl) if max_wl is not None else float("nan"),
        "workload_std_dev": (float(wl_std) if wl_std is not None
                             else float("nan")),
        "cap_broken": (float(cap_broken) if cap_broken is not None
                       else float("nan")),
        "wl_broken": (float(wl_broken) if wl_broken is not None
                      else float("nan")),
    }
    extra: Dict[str, Any] = {
        "hexaly_returned_visits": returned_visits_f,
        "hexaly_elapsed_s": elapsed_f,
        "hexaly_optimal_inferred": bool(optimal_inferred),
    }
    return "OK", metrics, extra


# --------------------------------------------------------------------------- #
#  PER-INSTANCE CSV (restartable append)                                      #
# --------------------------------------------------------------------------- #
def _per_instance_path(out_dir: str) -> str:
    return os.path.join(out_dir, "exp02a_per_instance.csv")


def load_done_keys(out_dir: str) -> set:
    """Return the set of (size_n, instance_seed, method, solver_seed) already run.

    Used to make the campaign restartable: completed combos are skipped.
    """
    path = _per_instance_path(out_dir)
    done: set = set()
    if not os.path.exists(path):
        return done
    try:
        prev = pd.read_csv(path)
    except Exception:  # noqa: BLE001 - corrupt/partial file: start fresh-ish
        return done
    for _, row in prev.iterrows():
        try:
            key = (int(row["size_n"]), int(row["instance_seed"]),
                   str(row["method"]), int(row["solver_seed"]))
        except (KeyError, ValueError, TypeError):
            continue
        done.add(key)
    return done


def migrate_per_instance_header(out_dir: str) -> None:
    """One-time header migration for REV-2 files written before the 3 REV-3 cols.

    A REV-2 exp02a_per_instance.csv has an 18-column header. REV 3 appends three
    Hexaly-only columns at the END (_PER_INSTANCE_COLS). Appending 21-field rows
    under an 18-name header would misalign pandas on read, so if the existing
    header is missing any new column we rewrite the file ONCE with the full
    header, padding pre-existing rows with blanks for the new columns. Idempotent
    (no-op when the header already matches, or the file does not exist).
    """
    path = _per_instance_path(out_dir)
    if not os.path.exists(path):
        return
    with open(path, "r", newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        try:
            header = next(reader)
        except StopIteration:
            return  # empty file -> next append writes the full header
        existing = list(reader)
    missing = [c for c in _PER_INSTANCE_COLS if c not in header]
    if not missing:
        return  # already migrated / already full
    # Rewrite with the canonical full header, mapping old rows by name.
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(_PER_INSTANCE_COLS))
        writer.writeheader()
        for r in existing:
            mapped = {header[i]: r[i] for i in range(min(len(header), len(r)))}
            writer.writerow({c: mapped.get(c, "") for c in _PER_INSTANCE_COLS})
    print(f"[migrate] exp02a_per_instance.csv header extended with "
          f"{len(missing)} REV-3 column(s): {', '.join(missing)}")


def append_row(out_dir: str, row: Dict[str, Any]) -> None:
    """Append one per-instance row, writing the header exactly once."""
    path = _per_instance_path(out_dir)
    write_header = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(_PER_INSTANCE_COLS))
        if write_header:
            writer.writeheader()
        writer.writerow({c: row.get(c, "") for c in _PER_INSTANCE_COLS})


# --------------------------------------------------------------------------- #
#  RUN ONE INSTANCE                                                           #
# --------------------------------------------------------------------------- #
def run_instance(
    size_n: int,
    instance_seed: int,
    time_limit: float,
    theta: float,
    ga_seeds: List[int],
    ga_sideprobe_seeds: List[int],
    is_sideprobe_instance: bool,
    instance_dir: str,
    out_dir: str,
    done_keys: set,
) -> None:
    """Run the 4 methods (Heuristic, SA-C, GA, Hexaly) on one instance.

    The instance is REUSED from disk when retained (F6); only generated if its
    CSVs are missing. Per-instance rows are appended as they complete
    (restartable: a re-run with cached GA/SA/heur rows executes ONLY Hexaly).

    Side-probe GA rows (solver_probe=True) are written but EXCLUDED downstream
    from CI aggregation and best_found (they only document GA's near-inert
    solver seed axis at N=50).

    Hexaly (F0-F5): R_Hexaly=1, solver_seed=-1 sentinel, solver_probe=False, no
    warm start. Its visits are RECOMPUTED from the returned assignment (F1) and
    it carries the hexaly_returned_visits / hexaly_elapsed_s /
    hexaly_optimal_inferred audit columns (F3). On infeasible/extraction failure
    (F2) its status is NO_SOLUTION with NaN metrics.
    """
    prefix = f"syn_{size_n}sku"

    # (a) REUSE the retained per-seed instance when present; only generate if the
    #     dir/CSVs are missing (F6). This guarantees the Hexaly pass solves the
    #     EXACT instances the cached GA/SA/heur rows used. Hash the CSVs into
    #     hash_manifest_v3.txt for pairing-integrity evidence (N1).
    inst_dir, regenerated = ensure_instance(
        size_n=size_n, instance_seed=instance_seed, theta=theta,
        instance_dir=instance_dir,
    )
    if regenerated:
        print(f"  [gen] regenerated instance N={size_n} seed={instance_seed} "
              f"(CSVs were missing).")
    else:
        print(f"  [reuse] retained instance N={size_n} seed={instance_seed} "
              f"(skip generation).")
    append_instance_hash_manifest(
        out_dir, size_n, instance_seed, inst_dir, regenerated)

    # Realized params from the (reused or freshly generated) CSVs on disk, so the
    # reported values match the instance actually solved -- read once here.
    _orders_df_raw = pd.read_csv(
        os.path.join(inst_dir, f"{prefix}_orders.csv"), sep=";")
    _stations_df_raw = pd.read_csv(
        os.path.join(inst_dir, f"{prefix}_stations.csv"), sep=";")
    params = realized_params(_orders_df_raw, _stations_df_raw, size_n)

    # (b) Load per baseline with each baseline's OWN read_data (different arity).
    #     heuristic -> 5-tuple ; ga / sa / hexaly -> 4-tuple.
    h_order_prods, h_stations, h_products, h_prod_lines, h_orders_df = \
        heuristic_synthetic.read_data(prefix, inst_dir)
    g_order_prods, g_stations, g_products, g_prod_lines = \
        ga_baseline.read_data(prefix, inst_dir)
    s_order_prods, s_stations, s_products, s_prod_lines = \
        sa_correlated.read_data(prefix, inst_dir)
    # Hexaly uses milp_synthetic.read_data (4-tuple, same shape as GA/SA).
    x_order_prods, x_stations, x_products, x_prod_lines = \
        milp_synthetic.read_data(prefix, inst_dir)

    # Collected (method, solver_seed, probe, status, metrics, extra) per instance.
    # `extra` carries the Hexaly-only audit columns ({} for the other methods).
    _empty_extra: Dict[str, Any] = {
        "hexaly_returned_visits": "", "hexaly_elapsed_s": "",
        "hexaly_optimal_inferred": "",
    }
    collected: List[
        Tuple[str, int, bool, str, Dict[str, float], Dict[str, Any]]
    ] = []

    # --- (c) HEURISTIC (deterministic, runs to completion; solver_seed=-1) ---
    key = (size_n, instance_seed, "Heuristic", -1)
    if key not in done_keys:
        status, m = _safe_run(
            f"Heuristic N={size_n} seed={instance_seed}",
            lambda: heuristic_synthetic.heuristic_cslap(
                h_order_prods, h_stations, h_products, h_prod_lines, h_orders_df),
        )
        collected.append(("Heuristic", -1, False, status, m, dict(_empty_extra)))
    else:
        print(f"  [skip] Heuristic N={size_n} seed={instance_seed} (already done)")

    # --- (d) SA-C (deterministic via internal RandomState(42); solver_seed=-1) ---
    key = (size_n, instance_seed, "SA-C", -1)
    if key not in done_keys:
        status, m = _safe_run(
            f"SA-C N={size_n} seed={instance_seed}",
            lambda: sa_correlated.simulated_annealing_correlated(
                s_order_prods, s_stations, s_products, s_prod_lines,
                time_limit=time_limit),
        )
        collected.append(("SA-C", -1, False, status, m, dict(_empty_extra)))
    else:
        print(f"  [skip] SA-C N={size_n} seed={instance_seed} (already done)")

    # --- (e) GA main seeds (solver_probe=False) ---
    for gseed in ga_seeds:
        key = (size_n, instance_seed, "GA", gseed)
        if key in done_keys:
            print(f"  [skip] GA N={size_n} seed={instance_seed} g={gseed} (done)")
            continue
        # Seed BEFORE the call: only controls repair_capacity's global shuffle
        # (np.random.shuffle), which fires only on capacity overflow -> near-inert.
        np.random.seed(gseed)
        random.seed(gseed)
        status, m = _safe_run(
            f"GA N={size_n} seed={instance_seed} g={gseed}",
            lambda: ga_baseline.genetic_algorithm(
                g_order_prods, g_stations, g_products, g_prod_lines,
                time_limit=time_limit),
        )
        collected.append(("GA", gseed, False, status, m, dict(_empty_extra)))

    # --- (f) GA side-probe (solver_probe=True) at N==sideprobe_size, first k ---
    if is_sideprobe_instance:
        for gseed in ga_sideprobe_seeds:
            key = (size_n, instance_seed, "GA", gseed)
            if key in done_keys:
                print(f"  [skip] GA-probe N={size_n} seed={instance_seed} "
                      f"g={gseed} (done)")
                continue
            np.random.seed(gseed)
            random.seed(gseed)
            status, m = _safe_run(
                f"GA-probe N={size_n} seed={instance_seed} g={gseed}",
                lambda: ga_baseline.genetic_algorithm(
                    g_order_prods, g_stations, g_products, g_prod_lines,
                    time_limit=time_limit),
            )
            collected.append(("GA", gseed, True, status, m, dict(_empty_extra)))

    # --- (g) HEXALY set-variable MILP (F0). R_Hexaly=1, solver_seed=-1, no probe,
    #         NO warm start. Authoritative per-instance reference (F1/F5). ---
    key = (size_n, instance_seed, "Hexaly", -1)
    if key not in done_keys:
        x_status, x_m, x_extra = _safe_run_hexaly(
            f"Hexaly N={size_n} seed={instance_seed}",
            lambda: milp_synthetic.run_milp_hexaly(
                x_order_prods, x_stations, x_products, x_prod_lines,
                time_limit=int(round(time_limit)), verbosity=0),
            x_order_prods, time_limit,
        )
        collected.append(("Hexaly", -1, False, x_status, x_m, x_extra))
    else:
        print(f"  [skip] Hexaly N={size_n} seed={instance_seed} (already done)")

    # (h) best_found over the MAIN (non-probe) successful runs only.
    #     If GA has >1 main seed, the FIRST main seed is the GA representative.
    #     Hexaly participates so best_found stays the genuine per-instance best
    #     (kept for REV-2 continuity; the Hexaly reference below is now primary).
    main_ga_seed: Optional[int] = ga_seeds[0] if ga_seeds else None
    main_runs: Dict[str, float] = {}
    for method, gseed, probe, status, m, _extra in collected:
        if probe or status != "OK":
            continue
        if method == "GA" and gseed != main_ga_seed:
            continue  # only the representative GA seed contributes to best_found
        main_runs[method] = m["visits"]
    valid_visits = [v for v in main_runs.values() if np.isfinite(v)]
    best_found: float = float(min(valid_visits)) if valid_visits else float("nan")

    # (i) Append every collected run immediately (restartable).
    for method, gseed, probe, status, m, extra in collected:
        visits = m["visits"]
        if probe or not np.isfinite(best_found) or not np.isfinite(visits) \
                or best_found <= 0:
            rel_rank = float("nan")
        else:
            rel_rank = 100.0 * (visits - best_found) / best_found
        row: Dict[str, Any] = {
            "size_n": size_n,
            "instance_seed": instance_seed,
            "method": method,
            "solver_seed": gseed,
            "solver_probe": probe,
            "status": status,
            "visits": visits,
            "time_s": m["time_s"],
            "best_found_visits": best_found if not probe else float("nan"),
            "rel_rank_pct": rel_rank,
            "max_workload": m["max_workload"],
            "workload_std_dev": m["workload_std_dev"],
            "cap_broken": m["cap_broken"],
            "wl_broken": m["wl_broken"],
            "num_orders": params["num_orders"],
            "num_itemsets": params["num_itemsets"],
            "num_skus": params["num_skus"],
            "num_stations": params["num_stations"],
            "hexaly_returned_visits": extra.get("hexaly_returned_visits", ""),
            "hexaly_elapsed_s": extra.get("hexaly_elapsed_s", ""),
            "hexaly_optimal_inferred": extra.get("hexaly_optimal_inferred", ""),
        }
        append_row(out_dir, row)
        done_keys.add((size_n, instance_seed, method, gseed))


# --------------------------------------------------------------------------- #
#  STATISTICS HELPERS                                                         #
# --------------------------------------------------------------------------- #
def _as_bool(series: pd.Series) -> pd.Series:
    """Coerce a CSV-read solver_probe column to a real boolean mask.

    csv writes Python bools as the strings "True"/"False"; pandas usually infers
    bool but may keep object dtype. Mapping by string is robust to both, where a
    naive `.astype(bool)` on object strings would treat every non-empty string
    (incl. "False") as True.
    """
    if series.dtype == bool:
        return series
    return series.astype(str).str.strip().str.lower().isin(
        ("true", "1", "yes"))


def _t_ci(values: List[float], conf: float = 0.95) -> Dict[str, float]:
    """Two-sided t-interval for a sample mean.

    Guards n < 2 (CI undefined -> NaN). ci_informative is computed by the
    caller (n >= 4). Returns mean, std (sample, ddof=1), n, ci lo/hi, t_mult, df.
    """
    arr = np.asarray([v for v in values if np.isfinite(v)], dtype=float)
    n = int(arr.size)
    out: Dict[str, float] = {
        "mean": float("nan"), "std": float("nan"), "n": float(n),
        "ci_lo": float("nan"), "ci_hi": float("nan"),
        "t_mult": float("nan"), "df": float("nan"),
        "min": float("nan"), "max": float("nan"),
    }
    if n == 0:
        return out
    mean = float(np.mean(arr))
    out["mean"] = mean
    out["min"] = float(np.min(arr))
    out["max"] = float(np.max(arr))
    if n < 2:
        out["std"] = 0.0
        return out
    std = float(np.std(arr, ddof=1))
    df = n - 1
    t_mult = float(stats.t.ppf(0.5 + conf / 2.0, df))
    half = t_mult * std / np.sqrt(n)
    out.update({
        "std": std, "ci_lo": mean - half, "ci_hi": mean + half,
        "t_mult": t_mult, "df": float(df),
    })
    return out


# --------------------------------------------------------------------------- #
#  HEXALY REFERENCE TABLE + JOINED PER-INSTANCE v3 (F5)                       #
# --------------------------------------------------------------------------- #
def hexaly_reference_table(df: pd.DataFrame) -> pd.DataFrame:
    """Per-(size_n, instance_seed) Hexaly reference for the gap relabel (F5).

    Builds one row per instance from the OK Hexaly rows, carrying
    hexaly_ref_visits (the F1 recomputed visits = `visits` on the Hexaly row),
    hexaly_optimal_inferred (F3) and hexaly_elapsed_s. Instances whose Hexaly
    row is NO_SOLUTION/ERROR (F2) get NO reference row -> they drop out of the
    gap join (gaps NaN, never computed against None).
    """
    hx = df[(df["method"] == "Hexaly") & (df["status"] == "OK")].copy()
    if hx.empty:
        return pd.DataFrame(columns=[
            "size_n", "instance_seed", "hexaly_ref_visits",
            "hexaly_optimal_inferred", "hexaly_elapsed_s"])
    hx = hx[np.isfinite(pd.to_numeric(hx["visits"], errors="coerce"))]
    ref = hx[["size_n", "instance_seed", "visits", "hexaly_optimal_inferred",
              "hexaly_elapsed_s"]].copy()
    ref = ref.rename(columns={"visits": "hexaly_ref_visits"})
    # One reference per instance (R_Hexaly=1; defensively drop any duplicate).
    ref = ref.drop_duplicates(subset=["size_n", "instance_seed"], keep="first")
    return ref


def _gap_label(optimal_inferred: Any) -> str:
    """F5 per-instance gap semantics from hexaly_optimal_inferred."""
    s = str(optimal_inferred).strip().lower()
    if s in ("true", "1", "yes"):
        return "optimality_gap"
    return "gap_to_best_feasible_budget"


def build_per_instance_v3(out_dir: str) -> pd.DataFrame:
    """Emit exp02a_per_instance_v3.csv: every method row + Hexaly-ref columns (F5).

    Chosen output strategy: rather than back-patching the appended REV-2 rows,
    we LEFT-JOIN the Hexaly reference (per size_n, instance_seed) onto the full
    per-instance table and compute, for EVERY method row:
      rel_gap_to_hexaly = (visits - hexaly_ref_visits) / hexaly_ref_visits
      gap_label         = optimality_gap | gap_to_best_feasible_budget  (F5)
    The Heuristic may yield rel_gap_to_hexaly < 0 (fewer visits) BECAUSE it is
    workload-INFEASIBLE; that is NOT an improvement. Its wl_broken column is
    carried through so the write-up flags it. Hexaly's own gap is ~0.
    """
    path = _per_instance_path(out_dir)
    df = pd.read_csv(path)
    ref = hexaly_reference_table(df)

    if ref.empty:
        merged = df.copy()
        merged["hexaly_ref_visits"] = float("nan")
        merged["hexaly_optimal_inferred_ref"] = ""
        merged["hexaly_elapsed_s_ref"] = float("nan")
    else:
        merged = df.merge(
            ref.rename(columns={
                "hexaly_optimal_inferred": "hexaly_optimal_inferred_ref",
                "hexaly_elapsed_s": "hexaly_elapsed_s_ref",
            }),
            on=["size_n", "instance_seed"], how="left",
        )

    visits = pd.to_numeric(merged["visits"], errors="coerce")
    ref_v = pd.to_numeric(merged["hexaly_ref_visits"], errors="coerce")
    with np.errstate(divide="ignore", invalid="ignore"):
        merged["rel_gap_to_hexaly"] = (visits - ref_v) / ref_v
    merged.loc[~(ref_v > 0), "rel_gap_to_hexaly"] = float("nan")
    merged["gap_label"] = merged["hexaly_optimal_inferred_ref"].apply(_gap_label)
    # No reference (F2 NO_SOLUTION instance) -> no gap, blank label.
    merged.loc[ref_v.isna(), "gap_label"] = ""

    merged.to_csv(
        os.path.join(out_dir, "exp02a_per_instance_v3.csv"), index=False)
    return merged


# --------------------------------------------------------------------------- #
#  AGGREGATION                                                                #
# --------------------------------------------------------------------------- #
def aggregate(
    out_dir: str,
    sizes: List[int],
    ga_main_seed: Optional[int],
    sideprobe_size: int,
    per_instance_v3: pd.DataFrame,
) -> pd.DataFrame:
    """Build exp02a_aggregated_v3.csv (one row per method x size; 4 methods).

    REV 3: 4 methods x 4 sizes = up to 16 rows. Per method x size we report the
    REV-2 columns (mean_visits +/- t-CI, rel_rank, wl frac/mean) PLUS the
    primary REV-3 reference column mean_rel_gap_to_hexaly +/- CI (Hexaly's own
    ~0). Excludes solver_probe + non-OK rows. For GA, only the representative
    main seed contributes. Reads the JOINED v3 table so the gap column is present.
    """
    df = per_instance_v3.copy()
    df = df[df["status"] == "OK"].copy()

    methods = ["Heuristic", "SA-C", "GA", "Hexaly"]
    rows: List[Dict[str, Any]] = []

    # ga_seed_std_n50: mean over side-probe instances of std(visits across GA seeds)
    ga_seed_std_n50 = _ga_seed_std_sideprobe(df, sideprobe_size)

    for size_n in sizes:
        for method in methods:
            sub = df[(df["size_n"] == size_n) & (df["method"] == method)
                     & (~_as_bool(df["solver_probe"]))].copy()
            if method == "GA" and ga_main_seed is not None:
                sub = sub[sub["solver_seed"] == ga_main_seed]
            visits = pd.to_numeric(sub["visits"], errors="coerce").tolist()
            rr = pd.to_numeric(sub["rel_rank_pct"], errors="coerce").tolist()
            gap = pd.to_numeric(
                sub["rel_gap_to_hexaly"], errors="coerce").tolist()
            wlb = pd.to_numeric(sub["wl_broken"], errors="coerce").tolist()

            ci = _t_ci(visits)
            rr_ci = _t_ci(rr)
            gap_ci = _t_ci(gap)
            n = int(ci["n"])
            wlb_finite = [w for w in wlb if np.isfinite(w)]
            frac_wl = (float(np.mean([1.0 if w > 0 else 0.0 for w in wlb_finite]))
                       if wlb_finite else float("nan"))
            mean_wl = (float(np.mean(wlb_finite)) if wlb_finite else float("nan"))

            rows.append({
                "size_n": size_n,
                "method": method,
                "n_instances": n,
                "mean_visits": ci["mean"],
                "std_visits": ci["std"],
                "ci95_lo": ci["ci_lo"],
                "ci95_hi": ci["ci_hi"],
                "t_mult": ci["t_mult"],
                "df": ci["df"],
                "min_visits": ci["min"],
                "max_visits": ci["max"],
                "ci_informative": bool(n >= 4),
                "mean_rel_rank_pct": rr_ci["mean"],
                "rel_rank_ci95_lo": rr_ci["ci_lo"],
                "rel_rank_ci95_hi": rr_ci["ci_hi"],
                # REV-3 PRIMARY: gap to the Hexaly golden reference.
                "mean_rel_gap_to_hexaly": gap_ci["mean"],
                "rel_gap_ci95_lo": gap_ci["ci_lo"],
                "rel_gap_ci95_hi": gap_ci["ci_hi"],
                "frac_instances_wl_broken": frac_wl,
                "mean_wl_broken": mean_wl,
                "ga_seed_std_n50": (ga_seed_std_n50 if method == "GA"
                                    else float("nan")),
            })

    agg = pd.DataFrame(rows)
    agg.to_csv(os.path.join(out_dir, "exp02a_aggregated_v3.csv"), index=False)
    return agg


def _ga_seed_std_sideprobe(df: pd.DataFrame, sideprobe_size: int) -> float:
    """Mean over the side-probe instances of std(visits across GA seeds).

    Uses ALL GA rows (main + probe) at N==sideprobe_size for the side-probe
    instances (those that actually carry probe rows). Documents the near-inert
    GA solver-seed axis. Returns NaN if no side-probe data exists.
    """
    ga = df[(df["size_n"] == sideprobe_size) & (df["method"] == "GA")].copy()
    if ga.empty:
        return float("nan")
    probe_instances = ga[_as_bool(ga["solver_probe"])]["instance_seed"].unique()
    if len(probe_instances) == 0:
        return float("nan")
    stds: List[float] = []
    for inst in probe_instances:
        v = ga[ga["instance_seed"] == inst]["visits"].dropna().tolist()
        v = [x for x in v if np.isfinite(x)]
        if len(v) >= 2:
            stds.append(float(np.std(v, ddof=1)))
        elif len(v) == 1:
            stds.append(0.0)
    return float(np.mean(stds)) if stds else float("nan")


# --------------------------------------------------------------------------- #
#  PAIRWISE PAIRED STATISTICS                                                 #
# --------------------------------------------------------------------------- #
def _paired_diffs(
    df: pd.DataFrame, size_n: int, m_a: str, m_b: str, ga_main_seed: Optional[int]
) -> Tuple[List[float], List[float], List[float]]:
    """Paired per-instance visits over instances shared by both methods.

    Only main (non-probe) OK rows. For GA, the main representative seed is used.
    Returns (vals_a, vals_b, diffs) all index-aligned to the shared instances.
    """
    def _series(method: str) -> Dict[int, float]:
        sub = df[(df["size_n"] == size_n) & (df["method"] == method)
                 & (df["status"] == "OK") & (~_as_bool(df["solver_probe"]))].copy()
        if method == "GA" and ga_main_seed is not None:
            sub = sub[sub["solver_seed"] == ga_main_seed]
        out: Dict[int, float] = {}
        for _, r in sub.iterrows():
            try:
                v = float(r["visits"])
            except (TypeError, ValueError):
                continue
            if np.isfinite(v):
                out[int(r["instance_seed"])] = v
        return out

    sa, sb = _series(m_a), _series(m_b)
    shared = sorted(set(sa) & set(sb))
    vals_a = [sa[i] for i in shared]
    vals_b = [sb[i] for i in shared]
    diffs = [a - b for a, b in zip(vals_a, vals_b)]
    return vals_a, vals_b, diffs


def pairwise(
    out_dir: str,
    sizes: List[int],
    sig_min_n: int,
    ga_main_seed: Optional[int],
    agg: pd.DataFrame,
    per_instance_v3: pd.DataFrame,
) -> pd.DataFrame:
    """Build exp02a_pairwise_v3.csv (REV-3 pairs incl. Hexaly-vs-*).

    Wilcoxon signed-rank (primary) + paired-t (secondary) on per-instance visit
    differences over shared instances. _PAIRS now includes Hexaly-GA, Hexaly-SA-C,
    Hexaly-Heuristic (Hexaly named first => mean_diff = Hexaly - other: GA/SA give
    positive diffs; the workload-infeasible Heuristic can give a NEGATIVE diff,
    which is NOT an improvement). significant = (wilcoxon_p < 0.05) for sizes with
    n >= sig_min_n; descriptive-only ("NA / descriptive") otherwise. At N=2000
    (K=3) the two-sided Wilcoxon floor is ~0.25, so EVERY N=2000 pair (incl. the
    new Hexaly ones) is marked "NA / descriptive". Reads the JOINED v3 table so
    the Hexaly rows are present.
    """
    df = per_instance_v3
    rows: List[Dict[str, Any]] = []

    for size_n in sizes:
        for m_a, m_b in _PAIRS:
            vals_a, vals_b, diffs = _paired_diffs(
                df, size_n, m_a, m_b, ga_main_seed)
            n = len(diffs)
            ci = _t_ci(diffs)

            wilcoxon_p: float = float("nan")
            paired_t_p: float = float("nan")
            note = ""
            if n >= 2:
                arr = np.asarray(diffs, dtype=float)
                if np.allclose(arr, 0.0):
                    note = "all-equal"  # wilcoxon undefined; p left NaN
                else:
                    try:
                        wilcoxon_p = float(stats.wilcoxon(arr).pvalue)
                    except ValueError as exc:
                        # e.g. all-zero after zero-handling -> report NaN
                        note = f"wilcoxon:{exc}"
                    try:
                        paired_t_p = float(
                            stats.ttest_rel(vals_a, vals_b).pvalue)
                    except Exception:  # noqa: BLE001
                        paired_t_p = float("nan")

            # N=2000 (K=3): Wilcoxon cannot reach p<0.05 (floor ~0.25) -> ALL
            # N=2000 pairs (incl. new Hexaly pairs) are descriptive-only.
            if n >= sig_min_n:
                significant: Any = bool(np.isfinite(wilcoxon_p)
                                        and wilcoxon_p < 0.05)
            else:
                significant = "NA / descriptive"

            ci_overlap = _ci_overlap_diag(agg, size_n, m_a, m_b)

            rows.append({
                "size_n": size_n,
                "pair": f"{m_a}-{m_b}",
                "n_shared": n,
                "mean_diff_visits": ci["mean"],
                "diff_ci95_lo": ci["ci_lo"],
                "diff_ci95_hi": ci["ci_hi"],
                "wilcoxon_p": wilcoxon_p,
                "paired_t_p": paired_t_p,
                "significant": significant,
                "ci_overlap_diagnostic": ci_overlap,
                "note": note,
            })

    pw = pd.DataFrame(rows)
    pw.to_csv(os.path.join(out_dir, "exp02a_pairwise_v3.csv"), index=False)
    return pw


def _ci_overlap_diag(
    agg: pd.DataFrame, size_n: int, m_a: str, m_b: str
) -> Any:
    """Descriptive diagnostic: do the two independent mean CIs overlap?

    Anti-conservative; NOT the significance verdict. Returns bool or NaN.
    """
    ra = agg[(agg["size_n"] == size_n) & (agg["method"] == m_a)]
    rb = agg[(agg["size_n"] == size_n) & (agg["method"] == m_b)]
    if ra.empty or rb.empty:
        return float("nan")
    a_lo, a_hi = ra.iloc[0]["ci95_lo"], ra.iloc[0]["ci95_hi"]
    b_lo, b_hi = rb.iloc[0]["ci95_lo"], rb.iloc[0]["ci95_hi"]
    if not all(np.isfinite([a_lo, a_hi, b_lo, b_hi])):
        return float("nan")
    return bool((a_lo <= b_hi) and (b_lo <= a_hi))


# --------------------------------------------------------------------------- #
#  SUMMARY PRINT                                                              #
# --------------------------------------------------------------------------- #
def print_summary(agg: pd.DataFrame, pw: pd.DataFrame, sizes: List[int]) -> None:
    """Print the final per-size summary (means +/- CI, pairwise significance)."""
    print("\n" + "=" * 78)
    print("EXP-02a SUMMARY (REV 3)  (visits = mean +/- 95% CI; '*' CI inf. n>=4; "
          "gapH = mean rel_gap_to_hexaly)")
    print("=" * 78)
    for size_n in sizes:
        print(f"\n--- N = {size_n} ---")
        sub = agg[agg["size_n"] == size_n]
        for _, r in sub.iterrows():
            star = "*" if bool(r["ci_informative"]) else " "
            ci = (f"+/-{(r['ci95_hi'] - r['mean_visits']):.1f}"
                  if np.isfinite(r["ci95_hi"]) else "[n<2]")
            gaph = r.get("mean_rel_gap_to_hexaly", float("nan"))
            gaph_s = (f"gapH={gaph * 100:+.2f}%" if np.isfinite(gaph)
                      else "gapH=NA")
            print(f"  {r['method']:<10} mean={r['mean_visits']:.1f} {ci} {star} "
                  f"{gaph_s} (n={int(r['n_instances'])}, "
                  f"range=[{r['min_visits']:.0f},{r['max_visits']:.0f}])")
        pwsub = pw[pw["size_n"] == size_n]
        for _, r in pwsub.iterrows():
            sig = r["significant"]
            sig_s = ("SIG" if sig is True or sig == "True"
                     else ("ns" if sig is False or sig == "False" else "NA"))
            print(f"    pair {r['pair']:<14} "
                  f"mean_diff={r['mean_diff_visits']:.1f} "
                  f"wilcoxon_p={r['wilcoxon_p']} t_p={r['paired_t_p']} "
                  f"-> {sig_s}")
    print("=" * 78 + "\n")


# --------------------------------------------------------------------------- #
#  CLI / MAIN                                                                 #
# --------------------------------------------------------------------------- #
def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="EXP-02a multi-instance CI runner "
                    "(GA / SA-C / Heuristic / Hexaly set-variable MILP). "
                    "Hexaly is the per-instance golden reference (REV 3); a "
                    "re-run on cached GA/SA/heur rows executes ONLY Hexaly.")
    p.add_argument("--sizes", nargs="+", type=int, default=[50, 500, 1000, 2000])
    p.add_argument("--k-per-size", nargs="+", type=int, default=[12, 10, 4, 3])
    p.add_argument("--ga-seeds", nargs="+", type=int, default=[20240612])
    p.add_argument("--ga-sideprobe-seeds", nargs="+", type=int,
                   default=[20240613, 20240614])
    p.add_argument("--sideprobe-size", type=int, default=50)
    p.add_argument("--sideprobe-k", type=int, default=3)
    p.add_argument("--instance-seed-start", type=int, default=1001)
    p.add_argument("--time-limits", nargs="+", type=float,
                   default=[120.0, 300.0, 600.0, 900.0])
    p.add_argument("--theta", type=float, default=0.7)
    p.add_argument("--out-dir", type=str, default="exp02a_results")
    p.add_argument("--instance-dir", type=str, default="exp02a_instances")
    p.add_argument("--sig-min-n", type=int, default=5,
                   help="Min shared instances for a significance verdict (else NA).")
    return p.parse_args(argv)


def validate_args(args: argparse.Namespace) -> None:
    """Fail loudly on list-length mismatches (clear error per spec)."""
    n = len(args.sizes)
    if len(args.k_per_size) != n:
        raise ValueError(
            f"--k-per-size has {len(args.k_per_size)} entries but --sizes has "
            f"{n}; they must match one-to-one.")
    if len(args.time_limits) != n:
        raise ValueError(
            f"--time-limits has {len(args.time_limits)} entries but --sizes has "
            f"{n}; they must match one-to-one.")


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    validate_args(args)

    os.makedirs(args.out_dir, exist_ok=True)
    os.makedirs(args.instance_dir, exist_ok=True)
    write_hash_manifest(args.out_dir)
    # REV 3: extend a pre-REV-3 per-instance header with the 3 Hexaly columns
    # before any append/read, so old + new rows stay column-aligned.
    migrate_per_instance_header(args.out_dir)

    done_keys = load_done_keys(args.out_dir)
    if done_keys:
        print(f"[restart] {len(done_keys)} (size,seed,method,solver_seed) combos "
              f"already present -> will skip them.")

    ga_main_seed: Optional[int] = args.ga_seeds[0] if args.ga_seeds else None

    t0 = time.time()
    for size_n, k, tl in zip(args.sizes, args.k_per_size, args.time_limits):
        seeds = list(range(args.instance_seed_start,
                           args.instance_seed_start + k))
        for idx, s in enumerate(seeds):
            is_probe = (size_n == args.sideprobe_size
                        and idx < args.sideprobe_k)
            print(f"\n>>> N={size_n} | instance_seed={s} | tl={tl}s "
                  f"| sideprobe={is_probe}")
            try:
                run_instance(
                    size_n=size_n, instance_seed=s, time_limit=tl,
                    theta=args.theta, ga_seeds=args.ga_seeds,
                    ga_sideprobe_seeds=args.ga_sideprobe_seeds,
                    is_sideprobe_instance=is_probe,
                    instance_dir=args.instance_dir, out_dir=args.out_dir,
                    done_keys=done_keys,
                )
            except Exception as exc:  # noqa: BLE001 - instance-level guard
                print(f"  [FATAL-INSTANCE] N={size_n} seed={s} aborted: "
                      f"{type(exc).__name__}: {exc}", file=sys.stderr)
                continue

    # Aggregate + pairwise from the (restartable) per-instance file.
    if not os.path.exists(_per_instance_path(args.out_dir)):
        print("[warn] no per-instance rows produced; nothing to aggregate.")
        return 1
    # REV 3: build the JOINED per-instance v3 table first (adds the Hexaly-ref
    # columns: hexaly_ref_visits, rel_gap_to_hexaly, gap_label), then aggregate
    # + pairwise off that joined frame and write the *_v3.csv outputs. The base
    # exp02a_per_instance.csv stays append-only (Hexaly rows added in place).
    piv3 = build_per_instance_v3(args.out_dir)
    agg = aggregate(args.out_dir, args.sizes, ga_main_seed,
                    args.sideprobe_size, piv3)
    pw = pairwise(args.out_dir, args.sizes, args.sig_min_n, ga_main_seed,
                  agg, piv3)
    print_summary(agg, pw, args.sizes)

    print(f"[done] total wall-clock {time.time() - t0:.1f}s")
    print(f"  per-instance     : {_per_instance_path(args.out_dir)}")
    print(f"  per-instance v3  : "
          f"{os.path.join(args.out_dir, 'exp02a_per_instance_v3.csv')}")
    print(f"  aggregated v3    : "
          f"{os.path.join(args.out_dir, 'exp02a_aggregated_v3.csv')}")
    print(f"  pairwise v3      : "
          f"{os.path.join(args.out_dir, 'exp02a_pairwise_v3.csv')}")
    print(f"  instance hashes  : "
          f"{os.path.join(args.out_dir, 'hash_manifest_v3.txt')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
