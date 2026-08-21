"""Out-of-sample workload feasibility analysis for the iscf480 family (PRIMARY).

Covers BOTH splits of the iscf480 instance (480 SKUs, 8 uniform stations
GARE4..GARE11, SPEED = 1.0):

* CV split      : iscf_folds / iscf_layouts / iscf_results          (5 random folds)
* temporal split: iscf_folds_temporal / iscf_layouts_temporal /
                  iscf_results_temporal                             (5 expanding cuts)

for k in {1, 2} (nominal layout vs kappa=2 closure layout).

Metric definitions (exactly as specified by the study protocol)
---------------------------------------------------------------
Given layout a: p -> s, test per-product lines te_lines[p]
(= groupby PRODUCT size on the fold's test_orders.csv; ISCF fold files have
no duplicate (ORDER, PRODUCT) rows, so this equals distinct-order counts),
train lines tr_lines[p] likewise, speed V, n_stations |S|, and the stored
ceiling T_s (TIME_CAPACITY of the TRAIN stations file, which the as-run
evaluation re-used for the test check):

* realized test workload      W_s      = sum_{p: a[p]=s} te_lines[p] / V
* AS-RUN violation count      viol_asrun = #{s : W_s > T_s}   (strict >)
* as-run load ratio           ratio_asrun_s = W_s / T_s
* volume-normalized ceiling   Tn = ceil(1.10 * (sum_p te_lines[p]) / (V * |S|))
* normalized violation count  viol_norm = #{s : W_s > Tn}
* normalized load ratio       ratio_norm_s = W_s / Tn
* load share                  share_s = W_s / sum_s' W_s'
* imbalance                   max_s share_s * |S|      (1.0 = perfect balance)
* bindingness                 B = (sum_p te_lines[p]) / (V * |S| * T_s)
                              (B >= 1/1.10 => the as-run check is volume-binding;
                               B << 1/1.10 => slack by volume, wl_broken=0 is
                               uninformative)
* excess fraction             X = sum_s max(0, W_s - Tn) / sum_s W_s
* train-side counterpart      W_tr_s = sum_{p: a[p]=s} tr_lines[p] / V,
                              checked against T_s (must hold: Hexaly enforced it)

Outputs (written under STUDY/data/iscf480/)
-------------------------------------------
* per_station.csv        one row per (split, fold, k, station)
* per_fold.csv           one row per (split, fold, k) with the fold-level metrics
* heatmap_<split>_k<k>.csv   4 matrices (rows = stations, cols = folds) of ratio_norm
* top3_overloaded_temporal.csv  top-3 stations by ratio_norm per temporal (fold, k)

Sanity contract: viol_asrun MUST equal the stored wl_broken of the as-run
results per_fold.csv for every (split, fold, k) — asserted, mismatches reported
verbatim before the assertion fires.
"""

from __future__ import annotations

import json
import math
import os
from typing import Dict, List, Tuple

import pandas as pd

BASE: str = (
    "C:/Users/Nico/PycharmProjects/CSLAP_Problem/Different_Solution_Approaches/"
    "Full_Package_Code_With_All_Approaches/CSLAP-Synthetic/Baselines"
)
STUDY: str = "C:/Users/Nico/PycharmProjects/CSLAP_Problem/reports/12_workload_feasibility"
OUT_DIR: str = os.path.join(STUDY, "data", "iscf480")

PREFIX: str = "iscf480"
FOLDS: List[str] = ["r0f0", "r0f1", "r0f2", "r0f3", "r0f4"]
K_VALUES: List[int] = [1, 2]
SLACK: float = 1.10

SPLITS: Dict[str, Dict[str, str]] = {
    "cv": {
        "folds_dir": os.path.join(BASE, "iscf_folds"),
        "layouts_dir": os.path.join(BASE, "iscf_layouts"),
        "results_csv": os.path.join(BASE, "iscf_results", "per_fold.csv"),
    },
    "temporal": {
        "folds_dir": os.path.join(BASE, "iscf_folds_temporal"),
        "layouts_dir": os.path.join(BASE, "iscf_layouts_temporal"),
        "results_csv": os.path.join(BASE, "iscf_results_temporal", "per_fold.csv"),
    },
}


def load_lines(orders_csv: str) -> "pd.Series":
    """Per-product line counts: groupby PRODUCT size on a semicolon orders CSV."""
    df = pd.read_csv(orders_csv, sep=";")
    return df.groupby("PRODUCT").size()


def load_stations(stations_csv: str) -> Tuple[List[str], float, float]:
    """Return (station ids in file order, uniform SPEED V, stored ceiling T_s).

    iscf480 stations are homogeneous (same CAPACITY / TIME_CAPACITY / SPEED);
    homogeneity is asserted.
    """
    st = pd.read_csv(stations_csv, sep=";")
    assert st["SPEED"].nunique() == 1, f"non-uniform SPEED in {stations_csv}"
    assert st["TIME_CAPACITY"].nunique() == 1, f"non-uniform T_s in {stations_csv}"
    return (
        st["STATION_ID"].astype(str).tolist(),
        float(st["SPEED"].iloc[0]),
        float(st["TIME_CAPACITY"].iloc[0]),
    )


def station_workloads(
    layout: Dict[str, str], lines: "pd.Series", stations: List[str], speed: float
) -> Dict[str, float]:
    """W_s = sum_{p: layout[p]=s} lines[p] / V; products absent from orders add 0."""
    w: Dict[str, float] = {s: 0.0 for s in stations}
    for prod, stn in layout.items():
        n = int(lines.get(prod, 0))
        if n:
            w[stn] += n / speed
    return w


def analyze() -> None:
    """Run the full iscf480 analysis for both splits and write all CSVs."""
    os.makedirs(OUT_DIR, exist_ok=True)

    per_station_rows: List[dict] = []
    per_fold_rows: List[dict] = []
    top3_rows: List[dict] = []
    heatmaps: Dict[Tuple[str, int], pd.DataFrame] = {}
    mismatches: List[str] = []

    for split, cfg in SPLITS.items():
        stored = pd.read_csv(cfg["results_csv"])
        stored = stored.set_index(["fold", "k"])

        # heatmap frames: rows = stations, cols = folds
        hm: Dict[int, Dict[str, Dict[str, float]]] = {k: {} for k in K_VALUES}

        for fold_tag in FOLDS:
            fold_idx = int(fold_tag.split("f")[1])
            fdir = cfg["folds_dir"]
            tr_lines = load_lines(os.path.join(fdir, f"{PREFIX}_{fold_tag}_train_orders.csv"))
            te_lines = load_lines(os.path.join(fdir, f"{PREFIX}_{fold_tag}_test_orders.csv"))
            stations, speed, t_stored = load_stations(
                os.path.join(fdir, f"{PREFIX}_{fold_tag}_train_stations.csv")
            )
            n_st = len(stations)
            total_te = int(te_lines.sum())
            total_tr = int(tr_lines.sum())
            t_norm = math.ceil(SLACK * total_te / (speed * n_st))
            bindingness = total_te / (speed * n_st * t_stored)

            for k in K_VALUES:
                lay_path = os.path.join(
                    cfg["layouts_dir"], f"layout_{PREFIX}_{fold_tag}_k{k}.json"
                )
                with open(lay_path, "r", encoding="utf-8") as fh:
                    layout: Dict[str, str] = json.load(fh)

                w_te = station_workloads(layout, te_lines, stations, speed)
                w_tr = station_workloads(layout, tr_lines, stations, speed)
                n_assigned = {s: 0 for s in stations}
                for stn in layout.values():
                    n_assigned[stn] += 1

                sum_w = sum(w_te.values())
                viol_asrun = sum(1 for s in stations if w_te[s] > t_stored)
                viol_norm = sum(1 for s in stations if w_te[s] > t_norm)
                viol_train = sum(1 for s in stations if w_tr[s] > t_stored)
                max_ratio_asrun = max(w_te[s] / t_stored for s in stations)
                max_ratio_norm = max(w_te[s] / t_norm for s in stations)
                imbalance = max(w_te[s] / sum_w for s in stations) * n_st
                excess = sum(max(0.0, w_te[s] - t_norm) for s in stations) / sum_w

                hm[k][fold_tag] = {s: w_te[s] / t_norm for s in stations}

                for s in stations:
                    per_station_rows.append(
                        {
                            "split": split,
                            "fold": fold_tag,
                            "k": k,
                            "station": s,
                            "n_products": n_assigned[s],
                            "W_tr": w_tr[s],
                            "W_te": w_te[s],
                            "T_s_stored": t_stored,
                            "Tn": t_norm,
                            "ratio_asrun": w_te[s] / t_stored,
                            "ratio_norm": w_te[s] / t_norm,
                            "share": w_te[s] / sum_w,
                            "flag_asrun": int(w_te[s] > t_stored),
                            "flag_norm": int(w_te[s] > t_norm),
                            "flag_train_viol": int(w_tr[s] > t_stored),
                        }
                    )

                stored_row = stored.loc[(fold_idx, k)]
                stored_wl = int(stored_row["wl_broken"])
                stored_maxw = float(stored_row["max_workload"])
                max_w = max(w_te.values())
                sanity_ok = viol_asrun == stored_wl
                if not sanity_ok:
                    mismatches.append(
                        f"{split} fold={fold_tag} k={k}: viol_asrun={viol_asrun} "
                        f"!= stored wl_broken={stored_wl}"
                    )
                if abs(max_w - stored_maxw) > 1e-6:
                    mismatches.append(
                        f"{split} fold={fold_tag} k={k}: max W_s={max_w} "
                        f"!= stored max_workload={stored_maxw} (soft check)"
                    )

                per_fold_rows.append(
                    {
                        "split": split,
                        "fold": fold_tag,
                        "k": k,
                        "viol_asrun": viol_asrun,
                        "stored_wl_broken": stored_wl,
                        "sanity_ok": sanity_ok,
                        "viol_norm": viol_norm,
                        "viol_train": viol_train,
                        "max_ratio_asrun": max_ratio_asrun,
                        "max_ratio_norm": max_ratio_norm,
                        "imbalance": imbalance,
                        "B": bindingness,
                        "X": excess,
                        "total_te_lines": total_te,
                        "total_tr_lines": total_tr,
                        "T_s_stored": t_stored,
                        "Tn": t_norm,
                        "max_W_te": max_w,
                        "stored_max_workload": stored_maxw,
                    }
                )

                if split == "temporal":
                    top3 = sorted(stations, key=lambda s: w_te[s], reverse=True)[:3]
                    for rank, s in enumerate(top3, start=1):
                        top3_rows.append(
                            {
                                "fold": fold_tag,
                                "k": k,
                                "rank": rank,
                                "station": s,
                                "ratio_norm": w_te[s] / t_norm,
                                "ratio_asrun": w_te[s] / t_stored,
                                "n_products": n_assigned[s],
                            }
                        )

                print(
                    f"[{split}] {fold_tag} k={k}: viol_asrun={viol_asrun} "
                    f"(stored {stored_wl}) viol_norm={viol_norm} "
                    f"max_ratio_norm={max_ratio_norm:.3f} B={bindingness:.3f} "
                    f"imbalance={imbalance:.3f} X={excess:.4f}"
                )

        for k in K_VALUES:
            heatmaps[(split, k)] = pd.DataFrame(hm[k])  # rows=stations, cols=folds

    ps = pd.DataFrame(per_station_rows)
    pf = pd.DataFrame(per_fold_rows)
    ps.to_csv(os.path.join(OUT_DIR, "per_station.csv"), index=False)
    pf.to_csv(os.path.join(OUT_DIR, "per_fold.csv"), index=False)
    pd.DataFrame(top3_rows).to_csv(
        os.path.join(OUT_DIR, "top3_overloaded_temporal.csv"), index=False
    )
    for (split, k), df in heatmaps.items():
        df.index.name = "station"
        df.to_csv(os.path.join(OUT_DIR, f"heatmap_{split}_k{k}.csv"))
    print(f"\nWrote CSVs to {OUT_DIR}")

    if mismatches:
        print("\nSANITY MISMATCHES:")
        for m in mismatches:
            print("  " + m)
    assert not mismatches, f"{len(mismatches)} sanity mismatch(es) — see above"
    print("SANITY PASS: viol_asrun == stored wl_broken for all 20 (split, fold, k) "
          "cells; max W_te matches stored max_workload.")


if __name__ == "__main__":
    analyze()
