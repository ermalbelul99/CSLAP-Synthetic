r"""
Per-station workload deviation against the legacy layout, industrial instance.

The manuscript reports, for each optimised industrial layout, the range of the
per-station change in realised load relative to the layout the site operates
today, and how many stations stay inside the site's +10% tolerance. The
``dev_*`` columns written by ``run_industrial_cg_setpart.py`` do NOT answer that
question in ``--match-hexaly`` mode: there they measure deviation against each
station's cap, which the run saturates, so they read 0.0 by construction.

This script recomputes the quantity the manuscript actually claims, with the
workload semantics of ``run_benchmarks_industrial.evaluate_full_metrics``: a
kept product charges its full order-line frequency ``pl_full`` against its
station's speed, statically fixed products included on both sides.

Usage (env savoye2023, from the CSLAP-Synthetic root):
    python Baselines/report_industrial_deviation.py [--layout <assignment.json>]
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)

from data_loader_industrial import load_industrial_data  # noqa: E402


def station_loads(assignment, static_assignment, pl_full, speeds, station_ids):
    """Realised daily load per station, in hours-equivalent line time."""
    full = dict(assignment)
    full.update(static_assignment)
    load = {sid: 0.0 for sid in station_ids}
    for p, sid in full.items():
        if sid in load and speeds.get(sid, 0) > 0:
            load[sid] += pl_full.get(p, 0) / speeds[sid]
    return load


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--layout", default="industrial_cg_setpart_assignment_matchhexaly.json")
    ap.add_argument("--tolerance", type=float, default=0.10)
    args = ap.parse_args()

    data = load_industrial_data(
        os.path.join(_ROOT, "Heuristic_Connex_Set_Project", "data",
                     "BERNER_ORDER_LINES_09-12.csv"))
    st_full = data["st_full"]
    speeds = {s["STATION_ID"]: s["SPEED"] for s in st_full}
    station_ids = [s["STATION_ID"] for s in st_full]
    pl_full = data["pl_full"]
    static = data["static_assignment"]

    legacy = station_loads(data["warm_start_assignment"], static, pl_full,
                           speeds, station_ids)

    with open(os.path.join(_ROOT, args.layout)) as fh:
        layout = json.load(fh)
    new = station_loads(layout, static, pl_full, speeds, station_ids)

    rows, devs = [], []
    for sid in station_ids:
        if legacy[sid] <= 0:
            continue
        d = 100.0 * (new[sid] - legacy[sid]) / legacy[sid]
        devs.append(d)
        rows.append((sid, legacy[sid], new[sid], d))
    devs = np.array(devs)

    print(f"layout: {args.layout}")
    print(f"stations with non-zero legacy load: {len(devs)} of {len(station_ids)}")
    print(f"{'station':>10} {'legacy':>12} {'new':>12} {'dev %':>8}")
    for sid, lo, nw, d in sorted(rows, key=lambda r: r[3]):
        print(f"{str(sid):>10} {lo:12.1f} {nw:12.1f} {d:+8.2f}")
    tol = 100.0 * args.tolerance
    print(f"\ndeviation range: [{devs.min():+.2f}%, {devs.max():+.2f}%]  "
          f"std {devs.std():.2f}%")
    print(f"stations within +/-{tol:.0f}%: {int(np.sum(np.abs(devs) <= tol))}/{len(devs)}")
    print(f"stations above +{tol:.0f}%: {int(np.sum(devs > tol))}")
    print(f"stations above legacy load: {int(np.sum(devs > 0))}")


if __name__ == "__main__":
    main()
