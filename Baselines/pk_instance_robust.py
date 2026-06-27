r"""
Enlarged-instance transform :math:`\mathcal{T}` for CSLAP robustness.

Implements the instance mapping of Method Report (``reports/2_method_report.md``)
Section C.3, equations (2) and (10): given the training instance and the P-K
cover :math:`(Q^*, \Pi^*)` produced by :mod:`pk_cover_construction`, it writes a
**replacement** CSLAP instance under prefix ``{prefix}_pkk{k}`` whose orders are
the per-order pattern closures :math:`\bar{P}_o`. The unchanged baseline solvers
then optimise the manuscript objective on this transformed instance, which by the
robust-counterpart identity (Method Report eq. (5)) equals the data-driven static
robust counterpart of the nominal CSLAP.

Transform (Method Report C.3)
-----------------------------
For each training order :math:`o` with product set :math:`P_o`, define the cover
and closure (eq. (2)):

.. math::
    Q(o) = \{q \in Q^* : q \cap P_o \neq \emptyset\}, \qquad
    \bar{P}_o = \bigcup_{q \in Q(o)} q .                                \tag{2}

Outputs (standard semicolon schema, byte-compatible with ``read_data``):

* ``{prefix}_pkk{k}_orders.csv`` -- one pseudo-order ``CORD_{orig}`` per training
  order; one row per :math:`p \in \bar{P}_o` with ``QTY=1``, ``STATION=1``
  (placeholders ignored by ``read_data``). Duplicate closures are **kept** (one
  pseudo-order per original order) so row multiplicity carries the empirical
  frequency weighting into the objective.
* ``{prefix}_pkk{k}_products.csv`` -- carried over unchanged (same universe).
* ``{prefix}_pkk{k}_stations.csv`` -- ``CAPACITY``/``SPEED`` unchanged;
  ``TIME_CAPACITY`` recalibrated per eq. (10):

.. math::
    \bar{T}_s = \Big\lceil 1.10 \cdot
    \frac{\sum_p \bar{L}_p / V_s}{|S|} \Big\rceil \quad \forall s,        \tag{10}

with :math:`\bar{L}_p = |\{o : p \in \bar{P}_o\}|` the transformed pick-line count
(the popularity of :math:`p`'s pattern, :math:`\ge L_p`). For homogeneous speeds
:math:`V_s \equiv V` this is identical across stations, matching the generator's
flat-ceiling rule.

Identity check (k=1)
--------------------
At :math:`k=1` every pattern is a singleton, so :math:`\bar{P}_o = P_o`: the
transform is the identity on order supports. The self-test asserts this exactly.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from collections import defaultdict
from typing import Dict, FrozenSet, List, Optional, Tuple

import pandas as pd

import pk_cover_construction as pk


# ---------------------------------------------------------------------------
#  COVER ACQUISITION (run or load)
# ---------------------------------------------------------------------------
def obtain_cover(
    prefix: str,
    data_dir: str,
    k: int,
    variant: str,
    backend: str,
    master_time_limit: float,
    pricing_time_limit: float,
    cover_json: Optional[str] = None,
    verbose: bool = True,
    cover_max_supports: Optional[int] = None,
    subsample_seed: int = 12345,
    cooccurrence_pairs: int = 0,
) -> Tuple[List[FrozenSet[str]], int, List[FrozenSet[str]], List[str]]:
    r"""Run or load the P-K cover :math:`(Q^*, \Pi^*)` for a training instance.

    Args:
        prefix: Training dataset prefix.
        data_dir: Directory holding the training CSVs.
        k: Maximum pattern size (conservatism knob).
        variant: ``"exact"`` or ``"cover"``.
        backend: Construction backend (``"highs"``/``"hexaly"``/``"auto"``).
        master_time_limit: CG + integer time budget (s).
        pricing_time_limit: Per-pricing time budget (s).
        cover_json: Optional path to a cached cover JSON (from
            :mod:`pk_cover_construction`); if given and present, patterns are
            loaded instead of recomputed.
        verbose: Console progress flag.
        cover_max_supports: **Deviation U7 (documented scalability fallback).** If
            set, cap the number of **distinct** order supports fed to the
            construction at this value, drawn by a **fixed-seed** random subsample
            (Method Report F.6 / U7). The cover is then built over a representative
            subset :math:`O^{tr}_{\neq,\text{sub}}` while the closures (eq. 2) are
            still computed over **all** orders downstream. ``None`` = no cap (use
            the full deduplicated support set, the committed primary path).
        subsample_seed: Fixed RNG seed for the U7 subsample (reproducibility).

    Returns:
        ``(patterns, pi_star, distinct_supports, universe)``.
    """
    supports, universe, distinct = pk.read_supports_from_instance(prefix, data_dir)

    if cover_json and os.path.exists(cover_json):
        with open(cover_json) as fh:
            payload = json.load(fh)
        patterns = [frozenset(p) for p in payload["patterns"]]
        pi_star = int(payload["pi_star"])
        if verbose:
            print(f"  T: loaded cover from {cover_json} (Pi*={pi_star}, "
                  f"{len(patterns)} patterns)")
        return patterns, pi_star, distinct, universe

    # --- Deviation U7: fixed-seed subsample of distinct supports if capped. ---
    cover_distinct = distinct
    cover_supports = supports
    if cover_max_supports is not None and len(distinct) > cover_max_supports:
        import numpy as _np
        rng = _np.random.RandomState(subsample_seed)
        idx = rng.choice(len(distinct), size=cover_max_supports, replace=False)
        cover_distinct = [distinct[i] for i in sorted(idx)]
        # Restrict the (duplicate-bearing) supports to those in the subsample so
        # the pricing linking constraints (8) stay consistent with the cover set.
        keep = set(cover_distinct)
        cover_supports = [s for s in supports if s in keep]
        if verbose:
            print(f"  T: [U7] subsampled distinct supports "
                  f"{len(distinct)} -> {len(cover_distinct)} "
                  f"(seed={subsample_seed})")

    patterns, pi_star, _ = pk.run_pk_cover(
        cover_supports, universe, cover_distinct,
        k=k, variant=variant,
        master_time_limit=master_time_limit,
        pricing_time_limit=pricing_time_limit,
        backend=backend,
        cooccurrence_pairs=cooccurrence_pairs,
        verbose=verbose,
    )
    return patterns, pi_star, distinct, universe


# ---------------------------------------------------------------------------
#  CLOSURE COMPUTATION (eq. 2)
# ---------------------------------------------------------------------------
def compute_closures(
    order_supports: List[FrozenSet[str]],
    patterns: List[FrozenSet[str]],
) -> List[FrozenSet[str]]:
    r"""Compute the per-order pattern closures :math:`\bar{P}_o` (eq. (2)).

    Args:
        order_supports: One support :math:`P_o` per training order (duplicates
            kept; order preserved so ``CORD_{i}`` aligns with the i-th order).
        patterns: The pattern family :math:`Q^*`.

    Returns:
        One closure frozenset per input order, in the same order.
    """
    closures: List[FrozenSet[str]] = []
    for support in order_supports:
        closure: set = set()
        for q in patterns:
            if q & support:
                closure |= q
        closures.append(frozenset(closure))
    return closures


# ---------------------------------------------------------------------------
#  TRANSFORM  T  (Method Report C.3)
# ---------------------------------------------------------------------------
def transform_instance(
    prefix: str,
    data_dir: str,
    k: int,
    variant: str = "exact",
    backend: str = "auto",
    master_time_limit: float = 600.0,
    pricing_time_limit: float = 30.0,
    cover_json: Optional[str] = None,
    out_dir: Optional[str] = None,
    slack: float = 1.10,
    verbose: bool = True,
    cover_max_supports: Optional[int] = None,
    cooccurrence_pairs: int = 0,
) -> Dict[str, object]:
    r"""Write the enlarged CSLAP instance :math:`\mathcal{T}(\text{instance})`.

    Reads the training CSVs (with the **original** per-order supports, duplicates
    kept), obtains the cover, computes closures (eq. (2)), and writes the three
    transformed CSV files under ``{prefix}_pkk{k}`` (eq. (10) for stations).

    Args:
        prefix: Training dataset prefix.
        data_dir: Directory of the training CSVs (also default output dir).
        k: Maximum pattern size.
        variant: ``"exact"`` (primary) or ``"cover"`` (sensitivity arm).
        backend: Construction backend.
        master_time_limit: CG + integer budget (s).
        pricing_time_limit: Per-pricing budget (s).
        cover_json: Optional cached cover JSON to load instead of recomputing.
        out_dir: Output directory (defaults to ``data_dir``).
        slack: Workload slack factor in eq. (10) (default 1.10, the generator's).
        verbose: Console progress flag.

    Returns:
        Metadata dict: output prefix, file paths, ``pi_star``, closure-size
        statistics, and the recalibrated ``time_capacity``.
    """
    out_dir = out_dir or data_dir
    out_prefix = f"{prefix}_pkk{k}"

    # --- Read original orders with duplicates preserved, in stable ORDER order.
    orders_df = pd.read_csv(os.path.join(data_dir, f"{prefix}_orders.csv"), sep=";")
    stations_df = pd.read_csv(
        os.path.join(data_dir, f"{prefix}_stations.csv"), sep=";"
    )
    products_df = pd.read_csv(
        os.path.join(data_dir, f"{prefix}_products.csv"), sep=";"
    )

    order_ids: List[str] = []
    order_supports: List[FrozenSet[str]] = []
    for oid, grp in orders_df.groupby("ORDER", sort=False):
        support = frozenset(grp["PRODUCT"])
        if not support:
            continue
        order_ids.append(str(oid))
        order_supports.append(support)

    # --- Obtain cover and closures. -----------------------------------------
    patterns, pi_star, _distinct, universe = obtain_cover(
        prefix, data_dir, k, variant, backend,
        master_time_limit, pricing_time_limit, cover_json, verbose,
        cover_max_supports=cover_max_supports,
        cooccurrence_pairs=cooccurrence_pairs,
    )
    closures = compute_closures(order_supports, patterns)

    # --- Build transformed orders (replacement, duplicates kept). -----------
    rows: List[Dict[str, object]] = []
    bar_L: Dict[str, int] = defaultdict(int)
    for oid, closure in zip(order_ids, closures):
        cord = f"CORD_{oid}"
        for p in sorted(closure):
            rows.append({"ORDER": cord, "PRODUCT": p, "QTY": 1, "STATION": 1})
            bar_L[p] += 1
    transformed_orders = pd.DataFrame(rows, columns=["ORDER", "PRODUCT", "QTY", "STATION"])

    # --- Recalibrate TIME_CAPACITY (eq. 10); CAPACITY/SPEED unchanged. ------
    # eq. (10): bar_T_s = ceil( slack * (sum_p bar_L_p / V_s) / |S| ).
    # With homogeneous V_s the numerator is identical across stations.
    n_stations = len(stations_df)
    new_stations = stations_df.copy()
    new_time_caps = []
    for _, srow in stations_df.iterrows():
        v_s = float(srow["SPEED"]) if float(srow["SPEED"]) > 0 else 1.0
        load = sum(bar_L.get(f"PROD_{pid}", 0) / v_s for pid in products_df["PRODUCT_ID"])
        new_time_caps.append(int(math.ceil(slack * load / n_stations)))
    new_stations["TIME_CAPACITY"] = new_time_caps

    # --- Write outputs. ------------------------------------------------------
    os.makedirs(out_dir, exist_ok=True)
    orders_path = os.path.join(out_dir, f"{out_prefix}_orders.csv")
    products_path = os.path.join(out_dir, f"{out_prefix}_products.csv")
    stations_path = os.path.join(out_dir, f"{out_prefix}_stations.csv")
    transformed_orders.to_csv(orders_path, index=False, sep=";")
    products_df.to_csv(products_path, index=False, sep=";")  # unchanged universe
    new_stations.to_csv(stations_path, index=False, sep=";")

    # --- Degeneracy diagnostics (Stage-5 reviewer item 1). -------------------
    # The achieved enlargement ratio c_bar = mean|closure| / mean|support| and the
    # fraction of orders whose closure STRICTLY contains its support. A transform
    # is DEGENERATE (an effective identity, k>1 == k=1) when essentially no order
    # grows -- the k=4 syn_50sku singleton-collapse the reviewer caught in §0.
    closure_sizes = [len(c) for c in closures]
    support_sizes = [len(s) for s in order_supports]
    mean_closure = (sum(closure_sizes) / len(closure_sizes)) if closure_sizes else 0.0
    mean_support = (sum(support_sizes) / len(support_sizes)) if support_sizes else 0.0
    n_strict = sum(
        1 for sup, clo in zip(order_supports, closures) if clo > sup  # strict superset
    )
    frac_strict = (n_strict / len(closures)) if closures else 0.0
    c_bar = (mean_closure / mean_support) if mean_support > 0 else 1.0
    # k=1 (identity) is non-degenerate by construction (c_bar == 1 is expected and
    # correct there); the degeneracy verdict applies only to enlargement arms k>1.
    degenerate = bool(k > 1 and frac_strict < 0.05)

    meta = {
        "out_prefix": out_prefix,
        "orders_path": orders_path,
        "products_path": products_path,
        "stations_path": stations_path,
        "k": k,
        "variant": variant,
        "pi_star": pi_star,
        "num_patterns": len(patterns),
        "num_orders": len(order_ids),
        "universe_size": len(universe),
        "mean_closure_size": mean_closure,
        "mean_support_size": mean_support,
        "max_closure_size": max(closure_sizes, default=0),
        "frac_strict_growth": frac_strict,
        "c_bar": c_bar,
        "degenerate": degenerate,
        "new_time_capacity": new_time_caps[0] if new_time_caps else None,
        "orig_time_capacity": int(stations_df["TIME_CAPACITY"].iloc[0])
        if n_stations else None,
        "cover_max_supports": cover_max_supports,
    }
    # Persist the transform meta JSON next to the instance (reviewer item 1).
    meta_path = os.path.join(out_dir, f"{out_prefix}_meta.json")
    with open(meta_path, "w") as fh:
        json.dump(meta, fh, indent=2)
    meta["meta_path"] = meta_path

    if verbose:
        print(
            f"  T: wrote {out_prefix} | Pi*={pi_star} | "
            f"mean|closure|={mean_closure:.2f} (support {mean_support:.2f}) | "
            f"c_bar={c_bar:.3f} frac_strict={frac_strict:.3f} | "
            f"max|closure|={meta['max_closure_size']} | "
            f"T_s {meta['orig_time_capacity']} -> {meta['new_time_capacity']}"
        )
        if degenerate:
            print(
                f"  T: [DEGENERATE] k={k} arm has only {frac_strict:.1%} of "
                f"orders with strict closure growth (c_bar={c_bar:.3f}); this is "
                f"an effective identity transform and will be EXCLUDED from the "
                f"summary CSV. Reduce --cover-max-supports / enrich the column "
                f"pool to recover genuine enlargement.",
                flush=True,
            )
    return meta


# ---------------------------------------------------------------------------
#  SELF-TEST  (k=1 identity, Method Report C.3)
# ---------------------------------------------------------------------------
def self_test_identity(prefix: str, data_dir: str, backend: str = "highs") -> bool:
    r"""Assert that :math:`k=1` reproduces the original order supports exactly.

    Builds the transform at :math:`k=1` and checks that every transformed
    pseudo-order's product set equals the original order's support
    (:math:`\bar{P}_o = P_o`), as required by Method Report C.3.

    Returns:
        ``True`` if the identity holds for every order.
    """
    orders_df = pd.read_csv(os.path.join(data_dir, f"{prefix}_orders.csv"), sep=";")
    orig: Dict[str, FrozenSet[str]] = {}
    for oid, grp in orders_df.groupby("ORDER", sort=False):
        orig[str(oid)] = frozenset(grp["PRODUCT"])

    meta = transform_instance(
        prefix, data_dir, k=1, variant="exact", backend=backend,
        master_time_limit=120, pricing_time_limit=15, verbose=False,
    )
    t_orders = pd.read_csv(meta["orders_path"], sep=";")
    trans: Dict[str, FrozenSet[str]] = {}
    for oid, grp in t_orders.groupby("ORDER", sort=False):
        trans[str(oid)] = frozenset(grp["PRODUCT"])

    ok = True
    for oid, support in orig.items():
        cord = f"CORD_{oid}"
        if trans.get(cord) != support:
            ok = False
            break
    return ok


# ---------------------------------------------------------------------------
#  CLI
# ---------------------------------------------------------------------------
def main() -> None:
    """CLI entry point: build the enlarged instance for one (prefix, k)."""
    parser = argparse.ArgumentParser(
        description="Enlarged-instance transform T (Method Report C.3, eqs. 2,10)."
    )
    parser.add_argument("--prefix", type=str, required=True)
    parser.add_argument("--dir", type=str, default="synthetic_datasets")
    parser.add_argument("--time", type=int, default=600,
                        help="Construction CG + integer time budget (s).")
    parser.add_argument("--pricing-time", type=float, default=30.0)
    parser.add_argument("--k", type=int, default=6)
    parser.add_argument("--variant", type=str, default="exact",
                        choices=["exact", "cover"])
    parser.add_argument("--backend", type=str, default="auto",
                        choices=["auto", "highs", "hexaly"])
    parser.add_argument("--cover-json", type=str, default=None,
                        help="Optional cached cover JSON to load instead of "
                             "recomputing the construction.")
    parser.add_argument("--out-dir", type=str, default=None)
    parser.add_argument("--cover-max-supports", type=int, default=None,
                        help="Deviation U7: cap distinct supports fed to the "
                             "construction (fixed-seed subsample).")
    parser.add_argument("--cooccurrence-pairs", type=int, default=0,
                        help="Reviewer item 2: seed N greedy co-occurrence "
                             "merges of sizes 2..k into the column pool.")
    parser.add_argument("--self-test", action="store_true",
                        help="Run the k=1 identity self-test and exit.")
    args = parser.parse_args()

    if args.self_test:
        ok = self_test_identity(args.prefix, args.dir, backend=args.backend)
        print(f"[self-test] k=1 identity holds: {ok}")
        raise SystemExit(0 if ok else 1)

    transform_instance(
        args.prefix, args.dir, k=args.k, variant=args.variant,
        backend=args.backend, master_time_limit=float(args.time),
        pricing_time_limit=args.pricing_time, cover_json=args.cover_json,
        out_dir=args.out_dir,
        cover_max_supports=args.cover_max_supports,
        cooccurrence_pairs=args.cooccurrence_pairs,
    )


if __name__ == "__main__":
    main()
