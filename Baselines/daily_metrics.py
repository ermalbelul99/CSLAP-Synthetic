r"""Daily workload-feasibility table for stored layouts.

Scores every layout of every fold against a daily ceiling and writes one tidy
CSV. Kept separate from the solve deliberately: the layouts are the expensive
artefact, and re-scoring them is cheap, so the revealed-capacity sweep of
assumption A2 costs nothing. Tightening the ceiling from ``max`` to ``p95`` to
``p90`` is a re-read of ``station_daily_loads.csv``, not a re-solve -- which is
what makes q a reported sensitivity axis rather than an arbitrary constant
chosen once.

Arms scored:

* ``incumbent`` -- the live layout, taken from the ``WARM_STATION`` column the
  fold builder writes. Present only on the industrial instances; the synthetic
  ``STATION`` label is random and is not an operating layout.
* every ``layout_*.json`` the harness persisted (nominal, robust, tightened).

Both train and test are scored. Train is the control: under A2 at ``q=max`` the
incumbent is feasible on its own history by construction, so a violation there
means the ceiling was built wrong, not that the layout is bad.

No solver is used or imported.

CLI::

    python daily_metrics.py --folds <folds_root> [--results <results_root>]
        [--quantiles max p95 p90] [--out <csv>]
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

BASE: str = os.path.dirname(os.path.abspath(__file__))
_ROOT: str = os.path.dirname(BASE)
sys.path.insert(0, BASE)
sys.path.insert(0, _ROOT)

from evaluate_layout_robust import (  # noqa: E402
    evaluate_layout_daily,
    load_daily_orders,
    load_layout,
)
from paths import RESULTS  # noqa: E402

QUANTILES: Dict[str, float] = {"p90": 0.90, "p95": 0.95, "max": 1.00}


def ceilings(loads: pd.DataFrame, stations: List[dict],
             quantile: str) -> List[dict]:
    """Return station records with ``TIME_CAPACITY`` set at ``quantile``."""
    q = QUANTILES[quantile]
    out = []
    for rec in stations:
        rec = dict(rec)
        sid = str(rec["STATION_ID"])
        if sid in loads.columns:
            col = loads[sid].to_numpy(dtype=float)
            val = float(col.max()) if q >= 1.0 else float(np.quantile(col, q))
            rec["TIME_CAPACITY"] = val / max(float(rec["SPEED"]), 1e-12)
        out.append(rec)
    return out


def incumbent_from_products(products: pd.DataFrame) -> Optional[Dict[str, str]]:
    """Recover the live layout from a fold's ``WARM_STATION`` column."""
    if "WARM_STATION" not in products.columns:
        return None
    pairs = {
        f"PROD_{pid}": str(sid)
        for pid, sid in zip(products["PRODUCT_ID"], products["WARM_STATION"])
        if pd.notna(sid) and str(sid) and str(sid).lower() != "nan"
    }
    return pairs or None


def collect_layouts(results_root: Optional[str],
                    fold_tag: str) -> Dict[str, Dict[str, str]]:
    """Find every persisted layout belonging to one fold.

    Args:
        results_root: Directory the harness wrote to, or ``None``.
        fold_tag: e.g. ``berner_daily_r0f0``.

    Returns:
        ``{arm_name: layout}``.
    """
    found: Dict[str, Dict[str, str]] = {}
    if not results_root or not os.path.isdir(results_root):
        return found
    pattern = os.path.join(results_root, "**", f"layout_{fold_tag}*.json")
    for path in sorted(glob.glob(pattern, recursive=True)):
        arm = os.path.splitext(os.path.basename(path))[0]
        arm = arm.replace(f"layout_{fold_tag}", "").lstrip("_") or "layout"
        try:
            found[arm] = load_layout(path)
        except (ValueError, json.JSONDecodeError, OSError) as exc:
            print(f"[daily_metrics] skipping {path}: {exc}", flush=True)
    return found


def score_fold(fold_dir: str, results_root: Optional[str],
               quantiles: List[str]) -> List[dict]:
    """Score every arm of one fold at every ceiling quantile."""
    meta_path = os.path.join(fold_dir, "fold_meta.json")
    if not os.path.isfile(meta_path):
        return []
    with open(meta_path, encoding="utf-8") as fh:
        meta = json.load(fh)
    tag = meta["fold_tag"]

    stations = pd.read_csv(
        os.path.join(fold_dir, f"{tag}_train_stations.csv"),
        sep=";").to_dict("records")
    products = pd.read_csv(
        os.path.join(fold_dir, f"{tag}_train_products.csv"), sep=";")
    loads = pd.read_csv(
        os.path.join(fold_dir, "station_daily_loads.csv"), index_col=0)
    loads.columns = [str(c) for c in loads.columns]

    arms: Dict[str, Dict[str, str]] = {}
    inc = incumbent_from_products(products)
    if inc:
        arms["incumbent"] = inc
    arms.update(collect_layouts(results_root, tag))
    if not arms:
        print(f"[daily_metrics] {tag}: no layouts found", flush=True)
        return []

    rows: List[dict] = []
    for role in ("train", "test"):
        orders = load_daily_orders(f"{tag}_{role}", fold_dir)
        for q in quantiles:
            st = ceilings(loads, stations, q)
            for arm, layout in arms.items():
                m = evaluate_layout_daily(layout, orders, st)
                rows.append({
                    "dataset": meta.get("dataset", ""),
                    "tag": meta.get("tag", ""),
                    "fold": meta.get("fold"),
                    "role": role,
                    "arm": arm,
                    "tcap_quantile": q,
                    "days_total": m.get("days_total", 0),
                    "days_violated": m.get("days_violated", 0),
                    "share_days_violated": m.get("share_days_violated", 0.0),
                    "worst_day_ratio": m.get("worst_day_ratio", 0.0),
                    "worst_day": m.get("worst_day", ""),
                    "worst_station": m.get("worst_station", ""),
                    "station_days_violated": m.get("station_days_violated", 0),
                    "station_days_total": m.get("station_days_total", 0),
                    "mean_daily_ratio": m.get("mean_daily_ratio", 0.0),
                    "p95_daily_ratio": m.get("p95_daily_ratio", 0.0),
                    "excess_fraction": m.get("excess_fraction", 0.0),
                    "test_date_min": meta.get("test_date_min", ""),
                    "test_date_max": meta.get("test_date_max", ""),
                    "drift": meta.get("drift", ""),
                })
    return rows


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Daily workload-feasibility table for stored layouts")
    parser.add_argument("--folds", type=str, required=True,
                        help="Fold root written by a *_daily_adapter")
    parser.add_argument("--results", type=str, default=None,
                        help="Harness output root holding layout_*.json")
    parser.add_argument("--quantiles", nargs="*", default=["max", "p95", "p90"],
                        choices=sorted(QUANTILES))
    parser.add_argument("--out", type=str,
                        default=os.path.join(RESULTS, "daily_metrics.csv"))
    args = parser.parse_args()

    fold_dirs = sorted(
        d for d in glob.glob(os.path.join(args.folds, "*"))
        if os.path.isfile(os.path.join(d, "fold_meta.json")))
    if not fold_dirs:
        raise SystemExit(f"no folds with fold_meta.json under {args.folds}")

    rows: List[dict] = []
    for d in fold_dirs:
        rows.extend(score_fold(d, args.results, list(args.quantiles)))
    if not rows:
        raise SystemExit("no arms scored -- was the harness run?")

    df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    df.to_csv(args.out, index=False)

    print(f"[daily_metrics] {len(df)} rows -> {args.out}\n")
    view = df[df["role"] == "test"]
    if not view.empty:
        summary = (view.groupby(["arm", "tcap_quantile"])
                       .agg(days_viol=("days_violated", "sum"),
                            days=("days_total", "sum"),
                            worst=("worst_day_ratio", "max"),
                            mean_ratio=("mean_daily_ratio", "mean"))
                       .reset_index())
        print("TEST-window summary (all folds pooled)")
        print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
