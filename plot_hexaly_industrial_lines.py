r"""Redraw Figure 11(b): per-station load change of the set-variable MILP layout.

PROVENANCE -- READ BEFORE TRUSTING THIS FIGURE
----------------------------------------------
Unlike the heuristic panel (plot_industrial_heuristic_workload.py, driven by
results_industrial_heuristic_per_station.csv) and the column-generation panel
(plot_cg_industrial_lines.py, driven by industrial_cg_setpart_assignment_*.json),
this panel is NOT recomputed from a stored layout. The set-variable Hexaly run
wrote its assignment to ``product_assignment_Hexaly_set_v1.csv`` from cell 46 of
Notebooks/MILP_Exact_Solution/Berner_Hexaly_Solution_Sets_v1.ipynb, and that file
is absent from the repository, absent from the notebook's working directory, and
was never committed (``git log --all`` finds no trace). The notebook's own output
cells are cleared, so the numbers do not survive there either.

The per-station values below are therefore transcribed from the figure the
manuscript already ships, Images_CSLAP/Hexaly_pt_relative_change_number_of_lines
_per_station.png, whose bars carry printed labels to one decimal. This script
restyles those values to match the other two panels; it does not re-derive them.
Two independent checks in _verify() tie the transcription back to the manuscript.

If ``product_assignment_Hexaly_set_v1.csv`` is ever recovered, replace this table
with the same treatment plot_cg_industrial_lines.py applies to the CG layout.

OPEN DISCREPANCY -- THE PANEL AND THE TABLE 6 ROW ARE NOT THE SAME RUN
----------------------------------------------------------------------
Utilisation is load over the station's own legacy load and load is lines over a
per-station speed, so the speed cancels and SD(utilisation) equals SD(relative
change in lines). That identity is exact, and it checks out for the
column-generation layout: the figure gives 2.413% and
Baselines/report_industrial_deviation.py gives 2.41%, the Table 6 value.

It fails here. The 24 values below give SD 3.65%, while the ``MILP Hexaly`` row
of results_industrial_benchmark_36.csv -- the row Table 6 prints -- carries
utilization_std_dev 4.4817%. The two cannot describe one layout. The likely
cause is that the shipped figure comes from the standalone notebook run
(``optimizer.param.time_limit = 72000``, 20 h) while the table row comes from
run_benchmarks_industrial.py (36,299 s, 10 h); the harness never saved its
assignment, so the two were never reconciled.

The span [-5.9%, +9.6%] quoted in Section 5 matches THIS figure, not necessarily
the tabled layout. Resolving it needs either the recovered assignment or a fresh
run; restyling the panel does not resolve it and must not be read as doing so.

Reproduce
---------
cd CSLAP-Synthetic
python plot_hexaly_industrial_lines.py
"""

from __future__ import annotations

import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker as mtick  # noqa: E402
import numpy as np  # noqa: E402

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(BASE_DIR, "Images_CSLAP")

# Ascending by legacy load, the order the other two panels of Figure 11 use and
# the order the published Hexaly figure already carried. S_25 and S_26 (01.GED,
# 01.15; 5 and 11 order lines, both at 0.0%) are dropped so that all three
# panels cover the same 24 evaluated stations of Table 6.
STATIONS = ["S_6", "S_19", "S_22", "S_14", "S_20", "S_9", "S_16", "S_23",
            "S_11", "S_21", "S_4", "S_1", "S_7", "S_15", "S_13", "S_24",
            "S_17", "S_10", "S_12", "S_18", "S_2", "S_5", "S_8", "S_3"]
PCT_CHANGE = [-0.3, 9.6, 0.2, -2.5, -2.7, -1.4, -0.5, -4.7,
              0.8, -4.5, -2.3, -3.6, -5.9, -3.3, -2.8, 2.6,
              0.3, -2.6, 0.5, -2.3, 4.2, 0.0, 2.6, 7.6]

# What Table 6 and Section 5 assert about this layout, used as the check.
REPORTED_SD = 4.48
REPORTED_SPAN = (-5.9, 9.6)


def _verify(pct: np.ndarray) -> bool:
    """Tie the transcribed values back to two numbers the manuscript states.

    Utilisation is load over the station's own legacy load, and load is lines
    divided by a per-station speed, so the speed cancels and the relative change
    in lines equals the relative change in utilisation. The dispersion of these
    values must therefore reproduce the Util. SD of the Table 6 row, and their
    extremes must reproduce the span quoted in the text.
    """
    ok = True
    sd = float(np.std(pct))
    if abs(sd - REPORTED_SD) > 0.05:
        # Known and documented in the module docstring: this is the signature of
        # the panel and the Table 6 row coming from two different Hexaly runs.
        # Loud, but not fatal -- the restyled panel still depicts exactly what
        # the previously shipped panel depicted.
        print(f"[WARN] dispersion {sd:.2f}% does not match the {REPORTED_SD}% of "
              f"the Table 6 set-variable MILP row. The panel and that row are "
              f"not the same run; see this module's docstring.", file=sys.stderr)
    else:
        print(f"[check] dispersion {sd:.2f} matches the reported {REPORTED_SD}")
    span = (float(pct.min()), float(pct.max()))
    if (abs(span[0] - REPORTED_SPAN[0]) > 0.05
            or abs(span[1] - REPORTED_SPAN[1]) > 0.05):
        print(f"[FAIL] span [{span[0]:+.1f}, {span[1]:+.1f}] does not match the "
              f"reported [{REPORTED_SPAN[0]:+.1f}, {REPORTED_SPAN[1]:+.1f}]",
              file=sys.stderr)
        ok = False
    else:
        print(f"[check] span [{span[0]:+.1f}%, {span[1]:+.1f}%] matches the text")
    return ok


def main() -> int:
    if len(STATIONS) != len(PCT_CHANGE):
        print("[error] station and value tables disagree in length", file=sys.stderr)
        return 1
    pct = np.asarray(PCT_CHANGE, dtype=float)
    if not _verify(pct):
        return 1

    idx = np.arange(len(STATIONS))
    plt.figure(figsize=(14, 6))
    ax = plt.gca()
    ax.bar(idx, pct, 0.6, color="tab:blue")
    ax.axhline(0.0, color="grey", lw=1.0)
    ax.axhline(10.0, color="red", ls="--", lw=1.0, label="+10% operational slack")
    for i, v in zip(idx, pct):
        ax.annotate(f"{v:.1f}%", xy=(i, v), textcoords="offset points",
                    xytext=(0, 4 if v >= 0 else -12), ha="center", fontsize=8)
    pad = 0.10 * (pct.max() - pct.min())
    ax.set_ylim(pct.min() - pad, max(pct.max(), 10.0) + pad)
    ax.yaxis.set_major_locator(mtick.MaxNLocator(nbins=8, steps=[1, 2, 2.5, 5, 10]))
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
    ax.grid(axis="y", ls="--", lw=0.5, alpha=0.4)
    ax.set_axisbelow(True)
    plt.xlabel("Station Name")
    plt.ylabel("Change in Lines (%)")
    plt.title("Relative Change in Number of Lines per Station")
    plt.xticks(idx, STATIONS, rotation=45)
    plt.legend(loc="lower left")
    plt.tight_layout()
    out = os.path.join(OUT_DIR, "Hexaly_pt_relative_change_number_of_lines_per_station.png")
    plt.savefig(out, dpi=150)
    plt.close()
    print(f"[out] {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
