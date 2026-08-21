r"""
Synthetic Data Generator for CSLAP Benchmarking
Strict implementation of Zhang et al. (2019) "Common Itemset" generation.

Optional temporal layer (``--calendar``)
----------------------------------------
The Zhang construction produces an i.i.d. bag of orders with no time dimension,
which is sufficient for a visit-count benchmark but cannot support a workload
*feasibility* study: a station's limit is a throughput rate, so testing it
out-of-sample requires a calendar. The optional calendar layer assigns a
``DELIVERY_DATE`` to every order **without altering the orders themselves** --
the order multiset, its itemset structure and every product frequency are
untouched, so an instance generated with ``--calendar`` aggregates to exactly
the instance generated without it.

Each order is placed on a day with probability proportional to

.. math::
    w_{o,d} \;\propto\; \underbrace{c_d}_{\text{calendar}}
                        \cdot \underbrace{\varepsilon_d}_{\text{common shock}}
                        \cdot \underbrace{g_{K_o,d}}_{\text{itemset shock}}

which reproduces the three features measured on the industrial series:

* ``c_d`` carries the **week-of-month ramp** (month-end is the dominant
  calendar driver) and a mild day-of-week profile;
* ``\varepsilon_d`` is a common lognormal lift shared by every order, giving the
  *common* variance component that a budgeted constraint cannot represent;
* ``g_{K_o,d}`` is a per-itemset lognormal shock, so orders drawn from the same
  common itemset cluster on the same days. Because Zhang itemsets are exactly
  the co-ordered groups, this makes **co-ordered products co-spike** -- the
  load-concentration mechanism the robustness study is about -- and it also
  supplies the overdispersion (Fano > 1) that popular SKUs show in practice.

Calibration defaults are taken from the industrial reference series (13 weeks,
63 working days) rather than invented; see ``Baselines/demand_diagnostics.py``,
which measures the same quantities on any dated order table and is how a
generated instance is checked against those targets.

``--drift`` adds a deterministic linear trend in daily volume across the
horizon, so demand growth between an early training window and a late test
window becomes a controlled dial rather than an accident of the data.

**Backward compatibility is exact.** Without ``--calendar`` the RNG stream, the
column set and every byte of output are unchanged; the calendar draws come from
a dedicated stream, the same discipline already used for ``station_rng``.
"""

import numpy as np
import pandas as pd
import os
import argparse
from typing import Dict, List, Optional, Sequence, Tuple

#: Week-of-month volume index measured on the industrial series (days 1-7,
#: 8-14, 15-21, 22-28, 29-35). Month-end is the dominant calendar driver.
_WOM_PROFILE: Tuple[float, ...] = (0.85, 0.93, 1.02, 1.09, 1.27)

#: Day-of-week volume index, Monday first. Weak (~7% of daily variance).
_DOW_PROFILE: Tuple[float, ...] = (0.93, 0.98, 1.08, 1.05, 0.97)

#: Offset for the calendar RNG stream. Isolating it means enabling the calendar
#: cannot desynchronise the order stream (cf. ``station_rng``).
_CALENDAR_STREAM_OFFSET: int = 15486277

def _lognormal_unit_mean(rng, cv: float, size) -> np.ndarray:
    r"""Lognormal draws with mean exactly 1 and coefficient of variation ``cv``.

    Unit mean matters: the shocks multiply a base intensity, so any drift in
    their mean would silently change total volume instead of only its shape.

    Args:
        rng: ``RandomState`` to draw from (the dedicated calendar stream).
        cv: Target coefficient of variation. ``0`` returns exact ones.
        size: Output shape.

    Returns:
        Array of positive multipliers with :math:`\mathbb{E}[x] = 1`.
    """
    if cv <= 0:
        return np.ones(size, dtype=float)
    sigma = np.sqrt(np.log(1.0 + cv * cv))
    return np.exp(rng.normal(-0.5 * sigma * sigma, sigma, size=size))


def _business_days(start_date: str, n_days: int) -> pd.DatetimeIndex:
    """Return ``n_days`` consecutive business days starting at ``start_date``."""
    return pd.bdate_range(start=start_date, periods=n_days)


def _calendar_factor(days: pd.DatetimeIndex,
                     month_end_index: float) -> np.ndarray:
    r"""Deterministic calendar intensity :math:`c_d`, normalised to mean 1.

    Combines the week-of-month ramp (the dominant driver: month-end runs well
    above month-start) with the weak day-of-week profile. ``month_end_index``
    rescales the amplitude of the ramp so the last week-of-month bucket sits at
    the requested multiple of the mean; ``1.0`` flattens the calendar entirely.

    Args:
        days: The horizon.
        month_end_index: Target index of the final week-of-month bucket.

    Returns:
        Array of length ``len(days)`` with mean 1.
    """
    wom_bucket = np.clip((days.day.to_numpy() - 1) // 7, 0, len(_WOM_PROFILE) - 1)
    wom = np.asarray(_WOM_PROFILE, dtype=float)[wom_bucket]
    wom = wom / wom.mean()

    # Rescale the ramp so the last bucket lands on the requested index.
    last_rel = float(_WOM_PROFILE[-1] / np.mean(_WOM_PROFILE))
    if abs(last_rel - 1.0) > 1e-9:
        amplitude = (month_end_index - 1.0) / (last_rel - 1.0)
        wom = 1.0 + amplitude * (wom - 1.0)
    wom = np.maximum(wom, 1e-6)

    dow_idx = np.clip(days.dayofweek.to_numpy(), 0, len(_DOW_PROFILE) - 1)
    dow = np.asarray(_DOW_PROFILE, dtype=float)[dow_idx]

    factor = wom * dow
    return factor / factor.mean()


def assign_order_dates(
    order_itemsets: Sequence[Sequence[int]],
    num_itemsets: int,
    days: pd.DatetimeIndex,
    cal_rng,
    residual_cv: float,
    month_end_index: float,
    cospike_cv: float,
    drift: float,
) -> np.ndarray:
    r"""Place each order on a day, preserving the order multiset exactly.

    Order ``o`` lands on day ``d`` with probability proportional to
    :math:`c_d \cdot t_d \cdot \varepsilon_d \cdot g_{K_o,d}`, where ``c`` is the
    calendar factor, ``t`` the linear drift trend, :math:`\varepsilon` a common
    lognormal shock and :math:`g` the geometric mean of the daily shocks of the
    itemsets order ``o`` was built from.

    Orders sharing an itemset therefore concentrate on the same days, which is
    what makes co-ordered products co-spike. Orders assembled purely from random
    fill carry no itemset shock and follow the common factor alone.

    Args:
        order_itemsets: For each order, the indices of the common itemsets used
            to build it (possibly empty).
        num_itemsets: Total number of common itemsets.
        days: Horizon.
        cal_rng: Dedicated ``RandomState`` for the calendar layer.
        residual_cv: CV of the common daily shock, i.e. the aggregate daily
            volume noise left after calendar structure is removed.
        month_end_index: See :func:`_calendar_factor`.
        cospike_cv: CV of the per-itemset daily shock. Drives both the co-spike
            correlation and the overdispersion of popular SKUs; ``0`` disables
            co-spiking entirely.
        drift: Fractional volume growth across the horizon. ``0.3`` means the
            last day runs 30% above the first; ``0`` is stationary.

    Returns:
        Integer array of day indices, one per order, aligned with
        ``order_itemsets``.
    """
    n_days = len(days)
    n_orders = len(order_itemsets)

    base = _calendar_factor(days, month_end_index)
    base = base * _lognormal_unit_mean(cal_rng, residual_cv, n_days)
    if drift:
        trend = 1.0 + drift * (np.arange(n_days, dtype=float) /
                               max(n_days - 1, 1))
        base = base * trend
    base = np.maximum(base, 1e-12)

    if cospike_cv > 0 and num_itemsets > 0:
        log_shock = np.log(
            _lognormal_unit_mean(cal_rng, cospike_cv, (num_itemsets, n_days)))
    else:
        log_shock = np.zeros((max(num_itemsets, 1), n_days), dtype=float)

    # Orders sharing an itemset signature share a day distribution, so the
    # weight vector is built once per distinct signature rather than per order.
    groups: Dict[Tuple[int, ...], List[int]] = {}
    for oi, sets_used in enumerate(order_itemsets):
        groups.setdefault(tuple(sorted(set(sets_used))), []).append(oi)

    out = np.empty(n_orders, dtype=int)
    for signature, members in groups.items():
        if signature:
            effect = np.exp(log_shock[list(signature), :].mean(axis=0))
        else:
            effect = np.ones(n_days, dtype=float)
        weight = base * effect
        cdf = np.cumsum(weight)
        cdf /= cdf[-1]
        draws = cal_rng.random_sample(len(members))
        out[np.asarray(members, dtype=int)] = np.searchsorted(cdf, draws)

    return np.clip(out, 0, n_days - 1)


def generate_synthetic_data_zhang(
    num_skus,
    theta=0.7,
    seed=42,
    output_dir="synthetic_datasets",
    num_stations=None,
    prefix=None,
    calendar=False,
    days=63,
    start_date="2021-09-01",
    residual_cv=0.167,
    month_end_index=1.27,
    cospike_cv=0.35,
    drift=0.0,
):
    """Generate one Zhang-style synthetic CSLAP instance.

    ``num_stations`` defaults to the historical ``max(5, num_skus // 100)``. When
    it is left at None the whole generator, including the RNG stream, behaves
    exactly as before, so the cached EXP-02a instances regenerate byte-identically.

    When ``num_stations`` IS given explicitly, the per-line historical-station
    label is drawn from a SEPARATE RNG stream. ``RandomState.randint`` consumes a
    range-dependent number of words through its rejection sampling, so drawing
    the station label from the main stream would desynchronise every later draw
    (including QTY) as soon as |S| changed. Isolating it means the order
    structure - sizes, itemsets, product fills, quantities - is identical across
    station counts at a fixed seed, so a sweep over |S| varies the station
    capacity zeta = floor(N/|S|) and nothing else.

    ``prefix`` overrides the output file stem (default ``syn_{num_skus}sku``).

    Temporal layer (all inert unless ``calendar=True``):

    * ``days`` / ``start_date`` -- horizon length in business days and its start.
      The default 63 matches the industrial reference window (13 weeks).
    * ``residual_cv`` -- CV of the common daily shock, i.e. the aggregate volume
      noise remaining once calendar structure is removed.
    * ``month_end_index`` -- volume index of the final week-of-month bucket
      relative to the mean; ``1.0`` removes the calendar ramp.
    * ``cospike_cv`` -- CV of the per-itemset daily shock. Controls how strongly
      co-ordered products surge together, and with it the overdispersion of
      popular SKUs. ``0`` makes days independent of itemset membership.
    * ``drift`` -- fractional volume growth across the horizon (``0.3`` = last
      day 30% above the first). ``0`` is stationary.

    With ``calendar=True`` the orders gain a ``DELIVERY_DATE`` column and the
    station ``TIME_CAPACITY`` becomes a *daily* line capacity; the orders
    themselves are unchanged, so the instance still aggregates to the
    undated one.
    """
    rng = np.random.RandomState(seed)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # --- 1. SKU Pool ---
    products = np.arange(1, num_skus + 1)

    # --- 2. Common Itemsets ---
    # Number of common itemsets is proportional to N: N * U[0.1, 0.5]
    num_itemsets = int(num_skus * rng.uniform(0.1, 0.5))
    num_itemsets = max(num_itemsets, 1)

    itemsets = []
    for _ in range(num_itemsets):
        # Size of common itemset: U[2, 5]
        size = rng.randint(2, 6)
        itemset = rng.choice(products, size=size, replace=False).tolist()
        itemsets.append(itemset)

    # --- 3. Orders ---
    # Number of orders is proportional to N: N * U[30, 50]
    num_orders = int(num_skus * rng.uniform(30.0, 50.0))

    # --- 4. Stations (Flat Setup) ---
    # station_rng is the main stream in the historical path (so nothing changes)
    # and a dedicated stream whenever |S| is set explicitly (see the docstring).
    if num_stations is None:
        num_stations = max(5, num_skus // 100)
        station_rng = rng
    else:
        num_stations = int(num_stations)
        if num_stations < 1 or num_stations > num_skus:
            raise ValueError(
                f"num_stations must be in [1, num_skus={num_skus}], got {num_stations}")
        station_rng = np.random.RandomState(seed + 999983)

    # Exact slot capacity to ensure uniform product counts across stations
    base_cap = num_skus // num_stations
    capacities = np.full(num_stations, base_cap)
    
    station_ids = np.arange(1, num_stations + 1)
    # Uniform speeds for all stations
    speeds = np.ones(num_stations)

    # --- 5. Generate Orders with Batch Correlation Injection ---
    order_data = []
    # Which common itemsets each order was built from, in generation order.
    # Recording consumes no randomness, so it is collected unconditionally and
    # leaves the non-calendar output bit-for-bit unchanged. The calendar layer
    # needs it to make orders sharing an itemset land on the same days.
    order_itemsets = []

    for order_id in range(1, num_orders + 1):
        # Size of an order: U[5, 15]
        target_size = rng.randint(5, 16)
        current_order_items = []
        used_sets = []

        # A decimal within [0, 1] is randomly generated
        prob = rng.uniform(0.0, 1.0)

        # If decimal is less than theta, one to three common itemsets are picked
        if prob < theta:
            num_sets_to_add = rng.randint(1, 4)
            for _ in range(num_sets_to_add):
                chosen_idx = rng.randint(0, len(itemsets))
                chosen_set = itemsets[chosen_idx]
                used_sets.append(chosen_idx)
                current_order_items.extend(chosen_set)
                if len(current_order_items) >= target_size:
                    break

        order_itemsets.append(used_sets)

        # If the order is not fulfilled, fill with random items from N
        while len(current_order_items) < target_size:
            current_order_items.append(rng.choice(products))

        # Truncate in case bulk itemset addition exceeded target_size
        current_order_items = current_order_items[:target_size]

        # Zhang et al. notes an item can appear more than once in an order
        for prod in current_order_items:
            original_station = station_rng.randint(1, num_stations + 1)
            order_data.append({
                "ORDER": f"ORD_{order_id}",
                "PRODUCT": f"PROD_{prod}",
                "QTY": int(rng.randint(1, 10)),
                "STATION": original_station,
            })

    df_orders = pd.DataFrame(order_data)

    # --- 5b. Optional temporal layer (no effect when calendar is False) ---
    if calendar:
        cal_rng = np.random.RandomState(seed + _CALENDAR_STREAM_OFFSET)
        days_index = _business_days(start_date, days)
        order_day = assign_order_dates(
            order_itemsets, len(itemsets), days_index, cal_rng,
            residual_cv=residual_cv, month_end_index=month_end_index,
            cospike_cv=cospike_cv, drift=drift,
        )
        # Orders were emitted as ORD_1..ORD_num_orders in generation order, so
        # entry k-1 of order_day is the day of ORD_k.
        order_num = df_orders["ORDER"].str.slice(4).astype(int).to_numpy()
        df_orders["DELIVERY_DATE"] = days_index[
            order_day[order_num - 1]].strftime("%Y-%m-%d")

    # --- 6. Products DataFrame ---
    prod_freq = df_orders.groupby("PRODUCT").size().reset_index(name="FREQUENCY")
    all_prods = pd.DataFrame({"PRODUCT_ID": products})
    all_prods["PRODUCT"] = all_prods["PRODUCT_ID"].apply(lambda x: f"PROD_{x}")
    all_prods = all_prods.merge(prod_freq, on="PRODUCT", how="left")
    all_prods["FREQUENCY"] = all_prods["FREQUENCY"].fillna(0).astype(int)
    all_prods["CATEGORY"] = rng.randint(0, max(5, num_skus // 25), size=num_skus)
    all_prods["POPULARITY"] = all_prods["FREQUENCY"]

    df_products = all_prods[["PRODUCT_ID", "CATEGORY", "POPULARITY"]].copy()

    # --- 6.5. Constructive Feasibility for Workload Capacity ---
    # We guarantee feasibility by enforcing a flat workload ceiling across all stations.
    # Total workload = sum of all product frequencies
    total_workload = all_prods["FREQUENCY"].sum()
    
    # Mathematical average if spread perfectly
    target_workload_per_station = total_workload / num_stations
    
    # Calculate a dynamic slack factor between 10% and 30% depending on constraints
    #slack_factor = max(1.10, min(1.30, 20 / num_stations))
    slack_factor = 1.10 
    # Fix the workload capacity identical across all stations
    flat_time_cap = int(np.ceil(target_workload_per_station * slack_factor))

    if calendar:
        # A1: with a calendar present the ceiling is a DAILY throughput, not a
        # total over the horizon. The synthetic warehouse has no operating
        # history to reveal capacity from (its STATION column is a random
        # label, not a live layout), so the design point is the busiest day
        # shared equally across stations -- the balanced analogue of revealed
        # capacity, and free of any arbitrary slack constant. daily_folds.py
        # recomputes this per quantile, so this is only the instance default.
        lines_per_day = df_orders.groupby("DELIVERY_DATE").size()
        flat_time_cap = int(np.ceil(float(lines_per_day.max()) / num_stations))

    time_capacities = np.full(num_stations, flat_time_cap)

    df_stations = pd.DataFrame({
        "STATION_ID": station_ids,
        "CAPACITY": capacities,
        "TIME_CAPACITY": time_capacities,
        "SPEED": speeds,
    })

    # --- 7. Save ---
    if prefix is None:
        prefix = f"syn_{num_skus}sku"
    df_orders.to_csv(os.path.join(output_dir, f"{prefix}_orders.csv"), index=False, sep=";")
    df_stations.to_csv(os.path.join(output_dir, f"{prefix}_stations.csv"), index=False, sep=";")
    df_products.to_csv(os.path.join(output_dir, f"{prefix}_products.csv"), index=False, sep=";")

    msg = (f"[Zhang Generator] N={num_skus} | Stations: {num_stations} "
           f"| Zeta: {base_cap} | Orders: {num_orders} | Itemsets: {num_itemsets}")
    if calendar:
        msg += (f" | Days: {days} ({start_date}+) | T_s/day: {flat_time_cap} "
                f"| drift={drift:g} cospike_cv={cospike_cv:g}")
    print(msg)
    return df_orders, df_stations, df_products

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sizes", nargs="+", type=int, default=[500, 1000, 2000, 5000])
    parser.add_argument("--theta", type=float, default=0.7)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output_dir", type=str, default="synthetic_datasets")
    parser.add_argument("--num-stations", type=int, default=None,
                        help="Station count |S| (default: max(5, N//100), the "
                             "historical formula). Setting it explicitly also "
                             "isolates the station-label RNG stream.")
    parser.add_argument("--calendar", action="store_true",
                        help="Emit DELIVERY_DATE and a daily TIME_CAPACITY. "
                             "Without this flag the output is byte-identical "
                             "to the published instances.")
    parser.add_argument("--days", type=int, default=63,
                        help="Business days in the horizon (default 63 = the "
                             "13-week industrial reference window).")
    parser.add_argument("--start-date", type=str, default="2021-09-01")
    parser.add_argument("--residual-cv", type=float, default=0.167,
                        help="CV of the common daily shock (aggregate volume "
                             "noise net of calendar structure).")
    parser.add_argument("--month-end-index", type=float, default=1.27,
                        help="Volume index of the final week-of-month bucket; "
                             "1.0 flattens the calendar ramp.")
    parser.add_argument("--cospike-cv", type=float, default=0.35,
                        help="CV of the per-itemset daily shock: how strongly "
                             "co-ordered products surge together. 0 disables.")
    parser.add_argument("--drift", type=float, default=0.0,
                        help="Fractional volume growth across the horizon "
                             "(0.3 = last day 30%% above the first).")
    args = parser.parse_args()

    for sku_size in args.sizes:
        generate_synthetic_data_zhang(
            num_skus=sku_size,
            theta=args.theta,
            seed=args.seed,
            output_dir=args.output_dir,
            num_stations=args.num_stations,
            calendar=args.calendar,
            days=args.days,
            start_date=args.start_date,
            residual_cv=args.residual_cv,
            month_end_index=args.month_end_index,
            cospike_cv=args.cospike_cv,
            drift=args.drift,
        )