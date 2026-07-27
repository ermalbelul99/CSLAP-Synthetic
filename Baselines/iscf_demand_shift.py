r"""
Demand-changing shift injector (popularity drift) with a flat-workload safeguard.

Unlike the curveball co-occurrence shift (`iscf_shift_inject.py`, which holds every
product's demand L_p fixed), this injector deliberately changes **product
popularity** in the test: a random subset of SKUs surges and another fades, so the
future demand distribution differs from the past. It tests a different robustness
dimension -- whether a layout is robust to demand drift -- on top of the
co-occurrence structure.

Mechanism (per fold, per magnitude rho)
---------------------------------------
1. Draw a per-product log-normal drift ``d_p = exp(rho * z_p)``, ``z_p ~ N(0,1)``
   (rho=0 -> no drift). Each real test order keeps its **real composition** (so
   co-occurrence within an order is preserved); its sampling weight is the
   geometric mean of its products' drift. The shifted test is a
   **weight-proportional resample (with replacement)** of the real test orders to
   the same order count -- orders rich in surging SKUs become more frequent, so the
   realised per-product line counts L_p shift while order compositions stay real.
2. **Flat-workload safeguard (user design).** After resampling, build a dummy
   balanced assignment of all products to the stations (greedy longest-processing-
   time on the shifted L_p, respecting slot capacity), take the **maximum** station
   workload, and set **every** station's ``TIME_CAPACITY`` to ``ceil(slack * Tmax)``.
   The capacity stays flat (uniform) and the dummy is feasible by construction, so
   the demand shift never makes the warehouse "break" and the k=1-vs-k>1 comparison
   carries no workload confound.

Output mirrors `iscf_shift_inject.py` so `run_robustness_iscf.py evaluate-shift
--mode demand` consumes it: ``{tag}_test_demand_r{rho}_{orders,products,stations}``.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from collections import Counter
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd


def _dummy_max_workload(
    lp: Dict[str, float], products: List[str], n_stations: int, cap: int
) -> float:
    """Greedy LPT balanced assignment; return the max station workload."""
    loads = [0.0] * n_stations
    counts = [0] * n_stations
    for p in sorted(products, key=lambda x: -lp.get(x, 0.0)):
        # least-loaded station that still has a free slot.
        best = min((s for s in range(n_stations) if counts[s] < cap),
                   key=lambda s: loads[s])
        loads[best] += lp.get(p, 0.0)
        counts[best] += 1
    return max(loads) if loads else 0.0


def inject_demand(
    manifest_path: str,
    fold_dir: str,
    out_dir: str,
    rhos: List[float],
    slack: float,
    seed: int,
    verbose: bool = True,
) -> None:
    os.makedirs(out_dir, exist_ok=True)
    with open(manifest_path) as fh:
        manifest = json.load(fh)

    for entry in manifest["folds"]:
        tag = entry["tag"]
        test_prefix = entry["test_prefix"]
        te = pd.read_csv(os.path.join(fold_dir, f"{test_prefix}_orders.csv"), sep=";")
        stations = pd.read_csv(
            os.path.join(fold_dir, f"{test_prefix}_stations.csv"), sep=";"
        )
        products_df = pd.read_csv(
            os.path.join(fold_dir, f"{test_prefix}_products.csv"), sep=";"
        )
        n_stations = len(stations)
        cap = int(stations["CAPACITY"].iloc[0])

        order_ids = list(te.groupby("ORDER").groups.keys())
        supports = te.groupby("ORDER")["PRODUCT"].apply(list).to_dict()
        universe = sorted(te["PRODUCT"].unique())
        prod_idx = {p: i for i, p in enumerate(universe)}
        # original per-product line count (for the drift report).
        orig_lp = Counter(te["PRODUCT"])

        for rho in rhos:
            rng = np.random.RandomState(seed + int(round(rho * 1000)))
            z = rng.normal(0.0, 1.0, size=len(universe))
            log_drift = rho * z  # log of d_p
            # order weight = geometric mean of product drift = exp(mean log_drift).
            weights = np.array([
                math.exp(np.mean([log_drift[prod_idx[p]] for p in supports[o]]))
                for o in order_ids
            ])
            weights = weights / weights.sum()
            n = len(order_ids)
            pick = rng.choice(n, size=n, replace=True, p=weights)

            rows: List[Dict[str, object]] = []
            for new_oid, src in enumerate(pick, start=1):
                for p in supports[order_ids[src]]:
                    rows.append({"ORDER": new_oid, "PRODUCT": p, "QTY": 1, "STATION": 1})
            shifted = pd.DataFrame(rows, columns=["ORDER", "PRODUCT", "QTY", "STATION"])

            # Shifted per-product demand + flat-workload safeguard.
            new_lp = shifted.groupby("PRODUCT")["ORDER"].nunique().to_dict()
            tmax = _dummy_max_workload(new_lp, universe, n_stations, cap)
            time_cap = int(math.ceil(slack * tmax))
            new_stations = stations.copy()
            new_stations["TIME_CAPACITY"] = time_cap

            out_prefix = f"{tag}_test_demand_r{rho}"
            shifted.to_csv(
                os.path.join(out_dir, f"{out_prefix}_orders.csv"), index=False, sep=";"
            )
            new_stations.to_csv(
                os.path.join(out_dir, f"{out_prefix}_stations.csv"), index=False, sep=";"
            )
            products_df.to_csv(
                os.path.join(out_dir, f"{out_prefix}_products.csv"), index=False, sep=";"
            )

            # --- drift report. ---
            shifted_lp = Counter(shifted["PRODUCT"])
            common = [p for p in universe]
            ov = np.array([orig_lp.get(p, 0) for p in common], dtype=float)
            nv = np.array([shifted_lp.get(p, 0) for p in common], dtype=float)
            lp_pearson = float(np.corrcoef(ov, nv)[0, 1]) if len(common) > 1 else float("nan")
            def top_share(cnt: Counter, k: int = 50) -> float:
                tot = sum(cnt.values())
                return sum(c for _p, c in cnt.most_common(k)) / tot if tot else float("nan")
            if verbose:
                print(f"  {out_prefix}: L_p Pearson(shift vs orig)={lp_pearson:.3f} | "
                      f"top50 share {top_share(orig_lp):.3f}->{top_share(shifted_lp):.3f} | "
                      f"T_s {int(stations['TIME_CAPACITY'].iloc[0])}->{time_cap} "
                      f"(flat, dummy-max safeguard)", flush=True)


def main() -> None:
    p = argparse.ArgumentParser(description="Demand-changing shift injector + flat-workload safeguard.")
    p.add_argument("--manifest", required=True)
    p.add_argument("--fold-dir", required=True)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--rhos", nargs="+", type=float, default=[0.0, 0.5, 1.0, 2.0])
    p.add_argument("--slack", type=float, default=1.10)
    p.add_argument("--seed", type=int, default=4242)
    args = p.parse_args()
    inject_demand(args.manifest, args.fold_dir, args.out_dir, args.rhos, args.slack, args.seed)


if __name__ == "__main__":
    main()
