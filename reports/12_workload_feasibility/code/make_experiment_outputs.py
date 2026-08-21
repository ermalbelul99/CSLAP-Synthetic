"""Post-process the Bertsimas-Sim robust-placement experiment into report assets.

Inputs  (written by Baselines/run_bs_robust_experiment.py, one dir per fold):
    STUDY/data/experiment_f{0..4}/results.csv      one row per (fold, arm)
    STUDY/data/experiment_f{0..4}/calibration.csv  one row per fold
    STUDY/data/experiment_f{0..4}/per_station.csv  station ratios per (fold, arm)

Outputs (merged into STUDY/data/experiment/):
    results.csv, calibration.csv, per_station.csv   merged tables
    exp_summary.csv                                 per-arm means over folds
    STUDY/figures/fig_exp_tradeoff.pdf              PoR + feasibility vs Gamma
    STUDY/figures/fig_exp_frontier.pdf              targeted (Gamma) vs uniform
                                                    (beta) price/peak frontier
    STUDY/figures/fig_exp_stations.pdf              per-station ratios, worst fold
    STUDY/figures/preview/*.png                     150 dpi previews

PoR/G are recomputed here from V_tr/V_te against each fold's gamma0 row
(defensive against partial harness runs). Figure style: Okabe-Ito palette
(blue #0072B2 = nominal/uniform-tightening, vermillion #D55E00 = robust/BS,
green #009E73 auxiliary), recessive grid, left+bottom spines, one y-axis per
panel, font size 9.
"""
from __future__ import annotations

import glob
import os
import shutil
from typing import List

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

STUDY = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
EXP = os.path.join(STUDY, "data", "experiment")
FIG = os.path.join(STUDY, "figures")
PREV = os.path.join(FIG, "preview")

BLUE, VERM, GREEN = "#0072B2", "#D55E00", "#009E73"
GRAY = "#DDDDDD"
INK = "#222222"

plt.rcParams.update({
    "font.size": 9,
    "text.color": INK,
    "axes.labelcolor": INK,
    "xtick.color": INK,
    "ytick.color": INK,
    "axes.edgecolor": INK,
})


def style_axis(ax: plt.Axes) -> None:
    """Recessive grid behind data; left+bottom spines only."""
    ax.set_axisbelow(True)
    ax.grid(color=GRAY, linewidth=0.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def merge_fold_dirs() -> pd.DataFrame:
    """Merge per-fold experiment dirs into STUDY/data/experiment."""
    os.makedirs(EXP, exist_ok=True)
    os.makedirs(os.path.join(EXP, "layouts"), exist_ok=True)
    frames = {"results": [], "calibration": [], "per_station": []}
    for d in sorted(glob.glob(os.path.join(STUDY, "data", "experiment_f*"))):
        for name in frames:
            path = os.path.join(d, f"{name}.csv")
            if os.path.exists(path):
                frames[name].append(pd.read_csv(path))
        for src in glob.glob(os.path.join(d, "layouts", "*.json")) + glob.glob(
            os.path.join(d, "lhat_*.json")
        ):
            dst_dir = (
                os.path.join(EXP, "layouts")
                if os.sep + "layouts" + os.sep in src
                else EXP
            )
            shutil.copy2(src, os.path.join(dst_dir, os.path.basename(src)))
    merged = {}
    for name, lst in frames.items():
        if not lst:
            raise FileNotFoundError(f"no {name}.csv found in experiment_f* dirs")
        df = pd.concat(lst, ignore_index=True)
        # gamma0 / hexaly_k1 rows are duplicated across the per-(fold, alpha)
        # jobs; the LS is pass-deterministic so duplicates are identical rows.
        subset = (
            ["fold", "arm", "station"]
            if "station" in df.columns
            else ["fold", "arm"] if "arm" in df.columns else ["fold", "lhat_scale"]
        )
        subset = [c for c in subset if c in df.columns]
        df = df.drop_duplicates(subset=subset, keep="first")
        merged[name] = df.sort_values(subset)
        merged[name].to_csv(os.path.join(EXP, f"{name}.csv"), index=False)
    return merged["results"]


def recompute_por_g(res: pd.DataFrame) -> pd.DataFrame:
    """Recompute PoR/G per fold against that fold's gamma0 arm."""
    res = res.copy()
    for f, grp in res.groupby("fold"):
        base = grp[grp["arm"] == "gamma0"]
        if base.empty or not bool(base["feasible_model"].iloc[0]):
            continue
        v_tr0 = float(base["V_tr"].iloc[0])
        v_te0 = float(base["V_te"].iloc[0])
        m = res["fold"] == f
        res.loc[m, "PoR_pct"] = 100.0 * (res.loc[m, "V_tr"] - v_tr0) / v_tr0
        res.loc[m, "G_pct"] = 100.0 * (v_te0 - res.loc[m, "V_te"]) / v_te0
    return res


def main() -> None:
    """Merge folds, build the summary CSV and the three experiment figures."""
    os.makedirs(PREV, exist_ok=True)
    res = recompute_por_g(merge_fold_dirs())
    res.to_csv(os.path.join(EXP, "results.csv"), index=False)

    ok = res[res["feasible_model"] == True].copy()  # noqa: E712
    summary = (
        ok.groupby("arm")
        .agg(
            n_folds=("fold", "nunique"),
            gamma=("gamma", "first"),
            PoR_pct=("PoR_pct", "mean"),
            G_pct=("G_pct", "mean"),
            viol_norm=("viol_norm", "mean"),
            max_ratio_norm=("max_ratio_norm", "mean"),
            max_ratio_worst=("max_ratio_norm", "max"),
            X=("X", "mean"),
            imbalance=("imbalance", "mean"),
            wl_asrun=("wl_broken_asrun", "mean"),
        )
        .reset_index()
    )
    n_inf = (
        res[res["feasible_model"] == False]  # noqa: E712
        .groupby("arm")["fold"].nunique().rename("n_infeasible")
    )
    summary = summary.merge(n_inf, on="arm", how="outer")
    inf_only = res[~res["arm"].isin(summary.dropna(subset=["n_folds"])["arm"])]
    summary["n_infeasible"] = summary["n_infeasible"].fillna(0).astype(int)
    summary.to_csv(os.path.join(EXP, "exp_summary.csv"), index=False)
    print(summary.to_string(index=False))

    gamma_arms = ok[ok["arm"].str.startswith("gamma")].copy()
    gamma_arms["gamma"] = gamma_arms["gamma"].astype(int)
    if "alpha" not in gamma_arms.columns:
        gamma_arms["alpha"] = 1.0
    gamma_arms["alpha"] = gamma_arms["alpha"].fillna(1.0)
    tight_arms = ok[ok["arm"].str.startswith("tight")].copy()
    hex_arms = ok[ok["arm"] == "hexaly_k1"].copy()

    # gamma0 belongs to every alpha series (protection vanishes at Gamma=0).
    alphas = sorted(a for a in gamma_arms["alpha"].unique()
                    if (gamma_arms["alpha"] == a).any())
    alphas = [a for a in alphas if a != 1.0 or
              len(gamma_arms[(gamma_arms["alpha"] == 1.0) &
                             (gamma_arms["gamma"] > 0)])]
    base0 = gamma_arms[gamma_arms["gamma"] == 0]

    def series_for(a: float) -> pd.DataFrame:
        s = gamma_arms[(gamma_arms["alpha"] == a) & (gamma_arms["gamma"] > 0)]
        return pd.concat([base0, s], ignore_index=True)

    ALPHA_STYLE = {0.25: (VERM, ":"), 0.5: (VERM, "-"), 1.0: (INK, "--")}

    n_total_folds = ok["fold"].nunique()

    def series_stats(a: float, col: str) -> pd.DataFrame:
        s = series_for(a).groupby("gamma").agg(
            val=(col, "mean"), n=("fold", "nunique")).reset_index()
        return s

    # ---- Figure 1: trade-off vs Gamma (one line per alpha) ---------------
    # Arms feasible on fewer than all folds are drawn as OPEN markers off the
    # mean line (their mean is not comparable with full-coverage points).
    fig, axes = plt.subplots(1, 3, figsize=(6.3, 2.3))
    panels = [("PoR_pct", "PoR (% train visits)"),
              ("viol_norm", "stations $>$ ceiling (of 8)"),
              ("max_ratio_norm", r"max ratio $W_s/T^{\mathrm{n}}$")]
    for ax, (col, ylab) in zip(axes, panels):
        for a in alphas:
            s = series_stats(a, col)
            full = s[s["n"] == n_total_folds]
            part = s[s["n"] < n_total_folds]
            color, lsty = ALPHA_STYLE.get(a, (GREEN, "-"))
            ax.plot(full["gamma"], full["val"], color=color, linestyle=lsty,
                    linewidth=1.8, marker="o", markersize=3.5, zorder=3,
                    label=rf"$\alpha$={a:g}")
            if len(part):
                ax.scatter(part["gamma"], part["val"], s=22, facecolor="white",
                           edgecolor=color, linewidth=1.2, zorder=4)
                for _i, r in part.iterrows():
                    ax.annotate(f"{int(r['n'])}/{n_total_folds}",
                                (r["gamma"], r["val"]),
                                textcoords="offset points", xytext=(4, -9),
                                fontsize=6.5, color=color)
        if col == "max_ratio_norm":
            ax.axhline(1.0, color=INK, linewidth=0.7, linestyle="--")
        ax.set_xlabel(r"$\Gamma$")
        ax.set_ylabel(ylab)
        style_axis(ax)
    axes[0].legend(frameon=False, fontsize=7.5)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig_exp_tradeoff.pdf"), bbox_inches="tight")
    fig.savefig(os.path.join(PREV, "fig_exp_tradeoff.png"), dpi=150,
                bbox_inches="tight")
    plt.close(fig)

    # ---- Figure 2: targeted vs uniform frontier -------------------------
    fig, ax = plt.subplots(figsize=(4.6, 3.0))
    tm = tight_arms.groupby("arm").agg(
        x=("PoR_pct", "mean"), y=("max_ratio_norm", "mean")).reset_index()
    hm = hex_arms.agg(x=("PoR_pct", "mean"), y=("max_ratio_norm", "mean"))
    for a in alphas:
        gm = series_for(a).groupby("gamma").agg(
            x=("PoR_pct", "mean"), y=("max_ratio_norm", "mean"),
            n=("fold", "nunique")).reset_index()
        full = gm[gm["n"] == n_total_folds]
        part = gm[gm["n"] < n_total_folds]
        color, lsty = ALPHA_STYLE.get(a, (GREEN, "-"))
        ax.plot(full["x"], full["y"], color=color, linestyle=lsty,
                linewidth=1.2, marker="o", markersize=5, zorder=3,
                label=rf"budgeted ($\Gamma$, $\alpha$={a:g})")
        if len(part):
            ax.scatter(part["x"], part["y"], s=30, facecolor="white",
                       edgecolor=color, linewidth=1.2, zorder=4)
        for _i, r in gm.iterrows():
            if r["gamma"] > 0:
                tag = rf"$\Gamma$={int(r['gamma'])}"
                if r["n"] < n_total_folds:
                    tag += f" ({int(r['n'])}/{n_total_folds})"
                off = (5, 5) if a == 0.5 else (5, -10)
                ax.annotate(tag, (r["x"], r["y"]),
                            textcoords="offset points", xytext=off,
                            fontsize=6.5, color=color)
    ax.scatter(tm["x"], tm["y"], color=BLUE, s=36, marker="s", zorder=3,
               label=r"uniform tightening ($\beta$)")
    for _i, r in tm.iterrows():
        ax.annotate(r["arm"].replace("tight", r"$\beta$="), (r["x"], r["y"]),
                    textcoords="offset points", xytext=(-2, 8), fontsize=6.5,
                    color=BLUE, ha="right")
    if len(hex_arms):
        ax.scatter([hm.loc["x", "PoR_pct"]], [hm.loc["y", "max_ratio_norm"]],
                   color=GREEN, s=40, marker="^", zorder=3, label="Hexaly k=1")
    ax.axhline(1.0, color=INK, linewidth=0.7, linestyle="--")
    ax.set_xlabel("price of robustness PoR (% train visits)")
    ax.set_ylabel(r"mean peak ratio $W_s/T^{\mathrm{n}}$ (test)")
    ax.legend(frameon=False, fontsize=8, loc="best")
    style_axis(ax)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig_exp_frontier.pdf"), bbox_inches="tight")
    fig.savefig(os.path.join(PREV, "fig_exp_frontier.png"), dpi=150,
                bbox_inches="tight")
    plt.close(fig)

    # ---- Figure 3: per-station ratios, worst-drift fold -----------------
    st = pd.read_csv(os.path.join(EXP, "per_station.csv"))
    g0 = ok[ok["arm"] == "gamma0"]
    worst_fold = int(g0.loc[g0["max_ratio_norm"].idxmax(), "fold"])
    sub = st[st["fold"] == worst_fold]
    import re

    def arm_key(a: str):
        if a == "gamma0":
            return (0, 0.0, 0)
        m = re.match(r"gamma(\d+)(?:_a([\d.]+))?$", a)
        if m:
            return (1, -float(m.group(2) or 1.0), int(m.group(1)))
        if a.startswith("tight"):
            return (2, -float(a[5:]), 0)
        return (3, 0.0, 0)

    arm_order = sorted(set(sub["arm"]), key=arm_key)
    fig, ax = plt.subplots(figsize=(6.3, 2.5))
    xpos = np.arange(len(arm_order))
    rng = np.random.RandomState(0)
    for i, arm in enumerate(arm_order):
        vals = sub[sub["arm"] == arm]["ratio_norm"].to_numpy()
        jitter = (rng.rand(len(vals)) - 0.5) * 0.18
        color = (VERM if arm.startswith("gamma") and arm != "gamma0"
                 else BLUE if arm.startswith("tight") else GREEN
                 if arm == "hexaly_k1" else INK)
        ax.scatter(np.full(len(vals), xpos[i]) + jitter, vals, s=16,
                   facecolor=color, edgecolor="white", linewidth=0.5, zorder=3)
    ax.axhline(1.0, color=INK, linewidth=0.7, linestyle="--")
    labels = [a.replace("gamma", r"$\Gamma$=").replace("tight", r"$\beta$=")
              .replace("hexaly_k1", "Hexaly") for a in arm_order]
    ax.set_xticks(xpos)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel(r"station ratio $W_s/T^{\mathrm{n}}$")
    ax.set_xlabel(f"arms, temporal cut {worst_fold} (worst nominal peak)")
    style_axis(ax)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig_exp_stations.pdf"), bbox_inches="tight")
    fig.savefig(os.path.join(PREV, "fig_exp_stations.png"), dpi=150,
                bbox_inches="tight")
    plt.close(fig)
    print(f"figures written (worst fold = {worst_fold})")


if __name__ == "__main__":
    main()
