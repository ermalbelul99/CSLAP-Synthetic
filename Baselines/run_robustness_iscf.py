r"""
Staged ISCF K-fold robustness harness (plan.md Phase D/E, CPLEX validation phase).

Tests hypothesis **H1** (P-K covering enlargement = data-driven robust counterpart
of CSLAP) on the clean, kappa-invariant ISCF instance with **repeated random
K-fold** train/test splits, an **exact CPLEX cover**, and **Hexaly placement** --
counting visits on **real** orders only. It removes the first-run biases
(reports/5_scientific_report_iter2.md): exact cover (G1/G2), kappa-invariant
capacity so the price/gain reading is not confounded by recalibration (G4),
multi-fold confidence intervals (G5), and feasibility enforced by the placement
solver and re-checked per station (G6). Closures only shape placement; every
reported visit count is on the real orders (G7).

Why staged (two virtual environments)
--------------------------------------
No single interpreter on this machine has both CPLEX (``docplex``) and Hexaly, so
the pipeline is split into subcommands run by the matching interpreter:

* ``make-folds``   -- pandas only (run in either venv).
* ``build-covers`` -- **CPLEX venv** (``Virtual_Environment_CPLEX_1``): the exact
  P-K cover per (fold, k); saves the pattern family JSON.
* ``place``        -- **Hexaly venv** (``Virtual_Environment_LocalSolver_3``): the
  product->station placement via the UNMODIFIED ``milp_synthetic.run_milp_hexaly``.
* ``evaluate``     -- pandas (+ scipy for stats); scores layouts on real orders and
  aggregates folds (mean +/- 95% CI, paired Wilcoxon, PoR/G tradeoff).

Because capacity is **kappa-invariant** (slot count, fixed per product/volume), the
enlarged instance's stations file is identical to the nominal one; placement
therefore needs only the cover **patterns** (to enlarge each order to its closure),
not a separate enlarged-orders file. The workload is driven by the **real**
per-product pick-lines ``REAL_LINES`` (carried in the products file by
``iscf_adapter``), passed to the placement solver as ``prod_lines`` -- never the
closure line counts.

Placement order set (tractability, plan.md Phase D)
---------------------------------------------------
Size-1 orders are a constant 1 visit and are dropped from the optimization;
multi-item orders are aggregated to distinct supports. The Hexaly objective sums
one term per order, and the full distinct-support set (tens of thousands) makes
each local-search move re-evaluate a huge objective, so the optimization uses the
**top-N most frequent** distinct supports (``--top-supports``; this also weights
the objective toward the common patterns). Both arms (k=1 raw, k>1 closures) use
the **same** N underlying supports, so the comparison stays paired. Evaluation is
always on the **full real** held-out orders.

Metrics (Method Report eq. 13)
------------------------------
.. math::
    \mathrm{PoR}(k) = \frac{N(a_k) - N(a_0)}{N(a_0)}, \qquad
    G(k) = \frac{V^{te}(a_0) - V^{te}(a_k)}{V^{te}(a_0)} ,

with ``N`` = visits on real **train** orders, ``V^{te}`` = visits on real **test**
orders, ``a_0`` the k=1 (nominal) layout and ``a_k`` the enlarged-arm layout.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from collections import Counter
from typing import Dict, FrozenSet, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

FOLD_DIR_DEFAULT = os.path.join(_HERE, "iscf_folds")
COVER_DIR_DEFAULT = os.path.join(_HERE, "iscf_covers")
LAYOUT_DIR_DEFAULT = os.path.join(_HERE, "iscf_layouts")
RESULT_DIR_DEFAULT = os.path.join(_HERE, "iscf_results")


# ---------------------------------------------------------------------------
#  SHARED I/O HELPERS
# ---------------------------------------------------------------------------
def _read_instance(
    prefix: str, data_dir: str
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Read the three standard semicolon CSVs of an instance prefix."""
    orders = pd.read_csv(os.path.join(data_dir, f"{prefix}_orders.csv"), sep=";")
    products = pd.read_csv(os.path.join(data_dir, f"{prefix}_products.csv"), sep=";")
    stations = pd.read_csv(os.path.join(data_dir, f"{prefix}_stations.csv"), sep=";")
    return orders, products, stations


def _supports(orders: pd.DataFrame) -> "pd.Series":
    """Per-order product frozenset (the support :math:`P_o`)."""
    return orders.groupby("ORDER")["PRODUCT"].apply(frozenset)


def _real_prod_lines(products: pd.DataFrame) -> Dict[str, int]:
    """Map ``PROD_<id> -> REAL_LINES`` (kappa-invariant real pick-line count)."""
    return {
        f"PROD_{pid}": int(n)
        for pid, n in zip(products["PRODUCT_ID"], products["REAL_LINES"])
    }


# ---------------------------------------------------------------------------
#  STAGE 1 -- MAKE FOLDS
# ---------------------------------------------------------------------------
def _temporal_cuts(order_ids: np.ndarray, k_folds: int) -> List[Tuple[np.ndarray, np.ndarray]]:
    r"""Train-early / test-late cuts by ORDER_ID rank (assumption U1: ID monotone in time).

    Produces ``k_folds`` expanding-train cuts at train fractions evenly spaced in
    ``[0.5, 0.9]``; test = the complementary late tail. The cuts share train mass
    (not independent), so they are a dispersion **proxy**, reported as such. Mirrors
    the manuscript's early/late temporal-holdout protocol (Method Report A.4(a)).
    """
    try:
        order = np.argsort(order_ids.astype(np.int64))
    except (ValueError, TypeError):
        order = np.argsort(order_ids.astype(str))
    ranked = order_ids[order]
    n = len(ranked)
    fracs = np.linspace(0.5, 0.9, k_folds)
    cuts: List[Tuple[np.ndarray, np.ndarray]] = []
    for fr in fracs:
        c = int(n * fr)
        cuts.append((ranked[:c], ranked[c:]))  # (train ids, test ids)
    return cuts


def make_folds(
    prefix: str,
    data_dir: str,
    out_dir: str,
    k_folds: int,
    repeats: int,
    seed: int,
    slack: float,
    mode: str = "random",
    train_cap: Optional[int] = None,
    verbose: bool = True,
) -> str:
    r"""Write repeated random K-fold train/test instances and a manifest.

    Orders are shuffled (seeded) and partitioned into ``k_folds`` folds, repeated
    ``repeats`` times with distinct seeds. For each (repeat, fold): test = the
    held-out fold's orders, train = the rest. Train/test order-id sets are asserted
    disjoint (no leakage). The train products file carries ``REAL_LINES`` recomputed
    on the **train** orders (kappa-invariant within the fold); the train stations
    file carries a kappa-invariant ``TIME_CAPACITY`` =
    :math:`\lceil \text{slack}\cdot\sum_p L_p^{tr}/|S|\rceil`. Both arms of a fold
    reuse this same stations file, so capacity never depends on :math:`\kappa`.
    """
    os.makedirs(out_dir, exist_ok=True)
    orders, products, stations = _read_instance(prefix, data_dir)
    n_stations = len(stations)
    speed = float(stations["SPEED"].iloc[0])

    order_ids = orders["ORDER"].unique()
    universe_attrs = products.set_index("PRODUCT_ID")  # VOLUME/FREQUENCY per SKU

    # Build the (repeat, fold, train_ids, test_ids) plan per mode.
    plan: List[Tuple[int, int, set, set]] = []
    if mode == "temporal":
        cuts = _temporal_cuts(order_ids, k_folds)
        for f, (tr_ids, te_ids) in enumerate(cuts):
            plan.append((0, f, set(tr_ids), set(te_ids)))
    else:
        for r in range(repeats):
            rng = np.random.RandomState(seed + r)
            perm = rng.permutation(len(order_ids))
            folds = np.array_split(perm, k_folds)
            for f in range(k_folds):
                test_idx = folds[f]
                train_idx = np.concatenate(
                    [folds[j] for j in range(k_folds) if j != f]
                )
                plan.append((r, f, set(order_ids[train_idx]), set(order_ids[test_idx])))

    manifest: List[Dict[str, object]] = []
    if True:
        for (r, f, train_ids, test_ids) in plan:
            assert train_ids.isdisjoint(test_ids), "LEAKAGE: train/test overlap"

            # Sparse-train: sub-sample the train orders to train_cap (seeded). The
            # product universe stays the full instance (the layout still places every
            # product), so test coverage kappa stays 1 -- only the train co-occurrence
            # density drops, which is the variable under study.
            if train_cap is not None and len(train_ids) > train_cap:
                rng_c = np.random.RandomState(seed + 1000 * r + f)
                arr = np.array(sorted(train_ids))
                train_ids = set(rng_c.choice(arr, size=train_cap, replace=False).tolist())

            tag = f"{prefix}_r{r}f{f}"
            train_prefix = f"{tag}_train"
            test_prefix = f"{tag}_test"

            train_orders = orders[orders["ORDER"].isin(train_ids)]
            test_orders = orders[orders["ORDER"].isin(test_ids)]

            # Train REAL_LINES = #distinct train orders containing each product.
            train_Lp = (
                train_orders.drop_duplicates(["ORDER", "PRODUCT"])
                .groupby("PRODUCT")["ORDER"].nunique()
            )
            train_products = products.copy()
            tok = "PROD_" + train_products["PRODUCT_ID"].astype(str)
            train_products["REAL_LINES"] = tok.map(train_Lp).fillna(0).astype(int).to_numpy()

            total_train_lines = int(train_products["REAL_LINES"].sum())
            time_cap = int(math.ceil(slack * total_train_lines / (speed * n_stations)))
            train_stations = stations.copy()
            train_stations["TIME_CAPACITY"] = time_cap

            # Write train + test instances.
            train_orders.to_csv(
                os.path.join(out_dir, f"{train_prefix}_orders.csv"), index=False, sep=";"
            )
            train_products.to_csv(
                os.path.join(out_dir, f"{train_prefix}_products.csv"), index=False, sep=";"
            )
            train_stations.to_csv(
                os.path.join(out_dir, f"{train_prefix}_stations.csv"), index=False, sep=";"
            )
            test_orders.to_csv(
                os.path.join(out_dir, f"{test_prefix}_orders.csv"), index=False, sep=";"
            )
            # Test reuses the train universe + stations (domain = train SKUs).
            train_products.to_csv(
                os.path.join(out_dir, f"{test_prefix}_products.csv"), index=False, sep=";"
            )
            train_stations.to_csv(
                os.path.join(out_dir, f"{test_prefix}_stations.csv"), index=False, sep=";"
            )

            entry = {
                "repeat": r, "fold": f, "tag": tag,
                "train_prefix": train_prefix, "test_prefix": test_prefix,
                "n_train_orders": int(len(train_ids)),
                "n_test_orders": int(len(test_ids)),
                "time_capacity": time_cap,
            }
            manifest.append(entry)
            if verbose:
                print(f"  fold r{r}f{f}: train={len(train_ids)} test={len(test_ids)} "
                      f"T_s={time_cap}", flush=True)

    manifest_path = os.path.join(out_dir, f"{prefix}_folds_manifest.json")
    with open(manifest_path, "w") as fh:
        json.dump({"prefix": prefix, "data_dir": data_dir, "k_folds": k_folds,
                   "repeats": repeats, "seed": seed, "slack": slack,
                   "folds": manifest}, fh, indent=2)
    if verbose:
        print(f"make-folds: wrote {len(manifest)} folds + manifest {manifest_path}")
    return manifest_path


# ---------------------------------------------------------------------------
#  STAGE 2 -- BUILD COVERS  (CPLEX venv)
# ---------------------------------------------------------------------------
def build_covers(
    manifest_path: str,
    fold_dir: str,
    out_dir: str,
    k_grid: Sequence[int],
    variant: str,
    cover_time: float,
    pricing_time: float,
    cooccurrence_pairs: int,
    seed_chunks: bool,
    objective: str = "minmax",
    verbose: bool = True,
) -> None:
    r"""Run the exact CPLEX P-K cover per (fold, k>1); save the pattern family.

    Saves ``{out_dir}/cover_{tag}_k{k}.json`` with the selected patterns, the
    achieved :math:`\Pi^*` (certified over **all** train distinct supports, no
    subsample), the realised enlargement :math:`\bar c`, and the **cover
    composition** -- the total number of sets and the pattern-size histogram
    ``{size: count}``. Appends one row per cover to ``cover_composition.csv``.
    """
    import csv as _csv
    from collections import Counter as _Counter

    import pk_cover_construction as pk

    os.makedirs(out_dir, exist_ok=True)
    with open(manifest_path) as fh:
        manifest = json.load(fh)

    comp_rows: List[Dict[str, object]] = []
    for entry in manifest["folds"]:
        tag = entry["tag"]
        train_prefix = entry["train_prefix"]
        supports, universe, distinct = pk.read_supports_from_instance(
            train_prefix, fold_dir
        )
        mean_support = float(np.mean([len(s) for s in supports])) if supports else 0.0
        for k in k_grid:
            if k <= 1:
                continue
            t0 = time.time()
            patterns, pi_star, timing = pk.run_pk_cover(
                supports, universe, distinct, k=k, variant=variant,
                master_time_limit=cover_time, pricing_time_limit=pricing_time,
                backend="cplex", cooccurrence_pairs=cooccurrence_pairs,
                seed_chunks=seed_chunks, objective=objective, verbose=False,
            )
            # Certify Pi_true + partition validity over ALL train distinct supports.
            check = pk.check_partition_and_pi(patterns, universe, distinct, variant)
            # Realised enlargement c_bar over the train orders.
            closures = [
                frozenset().union(*[q for q in patterns if q & s]) if s else frozenset()
                for s in supports
            ]
            mean_closure = float(np.mean([len(c) for c in closures])) if closures else 0.0
            c_bar = (mean_closure / mean_support) if mean_support > 0 else 1.0
            # Cover composition: total sets + pattern-size histogram (user-requested).
            size_hist = {int(s): int(c) for s, c in
                         sorted(_Counter(len(p) for p in patterns).items())}
            out = {
                "tag": tag, "k": k, "variant": variant, "objective": objective,
                "pi_star": int(pi_star), "pi_true_check": int(check["pi"]),
                "valid_partition": bool(check["valid"]),
                "num_patterns": len(patterns),
                "pattern_size_histogram": size_hist,
                "total_hits": int(timing.get("total_hits", 0)),
                "max_pattern_size": int(check["max_pattern_size"]),
                "mean_support_size": mean_support,
                "mean_closure_size": mean_closure,
                "c_bar": c_bar,
                "int_optimal": timing.get("int_optimal"),
                "solve_seconds": round(time.time() - t0, 1),
                "patterns": [sorted(p) for p in patterns],
            }
            out_path = os.path.join(out_dir, f"cover_{tag}_k{k}.json")
            with open(out_path, "w") as fh:
                json.dump(out, fh)
            row = {
                "tag": tag, "objective": objective, "K": k,
                "num_patterns": len(patterns), "total_hits": out["total_hits"],
                "pi": int(pi_star), "c_bar": round(c_bar, 4),
                "int_optimal": timing.get("int_optimal"),
            }
            for s in range(1, k + 1):
                row[f"n_size{s}"] = size_hist.get(s, 0)
            comp_rows.append(row)
            if verbose:
                print(f"  cover {tag} k={k} [{objective}]: sets={len(patterns)} "
                      f"hist={size_hist} Pi*={pi_star} total_hits={out['total_hits']} "
                      f"c_bar={c_bar:.3f} opt={timing.get('int_optimal')} "
                      f"{out['solve_seconds']}s", flush=True)

    # Consolidated composition CSV (union of size columns across all K seen).
    if comp_rows:
        size_cols = sorted({c for r in comp_rows for c in r if str(c).startswith("n_size")},
                           key=lambda c: int(c[len("n_size"):]))
        cols = ["tag", "objective", "K", "num_patterns"] + size_cols + \
               ["total_hits", "pi", "c_bar", "int_optimal"]
        comp_path = os.path.join(out_dir, "cover_composition.csv")
        with open(comp_path, "w", newline="") as fh:
            w = _csv.DictWriter(fh, fieldnames=cols)
            w.writeheader()
            for r in comp_rows:
                w.writerow({c: r.get(c, 0) for c in cols})
        if verbose:
            print(f"  wrote cover composition -> {comp_path}")


# ---------------------------------------------------------------------------
#  STAGE 3 -- PLACE  (Hexaly venv)
# ---------------------------------------------------------------------------
def _closure(support: FrozenSet[str], patterns: List[FrozenSet[str]]) -> FrozenSet[str]:
    """Pattern-closure :math:`\\bar P_o = \\bigcup_{q\\cap P_o\\neq\\emptyset} q`."""
    out: set = set()
    for q in patterns:
        if q & support:
            out |= q
    return frozenset(out)


def _placement_orders(
    train_orders: pd.DataFrame,
    top_supports: int,
    patterns: Optional[List[FrozenSet[str]]],
) -> Dict[str, List[str]]:
    """Top-N frequent distinct multi-item train supports (raw, or closures)."""
    sup = _supports(train_orders)
    cnt = Counter(s for s in sup if len(s) >= 2)
    top = cnt.most_common(top_supports) if top_supports else list(cnt.items())
    op: Dict[str, List[str]] = {}
    for i, (s, _c) in enumerate(top):
        order_set = _closure(s, patterns) if patterns is not None else s
        op[f"D{i}"] = sorted(order_set)
    return op


def place(
    manifest_path: str,
    fold_dir: str,
    cover_dir: str,
    out_dir: str,
    k_grid: Sequence[int],
    top_supports: int,
    place_time: int,
    verbose: bool = True,
) -> None:
    r"""Run Hexaly placement per (fold, k) and persist ``{product: station}`` JSON.

    Uses the UNMODIFIED ``milp_synthetic.run_milp_hexaly``; the kappa-invariant
    real pick-lines ``REAL_LINES`` are passed as ``prod_lines`` (a parameter, so no
    baseline edit), and the workload cap is the train stations' ``TIME_CAPACITY``.
    """
    import milp_synthetic as M

    os.makedirs(out_dir, exist_ok=True)
    with open(manifest_path) as fh:
        manifest = json.load(fh)

    for entry in manifest["folds"]:
        tag = entry["tag"]
        train_orders, train_products, train_stations = _read_instance(
            entry["train_prefix"], fold_dir
        )
        products = ("PROD_" + train_products["PRODUCT_ID"].astype(str)).tolist()
        stations = train_stations.to_dict(orient="records")
        prod_lines = _real_prod_lines(train_products)

        for k in k_grid:
            patterns = None
            if k > 1:
                cover_path = os.path.join(cover_dir, f"cover_{tag}_k{k}.json")
                if not os.path.exists(cover_path):
                    if verbose:
                        print(f"  [skip] no cover {os.path.basename(cover_path)}")
                    continue
                with open(cover_path) as fh:
                    patterns = [frozenset(p) for p in json.load(fh)["patterns"]]
            op = _placement_orders(train_orders, top_supports, patterns)
            t0 = time.time()
            result = M.run_milp_hexaly(
                op, stations, products, prod_lines,
                time_limit=place_time, verbosity=0,
            )
            assignment = result[0]
            if assignment is None:
                print(f"  [{tag} k={k}] NO FEASIBLE LAYOUT", flush=True)
                continue
            layout = {str(p): str(s) for p, s in assignment.items()}
            out_path = os.path.join(out_dir, f"layout_{tag}_k{k}.json")
            with open(out_path, "w") as fh:
                json.dump(layout, fh)
            if verbose:
                print(f"  [{tag} k={k}] place_orders={len(op)} "
                      f"train_obj_visits={result[1]} "
                      f"({round(time.time()-t0,1)}s) -> {os.path.basename(out_path)}",
                      flush=True)


# ---------------------------------------------------------------------------
#  STAGE 4 -- EVALUATE + AGGREGATE
# ---------------------------------------------------------------------------
def evaluate(
    manifest_path: str,
    fold_dir: str,
    layout_dir: str,
    cover_dir: str,
    out_dir: str,
    k_grid: Sequence[int],
    verbose: bool = True,
) -> str:
    r"""Score every layout on **real** train + test orders; aggregate folds.

    Writes ``iscf_results/per_fold.csv`` (one row per fold/arm with N, V_te, PoR, G,
    per-station feasibility) and ``iscf_results/summary.csv`` (per k: mean PoR, mean
    G with 95% t-CIs across folds, paired Wilcoxon on the per-fold test-visit
    differences, mean realised enlargement :math:`\bar c`).
    """
    import evaluate_layout_robust as ev

    os.makedirs(out_dir, exist_ok=True)
    with open(manifest_path) as fh:
        manifest = json.load(fh)

    per_fold: List[Dict[str, object]] = []
    for entry in manifest["folds"]:
        tag = entry["tag"]
        # Real train + test order families and stations (for feasibility).
        tr_orders, _tp, stations_df = _read_instance(entry["train_prefix"], fold_dir)
        te_orders, _ep, _es = _read_instance(entry["test_prefix"], fold_dir)
        stations = stations_df.to_dict(orient="records")
        tr_op = tr_orders.groupby("ORDER")["PRODUCT"].apply(list).to_dict()
        te_op = te_orders.groupby("ORDER")["PRODUCT"].apply(list).to_dict()
        tr_lines = tr_orders.groupby("PRODUCT").size().to_dict()
        te_lines = te_orders.groupby("PRODUCT").size().to_dict()

        for k in k_grid:
            layout_path = os.path.join(layout_dir, f"layout_{tag}_k{k}.json")
            if not os.path.exists(layout_path):
                continue
            with open(layout_path) as fh:
                assignment = json.load(fh)
            n_metrics = ev.evaluate_layout(assignment, tr_op, stations, tr_lines)
            t_metrics = ev.evaluate_layout(assignment, te_op, stations, te_lines)
            c_bar = 1.0
            if k > 1:
                cpath = os.path.join(cover_dir, f"cover_{tag}_k{k}.json")
                if os.path.exists(cpath):
                    with open(cpath) as fh:
                        c_bar = float(json.load(fh).get("c_bar", 1.0))
            per_fold.append({
                "tag": tag, "repeat": entry["repeat"], "fold": entry["fold"], "k": k,
                "N_train_visits": n_metrics["total_visits"],
                "V_test_visits": t_metrics["total_visits"],
                "test_mean_per_order": t_metrics["mean_visits_per_order"],
                "coverage_kappa": t_metrics["coverage_kappa"],
                "cap_broken": t_metrics["cap_broken"],
                "wl_broken": t_metrics["wl_broken"],
                "max_workload": t_metrics["max_workload"],
                "workload_std": t_metrics["workload_std"],
                "c_bar": c_bar,
            })

    per_fold_df = pd.DataFrame(per_fold)
    per_fold_path = os.path.join(out_dir, "per_fold.csv")
    per_fold_df.to_csv(per_fold_path, index=False)

    # --- Aggregate: PoR/G per fold vs k=1, then across folds. ----------------
    summary = _aggregate(per_fold_df, k_grid)
    summary_path = os.path.join(out_dir, "summary.csv")
    summary.to_csv(summary_path, index=False)
    if verbose:
        print(f"evaluate: wrote {per_fold_path} and {summary_path}")
        with pd.option_context("display.width", 160, "display.max_columns", 20):
            print(summary.to_string(index=False))
    return summary_path


def _aggregate(per_fold_df: pd.DataFrame, k_grid: Sequence[int]) -> pd.DataFrame:
    """Per-k mean PoR/G with 95% t-CI and paired Wilcoxon vs the k=1 baseline."""
    from scipy import stats as st

    base = per_fold_df[per_fold_df["k"] == 1].set_index("tag")
    rows: List[Dict[str, object]] = []
    for k in k_grid:
        sub = per_fold_df[per_fold_df["k"] == k]
        pors: List[float] = []
        gains: List[float] = []
        v0_list: List[float] = []
        vk_list: List[float] = []
        for _, row in sub.iterrows():
            tag = row["tag"]
            if tag not in base.index:
                continue
            n0 = float(base.loc[tag, "N_train_visits"])
            v0 = float(base.loc[tag, "V_test_visits"])
            nk = float(row["N_train_visits"])
            vk = float(row["V_test_visits"])
            if n0 > 0:
                pors.append((nk - n0) / n0)
            if v0 > 0:
                gains.append((v0 - vk) / v0)
            v0_list.append(v0)
            vk_list.append(vk)

        def _ci(vals: List[float]) -> Tuple[float, float, float]:
            a = np.asarray(vals, dtype=float)
            if len(a) == 0:
                return float("nan"), float("nan"), float("nan")
            m = float(a.mean())
            if len(a) < 2:
                return m, float("nan"), float("nan")
            sem = st.sem(a)
            h = sem * st.t.ppf(0.975, len(a) - 1)
            return m, m - h, m + h

        por_m, por_lo, por_hi = _ci(pors)
        g_m, g_lo, g_hi = _ci(gains)
        # Paired Wilcoxon on per-fold (V_te(a0) - V_te(ak)); + gain = robust better.
        wilcoxon_p = float("nan")
        if k != 1 and len(v0_list) >= 1:
            diffs = np.asarray(v0_list) - np.asarray(vk_list)
            if np.any(diffs != 0) and len(diffs) >= 2:
                try:
                    wilcoxon_p = float(st.wilcoxon(v0_list, vk_list).pvalue)
                except ValueError:
                    wilcoxon_p = float("nan")
        rows.append({
            "k": k, "n_folds": len(sub),
            "mean_c_bar": round(float(sub["c_bar"].mean()), 4) if len(sub) else "",
            "mean_PoR": round(por_m, 5), "PoR_lo95": round(por_lo, 5), "PoR_hi95": round(por_hi, 5),
            "mean_G": round(g_m, 5), "G_lo95": round(g_lo, 5), "G_hi95": round(g_hi, 5),
            "wilcoxon_p_Vte": round(wilcoxon_p, 5) if wilcoxon_p == wilcoxon_p else "",
            "mean_N_train": round(float(sub["N_train_visits"].mean()), 1) if len(sub) else "",
            "mean_V_test": round(float(sub["V_test_visits"].mean()), 1) if len(sub) else "",
            "cap_broken_any": int(sub["cap_broken"].sum()) if len(sub) else 0,
            "wl_broken_any": int(sub["wl_broken"].sum()) if len(sub) else 0,
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
#  STAGE 4b -- EVALUATE ON INJECTED-SHIFT TEST SETS (rho sweep)
# ---------------------------------------------------------------------------
def evaluate_shift(
    manifest_path: str,
    fold_dir: str,
    layout_dir: str,
    shift_dir: str,
    out_dir: str,
    k_grid: Sequence[int],
    mode: str,
    rhos: Sequence[float],
    verbose: bool = True,
) -> str:
    r"""Score the trained layouts on the marginal-preserving shifted test sets.

    For each shift magnitude ``rho`` the existing per-fold layouts (trained on the
    real train orders, unchanged) are evaluated on the shifted test orders produced
    by :mod:`iscf_shift_inject` (``{tag}_test_{mode}_r{rho}`` under ``shift_dir``).
    The nominal cost ``N`` is the visits on the real train orders (rho-independent);
    the out-of-sample cost ``V_te`` is on the shifted test. PoR/G are then aggregated
    per (k, rho) with 95% CIs and the paired Wilcoxon, so the tradeoff curve in the
    shift magnitude can be read directly. Because the swaps preserve demand and the
    flat layout, any change in G across rho is pure co-occurrence shift.
    """
    import evaluate_layout_robust as ev

    os.makedirs(out_dir, exist_ok=True)
    with open(manifest_path) as fh:
        manifest = json.load(fh)

    per_fold: List[Dict[str, object]] = []
    for entry in manifest["folds"]:
        tag = entry["tag"]
        tr_orders, _tp, stations_df = _read_instance(entry["train_prefix"], fold_dir)
        stations = stations_df.to_dict(orient="records")
        tr_op = tr_orders.groupby("ORDER")["PRODUCT"].apply(list).to_dict()
        tr_lines = tr_orders.groupby("PRODUCT").size().to_dict()

        # Per-k nominal cost on the real train orders (rho-independent).
        n_train: Dict[int, Optional[int]] = {}
        layouts: Dict[int, Optional[Dict[str, object]]] = {}
        for k in k_grid:
            lp = os.path.join(layout_dir, f"layout_{tag}_k{k}.json")
            if not os.path.exists(lp):
                layouts[k] = None
                n_train[k] = None
                continue
            with open(lp) as fh:
                layouts[k] = json.load(fh)
            n_train[k] = ev.evaluate_layout(layouts[k], tr_op, stations, tr_lines)[
                "total_visits"
            ]

        for rho in rhos:
            te_prefix = f"{tag}_test_{mode}_r{rho}"
            te_path = os.path.join(shift_dir, f"{te_prefix}_orders.csv")
            if not os.path.exists(te_path):
                continue
            te_df = pd.read_csv(te_path, sep=";")
            te_op = te_df.groupby("ORDER")["PRODUCT"].apply(list).to_dict()
            te_lines = te_df.groupby("PRODUCT").size().to_dict()
            # Use the shift-set's own stations file if present (the demand-shift
            # safeguard recomputes a flat TIME_CAPACITY; co-occurrence shifts copy
            # the train stations, so this is identical there).
            te_st_path = os.path.join(shift_dir, f"{te_prefix}_stations.csv")
            te_stations = (
                pd.read_csv(te_st_path, sep=";").to_dict(orient="records")
                if os.path.exists(te_st_path) else stations
            )
            for k in k_grid:
                if layouts[k] is None:
                    continue
                tm = ev.evaluate_layout(layouts[k], te_op, te_stations, te_lines)
                per_fold.append({
                    "tag": tag, "fold": entry["fold"], "k": k, "rho": rho,
                    "N_train_visits": n_train[k],
                    "V_test_visits": tm["total_visits"],
                    "coverage_kappa": tm["coverage_kappa"],
                    "cap_broken": tm["cap_broken"], "wl_broken": tm["wl_broken"],
                    "c_bar": 1.0,
                })

    per_fold_df = pd.DataFrame(per_fold)
    per_path = os.path.join(out_dir, f"per_fold_shift_{mode}.csv")
    per_fold_df.to_csv(per_path, index=False)

    # Aggregate per rho (reusing the per-k aggregator on each rho slice).
    summaries: List[pd.DataFrame] = []
    for rho in sorted(set(per_fold_df["rho"])):
        sub = per_fold_df[per_fold_df["rho"] == rho].copy()
        agg = _aggregate(sub, k_grid)
        agg.insert(0, "rho", rho)
        summaries.append(agg)
    summary = pd.concat(summaries, ignore_index=True) if summaries else pd.DataFrame()
    summary_path = os.path.join(out_dir, f"summary_shift_{mode}.csv")
    summary.to_csv(summary_path, index=False)
    if verbose:
        print(f"evaluate-shift ({mode}): wrote {per_path} and {summary_path}")
        with pd.option_context("display.width", 200, "display.max_columns", 25):
            print(summary.to_string(index=False))
    return summary_path


# ---------------------------------------------------------------------------
#  CLI
# ---------------------------------------------------------------------------
def main() -> None:
    """CLI dispatch for the four staged subcommands."""
    p = argparse.ArgumentParser(description="Staged ISCF K-fold robustness harness.")
    sub = p.add_subparsers(dest="cmd", required=True)

    pf = sub.add_parser("make-folds")
    pf.add_argument("--prefix", default="iscf480")
    pf.add_argument("--dir", default="../../../../iscf_instances")
    pf.add_argument("--out-dir", default=FOLD_DIR_DEFAULT)
    pf.add_argument("--k-folds", type=int, default=5)
    pf.add_argument("--repeats", type=int, default=1)
    pf.add_argument("--seed", type=int, default=12345)
    pf.add_argument("--slack", type=float, default=1.10)
    pf.add_argument("--mode", default="random", choices=["random", "temporal"],
                    help="random i.i.d. K-fold (primary) or temporal early/late "
                         "cuts by ORDER_ID rank (shift test, assumption U1).")
    pf.add_argument("--train-cap", type=int, default=None,
                    help="Sparse-train: sub-sample each fold's train to this many "
                         "orders (universe unchanged). Tests whether sparser train "
                         "lets the closure's transitive affinity beat the direct layout.")

    pc = sub.add_parser("build-covers")
    pc.add_argument("--manifest", required=True)
    pc.add_argument("--fold-dir", default=FOLD_DIR_DEFAULT)
    pc.add_argument("--out-dir", default=COVER_DIR_DEFAULT)
    pc.add_argument("--k", nargs="+", type=int, default=[2, 4])
    pc.add_argument("--variant", default="exact", choices=["exact", "cover"])
    pc.add_argument("--objective", default="minmax", choices=["minmax", "minsum"],
                    help="Cover objective: minmax bottleneck (Pi) or minsum total hits.")
    pc.add_argument("--cover-time", type=float, default=300.0)
    pc.add_argument("--pricing-time", type=float, default=8.0)
    pc.add_argument("--cooccurrence-pairs", type=int, default=3000)
    pc.add_argument("--chunk-seed", action="store_true",
                    help="Enable size-k chunk seeding (default off for ISCF scale).")

    pp = sub.add_parser("place")
    pp.add_argument("--manifest", required=True)
    pp.add_argument("--fold-dir", default=FOLD_DIR_DEFAULT)
    pp.add_argument("--cover-dir", default=COVER_DIR_DEFAULT)
    pp.add_argument("--out-dir", default=LAYOUT_DIR_DEFAULT)
    pp.add_argument("--k", nargs="+", type=int, default=[1, 2, 4])
    pp.add_argument("--top-supports", type=int, default=3000)
    pp.add_argument("--place-time", type=int, default=60)

    pe = sub.add_parser("evaluate")
    pe.add_argument("--manifest", required=True)
    pe.add_argument("--fold-dir", default=FOLD_DIR_DEFAULT)
    pe.add_argument("--layout-dir", default=LAYOUT_DIR_DEFAULT)
    pe.add_argument("--cover-dir", default=COVER_DIR_DEFAULT)
    pe.add_argument("--out-dir", default=RESULT_DIR_DEFAULT)
    pe.add_argument("--k", nargs="+", type=int, default=[1, 2, 4])

    ps = sub.add_parser("evaluate-shift")
    ps.add_argument("--manifest", required=True)
    ps.add_argument("--fold-dir", default=FOLD_DIR_DEFAULT)
    ps.add_argument("--layout-dir", default=LAYOUT_DIR_DEFAULT)
    ps.add_argument("--shift-dir", required=True)
    ps.add_argument("--out-dir", default=RESULT_DIR_DEFAULT)
    ps.add_argument("--k", nargs="+", type=int, default=[1, 2, 3, 4, 6])
    ps.add_argument("--mode", choices=["structured", "unstructured", "demand"], default="structured")
    ps.add_argument("--rhos", nargs="+", type=float, default=[0.0, 0.25, 0.5, 1.0, 2.0])

    args = p.parse_args()
    if args.cmd == "make-folds":
        make_folds(args.prefix, args.dir, args.out_dir, args.k_folds,
                   args.repeats, args.seed, args.slack, mode=args.mode,
                   train_cap=args.train_cap)
    elif args.cmd == "build-covers":
        build_covers(args.manifest, args.fold_dir, args.out_dir, args.k,
                     args.variant, args.cover_time, args.pricing_time,
                     args.cooccurrence_pairs, seed_chunks=args.chunk_seed,
                     objective=args.objective)
    elif args.cmd == "place":
        place(args.manifest, args.fold_dir, args.cover_dir, args.out_dir,
              args.k, args.top_supports, args.place_time)
    elif args.cmd == "evaluate":
        evaluate(args.manifest, args.fold_dir, args.layout_dir, args.cover_dir,
                 args.out_dir, args.k)
    elif args.cmd == "evaluate-shift":
        evaluate_shift(args.manifest, args.fold_dir, args.layout_dir, args.shift_dir,
                       args.out_dir, args.k, args.mode, args.rhos)


if __name__ == "__main__":
    main()
