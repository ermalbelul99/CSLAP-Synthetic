r"""Build standard-schema CSLAP instances from the BERNER industrial order lines.

Stage-3 reviewer/human-supervisor item T5. Produces a train-early / test-late
temporal split of ``BERNER_ORDER_LINES_09-12.csv`` (schema
``PRODUCT;ORDER;QTY;STATION;BOX_ID``) in the standard semicolon schema consumed by
the unchanged baseline solvers, with the station configuration replicated from the
repository's own industrial loader ``data_loader_industrial.py`` (speed tiers,
capacity-by-distinct-products rule) but computed on the **training window only**
to respect the no-leakage protocol (Method Report E.2).

Assumption U1 (flagged, no date column)
---------------------------------------
The file has no date column, so the manuscript's 13-week temporal split is
reproduced by an **order-ID-rank** proxy: order ids are numeric and monotone in
time (verified: 8076384032 -> 8076739874), so ranking by order id and cutting at
the 10/13 (primary) or 8/13 quantile yields an early-train / late-test split.

Station configuration (replicated from data_loader_industrial.py)
-----------------------------------------------------------------
* Drop stations ``01.Z8 / 01.15 / 01.GED`` and the blank station; merge
  ``01.GE4 -> 01.E4`` (loader step 3).
* Each product is pinned to the station of its latest order (loader step 2).
* Speed tiers (loader step 5): STATIC 37700 (01.E4/01.31/01.30),
  PALETTE 57200 (01.01..01.05), DYNAMIC 83200 (rest); per-station SPEED =
  tier / (#distinct products on the station).
* CAPACITY = number of distinct products pinned to the station (loader step 7);
  a small documented slack is added so the assignment problem is feasible for the
  metaheuristics (the loader's capacities sum to exactly |P_train|; we widen each
  by 15% so the solvers have placement freedom). The summed CAPACITY therefore
  exceeds |P_train| as required.
* TIME_CAPACITY = sum over the station's pinned products of frequency/SPEED,
  scaled by the same slack (the loader's realised workload, eq. (10) analogue).

Standard-schema mapping
-----------------------
Physical station ids (``01.E4`` ...) are mapped to integer ``STATION_ID`` 1..|S|
(the synthetic solvers key layouts by ``STATION_ID``; any hashable works, but
integers keep the layout JSONs and ``read_data`` clean). Products are emitted as
``PROD_{token}`` to match ``read_data``'s ``PROD_`` convention; the products file
uses ``PRODUCT_ID = token`` so ``read_data`` reconstructs ``PROD_{token}``.

Leakage assertions
------------------
Train and test order-ID sets are asserted disjoint. The test window contributes
**orders only**; products and stations are frozen from the train window. Test SKUs
unseen in training are expected and surface as coverage ``kappa`` < 1 in the
evaluator (Method Report eq. 11 excludes them, identically for all layouts).
"""
from __future__ import annotations

import argparse
import math
import os
from typing import Dict, List, Tuple

import pandas as pd

DROP_STATIONS = {"01.Z8", "01.15", "01.GED", " ", ""}
STATIC_STATIONS = {"01.E4", "01.31", "01.30"}
PALETTE_STATIONS = {"01.01", "01.02", "01.03", "01.04", "01.05"}
STATIC_SPEED = 37700.0
PALETTE_SPEED = 57200.0
DYNAMIC_SPEED = 83200.0


def _tier_speed(station: str) -> float:
    if station in STATIC_STATIONS:
        return STATIC_SPEED
    if station in PALETTE_STATIONS:
        return PALETTE_SPEED
    return DYNAMIC_SPEED


def build_berner_split(
    order_lines_csv: str,
    out_dir: str,
    out_prefix: str,
    train_quantile: float,
    cap_slack: float = 1.15,
    min_order_size: int = 1,
) -> Dict[str, object]:
    r"""Build the train-early / test-late BERNER instances (standard schema).

    Args:
        order_lines_csv: Path to ``BERNER_ORDER_LINES_09-12.csv``.
        out_dir: Output directory for the standard-schema CSVs.
        out_prefix: Base prefix; ``_train`` / ``_test`` suffixes are appended.
        train_quantile: Train fraction of ranked orders (10/13 or 8/13).
        cap_slack: Multiplicative slack on CAPACITY / TIME_CAPACITY so the
            placement problem is feasible (documented; loader caps are tight).
        min_order_size: Minimum distinct products per order to keep (1 = keep all;
            the loader used >5 for its solver slice, relaxed here so the temporal
            shift is measured on the genuine order stream).

    Returns:
        Metadata dict (train/test prefixes, sizes, station count, kappa proxy).
    """
    df = pd.read_csv(order_lines_csv, sep=";",
                     usecols=["PRODUCT", "ORDER", "QTY", "STATION"], dtype=str)
    df["ORDER"] = df["ORDER"].astype(str)
    df["STATION"] = df["STATION"].astype(str).str.strip()
    df["PRODUCT"] = df["PRODUCT"].astype(str)

    # Station cleaning (loader steps 2-3): merge 01.GE4 -> 01.E4, drop excluded.
    df.loc[df["STATION"] == "01.GE4", "STATION"] = "01.E4"
    df = df[~df["STATION"].isin(DROP_STATIONS)]
    df = df.dropna(subset=["PRODUCT", "ORDER", "STATION"])

    # Temporal rank split on numeric order id (assumption U1).
    order_ids = sorted(df["ORDER"].unique(), key=lambda v: int(v))
    cut = int(len(order_ids) * train_quantile)
    train_ids = set(order_ids[:cut])
    test_ids = set(order_ids[cut:])
    assert train_ids.isdisjoint(test_ids), "BERNER train/test order ids overlap"

    train_df = df[df["ORDER"].isin(train_ids)].copy()
    test_df = df[df["ORDER"].isin(test_ids)].copy()

    # --- Pin each TRAIN product to the station of its latest order (loader 2).
    # Latest = max numeric order id carrying that product in the train window.
    train_df["ORDER_NUM"] = train_df["ORDER"].astype("int64")
    idx = train_df.groupby("PRODUCT")["ORDER_NUM"].idxmax()
    prod_station = train_df.loc[idx].set_index("PRODUCT")["STATION"].to_dict()

    # Train product frequency = #order lines (loader's Product_Frequency proxy).
    prod_freq = train_df.groupby("PRODUCT")["ORDER"].nunique().to_dict()

    # Distinct products per physical station (capacity & speed denominator).
    station_products: Dict[str, List[str]] = {}
    for p, s in prod_station.items():
        station_products.setdefault(s, []).append(p)
    phys_stations = sorted(station_products.keys())

    # Per-station speed (tier / #locations), capacity, time-capacity.
    station_records: List[dict] = []
    phys_to_int: Dict[str, int] = {s: i + 1 for i, s in enumerate(phys_stations)}
    for s in phys_stations:
        locs = max(len(station_products[s]), 1)
        speed = _tier_speed(s) / locs
        workload = sum(prod_freq.get(p, 0) / speed for p in station_products[s])
        cap = int(math.ceil(len(station_products[s]) * cap_slack))
        station_records.append({
            "STATION_ID": phys_to_int[s],
            "CAPACITY": cap,
            "TIME_CAPACITY": int(math.ceil(workload * cap_slack)),
            "SPEED": round(speed, 6),
        })

    n_train_prod = len(prod_station)
    total_cap = sum(r["CAPACITY"] for r in station_records)
    assert total_cap >= n_train_prod, (
        f"CAPACITY sum {total_cap} < |P_train| {n_train_prod}")

    os.makedirs(out_dir, exist_ok=True)
    train_prefix = f"{out_prefix}_train"
    test_prefix = f"{out_prefix}_test"

    # --- Write TRAIN instance. ----------------------------------------------
    _write_orders(train_df, os.path.join(out_dir, f"{train_prefix}_orders.csv"))
    _write_products(sorted(prod_station.keys()),
                    os.path.join(out_dir, f"{train_prefix}_products.csv"),
                    prod_freq)
    pd.DataFrame(station_records).to_csv(
        os.path.join(out_dir, f"{train_prefix}_stations.csv"),
        index=False, sep=";")

    # --- Write TEST instance (orders only new; products/stations frozen). ----
    _write_orders(test_df, os.path.join(out_dir, f"{test_prefix}_orders.csv"))
    # Frozen universe/stations carried from train (evaluator restricts to dom(a)).
    _write_products(sorted(prod_station.keys()),
                    os.path.join(out_dir, f"{test_prefix}_products.csv"),
                    prod_freq)
    pd.DataFrame(station_records).to_csv(
        os.path.join(out_dir, f"{test_prefix}_stations.csv"),
        index=False, sep=";")

    # --- Diagnostics: kappa proxy (fraction of test SKUs seen in training). --
    test_prods = set(test_df["PRODUCT"].unique())
    train_prods = set(prod_station.keys())
    seen = len(test_prods & train_prods)
    kappa_sku = seen / len(test_prods) if test_prods else 0.0

    meta = {
        "train_prefix": train_prefix,
        "test_prefix": test_prefix,
        "train_quantile": train_quantile,
        "n_orders_train": len(train_ids),
        "n_orders_test": len(test_ids),
        "n_products_train": n_train_prod,
        "n_products_test": len(test_prods),
        "n_stations": len(station_records),
        "total_capacity": total_cap,
        "kappa_sku": round(kappa_sku, 4),
    }
    print(
        f"[BERNER {out_prefix} q={train_quantile:.3f}] "
        f"train orders={meta['n_orders_train']} prods={n_train_prod} | "
        f"test orders={meta['n_orders_test']} prods={meta['n_products_test']} | "
        f"stations={meta['n_stations']} capSum={total_cap} | "
        f"kappa_sku(test seen in train)={meta['kappa_sku']}"
    )
    return meta


def _write_orders(frame: pd.DataFrame, path: str) -> None:
    """Write orders in the standard ``ORDER;PRODUCT;QTY;STATION`` schema."""
    out = pd.DataFrame({
        "ORDER": frame["ORDER"].astype(str),
        "PRODUCT": frame["PRODUCT"].apply(
            lambda v: v if str(v).startswith("PROD_") else f"PROD_{v}"),
        "QTY": frame["QTY"] if "QTY" in frame.columns else 1,
        "STATION": 1,  # placeholder, ignored by read_data
    })
    out.to_csv(path, index=False, sep=";")


def _write_products(tokens: List[str], path: str,
                    prod_freq: Dict[str, int]) -> None:
    """Write the products file (PRODUCT_ID = raw token, read_data adds PROD_)."""
    pdf = pd.DataFrame({"PRODUCT_ID": tokens})
    pdf["CATEGORY"] = 0
    pdf["POPULARITY"] = [int(prod_freq.get(t, 0)) for t in tokens]
    pdf.to_csv(path, index=False, sep=";")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build BERNER train-early/test-late standard-schema instances.")
    parser.add_argument("--csv", type=str,
                        default="Heuristic_Connex_Set_Project/data/"
                                "BERNER_ORDER_LINES_09-12.csv")
    parser.add_argument("--out-dir", type=str, default="synthetic_datasets")
    parser.add_argument("--out-prefix", type=str, required=True)
    parser.add_argument("--train-quantile", type=float, required=True)
    parser.add_argument("--cap-slack", type=float, default=1.15)
    args = parser.parse_args()
    build_berner_split(args.csv, args.out_dir, args.out_prefix,
                       args.train_quantile, args.cap_slack)


if __name__ == "__main__":
    main()
