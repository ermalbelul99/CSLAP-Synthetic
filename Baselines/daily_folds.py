r"""Rolling-origin daily folds for the workload-feasibility study.

Shared fold builder behind both the industrial and the synthetic adapters. It
replaces the study's earlier protocol, which split the order *list* by rank and
compared a test window against a ceiling calibrated on a training window of a
different length. Two things change here.

**Splitting is by date, and test windows are disjoint.** The earlier expanding
cuts (50/50, 60/40 ... 90/10) were *nested*: every training window contained the
previous one and the test windows overlapped heavily, so "5 of 5 folds agree"
was far weaker evidence than it read and no confidence interval was defensible.
Rolling origin keeps the natural expanding-history structure a planner actually
faces, while each fold is scored on a **week no other fold is scored on**.

**The ceiling is a daily rate.** ``TIME_CAPACITY`` becomes a per-day line
capacity and ``REAL_LINES`` a per-day mean, which is what the published model
always meant: it defines :math:`V_s` as "a processing rate in lines per unit
time" and :math:`T_s` as a budget in the units of :math:`\sum_p L_p/V_s`. No
model changes -- the same columns now carry rates instead of window totals, so
the robust MILP consumes them unaltered.

Capacity is *revealed*, never assumed (assumption A2). Two modes:

``incumbent``
    Each station's ceiling is a quantile of the daily load it demonstrably
    carried under the live layout. Defensible in one sentence to an industrial
    partner -- *the station did this, so it can do this* -- and it retires the
    arbitrary 1.10 slack constant.
``balanced``
    For a synthetic warehouse, which has no operating history (its station
    labels are random), the ceiling is an equal share of a quantile *day*.

Both write ``station_daily_loads.csv`` so the quantile can be swept in the
harness without rebuilding folds, and ``fold_meta.json`` so a run cannot
silently apply window-block calibration to daily folds.

No solver is used or imported.
"""
from __future__ import annotations

import json
import math
import os
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

#: Quantile aliases accepted for the revealed-capacity rule (A2).
QUANTILES: Dict[str, float] = {"p90": 0.90, "p95": 0.95, "max": 1.00}


def week_index(dates: pd.Series) -> pd.Series:
    """Map dates to a 0-based ISO week ordinal, contiguous over the horizon."""
    periods = dates.dt.to_period("W")
    uniq = {p: i for i, p in enumerate(sorted(periods.unique()))}
    return periods.map(uniq)


def rolling_origin_weeks(n_weeks: int, min_train_weeks: int,
                         n_test_weeks: int) -> List[Tuple[List[int], List[int]]]:
    """Enumerate (train weeks, test weeks) with non-overlapping test windows.

    Args:
        n_weeks: Number of distinct weeks in the horizon.
        min_train_weeks: Weeks of history before the first evaluation.
        n_test_weeks: How many folds to emit; each scores one later week.

    Returns:
        List of ``(train_week_indices, test_week_indices)``. Empty if the
        horizon is too short.
    """
    folds: List[Tuple[List[int], List[int]]] = []
    first_test = min_train_weeks
    last_test = min(n_weeks - 1, first_test + n_test_weeks - 1)
    for t in range(first_test, last_test + 1):
        folds.append((list(range(0, t)), [t]))
    return folds


def station_daily_loads(orders: pd.DataFrame,
                        assignment: Optional[Dict[str, str]],
                        station_ids: Sequence[str]) -> pd.DataFrame:
    r"""Realised daily pick-lines per station under a fixed layout.

    Args:
        orders: Rows with ``PRODUCT`` and ``DATE``.
        assignment: ``{product: station}``. When ``None`` the caller wants the
            balanced mode and only the daily totals matter.
        station_ids: Station order for the returned columns.

    Returns:
        Frame indexed by date, one column per station, values in pick-lines.
    """
    if assignment is None:
        total = orders.groupby("DATE").size()
        share = pd.DataFrame(
            {s: total / float(len(station_ids)) for s in station_ids})
        return share

    mapped = orders["PRODUCT"].map(assignment)
    sub = orders.assign(STATION=mapped).dropna(subset=["STATION"])
    piv = (sub.groupby(["DATE", "STATION"]).size().unstack(fill_value=0)
              .reindex(columns=list(station_ids), fill_value=0))
    return piv


def _ceiling_from_loads(loads: pd.DataFrame, speeds: Dict[str, float],
                        quantile: str) -> Dict[str, float]:
    r"""Daily time-capacity per station from realised loads (assumption A2).

    ``TIME_CAPACITY`` is compared against :math:`\sum_p L_p / V_s`, so the
    quantile of realised *lines* is divided by the station speed to land in the
    same units.
    """
    q = QUANTILES[quantile]
    out: Dict[str, float] = {}
    for s in loads.columns:
        col = loads[s].to_numpy(dtype=float)
        val = float(col.max()) if q >= 1.0 else float(np.quantile(col, q))
        out[str(s)] = val / max(speeds.get(str(s), 1.0), 1e-12)
    return out


def build_daily_folds(
    orders: pd.DataFrame,
    stations: pd.DataFrame,
    out_root: str,
    tag: str,
    incumbent: Optional[Dict[str, str]] = None,
    min_train_weeks: int = 8,
    n_test_weeks: int = 4,
    tcap_mode: str = "incumbent",
    tcap_quantile: str = "max",
    product_prefix: str = "PROD_",
    frozen_products: Optional[Sequence[str]] = None,
    extra_meta: Optional[Dict[str, object]] = None,
) -> List[str]:
    r"""Write rolling-origin daily folds in the established instance schema.

    Args:
        orders: Long order table with ``ORDER``, ``PRODUCT`` (bare id, no
            prefix), ``DATE`` and optionally ``QTY``.
        stations: Records with ``STATION_ID``, ``CAPACITY``, ``SPEED``.
        out_root: Root directory; one subdirectory per fold is created.
        tag: Instance tag, used as the fold-file stem.
        incumbent: ``{bare product id: station}`` live layout. Required for
            ``tcap_mode="incumbent"``.
        min_train_weeks: History before the first scored week.
        n_test_weeks: Number of folds (one scored week each, disjoint).
        tcap_mode: ``"incumbent"`` or ``"balanced"`` (see module docstring).
        tcap_quantile: Key of :data:`QUANTILES`.
        product_prefix: Token prefix the solver expects (``PROD_``).
        extra_meta: Merged into ``fold_meta.json``.

    Returns:
        The fold directory paths written.

    Raises:
        ValueError: On an unusable horizon, an unknown mode/quantile, or a
            missing incumbent layout.
    """
    if tcap_quantile not in QUANTILES:
        raise ValueError(f"tcap_quantile must be one of {sorted(QUANTILES)}")
    if tcap_mode not in ("incumbent", "balanced"):
        raise ValueError("tcap_mode must be 'incumbent' or 'balanced'")
    if tcap_mode == "incumbent" and not incumbent:
        raise ValueError("tcap_mode='incumbent' requires an incumbent layout")

    orders = orders.copy()
    orders["DATE"] = pd.to_datetime(orders["DATE"])
    orders["WEEK"] = week_index(orders["DATE"])
    n_weeks = int(orders["WEEK"].max()) + 1

    folds = rolling_origin_weeks(n_weeks, min_train_weeks, n_test_weeks)
    if not folds:
        raise ValueError(
            f"{tag}: horizon has {n_weeks} weeks, too short for "
            f"min_train_weeks={min_train_weeks}. Lower it or extend the data.")

    station_ids = [str(s) for s in stations["STATION_ID"]]
    speeds = {str(r["STATION_ID"]): float(r["SPEED"])
              for _, r in stations.iterrows()}

    # Partial re-optimisation: at industrial catalogue size the full placement
    # is not solvable, so a subset stays pinned to its live station and the
    # budget offered to the free SKUs is what remains after the pinned ones
    # have taken their share (the residual-budget scheme of
    # berner_bs_adapter.py). Frozen SKUs still consume slots and workload; they
    # are simply not decision variables.
    frozen = {str(p) for p in (frozen_products or ())}
    all_products = sorted(orders["PRODUCT"].astype(str).unique())
    universe = [p for p in all_products if p not in frozen]
    if frozen and not universe:
        raise ValueError(f"{tag}: every product is frozen; nothing to place")

    free_orders = (orders[~orders["PRODUCT"].astype(str).isin(frozen)]
                   if frozen else orders)

    os.makedirs(out_root, exist_ok=True)
    written: List[str] = []

    for f_i, (tr_weeks, te_weeks) in enumerate(folds):
        tr_all = orders[orders["WEEK"].isin(tr_weeks)]
        te_all = orders[orders["WEEK"].isin(te_weeks)]
        tr = free_orders[free_orders["WEEK"].isin(tr_weeks)]
        te = free_orders[free_orders["WEEK"].isin(te_weeks)]
        tr_days = tr_all["DATE"].nunique()
        te_days = te_all["DATE"].nunique()
        if tr_days == 0 or te_days == 0:
            continue

        # A1: REAL_LINES is a per-day mean, not a window total.
        tr_lines = tr.groupby("PRODUCT").size()
        lbar = (tr_lines / float(tr_days)).astype(float)

        # A2: the ceiling is the daily load the incumbent demonstrably carried.
        # With frozen SKUs the budget offered to the free ones is derived from
        # what the *free* SKUs themselves consumed, not from the station total
        # minus the frozen total. Those two differ: a station's busiest total
        # day and its busiest frozen day are usually different dates, so
        # subtracting one maximum from the other removes headroom that was
        # never occupied simultaneously and would report the live layout as
        # infeasible against its own history.
        loads_total = station_daily_loads(
            tr_all, incumbent if tcap_mode == "incumbent" else None, station_ids)
        loads = (station_daily_loads(tr, incumbent, station_ids)
                 if frozen else loads_total)
        tcap = _ceiling_from_loads(loads, speeds, tcap_quantile)

        prod_df = pd.DataFrame({"PRODUCT_ID": universe})
        prod_df["CATEGORY"] = 0
        prod_df["POPULARITY"] = prod_df["PRODUCT_ID"].map(
            tr_lines).fillna(0.0).astype(float).round(6)
        prod_df["REAL_LINES"] = prod_df["PRODUCT_ID"].map(
            lbar).fillna(0.0).astype(float).round(6)

        st_df = stations.copy()
        st_df["STATION_ID"] = st_df["STATION_ID"].astype(str)
        st_df["TIME_CAPACITY"] = st_df["STATION_ID"].map(tcap).astype(float)

        if frozen and incumbent:
            # Frozen SKUs keep occupying their slots, so the free placement may
            # only use what is left (A5: no location is ever empty).
            held: Dict[str, int] = {}
            for p in frozen:
                s = incumbent.get(p)
                if s is not None:
                    held[str(s)] = held.get(str(s), 0) + 1
            st_df["CAPACITY"] = [
                max(int(c) - held.get(str(s), 0), 0)
                for s, c in zip(st_df["STATION_ID"], st_df["CAPACITY"])
            ]

        fold_tag = f"{tag}_r0f{f_i}"
        out_dir = os.path.join(out_root, fold_tag)
        os.makedirs(out_dir, exist_ok=True)

        for role, odf in (("train", tr), ("test", te)):
            cols = ["ORDER", "PRODUCT"]
            if "QTY" in odf.columns:
                cols.append("QTY")
            emit = odf[cols + ["DATE"]].copy()
            emit["PRODUCT"] = product_prefix + emit["PRODUCT"].astype(str)
            # The evaluator groups the test set by day; the train file carries
            # the same column so lhat can be calibrated across real days.
            emit["DELIVERY_DATE"] = emit["DATE"].dt.strftime("%Y-%m-%d")
            emit = emit.drop(columns=["DATE"])
            emit.to_csv(os.path.join(out_dir, f"{fold_tag}_{role}_orders.csv"),
                        index=False, sep=";")
            prod_df.to_csv(
                os.path.join(out_dir, f"{fold_tag}_{role}_products.csv"),
                index=False, sep=";")
            st_df.to_csv(
                os.path.join(out_dir, f"{fold_tag}_{role}_stations.csv"),
                index=False, sep=";")

        # The basis T_s is derived from, so the harness can re-derive any
        # quantile without rebuilding folds. The station total is kept beside it
        # for diagnostics when part of the catalogue is frozen.
        loads.to_csv(os.path.join(out_dir, "station_daily_loads.csv"))
        if frozen:
            loads_total.to_csv(
                os.path.join(out_dir, "station_daily_loads_total.csv"))

        missing = int(sum(1 for p in universe if p not in set(tr["PRODUCT"].astype(str))))
        meta: Dict[str, object] = {
            "granularity": "daily",
            "tag": tag,
            "fold": f_i,
            "fold_tag": fold_tag,
            "train_weeks": tr_weeks,
            "test_weeks": te_weeks,
            "train_days": int(tr_days),
            "test_days": int(te_days),
            "train_date_min": str(tr["DATE"].min().date()),
            "train_date_max": str(tr["DATE"].max().date()),
            "test_date_min": str(te["DATE"].min().date()),
            "test_date_max": str(te["DATE"].max().date()),
            "n_products": len(universe),
            "n_products_frozen": len(frozen),
            "n_products_total": len(all_products),
            "n_products_missing_from_train": missing,
            "n_stations": len(station_ids),
            "tcap_mode": tcap_mode,
            "tcap_quantile": tcap_quantile,
            "mean_daily_lines_train": float(len(tr)) / float(tr_days),
            "mean_daily_lines_test": float(len(te)) / float(te_days),
        }
        if extra_meta:
            meta.update(extra_meta)
        with open(os.path.join(out_dir, "fold_meta.json"), "w",
                  encoding="utf-8") as fh:
            json.dump(meta, fh, indent=2)

        if missing:
            # A5 assumes a closed universe: every SKU has a home, so a SKU
            # absent from training would have no basis for placement.
            print(f"[daily_folds] WARNING {fold_tag}: {missing} products absent "
                  f"from train -- closed-universe assumption A5 violated",
                  flush=True)

        print(f"[daily_folds] {fold_tag}: train {meta['train_date_min']}"
              f"..{meta['train_date_max']} ({tr_days}d) -> test "
              f"{meta['test_date_min']}..{meta['test_date_max']} ({te_days}d) "
              f"| lines/day tr {meta['mean_daily_lines_train']:.0f} "
              f"te {meta['mean_daily_lines_test']:.0f}", flush=True)
        written.append(out_dir)

    return written
