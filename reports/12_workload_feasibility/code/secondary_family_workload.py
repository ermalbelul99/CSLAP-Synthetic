"""Workload-feasibility recomputation for the SECONDARY testbeds.

Families covered
----------------
1. iscfco base temporal (co-occurrence-rich instance), layouts from BOTH cover
   objectives: ``iscfco_layouts_mm`` (min-max) and ``iscfco_layouts_ms``
   (min-sum); folds shared in ``iscfco_folds_temporal``; k in {1, 10}.
2. Planted-affinity main run: 18 tags ``aff_{combine|reassign}_a{0.0|0.5|1.0}_r{0|1|2}``,
   k in {1, 10}, folds in ``iscf_affinity``, layouts in ``iscf_affinity_layouts``.
3. iscfco DEMAND-shift test sets (the only shift mode where per-product volumes
   move): rho in {0.0, 0.5, 1.0, 2.0}, evaluated for both mm and ms layouts
   against the shift set's OWN stations file (recomputed flat T_s), exactly as
   the as-run harness did (run_robustness_iscf.py:666-671).

Metrics (per the study protocol)
--------------------------------
Given layout a: p->s, test lines te_lines[p] (groupby PRODUCT size), speed V,
n_stations |S|, stored ceiling T_s (TIME_CAPACITY of the stations file the
as-run evaluation used):

* W_s        = sum_{p: a[p]=s} te_lines[p] / V   (layout-domain products only)
* viol_asrun = #{s : W_s > T_s};  ratio_asrun_s = W_s / T_s
* Tn         = ceil(1.10 * sum_p te_lines[p] / (V * |S|))   (volume-normalized)
* viol_norm  = #{s : W_s > Tn};   ratio_norm_s = W_s / Tn
* share_s    = W_s / sum W;  imbalance = max share * |S|
* B          = sum_p te_lines[p] / (V * |S| * T_s)   (bindingness of as-run check)
* X          = sum_s max(0, W_s - Tn) / sum_s W_s    (excess fraction)
* Train side: W_tr_s from tr_lines vs the TRAIN stations T_s (Hexaly enforced
  this HARD, so wl_tr_broken must be 0).

Sanity contract
---------------
viol_asrun MUST equal the stored wl_broken:
* iscfco base      -> rho==0.0 rows of iscfco_results_{mm,ms}/per_fold_shift_structured.csv
  (structured rho=0 orders verified byte-identical to the fold test orders).
* affinity         -> iscf_affinity_results/per_fold.csv (also checks max_workload).
* iscfco demand    -> iscfco_results_{mm,ms}/per_fold_shift_demand.csv per (tag,k,rho).

Outputs
-------
STUDY/data/secondary/per_station.csv
STUDY/data/secondary/per_fold.csv
"""

from __future__ import annotations

import json
import math
import os
from typing import Dict, List, Optional, Tuple

import pandas as pd

BASE = (
    "C:/Users/Nico/PycharmProjects/CSLAP_Problem/Different_Solution_Approaches/"
    "Full_Package_Code_With_All_Approaches/CSLAP-Synthetic/Baselines"
)
STUDY = "C:/Users/Nico/PycharmProjects/CSLAP_Problem/reports/12_workload_feasibility"
OUT_DIR = os.path.join(STUDY, "data", "secondary")
SLACK = 1.10

ISCFCO_TAGS = [f"iscfco_r0f{f}" for f in range(5)]
ISCFCO_K = [1, 10]
DEMAND_RHOS = [0.0, 0.5, 1.0, 2.0]
AFF_TAGS = [
    f"aff_{mode}_a{alpha}_r{rep}"
    for rep in range(3)
    for mode in ("combine", "reassign")
    for alpha in ("0.0", "0.5", "1.0")
]
AFF_K = [1, 10]


def load_layout(path: str) -> Dict[str, str]:
    """Load a flat {'PROD_<id>': 'GARE<n>'} layout JSON.

    NOTE: the planted-affinity r1 rep persisted EMPTY layouts ('{}', 2 bytes);
    the as-run per_fold.csv rows for r1 are correspondingly degenerate
    (coverage_kappa=0, V_test_visits=0, wl_broken=0). Empty layouts are allowed
    here and flagged downstream via the 'empty_layout' column."""
    with open(path, "r", encoding="utf-8") as fh:
        layout = json.load(fh)
    assert isinstance(layout, dict), f"invalid layout {path}"
    return layout


def load_lines(orders_csv: str) -> pd.Series:
    """Per-product line counts: groupby('PRODUCT').size() on a semicolon orders CSV."""
    df = pd.read_csv(orders_csv, sep=";")
    return df.groupby("PRODUCT").size()


def load_stations(stations_csv: str) -> Tuple[List[str], float, float]:
    """Return (station_ids, uniform speed V, uniform stored T_s) from a stations CSV.

    Asserts SPEED and TIME_CAPACITY are uniform across stations (true for all
    ISCF-derived families)."""
    st = pd.read_csv(stations_csv, sep=";")
    speeds = st["SPEED"].unique()
    tcaps = st["TIME_CAPACITY"].unique()
    assert len(speeds) == 1, f"non-uniform SPEED in {stations_csv}"
    assert len(tcaps) == 1, f"non-uniform TIME_CAPACITY in {stations_csv}"
    return list(st["STATION_ID"]), float(speeds[0]), float(tcaps[0])


def station_workloads(
    layout: Dict[str, str], lines: pd.Series, stations: List[str], speed: float
) -> Dict[str, float]:
    """Realized workload W_s = sum_{p: a[p]=s} lines[p]/V (layout-domain only)."""
    w = {s: 0.0 for s in stations}
    ld = lines.to_dict()
    for prod, stn in layout.items():
        cnt = ld.get(prod)
        if cnt is not None and stn in w:
            w[stn] += cnt / speed
    return w


def analyse_case(
    family: str,
    tag: str,
    k: int,
    mode: str,
    rho: float,
    layout_path: str,
    train_orders: str,
    test_orders: str,
    stored_stations: str,
    train_stations: str,
) -> Tuple[List[dict], dict]:
    """Compute per-station and per-fold workload metrics for one (tag, k[, rho]) case."""
    layout = load_layout(layout_path)
    tr_lines = load_lines(train_orders)
    te_lines = load_lines(test_orders)
    stations, v_stored, ts_stored = load_stations(stored_stations)
    stations_tr, v_train, ts_train = load_stations(train_stations)
    assert stations == stations_tr and v_stored == v_train
    n_s = len(stations)

    w_te = station_workloads(layout, te_lines, stations, v_stored)
    w_tr = station_workloads(layout, tr_lines, stations, v_train)

    total_te = float(te_lines.sum())
    total_tr = float(tr_lines.sum())
    tn = math.ceil(SLACK * total_te / (v_stored * n_s))
    sum_w = sum(w_te.values())

    st_rows: List[dict] = []
    for s in stations:
        st_rows.append(
            {
                "family": family,
                "tag": tag,
                "k": k,
                "mode": mode,
                "rho": rho,
                "station": s,
                "W_tr": w_tr[s],
                "W_te": w_te[s],
                "T_s_stored": ts_stored,
                "T_s_train": ts_train,
                "Tn": tn,
                "ratio_asrun": w_te[s] / ts_stored,
                "ratio_norm": w_te[s] / tn,
                "share": (w_te[s] / sum_w) if sum_w > 0 else 0.0,
                "viol_asrun_flag": int(w_te[s] > ts_stored),
                "viol_norm_flag": int(w_te[s] > tn),
                "wl_tr_broken_flag": int(w_tr[s] > ts_train),
            }
        )

    viol_asrun = sum(r["viol_asrun_flag"] for r in st_rows)
    viol_norm = sum(r["viol_norm_flag"] for r in st_rows)
    fold_row = {
        "family": family,
        "tag": tag,
        "k": k,
        "mode": mode,
        "rho": rho,
        "viol_asrun": viol_asrun,
        "viol_norm": viol_norm,
        "max_ratio_asrun": max(r["ratio_asrun"] for r in st_rows),
        "max_ratio_norm": max(r["ratio_norm"] for r in st_rows),
        "imbalance": max(r["share"] for r in st_rows) * n_s,
        "B": total_te / (v_stored * n_s * ts_stored),
        "X": sum(max(0.0, w - tn) for w in w_te.values()) / sum_w if sum_w > 0 else 0.0,
        "total_te_lines": total_te,
        "total_tr_lines": total_tr,
        "max_W_te": max(w_te.values()),
        "wl_tr_broken": sum(r["wl_tr_broken_flag"] for r in st_rows),
        "n_stations": n_s,
        "empty_layout": int(len(layout) == 0),
    }
    return st_rows, fold_row


def main() -> None:
    """Run all secondary-family recomputations, write CSVs, assert sanity."""
    os.makedirs(OUT_DIR, exist_ok=True)
    st_all: List[dict] = []
    fd_all: List[dict] = []
    mismatches: List[str] = []

    # ---------- stored anchors ----------
    anchors: Dict[str, pd.DataFrame] = {}
    for v in ("mm", "ms"):
        anchors[f"iscfco_{v}_base"] = pd.read_csv(
            os.path.join(BASE, f"iscfco_results_{v}", "per_fold_shift_structured.csv")
        )
        anchors[f"iscfco_{v}_demand"] = pd.read_csv(
            os.path.join(BASE, f"iscfco_results_{v}", "per_fold_shift_demand.csv")
        )
    anchors["affinity"] = pd.read_csv(
        os.path.join(BASE, "iscf_affinity_results", "per_fold.csv")
    )

    def stored_wl(df: pd.DataFrame, tag: str, k: int, rho: Optional[float]) -> int:
        m = (df["tag"] == tag) & (df["k"] == k)
        if rho is not None:
            m &= df["rho"] == rho
        sub = df[m]
        assert len(sub) == 1, f"anchor rows != 1 for {tag} k={k} rho={rho}: {len(sub)}"
        return int(sub["wl_broken"].iloc[0])

    # ---------- 1) iscfco base temporal, mm + ms layouts ----------
    for v in ("mm", "ms"):
        fam = f"iscfco_{v}"
        for tag in ISCFCO_TAGS:
            fdir = os.path.join(BASE, "iscfco_folds_temporal")
            tr_o = os.path.join(fdir, f"{tag}_train_orders.csv")
            te_o = os.path.join(fdir, f"{tag}_test_orders.csv")
            st_f = os.path.join(fdir, f"{tag}_train_stations.csv")
            for k in ISCFCO_K:
                lay = os.path.join(BASE, f"iscfco_layouts_{v}", f"layout_{tag}_k{k}.json")
                srows, frow = analyse_case(
                    fam, tag, k, "base", 0.0, lay, tr_o, te_o, st_f, st_f
                )
                anchor = stored_wl(anchors[f"iscfco_{v}_base"], tag, k, 0.0)
                frow["stored_wl_broken"] = anchor
                frow["sanity_ok"] = int(frow["viol_asrun"] == anchor)
                if frow["viol_asrun"] != anchor:
                    mismatches.append(
                        f"{fam} {tag} k={k} base: viol_asrun={frow['viol_asrun']} "
                        f"!= stored wl_broken={anchor}"
                    )
                st_all += srows
                fd_all.append(frow)
                print(
                    f"[{fam}] {tag} k={k} base: viol_asrun={frow['viol_asrun']} "
                    f"(stored {anchor}), viol_norm={frow['viol_norm']}, "
                    f"B={frow['B']:.3f}, imb={frow['imbalance']:.3f}"
                )

    # ---------- 2) planted-affinity main run ----------
    for tag in AFF_TAGS:
        fdir = os.path.join(BASE, "iscf_affinity")
        tr_o = os.path.join(fdir, f"{tag}_train_orders.csv")
        te_o = os.path.join(fdir, f"{tag}_test_orders.csv")
        st_f = os.path.join(fdir, f"{tag}_train_stations.csv")
        for k in AFF_K:
            lay = os.path.join(BASE, "iscf_affinity_layouts", f"layout_{tag}_k{k}.json")
            srows, frow = analyse_case(
                "affinity", tag, k, "base", 0.0, lay, tr_o, te_o, st_f, st_f
            )
            adf = anchors["affinity"]
            sub = adf[(adf["tag"] == tag) & (adf["k"] == k)]
            assert len(sub) == 1, f"affinity anchor rows != 1 for {tag} k={k}"
            anchor = int(sub["wl_broken"].iloc[0])
            stored_maxw = float(sub["max_workload"].iloc[0])
            frow["stored_wl_broken"] = anchor
            ok = frow["viol_asrun"] == anchor and abs(frow["max_W_te"] - stored_maxw) < 1e-6
            frow["sanity_ok"] = int(ok)
            if not ok:
                mismatches.append(
                    f"affinity {tag} k={k}: viol_asrun={frow['viol_asrun']} vs stored "
                    f"wl_broken={anchor}; max_W_te={frow['max_W_te']} vs stored "
                    f"max_workload={stored_maxw}"
                )
            st_all += srows
            fd_all.append(frow)
            print(
                f"[affinity] {tag} k={k}: viol_asrun={frow['viol_asrun']} "
                f"(stored {anchor}), viol_norm={frow['viol_norm']}, "
                f"maxW={frow['max_W_te']:.0f} (stored {stored_maxw:.0f}), "
                f"B={frow['B']:.3f}"
            )

    # ---------- 3) iscfco demand-shift recomputation (mm + ms layouts) ----------
    for v in ("mm", "ms"):
        fam = f"iscfco_{v}"
        for tag in ISCFCO_TAGS:
            tr_o = os.path.join(BASE, "iscfco_folds_temporal", f"{tag}_train_orders.csv")
            st_tr = os.path.join(
                BASE, "iscfco_folds_temporal", f"{tag}_train_stations.csv"
            )
            for rho in DEMAND_RHOS:
                sdir = os.path.join(BASE, "iscfco_shift_demand")
                te_o = os.path.join(sdir, f"{tag}_test_demand_r{rho}_orders.csv")
                st_sh = os.path.join(sdir, f"{tag}_test_demand_r{rho}_stations.csv")
                for k in ISCFCO_K:
                    lay = os.path.join(
                        BASE, f"iscfco_layouts_{v}", f"layout_{tag}_k{k}.json"
                    )
                    srows, frow = analyse_case(
                        fam, tag, k, "demand", rho, lay, tr_o, te_o, st_sh, st_tr
                    )
                    anchor = stored_wl(anchors[f"iscfco_{v}_demand"], tag, k, rho)
                    frow["stored_wl_broken"] = anchor
                    frow["sanity_ok"] = int(frow["viol_asrun"] == anchor)
                    if frow["viol_asrun"] != anchor:
                        mismatches.append(
                            f"{fam} {tag} k={k} demand rho={rho}: viol_asrun="
                            f"{frow['viol_asrun']} != stored wl_broken={anchor}"
                        )
                    st_all += srows
                    fd_all.append(frow)
                    print(
                        f"[{fam}] {tag} k={k} demand rho={rho}: "
                        f"viol_asrun={frow['viol_asrun']} (stored {anchor}), "
                        f"viol_norm={frow['viol_norm']}, B={frow['B']:.3f}"
                    )

    per_station = pd.DataFrame(st_all)
    per_fold = pd.DataFrame(fd_all)
    ps_path = os.path.join(OUT_DIR, "per_station.csv")
    pf_path = os.path.join(OUT_DIR, "per_fold.csv")
    per_station.to_csv(ps_path, index=False)
    per_fold.to_csv(pf_path, index=False)
    print(f"\nwrote {ps_path} ({len(per_station)} rows)")
    print(f"wrote {pf_path} ({len(per_fold)} rows)")

    n_tr_broken = int(per_fold["wl_tr_broken"].sum())
    print(f"\nTRAIN-side violations across all base cases (should be 0 for base): "
          f"{int(per_fold.loc[per_fold['mode'] == 'base', 'wl_tr_broken'].sum())}")
    print(f"TRAIN-side violations total (incl. demand rows, train vs train T_s): {n_tr_broken}")

    if mismatches:
        print("\nSANITY FAIL — mismatches:")
        for m in mismatches:
            print("  " + m)
        raise AssertionError(f"{len(mismatches)} sanity mismatches (see above)")
    print("\nSANITY PASS: every viol_asrun equals the stored wl_broken "
          "(and affinity max_W_te equals stored max_workload).")


if __name__ == "__main__":
    main()
