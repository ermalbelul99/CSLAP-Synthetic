"""Aggregate the exp02a BS-robustness sweep into a size-class summary.

Inputs:  STUDY/data/exp02a/<instance_tag>/results.csv   (one dir per instance)
Outputs: STUDY/data/exp02a/exp02a_all.csv               merged per-arm rows
         STUDY/data/exp02a/exp02a_summary.csv           per (size, arm) stats
                                                        across seeds (mean, sd)

PoR/G are recomputed per instance against its gamma0 arm (defensive). Size
class parsed from the tag (syn_{N}sku_seed{S}).
"""
from __future__ import annotations

import glob
import os
import re

import numpy as np
import pandas as pd

STUDY = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
EXP = os.path.join(STUDY, "data", "exp02a")


def main() -> None:
    """Merge per-instance results and build the per-size summary."""
    frames = []
    for path in sorted(glob.glob(os.path.join(EXP, "syn_*", "results.csv"))):
        tag = os.path.basename(os.path.dirname(path))
        m = re.match(r"syn_(\d+)sku_seed(\d+)", tag)
        df = pd.read_csv(path)
        df["instance"] = tag
        df["size"] = int(m.group(1))
        df["seed"] = int(m.group(2))
        frames.append(df)
    if not frames:
        raise FileNotFoundError(f"no results under {EXP}")
    allr = pd.concat(frames, ignore_index=True)

    # Defensive PoR/G recompute vs each instance's gamma0.
    for tag, grp in allr.groupby("instance"):
        base = grp[grp["arm"] == "gamma0"]
        if base.empty or not bool(base["feasible_model"].iloc[0]):
            continue
        v_tr0, v_te0 = float(base["V_tr"].iloc[0]), float(base["V_te"].iloc[0])
        m = allr["instance"] == tag
        allr.loc[m, "PoR_pct"] = 100.0 * (allr.loc[m, "V_tr"] - v_tr0) / v_tr0
        allr.loc[m, "G_pct"] = 100.0 * (v_te0 - allr.loc[m, "V_te"]) / v_te0
    allr.to_csv(os.path.join(EXP, "exp02a_all.csv"), index=False)

    ok = allr[allr["feasible_model"] == True].copy()  # noqa: E712
    summary = (
        ok.groupby(["size", "arm"])
        .agg(
            n_seeds=("seed", "nunique"),
            PoR_mean=("PoR_pct", "mean"),
            PoR_sd=("PoR_pct", "std"),
            G_mean=("G_pct", "mean"),
            viol_mean=("viol_norm", "mean"),
            viol_max=("viol_norm", "max"),
            peak_mean=("max_ratio_norm", "mean"),
            peak_max=("max_ratio_norm", "max"),
            X_mean=("X", "mean"),
            wl_asrun_mean=("wl_broken_asrun", "mean"),
            robust_ok_all=("robust_ok", "min"),
            solve_time_mean=("solve_time", "mean"),
        )
        .reset_index()
    )
    n_inf = (
        allr[allr["feasible_model"] == False]  # noqa: E712
        .groupby(["size", "arm"])["instance"].nunique().rename("n_infeasible")
    )
    summary = summary.merge(n_inf, on=["size", "arm"], how="outer")
    summary["n_infeasible"] = summary["n_infeasible"].fillna(0).astype(int)
    summary = summary.sort_values(["size", "arm"])
    summary.to_csv(os.path.join(EXP, "exp02a_summary.csv"), index=False)

    with pd.option_context("display.width", 250, "display.max_columns", 99):
        print(summary.round(3).to_string(index=False))
    n_missing = 29 - allr["instance"].nunique()
    print(f"\ninstances aggregated: {allr['instance'].nunique()}/29"
          + (f"  (MISSING {n_missing})" if n_missing else ""))
    # Per-fold c fit diagnostics from calibration files.
    cals = []
    for path in sorted(glob.glob(os.path.join(EXP, "syn_*", "calibration.csv"))):
        c = pd.read_csv(path)
        c["instance"] = os.path.basename(os.path.dirname(path))
        cals.append(c)
    cal = pd.concat(cals, ignore_index=True)
    print("\ncalibration c_q90: min={:.2f} median={:.2f} max={:.2f}; "
          "lhat_max median={:.0f}".format(
              cal["c_fit_q90"].min(), cal["c_fit_q90"].median(),
              cal["c_fit_q90"].max(), cal["lhat_max"].median()))


if __name__ == "__main__":
    main()
