"""Verify, instance by instance, WHY two of the heuristic's four thresholds are inert.

EXP-02a measured that rescaling the frequency floor phi or the co-occurrence floor
gamma from x0.5 to x2 leaves the output bit-identical. A measured null is weak
evidence: it says nothing about a new site. This script checks the STRUCTURAL
reason instead, so the article can state a condition a warehouse can test on its
own order history rather than an empirical accident of one generator.

The filter chain is
    (1) P*    = { p : freq(p) >= phi }
    (2) pairs with cnt_ij >= gamma
    (3) pairs with cnt_ij / max(cnt_i, cnt_j) >= r
and the two dominance conditions are

    D1  phi is inert   <=>  phi <= min_p freq(p)
        (exact: no product is removed, so P* = P)

    D2  gamma is inert  <=>  gamma <= r * min { max(cnt_i, cnt_j) : pair survives (3) }
        (exact: every pair the ratio test keeps already clears gamma, so the
         count floor never removes a pair the ratio floor would have kept)

D2's right-hand side needs the surviving pairs, so it is computed by replaying
steps (1)-(3). A cheaper, conservative surrogate is r * min_p freq(p), which
LOWER-bounds the exact threshold; where the surrogate certifies inertness the
exact condition certainly holds, but the surrogate can be inconclusive while the
exact condition still holds, and both are reported so the article can be precise
about which claim is being made at which catalogue size.

Usage
-----
cd CSLAP-Synthetic
python Baselines/verify_threshold_dominance.py
python Baselines/verify_threshold_dominance.py --sizes 50 500
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from collections import defaultdict
from itertools import combinations
from typing import Dict, List, Optional, Sequence

import numpy as np
import pandas as pd

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

import heuristic_synthetic as H  # noqa: E402

_INST_RE = re.compile(r"^syn_(\d+)sku_seed(\d+)$")


def analyse(inst_dir: str, prefix: str, size_n: int, seed: int) -> Dict[str, object]:
    order_prods, _stations, products, prod_lines, _odf = H.read_data(prefix, inst_dir)
    N = len(products)
    phi = max(2, N // 100)
    gamma = max(2, N // 50)
    r = 0.1

    freqs = np.array([prod_lines.get(p, 0) for p in products], dtype=float)
    min_freq = float(freqs.min())

    # (1) exactly as the heuristic does it
    p_star = {p for p, f in prod_lines.items() if f >= phi}

    # (2)-(3) replayed on the SAME pair construction
    pair_counts: Dict[tuple, int] = defaultdict(int)
    for _o, prods in order_prods.items():
        filtered = [p for p in set(prods) if p in p_star]
        if len(filtered) < 2:
            continue
        for p1, p2 in combinations(sorted(filtered), 2):
            pair_counts[(p1, p2)] += 1

    kept_by_ratio: List[float] = []      # max(cnt_i,cnt_j) of pairs surviving (3)
    n_kept_ratio_only = 0
    n_removed_by_gamma_alone = 0
    for (p1, p2), cnt in pair_counts.items():
        denom = max(prod_lines.get(p1, 1), prod_lines.get(p2, 1))
        passes_ratio = (cnt / denom) >= r
        passes_gamma = cnt >= gamma
        if passes_ratio:
            n_kept_ratio_only += 1
            kept_by_ratio.append(float(denom))
            if not passes_gamma:
                # gamma removes a pair the ratio test would have kept => it binds
                n_removed_by_gamma_alone += 1

    exact_bound = r * min(kept_by_ratio) if kept_by_ratio else float("nan")
    surrogate_bound = r * min_freq

    return {
        "size_n": size_n, "seed": seed, "N": N,
        "phi": phi, "gamma": gamma, "r": r,
        "min_product_freq": min_freq,
        "n_pstar": len(p_star), "n_products": N,
        "D1_phi_inert": len(p_star) == N,
        "D1_margin": min_freq / phi,
        "gamma_exact_bound": exact_bound,
        "D2_gamma_inert_exact": bool(gamma <= exact_bound),
        "D2_exact_margin": exact_bound / gamma,
        "gamma_surrogate_bound": surrogate_bound,
        "D2_surrogate_certifies": bool(gamma <= surrogate_bound),
        "D2_surrogate_margin": surrogate_bound / gamma,
        "n_pairs_kept_by_ratio": n_kept_ratio_only,
        "n_pairs_gamma_would_remove": n_removed_by_gamma_alone,
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--instance-dir", type=str, default="exp02a_instances")
    p.add_argument("--sizes", nargs="+", type=int, default=None)
    p.add_argument("--out", type=str, default="exp02a_results/threshold_dominance.csv")
    args = p.parse_args(argv)

    rows: List[Dict[str, object]] = []
    names = sorted(os.listdir(args.instance_dir))
    for name in names:
        m = _INST_RE.match(name)
        if not m:
            continue
        size_n, seed = int(m.group(1)), int(m.group(2))
        if args.sizes is not None and size_n not in args.sizes:
            continue
        print(f"[{name}] ...", flush=True)
        rows.append(analyse(os.path.join(args.instance_dir, name),
                            f"syn_{size_n}sku", size_n, seed))

    df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    df.to_csv(args.out, index=False)

    print("\n=== D1: frequency floor phi ===")
    print(df.groupby("size_n").agg(
        K=("seed", "count"), phi=("phi", "first"),
        min_freq=("min_product_freq", "min"),
        all_inert=("D1_phi_inert", "all"),
        worst_margin=("D1_margin", "min")).to_string())

    print("\n=== D2: co-occurrence floor gamma ===")
    print(df.groupby("size_n").agg(
        K=("seed", "count"), gamma=("gamma", "first"),
        exact_inert=("D2_gamma_inert_exact", "all"),
        worst_exact_margin=("D2_exact_margin", "min"),
        surrogate_certifies=("D2_surrogate_certifies", "all"),
        worst_surrogate_margin=("D2_surrogate_margin", "min"),
        pairs_gamma_removes=("n_pairs_gamma_would_remove", "max")).to_string())

    print(f"\n[out] {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
