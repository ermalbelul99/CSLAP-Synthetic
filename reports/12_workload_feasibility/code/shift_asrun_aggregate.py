"""Aggregate the as-run wl_broken (and max_workload where present) columns from
ALL per_fold_shift_*.csv files across iscf10kt_results_* and iscfco_results_*.

One output row per (results_dir, shift_mode, tag, fold, k, rho) with the stored
wl_broken and max_workload. NOTE: none of the per_fold_shift CSVs on disk carry
a max_workload column (schema: tag,fold,k,rho,N_train_visits,V_test_visits,
coverage_kappa,cap_broken,wl_broken,c_bar), so max_workload is emitted as NaN;
cap_broken and visit counts are carried along for context.

Output: STUDY/data/secondary/shift_asrun_aggregate.csv
Also prints summary statistics of how often wl_broken > 0.
"""

from __future__ import annotations

import glob
import os
import re
from typing import List

import pandas as pd

BASE = (
    "C:/Users/Nico/PycharmProjects/CSLAP_Problem/Different_Solution_Approaches/"
    "Full_Package_Code_With_All_Approaches/CSLAP-Synthetic/Baselines"
)
STUDY = "C:/Users/Nico/PycharmProjects/CSLAP_Problem/reports/12_workload_feasibility"
OUT = os.path.join(STUDY, "data", "secondary", "shift_asrun_aggregate.csv")


def main() -> None:
    """Scan results dirs, concatenate all per_fold_shift CSVs, summarize."""
    dirs = sorted(
        d
        for d in glob.glob(os.path.join(BASE, "iscf10kt_results_*"))
        + glob.glob(os.path.join(BASE, "iscfco_results_*"))
        if os.path.isdir(d)
    )
    frames: List[pd.DataFrame] = []
    for d in dirs:
        for f in sorted(glob.glob(os.path.join(d, "per_fold_shift_*.csv"))):
            mode = re.match(r"per_fold_shift_(\w+)\.csv", os.path.basename(f)).group(1)
            df = pd.read_csv(f)
            df.insert(0, "results_dir", os.path.basename(d))
            df.insert(1, "shift_mode", mode)
            if "max_workload" not in df.columns:
                df["max_workload"] = float("nan")
            frames.append(df)
            print(f"loaded {os.path.basename(d)}/{os.path.basename(f)}: {len(df)} rows")
    agg = pd.concat(frames, ignore_index=True)
    cols = [
        "results_dir", "shift_mode", "tag", "fold", "k", "rho",
        "wl_broken", "max_workload", "cap_broken",
        "N_train_visits", "V_test_visits", "coverage_kappa",
    ]
    agg = agg[cols]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    agg.to_csv(OUT, index=False)
    print(f"\nwrote {OUT} ({len(agg)} rows)")

    n = len(agg)
    n_pos = int((agg["wl_broken"] > 0).sum())
    print(f"\nOVERALL: wl_broken>0 in {n_pos}/{n} rows ({100.0 * n_pos / n:.1f}%)")
    print(f"cap_broken>0 in {int((agg['cap_broken'] > 0).sum())}/{n} rows")
    by = (
        agg.groupby(["results_dir", "shift_mode"])
        .agg(rows=("wl_broken", "size"),
             rows_wl_pos=("wl_broken", lambda s: int((s > 0).sum())),
             max_wl_broken=("wl_broken", "max"),
             mean_wl_broken=("wl_broken", "mean"))
        .reset_index()
    )
    print("\nPer (results_dir, shift_mode):")
    print(by.to_string(index=False))
    byr = (
        agg.groupby("rho")
        .agg(rows=("wl_broken", "size"),
             rows_wl_pos=("wl_broken", lambda s: int((s > 0).sum())),
             mean_wl_broken=("wl_broken", "mean"))
        .reset_index()
    )
    print("\nPer rho (pooled):")
    print(byr.to_string(index=False))


if __name__ == "__main__":
    main()
