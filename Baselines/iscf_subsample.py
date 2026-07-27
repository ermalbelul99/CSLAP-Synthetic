r"""
Coverage-guaranteed, distribution-preserving down-sample of an ISCF order stream.

Purpose (user request, 2026-06-20): take the full ISCF order file (~419k orders,
4,328 SKUs) and produce a much smaller order file (<= ``--target`` orders, default
10,000) that (i) contains **every** product of the universe at least once and
(ii) preserves the *shape* of the original distribution -- the order-size
distribution and the relative product-popularity ranking -- while keeping the
real ``ORDER_ID`` values so a temporal (early/late) split still makes sense.

Why a naive random sample is wrong here
---------------------------------------
At target/total approx 2.4% sampling, a plain i.i.d. sample misses a large fraction
of mid-/low-frequency products (a median product, ~56 orders, is missed ~34% of
the time), so the universe would not be fully covered. Absolute frequencies cannot
be preserved either -- the most popular SKU appears 39,156 times, which cannot fit
in 10,000 orders. We therefore preserve the **shape**, not the absolute counts:

1. **Coverage skeleton (greedy).** Visit products in ascending frequency; for each
   still-uncovered product, add the order containing it that covers the most
   currently-uncovered products. This guarantees all SKUs appear and is small
   because only 52 SKUs are singletons.
2. **Size-stratified fill.** Fill the remaining budget by sampling orders so the
   final order-size histogram matches the original (same per-size fraction),
   preserving the size distribution and -- in expectation -- the co-occurrence /
   popularity structure among the frequent items the layout actually exploits.

The skeleton slightly over-weights rare products (unavoidable given the coverage
constraint); the fill is the large majority, so the overall shape stays close. The
script reports the size-distribution match and the popularity rank correlation so
the distortion is visible, not hidden.

Output: a standard CSLAP instance ``{out_prefix}_{orders,products,stations}.csv``
in the same schema as :mod:`iscf_adapter`. Universe (products), the 8x541 balanced
station layout, and the κ-invariant capacity are carried over unchanged; only the
order set shrinks. ``REAL_LINES`` and ``TIME_CAPACITY`` are recomputed on the
subsample so the κ-invariant workload reflects the smaller stream.
"""

from __future__ import annotations

import argparse
import math
import os
from typing import Dict, FrozenSet, List, Tuple

import numpy as np
import pandas as pd


def _load(prefix: str, data_dir: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    orders = pd.read_csv(os.path.join(data_dir, f"{prefix}_orders.csv"), sep=";")
    products = pd.read_csv(os.path.join(data_dir, f"{prefix}_products.csv"), sep=";")
    stations = pd.read_csv(os.path.join(data_dir, f"{prefix}_stations.csv"), sep=";")
    return orders, products, stations


def _greedy_coverage(
    order_support: Dict[object, FrozenSet[str]],
    product_orders: Dict[str, List[object]],
    product_freq: Dict[str, int],
    size_cap: int,
) -> List[object]:
    r"""Coverage skeleton covering every product with typical-sized orders.

    Products are processed in ascending frequency so the rare ones (which force a
    specific order) are handled first. For each still-uncovered product the chosen
    order is the one that, **among orders no larger than** ``size_cap`` (a typical
    order, e.g. the original 95th-percentile size), covers the most currently
    uncovered products; if every order of that product exceeds the cap, the
    smallest is taken. Capping the size avoids the long right tail (orders up to
    132 SKUs) inflating the mean, while maximising coverage keeps the skeleton
    small so it perturbs the distribution as little as possible.
    """
    covered: set = set()
    selected: List[object] = []
    selected_set: set = set()
    for product in sorted(product_freq, key=lambda p: product_freq[p]):
        if product in covered:
            continue
        best_oid = None
        best_key = None  # minimise (over_cap_flag, -new_coverage, size)
        for oid in product_orders[product]:
            size = len(order_support[oid])
            key = (1 if size > size_cap else 0, -len(order_support[oid] - covered), size)
            if best_key is None or key < best_key:
                best_key = key
                best_oid = oid
        if best_oid is not None and best_oid not in selected_set:
            selected.append(best_oid)
            selected_set.add(best_oid)
            covered |= order_support[best_oid]
    return selected


def _stratified_fill(
    order_size: Dict[object, int],
    exclude: set,
    n_fill: int,
    seed: int,
) -> List[object]:
    r"""Sample ``n_fill`` orders preserving the order-size distribution.

    Draws from the orders not already in ``exclude``, allocating the per-size quota
    in proportion to each size's share of the *remaining* pool (so the fill matches
    the original size histogram). Deterministic given ``seed``.
    """
    rng = np.random.RandomState(seed)
    remaining = [oid for oid in order_size if oid not in exclude]
    if n_fill <= 0 or not remaining:
        return []
    by_size: Dict[int, List[object]] = {}
    for oid in remaining:
        by_size.setdefault(order_size[oid], []).append(oid)
    total_remaining = len(remaining)
    picked: List[object] = []
    for size, oids in by_size.items():
        quota = int(round(n_fill * len(oids) / total_remaining))
        quota = min(quota, len(oids))
        if quota > 0:
            idx = rng.choice(len(oids), size=quota, replace=False)
            picked.extend(oids[i] for i in idx)
    # Trim or top up to exactly n_fill (rounding drift).
    if len(picked) > n_fill:
        idx = rng.choice(len(picked), size=n_fill, replace=False)
        picked = [picked[i] for i in idx]
    elif len(picked) < n_fill:
        pset = set(picked)
        leftover = [oid for oid in remaining if oid not in pset]
        need = min(n_fill - len(picked), len(leftover))
        if need > 0:
            idx = rng.choice(len(leftover), size=need, replace=False)
            picked.extend(leftover[i] for i in idx)
    return picked


def subsample(
    prefix: str,
    data_dir: str,
    out_prefix: str,
    target: int,
    slack: float,
    seed: int,
    front_load_coverage: bool = False,
    verbose: bool = True,
) -> Dict[str, object]:
    r"""Produce the down-sampled, full-universe instance and report fidelity.

    If ``front_load_coverage`` is set, the ``ORDER`` column is renumbered to a
    synthetic temporal axis in which the **coverage skeleton** (a real set of
    orders covering every product) receives the earliest ranks and the remaining
    (fill) orders follow in their real ``ORDER_ID`` order. Because the skeleton
    (~1.5k orders) is far smaller than half the target, **every** early/late cut
    from 50/50 to 90/10 then has the *entire* product universe on the train side,
    so an out-of-sample test isolates unseen **combinations** of seen products
    rather than the arrival of unseen products. No order is fabricated or
    duplicated: the skeleton orders are real, carry real co-occurrence, and each
    order appears exactly once, so the train/test split stays leakage-free.
    """
    orders, products, stations = _load(prefix, data_dir)
    universe = set("PROD_" + products["PRODUCT_ID"].astype(str))

    grp = orders.groupby("ORDER")["PRODUCT"]
    order_support: Dict[object, FrozenSet[str]] = {
        oid: frozenset(v) for oid, v in grp
    }
    order_size: Dict[object, int] = {o: len(s) for o, s in order_support.items()}
    product_orders: Dict[str, List[object]] = {}
    for oid, sup in order_support.items():
        for p in sup:
            product_orders.setdefault(p, []).append(oid)
    product_freq: Dict[str, int] = {p: len(v) for p, v in product_orders.items()}
    # Universe products absent from the order stream (none for ISCF) still must be
    # representable; they simply will not appear in any order.
    for p in universe:
        product_orders.setdefault(p, [])
        product_freq.setdefault(p, 0)

    # 1) coverage skeleton, 2) size-stratified fill up to the target.
    size_cap = int(pd.Series(order_size).quantile(0.95))  # typical-order cap (~7)
    skeleton = _greedy_coverage(order_support, product_orders, product_freq, size_cap)
    skeleton_set = set(skeleton)
    n_fill = max(0, target - len(skeleton_set))
    fill = _stratified_fill(order_size, skeleton_set, n_fill, seed)
    chosen = list(skeleton_set | set(fill))
    if len(chosen) > target:  # safety (skeleton alone exceeded target)
        rng = np.random.RandomState(seed + 1)
        forced = list(skeleton_set)  # coverage is non-negotiable; trim fill only
        room = max(0, target - len(forced))
        extra = [o for o in chosen if o not in skeleton_set]
        keep = [extra[i] for i in rng.choice(len(extra), size=min(room, len(extra)),
                                              replace=False)] if extra and room else []
        chosen = forced + keep

    sub = orders[orders["ORDER"].isin(set(chosen))].copy()

    # Optional: renumber ORDER so the coverage skeleton occupies the earliest
    # temporal ranks (front-load coverage). The fill keeps its real ORDER_ID
    # order, so the late test orders remain genuinely "future" real orders.
    front_missing = None
    if front_load_coverage:
        skel_real = sorted(skeleton_set)  # real ids, deterministic
        fill_real = sorted(set(chosen) - skeleton_set)
        ordered_real = skel_real + fill_real  # skeleton first, then fill by id
        remap = {rid: rank + 1 for rank, rid in enumerate(ordered_real)}
        sub["ORDER"] = sub["ORDER"].map(remap)
        # Verify the worst-case (50%) cut covers the full universe.
        new_ids = sorted(sub["ORDER"].unique())
        cut50 = set(new_ids[: int(len(new_ids) * 0.5)])
        first_half_products = set(sub[sub["ORDER"].isin(cut50)]["PRODUCT"].unique())
        front_missing = len(set(sub["PRODUCT"].unique()) - first_half_products)

    # Recompute REAL_LINES on the subsample (κ-invariant workload signal).
    sub_Lp = sub.drop_duplicates(["ORDER", "PRODUCT"]).groupby("PRODUCT")["ORDER"].nunique()
    new_products = products.copy()
    tok = "PROD_" + new_products["PRODUCT_ID"].astype(str)
    new_products["REAL_LINES"] = tok.map(sub_Lp).fillna(0).astype(int).to_numpy()

    n_stations = len(stations)
    speed = float(stations["SPEED"].iloc[0])
    total_lines = int(new_products["REAL_LINES"].sum())
    time_cap = int(math.ceil(slack * total_lines / (speed * n_stations)))
    new_stations = stations.copy()
    new_stations["TIME_CAPACITY"] = time_cap

    os.makedirs(data_dir, exist_ok=True)
    op = os.path.join(data_dir, f"{out_prefix}_orders.csv")
    pp = os.path.join(data_dir, f"{out_prefix}_products.csv")
    sp = os.path.join(data_dir, f"{out_prefix}_stations.csv")
    sub.to_csv(op, index=False, sep=";")
    new_products.to_csv(pp, index=False, sep=";")
    new_stations.to_csv(sp, index=False, sep=";")

    # --- Fidelity report. ----------------------------------------------------
    n_orders_sub = sub["ORDER"].nunique()
    covered = set(sub["PRODUCT"].unique())
    full_universe = covered >= universe
    # Order-size distribution comparison.
    orig_sz = pd.Series(order_size)
    sub_sz = sub.groupby("ORDER")["PRODUCT"].size()
    def _shares(s: "pd.Series") -> Dict[int, float]:
        vc = s.value_counts(normalize=True)
        return {int(k): round(float(v), 4) for k, v in vc.sort_index().items() if k <= 6}
    # Popularity rank correlation (Spearman) on shared products.
    orig_rank = pd.Series(product_freq).rank()
    sub_rank = sub_Lp.rank()
    common = orig_rank.index.intersection(sub_rank.index)
    spearman = float(
        np.corrcoef(orig_rank.loc[common].rank(), sub_rank.loc[common].rank())[0, 1]
    ) if len(common) > 1 else float("nan")

    meta = {
        "out_prefix": out_prefix,
        "n_orders": int(n_orders_sub),
        "n_lines": int(len(sub)),
        "n_products_present": int(len(covered)),
        "universe_size": len(universe),
        "full_universe_covered": bool(full_universe),
        "skeleton_orders": int(len(skeleton_set)),
        "fill_orders": int(n_orders_sub - len(skeleton_set)),
        "mean_order_size": round(float(sub_sz.mean()), 3),
        "time_capacity": time_cap,
        "spearman_popularity": round(spearman, 4),
        "front_load_coverage": bool(front_load_coverage),
        "missing_from_first_half": front_missing,
    }
    if verbose:
        print(f"subsample -> '{out_prefix}'")
        print(f"  orders {meta['n_orders']} (skeleton {meta['skeleton_orders']} + "
              f"fill {meta['fill_orders']}), lines {meta['n_lines']}")
        print(f"  products present {meta['n_products_present']}/{meta['universe_size']} "
              f"-> FULL UNIVERSE: {meta['full_universe_covered']}")
        print(f"  mean order size  sub={meta['mean_order_size']}  "
              f"orig={round(float(orig_sz.mean()),3)}")
        print(f"  size shares (1..6)  orig={_shares(orig_sz)}")
        print(f"                       sub={_shares(sub_sz)}")
        print(f"  popularity Spearman rank-corr (sub vs orig): "
              f"{meta['spearman_popularity']}")
        if front_load_coverage:
            print(f"  FRONT-LOAD COVERAGE on: products missing from the 50% train "
                  f"cut = {front_missing} (target 0 -> full universe in every cut)")
        print(f"  TIME_CAPACITY {meta['time_capacity']} (kappa-invariant)")
        print(f"  wrote: {op}\n         {pp}\n         {sp}")
    return meta


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Coverage-guaranteed, distribution-preserving ISCF order down-sample."
    )
    parser.add_argument("--prefix", default="iscf")
    parser.add_argument("--dir", default="../../../../iscf_instances")
    parser.add_argument("--out-prefix", default="iscf10k")
    parser.add_argument("--target", type=int, default=10000,
                        help="Maximum number of orders to keep (default 10000).")
    parser.add_argument("--slack", type=float, default=1.10)
    parser.add_argument("--seed", type=int, default=12345)
    parser.add_argument("--front-load-coverage", action="store_true",
                        help="Renumber ORDER so the coverage skeleton gets the "
                             "earliest temporal ranks -> every 50/50..90/10 cut "
                             "has the full product universe on the train side "
                             "(isolates unseen-combination robustness).")
    args = parser.parse_args()
    subsample(args.prefix, args.dir, args.out_prefix, args.target, args.slack,
              args.seed, front_load_coverage=args.front_load_coverage)


if __name__ == "__main__":
    main()
