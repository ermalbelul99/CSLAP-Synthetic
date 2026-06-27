"""EXP-02b: consolidated cross-method CSLAP scalability figure.

Plots the mean gap to the Hexaly set-variable MILP reference (%) versus SKU count
for the three non-reference methods (GA, SA-C, greedy heuristic), across the four
multi-instance sizes of EXP-02a, with 95% t-confidence intervals where the sample
is informative (K>=5) and point markers otherwise. Hexaly is the 0% reference.

Reads exp02a_results/exp02a_per_instance_v3.csv (the REV-3 EXP-02a output) and
writes exp02b_scalability.png. Reproducible; no licensed solver needed.
"""
from __future__ import annotations
import os
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "exp02a_results", "exp02a_per_instance_v3.csv")
OUT = os.path.join(HERE, "exp02a_results", "exp02b_scalability.png")

SIZES = [50, 500, 1000, 2000]
METHODS = ["Heuristic", "GA", "SA-C"]            # Hexaly is the reference (0%)
STYLE = {                                        # colour, marker, line
    "Heuristic": ("#d62728", "s", "--"),         # dashed: workload-infeasible
    "GA":        ("#1f77b4", "o", "-"),
    "SA-C":      ("#2ca02c", "^", "-"),
}
CI_MIN_N = 5                                      # below this, CI is uninformative


def mean_ci(vals: np.ndarray) -> tuple[float, float, bool]:
    """Return (mean%, 95% t half-width %, ci_informative)."""
    v = vals[np.isfinite(vals)] * 100.0          # fraction -> percent
    n = v.size
    if n == 0:
        return float("nan"), float("nan"), False
    m = float(v.mean())
    if n < 2:
        return m, float("nan"), False
    hw = float(stats.t.ppf(0.975, n - 1) * v.std(ddof=1) / np.sqrt(n))
    return m, hw, n >= CI_MIN_N


def main() -> None:
    df = pd.read_csv(SRC)
    df = df[(df["status"] == "OK") & (df["solver_probe"].astype(str).str.lower() != "true")]

    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    ax.axhline(0.0, color="0.45", lw=1.2, zorder=1)
    ax.text(50, 0.0, "Hexaly $=0$ (reference)  ", va="bottom", ha="left",
            fontsize=8, color="0.35")

    for method in METHODS:
        colour, marker, ls = STYLE[method]
        xs, ys, errs, informative = [], [], [], []
        for n_sku in SIZES:
            cell = df[(df["method"] == method) & (df["size_n"] == n_sku)]
            m, hw, info = mean_ci(cell["rel_gap_to_hexaly"].to_numpy(dtype=float))
            xs.append(n_sku); ys.append(m); errs.append(hw); informative.append(info)
        xs = np.array(xs, float); ys = np.array(ys, float); errs = np.array(errs, float)
        ax.plot(xs, ys, ls=ls, color=colour, lw=1.6, marker=marker, ms=6,
                label=method, zorder=3)
        mask = np.array(informative)
        if mask.any():
            ax.errorbar(xs[mask], ys[mask], yerr=errs[mask], fmt="none",
                        ecolor=colour, elinewidth=1.2, capsize=3, zorder=2)

    ax.set_xscale("log")
    ax.set_xticks(SIZES)
    ax.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
    ax.set_xlabel("number of products (SKUs)")
    ax.set_ylabel(r"mean gap to Hexaly reference (\%)".replace("\\%", "%"))
    ax.set_title("Cross-method CSLAP scalability (gap to the Hexaly MILP)")
    ax.grid(True, which="both", ls=":", lw=0.5, alpha=0.6)
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    fig.tight_layout()
    fig.savefig(OUT, dpi=200)
    print("wrote", OUT)
    # quick numeric echo for the caption
    for method in METHODS:
        row = []
        for n_sku in SIZES:
            cell = df[(df["method"] == method) & (df["size_n"] == n_sku)]
            m, hw, info = mean_ci(cell["rel_gap_to_hexaly"].to_numpy(dtype=float))
            row.append(f"N{n_sku}:{m:.1f}%" + (f"+/-{hw:.1f}" if info else ""))
        print(f"  {method:10s} " + "  ".join(row))


if __name__ == "__main__":
    main()
