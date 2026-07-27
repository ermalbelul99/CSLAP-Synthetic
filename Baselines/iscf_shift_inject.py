r"""
Marginal-preserving co-occurrence-shift injector for the ISCF temporal test.

The ISCF order stream is temporally stationary (train co-occurrence approx test
co-occurrence), so it cannot exhibit the distribution shift hypothesis H1 is meant
to defend against. This tool injects *controlled* co-occurrence shift into the
**test** orders while leaving the demand and the flat warehouse layout untouched,
so the k=1-vs-k>1 robustness comparison stays free of any workload confound.

Why degree-preserving swaps
---------------------------
A per-station workload is :math:`W_s = \sum_{p\to s} L_p / V_s`, and the flat
capacity :math:`T_s = \lceil 1.10\,\sum_p L_p/|S|\rceil` is valid exactly while the
marginal product demands :math:`L_p` are unchanged. We therefore shift the test by
a **degree-preserving swap** (curveball / checkerboard null model): pick two orders
``{A,B}`` and ``{C,D}`` and rewrite them to ``{A,D}`` and ``{C,B}``. Each product's
frequency and each order's size are conserved exactly, so

* :math:`L_p` is invariant  ->  the flat :math:`T_s` stays valid, no station breaks,
  no per-station rebalancing, no workload confound;
* the order-size distribution is invariant;
* but new product pairs now co-occur  ->  genuine co-occurrence shift.

The shift magnitude is a knob ``rho``: the number of accepted swaps is
``round(rho * (#product-order incidences in the test set))``.

Two modes
---------
* ``unstructured`` -- global random swaps. Rewires co-occurrence arbitrarily,
  including across affinity neighbourhoods. This is shift the covering closures
  cannot anticipate from train; it stress-tests robustness against unpredictable
  change.
* ``structured`` -- swaps are restricted so the two exchanged products lie in the
  **same affinity community** (communities are detected from the *train* orders by
  bounded greedy co-occurrence agglomeration, an algorithm independent of the
  min-Pi cover). Test orders then become novel recombinations *consistent with* the
  train affinity structure -- the ``{A,B},{B,C} -> {A,C}`` regime where the closure
  (which captures affinity transitively) is supposed to help. This is the fair
  best-case test of the mechanism.

Outputs one shifted test instance per (fold, rho) in the standard schema, plus a
verification report confirming demand/size invariance and the realised shift.
"""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from itertools import combinations
from typing import Dict, FrozenSet, List, Optional, Tuple

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
#  AFFINITY COMMUNITIES (structured mode) -- bounded greedy agglomeration
# ---------------------------------------------------------------------------
def detect_communities(
    train_supports: List[FrozenSet[str]],
    universe: List[str],
    size_cap: int,
) -> Tuple[Dict[str, str], Dict[str, List[str]]]:
    r"""Cluster products into bounded affinity communities from train co-occurrence.

    Union-find over product pairs processed in descending train co-occurrence,
    merging two communities only while their combined size stays ``<= size_cap``.
    Products that never co-occur (or whose merges are all blocked by the cap) remain
    singletons. This is a deterministic, library-free community detection that is
    independent of the covering construction.

    Returns ``(community_of, members_of)`` mapping each product to its community
    root and each root to its product list.
    """
    pair_count: Counter = Counter()
    for s in train_supports:
        if len(s) >= 2:
            for a, b in combinations(sorted(s), 2):
                pair_count[(a, b)] += 1

    parent = {p: p for p in universe}
    size = {p: 1 for p in universe}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for (a, b), _c in sorted(pair_count.items(), key=lambda kv: -kv[1]):
        if a not in parent or b not in parent:
            continue
        ra, rb = find(a), find(b)
        if ra == rb:
            continue
        if size[ra] + size[rb] <= size_cap:
            if size[ra] < size[rb]:
                ra, rb = rb, ra
            parent[rb] = ra
            size[ra] += size[rb]

    community_of = {p: find(p) for p in universe}
    members_of: Dict[str, List[str]] = {}
    for p, r in community_of.items():
        members_of.setdefault(r, []).append(p)
    return community_of, members_of


# ---------------------------------------------------------------------------
#  SWAP ENGINE (degree-preserving)
# ---------------------------------------------------------------------------
def _rand_from(s: set, rng: np.random.RandomState) -> object:
    """Uniform random element of a set."""
    t = tuple(s)
    return t[rng.randint(len(t))]


def _swap_unstructured(
    orders: List[set], index: Dict[str, set], rng: np.random.RandomState, tries: int = 30
) -> bool:
    """One global degree-preserving swap between two random orders."""
    n = len(orders)
    for _ in range(tries):
        o1 = rng.randint(n)
        o2 = rng.randint(n)
        if o1 == o2:
            continue
        s1, s2 = orders[o1], orders[o2]
        d1 = s1 - s2
        d2 = s2 - s1
        if not d1 or not d2:
            continue
        p1 = _rand_from(d1, rng)
        p2 = _rand_from(d2, rng)
        s1.discard(p1); s1.add(p2)
        s2.discard(p2); s2.add(p1)
        index[p1].discard(o1); index[p1].add(o2)
        index[p2].discard(o2); index[p2].add(o1)
        return True
    return False


def _swap_structured(
    orders: List[set], index: Dict[str, set], community_of: Dict[str, str],
    members_of: Dict[str, List[str]], rng: np.random.RandomState, tries: int = 30
) -> bool:
    """One degree-preserving swap whose two products share an affinity community."""
    n = len(orders)
    for _ in range(tries):
        o1 = rng.randint(n)
        s1 = orders[o1]
        if not s1:
            continue
        p1 = _rand_from(s1, rng)
        members = members_of.get(community_of[p1])
        if not members or len(members) < 2:
            continue
        for _ in range(8):
            p2 = members[rng.randint(len(members))]
            if p2 == p1 or p2 in s1:
                continue
            orders2 = index.get(p2)
            if not orders2:
                continue
            o2 = None
            for _ in range(8):
                cand = _rand_from(orders2, rng)
                if cand != o1 and p1 not in orders[cand]:
                    o2 = cand
                    break
            if o2 is None:
                continue
            s2 = orders[o2]
            s1.discard(p1); s1.add(p2)
            s2.discard(p2); s2.add(p1)
            index[p1].discard(o1); index[p1].add(o2)
            index[p2].discard(o2); index[p2].add(o1)
            return True
    return False


def shift_test(
    test_supports: List[FrozenSet[str]],
    n_swaps: int,
    mode: str,
    rng: np.random.RandomState,
    community_of: Optional[Dict[str, str]] = None,
    members_of: Optional[Dict[str, List[str]]] = None,
) -> Tuple[List[set], int]:
    r"""Apply ``n_swaps`` degree-preserving swaps to the test orders.

    Returns ``(shifted_orders, accepted)`` where ``accepted`` is the number of swaps
    actually performed (some attempts fail when no valid pair is found).
    """
    orders = [set(s) for s in test_supports]
    index: Dict[str, set] = {}
    for i, s in enumerate(orders):
        for p in s:
            index.setdefault(p, set()).add(i)
    accepted = 0
    for _ in range(n_swaps):
        ok = (
            _swap_structured(orders, index, community_of, members_of, rng)
            if mode == "structured"
            else _swap_unstructured(orders, index, rng)
        )
        accepted += int(ok)
    return orders, accepted


# ---------------------------------------------------------------------------
#  ORCHESTRATION
# ---------------------------------------------------------------------------
def _read_supports(prefix: str, data_dir: str) -> Tuple[List[str], List[FrozenSet[str]]]:
    df = pd.read_csv(os.path.join(data_dir, f"{prefix}_orders.csv"), sep=";")
    grp = df.groupby("ORDER")["PRODUCT"].apply(frozenset)
    return list(grp.index), list(grp.values)


def _pairset(supports) -> set:
    out = set()
    for s in supports:
        if len(s) >= 2:
            for a, b in combinations(sorted(s), 2):
                out.add((a, b))
    return out


def inject(
    manifest_path: str,
    fold_dir: str,
    out_dir: str,
    mode: str,
    rhos: List[float],
    community_cap: int,
    seed: int,
    verbose: bool = True,
) -> None:
    r"""Generate shifted test instances for every (fold, rho) and verify them."""
    os.makedirs(out_dir, exist_ok=True)
    with open(manifest_path) as fh:
        manifest = json.load(fh)

    for entry in manifest["folds"]:
        tag = entry["tag"]
        train_ids, train_sup = _read_supports(entry["train_prefix"], fold_dir)
        test_ids, test_sup = _read_supports(entry["test_prefix"], fold_dir)
        universe = sorted({p for s in train_sup for p in s} | {p for s in test_sup for p in s})
        train_pairs = _pairset(train_sup)

        community_of = members_of = None
        if mode == "structured":
            community_of, members_of = detect_communities(train_sup, universe, community_cap)
            n_comm = sum(1 for r, m in members_of.items() if len(m) >= 2)
            in_comm = sum(len(m) for m in members_of.values() if len(m) >= 2)
            if verbose:
                print(f"[{tag}] communities: {n_comm} non-singleton, "
                      f"{in_comm}/{len(universe)} products grouped "
                      f"(cap {community_cap})", flush=True)

        incid = sum(len(s) for s in test_sup)
        # Per-product reference frequency + size multiset for the invariance check.
        ref_freq = Counter(p for s in test_sup for p in s)
        ref_sizes = Counter(len(s) for s in test_sup)
        base_novel = None

        for rho in rhos:
            rng = np.random.RandomState(seed + int(round(rho * 1000)))
            n_swaps = int(round(rho * incid))
            shifted, accepted = shift_test(
                test_sup, n_swaps, mode, rng, community_of, members_of
            )
            # --- invariance + shift verification. ---
            new_freq = Counter(p for s in shifted for p in s)
            new_sizes = Counter(len(s) for s in shifted)
            demand_ok = new_freq == ref_freq
            size_ok = new_sizes == ref_sizes
            shifted_pairs = _pairset(shifted)
            novel = sum(1 for s in shifted if len(s) >= 2
                        for a, b in combinations(sorted(s), 2)) if False else None
            # fraction of shifted multi-item orders novel as exact set vs train
            train_sets = set(train_sup)
            multi = [s for s in shifted if len(s) >= 2]
            order_novel = (
                sum(1 for s in multi if frozenset(s) not in train_sets) / len(multi)
                if multi else float("nan")
            )
            # fraction of shifted distinct pairs NOT in train (co-occurrence shift)
            pair_novel = (
                len(shifted_pairs - train_pairs) / len(shifted_pairs)
                if shifted_pairs else float("nan")
            )
            if rho == 0.0:
                base_novel = pair_novel

            out_prefix = f"{tag}_test_{mode}_r{rho}"
            rows = []
            for oid, s in zip(test_ids, shifted):
                for p in sorted(s):
                    rows.append({"ORDER": f"{oid}", "PRODUCT": p, "QTY": 1, "STATION": 1})
            pd.DataFrame(rows, columns=["ORDER", "PRODUCT", "QTY", "STATION"]).to_csv(
                os.path.join(out_dir, f"{out_prefix}_orders.csv"), index=False, sep=";"
            )
            # Carry products/stations from the fold's test instance (flat layout).
            for kind in ("products", "stations"):
                src = os.path.join(fold_dir, f"{entry['test_prefix']}_{kind}.csv")
                pd.read_csv(src, sep=";").to_csv(
                    os.path.join(out_dir, f"{out_prefix}_{kind}.csv"), index=False, sep=";"
                )

            if not demand_ok or not size_ok:
                raise AssertionError(
                    f"INVARIANCE BROKEN at {out_prefix}: demand_ok={demand_ok} "
                    f"size_ok={size_ok} (degree-preserving swap bug)"
                )
            if verbose:
                print(f"  {out_prefix}: swaps {accepted}/{n_swaps} | "
                      f"demand_invariant={demand_ok} size_invariant={size_ok} | "
                      f"pair_novel_vs_train={pair_novel:.3f} "
                      f"order_novel={order_novel:.3f}", flush=True)


def main() -> None:
    p = argparse.ArgumentParser(
        description="Marginal-preserving co-occurrence shift injector (ISCF temporal)."
    )
    p.add_argument("--manifest", required=True)
    p.add_argument("--fold-dir", required=True)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--mode", choices=["structured", "unstructured"], default="structured")
    p.add_argument("--rhos", nargs="+", type=float, default=[0.0, 0.25, 0.5, 1.0, 2.0])
    p.add_argument("--community-cap", type=int, default=50,
                   help="Max affinity-community size (structured mode).")
    p.add_argument("--seed", type=int, default=777)
    args = p.parse_args()
    inject(args.manifest, args.fold_dir, args.out_dir, args.mode, args.rhos,
           args.community_cap, args.seed)


if __name__ == "__main__":
    main()
