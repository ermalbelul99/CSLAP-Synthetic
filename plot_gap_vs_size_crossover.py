"""Figure: mean gap to the set-variable MILP reference against catalogue size.

Draws Images_CSLAP/gap_vs_size_crossover.png (fig:crossover in the manuscript).

Why this file exists
--------------------
The figure previously had NO generator in the repository. IJPR_revision_changelog
records it as "built from Table 4's Gap column", i.e. hand-authored, and a search
of every savefig call in the tree confirms nothing wrote it. That was tolerable
while the curves were static; it is not tolerable now that re-indexing the
community bound on zeta moves the heuristic curve at three of its four points and
makes it cross the reference. A hand-drawn figure would silently disagree with
the table it is drawn from.

Source of truth
---------------
exp02a_results/final_formulation_analysis_perinstance.csv, written by
Baselines/final_formulation_analysis.py. Curves are the MEAN OF PER-INSTANCE
percentage gaps against the `setvar` column -- the same convention Table 4's Gap
column uses (see IJPR_revision_changelog Part N: the paired tests and the Gap
column both run on per-instance quantities, not on ratios of column means).
Reading the gaps from this one file is what keeps the figure and the table in
agreement by construction.

Usage
-----
    python plot_gap_vs_size_crossover.py
    python plot_gap_vs_size_crossover.py --print-only
"""

from __future__ import annotations

import argparse
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE_DIR, "exp02a_results",
                   "final_formulation_analysis_perinstance.csv")
OUT = os.path.join(BASE_DIR, "Images_CSLAP", "gap_vs_size_crossover.png")

# column in the source -> (legend label, colour, marker, linestyle)
SERIES = {
    "cg":     ("Column generation", "#1f77b4", "o", "-"),
    "heur":   ("Clustering heuristic", "#d62728", "s", "-"),
    "binary": ("Binary MILP", "#7f7f7f", "^", "--"),
}


def gaps(df: pd.DataFrame) -> pd.DataFrame:
    """Mean per-instance % gap to `setvar`, per size, for each series."""
    out = {}
    for col in SERIES:
        out[col] = (df.groupby("size_n")
                    .apply(lambda g, c=col: 100.0 * ((g[c] - g.setvar) / g.setvar).mean()))
    return pd.DataFrame(out)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--src", default=SRC)
    p.add_argument("--out", default=OUT)
    p.add_argument("--print-only", action="store_true")
    args = p.parse_args(argv)

    if not os.path.isfile(args.src):
        print(f"missing {args.src}; run Baselines/final_formulation_analysis.py first",
              file=sys.stderr)
        return 2

    g = gaps(pd.read_csv(args.src))

    print("mean per-instance gap to the set-variable reference (%)")
    print(g.round(2).to_string())
    crossers = [SERIES[c][0] for c in g.columns if (g[c] < 0).any()]
    print("\nseries crossing below the reference:", ", ".join(crossers) or "none")
    if args.print_only:
        return 0

    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    ax.axhline(0.0, color="black", lw=1.2, zorder=2)
    ax.annotate("set-variable MILP reference", xy=(g.index[0], 0), xytext=(4, 4),
                textcoords="offset points", fontsize=8, color="black")

    for col, (label, colour, marker, ls) in SERIES.items():
        ax.plot(g.index, g[col], marker=marker, ls=ls, color=colour, lw=1.8,
                ms=6, label=label, zorder=3)

    ax.set_xscale("log")
    ax.set_xticks(list(g.index))
    ax.set_xticklabels([f"{int(n):,}" for n in g.index])
    ax.set_xlabel("Catalogue size $N$ (products, log scale)")
    ax.set_ylabel("Mean gap to reference (%)")
    ax.grid(True, which="major", axis="y", alpha=0.3)
    ax.legend(frameon=False, fontsize=9)

    # Shade the region where a curve uses FEWER visits than the reference, so the
    # sign convention cannot be misread.
    lo = min(-0.6, float(g.min().min()) - 0.4)
    ax.set_ylim(lo, float(g.max().max()) + 0.6)
    ax.axhspan(lo, 0.0, color="#2ca02c", alpha=0.06, zorder=1)
    ax.annotate("fewer visits than the reference", xy=(g.index[-1], lo),
                xytext=(-6, 6), textcoords="offset points", ha="right",
                fontsize=8, color="#2ca02c")

    fig.tight_layout()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    fig.savefig(args.out, dpi=200)
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
