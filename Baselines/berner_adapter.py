r"""
BERNER -> harness-format adapter for the preprocess-vs-capacity decomposition.

The earlier industrial run on BERNER (Company B) was the *only* place a positive
out-of-sample gain appeared, but it confounded two effects: the covering
**enlargement** (outer-approximation) and a **time-capacity recalibration** (the
robust arm's workload cap was rebuilt from the inflated closure line counts, eq. 10
of ``pk_instance_robust``, making it looser -> more placement freedom -> fewer
visits on its own). This adapter rebuilds BERNER in the exact format consumed by
``run_robustness_iscf.py`` so the decomposition runs through the unchanged staged
harness, with the **kappa-invariant real capacity** that isolates the enlargement.

It mirrors ``build_berner_instance.py`` (temporal rank split on order id;
station pinning to the latest order; tier speeds; capacity by distinct-product
count) but (1) restricts to the **top-N most frequent train products** for Hexaly
tractability (orders keep their kept-product subset, exactly as the ISCF top-480
study), (2) emits the products file with the ``REAL_LINES`` column the harness
passes as the kappa-invariant workload ``prod_lines``, and (3) writes a one-fold
manifest. The test window contributes **orders only**; products/stations are frozen
from train; unseen test SKUs surface as coverage < 1 in the evaluator (excluded
identically for every arm).

Arms downstream (all via the harness ``place``/``evaluate``):
* A = fold ``bern`` k=1   -> nominal orders, real capacity (baseline).
* B = fold ``bern`` k=2   -> closures, real (kappa-invariant) capacity = PREPROCESS-ONLY.
* C = fold ``bern_recal`` k=2 -> closures, recalibrated (loose) capacity = the v2 arm.
* D = fold ``bern_recal`` k=1 -> nominal orders, loose capacity = CAPACITY-ONLY control.
(The ``bern_recal`` stations are written by ``berner_recal_stations.py`` after the
cover exists, since the recalibrated cap depends on the closures.)
"""

from __future__ import annotations

import argparse
import json
import math
import os
from typing import Dict, List

import pandas as pd

DROP_STATIONS = {"01.Z8", "01.15", "01.GED", " ", ""}
STATIC_STATIONS = {"01.E4", "01.31", "01.30"}
PALETTE_STATIONS = {"01.01", "01.02", "01.03", "01.04", "01.05"}
STATIC_SPEED, PALETTE_SPEED, DYNAMIC_SPEED = 37700.0, 57200.0, 83200.0


def _tier_speed(station: str) -> float:
    if station in STATIC_STATIONS:
        return STATIC_SPEED
    if station in PALETTE_STATIONS:
        return PALETTE_SPEED
    return DYNAMIC_SPEED


def _write_orders(frame: pd.DataFrame, path: str) -> int:
    out = pd.DataFrame({
        "ORDER": frame["ORDER"].astype(str),
        "PRODUCT": frame["PRODUCT"],
        "QTY": 1, "STATION": 1,
    })
    out.to_csv(path, index=False, sep=";")
    return out["ORDER"].nunique()


def build(
    order_lines_csv: str, out_dir: str, prefix: str, train_quantile: float,
    top_products: int, cap_slack: float, seed: int = 0,
) -> Dict[str, object]:
    os.makedirs(out_dir, exist_ok=True)
    df = pd.read_csv(order_lines_csv, sep=";",
                     usecols=["PRODUCT", "ORDER", "QTY", "STATION"], dtype=str)
    df["ORDER"] = df["ORDER"].astype(str)
    df["STATION"] = df["STATION"].astype(str).str.strip()
    df["PRODUCT"] = df["PRODUCT"].astype(str)
    df.loc[df["STATION"] == "01.GE4", "STATION"] = "01.E4"
    df = df[~df["STATION"].isin(DROP_STATIONS)].dropna(subset=["PRODUCT", "ORDER", "STATION"])

    # Temporal rank split on numeric order id (assumption U1).
    order_ids = sorted(df["ORDER"].unique(), key=lambda v: int(v))
    cut = int(len(order_ids) * train_quantile)
    train_ids, test_ids = set(order_ids[:cut]), set(order_ids[cut:])
    assert train_ids.isdisjoint(test_ids)
    train_df = df[df["ORDER"].isin(train_ids)].copy()
    test_df = df[df["ORDER"].isin(test_ids)].copy()

    # --- Top-N most frequent TRAIN products (by distinct train orders). -------
    freq_all = train_df.groupby("PRODUCT")["ORDER"].nunique().sort_values(ascending=False)
    keep = list(freq_all.index[:top_products]) if top_products else list(freq_all.index)
    keep_set = set(keep)
    train_df = train_df[train_df["PRODUCT"].isin(keep_set)].copy()
    test_df = test_df[test_df["PRODUCT"].isin(keep_set)].copy()

    # Pin each kept product to the station of its latest train order (loader 2).
    train_df["ORDER_NUM"] = train_df["ORDER"].astype("int64")
    idx = train_df.groupby("PRODUCT")["ORDER_NUM"].idxmax()
    prod_station = train_df.loc[idx].set_index("PRODUCT")["STATION"].to_dict()
    prod_freq = train_df.groupby("PRODUCT")["ORDER"].nunique().to_dict()  # REAL_LINES

    station_products: Dict[str, List[str]] = {}
    for p, s in prod_station.items():
        station_products.setdefault(s, []).append(p)
    phys = sorted(station_products.keys())
    phys_to_int = {s: i + 1 for i, s in enumerate(phys)}

    station_records: List[dict] = []
    for s in phys:
        locs = max(len(station_products[s]), 1)
        speed = _tier_speed(s) / locs
        workload = sum(prod_freq.get(p, 0) / speed for p in station_products[s])
        station_records.append({
            "STATION_ID": phys_to_int[s],
            "CAPACITY": int(math.ceil(locs * cap_slack)),
            "TIME_CAPACITY": int(math.ceil(workload * cap_slack)),
            "SPEED": round(speed, 6),
        })
    n_keep = len(prod_station)
    total_cap = sum(r["CAPACITY"] for r in station_records)
    assert total_cap >= n_keep, f"capacity {total_cap} < |P| {n_keep}"

    # PROD_ token products file with REAL_LINES (harness kappa-invariant workload).
    def _products_frame() -> pd.DataFrame:
        toks = sorted(prod_station.keys())
        return pd.DataFrame({
            "PRODUCT_ID": toks,
            "REAL_LINES": [int(prod_freq.get(t, 0)) for t in toks],
            "VOLUME": 0, "FREQUENCY": [int(prod_freq.get(t, 0)) for t in toks],
        })

    def _tok(frame: pd.DataFrame) -> pd.DataFrame:
        frame = frame.copy()
        frame["PRODUCT"] = frame["PRODUCT"].apply(
            lambda v: v if str(v).startswith("PROD_") else f"PROD_{v}")
        return frame

    # PRODUCT_ID stays the RAW token (the harness prepends PROD_ itself in both
    # the products list and _real_prod_lines); orders carry the PROD_ form.
    products_frame = _products_frame()
    stations_frame = pd.DataFrame(station_records)

    tr_pre, te_pre = f"{prefix}_train", f"{prefix}_test"
    n_tr = _write_orders(_tok(train_df), os.path.join(out_dir, f"{tr_pre}_orders.csv"))
    n_te = _write_orders(_tok(test_df), os.path.join(out_dir, f"{te_pre}_orders.csv"))
    for pre in (tr_pre, te_pre):
        products_frame.to_csv(os.path.join(out_dir, f"{pre}_products.csv"), index=False, sep=";")
        stations_frame.to_csv(os.path.join(out_dir, f"{pre}_stations.csv"), index=False, sep=";")

    test_prods = set(test_df["PRODUCT"].unique())
    kappa_sku = len(test_prods & keep_set) / len(test_prods) if test_prods else 0.0
    fold = {
        "repeat": 0, "fold": 0, "tag": prefix,
        "train_prefix": tr_pre, "test_prefix": te_pre,
        "n_train_orders": int(n_tr), "n_test_orders": int(n_te),
        "time_capacity": int(stations_frame["TIME_CAPACITY"].iloc[0]),
    }
    manifest_path = os.path.join(out_dir, f"{prefix}_folds_manifest.json")
    with open(manifest_path, "w") as fh:
        json.dump({"prefix": prefix, "data_dir": out_dir, "n_products": n_keep,
                   "folds": [fold]}, fh, indent=2)

    line_cov = train_df.shape[0] / df[df["ORDER"].isin(train_ids)].shape[0]
    print(f"[BERNER {prefix} q={train_quantile} topN={top_products}] "
          f"train orders={n_tr} prods={n_keep} | test orders={n_te} | "
          f"stations={len(station_records)} capSum={total_cap} | "
          f"kappa_sku={kappa_sku:.3f} | train_line_coverage={line_cov:.3f} -> {manifest_path}")
    return fold


def main() -> None:
    p = argparse.ArgumentParser(description="BERNER -> harness-format adapter (top-N, REAL_LINES).")
    p.add_argument("--csv", default="Heuristic_Connex_Set_Project/data/BERNER_ORDER_LINES_09-12.csv")
    p.add_argument("--out-dir", default="berner_topn")
    p.add_argument("--prefix", default="bern")
    p.add_argument("--train-quantile", type=float, default=0.7692)  # 10/13 weeks
    p.add_argument("--top-products", type=int, default=2000)
    p.add_argument("--cap-slack", type=float, default=1.20)
    args = p.parse_args()
    build(args.csv, args.out_dir, args.prefix, args.train_quantile,
          args.top_products, args.cap_slack)


if __name__ == "__main__":
    main()
