r"""
Robustness experiment harness for CSLAP under order-distribution shift.

Stage-3 contract item F.4. Orchestrates the full H1 test (Method Report
``reports/2_method_report.md`` Sections D, E): build the enlarged training
instances :math:`\mathcal{T}` for a grid of conservatism knobs :math:`k`, run each
**unchanged** baseline solver on the nominal (k=1) and robust (k>1) instances,
persist the resulting layouts, and evaluate every layout on the nominal training
orders and on a grid of shifted test cells (eqs. (11)-(13)).

Design constraints (binding)
----------------------------
* **No baseline file is modified.** Runner functions are imported and called
  through thin adapters in :func:`run_solver` that normalise the differing return
  arities (8-tuple MILP vs 7-tuple heuristic/GA/SA/CG).
* **No data generator file is modified.** The Zhang shift wrapper
  (:func:`zhang_shift_orders`) replicates the generator's order-generation
  mechanics against a **frozen** universe / stations / products, regenerating
  **orders only** (Method Report A.4(b), eq. (4)).
* **No leakage** (Method Report E.2): the construction and every solver see only
  training-derived CSVs; test orders are read exclusively by
  :mod:`evaluate_layout_robust`. Disjointness assertions (test seeds != train
  seed) are enforced and logged.
* **Solver backend**: Gurobi arms are skipped (no license in this environment;
  project directive). Hexaly arms (``milp_synthetic``, ``cg_synthetic``) and the
  pure-Python arms (``heuristic_synthetic``, ``ga_baseline``, ``sa_correlated``)
  are run. The construction uses HiGHS via SciPy.

Robustness metrics (Method Report E.1, eq. (13))
------------------------------------------------
.. math::
    \mathrm{PoR}(k) = \frac{N(a_k) - N(a_0)}{N(a_0)}, \qquad
    G(k) = \frac{V^{te}(a_0) - V^{te}(a_k)}{V^{te}(a_0)} .                 \tag{13}
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

# Local imports (this file lives in Baselines/ alongside the solvers).
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import evaluate_layout_robust as ev  # noqa: E402
import pk_instance_robust as tr  # noqa: E402

LAYOUT_DIR = os.path.join(_HERE, "layouts")
LOG_DIR = os.path.join(_HERE, "logs")


# ---------------------------------------------------------------------------
#  ZHANG SHIFT WRAPPER  (frozen universe, orders-only regeneration; eq. 4)
# ---------------------------------------------------------------------------
def zhang_shift_orders(
    train_prefix: str,
    data_dir: str,
    out_prefix: str,
    theta_prime: float,
    rho: float,
    seed: int,
    out_dir: Optional[str] = None,
) -> str:
    r"""Regenerate **orders only** under a shifted distribution (Method Report eq. 4).

    Faithfully replicates the order-generation mechanics of
    ``Data_Generators/synthetic_data_zhang.py`` (common-itemset injection) but
    against a **frozen** universe, products, and stations taken from the training
    instance. The shift parameters are:

    * ``theta_prime``: itemset-injection probability (train default 0.7).
    * ``rho``: fraction of the common-itemset pool **resampled** (replaced by
      fresh random itemsets over the same universe); ``0`` = pure sampling noise,
      ``1`` = complete correlation-structure replacement.
    * ``seed``: RNG seed (must differ from the train seed; asserted by the caller).

    The products and stations files are copied verbatim from the training
    instance, so the universe :math:`P` and capacities are identical; only
    ``{out_prefix}_orders.csv`` carries the shift.

    Args:
        train_prefix: Frozen training prefix supplying universe/products/stations.
        data_dir: Directory of the training CSVs.
        out_prefix: Output prefix for the shifted test instance.
        theta_prime: Shifted injection probability.
        rho: Resampling fraction of the common-itemset pool.
        seed: Test RNG seed.
        out_dir: Output directory (defaults to ``data_dir``).

    Returns:
        The output prefix written.
    """
    out_dir = out_dir or data_dir
    rng = np.random.RandomState(seed)

    products_df = pd.read_csv(
        os.path.join(data_dir, f"{train_prefix}_products.csv"), sep=";"
    )
    stations_df = pd.read_csv(
        os.path.join(data_dir, f"{train_prefix}_stations.csv"), sep=";"
    )
    num_skus = len(products_df)
    products = np.arange(1, num_skus + 1)
    num_stations = len(stations_df)

    # Common itemsets: same count rule as the generator (N * U[0.1, 0.5]).
    num_itemsets = max(int(num_skus * rng.uniform(0.1, 0.5)), 1)
    itemsets: List[List[int]] = []
    for _ in range(num_itemsets):
        size = rng.randint(2, 6)
        itemset = rng.choice(products, size=size, replace=False).tolist()
        itemsets.append(itemset)

    # rho-fraction resampling of the common-itemset pool (the shift mechanism).
    n_resample = int(round(rho * num_itemsets))
    if n_resample > 0:
        idxs = rng.choice(num_itemsets, size=n_resample, replace=False)
        for j in idxs:
            size = rng.randint(2, 6)
            itemsets[j] = rng.choice(products, size=size, replace=False).tolist()

    num_orders = int(num_skus * rng.uniform(30.0, 50.0))

    order_data: List[Dict[str, object]] = []
    for order_id in range(1, num_orders + 1):
        target_size = rng.randint(5, 16)
        current: List[int] = []
        prob = rng.uniform(0.0, 1.0)
        if prob < theta_prime:
            num_sets = rng.randint(1, 4)
            for _ in range(num_sets):
                chosen = itemsets[rng.randint(0, len(itemsets))]
                current.extend(chosen)
                if len(current) >= target_size:
                    break
        while len(current) < target_size:
            current.append(int(rng.choice(products)))
        current = current[:target_size]
        for prod in current:
            order_data.append({
                "ORDER": f"ORD_{order_id}",
                "PRODUCT": f"PROD_{prod}",
                "QTY": int(rng.randint(1, 10)),
                "STATION": int(rng.randint(1, num_stations + 1)),
            })

    df_orders = pd.DataFrame(order_data, columns=["ORDER", "PRODUCT", "QTY", "STATION"])
    os.makedirs(out_dir, exist_ok=True)
    df_orders.to_csv(os.path.join(out_dir, f"{out_prefix}_orders.csv"),
                     index=False, sep=";")
    # Frozen universe/stations carried over verbatim.
    products_df.to_csv(os.path.join(out_dir, f"{out_prefix}_products.csv"),
                       index=False, sep=";")
    stations_df.to_csv(os.path.join(out_dir, f"{out_prefix}_stations.csv"),
                       index=False, sep=";")
    return out_prefix


# ---------------------------------------------------------------------------
#  BERNER TEMPORAL SPLITTER  (implemented, NOT run; assumption U1)
# ---------------------------------------------------------------------------
def berner_temporal_split(
    order_lines_csv: str,
    out_dir: str,
    out_prefix: str,
    train_quantile: float,
    station_template_csv: Optional[str] = None,
) -> Tuple[str, str]:
    r"""Split the industrial BERNER order lines into early-train / late-test.

    **Assumption U1 (flagged, NOT executed in the smoke run).** The BERNER file
    ``BERNER_ORDER_LINES_09-12.csv`` (schema ``PRODUCT;ORDER;QTY;STATION;BOX_ID``)
    has **no date column**, so the manuscript's 13-week temporal split is
    reproduced by an **order-ID-rank** proxy: orders are ranked by id and split at
    the given quantile (10/13 or 8/13). This is a labelled assumption, not a
    verified temporal split.

    Args:
        order_lines_csv: Path to the BERNER order-lines CSV.
        out_dir: Output directory.
        out_prefix: Base prefix; ``_train`` / ``_test`` suffixes are appended.
        train_quantile: Fraction of (ranked) orders in the train split
            (e.g. ``10/13`` or ``8/13``).
        station_template_csv: Optional station file to reuse; if absent,
            homogeneous stations are built by the Zhang flat rule.

    Returns:
        ``(train_prefix, test_prefix)`` written under ``out_dir``.
    """
    df = pd.read_csv(order_lines_csv, sep=";")
    # Standardise to ORDER;PRODUCT;QTY;STATION (BERNER uses PRODUCT;ORDER;...).
    df = df.rename(columns={c: c.upper() for c in df.columns})
    order_ids = sorted(df["ORDER"].unique())
    cut = int(len(order_ids) * train_quantile)
    train_ids = set(order_ids[:cut])
    test_ids = set(order_ids[cut:])
    assert train_ids.isdisjoint(test_ids), "BERNER train/test order ids overlap"

    def _write(ids: set, suffix: str) -> str:
        sub = df[df["ORDER"].isin(ids)].copy()
        sub["PRODUCT"] = sub["PRODUCT"].apply(
            lambda v: v if str(v).startswith("PROD_") else f"PROD_{v}"
        )
        prefix = f"{out_prefix}_{suffix}"
        cols = [c for c in ["ORDER", "PRODUCT", "QTY", "STATION"] if c in sub.columns]
        sub[cols].to_csv(os.path.join(out_dir, f"{prefix}_orders.csv"),
                         index=False, sep=";")
        # Products = universe of this split's SKUs.
        prods = sorted(sub["PRODUCT"].str.replace("PROD_", "", regex=False).unique())
        pdf = pd.DataFrame({"PRODUCT_ID": prods})
        pdf["CATEGORY"] = 0
        pdf["POPULARITY"] = 0
        pdf.to_csv(os.path.join(out_dir, f"{prefix}_products.csv"),
                   index=False, sep=";")
        return prefix

    os.makedirs(out_dir, exist_ok=True)
    train_prefix = _write(train_ids, "train")
    test_prefix = _write(test_ids, "test")
    return train_prefix, test_prefix


# ---------------------------------------------------------------------------
#  SOLVER ADAPTERS  (no baseline modified; arity normalised here)
# ---------------------------------------------------------------------------
def _import_runner(solver: str) -> Tuple[Callable, Callable]:
    """Return ``(read_data, runner)`` for a solver key, importing the baseline."""
    if solver == "heuristic":
        import heuristic_synthetic as m
        return m.read_data, m.heuristic_cslap
    if solver == "ga":
        import ga_baseline as m
        return m.read_data, m.genetic_algorithm
    if solver == "sa":
        import sa_correlated as m
        return m.read_data, m.simulated_annealing_correlated
    if solver == "milp_hexaly":
        import milp_synthetic as m
        return m.read_data, m.run_milp_hexaly
    if solver == "cg_hexaly":
        import cg_synthetic as m
        return m.read_data, m.column_generation_hexaly
    raise ValueError(f"unknown solver {solver!r}")


GA_GLOBAL_SEED: int = 20240612  # fixed global-RNG seed for the GA capacity repair


def run_solver(
    solver: str,
    prefix: str,
    data_dir: str,
    time_limit: int,
    quick: bool = False,
) -> Tuple[Optional[Dict[str, object]], Optional[int], float]:
    r"""Run one baseline solver on one instance and return its layout.

    Adapts the differing baseline signatures and return arities **without
    modifying any baseline file**. The layout is the ``assignment`` dict (first
    element of the standard return tuple).

    Args:
        solver: One of ``heuristic|ga|sa|milp_hexaly|cg_hexaly``.
        prefix: Instance prefix to solve.
        data_dir: Directory holding the instance CSVs.
        time_limit: Per-run time budget (s).
        quick: Reduced-effort flag for GA/SA (smaller pop/gens, fewer iters).

    Returns:
        ``(assignment, total_visits, elapsed)``; ``assignment`` is ``None`` if the
        solver found no feasible layout.
    """
    read_data, runner = _import_runner(solver)
    loaded = read_data(prefix, data_dir)

    t0 = time.time()
    if solver == "heuristic":
        # read_data returns 5-tuple incl. orders_df.
        order_prods, stations, products, prod_lines, orders_df = loaded
        result = runner(order_prods, stations, products, prod_lines, orders_df)
    else:
        order_prods, stations, products, prod_lines = loaded
        if solver in ("ga", "sa"):
            if solver == "ga":
                # Reviewer item (3) determinism fix: ga_baseline.py L176 calls
                # np.random.shuffle on the *unseeded* global RNG (its internal
                # RandomState(42) covers everything else). We cannot edit the
                # baseline, so we seed the global RNG here immediately before the
                # call, making the capacity-repair shuffle reproducible.
                np.random.seed(GA_GLOBAL_SEED)
            result = runner(order_prods, stations, products, prod_lines,
                            time_limit=time_limit, quick=quick)
        else:  # milp_hexaly, cg_hexaly
            if solver == "cg_hexaly":
                result = runner(order_prods, stations, products, prod_lines,
                                time_limit=time_limit, scenario_name=prefix)
            else:
                result = runner(order_prods, stations, products, prod_lines,
                                time_limit=time_limit)
    elapsed = time.time() - t0

    assignment = result[0]
    total_visits = result[1]
    if assignment is None:
        return None, None, elapsed
    return dict(assignment), total_visits, elapsed


def persist_layout(
    assignment: Dict[str, object], layout_id: str
) -> str:
    """Write a ``{product: station}`` layout JSON to ``layouts/`` and return path."""
    os.makedirs(LAYOUT_DIR, exist_ok=True)
    path = os.path.join(LAYOUT_DIR, f"{layout_id}.json")
    serialisable = {str(p): int(s) if isinstance(s, (np.integer,)) else s
                    for p, s in assignment.items()}
    with open(path, "w") as fh:
        json.dump(serialisable, fh)
    return path


# ---------------------------------------------------------------------------
#  EXPERIMENT DRIVER
# ---------------------------------------------------------------------------
def run_experiment(
    instances: Sequence[str],
    solvers: Sequence[str],
    k_grid: Sequence[int],
    data_dir: str,
    theta_primes: Sequence[float],
    rhos: Sequence[float],
    test_seeds: Sequence[int],
    train_seed: int,
    variant: str,
    time_budgets: Dict[str, int],
    construction_backend: str,
    quick_metaheuristics: bool,
    verbose: bool = True,
    cover_max_supports: Optional[int] = None,
    cooccurrence_pairs: int = 0,
    pkk1_control: bool = False,
    cover_json_dir: Optional[str] = None,
) -> str:
    r"""Run the full nominal-vs-robust robustness experiment (Method Report E).

    For each (instance, k) builds :math:`\mathcal{T}` (k=1 is the nominal/identity
    instance); for each solver produces the layout on that instance; evaluates
    every layout on the nominal training orders and on every shifted test cell
    ``(theta', rho, seed)``; writes per-cell rows to
    ``results_robustness_{instance}.csv`` and returns the aggregate results path.

    Leakage guard (Method Report E.2): test seeds must differ from the train
    seed; asserted and logged here.
    """
    assert train_seed not in set(test_seeds), (
        f"LEAKAGE: train_seed {train_seed} appears in test_seeds {list(test_seeds)}"
    )
    os.makedirs(LOG_DIR, exist_ok=True)
    log_path = os.path.join(LOG_DIR, "robustness_harness.log")
    log = open(log_path, "a")

    def _log(msg: str) -> None:
        line = f"[{time.strftime('%H:%M:%S')}] {msg}"
        if verbose:
            print(line, flush=True)
        log.write(line + "\n")
        log.flush()

    _log(f"=== EXPERIMENT START | instances={list(instances)} "
         f"solvers={list(solvers)} k={list(k_grid)} variant={variant} "
         f"backend={construction_backend} train_seed={train_seed} ===")
    _log(f"LEAKAGE GUARD OK: train_seed={train_seed} disjoint from "
         f"test_seeds={list(test_seeds)}")

    eval_csv = os.path.join(_HERE, "results_robustness_eval.csv")
    agg_rows: List[Dict[str, object]] = []

    for instance in instances:
        budget = time_budgets.get(instance, 60)
        _log(f"--- instance={instance} budget={budget}s ---")

        # Build the shifted TEST instances once per cell (frozen universe).
        test_cells: List[Tuple[str, float, float, int]] = []
        for tp in theta_primes:
            for rho in rhos:
                for sd in test_seeds:
                    out_prefix = f"{instance}_te_t{tp}_r{rho}_s{sd}"
                    zhang_shift_orders(instance, data_dir, out_prefix,
                                       theta_prime=tp, rho=rho, seed=sd)
                    test_cells.append((out_prefix, tp, rho, sd))
        _log(f"built {len(test_cells)} shifted test cells")

        # Build the enlarged TRAIN instances for each k (k=1 == nominal).
        # k-keys are integers; the optional pkk1 control arm uses the string
        # key "1T" -- it IS the k=1 closure-transform written through T (so the
        # T_s recalibration / duplicate-collapse side-channel is present) but
        # with closures == supports, isolating that side-channel from the
        # enlargement effect (reviewer item 3).
        train_instances: Dict[object, str] = {}
        # Transform diagnostics per arm: c_bar, degenerate flag (reviewer item 1).
        meta_by_arm: Dict[object, Dict[str, object]] = {}
        run_arms: List[object] = list(k_grid)
        for k in k_grid:
            if k == 1:
                train_instances[k] = instance  # identity transform (no T)
                meta_by_arm[k] = {"c_bar": 1.0, "degenerate": False,
                                  "mean_closure_size": None, "pi_star": 1}
                continue
            # Prefer a pre-built, validated cover JSON (deterministic, avoids the
            # time-budget-dependent integer-master nondeterminism the reviewer
            # flagged). Falls back to building if the JSON is absent.
            cj = None
            if cover_json_dir:
                cand = os.path.join(cover_json_dir, f"cover_{instance}_k{k}.json")
                if os.path.exists(cand):
                    cj = cand
            meta = tr.transform_instance(
                instance, data_dir, k=k, variant=variant,
                backend=construction_backend,
                master_time_limit=max(120, budget * 2),
                pricing_time_limit=15, verbose=False,
                cover_json=cj,
                cover_max_supports=cover_max_supports,
                cooccurrence_pairs=cooccurrence_pairs,
            )
            train_instances[k] = str(meta["out_prefix"])
            meta_by_arm[k] = meta
            if cj:
                _log(f"  (loaded validated cover JSON {os.path.basename(cj)})")
            _log(f"  T(k={k}) -> {meta['out_prefix']} Pi*={meta['pi_star']} "
                 f"mean|closure|={meta['mean_closure_size']:.2f} "
                 f"(support {meta['mean_support_size']:.2f}) "
                 f"c_bar={meta['c_bar']:.3f} frac_strict={meta['frac_strict_growth']:.3f} "
                 f"DEGENERATE={meta['degenerate']} sub={meta.get('cover_max_supports')}")
            if meta["degenerate"]:
                _log(f"  [DEGENERATE] {instance} k={k} arm has only "
                     f"{meta['frac_strict_growth']:.1%} strict-growth orders "
                     f"(c_bar={meta['c_bar']:.3f}); EXCLUDED from summary CSV.")

        # Optional pkk1 control arm (T_s side-channel decomposition).
        if pkk1_control:
            meta1 = tr.transform_instance(
                instance, data_dir, k=1, variant=variant,
                backend=construction_backend,
                master_time_limit=max(120, budget * 2),
                pricing_time_limit=15, verbose=False,
                cover_max_supports=cover_max_supports,
                cooccurrence_pairs=cooccurrence_pairs,
            )
            train_instances["1T"] = str(meta1["out_prefix"])
            # k=1 closure transform is non-degenerate by definition (it is the
            # identity on supports but DOES carry the recalibrated T_s); flag it
            # as a control, c_bar==1.0 expected.
            meta1["degenerate"] = False
            meta_by_arm["1T"] = meta1
            run_arms.append("1T")
            _log(f"  T(k=1T control) -> {meta1['out_prefix']} "
                 f"c_bar={meta1['c_bar']:.3f} T_s "
                 f"{meta1['orig_time_capacity']}->{meta1['new_time_capacity']}")

        for solver in solvers:
            # a_k for every arm: layout optimised on the (transformed) train.
            layouts: Dict[object, Optional[str]] = {}
            nominal_visits: Dict[object, Optional[int]] = {}
            for k in run_arms:
                tinst = train_instances[k]
                try:
                    assignment, visits, elapsed = run_solver(
                        solver, tinst, data_dir, budget,
                        quick=quick_metaheuristics,
                    )
                except Exception as exc:  # noqa: BLE001  (log + continue)
                    _log(f"  [{solver} k={k}] SOLVER ERROR: "
                         f"{type(exc).__name__}: {exc}")
                    layouts[k] = None
                    nominal_visits[k] = None
                    continue
                if assignment is None:
                    _log(f"  [{solver} k={k}] no feasible layout")
                    layouts[k] = None
                    nominal_visits[k] = None
                    continue
                layout_id = f"{instance}_{solver}_k{k}_{variant}"
                path = persist_layout(assignment, layout_id)
                layouts[k] = path
                # Nominal cost N(a_k): evaluate on the ORIGINAL training orders.
                nom = ev.evaluate_and_log(
                    path, instance, data_dir, eval_csv,
                    meta={"solver": solver, "instance": instance, "k": k,
                          "variant": variant, "split": "nominal_train",
                          "theta_prime": "", "rho": "", "test_seed": ""},
                )
                nominal_visits[k] = int(nom["total_visits"])
                _log(f"  [{solver} k={k}] nominal visits={nom['total_visits']} "
                     f"(solve {elapsed:.1f}s)")

            # Evaluate each layout on every shifted test cell (paired).
            te_visits: Dict[object, List[int]] = {k: [] for k in run_arms}
            for (te_prefix, tp, rho, sd) in test_cells:
                for k in run_arms:
                    if layouts[k] is None:
                        continue
                    row = ev.evaluate_and_log(
                        layouts[k], te_prefix, data_dir, eval_csv,
                        meta={"solver": solver, "instance": instance, "k": k,
                              "variant": variant, "split": "shift_test",
                              "theta_prime": tp, "rho": rho, "test_seed": sd},
                    )
                    te_visits[k].append(int(row["total_visits"]))

            # Aggregate: PoR(k), G(k) vs k=1 baseline (eq. 13).
            base_nom = nominal_visits.get(1)
            base_te = float(np.mean(te_visits.get(1, []))) if te_visits.get(1) else None
            for k in run_arms:
                nk = nominal_visits.get(k)
                tek = float(np.mean(te_visits[k])) if te_visits[k] else None
                por = ((nk - base_nom) / base_nom) if (nk and base_nom) else None
                gain = ((base_te - tek) / base_te) if (tek and base_te) else None
                arm_meta = meta_by_arm.get(k, {})
                c_bar = arm_meta.get("c_bar", 1.0)
                degenerate = bool(arm_meta.get("degenerate", False))
                row = {
                    "instance": instance, "solver": solver, "k": k,
                    "variant": variant,
                    "nominal_visits": nk,
                    "mean_test_visits": tek,
                    "PoR": por, "G": gain,
                    "n_test_cells": len(te_visits[k]),
                    "c_bar": round(c_bar, 4) if c_bar is not None else "",
                    "degenerate": degenerate,
                }
                _log(f"  [{solver} k={k}] N={nk} V_te(mean)="
                     f"{tek if tek is None else round(tek,1)} "
                     f"PoR={por if por is None else round(por,4)} "
                     f"G={gain if gain is None else round(gain,4)} "
                     f"c_bar={round(c_bar,3) if c_bar is not None else 'NA'} "
                     f"degenerate={degenerate}")
                if degenerate:
                    # Reviewer item 1: degenerate enlargement arms are EXCLUDED
                    # from the summary CSV (kept in the eval CSV + log only).
                    _log(f"  [{solver} k={k}] EXCLUDED from summary (degenerate).")
                    continue
                agg_rows.append(row)

        # Per-instance results CSV.
        inst_csv = os.path.join(_HERE, f"results_robustness_{instance}.csv")
        _write_rows(inst_csv, [r for r in agg_rows if r["instance"] == instance])
        _log(f"wrote {inst_csv}")

    agg_csv = os.path.join(_HERE, "results_robustness_summary.csv")
    _append_summary(agg_csv, agg_rows)
    _log(f"=== EXPERIMENT DONE -> {agg_csv} (appended {len(agg_rows)} rows) ===")
    log.close()
    return agg_csv


SUMMARY_COLS: List[str] = [
    "instance", "solver", "k", "variant", "nominal_visits",
    "mean_test_visits", "PoR", "G", "n_test_cells", "c_bar", "degenerate",
]


def _write_rows(path: str, rows: List[Dict[str, object]]) -> None:
    """Write a list of dict rows to a CSV (overwrite). Per-instance file only."""
    if not rows:
        return
    with open(path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=SUMMARY_COLS)
        writer.writeheader()
        for r in rows:
            writer.writerow({c: r.get(c, "") for c in SUMMARY_COLS})


def _append_summary(path: str, rows: List[Dict[str, object]]) -> None:
    """Append rows to the unified summary CSV, preserving existing rows.

    Reviewer item 1: the unified summary must keep prior rows and carry the new
    ``c_bar`` / ``degenerate`` columns. If the file pre-dates those columns it is
    re-written with the columns added (legacy rows get blank/migrated values; the
    legacy k=4 syn_50sku rows are migrated to degenerate=True, c_bar=1.0 by the
    caller via :func:`migrate_legacy_summary` before this append).
    """
    if not rows:
        return
    existing: List[Dict[str, object]] = []
    if os.path.exists(path):
        with open(path, newline="") as fh:
            existing = list(csv.DictReader(fh))
    # Drop existing rows that this run regenerates (same instance+solver+k).
    keys = {(str(r["instance"]), str(r["solver"]), str(r["k"])) for r in rows}
    kept = [r for r in existing
            if (str(r.get("instance")), str(r.get("solver")), str(r.get("k")))
            not in keys]
    with open(path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=SUMMARY_COLS)
        writer.writeheader()
        for r in kept + rows:
            writer.writerow({c: r.get(c, "") for c in SUMMARY_COLS})


# ---------------------------------------------------------------------------
#  CLI
# ---------------------------------------------------------------------------
def main() -> None:
    """CLI entry point for the robustness experiment harness."""
    parser = argparse.ArgumentParser(
        description="CSLAP robustness experiment harness (Method Report E)."
    )
    parser.add_argument("--instances", nargs="+", default=["syn_50sku"])
    parser.add_argument("--solvers", nargs="+",
                        default=["heuristic", "ga", "sa"],
                        help="Subset of heuristic|ga|sa|milp_hexaly|cg_hexaly.")
    parser.add_argument("--k", nargs="+", type=int, default=[1, 2, 4, 6])
    parser.add_argument("--dir", type=str, default="synthetic_datasets")
    parser.add_argument("--theta-primes", nargs="+", type=float,
                        default=[0.5, 0.7, 0.9])
    parser.add_argument("--rhos", nargs="+", type=float, default=[0.0, 0.5, 1.0])
    parser.add_argument("--test-seeds", nargs="+", type=int,
                        default=[43, 44, 45, 46, 47])
    parser.add_argument("--train-seed", type=int, default=42)
    parser.add_argument("--variant", type=str, default="exact",
                        choices=["exact", "cover"])
    parser.add_argument("--backend", type=str, default="highs",
                        choices=["auto", "highs", "hexaly"])
    parser.add_argument("--time-50", type=int, default=60)
    parser.add_argument("--time-500", type=int, default=120)
    parser.add_argument("--quick", action="store_true",
                        help="Reduced-effort GA/SA (smaller pop/gens/iters).")
    parser.add_argument("--cover-max-supports", type=int, default=None,
                        help="Deviation U7: cap distinct supports fed to the "
                             "construction (fixed-seed subsample). None = full set.")
    parser.add_argument("--cooccurrence-pairs", type=int, default=0,
                        help="Reviewer item 2: seed N greedy co-occurrence merges "
                             "of sizes 2..k into the construction column pool.")
    parser.add_argument("--pkk1-control", action="store_true",
                        help="Reviewer item 3: also run the k=1 closure-transform "
                             "control arm (labelled 1T) to decompose the T_s "
                             "recalibration side-channel from the enlargement.")
    parser.add_argument("--cover-json-dir", type=str, default=None,
                        help="Directory of pre-built validated cover JSONs "
                             "(cover_{instance}_k{k}.json); loaded if present to "
                             "make the construction deterministic.")
    args = parser.parse_args()

    budgets: Dict[str, int] = {}
    for inst in args.instances:
        budgets[inst] = args.time_500 if "500" in inst else args.time_50

    run_experiment(
        instances=args.instances, solvers=args.solvers, k_grid=args.k,
        data_dir=args.dir, theta_primes=args.theta_primes, rhos=args.rhos,
        test_seeds=args.test_seeds, train_seed=args.train_seed,
        variant=args.variant, time_budgets=budgets,
        construction_backend=args.backend,
        quick_metaheuristics=args.quick,
        cover_max_supports=args.cover_max_supports,
        cooccurrence_pairs=args.cooccurrence_pairs,
        pkk1_control=args.pkk1_control,
        cover_json_dir=args.cover_json_dir,
    )


if __name__ == "__main__":
    main()
