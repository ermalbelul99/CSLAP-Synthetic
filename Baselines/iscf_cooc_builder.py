r"""
Co-occurrence-rich CSLAP instance builder derived from the real ISCF orders.

The standard ISCF stream is 55% singletons (zero co-occurrence value) and its
co-occurrence is sparse over the full 4,328-SKU universe (median product appears in
only ~38 multi-item orders). For a robustness test we want a **dense, learnable**
co-occurrence structure with **few singletons**, while keeping the data grounded in
the real orders. This builder produces such an instance:

1. **Dense universe.** Keep the ``--n-products`` SKUs with the highest *multi-item*
   order frequency (rounded to a multiple of ``--n-stations`` for a balanced flat
   layout). Trimming the rare tail multiplies the median per-product co-occurrence
   (e.g. top-1600 -> median ~158 vs 38 over all 4,328) while retaining almost every
   multi-item order (they are built from frequent SKUs).
2. **Restrict + sample.** Restrict every order to the kept universe. Sample
   ``--n-orders`` orders with a **capped singleton fraction** ``--singleton-frac``
   (default 0.20, well under a 30% ceiling): the multi-item quota is drawn from the
   real multi-item orders (preserving co-occurrence and the multi-item size
   distribution), the singleton quota from real singletons.
3. **Coverage, front-loaded.** A greedy multi-item coverage skeleton guarantees
   every kept SKU appears, and is assigned the earliest synthetic ``ORDER`` ids so
   that every temporal cut from 50/50 to 90/10 has the full universe on the train
   side (isolating unseen-combination / demand robustness, not unseen products).
4. **Flat, kappa-invariant layout.** ``--n-stations`` uniform stations whose slot
   counts sum exactly to the kept SKU count; ``REAL_LINES`` (per-product pick lines)
   and a flat ``TIME_CAPACITY`` are recomputed from the sampled orders, so the
   workload is kappa-invariant and the layout stays balanced.

Output: ``{out_prefix}_{orders,products,stations}.csv`` in the standard schema,
plus a verification report (size histogram, singleton %, coverage, median
co-occurrence, distinct multi-supports).
"""

from __future__ import annotations

import argparse
import math
import os
from collections import Counter
from typing import Dict, FrozenSet, List, Tuple

import numpy as np
import pandas as pd


def _greedy_cover(
    pool_supports: Dict[object, FrozenSet[str]],
    universe: set,
    size_cap: int,
) -> List[object]:
    """Greedy multi-item coverage skeleton over ``universe`` (small orders preferred)."""
    covered: set = set()
    selected: List[object] = []
    # Index product -> orders (within the pool) containing it.
    prod_orders: Dict[str, List[object]] = {}
    for oid, s in pool_supports.items():
        for p in s:
            prod_orders.setdefault(p, []).append(oid)
    # Process products by ascending pool frequency (rare first).
    order_by_rarity = sorted(universe, key=lambda p: len(prod_orders.get(p, [])))
    chosen: set = set()
    for p in order_by_rarity:
        if p in covered:
            continue
        best = None
        best_key = None
        for oid in prod_orders.get(p, []):
            s = pool_supports[oid]
            key = (1 if len(s) > size_cap else 0, -len(s - covered), len(s))
            if best_key is None or key < best_key:
                best_key, best = key, oid
        if best is not None and best not in chosen:
            chosen.add(best)
            selected.append(best)
            covered |= pool_supports[best]
    return selected


def build(
    orders_path: str,
    products_path: str,
    out_dir: str,
    out_prefix: str,
    n_products: int,
    n_orders: int,
    singleton_frac: float,
    n_stations: int,
    slack: float,
    seed: int,
    verbose: bool = True,
) -> Dict[str, object]:
    rng = np.random.RandomState(seed)
    orders = pd.read_csv(orders_path, sep=";")
    products_full = pd.read_csv(products_path, sep=";")

    supports = orders.groupby("ORDER")["PRODUCT"].apply(frozenset).to_dict()

    # 1) dense universe: top SKUs by multi-item order frequency, multiple of n_stations.
    multi_freq: Counter = Counter()
    for s in supports.values():
        if len(s) >= 2:
            multi_freq.update(s)
    keep_n = (min(n_products, len(multi_freq)) // n_stations) * n_stations
    universe = set(p for p, _c in multi_freq.most_common(keep_n))

    # 2) restrict every order to the universe; split into multi / singleton pools.
    multi_pool: Dict[object, FrozenSet[str]] = {}
    singleton_pool: List[object] = []
    restricted: Dict[object, FrozenSet[str]] = {}
    for oid, s in supports.items():
        r = s & universe
        if len(r) >= 2:
            restricted[oid] = r
            multi_pool[oid] = r
        elif len(r) == 1:
            restricted[oid] = r
            singleton_pool.append(oid)

    n_singleton = int(round(singleton_frac * n_orders))
    n_multi = n_orders - n_singleton

    # 3) coverage skeleton (multi-item) guaranteeing every kept SKU appears.
    size_cap = 7
    skeleton = _greedy_cover(multi_pool, universe, size_cap)
    skeleton_set = set(skeleton)

    # 4) fill the multi quota with a random sample of the remaining multi pool.
    remaining_multi = [o for o in multi_pool if o not in skeleton_set]
    n_extra = max(0, n_multi - len(skeleton_set))
    take = min(n_extra, len(remaining_multi))
    extra_idx = rng.choice(len(remaining_multi), size=take, replace=False) if take else []
    extra_multi = [remaining_multi[i] for i in extra_idx]
    chosen_multi = list(skeleton_set) + extra_multi

    # 5) singleton quota (random sample of singleton pool).
    take_s = min(n_singleton, len(singleton_pool))
    s_idx = rng.choice(len(singleton_pool), size=take_s, replace=False) if take_s else []
    chosen_singleton = [singleton_pool[i] for i in s_idx]

    # 6) assemble + assign a synthetic temporal axis: coverage skeleton first
    #    (earliest ids), then the rest shuffled (demand-shift is injected later, so
    #    the non-skeleton order is arbitrary but full-universe coverage sits early).
    rest = [o for o in chosen_multi if o not in skeleton_set] + chosen_singleton
    rng.shuffle(rest)
    ordered = skeleton + rest
    new_id = {oid: i + 1 for i, oid in enumerate(ordered)}

    rows: List[Dict[str, object]] = []
    for oid in ordered:
        nid = new_id[oid]
        for p in sorted(restricted[oid]):
            rows.append({"ORDER": nid, "PRODUCT": p, "QTY": 1, "STATION": 1})
    orders_out = pd.DataFrame(rows, columns=["ORDER", "PRODUCT", "QTY", "STATION"])

    # 7) products file (REAL_LINES recomputed on chosen orders; VOLUME/FREQUENCY carried).
    real_lines = orders_out.drop_duplicates(["ORDER", "PRODUCT"]).groupby("PRODUCT")["ORDER"].nunique()
    universe_ids = sorted(int(p[len("PROD_"):]) for p in universe)
    attrs = products_full.set_index("PRODUCT_ID")
    prod_rows = []
    for pid in universe_ids:
        tok = f"PROD_{pid}"
        prod_rows.append({
            "PRODUCT_ID": pid,
            "REAL_LINES": int(real_lines.get(tok, 0)),
            "VOLUME": attrs["VOLUME"].get(pid, 0) if "VOLUME" in attrs else 0,
            "FREQUENCY": attrs["FREQUENCY"].get(pid, 0) if "FREQUENCY" in attrs else 0,
        })
    products_out = pd.DataFrame(prod_rows)

    # 8) flat stations: n_stations x (|P|/n_stations) slots; kappa-invariant T_s.
    n_p = len(universe_ids)
    if n_p % n_stations != 0:
        raise AssertionError(f"|P|={n_p} not divisible by n_stations={n_stations}")
    slots = n_p // n_stations
    total_lines = int(products_out["REAL_LINES"].sum())
    time_cap = int(math.ceil(slack * total_lines / n_stations))
    stations_out = pd.DataFrame({
        "STATION_ID": [f"GARE{4 + i}" for i in range(n_stations)],
        "CAPACITY": slots, "TIME_CAPACITY": time_cap, "SPEED": 1.0,
    })

    os.makedirs(out_dir, exist_ok=True)
    op = os.path.join(out_dir, f"{out_prefix}_orders.csv")
    pp = os.path.join(out_dir, f"{out_prefix}_products.csv")
    sp = os.path.join(out_dir, f"{out_prefix}_stations.csv")
    orders_out.to_csv(op, index=False, sep=";")
    products_out.to_csv(pp, index=False, sep=";")
    stations_out.to_csv(sp, index=False, sep=";")

    # --- Verification report. ------------------------------------------------
    sz = orders_out.groupby("ORDER")["PRODUCT"].size()
    n_tot = orders_out["ORDER"].nunique()
    n_single = int((sz == 1).sum())
    present = set(orders_out["PRODUCT"].unique())
    sup_final = orders_out.groupby("ORDER")["PRODUCT"].apply(frozenset)
    d_multi = len({s for s in sup_final if len(s) >= 2})
    lp = orders_out.groupby("PRODUCT")["ORDER"].nunique()
    # coverage in the first 50% (temporal-cut guarantee).
    ids_sorted = sorted(orders_out["ORDER"].unique())
    half = set(ids_sorted[: len(ids_sorted) // 2])
    half_products = set(orders_out[orders_out["ORDER"].isin(half)]["PRODUCT"].unique())
    meta = {
        "out_prefix": out_prefix, "n_products": n_p, "n_orders": n_tot,
        "n_lines": len(orders_out), "mean_order_size": round(float(sz.mean()), 3),
        "singleton_frac": round(n_single / n_tot, 4),
        "skeleton_orders": len(skeleton_set),
        "full_universe_covered": bool(present >= universe),
        "missing_from_first_half": len(universe - half_products),
        "median_cooc": int(lp.median()), "mean_cooc": round(float(lp.mean()), 1),
        "distinct_multi_supports": d_multi, "slots_per_station": slots,
        "time_capacity": time_cap,
    }
    if verbose:
        print(f"cooc-builder -> '{out_prefix}'")
        print(f"  products {n_p} ({n_stations}x{slots}) | orders {n_tot} "
              f"(skeleton {len(skeleton_set)}) | lines {len(orders_out)}")
        print(f"  mean size {meta['mean_order_size']} | SINGLETON frac "
              f"{meta['singleton_frac']:.1%} | full universe {meta['full_universe_covered']} "
              f"| missing@50%cut {meta['missing_from_first_half']}")
        print(f"  per-product co-occurrence: median {meta['median_cooc']} "
              f"mean {meta['mean_cooc']} | distinct multi-supports {d_multi}")
        print(f"  size hist (1..8): "
              f"{ {int(s): int(c) for s, c in sz.value_counts().sort_index().items() if s <= 8} }")
        print(f"  TIME_CAPACITY {time_cap} (flat, kappa-invariant)")
        print(f"  wrote: {op}\n         {pp}\n         {sp}")
    return meta


def main() -> None:
    p = argparse.ArgumentParser(description="Co-occurrence-rich ISCF-derived instance builder.")
    p.add_argument("--orders", default="../../../../iscf_instances/iscf_orders.csv")
    p.add_argument("--products", default="../../../../iscf_instances/iscf_products.csv")
    p.add_argument("--out-dir", default="../../../../iscf_instances")
    p.add_argument("--out-prefix", default="iscfco")
    p.add_argument("--n-products", type=int, default=1600)
    p.add_argument("--n-orders", type=int, default=15000)
    p.add_argument("--singleton-frac", type=float, default=0.20)
    p.add_argument("--n-stations", type=int, default=8)
    p.add_argument("--slack", type=float, default=1.10)
    p.add_argument("--seed", type=int, default=20260622)
    args = p.parse_args()
    build(args.orders, args.products, args.out_dir, args.out_prefix, args.n_products,
          args.n_orders, args.singleton_frac, args.n_stations, args.slack, args.seed)


if __name__ == "__main__":
    main()
