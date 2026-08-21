"""Publication figures for report 12 (out-of-sample workload feasibility).

Reads the precomputed analysis CSVs under
``reports/12_workload_feasibility/data/`` and renders six vector-PDF
figures into ``reports/12_workload_feasibility/figures/`` plus 150-dpi
PNG previews into ``figures/preview/``.

Figures
-------
1. fig_violations.pdf   -- grouped bars, stations violated per temporal fold,
                           k=1 vs k=2, as-run check vs volume-normalized check
                           (iscf480 temporal).
2. fig_ratio_heatmap.pdf-- stations x folds heatmap of ratio_norm, k=1 and k=2
                           panels, diverging RdBu_r centered at 1.0, annotated.
3. fig_bindingness.pdf  -- bindingness B per fold, CV vs temporal splits
                           (iscf480), reference line at 1/1.10.
4. fig_concentration.pdf-- cumulative share of station overload vs top-j
                           deviating products (gamma/concentration.csv).
5. fig_gamma.pdf        -- GammaCover as % of |Phi_s| on violated stations,
                           grouped by deviation model M1/M2/M3 (q=90 fit).
6. fig_k_effect.pdf     -- iscf10kt temporal: viol_norm and imbalance vs k.

Style: Okabe-Ito subset (#0072B2 blue = k=1/nominal, #D55E00 vermillion =
k=2/robust, #009E73 green = third series), recessive #DDDDDD grid behind
data, left+bottom spines only, font size 9, near-black #222222 text,
single-column 3.2in / full-width 6.3in, matplotlib only.

Missing input CSVs are skipped gracefully with a console note.
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional, Tuple

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import TwoSlopeNorm  # noqa: E402

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
STUDY: str = r"C:\Users\Nico\PycharmProjects\CSLAP_Problem\reports\12_workload_feasibility"
DATA: str = os.path.join(STUDY, "data")
FIG: str = os.path.join(STUDY, "figures")
PREVIEW: str = os.path.join(FIG, "preview")

# --------------------------------------------------------------------------
# Fixed style tokens (mandatory palette)
# --------------------------------------------------------------------------
COL_K1: str = "#0072B2"   # blue      : k=1 / nominal / highlighted series
COL_K2: str = "#D55E00"   # vermillion: k=2 / robust
COL_3: str = "#009E73"    # green     : third series
INK: str = "#222222"      # near-black text
GRID: str = "#DDDDDD"     # recessive grid
GRAY: str = "#BBBBBB"     # de-emphasized spaghetti lines
REF: str = "#666666"      # reference/threshold line

plt.rcParams.update({
    "font.size": 9,
    "text.color": INK,
    "axes.labelcolor": INK,
    "axes.edgecolor": INK,
    "xtick.color": INK,
    "ytick.color": INK,
    "axes.linewidth": 0.8,
    "xtick.labelsize": 8.5,
    "ytick.labelsize": 8.5,
    "legend.fontsize": 8,
    "legend.frameon": False,
    "pdf.fonttype": 42,
})


def style_ax(ax: plt.Axes, grid_axis: str = "y") -> None:
    """Apply the shared axes style: recessive grid, left+bottom spines only."""
    ax.set_axisbelow(True)
    if grid_axis:
        ax.grid(True, axis=grid_axis, color=GRID, linewidth=0.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(length=3, width=0.8)


def save(fig: plt.Figure, name: str) -> None:
    """Save a figure as vector PDF plus a 150-dpi PNG preview."""
    pdf_path = os.path.join(FIG, f"{name}.pdf")
    png_path = os.path.join(PREVIEW, f"{name}.png")
    fig.savefig(pdf_path, bbox_inches="tight")
    fig.savefig(png_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[ok] wrote {pdf_path} (+ preview PNG)")


def load_csv(path: str) -> Optional[pd.DataFrame]:
    """Load a CSV or return None with a skip note if it is missing."""
    if not os.path.isfile(path):
        print(f"[skip] missing CSV: {path}")
        return None
    return pd.read_csv(path)


# --------------------------------------------------------------------------
# Figure 1: stations violated per temporal fold, as-run vs normalized
# --------------------------------------------------------------------------
def fig_violations() -> None:
    """Grouped bars: violated stations per temporal fold, two check panels."""
    df = load_csv(os.path.join(DATA, "iscf480", "per_fold.csv"))
    if df is None:
        return
    tmp = df[df["split"] == "temporal"].copy()
    folds: List[str] = sorted(tmp["fold"].unique())
    x = np.arange(len(folds))
    width = 0.32

    fig, axes = plt.subplots(1, 2, figsize=(6.3, 2.3), sharey=True)
    panels: List[Tuple[str, str]] = [
        ("viol_asrun", "as-run check (train-calibrated $T_s$)"),
        ("viol_norm", "volume-normalized check ($\\hat{T}$)"),
    ]
    for ax, (col, tag) in zip(axes, panels):
        v1 = [int(tmp[(tmp["fold"] == f) & (tmp["k"] == 1)][col].iloc[0]) for f in folds]
        v2 = [int(tmp[(tmp["fold"] == f) & (tmp["k"] == 2)][col].iloc[0]) for f in folds]
        ax.bar(x - width / 2, v1, width, color=COL_K1, label="$k=1$ (nominal)")
        ax.bar(x + width / 2, v2, width, color=COL_K2, label="$k=2$ (closure)")
        ax.set_xticks(x)
        ax.set_xticklabels([f"{0.5 + 0.1 * i:.1f}" for i in range(len(folds))])
        ax.set_xlabel("temporal cut (train fraction)")
        ax.set_ylim(0, 4.9)
        ax.set_yticks(range(5))
        ax.text(0.03, 0.97, tag, transform=ax.transAxes,
                ha="left", va="top", fontsize=8.5, color=INK)
        style_ax(ax)
    axes[0].set_ylabel("stations violated (of 8)")
    axes[0].legend(loc="upper right", bbox_to_anchor=(1.0, 0.88))
    fig.tight_layout()
    save(fig, "fig_violations")


# --------------------------------------------------------------------------
# Figure 2: ratio_norm heatmap, stations x folds, k=1 and k=2
# --------------------------------------------------------------------------
def fig_ratio_heatmap() -> None:
    """Annotated diverging heatmaps of ratio_norm (iscf480 temporal)."""
    h1 = load_csv(os.path.join(DATA, "iscf480", "heatmap_temporal_k1.csv"))
    h2 = load_csv(os.path.join(DATA, "iscf480", "heatmap_temporal_k2.csv"))
    if h1 is None or h2 is None:
        return
    h1 = h1.set_index("station")
    h2 = h2.set_index("station")
    vmin = float(min(h1.values.min(), h2.values.min()))
    vmax = float(max(h1.values.max(), h2.values.max()))
    norm = TwoSlopeNorm(vcenter=1.0, vmin=vmin, vmax=vmax)
    cmap = plt.get_cmap("RdBu_r")

    fig, axes = plt.subplots(1, 2, figsize=(6.3, 2.9), sharey=True)
    for ax, mat, tag in [(axes[0], h1, "$k=1$ (nominal)"),
                         (axes[1], h2, "$k=2$ (closure)")]:
        im = ax.imshow(mat.values, cmap=cmap, norm=norm, aspect="auto")
        ax.set_xticks(range(mat.shape[1]))
        ax.set_xticklabels([f"{0.5 + 0.1 * i:.1f}" for i in range(mat.shape[1])])
        ax.set_yticks(range(mat.shape[0]))
        ax.set_yticklabels(mat.index)
        ax.set_xlabel("temporal cut (train fraction)")
        ax.set_title(tag, fontsize=9, color=INK, pad=4)
        ax.tick_params(length=0)
        for sp in ax.spines.values():
            sp.set_visible(False)
        for i in range(mat.shape[0]):
            for j in range(mat.shape[1]):
                val = float(mat.values[i, j])
                r, g, b, _ = cmap(norm(val))
                lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
                ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                        fontsize=7, color=("white" if lum < 0.45 else INK))
    cbar = fig.colorbar(im, ax=axes, shrink=0.9, pad=0.02)
    cbar.set_label("ratio $\\hat{W}_s/\\hat{T}$ (1 = ceiling)", fontsize=8.5)
    cbar.ax.tick_params(labelsize=8)
    cbar.outline.set_visible(False)
    save(fig, "fig_ratio_heatmap")


# --------------------------------------------------------------------------
# Figure 3: bindingness B per fold, CV vs temporal
# --------------------------------------------------------------------------
def fig_bindingness() -> None:
    """Dot/line plot of bindingness B per fold with the 1/1.10 threshold."""
    df = load_csv(os.path.join(DATA, "iscf480", "per_fold.csv"))
    if df is None:
        return
    sub = df[df["k"] == 1]
    folds = [f"r0f{i}" for i in range(5)]
    x = np.arange(5)
    b_cv = [float(sub[(sub["split"] == "cv") & (sub["fold"] == f)]["B"].iloc[0])
            for f in folds]
    b_tp = [float(sub[(sub["split"] == "temporal") & (sub["fold"] == f)]["B"].iloc[0])
            for f in folds]
    thr = 1.0 / 1.10

    fig, ax = plt.subplots(figsize=(3.2, 2.5))
    ax.axhline(thr, color=REF, linewidth=1.0, linestyle="--")
    ax.text(5.05, thr + 0.02, "volume-binding threshold (1/1.10)",
            fontsize=7.5, color=REF, ha="right", va="bottom")
    ax.plot(x, b_tp, color=COL_K1, linewidth=1.8, marker="o", markersize=5,
            label="temporal split")
    ax.plot(x, b_cv, color=COL_3, linewidth=1.8, marker="s", markersize=5,
            label="CV split")
    ax.text(4.15, b_tp[-1], "temporal", fontsize=8, color=COL_K1, va="center")
    ax.text(4.15, b_cv[-1] + 0.01, "CV", fontsize=8, color=COL_3, va="center")
    ax.set_xlim(-0.3, 5.15)
    ax.set_xticks(x)
    ax.set_xlabel("fold / temporal cut")
    ax.set_ylabel("bindingness $B$ (fair share / ceiling)")
    ax.set_ylim(0, 1.12)
    ax.legend(loc="upper right", bbox_to_anchor=(1.0, 0.76))
    style_ax(ax)
    fig.tight_layout()
    save(fig, "fig_bindingness")


# --------------------------------------------------------------------------
# Figure 4: overload concentration curves
# --------------------------------------------------------------------------
def fig_concentration() -> None:
    """Cumulative share of positive deviation mass vs top-j products."""
    df = load_csv(os.path.join(DATA, "gamma", "concentration.csv"))
    if df is None:
        return
    df = df[df["k"] == 1]
    xs = np.array([0, 1, 2, 5, 10, 20])
    cols = ["top1_share", "top2_share", "top5_share", "top10_share", "top20_share"]
    curves = np.array([[0.0] + [min(float(r[c]), 1.0) for c in cols]
                       for _, r in df.iterrows()])

    fig, ax = plt.subplots(figsize=(3.2, 2.5))
    for row in curves:
        ax.plot(xs, row, color=GRAY, linewidth=0.8, alpha=0.85, zorder=2)
    med = np.median(curves, axis=0)
    ax.plot(xs, med, color=COL_K1, linewidth=2.0, marker="o", markersize=5,
            zorder=3)
    ax.text(10.4, med[4] - 0.06, "median", fontsize=8.5, color=COL_K1,
            ha="left", va="top")
    ax.text(16.0, 0.30,
            f"{curves.shape[0]} violating\n(fold, station) pairs",
            fontsize=7.5, color=REF, ha="center", va="center")
    ax.set_xticks([0, 1, 2, 5, 10, 20])
    ax.set_xlabel("top-$j$ deviating products")
    ax.set_ylabel("cumulative overload share")
    ax.set_ylim(0, 1.04)
    ax.set_xlim(-0.4, 20.6)
    style_ax(ax)
    fig.tight_layout()
    save(fig, "fig_concentration")


# --------------------------------------------------------------------------
# Figure 5: GammaCover as % of |Phi_s| on violated stations
# --------------------------------------------------------------------------
def fig_gamma() -> None:
    """Dot plot of GammaCover_frac by deviation model, violated stations."""
    df = load_csv(os.path.join(DATA, "gamma", "gamma_station.csv"))
    if df is None:
        return
    df = df[(df["k"] == 1) & (df["viol_norm_flag"])]
    models = ["M1_prop", "M2_sqrt", "M3_empirical"]
    labels = ["M1\nproportional", "M2\nsquare-root", "M3\nempirical"]
    fams = [("iscf480-temporal", "iscf480  ($|\\Phi_s|=60$)"),
            ("iscf10kt-temporal", "iscf10kt  ($|\\Phi_s|=541$)")]

    fig, axes = plt.subplots(1, 2, figsize=(6.3, 2.5), sharey=True)
    for ax, (fam, tag) in zip(axes, fams):
        sub = df[df["family"] == fam]
        for gi, model in enumerate(models):
            vals = sub[sub["model"] == model]["GammaCover_frac"].values * 100.0
            finite = np.sort(vals[np.isfinite(vals)])
            n_inf = int(np.sum(~np.isfinite(vals)))
            jit = (np.linspace(-0.16, 0.16, len(finite))
                   if len(finite) > 1 else np.zeros(len(finite)))
            ax.plot(gi + jit, finite, linestyle="none", marker="o",
                    markersize=5, markerfacecolor=COL_K1,
                    markeredgecolor="white", markeredgewidth=0.5,
                    alpha=0.85, zorder=3)
            if len(finite):
                m = float(np.median(finite))
                ax.hlines(m, gi - 0.24, gi + 0.24, color=INK,
                          linewidth=1.6, zorder=4)
            if n_inf:
                ax.text(gi, 103, f"+{n_inf} $\\infty$", fontsize=7.5,
                        ha="center", va="bottom", color=REF)
        ax.set_xticks(range(len(models)))
        ax.set_xticklabels(labels, fontsize=8)
        ax.set_xlim(-0.6, len(models) - 0.4)
        ax.set_ylim(0, 112)
        ax.set_yticks([0, 25, 50, 75, 100])
        ax.set_title(tag, fontsize=9, color=INK, pad=4)
        style_ax(ax)
    axes[0].set_ylabel("$\\Gamma^{cover}$ as % of $|\\Phi_s|$  ($q=90$ fit)")
    handles = [plt.Line2D([], [], linestyle="none", marker="o", markersize=5,
                          markerfacecolor=COL_K1, markeredgecolor="white",
                          markeredgewidth=0.5),
               plt.Line2D([], [], color=INK, linewidth=1.6)]
    axes[1].legend(handles, ["violated station", "median"],
                   loc="upper left", bbox_to_anchor=(0.02, 0.98))
    fig.tight_layout()
    save(fig, "fig_gamma")


# --------------------------------------------------------------------------
# Figure 6: iscf10kt temporal, viol_norm and imbalance vs k
# --------------------------------------------------------------------------
def fig_k_effect() -> None:
    """Two stacked panels: viol_norm and imbalance vs closure size k."""
    df = load_csv(os.path.join(DATA, "iscf10kt", "k_effect.csv"))
    if df is None:
        return
    sub = df[df["variant"] == "temporal"]
    ks = [1, 2, 3, 4, 6]
    viol = sub[[f"viol_norm_k{k}" for k in ks]].values.astype(float)
    imb = sub[[f"imbalance_k{k}" for k in ks]].values.astype(float)

    fig, axes = plt.subplots(2, 1, figsize=(3.2, 3.6), sharex=True)
    for ax, mat, ylab in [(axes[0], viol, "stations violated\n(normalized, of 8)"),
                          (axes[1], imb, "imbalance\n$\\max_s W_s\\,/\\,\\overline{W}$")]:
        for row in mat:
            ax.plot(ks, row, color=GRAY, linewidth=1.0, alpha=0.9, zorder=2)
        mean = mat.mean(axis=0)
        ax.plot(ks, mean, color=COL_K1, linewidth=2.0, marker="o",
                markersize=5, zorder=3)
        ax.text(ks[-1] + 0.15, mean[-1], "mean", fontsize=8, color=COL_K1,
                va="center", ha="left")
        ax.set_ylabel(ylab)
        style_ax(ax)
    axes[0].set_ylim(0, 3.4)
    axes[0].set_yticks([0, 1, 2, 3])
    axes[1].axhline(1.10, color=REF, linewidth=1.0, linestyle="--")
    axes[1].text(1.0, 1.14, "1.10 slack rule", fontsize=7.5, color=REF,
                 ha="left", va="bottom")
    axes[1].set_ylim(0.95, axes[1].get_ylim()[1])
    axes[1].set_xticks(ks)
    axes[1].set_xlim(0.7, 7.0)
    axes[1].set_xlabel("closure size $k$")
    handles = [plt.Line2D([], [], color=GRAY, linewidth=1.0),
               plt.Line2D([], [], color=COL_K1, linewidth=2.0, marker="o",
                          markersize=5)]
    axes[0].legend(handles, ["individual folds", "mean"], loc="lower right")
    fig.tight_layout()
    save(fig, "fig_k_effect")


def main() -> None:
    """Render all six figures."""
    os.makedirs(FIG, exist_ok=True)
    os.makedirs(PREVIEW, exist_ok=True)
    fig_violations()
    fig_ratio_heatmap()
    fig_bindingness()
    fig_concentration()
    fig_gamma()
    fig_k_effect()
    print("[done] all figures rendered")


if __name__ == "__main__":
    main()
