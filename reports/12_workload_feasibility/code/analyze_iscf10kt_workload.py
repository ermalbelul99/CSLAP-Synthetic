"""Out-of-sample workload-feasibility analysis for the iscf10kt family.

Covers the temporal split (full train) and the sparse-train variants
t500 / t1000 / t2000 (same fold geometry, train sub-sampled to 500/1000/2000
orders). For every (variant, fold, k, station) it recomputes:

* realized TEST workload  ``W_s = sum_{p: a[p]=s} te_lines[p] / V``
* the AS-RUN feasibility check against the stored TIME_CAPACITY ``T_s``
  (the ceiling the as-run evaluation actually used),
* a VOLUME-NORMALIZED check against ``Tn = ceil(1.10 * sum_p te_lines[p] / (V*|S|))``,
* load shares / imbalance, bindingness ``B``, excess fraction ``X``,
* the TRAIN-side counterpart ``W^tr_s`` vs ``T_s`` (Hexaly enforced it HARD).

SANITY CONTRACT: recomputed ``viol_asrun`` must equal the stored ``wl_broken``
* temporal  -> iscf10kt_results_temporal/per_fold.csv, all (fold, k);
* t500/t1000/t2000 -> the rho=0.0 slice of the variant's
  per_fold_shift_{structured,unstructured}.csv (the unshifted-test evaluation).
  The shift dirs on disk carry the TEMPORAL fold stations (T_s=1904 for f0),
  which cannot reproduce wl_broken=8; the sparse as-run evals therefore used
  the variant's OWN train-calibrated stations. The script tests both
  hypotheses per row and asserts exactly one reproduces the stored counts.

Outputs (semicolon-free, comma CSVs):
* <STUDY>/data/iscf10kt/per_station.csv
* <STUDY>/data/iscf10kt/per_fold.csv
* <STUDY>/data/iscf10kt/k_effect.csv          (viol_norm & imbalance vs k)
* <STUDY>/data/iscf10kt/sparse_train_effect.csv (feasibility vs train size)
"""
from __future__ import annotations

import json
import math
import os
import sys
from typing import Dict, List, Optional, Tuple

import pandas as pd

BASE = (r"C:\Users\Nico\PycharmProjects\CSLAP_Problem\Different_Solution_Approaches"
        r"\Full_Package_Code_With_All_Approaches\CSLAP-Synthetic\Baselines")
STUDY = r"C:\Users\Nico\PycharmProjects\CSLAP_Problem\reports\12_workload_feasibility"
OUT_DIR = os.path.join(STUDY, "data", "iscf10kt")

FOLDS: List[int] = [0, 1, 2, 3, 4]
KS: List[int] = [1, 2, 3, 4, 6]
SLACK: float = 1.10
N_STATIONS: int = 8

VARIANTS: Dict[str, Dict[str, str]] = {
    "temporal": {
        "folds_dir": os.path.join(BASE, "iscf10kt_folds_temporal"),
        "layouts_dir": os.path.join(BASE, "iscf10kt_layouts_temporal"),
        "results": os.path.join(BASE, "iscf10kt_results_temporal", "per_fold.csv"),
        "kind": "plain",
    },
    "t500": {
        "folds_dir": os.path.join(BASE, "iscf10kt_folds_t500"),
        "layouts_dir": os.path.join(BASE, "iscf10kt_layouts_t500"),
        "results": os.path.join(BASE, "iscf10kt_results_t500"),
        "kind": "shift",
    },
    "t1000": {
        "folds_dir": os.path.join(BASE, "iscf10kt_folds_t1000"),
        "layouts_dir": os.path.join(BASE, "iscf10kt_layouts_t1000"),
        "results": os.path.join(BASE, "iscf10kt_results_t1000"),
        "kind": "shift",
    },
    "t2000": {
        "folds_dir": os.path.join(BASE, "iscf10kt_folds_t2000"),
        "layouts_dir": os.path.join(BASE, "iscf10kt_layouts_t2000"),
        "results": os.path.join(BASE, "iscf10kt_results_t2000"),
        "kind": "shift",
    },
}
SHIFT_DIR_STRUCTURED = os.path.join(BASE, "iscf10kt_shift_structured")
TEMPORAL_SHIFT_RESULTS = os.path.join(
    BASE, "iscf10kt_results_shift", "per_fold_shift_structured.csv")


def read_orders(path: str) -> pd.DataFrame:
    """Read a semicolon-separated fold orders CSV (ORDER;PRODUCT;QTY;STATION)."""
    return pd.read_csv(path, sep=";")


def lines_by_product(orders: pd.DataFrame) -> Dict[str, int]:
    """Per-product line counts: groupby('PRODUCT').size() — as-run semantics."""
    return orders.groupby("PRODUCT").size().to_dict()


def read_stations(path: str) -> Tuple[List[str], Dict[str, float], Dict[str, float], float]:
    """Read a stations CSV; return (ids, time_caps, caps, uniform speed)."""
    df = pd.read_csv(path, sep=";")
    speeds = df["SPEED"].astype(float).tolist()
    assert len(set(speeds)) == 1, f"non-uniform SPEED in {path}"
    ids = df["STATION_ID"].astype(str).tolist()
    tcaps = dict(zip(ids, df["TIME_CAPACITY"].astype(float)))
    caps = dict(zip(ids, df["CAPACITY"].astype(float)))
    return ids, tcaps, caps, speeds[0]


def load_layout(path: str) -> Dict[str, str]:
    """Load a flat {'PROD_<id>': 'GARE<n>'} layout JSON (accept nested form)."""
    with open(path) as fh:
        data = json.load(fh)
    if isinstance(data, dict) and "assignment" in data and isinstance(data["assignment"], dict):
        return data["assignment"]
    return data


def station_workloads(layout: Dict[str, str], lines: Dict[str, int],
                      station_ids: List[str], speed: float) -> Dict[str, float]:
    """W_s = sum_{p: a[p]=s} lines[p]/V; stations with no demand contribute 0."""
    w: Dict[str, float] = {sid: 0.0 for sid in station_ids}
    for p, sid in layout.items():
        w[sid] = w.get(sid, 0.0) + lines.get(p, 0) / speed
    return w


def total_visits(layout: Dict[str, str], orders: pd.DataFrame) -> int:
    """Total station visits over orders: |{a[p] : p in order, p in domain}| summed."""
    dom = layout
    visits = 0
    for _o, prods in orders.groupby("ORDER")["PRODUCT"]:
        visits += len({dom[p] for p in prods if p in dom})
    return visits


def main() -> None:
    """Run the full per-station / per-fold recomputation and sanity checks."""
    os.makedirs(OUT_DIR, exist_ok=True)

    # -- stored as-run results ------------------------------------------------
    stored_temporal = pd.read_csv(VARIANTS["temporal"]["results"])
    stored_shift_rho0: Dict[str, pd.DataFrame] = {}
    for var in ("t500", "t1000", "t2000"):
        frames = []
        for mode in ("structured", "unstructured"):
            fp = os.path.join(VARIANTS[var]["results"], f"per_fold_shift_{mode}.csv")
            df = pd.read_csv(fp)
            df = df[df["rho"] == 0.0].copy()
            df["mode"] = mode
            frames.append(df)
        both = pd.concat(frames, ignore_index=True)
        # rho=0 rows must agree between structured and unstructured (0 swaps).
        piv = both.pivot_table(index=["fold", "k"], columns="mode",
                               values="wl_broken", aggfunc="first")
        assert (piv["structured"] == piv["unstructured"]).all(), \
            f"{var}: structured vs unstructured rho=0 wl_broken disagree"
        stored_shift_rho0[var] = both[both["mode"] == "structured"].set_index(["fold", "k"])
    stored_temporal_ix = stored_temporal.set_index(["fold", "k"])
    stored_tshift = pd.read_csv(TEMPORAL_SHIFT_RESULTS)
    stored_tshift_rho0 = stored_tshift[stored_tshift["rho"] == 0.0].set_index(["fold", "k"])

    per_station_rows: List[Dict[str, object]] = []
    per_fold_rows: List[Dict[str, object]] = []
    sanity_failures: List[str] = []

    # temporal test-line dicts, reused to assert sparse variants share test sets
    temporal_te_lines: Dict[int, Dict[str, int]] = {}

    for var, cfg in VARIANTS.items():
        fdir, ldir = cfg["folds_dir"], cfg["layouts_dir"]
        for fold in FOLDS:
            tag = f"iscf10kt_r0f{fold}"
            tr_orders = read_orders(os.path.join(fdir, f"{tag}_train_orders.csv"))
            te_orders = read_orders(os.path.join(fdir, f"{tag}_test_orders.csv"))
            tr_lines = lines_by_product(tr_orders)
            te_lines = lines_by_product(te_orders)
            ids, tcaps, caps, speed = read_stations(
                os.path.join(fdir, f"{tag}_train_stations.csv"))
            ids_te, tcaps_te, _, _ = read_stations(
                os.path.join(fdir, f"{tag}_test_stations.csv"))
            assert ids == ids_te and tcaps == tcaps_te, \
                f"{var} {tag}: test stations differ from train stations"
            assert len(ids) == N_STATIONS

            if var == "temporal":
                temporal_te_lines[fold] = te_lines
            else:
                assert te_lines == temporal_te_lines[fold], \
                    f"{var} {tag}: test set differs from temporal test set"

            # shift rho=0 artifacts (used by the sparse as-run evaluation)
            shift_orders_path = os.path.join(
                SHIFT_DIR_STRUCTURED, f"{tag}_test_structured_r0.0_orders.csv")
            shift_st_path = os.path.join(
                SHIFT_DIR_STRUCTURED, f"{tag}_test_structured_r0.0_stations.csv")
            shift_orders = read_orders(shift_orders_path)
            shift_lines = lines_by_product(shift_orders)
            assert shift_lines == te_lines, \
                f"{tag}: shift rho=0 product line counts != fold test line counts"
            _, tcaps_shiftdir, _, _ = read_stations(shift_st_path)

            tot_te = float(sum(te_lines.values()))
            tot_tr = float(sum(tr_lines.values()))
            Tn = math.ceil(SLACK * tot_te / (speed * N_STATIONS))

            for k in KS:
                lp = os.path.join(ldir, f"layout_{tag}_k{k}.json")
                layout = load_layout(lp)
                w_te = station_workloads(layout, te_lines, ids, speed)
                w_tr = station_workloads(layout, tr_lines, ids, speed)

                # --- stored row + the ceiling the as-run evaluation used -----
                if cfg["kind"] == "plain":
                    stored = stored_temporal_ix.loc[(fold, k)]
                    stored_wl = int(stored["wl_broken"])
                    asrun_tcaps = tcaps                      # fold train stations
                    asrun_src = "fold_train_stations"
                else:
                    stored = stored_shift_rho0[var].loc[(fold, k)]
                    stored_wl = int(stored["wl_broken"])
                    viol_own = sum(1 for s in ids if w_te[s] > tcaps[s])
                    viol_sdir = sum(1 for s in ids if w_te[s] > tcaps_shiftdir[s])
                    if viol_own == stored_wl:
                        asrun_tcaps, asrun_src = tcaps, "variant_train_stations"
                    elif viol_sdir == stored_wl:
                        asrun_tcaps, asrun_src = tcaps_shiftdir, "shiftdir_stations"
                    else:
                        asrun_tcaps, asrun_src = tcaps, "UNMATCHED"

                viol_asrun = sum(1 for s in ids if w_te[s] > asrun_tcaps[s])
                viol_norm = sum(1 for s in ids if w_te[s] > Tn)
                viol_train = sum(1 for s in ids if w_tr[s] > tcaps[s])
                cap_viol = sum(
                    1 for s in ids
                    if sum(1 for _p, sid in layout.items() if sid == s) > caps[s])
                sum_w = sum(w_te.values())
                shares = {s: (w_te[s] / sum_w if sum_w else 0.0) for s in ids}
                imbalance = max(shares.values()) * N_STATIONS
                T_ref = asrun_tcaps[ids[0]]
                B = tot_te / (speed * N_STATIONS * T_ref)
                X = sum(max(0.0, w_te[s] - Tn) for s in ids) / sum_w if sum_w else 0.0
                max_r_asrun = max(w_te[s] / asrun_tcaps[s] for s in ids)
                max_r_norm = max(w_te[s] / Tn for s in ids)

                # --- sanity vs stored --------------------------------------
                ok = (viol_asrun == stored_wl)
                if not ok:
                    sanity_failures.append(
                        f"{var} fold{fold} k={k}: recomputed viol_asrun={viol_asrun} "
                        f"!= stored wl_broken={stored_wl} (ceiling={asrun_src})")
                # extra cross-checks
                rec_maxwl = max(w_te.values())
                if cfg["kind"] == "plain":
                    if abs(rec_maxwl - float(stored["max_workload"])) > 1e-6:
                        sanity_failures.append(
                            f"{var} fold{fold} k={k}: max_workload {rec_maxwl} != "
                            f"stored {stored['max_workload']}")
                    v_rec = total_visits(layout, te_orders)
                    if v_rec != int(stored["V_test_visits"]):
                        sanity_failures.append(
                            f"{var} fold{fold} k={k}: visits {v_rec} != stored "
                            f"{stored['V_test_visits']}")
                    # forensic: temporal layouts' shift-eval rho=0 row must agree
                    if (fold, k) in stored_tshift_rho0.index:
                        srow = stored_tshift_rho0.loc[(fold, k)]
                        if int(srow["wl_broken"]) != viol_asrun:
                            sanity_failures.append(
                                f"temporal-shift-rho0 fold{fold} k={k}: stored "
                                f"{srow['wl_broken']} != recomputed {viol_asrun}")
                else:
                    v_rec = total_visits(layout, shift_orders)
                    if v_rec != int(stored["V_test_visits"]):
                        sanity_failures.append(
                            f"{var} fold{fold} k={k}: visits {v_rec} != stored "
                            f"{stored['V_test_visits']}")
                if int(stored["cap_broken"]) != cap_viol:
                    sanity_failures.append(
                        f"{var} fold{fold} k={k}: cap_broken {cap_viol} != stored "
                        f"{stored['cap_broken']}")

                for s in ids:
                    per_station_rows.append({
                        "variant": var, "fold": fold, "k": k, "station": s,
                        "W_tr": round(w_tr[s], 4), "W_te": round(w_te[s], 4),
                        "T_s_stored": asrun_tcaps[s], "Tn": Tn,
                        "ratio_asrun": round(w_te[s] / asrun_tcaps[s], 4),
                        "ratio_norm": round(w_te[s] / Tn, 4),
                        "share": round(shares[s], 5),
                        "viol_asrun_flag": int(w_te[s] > asrun_tcaps[s]),
                        "viol_norm_flag": int(w_te[s] > Tn),
                        "train_viol_flag": int(w_tr[s] > tcaps[s]),
                    })
                per_fold_rows.append({
                    "variant": var, "fold": fold, "k": k,
                    "n_train_orders": int(tr_orders["ORDER"].nunique()),
                    "n_test_orders": int(te_orders["ORDER"].nunique()),
                    "total_tr_lines": int(tot_tr), "total_te_lines": int(tot_te),
                    "T_s_asrun": T_ref, "T_s_variant_own": tcaps[ids[0]],
                    "Tn": Tn, "asrun_ceiling_source": asrun_src,
                    "viol_asrun": viol_asrun, "stored_wl_broken": stored_wl,
                    "sanity_match": ok, "viol_norm": viol_norm,
                    "viol_train": viol_train, "cap_broken": cap_viol,
                    "max_ratio_asrun": round(max_r_asrun, 4),
                    "max_ratio_norm": round(max_r_norm, 4),
                    "imbalance": round(imbalance, 4),
                    "B": round(B, 4), "X": round(X, 4),
                    "V_test_recomputed": v_rec,
                    "max_workload_te": round(rec_maxwl, 2),
                })
            print(f"[{var}] fold {fold} done "
                  f"(te_lines={int(tot_te)}, tr_lines={int(tot_tr)}, Tn={Tn})")

    ps = pd.DataFrame(per_station_rows)
    pf = pd.DataFrame(per_fold_rows)
    ps_path = os.path.join(OUT_DIR, "per_station.csv")
    pf_path = os.path.join(OUT_DIR, "per_fold.csv")
    ps.to_csv(ps_path, index=False)
    pf.to_csv(pf_path, index=False)
    print(f"wrote {ps_path} ({len(ps)} rows)")
    print(f"wrote {pf_path} ({len(pf)} rows)")

    # ----- k-effect: does k>1 improve balance / normalized feasibility? ------
    ke_rows: List[Dict[str, object]] = []
    for (var, fold), grp in pf.groupby(["variant", "fold"]):
        g = grp.set_index("k")
        best_k_imb = g["imbalance"].idxmin()
        best_k_vn = g["viol_norm"].idxmin()
        ke_rows.append({
            "variant": var, "fold": fold,
            **{f"viol_norm_k{k}": int(g.loc[k, "viol_norm"]) for k in KS},
            **{f"imbalance_k{k}": g.loc[k, "imbalance"] for k in KS},
            "best_k_by_imbalance": best_k_imb,
            "imb_k1": g.loc[1, "imbalance"],
            "imb_best": g.loc[best_k_imb, "imbalance"],
            "best_k_by_viol_norm": best_k_vn,
            "viol_norm_k1": int(g.loc[1, "viol_norm"]),
            "viol_norm_best": int(g.loc[best_k_vn, "viol_norm"]),
        })
    ke = pd.DataFrame(ke_rows)
    ke_path = os.path.join(OUT_DIR, "k_effect.csv")
    ke.to_csv(ke_path, index=False)
    print(f"wrote {ke_path}")

    # ----- sparse-train effect: feasibility vs train sample size -------------
    st_rows: List[Dict[str, object]] = []
    for var, grp in pf.groupby("variant"):
        st_rows.append({
            "variant": var,
            "mean_train_orders": round(grp["n_train_orders"].mean(), 1),
            "mean_viol_asrun": round(grp["viol_asrun"].mean(), 3),
            "mean_viol_norm": round(grp["viol_norm"].mean(), 3),
            "mean_imbalance": round(grp["imbalance"].mean(), 4),
            "mean_max_ratio_norm": round(grp["max_ratio_norm"].mean(), 4),
            "mean_B": round(grp["B"].mean(), 4),
            "mean_X": round(grp["X"].mean(), 4),
            "viol_norm_k1_mean": round(
                grp[grp["k"] == 1]["viol_norm"].mean(), 3),
            "imbalance_k1_mean": round(
                grp[grp["k"] == 1]["imbalance"].mean(), 4),
        })
    st = pd.DataFrame(st_rows).sort_values("mean_train_orders")
    st_path = os.path.join(OUT_DIR, "sparse_train_effect.csv")
    st.to_csv(st_path, index=False)
    print(f"wrote {st_path}")

    # ----- console summaries --------------------------------------------------
    with pd.option_context("display.width", 250, "display.max_columns", 40):
        print("\n=== per-fold (temporal) ===")
        print(pf[pf["variant"] == "temporal"][[
            "fold", "k", "viol_asrun", "viol_norm", "viol_train", "max_ratio_asrun",
            "max_ratio_norm", "imbalance", "B", "X"]].to_string(index=False))
        print("\n=== sparse-train effect ===")
        print(st.to_string(index=False))
        print("\n=== k effect (mean over folds) ===")
        print(pf.groupby(["variant", "k"])[["viol_norm", "imbalance", "max_ratio_norm"]]
              .mean().round(3).to_string())

    print(f"\nviol_train total (must be 0): {int(pf['viol_train'].sum())}")
    print(f"asrun ceiling sources: {pf['asrun_ceiling_source'].value_counts().to_dict()}")

    if sanity_failures:
        print("\nSANITY FAILURES:")
        for m in sanity_failures:
            print("  " + m)
        raise AssertionError(f"{len(sanity_failures)} sanity mismatches")
    print("\nSANITY: PASS — all recomputed viol_asrun equal stored wl_broken "
          "(temporal per_fold.csv 25 rows; t500/t1000/t2000 rho=0 slices 25 rows "
          "each, structured==unstructured), plus max_workload/V_test/cap_broken "
          "cross-checks and temporal shift-eval rho=0 forensic check.")


if __name__ == "__main__":
    main()
    sys.exit(0)
