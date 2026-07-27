r"""
Order-data distributional diagnostics across the tested datasets, with graphs.

Critical question: *why* does the covering-enlargement robustness not pay off?
Since the product universe and the station layout are identical across every
scenario, the answer must live in the **order distribution**. This tool quantifies,
and plots, the properties of the order stream that decide whether (a) the data is a
realistic warehouse demand process and (b) there is exploitable structure for the
robustness construction to leverage:

1. **Order-size distribution** -- realistic warehouses are right-skewed.
2. **Product popularity (Zipf / Pareto)** -- realistic demand is heavy-tailed
   (few SKUs dominate); we report the Gini coefficient and the rank-frequency slope.
3. **Co-occurrence AFFINITY via lift** -- the decisive one. For the most popular
   products we compute, for every pair, ``lift = observed_cooccurrence /
   expected_under_independence`` (expected = freq_a*freq_b/N). lift >> 1 means SKUs
   co-occur because of genuine affinity (market-basket structure the layout can
   exploit); lift ~ 1 means they co-occur only because both are popular (no real
   correlation to exploit). The lift distribution tells us whether CSLAP has a
   strong signal at all, and -- read together with the train/test stationarity
   already measured -- whether robustness has anything to defend against.

Outputs PNG figures to ``reports/figures/`` and prints a comparative table.
"""

from __future__ import annotations

import argparse
import os
from collections import Counter
from itertools import combinations
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def _load(prefix: str, data_dir: str) -> "pd.Series":
    df = pd.read_csv(os.path.join(data_dir, f"{prefix}_orders.csv"), sep=";")
    return df.groupby("ORDER")["PRODUCT"].apply(frozenset)


def _gini(x: np.ndarray) -> float:
    """Gini coefficient of a non-negative array (demand concentration)."""
    x = np.sort(np.asarray(x, dtype=float))
    n = len(x)
    if n == 0 or x.sum() == 0:
        return float("nan")
    cum = np.cumsum(x)
    return float((n + 1 - 2 * np.sum(cum) / cum[-1]) / n)


def _stats(supports: "pd.Series", top_for_lift: int = 300) -> Dict[str, object]:
    sizes = supports.apply(len)
    n = len(supports)
    freq: Counter = Counter()
    for s in supports:
        freq.update(s)
    freq_arr = np.array(sorted(freq.values(), reverse=True), dtype=float)

    # --- co-occurrence lift over the top-N most popular products. -----------
    top = [p for p, _c in freq.most_common(top_for_lift)]
    top_set = set(top)
    idx = {p: i for i, p in enumerate(top)}
    pair_co: Counter = Counter()
    for s in supports:
        ts = [p for p in s if p in top_set]
        for a, b in combinations(sorted(ts), 2):
            pair_co[(a, b)] += 1
    lifts: List[float] = []
    cooc_frac = 0
    n_pairs = len(top) * (len(top) - 1) // 2
    for a, b in combinations(top, 2):
        obs = pair_co.get((a, b) if a < b else (b, a), 0)
        exp = freq[a] * freq[b] / n
        if exp > 0:
            lifts.append(obs / exp)
        if obs > 0:
            cooc_frac += 1
    lifts_arr = np.array(lifts, dtype=float)

    return {
        "n_orders": n, "n_products": len(freq),
        "mean_size": float(sizes.mean()), "median_size": int(sizes.median()),
        "singleton_frac": float((sizes == 1).mean()),
        "gini_demand": _gini(np.array(list(freq.values()))),
        "median_lift": float(np.median(lifts_arr)) if len(lifts_arr) else float("nan"),
        "mean_lift": float(np.mean(lifts_arr)) if len(lifts_arr) else float("nan"),
        "frac_lift_gt2": float(np.mean(lifts_arr > 2)) if len(lifts_arr) else float("nan"),
        "frac_lift_gt5": float(np.mean(lifts_arr > 5)) if len(lifts_arr) else float("nan"),
        "top_pairs_cooccur_frac": cooc_frac / n_pairs if n_pairs else float("nan"),
        "_sizes": sizes.values, "_freq_sorted": freq_arr, "_lifts": lifts_arr,
    }


def run(datasets: List[Tuple[str, str]], data_dir: str, fig_dir: str) -> None:
    os.makedirs(fig_dir, exist_ok=True)
    results: Dict[str, Dict[str, object]] = {}
    for label, prefix in datasets:
        print(f"[{label}] loading {prefix} ...", flush=True)
        sup = _load(prefix, data_dir)
        results[label] = _stats(sup)

    # --- comparative table. --------------------------------------------------
    print("\n=== ORDER-DATA DIAGNOSTICS (universe & layout identical across all) ===")
    hdr = ["dataset", "orders", "mean_sz", "singl%", "gini", "med_lift",
           "%lift>2", "%lift>5", "top-pair cooc%"]
    print("  " + " | ".join(f"{h:>9}" for h in hdr))
    for label, st in results.items():
        print("  " + " | ".join(f"{v:>9}" for v in [
            label[:9], st["n_orders"], f"{st['mean_size']:.2f}",
            f"{100*st['singleton_frac']:.0f}", f"{st['gini_demand']:.3f}",
            f"{st['median_lift']:.2f}", f"{100*st['frac_lift_gt2']:.0f}",
            f"{100*st['frac_lift_gt5']:.0f}", f"{100*st['top_pairs_cooccur_frac']:.0f}"]))

    colors = {"baseline": "k", "iscf10kt": "tab:blue", "iscfco": "tab:red"}
    def col(lbl: str) -> str:
        return colors.get(lbl, "tab:green")

    # --- Fig 1: order-size distribution (normalised, log-y). ----------------
    plt.figure(figsize=(7, 4.5))
    for label, st in results.items():
        sizes = st["_sizes"]
        m = int(min(20, sizes.max()))
        bins = np.arange(1, m + 2) - 0.5
        h, _ = np.histogram(sizes, bins=bins, density=True)
        plt.plot(np.arange(1, m + 1), h, marker="o", ms=3, label=label, color=col(label))
    plt.yscale("log"); plt.xlabel("order size (#products)"); plt.ylabel("fraction of orders (log)")
    plt.title("Order-size distribution"); plt.legend(); plt.grid(alpha=0.3)
    plt.tight_layout(); plt.savefig(os.path.join(fig_dir, "fig1_order_size.png"), dpi=130); plt.close()

    # --- Fig 2: product popularity rank-frequency (Zipf, log-log). ----------
    plt.figure(figsize=(7, 4.5))
    for label, st in results.items():
        f = st["_freq_sorted"]
        r = np.arange(1, len(f) + 1)
        plt.plot(r, f, label=label, color=col(label))
    plt.xscale("log"); plt.yscale("log")
    plt.xlabel("product rank (log)"); plt.ylabel("order frequency (log)")
    plt.title("Product popularity (Zipf / Pareto)"); plt.legend(); plt.grid(alpha=0.3)
    plt.tight_layout(); plt.savefig(os.path.join(fig_dir, "fig2_popularity_zipf.png"), dpi=130); plt.close()

    # --- Fig 3: co-occurrence LIFT distribution (the affinity diagnostic). ---
    plt.figure(figsize=(7, 4.5))
    for label, st in results.items():
        lifts = st["_lifts"]
        lifts = lifts[lifts > 0]
        if len(lifts) == 0:
            continue
        ll = np.log10(lifts)
        plt.hist(ll, bins=60, histtype="step", density=True, label=label, color=col(label))
    plt.axvline(0, color="gray", ls="--", lw=1, label="lift=1 (independence)")
    plt.xlabel("log10(co-occurrence lift)  [0 = pure popularity, >0 = affinity]")
    plt.ylabel("density"); plt.title("Co-occurrence affinity: lift over top-300 products")
    plt.legend(); plt.grid(alpha=0.3)
    plt.tight_layout(); plt.savefig(os.path.join(fig_dir, "fig3_cooccurrence_lift.png"), dpi=130); plt.close()

    # --- Fig 4: demand Lorenz curve (concentration). ------------------------
    plt.figure(figsize=(6, 6))
    for label, st in results.items():
        f = np.sort(st["_freq_sorted"])
        cum = np.cumsum(f) / f.sum()
        x = np.linspace(0, 1, len(cum))
        plt.plot(x, cum, label=f"{label} (Gini {st['gini_demand']:.2f})", color=col(label))
    plt.plot([0, 1], [0, 1], "gray", ls="--", lw=1, label="equality")
    plt.xlabel("cumulative share of products"); plt.ylabel("cumulative share of demand")
    plt.title("Demand concentration (Lorenz curve)"); plt.legend(); plt.grid(alpha=0.3)
    plt.tight_layout(); plt.savefig(os.path.join(fig_dir, "fig4_demand_lorenz.png"), dpi=130); plt.close()

    print(f"\nfigures written to {fig_dir}")


def main() -> None:
    p = argparse.ArgumentParser(description="Order-data distributional diagnostics + figures.")
    p.add_argument("--dir", default="../../../../iscf_instances")
    p.add_argument("--fig-dir", default="../../../../reports/figures")
    p.add_argument("--datasets", nargs="+",
                   default=["baseline:iscf", "iscf10kt:iscf10kt", "iscfco:iscfco"],
                   help="label:prefix pairs.")
    args = p.parse_args()
    ds = [(d.split(":", 1)[0], d.split(":", 1)[1]) for d in args.datasets]
    run(ds, args.dir, args.fig_dir)


if __name__ == "__main__":
    main()
