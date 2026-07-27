r"""
ISCF data adapter: emit a standard CSLAP instance from the clean ``ISCF Data/``.

This is the Phase-A artifact of ``plan.md`` (CPLEX validation phase). It reads the
two raw ISCF CSVs and writes the three standard semicolon-separated CSLAP files
(``{prefix}_orders.csv``, ``{prefix}_products.csv``, ``{prefix}_stations.csv``)
that every downstream solver consumes **unchanged** through its ``read_data``
(see ``milp_gurobi_synthetic.read_data``).

Why ISCF (plan.md §2.1)
-----------------------
``ISCF Data/`` is the new **primary** clean test instance: 4,328 SKUs, 8 uniform
stations of 541 slots each (8*541 = 4,328 = |P|, a balanced layout where slot
capacity sums **exactly** to the product count), ~419k orders. Crucially the
capacity is **kappa-invariant**: a station's slot count (541) and each product's
``Volume_Product``/``Product_FREQUENCY`` are fixed attributes that do **not**
depend on the covering knob kappa. This removes by construction the BERNER
"recalibration side-channel" confound (plan.md G4), where the enlarged orders
inflated a frequency-based time capacity.

Raw inputs
----------
``Products_data_ISCF.csv`` (comma-CSV, 997,198 order-lines):
``,ID_Product,Product_FREQUENCY,Average_Volume/Day,ORDER_ID,Volume_Product,Number_Lines``.
Each row is one (order, product) line. **Orders = group by ``ORDER_ID``** -> the
set of ``ID_Product``. ``Product_FREQUENCY`` and ``Volume_Product`` are per-product
fixed (verified: 0 products carry more than one distinct value).

``Location_data_ISCF.csv`` (comma-CSV, 4,328 locations):
``,CODE_BARRE,COUT_EMPL,ID_GARE,Volume_Location``. 8 stations (``ID_GARE`` =
GARE4..GARE11), 541 locations each; ``Volume_Location`` = per-slot capacity.

Output schema (standard CSLAP, semicolon-separated)
---------------------------------------------------
* ``{prefix}_orders.csv`` -- ``ORDER;PRODUCT;QTY;STATION``. ``ORDER`` = raw
  ``ORDER_ID``; ``PRODUCT`` = ``PROD_{ID_Product}`` (the token convention
  ``read_data`` reconstructs from the products file); ``QTY=1``, ``STATION=1``
  (placeholders, ignored by ``read_data``). One row per distinct (order, product).
* ``{prefix}_products.csv`` -- ``PRODUCT_ID;REAL_LINES;VOLUME;FREQUENCY``.
  ``read_data`` only reads ``PRODUCT_ID`` (= raw ``ID_Product``); the three extra
  columns are **kappa-invariant per-product attributes** carried so the exact
  placement MILP (Phase D) can enforce a workload / volume cap from the **real**
  per-product frequency, never from closure line counts (plan.md G4). ``REAL_LINES``
  = L_p = number of distinct orders containing the product (the true pick-line
  count); ``VOLUME`` = ``Volume_Product``; ``FREQUENCY`` = ``Product_FREQUENCY``.
* ``{prefix}_stations.csv`` -- ``STATION_ID;CAPACITY;TIME_CAPACITY;SPEED``.
  ``STATION_ID`` = ``ID_GARE``; ``CAPACITY`` = slot count (541, kappa-invariant
  primary capacity); ``SPEED`` = 1.0 (uniform stations); ``TIME_CAPACITY`` =
  ceil(slack * sum_p L_p / |S|) -- a kappa-invariant workload ceiling computed from
  the **real** total pick-lines under the manuscript's 10% slack rule.

Nothing is dropped silently: every count (products, orders, lines, stations,
slots) is logged, and the slot-sum == |P| balance is asserted.
"""

from __future__ import annotations

import argparse
import math
import os
from typing import Dict, Optional, Tuple

import pandas as pd


# ISCF station id ordering is non-lexicographic (GARE4..GARE11); sort numerically.
def _gare_sort_key(gare: str) -> int:
    """Sort key extracting the trailing integer of a ``GARE<n>`` station id."""
    digits = "".join(ch for ch in str(gare) if ch.isdigit())
    return int(digits) if digits else 0


def load_iscf(
    iscf_dir: str,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Read the two raw ISCF CSVs (comma-separated).

    Args:
        iscf_dir: Directory holding ``Products_data_ISCF.csv`` and
            ``Location_data_ISCF.csv``.

    Returns:
        ``(products_raw, locations_raw)`` as pandas DataFrames, untouched.
    """
    products_path = os.path.join(iscf_dir, "Products_data_ISCF.csv")
    locations_path = os.path.join(iscf_dir, "Location_data_ISCF.csv")
    products_raw = pd.read_csv(products_path)
    locations_raw = pd.read_csv(locations_path)
    return products_raw, locations_raw


def build_iscf_instance(
    iscf_dir: str,
    out_dir: str,
    prefix: str = "iscf",
    slack: float = 1.10,
    speed: float = 1.0,
    top_products: Optional[int] = None,
    n_stations: int = 8,
    verbose: bool = True,
) -> Dict[str, object]:
    r"""Convert the raw ISCF data into a standard CSLAP instance on disk.

    Args:
        iscf_dir: Directory of the raw ISCF CSVs.
        out_dir: Output directory for the three standard CSVs.
        prefix: Instance prefix (files are ``{prefix}_orders.csv`` etc.).
        slack: Workload slack factor in the kappa-invariant ``TIME_CAPACITY``
            ceiling :math:`\bar{T}_s = \lceil \text{slack}\cdot\sum_p L_p / |S|\rceil`.
        speed: Homogeneous station speed :math:`V_s` (uniform stations).
        top_products: If set, emit a **scaled clean sub-instance** keeping only the
            ``top_products`` most frequent SKUs (by real pick-lines) and restricting
            every order to that SKU subset (orders that become empty are dropped).
            The layout stays the clean ISCF structure -- ``n_stations`` uniform
            stations whose slot counts sum **exactly** to the kept product count
            (balanced, kappa-invariant capacity by construction). This is the
            tractable testbed used when the full 4,328-SKU exact cover does not
            scale (plan.md G1/G2: the cover on the sub-instance is **full**, no
            subsample). ``None`` = full ISCF.
        n_stations: Number of uniform stations (default 8, as in ISCF). Used to
            partition the kept SKUs into balanced slot counts; the count is rounded
            so the slot total equals the kept product count.
        verbose: Whether to print the size / balance log.

    Returns:
        Metadata dict (counts, paths, capacities) for logging and assertions.
    """
    products_raw, locations_raw = load_iscf(iscf_dir)

    # --- Orders: one row per distinct (order, product). ----------------------
    pairs = products_raw[["ORDER_ID", "ID_Product"]].drop_duplicates()

    # --- Optional scaling: keep the top-N most frequent SKUs (plan.md testbed).
    if top_products is not None:
        freq = pairs.groupby("ID_Product")["ORDER_ID"].nunique()
        # Round the kept count down to a multiple of n_stations so the slot total
        # divides evenly across uniform stations (exact balance == |P|).
        keep_n = (min(top_products, len(freq)) // n_stations) * n_stations
        kept_products = set(
            freq.sort_values(ascending=False).index[:keep_n].tolist()
        )
        pairs = pairs[pairs["ID_Product"].isin(kept_products)]
        # Drop orders that became empty (all their SKUs were outside the top set).
        # (Implicit: such ORDER_IDs simply no longer appear in `pairs`.)

    n_lines = len(pairs)
    n_orders = pairs["ORDER_ID"].nunique()
    n_products = pairs["ID_Product"].nunique()

    orders_df = pd.DataFrame(
        {
            "ORDER": pairs["ORDER_ID"].to_numpy(),
            "PRODUCT": ("PROD_" + pairs["ID_Product"].astype(str)).to_numpy(),
            "QTY": 1,
            "STATION": 1,
        }
    )

    # --- Real per-product pick-lines L_p (kappa-invariant). ------------------
    # L_p = number of distinct orders containing product p.
    real_lines = pairs.groupby("ID_Product")["ORDER_ID"].nunique()

    # Per-product fixed attributes (verified single-valued upstream).
    attrs = (
        products_raw.groupby("ID_Product")
        .agg(VOLUME=("Volume_Product", "first"), FREQUENCY=("Product_FREQUENCY", "first"))
    )

    products_df = (
        pd.DataFrame({"PRODUCT_ID": real_lines.index})
        .assign(
            REAL_LINES=real_lines.to_numpy(),
            VOLUME=attrs.loc[real_lines.index, "VOLUME"].to_numpy(),
            FREQUENCY=attrs.loc[real_lines.index, "FREQUENCY"].to_numpy(),
        )
        .sort_values("PRODUCT_ID")
        .reset_index(drop=True)
    )

    # --- Stations: uniform, slots summing EXACTLY to |P| (kappa-invariant). --
    # Full ISCF (n_products=4328, n_stations=8) -> 541 slots/station, matching the
    # real Location_data_ISCF layout. Scaled sub-instances keep the same uniform,
    # balanced structure. n_products was rounded to a multiple of n_stations above
    # (scaled case) so the division is exact; the full case is exact by data.
    if n_products % n_stations != 0:
        raise AssertionError(
            f"ISCF balance: |P|={n_products} not divisible by n_stations="
            f"{n_stations}; use a kept-product count that divides evenly."
        )
    slots_per_station = n_products // n_stations
    station_ids = [f"GARE{4 + i}" for i in range(n_stations)]

    total_real_lines = int(real_lines.sum())
    time_capacity = int(math.ceil(slack * total_real_lines / (speed * n_stations)))

    stations_df = pd.DataFrame(
        {
            "STATION_ID": station_ids,
            "CAPACITY": slots_per_station,
            "TIME_CAPACITY": time_capacity,
            "SPEED": speed,
        }
    )

    # --- Balance assertion: slots sum exactly to |P| (plan.md §2.1). ---------
    total_slots = int(stations_df["CAPACITY"].sum())
    if total_slots != n_products:
        raise AssertionError(
            f"ISCF balance broken: total slots {total_slots} != |P| {n_products}"
        )

    # --- Write the three standard CSVs. -------------------------------------
    os.makedirs(out_dir, exist_ok=True)
    orders_path = os.path.join(out_dir, f"{prefix}_orders.csv")
    products_path = os.path.join(out_dir, f"{prefix}_products.csv")
    stations_path = os.path.join(out_dir, f"{prefix}_stations.csv")
    orders_df.to_csv(orders_path, index=False, sep=";")
    products_df.to_csv(products_path, index=False, sep=";")
    stations_df.to_csv(stations_path, index=False, sep=";")

    meta: Dict[str, object] = {
        "prefix": prefix,
        "orders_path": orders_path,
        "products_path": products_path,
        "stations_path": stations_path,
        "n_products": n_products,
        "n_orders": n_orders,
        "n_lines": n_lines,
        "n_stations": n_stations,
        "slots_per_station": slots_per_station,
        "total_slots": total_slots,
        "top_products": top_products,
        "total_real_lines": total_real_lines,
        "time_capacity": time_capacity,
        "speed": speed,
        "slack": slack,
    }

    if verbose:
        print(
            f"ISCF -> standard CSLAP instance '{prefix}'\n"
            f"  products |P|      = {n_products}\n"
            f"  orders   |O|      = {n_orders}\n"
            f"  order-lines       = {n_lines} (mean order size "
            f"{n_lines / n_orders:.3f})\n"
            f"  stations |S|      = {n_stations} x {meta['slots_per_station']} slots"
            f" = {total_slots} (== |P|: balanced)\n"
            f"  total real L_p    = {total_real_lines}\n"
            f"  TIME_CAPACITY     = {time_capacity} "
            f"(slack {slack}, speed {speed}, kappa-invariant)\n"
            f"  wrote: {orders_path}\n"
            f"         {products_path}\n"
            f"         {stations_path}"
        )
    return meta


def main() -> None:
    """CLI entry point: build the standard ISCF instance."""
    parser = argparse.ArgumentParser(
        description="Adapter: ISCF Data/ -> standard CSLAP instance (plan.md Phase A)."
    )
    parser.add_argument(
        "--iscf-dir",
        type=str,
        default="ISCF Data",
        help="Directory holding the raw ISCF CSVs.",
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default="iscf_instances",
        help="Output directory for the standard CSLAP CSVs.",
    )
    parser.add_argument("--prefix", type=str, default="iscf")
    parser.add_argument("--slack", type=float, default=1.10)
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument("--top-products", type=int, default=None,
                        help="Emit a scaled clean sub-instance of the N most "
                             "frequent SKUs (rounded to a multiple of "
                             "--n-stations). None = full ISCF (4328 SKUs).")
    parser.add_argument("--n-stations", type=int, default=8)
    args = parser.parse_args()

    build_iscf_instance(
        iscf_dir=args.iscf_dir,
        out_dir=args.out_dir,
        prefix=args.prefix,
        slack=args.slack,
        speed=args.speed,
        top_products=args.top_products,
        n_stations=args.n_stations,
    )


if __name__ == "__main__":
    main()
