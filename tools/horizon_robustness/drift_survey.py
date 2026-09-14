"""Demand-mix drift in total-variation distance: how far do blocks move from pooled history?

Motivation (13 Sep 2026 review, section 4): for any layout x and any station s,

    | r_s(x, q) - r_s(x, qH) |  <=  TV(q, qH) = (1/2) sum_p | q_p - qH_p |,

because a station share is the mass of a product subset. So a layout that sits
within delta - rho of its pooled-history targets stays within delta on any
demand vector whose product mix is within rho of pooled history in total
variation. TIGHT reserves rho = lambda * delta (0.01 at the primary setting).
This survey measures, without any solver:

  * historical drift: TV between each right-aligned n-block of the history
    prefix and the pooled history of the SAME prefix (the quantity a
    date-free margin rule could be predeclared from);
  * ex-post future drift, clearly labelled as such: TV between each ALREADY
    SCORED future window (first origin, grid horizons) and the pooled history
    it was scored against. This reads no order beyond the furthest scored
    future (index origin + 2P); the tail after it stays unexamined.

It never reads orders past ``origin + n_max``. Output: tables/drift_survey.csv.
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
import time
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from Baselines.horizon_robustness.orders import complete_window                  # noqa: E402
from Baselines.horizon_robustness.protocol import Protocol, horizon_grid, origins  # noqa: E402
from Baselines.horizon_robustness.runner import _load_dataset                    # noqa: E402
from Baselines.horizon_robustness.uncertainty import make_scenarios              # noqa: E402

OUT = ROOT / "reports" / "horizon_robustness_results" / "tables" / "drift_survey.csv"
DEFAULT = ("syn_50sku_seed1001", "syn_500sku_seed1001", "syn_1000sku_seed1001", "syn_2000sku_seed1001", "BERNER")


def mix(counts, product_count):
    vector = [Fraction(0)] * product_count
    total = 0
    for p, c in counts:
        vector[p] += c
        total += c
    return [v / total for v in vector] if total else vector


def tv(a, b):
    return sum(abs(x - y) for x, y in zip(a, b)) / 2


def window_counts(orders):
    counts = {}
    for order in orders:
        for p, c in order.lines:
            counts[p] = counts.get(p, 0) + c
    return tuple(sorted(counts.items()))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--datasets", nargs="+", default=list(DEFAULT))
    parser.add_argument("--holdout", action="store_true",
                        help="also measure the revision-3 deployment window [first+2P, first+3P); allowed only "
                             "because that future has already been scored by campaign ho3_20260913")
    args = parser.parse_args(argv)
    started = time.time()
    policy = Protocol()
    rho = Fraction(policy.two_sided_delta) * Fraction(policy.tightening[2])  # lambda*delta at the primary setting
    rows = []
    for dataset in args.datasets:
        demand = _load_dataset(dataset, ROOT)
        product_count = demand.catalogue.p
        origin = origins(len(demand.orders), product_count, maximum=1)[0]
        history = complete_window(demand.orders, 0, origin)
        pooled = mix(window_counts(history), product_count)
        for n in horizon_grid(product_count):
            scenarios = make_scenarios(history, product_count, n)
            blocks = [s for s in scenarios if s.label == "block"]
            historical = [tv(mix(s.counts, product_count), pooled) for s in blocks]
            future = complete_window(demand.orders, origin, origin + n)   # already scored window
            assert len(future) == n and origin + n <= origin + 2 * product_count
            future_tv = tv(mix(window_counts(future), product_count), pooled)
            row = dict(
                dataset_id=dataset, origin=origin, n=n, historical_blocks=len(blocks),
                historical_tv_max=float(max(historical)), historical_tv_mean=float(statistics.fmean(historical)),
                historical_tv_p90=float(sorted(historical)[max(0, int(0.9 * len(historical)) - 1)]),
                historical_tv_last=float(historical[-1]),
                future_tv_ex_post=float(future_tv),
                reserved_margin_rho=float(rho),
                future_tv_within_rho=future_tv <= rho,
                historical_max_within_rho=max(historical) <= rho,
                note="future_tv is ex post: the scored future compared with the pooled history it was "
                     "scored against; never used to choose a parameter")
            rows.append(row)
            print(json.dumps({k: row[k] for k in ("dataset_id", "n", "historical_blocks", "historical_tv_max",
                                                    "historical_tv_mean", "future_tv_ex_post",
                                                    "reserved_margin_rho", "future_tv_within_rho")}))
    if args.holdout:
        from Baselines.horizon_robustness.protocol import holdout_origin
        for dataset in args.datasets:
            if dataset != "BERNER":
                continue
            demand = _load_dataset(dataset, ROOT)
            product_count = demand.catalogue.p
            origin = holdout_origin(len(demand.orders), product_count)
            n = product_count
            history = complete_window(demand.orders, 0, origin)
            pooled = mix(window_counts(history), product_count)
            blocks = [s for s in make_scenarios(history, product_count, n) if s.label == "block"]
            historical = [tv(mix(s.counts, product_count), pooled) for s in blocks]
            future = complete_window(demand.orders, origin, origin + n)
            future_tv = tv(mix(window_counts(future), product_count), pooled)
            row = dict(dataset_id=dataset + "@holdout", origin=origin, n=n, historical_blocks=len(blocks),
                       historical_tv_max=float(max(historical)), historical_tv_mean=float(statistics.fmean(historical)),
                       historical_tv_p90=float(sorted(historical)[max(0, int(0.9 * len(historical)) - 1)]),
                       historical_tv_last=float(historical[-1]), future_tv_ex_post=float(future_tv),
                       reserved_margin_rho=float(rho), future_tv_within_rho=future_tv <= rho,
                       historical_max_within_rho=max(historical) <= rho,
                       note="revision-3 deployment window, measured only after campaign ho3_20260913 scored it")
            rows.append(row)
            print(json.dumps({k: row[k] for k in ("dataset_id", "n", "historical_blocks", "historical_tv_max",
                                                    "historical_tv_mean", "future_tv_ex_post")}))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps(dict(rows=len(rows), path=str(OUT), elapsed_seconds=round(time.time() - started, 1))))
    print("DRIFT SURVEY COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
