"""Aggregate the BERNER industrial (beta, Gamma) sweep into a report table.

Inputs:  STUDY/data/bern/bern{N}_b{beta}_{a|b}/results.csv
Outputs: STUDY/data/bern/bern_all.csv      merged rows, beta/gamma parsed
         STUDY/data/bern/bern_grid.csv     the (beta x Gamma) frontier table

PoR/G are recomputed per beta against that beta's own Gamma=0 arm (each beta is
a different training contract, so pairing must stay within a beta). Duplicate
Gamma=0 rows (present in both the a/b job halves) are de-duplicated.
"""
from __future__ import annotations

import glob
import os
import re

import numpy as np
import pandas as pd

STUDY = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
BERN = os.path.join(STUDY, "data", "bern")


def main() -> None:
    """Merge the per-(beta, half) result files and print the frontier grid."""
    frames = []
    for path in sorted(glob.glob(os.path.join(BERN, "bern*_b*_*", "results.csv"))):
        d = os.path.basename(os.path.dirname(path))
        m = re.match(r"bern(\d+)_b([\d.]+)_([ab])$", d)
        if not m:
            continue
        df = pd.read_csv(path)
        df["top_n"] = int(m.group(1))
        df["beta"] = float(m.group(2))
        frames.append(df)
    if not frames:
        raise FileNotFoundError(f"no results under {BERN}")
    allr = pd.concat(frames, ignore_index=True)
    allr["gamma_i"] = allr["gamma"].fillna(-1).astype(int)
    allr = allr.drop_duplicates(subset=["beta", "gamma_i"], keep="first")

    # Pair PoR/G within each beta (each beta is its own training contract).
    for beta, grp in allr.groupby("beta"):
        base = grp[grp["gamma_i"] == 0]
        if base.empty or not bool(base["feasible_model"].iloc[0]):
            continue
        v_tr0, v_te0 = float(base["V_tr"].iloc[0]), float(base["V_te"].iloc[0])
        m = allr["beta"] == beta
        allr.loc[m, "PoR_pct"] = 100.0 * (allr.loc[m, "V_tr"] - v_tr0) / v_tr0
        allr.loc[m, "G_pct"] = 100.0 * (v_te0 - allr.loc[m, "V_te"]) / v_te0
    allr = allr.sort_values(["beta", "gamma_i"])
    allr.to_csv(os.path.join(BERN, "bern_all.csv"), index=False)

    cols = ["beta", "gamma_i", "feasible_model", "proven_infeasible", "robust_ok",
            "V_tr", "V_te", "PoR_pct", "G_pct", "viol_norm", "max_ratio_norm",
            "X", "imbalance", "wl_broken_asrun", "solve_time"]
    grid = allr[[c for c in cols if c in allr.columns]].copy()
    grid.to_csv(os.path.join(BERN, "bern_grid.csv"), index=False)

    show = grid.copy()
    for c in ("PoR_pct", "G_pct", "max_ratio_norm", "imbalance"):
        if c in show:
            show[c] = show[c].round(3)
    if "X" in show:
        show["X_pct"] = (100 * show["X"]).round(2)
        show = show.drop(columns=["X"])
    with pd.option_context("display.width", 250, "display.max_columns", 99):
        print(show.to_string(index=False))

    feas = grid[grid["feasible_model"] == True]  # noqa: E712
    print(f"\nfeasible arms: {len(feas)}/{len(grid)}")
    if "robust_ok" in feas.columns:
        rb = feas[feas["gamma_i"] > 0]["robust_ok"]
        print(f"robust_ok on Gamma>0 arms: {int(rb.sum())}/{len(rb)}")


if __name__ == "__main__":
    main()
