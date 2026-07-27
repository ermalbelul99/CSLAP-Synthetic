r"""
Planted-affinity order generator for the covering-robustness boundary stress-test.

The real ISCF data is the wrong regime for the covering enlargement (sparse,
stationary, popularity-driven co-occurrence; see reports/9). To find the
parameterized conditions under which the method *does* pay off, we generate
controlled data with an EXPLICIT, strong affinity-community structure and a tunable
structural break between the historical (train, regime A) and future (test,
regime B) periods. Marginals (product popularity, order sizes) are calibrated to
the real data so the instance stays realistic; only the affinity and its drift are
controlled.

Design
------
* **Universe + flat layout.** ``n_products`` SKUs (default 800) over ``n_stations``
  uniform stations whose slots sum to |P| (kappa-invariant, identical to every
  other scenario). Communities are ``comm_size`` SKUs each (default 10), so the
  cover bound ``K=comm_size`` can place one community per set.
* **Popularity.** Per-product Zipf weights (exponent tuned to the real demand Gini
  ~0.77). Communities inherit the summed popularity of their members.
* **Regime A (train) = sparse fragments.** Small orders (sizes ~2-3) that
  under-sample each community's internal co-occurrence, so the *direct* layout
  cannot fully learn the community while the covering closure can recover it.
* **Regime B (test), two drift modes x magnitude ``alpha``:**
  - ``combine`` (predicted to favour the robust layout): future orders **grow
    within the same communities** -- larger orders realising the unseen
    within-community combinations (the closures of the A fragments). ``alpha``
    interpolates the test order size from the train size (alpha=0) to the full
    community size (alpha=1) via a Binomial.
  - ``reassign`` (the control, predicted NOT to help): a fraction ``alpha`` of SKUs
    switch communities in regime B (the stochastic-block reassignment / bridge
    break), then small orders are drawn from the reassigned communities. This
    scatters the train-fit layout for both arms.
  - ``alpha=0`` => B is the same distribution as A (sanity: i.i.d. break-even).

Output: standard semicolon instances ``{tag}_train_*`` / ``{tag}_test_*`` and a
fold-style manifest consumed unchanged by ``run_robustness_iscf.py``.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from collections import Counter
from itertools import combinations
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd


def _gini(x: np.ndarray) -> float:
    x = np.sort(np.asarray(x, dtype=float))
    n = len(x)
    if n == 0 or x.sum() == 0:
        return float("nan")
    return float((n + 1 - 2 * np.cumsum(x).sum() / x.sum()) / n)


def _zipf_weights(n: int, s: float, rng: np.random.RandomState) -> np.ndarray:
    """Per-item Zipf popularity weights (shuffled so rank != community order)."""
    w = 1.0 / np.power(np.arange(1, n + 1), s)
    rng.shuffle(w)
    return w / w.sum()


def _gen_orders(
    n_orders: int,
    comm_of: np.ndarray,           # community id per product
    members: List[np.ndarray],     # product ids per community
    prod_w: np.ndarray,            # per-product popularity
    sizes: np.ndarray,             # one drawn size per order
    p_in: float,
    rng: np.random.RandomState,
) -> List[frozenset]:
    """Draw orders: pick a community by mass, then sample products mostly within it."""
    comm_mass = np.array([prod_w[m].sum() for m in members])
    comm_mass = comm_mass / comm_mass.sum()
    n_comm = len(members)
    n_prod = len(prod_w)
    all_ids = np.arange(n_prod)
    orders: List[frozenset] = []
    for i in range(n_orders):
        c = rng.choice(n_comm, p=comm_mass)
        k = int(sizes[i])
        mem = members[c]
        wm = prod_w[mem] / prod_w[mem].sum()
        chosen: set = set()
        tries = 0
        while len(chosen) < k and tries < 10 * k:
            tries += 1
            if rng.random() < p_in:
                p = mem[rng.choice(len(mem), p=wm)]
            else:
                p = all_ids[rng.choice(n_prod, p=prod_w)]
            chosen.add(int(p))
        if len(chosen) >= 2 or k == 1:
            orders.append(frozenset(f"PROD_{p}" for p in chosen))
    return orders


def _write_instance(
    orders: List[frozenset], universe_ids: List[int], n_stations: int,
    slack: float, out_dir: str, prefix: str,
) -> Tuple[int, int]:
    rows = []
    for oid, s in enumerate(orders, start=1):
        for p in sorted(s):
            rows.append({"ORDER": oid, "PRODUCT": p, "QTY": 1, "STATION": 1})
    odf = pd.DataFrame(rows, columns=["ORDER", "PRODUCT", "QTY", "STATION"])
    real_lines = odf.drop_duplicates(["ORDER", "PRODUCT"]).groupby("PRODUCT")["ORDER"].nunique()
    pdf = pd.DataFrame({"PRODUCT_ID": universe_ids})
    tok = "PROD_" + pdf["PRODUCT_ID"].astype(str)
    pdf["REAL_LINES"] = tok.map(real_lines).fillna(0).astype(int).to_numpy()
    pdf["VOLUME"] = 0
    pdf["FREQUENCY"] = 0
    n_p = len(universe_ids)
    slots = n_p // n_stations
    total = int(pdf["REAL_LINES"].sum())
    tcap = int(math.ceil(slack * total / n_stations))
    sdf = pd.DataFrame({
        "STATION_ID": [f"GARE{4 + i}" for i in range(n_stations)],
        "CAPACITY": slots, "TIME_CAPACITY": tcap, "SPEED": 1.0,
    })
    odf.to_csv(os.path.join(out_dir, f"{prefix}_orders.csv"), index=False, sep=";")
    pdf.to_csv(os.path.join(out_dir, f"{prefix}_products.csv"), index=False, sep=";")
    sdf.to_csv(os.path.join(out_dir, f"{prefix}_stations.csv"), index=False, sep=";")
    return odf["ORDER"].nunique(), tcap


def _within_lift(orders: List[frozenset], comm_of: Dict[str, int], topn: int = 300) -> float:
    """Median lift over observed pairs (sanity: planted affinity => lift >> 1)."""
    freq: Counter = Counter()
    for s in orders:
        freq.update(s)
    n = len(orders)
    top = [p for p, _ in freq.most_common(topn)]
    tset = set(top)
    pc: Counter = Counter()
    for s in orders:
        ts = [p for p in s if p in tset]
        for a, b in combinations(sorted(ts), 2):
            pc[(a, b)] += 1
    lifts = [c * n / (freq[a] * freq[b]) for (a, b), c in pc.items() if freq[a] and freq[b]]
    return float(np.median(lifts)) if lifts else float("nan")


def generate(
    out_dir: str, prefix: str, n_products: int, comm_size: int, n_stations: int,
    n_train: int, n_test: int, p_in: float, zipf_s: float, alphas: List[float],
    modes: List[str], replicates: int, slack: float, seed: int, verbose: bool = True,
) -> str:
    os.makedirs(out_dir, exist_ok=True)
    keep_n = (n_products // n_stations) * n_stations
    universe_ids = list(range(1, keep_n + 1))
    n_comm = keep_n // comm_size
    train_size_w = np.array([0.0, 0.0, 0.5, 0.3, 0.2])  # sizes 1..5: fragments (2-4)

    folds: List[Dict[str, object]] = []
    for rep in range(replicates):
        base_rng = np.random.RandomState(seed + 1000 * rep)
        # Planted communities (contiguous blocks) + product popularity (regime A).
        comm_of = np.repeat(np.arange(n_comm), comm_size)[:keep_n]
        members = [np.where(comm_of == c)[0] for c in range(n_comm)]
        prod_w = _zipf_weights(keep_n, zipf_s, base_rng)

        # Train (regime A): sparse fragments.
        tr_sizes = base_rng.choice(np.arange(1, 6), size=n_train, p=train_size_w)
        train_orders = _gen_orders(n_train, comm_of, members, prod_w, tr_sizes, p_in, base_rng)

        for mode in modes:
            for alpha in alphas:
                tag = f"aff_{mode}_a{alpha}_r{rep}"
                rng = np.random.RandomState(seed + 7919 * rep + int(round(alpha * 1000)) + hash(mode) % 1000)
                if mode == "combine":
                    base = rng.choice(np.arange(1, 6), size=n_test, p=train_size_w)
                    extra = rng.binomial(np.maximum(0, comm_size - base), alpha)
                    te_sizes = np.minimum(comm_size, base + extra)
                    test_orders = _gen_orders(n_test, comm_of, members, prod_w, te_sizes, p_in, rng)
                else:  # reassign
                    comm_b = comm_of.copy()
                    n_move = int(round(alpha * keep_n))
                    if n_move:
                        mv = rng.choice(keep_n, size=n_move, replace=False)
                        comm_b[mv] = rng.choice(n_comm, size=n_move)
                    members_b = [np.where(comm_b == c)[0] for c in range(n_comm)]
                    members_b = [m if len(m) else np.array([rng.choice(keep_n)]) for m in members_b]
                    te_sizes = rng.choice(np.arange(1, 6), size=n_test, p=train_size_w)
                    test_orders = _gen_orders(n_test, comm_b, members_b, prod_w, te_sizes, p_in, rng)

                # alpha=0 in either mode shares the same (no-drift) train; both modes
                # write their own files so the harness folds stay independent.
                ntr, tcap = _write_instance(train_orders, universe_ids, n_stations, slack, out_dir, f"{tag}_train")
                nte, _ = _write_instance(test_orders, universe_ids, n_stations, slack, out_dir, f"{tag}_test")
                folds.append({
                    "repeat": rep, "fold": len(folds), "tag": tag,
                    "train_prefix": f"{tag}_train", "test_prefix": f"{tag}_test",
                    "n_train_orders": int(ntr), "n_test_orders": int(nte),
                    "time_capacity": int(tcap), "mode": mode, "alpha": float(alpha),
                })
                if verbose:
                    cmap = {f"PROD_{p+1}": int(comm_of[p]) for p in range(keep_n)}
                    print(f"  {tag}: train={ntr}(lift~{_within_lift(train_orders,cmap):.1f}) "
                          f"test={nte} mean_te_size="
                          f"{np.mean([len(s) for s in test_orders]):.2f}", flush=True)

    manifest_path = os.path.join(out_dir, f"{prefix}_folds_manifest.json")
    with open(manifest_path, "w") as fh:
        json.dump({"prefix": prefix, "data_dir": out_dir, "n_products": keep_n,
                   "comm_size": comm_size, "n_comm": n_comm, "folds": folds}, fh, indent=2)
    if verbose:
        # demand Gini sanity on the last train.
        fr = Counter()
        for s in train_orders:
            fr.update(s)
        print(f"generate: {len(folds)} cells -> {manifest_path} | "
              f"demand Gini~{_gini(np.array(list(fr.values()))):.3f} | "
              f"|P|={keep_n} comms={n_comm}x{comm_size}")
    return manifest_path


def main() -> None:
    p = argparse.ArgumentParser(description="Planted-affinity order generator (boundary stress-test).")
    p.add_argument("--out-dir", default="iscf_affinity")
    p.add_argument("--prefix", default="aff")
    p.add_argument("--n-products", type=int, default=800)
    p.add_argument("--comm-size", type=int, default=10)
    p.add_argument("--n-stations", type=int, default=8)
    p.add_argument("--n-train", type=int, default=5000)
    p.add_argument("--n-test", type=int, default=5000)
    p.add_argument("--p-in", type=float, default=0.9)
    p.add_argument("--zipf-s", type=float, default=1.1)
    p.add_argument("--alphas", nargs="+", type=float, default=[0.0, 0.25, 0.5, 0.75, 1.0])
    p.add_argument("--modes", nargs="+", default=["combine", "reassign"])
    p.add_argument("--replicates", type=int, default=3)
    p.add_argument("--slack", type=float, default=1.10)
    p.add_argument("--seed", type=int, default=20260624)
    args = p.parse_args()
    generate(args.out_dir, args.prefix, args.n_products, args.comm_size, args.n_stations,
             args.n_train, args.n_test, args.p_in, args.zipf_s, args.alphas, args.modes,
             args.replicates, args.slack, args.seed)


if __name__ == "__main__":
    main()
