"""Two-sided historical dispersion of station shares under the incumbent.

Question it answers, with NO solver time: how far does each station's share
actually deviate, block by block, from their pooled historical value under the
layout the warehouse really ran? A slack narrower than that swing is one the
warehouse's own history already violates, so it cannot be a data-supported
tolerance for either an upper-only or a two-sided rule.

For every approved dataset, first origin, each declared horizon n:
  blocks   = right-aligned disjoint n-order blocks of the history (as the
             scenario builder defines them) plus the pooled history
  b_s      = pooled share of station s under the incumbent
  d_{k,s}  = share of s in block k minus b_s

Reported per (dataset, n): the largest upward and downward deviation, the
largest absolute deviation, its 90th/95th percentiles over (block, station),
whether the incumbent's OWN history stays inside +/-delta for each grid delta,
and a per-station multinomial noise scale using the ACTUAL b_s (not a uniform
1/S), so the ratio of observed swing to sampling noise is comparable across
datasets. Descriptive only; not a test and not a certified bound on anything
an optimizer could achieve.

    C:\\ermal\\Virtual_Environment_CPLEX_1\\Scripts\\python.exe \\
        tools/horizon_robustness/dispersion_survey.py
"""

from __future__ import annotations

import argparse
from fractions import Fraction
import json
from pathlib import Path
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from Baselines.horizon_robustness.orders import complete_window  # noqa: E402
from Baselines.horizon_robustness.protocol import canonical_json, digest, horizon_grid  # noqa: E402
from Baselines.horizon_robustness.reference import build_reference  # noqa: E402
from Baselines.horizon_robustness.runner import _load_dataset  # noqa: E402
from Baselines.horizon_robustness.uncertainty import make_scenarios  # noqa: E402

GRID = ("0.0025", "0.005", "0.01", "0.02", "0.03", "0.05")


def datasets():
    names = sorted(p.name for p in (ROOT / "exp02a_instances").iterdir() if p.is_dir())
    return names + ["BERNER"]


def quantile(values, q):
    values = sorted(values)
    if not values:
        return None
    position = (len(values) - 1) * q
    lo, hi = int(position), min(int(position) + 1, len(values) - 1)
    return values[lo] + (values[hi] - values[lo]) * (position - lo)


def survey(name):
    started = time.time()
    demand = _load_dataset(name, ROOT)
    catalogue, orders = demand.catalogue, demand.orders
    origin = 7 * len(orders) // 10
    history = complete_window(orders, 0, origin)
    reference = build_reference(catalogue, history)
    assignment = reference.assignment
    total_history = sum(reference.historical_counts)
    b = [Fraction(c, total_history) for c in reference.station_line_counts]
    rows = []
    for n in horizon_grid(catalogue.p):
        scenarios = make_scenarios(history, catalogue.p, n)
        blocks = [s for s in scenarios if s.label == "block"]
        deviations = []                      # (block, station) -> share - b
        per_station_abs = [[] for _ in range(catalogue.s)]
        for block in blocks:
            lines = [0] * catalogue.s
            for p, count in block.counts:
                lines[assignment[p]] += count
            for s in range(catalogue.s):
                d = Fraction(lines[s], block.total_lines) - b[s]
                deviations.append(d)
                per_station_abs[s].append(abs(d))
        abs_dev = [abs(d) for d in deviations]
        max_up = max(deviations)
        max_down = max(-d for d in deviations)
        max_abs = max(abs_dev)
        mean_block_lines = statistics.fmean(block.total_lines for block in blocks)
        # Multinomial one-sigma scale of a station's share at this block size,
        # using each station's actual pooled share; report the median station.
        noise = [((float(bs) * (1 - float(bs))) / mean_block_lines) ** 0.5 for bs in b]
        noise_median = statistics.median(noise)
        row = dict(dataset_id=name, kind=catalogue.kind, catalogue_size=catalogue.p,
                   stations=catalogue.s, origin=origin, n=n,
                   horizon_multiple=str(Fraction(n, catalogue.p)), blocks=len(blocks),
                   mean_block_lines=round(mean_block_lines, 1),
                   max_upward_pp=round(100 * float(max_up), 4),
                   max_downward_pp=round(100 * float(max_down), 4),
                   max_abs_pp=round(100 * float(max_abs), 4),
                   q95_abs_pp=round(100 * float(quantile(abs_dev, 0.95)), 4),
                   q90_abs_pp=round(100 * float(quantile(abs_dev, 0.90)), 4),
                   median_station_max_abs_pp=round(
                       100 * float(statistics.median(max(v) for v in per_station_abs)), 4),
                   noise_sigma_median_station_pp=round(100 * noise_median, 4),
                   max_abs_over_noise_sigma=round(float(max_abs) / noise_median, 2) if noise_median else None,
                   fraction_block_station_pairs_beyond_1pp=round(
                       sum(1 for v in abs_dev if v > Fraction(1, 100)) / len(abs_dev), 4))
        for g in GRID:
            gd = Fraction(g)
            row[f"incumbent_history_within_upper_{g}"] = max_up <= gd
            row[f"incumbent_history_within_twosided_{g}"] = max_abs <= gd
        row["smallest_grid_delta_upper_only"] = next((g for g in GRID if max_up <= Fraction(g)), None)
        row["smallest_grid_delta_two_sided"] = next((g for g in GRID if max_abs <= Fraction(g)), None)
        rows.append(row)
    return rows, round(time.time() - started, 1)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--datasets", nargs="+", default=None)
    parser.add_argument("--output", default="reports/horizon_robustness_results/tables/dispersion_survey.csv")
    args = parser.parse_args(argv)
    selected = args.datasets or datasets()
    rows, timings = [], {}
    for name in selected:
        produced, seconds = survey(name)
        rows.extend(produced)
        timings[name] = seconds
        worst = max(r["max_abs_pp"] for r in produced)
        print(f"{name:<24} rows={len(produced)} max|dev|={worst:.3f}pp two-sided-1pp-ok="
              f"{sum(r['incumbent_history_within_twosided_0.01'] for r in produced)}/{len(produced)} "
              f"({seconds}s)", flush=True)
    from Baselines.horizon_robustness_analysis.analysis import write_csv
    summary = write_csv(rows, ROOT / args.output)
    (ROOT / args.output).with_suffix(".meta.json").write_text(canonical_json(dict(
        datasets=selected, load_seconds=timings, rows=len(rows), table=summary,
        method="station-share deviation of each historical n-block from the pooled share under the incumbent; no optimizer",
        record_hash=digest(rows))), encoding="utf-8")
    print(canonical_json(dict(rows=len(rows), table=summary["path"], sha256=summary["sha256"])))
    print("DISPERSION SURVEY COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
