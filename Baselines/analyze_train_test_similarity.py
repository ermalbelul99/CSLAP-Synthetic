r"""
Train (history) vs test (future) similarity study for the temporal folds.

Diagnoses *why* the covering enlargement returns no out-of-sample gain. The robust
(enlarged) layout can only beat the direct layout out of sample when the future
genuinely differs from the past in the structure the layout exploits -- the
**pairwise co-occurrence** of products. If train and test share that structure,
the direct layout is already near-optimal for the future and the enlargement only
pays its price (G < 0). This script quantifies the similarity at several levels so
that "the data has no real shift" can be confirmed or rejected.

Per fold it compares the train and test order families on:

* order-size distribution (mean, and the size histogram);
* product popularity -- Pearson/Spearman correlation of per-product order frequency
  (does the future reorder the same products as often?);
* **pairwise co-occurrence (the load-bearing metric)** -- of all product pairs that
  co-occur in some test order, the fraction whose pair already co-occurs in train
  (unweighted, and weighted by test pair frequency), plus the cosine similarity of
  the train/test pair-frequency vectors and the Jaccard overlap of the pair sets;
* exact-order novelty -- fraction of test multi-item orders whose exact product set
  never appears in train (the "novel combination" rate already seen in evaluation);
* recombination rate -- fraction of test multi-item orders **all of whose pairs are
  already present in train** (orders that are pure recombinations of seen pairs;
  the direct layout already clusters these well, so robustness cannot help them).

A high pairwise-similarity / high-recombination reading means the testbed has no
authentic structural shift and is unsuitable for the robustness test.
"""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from itertools import combinations
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd


def _orders(prefix: str, data_dir: str) -> "pd.Series":
    df = pd.read_csv(os.path.join(data_dir, f"{prefix}_orders.csv"), sep=";")
    return df.groupby("ORDER")["PRODUCT"].apply(frozenset)


def _pairs(supports: "pd.Series") -> Counter:
    c: Counter = Counter()
    for s in supports:
        if len(s) >= 2:
            for a, b in combinations(sorted(s), 2):
                c[(a, b)] += 1
    return c


def _cosine(a: Counter, b: Counter) -> float:
    keys = set(a) | set(b)
    va = np.array([a.get(k, 0) for k in keys], dtype=float)
    vb = np.array([b.get(k, 0) for k in keys], dtype=float)
    na, nb = np.linalg.norm(va), np.linalg.norm(vb)
    return float(va.dot(vb) / (na * nb)) if na > 0 and nb > 0 else float("nan")


def _fold_stats(train: "pd.Series", test: "pd.Series") -> Dict[str, float]:
    tr_sz = train.apply(len)
    te_sz = test.apply(len)

    # Product popularity (frequency) correlation over products present in test.
    tr_freq: Counter = Counter()
    for s in train:
        tr_freq.update(s)
    te_freq: Counter = Counter()
    for s in test:
        te_freq.update(s)
    prods = sorted(te_freq)
    tv = np.array([tr_freq.get(p, 0) for p in prods], dtype=float)
    ev = np.array([te_freq.get(p, 0) for p in prods], dtype=float)
    pop_pearson = float(np.corrcoef(tv, ev)[0, 1]) if len(prods) > 1 else float("nan")
    pop_spearman = (
        float(np.corrcoef(pd.Series(tv).rank(), pd.Series(ev).rank())[0, 1])
        if len(prods) > 1 else float("nan")
    )

    # Pairwise co-occurrence.
    tr_pairs = _pairs(train)
    te_pairs = _pairs(test)
    tr_pair_set = set(tr_pairs)
    te_pair_set = set(te_pairs)
    pair_seen_unw = (
        len(te_pair_set & tr_pair_set) / len(te_pair_set) if te_pair_set else float("nan")
    )
    te_pair_instances = sum(te_pairs.values())
    pair_seen_w = (
        sum(c for k, c in te_pairs.items() if k in tr_pair_set) / te_pair_instances
        if te_pair_instances else float("nan")
    )
    pair_jaccard = (
        len(te_pair_set & tr_pair_set) / len(te_pair_set | tr_pair_set)
        if (te_pair_set or tr_pair_set) else float("nan")
    )
    pair_cosine = _cosine(tr_pairs, te_pairs)

    # Exact-order novelty + recombination (all pairs seen) on multi-item test orders.
    tr_sets = set(train)
    te_multi = [s for s in test if len(s) >= 2]
    novel_set = sum(1 for s in te_multi if s not in tr_sets)
    recomb = sum(
        1 for s in te_multi
        if all(((a, b) in tr_pair_set) for a, b in combinations(sorted(s), 2))
    )
    n_multi = len(te_multi)

    # --- Demand drift (per-product order frequency / line counts L_p). -------
    # pop_pearson/pop_spearman above already correlate per-product frequency
    # train-vs-test (the demand drift). Add concentration and rank-mover stats.
    tr_total = sum(tr_freq.values())
    te_total = sum(te_freq.values())
    top50_tr = (sum(c for _, c in tr_freq.most_common(50)) / tr_total) if tr_total else float("nan")
    top50_te = (sum(c for _, c in te_freq.most_common(50)) / te_total) if te_total else float("nan")
    tr_rank = {p: i for i, (p, _c) in enumerate(tr_freq.most_common())}
    te_rank = {p: i for i, (p, _c) in enumerate(te_freq.most_common())}
    common_p = set(tr_rank) & set(te_rank)
    big_movers = sum(1 for p in common_p if abs(tr_rank[p] - te_rank[p]) > 200)
    big_mover_frac = (big_movers / len(common_p)) if common_p else float("nan")

    return {
        "n_train": int(len(train)), "n_test": int(len(test)),
        "train_mean_size": round(float(tr_sz.mean()), 3),
        "test_mean_size": round(float(te_sz.mean()), 3),
        "pop_pearson": round(pop_pearson, 4),
        "pop_spearman": round(pop_spearman, 4),
        "demand_top50_share_train": round(top50_tr, 4),
        "demand_top50_share_test": round(top50_te, 4),
        "demand_big_movers_frac": round(big_mover_frac, 4),
        "pair_seen_unweighted": round(pair_seen_unw, 4),
        "pair_seen_weighted": round(pair_seen_w, 4),
        "pair_jaccard": round(pair_jaccard, 4),
        "pair_cosine": round(pair_cosine, 4),
        "exact_order_novel_frac": round(novel_set / n_multi, 4) if n_multi else float("nan"),
        "recomb_seen_pairs_frac": round(recomb / n_multi, 4) if n_multi else float("nan"),
        "n_test_multi": n_multi,
    }


def run(manifest_path: str, fold_dir: str) -> None:
    with open(manifest_path) as fh:
        manifest = json.load(fh)
    rows: List[Dict[str, float]] = []
    for entry in manifest["folds"]:
        tr = _orders(entry["train_prefix"], fold_dir)
        te = _orders(entry["test_prefix"], fold_dir)
        st = _fold_stats(tr, te)
        st["tag"] = entry["tag"]
        rows.append(st)
        print(f"[{st['tag']}] train={st['n_train']} test={st['n_test']} "
              f"| size tr={st['train_mean_size']} te={st['test_mean_size']} "
              f"| pop r={st['pop_pearson']} | PAIR seen(w)={st['pair_seen_weighted']} "
              f"cos={st['pair_cosine']} jacc={st['pair_jaccard']} "
              f"| order-novel={st['exact_order_novel_frac']} "
              f"recomb={st['recomb_seen_pairs_frac']}", flush=True)
    df = pd.DataFrame(rows)
    num = df.select_dtypes(include=[float, int]).mean(numeric_only=True)
    print("\n=== MEAN ACROSS FOLDS ===")
    for k in ["pop_pearson", "pop_spearman",
              "demand_top50_share_train", "demand_top50_share_test",
              "demand_big_movers_frac",
              "pair_seen_unweighted", "pair_seen_weighted", "pair_jaccard",
              "pair_cosine", "exact_order_novel_frac", "recomb_seen_pairs_frac"]:
        print(f"  {k:28s} {num[k]:.4f}")
    # Per-fold demand drift line.
    print("\n=== DEMAND DRIFT per fold (top-50 share train->test, big-mover frac) ===")
    for _, r in df.iterrows():
        print(f"  {r['tag']}: top50 {r['demand_top50_share_train']:.3f}->"
              f"{r['demand_top50_share_test']:.3f} | pop r={r['pop_pearson']:.3f} "
              f"| big-movers(>200 ranks)={r['demand_big_movers_frac']:.3f}")


def main() -> None:
    p = argparse.ArgumentParser(description="Train/test similarity diagnostic.")
    p.add_argument("--manifest", required=True)
    p.add_argument("--fold-dir", required=True)
    args = p.parse_args()
    run(args.manifest, args.fold_dir)


if __name__ == "__main__":
    main()
