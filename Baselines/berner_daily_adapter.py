r"""Adapter: dated industrial order lines -> rolling-origin daily folds.

Builds the industrial arm of the workload-feasibility study from
``BERNER_ORDER_LINES_DATE_ASSIGNED_21.csv``, the export obtained from the
partner's WMS specifically for this study. The original extract carried no time
dimension at all, which made the workload constraint untestable out-of-sample:
a station limit is a throughput *rate*, so validating it requires a calendar.
The dated export is a strict subset of the original -- every one of its 284,871
orders and 21,877 SKUs appears in the undated file -- so the article's
industrial setup carries over unchanged; only rows whose delivery date could not
be recovered are absent.

Station handling reproduces ``data_loader_industrial.load_industrial_data``
exactly, so the instance matches the one behind the published industrial
section: the same station canonicalisation, the same three speed classes scaled
by slot count, and ``CAPACITY`` equal to the number of products a station
already holds (assumption A5 -- the catalogue is closed and no location is
empty).

The ``STATION`` column is the **live layout**, which serves two purposes here.
It supplies the incumbent control arm, and under assumption A2 it reveals
capacity: each station's ceiling is a quantile of the daily load it
demonstrably carried, which retires the arbitrary 1.10 slack constant.

At 21,877 SKUs the full placement is not solvable, so ``--top-n`` frees only the
busiest SKUs and pins the rest to their live station, with the freed budget
reduced by what the pinned ones consume (the residual-budget scheme of
``berner_bs_adapter.py``). The selection uses **only the earliest training
weeks**, which every fold's training window contains, so no fold's choice of
free SKUs can depend on data it is later scored on.

No solver is used or imported.

CLI::

    python berner_daily_adapter.py --out <folds_root> [--top-n 2000]
        [--tcap-quantile max] [--min-train-weeks 8] [--test-weeks 4]
"""
from __future__ import annotations

import argparse
import os
import sys
from typing import Dict, Optional

import pandas as pd

BASE: str = os.path.dirname(os.path.abspath(__file__))
_ROOT: str = os.path.dirname(BASE)
sys.path.insert(0, BASE)
sys.path.insert(0, _ROOT)

from daily_folds import QUANTILES, build_daily_folds, week_index  # noqa: E402
from paths import BERNER_RAW, DERIVED  # noqa: E402

DEFAULT_DATA: str = os.path.join(
    BERNER_RAW, "BERNER_ORDER_LINES_DATE_ASSIGNED_21.csv")
DEFAULT_OUT: str = os.path.join(DERIVED, "berner_daily_folds")

#: Station canonicalisation, verbatim from ``data_loader_industrial``.
STATIONS_EXCLUDED = ("01.Z8", "01.15", "01.GED")
STATION_ALIASES = {"01.GE4": "01.E4"}

#: Prefix applied to station ids so CSV round-trips keep them textual.
STATION_PREFIX = "ST_"

#: Throughput classes (lines per unit time before the slot-count division).
STATIC_STATIONS = ("01.E4", "01.31", "01.30")
PALETTE_STATIONS = ("01.01", "01.02", "01.03", "01.04", "01.05")
STATIC_SPEED = 37700.0
PALETTE_SPEED = 57200.0
DYNAMIC_SPEED = 83200.0


def load_dated_orders(path: str) -> pd.DataFrame:
    """Read and canonicalise the dated industrial export.

    Args:
        path: CSV path.

    Returns:
        Frame with ``ORDER``, ``PRODUCT``, ``STATION``, ``DATE``; excluded
        stations dropped and aliases applied.
    """
    df = pd.read_csv(path, usecols=["PRODUCT", "ORDER", "STATION",
                                    "DELIVERY_DATE"], low_memory=False)
    df = df.rename(columns={"DELIVERY_DATE": "DATE"})
    df["PRODUCT"] = df["PRODUCT"].astype(str)
    df["ORDER"] = df["ORDER"].astype(str)
    df["STATION"] = df["STATION"].astype(str).replace(STATION_ALIASES)
    df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce")
    df = df.dropna(subset=["DATE"])
    df = df[~df["STATION"].isin(STATIONS_EXCLUDED)]

    # Station ids such as "01.01" round-trip through CSV as the float 1.01,
    # silently detaching the layout from the station records downstream. The
    # prefix keeps them unambiguously textual wherever pandas infers dtypes.
    df["STATION"] = STATION_PREFIX + df["STATION"]
    return df.reset_index(drop=True)


def incumbent_layout(df: pd.DataFrame) -> Dict[str, str]:
    """Resolve one live station per product.

    A handful of products appear at more than one station across the horizon.
    The most recent order wins, matching ``data_loader_industrial``.

    Args:
        df: Canonicalised order table.

    Returns:
        ``{product: station}``.
    """
    latest = (df.sort_values("ORDER")
                .drop_duplicates(subset=["PRODUCT"], keep="last"))
    return dict(zip(latest["PRODUCT"], latest["STATION"]))


def station_records(df: pd.DataFrame,
                    incumbent: Dict[str, str]) -> pd.DataFrame:
    r"""Build station records with class speeds and held-slot capacities.

    ``CAPACITY`` is the number of products the station already holds, which is
    the article's industrial reading of :math:`\zeta_s`; speeds follow the three
    throughput classes divided by that slot count.

    Args:
        df: Canonicalised order table.
        incumbent: Live layout.

    Returns:
        Frame with ``STATION_ID``, ``CAPACITY``, ``TIME_CAPACITY`` (placeholder,
        overwritten per fold) and ``SPEED``.
    """
    held: Dict[str, int] = {}
    for _p, s in incumbent.items():
        held[s] = held.get(s, 0) + 1

    rows = []
    for s in sorted(df["STATION"].unique()):
        locs = max(held.get(s, 1), 1)
        bare = s[len(STATION_PREFIX):] if s.startswith(STATION_PREFIX) else s
        if bare in STATIC_STATIONS:
            base = STATIC_SPEED
        elif bare in PALETTE_STATIONS:
            base = PALETTE_SPEED
        else:
            base = DYNAMIC_SPEED
        rows.append({"STATION_ID": s, "CAPACITY": locs,
                     "TIME_CAPACITY": 0.0, "SPEED": base / locs})
    return pd.DataFrame(rows)


def select_free_products(df: pd.DataFrame, top_n: Optional[int],
                         min_train_weeks: int) -> Optional[list]:
    """Choose which SKUs stay decision variables.

    Selection is restricted to the earliest ``min_train_weeks``, a window every
    fold's training set contains, so the choice cannot leak information from any
    fold's test week.

    Args:
        df: Canonicalised order table.
        top_n: Keep this many busiest SKUs free; ``None`` frees everything.
        min_train_weeks: Size of the leakage-free selection window.

    Returns:
        The frozen product list, or ``None`` when nothing is frozen.
    """
    if not top_n:
        return None
    weeks = week_index(df["DATE"])
    early = df[weeks < min_train_weeks]
    if early.empty:
        early = df
    ranked = early["PRODUCT"].value_counts()
    free = set(ranked.head(int(top_n)).index)
    frozen = [p for p in df["PRODUCT"].unique() if p not in free]
    return frozen


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Dated BERNER -> rolling-origin daily folds")
    parser.add_argument("--data", type=str, default=DEFAULT_DATA)
    parser.add_argument("--out", type=str, default=DEFAULT_OUT)
    parser.add_argument("--tag", type=str, default="berner_daily")
    parser.add_argument("--top-n", type=int, default=2000,
                        help="Busiest SKUs left free; the rest stay pinned to "
                             "their live station. 0 frees the whole catalogue "
                             "(not solvable at industrial size).")
    parser.add_argument("--tcap-quantile", type=str, default="max",
                        choices=sorted(QUANTILES))
    parser.add_argument("--min-train-weeks", type=int, default=8)
    parser.add_argument("--test-weeks", type=int, default=4)
    args = parser.parse_args()

    print(f"[berner_daily_adapter] reading {args.data}", flush=True)
    df = load_dated_orders(args.data)
    incumbent = incumbent_layout(df)
    stations = station_records(df, incumbent)
    frozen = select_free_products(df, args.top_n, args.min_train_weeks)

    print(f"[berner_daily_adapter] {len(df)} lines | "
          f"{df['ORDER'].nunique()} orders | {df['PRODUCT'].nunique()} SKUs | "
          f"{len(stations)} stations | "
          f"{'all free' if not frozen else f'{args.top_n} free, {len(frozen)} frozen'}",
          flush=True)

    out_dirs = build_daily_folds(
        orders=df[["ORDER", "PRODUCT", "DATE"]],
        stations=stations,
        out_root=args.out,
        tag=args.tag,
        incumbent=incumbent,
        min_train_weeks=args.min_train_weeks,
        n_test_weeks=args.test_weeks,
        tcap_mode="incumbent",
        tcap_quantile=args.tcap_quantile,
        frozen_products=frozen,
        extra_meta={"dataset": "berner", "source": os.path.basename(args.data)},
    )

    # The incumbent is an arm of the experiment, not just a calibration device.
    layout_path = os.path.join(args.out, f"{args.tag}_incumbent_layout.json")
    pd.Series({f"PROD_{p}": s for p, s in incumbent.items()}).to_json(
        layout_path, indent=2)
    print(f"[berner_daily_adapter] wrote {len(out_dirs)} folds -> {args.out}")
    print(f"[berner_daily_adapter] wrote incumbent layout -> {layout_path}")


if __name__ == "__main__":
    main()
