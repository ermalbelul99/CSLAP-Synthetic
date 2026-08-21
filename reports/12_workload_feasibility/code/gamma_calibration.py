"""Gamma calibration study: empirical bridge from realized out-of-sample workload
overloads to a Bertsimas-Sim budget-uncertainty robust workload constraint.

Families: iscf480-temporal and iscf10kt-temporal (5 expanding temporal cuts each),
nominal layouts k=1 (primary) and k=2 (secondary).

Metric definitions (implemented exactly as specified by the study protocol):

Common workload metrics, per (fold, k, station s), layout a: p -> s
    te_lines[p] = test_orders.groupby('PRODUCT').size()   (no dup rows in ISCF)
    tr_lines[p] = train_orders.groupby('PRODUCT').size()
    W_s        = sum_{p: a[p]=s} te_lines[p] / V           (realized test workload)
    viol_asrun = #{s : W_s > T_s_stored}                   (as-run check, strict >)
    Tn         = ceil(1.10 * sum_p te_lines[p] / (V*|S|))  (volume-normalized ceiling)
    share_s    = W_s / sum_s' W_s' ;  imbalance = max_s share_s * |S|
    B          = sum_p te_lines[p] / (V * |S| * T_s)       (bindingness of as-run check)
    X          = sum_s max(0, W_s - Tn) / sum_s W_s        (excess fraction)

Gamma calibration, per fold:
    lambda   = sum(tr_lines) / sum(te_lines)
    Ln_p     = lambda * te_lines[p]        (0 for products unseen in test)
    delta_p  = Ln_p - tr_lines[p]          (tr_lines[p] = 0 if absent from train)
    Lbar_p   = tr_lines[p]

Deviation models (calibrated train-internal, i.e. with planner-available data):
    M1 proportional : Lhat_p = c1 * Lbar_p
    M2 sqrt         : Lhat_p = c2 * sqrt(Lbar_p)
    M3 empirical    : split TRAIN orders into 5 equal temporal blocks by ORDER_ID
                      rank; per block b, block lines scaled to full-train volume
                      (scale = total_train_lines / block_total_lines);
                      Lhat_p = std (ddof=1) over the 5 scaled block line counts.
    c1, c2 fitted as the smallest constants such that Lhat_p >= |delta_p| for
    q in {80, 90, 95} percent of products WEIGHTED by Lbar_p (weighted quantile
    of the ratio |delta_p| / f(Lbar_p) over products with Lbar_p > 0).
    M3 is used as-is; its Lbar-weighted coverage fraction is reported.

Per (fold, k, station), with Phi_s = {p : a[p] = s}:
    Wbar_s   = sum_{p in Phi_s} tr_lines[p] / V     (train load)
    Wn_s     = sum_{p in Phi_s} Ln_p / V            (realized normalized test load)
    Tn_equiv = ceil(1.10 * sum_p tr_lines[p] / (V*|S|))
               (normalized-unit ceiling: lambda rescales test volume to train
                volume, so the volume-normalized ceiling in normalized units is
                the train-volume fair-share ceiling)
    GammaCover(s) = min Gamma s.t. Wbar_s + (sum of Gamma largest Lhat_p among
                    Phi_s)/V >= Wn_s ;  +inf if Gamma = |Phi_s| still short.
    GammaBind(s)  = min Gamma s.t. Wbar_s + protection(Gamma)/V > T_s_stored
                    (the BS-robust constraint would already be active/violated
                    at train, forcing a different assignment); +inf if never.

Concentration, per violating station (ratio_norm > 1) under k=1:
    positive deviations d_p = max(delta_p, 0), p in Phi_s;
    cumulative share of sum d_p captured by the top-j products, j in {1,2,5,10,20};
    Gini coefficient over the strictly positive d_p.

Outputs (CSV) written to STUDY\\data\\gamma\\ :
    per_station.csv, per_fold.csv, gamma_fits.csv, gamma_station.csv,
    concentration.csv, sanity_report.csv
"""
from __future__ import annotations

import json
import math
import os
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

BASE: str = (
    r"C:\Users\Nico\PycharmProjects\CSLAP_Problem\Different_Solution_Approaches"
    r"\Full_Package_Code_With_All_Approaches\CSLAP-Synthetic\Baselines"
)
STUDY: str = r"C:\Users\Nico\PycharmProjects\CSLAP_Problem\reports\12_workload_feasibility"
OUT_DIR: str = os.path.join(STUDY, "data", "gamma")

SLACK: float = 1.10
QUANTILES: List[int] = [80, 90, 95]
Q_HEADLINE: int = 90
N_BLOCKS: int = 5
TOP_J: List[int] = [1, 2, 5, 10, 20]

FAMILIES: Dict[str, Dict[str, object]] = {
    "iscf480-temporal": {
        "folds_dir": os.path.join(BASE, "iscf_folds_temporal"),
        "layouts_dir": os.path.join(BASE, "iscf_layouts_temporal"),
        "results_per_fold": os.path.join(BASE, "iscf_results_temporal", "per_fold.csv"),
        "prefix": "iscf480",
        "k_values": [1, 2],
    },
    "iscf10kt-temporal": {
        "folds_dir": os.path.join(BASE, "iscf10kt_folds_temporal"),
        "layouts_dir": os.path.join(BASE, "iscf10kt_layouts_temporal"),
        "results_per_fold": os.path.join(BASE, "iscf10kt_results_temporal", "per_fold.csv"),
        "prefix": "iscf10kt",
        "k_values": [1, 2],
    },
}
FOLDS: List[str] = [f"r0f{i}" for i in range(5)]


def read_orders(path: str) -> pd.DataFrame:
    """Read a semicolon-separated fold orders CSV (ORDER;PRODUCT;QTY;STATION)."""
    return pd.read_csv(path, sep=";")


def lines_per_product(orders: pd.DataFrame) -> pd.Series:
    """Per-product line counts = groupby('PRODUCT').size().

    ISCF fold orders have zero duplicate (ORDER, PRODUCT) rows, so this equals
    the distinct-order count per product (the as-run evaluator's te_lines).
    """
    return orders.groupby("PRODUCT").size().astype(float)


def read_stations(path: str) -> pd.DataFrame:
    """Read a stations CSV; index STATION_ID, columns CAPACITY/TIME_CAPACITY/SPEED."""
    df = pd.read_csv(path, sep=";")
    return df.set_index("STATION_ID")


def load_layout(path: str) -> Dict[str, str]:
    """Load a flat {'PROD_<id>': 'GARE<n>'} layout JSON."""
    with open(path, "r", encoding="utf-8") as fh:
        layout = json.load(fh)
    if "assignment" in layout and isinstance(layout["assignment"], dict):
        layout = layout["assignment"]
    return {str(p): str(s) for p, s in layout.items()}


def weighted_cover_quantile(ratios: np.ndarray, weights: np.ndarray, q: float) -> float:
    """Smallest c such that ratios <= c holds for >= q% of the total weight.

    Sorts ratios ascending and returns the first value whose cumulative weight
    reaches q/100 of the total weight.
    """
    order = np.argsort(ratios)
    r_sorted = ratios[order]
    w_sorted = weights[order]
    cumw = np.cumsum(w_sorted)
    target = (q / 100.0) * cumw[-1]
    idx = int(np.searchsorted(cumw, target, side="left"))
    idx = min(idx, len(r_sorted) - 1)
    return float(r_sorted[idx])


def m3_empirical_lhat(train_orders: pd.DataFrame, products: pd.Index) -> pd.Series:
    """M3 deviation scale: std over 5 volume-rescaled temporal train blocks.

    Splits distinct ORDER ids by ascending ORDER_ID rank into 5 equal blocks,
    computes per-block per-product line counts, rescales each block's counts to
    full-train volume, and returns the ddof=1 std across blocks (0 for products
    never seen in train).
    """
    ids = np.sort(train_orders["ORDER"].unique())
    blocks = np.array_split(ids, N_BLOCKS)
    total_lines = float(len(train_orders))
    mat = pd.DataFrame(0.0, index=products, columns=range(N_BLOCKS))
    order_to_block = pd.Series(
        np.concatenate([np.full(len(b), i) for i, b in enumerate(blocks)]),
        index=np.concatenate(blocks),
    )
    blk = train_orders["ORDER"].map(order_to_block)
    grouped = train_orders.groupby([blk, train_orders["PRODUCT"]]).size()
    for b in range(N_BLOCKS):
        if b in grouped.index.get_level_values(0):
            cnt = grouped.loc[b]
            scale = total_lines / float(cnt.sum())
            mat.loc[cnt.index.intersection(products), b] = (
                cnt.reindex(mat.index).fillna(0.0) * scale
            )
    return mat.std(axis=1, ddof=1)


def min_gamma(
    wbar: float, target: float, lhat_desc_cumsum: np.ndarray, speed: float, strict: bool
) -> float:
    """Min Gamma s.t. wbar + cumsum[Gamma]/speed >= target (or > if strict).

    lhat_desc_cumsum[j] = sum of the (j+1) largest Lhat values; Gamma=0 means no
    protection. Returns math.inf when even the full budget falls short.
    """

    def ok(prot: float) -> bool:
        lhs = wbar + prot / speed
        return lhs > target if strict else lhs >= target - 1e-9

    if ok(0.0):
        return 0.0
    for j, prot in enumerate(lhat_desc_cumsum):
        if ok(float(prot)):
            return float(j + 1)
    return math.inf


def gini(values: np.ndarray) -> float:
    """Gini coefficient of a non-negative sample (NaN when empty or all zero)."""
    x = np.sort(values.astype(float))
    n = len(x)
    if n == 0 or x.sum() <= 0:
        return float("nan")
    i = np.arange(1, n + 1)
    return float((2.0 * np.sum(i * x) - (n + 1) * np.sum(x)) / (n * np.sum(x)))


def main() -> None:
    """Run the full gamma-calibration study and write all output CSVs."""
    os.makedirs(OUT_DIR, exist_ok=True)

    per_station_rows: List[dict] = []
    per_fold_rows: List[dict] = []
    fit_rows: List[dict] = []
    gamma_rows: List[dict] = []
    conc_rows: List[dict] = []
    sanity_rows: List[dict] = []
    sanity_all_ok = True

    for fam_name, fam in FAMILIES.items():
        stored = pd.read_csv(str(fam["results_per_fold"]))
        stored = stored.set_index(["fold", "k"])
        prefix = str(fam["prefix"])
        folds_dir = str(fam["folds_dir"])
        layouts_dir = str(fam["layouts_dir"])
        k_values = list(fam["k_values"])  # type: ignore[arg-type]

        for fi, fold in enumerate(FOLDS):
            tag = f"{prefix}_{fold}"
            print(f"[{fam_name}] fold {fold} ...", flush=True)
            tr_orders = read_orders(os.path.join(folds_dir, f"{tag}_train_orders.csv"))
            te_orders = read_orders(os.path.join(folds_dir, f"{tag}_test_orders.csv"))
            stations = read_stations(os.path.join(folds_dir, f"{tag}_train_stations.csv"))
            speed = float(stations["SPEED"].iloc[0])
            n_stations = len(stations)
            t_stored = stations["TIME_CAPACITY"].astype(float)  # per-station stored T_s

            tr_lines = lines_per_product(tr_orders)
            te_lines = lines_per_product(te_orders)
            tot_tr = float(tr_lines.sum())
            tot_te = float(te_lines.sum())
            lam = tot_tr / tot_te

            products = tr_lines.index.union(te_lines.index)
            lbar = tr_lines.reindex(products).fillna(0.0)
            ln = (lam * te_lines).reindex(products).fillna(0.0)
            delta = ln - lbar
            abs_delta = delta.abs()

            # ---- model fits (train-weighted quantiles) ----
            pos_mask = lbar.values > 0
            w = lbar.values[pos_mask]
            r1 = abs_delta.values[pos_mask] / lbar.values[pos_mask]
            r2 = abs_delta.values[pos_mask] / np.sqrt(lbar.values[pos_mask])
            lhat_m3 = m3_empirical_lhat(tr_orders, products)
            c1: Dict[int, float] = {}
            c2: Dict[int, float] = {}
            for q in QUANTILES:
                c1[q] = weighted_cover_quantile(r1, w, q)
                c2[q] = weighted_cover_quantile(r2, w, q)
                fit_rows.append(
                    dict(family=fam_name, fold=fold, model="M1_prop", q=q, c=c1[q],
                         coverage_weighted=q / 100.0)
                )
                fit_rows.append(
                    dict(family=fam_name, fold=fold, model="M2_sqrt", q=q, c=c2[q],
                         coverage_weighted=q / 100.0)
                )
            m3_cov = float(
                np.sum(w * (lhat_m3.values[pos_mask] >= abs_delta.values[pos_mask] - 1e-9))
                / np.sum(w)
            )
            fit_rows.append(
                dict(family=fam_name, fold=fold, model="M3_empirical", q=np.nan,
                     c=1.0, coverage_weighted=m3_cov)
            )

            lhat_models: Dict[str, pd.Series] = {
                "M1_prop": c1[Q_HEADLINE] * lbar,
                "M2_sqrt": c2[Q_HEADLINE] * np.sqrt(lbar),
                "M3_empirical": lhat_m3,
            }

            tn = math.ceil(SLACK * tot_te / (speed * n_stations))
            tn_equiv = math.ceil(SLACK * tot_tr / (speed * n_stations))

            for k in k_values:
                layout_path = os.path.join(layouts_dir, f"layout_{tag}_k{k}.json")
                layout = load_layout(layout_path)
                assign = pd.Series(layout)
                assign = assign[assign.index.isin(products) | True]  # keep all keys

                # station aggregates (products absent from an orders file count 0)
                w_te = te_lines.reindex(assign.index).fillna(0.0).groupby(assign).sum() / speed
                w_tr = tr_lines.reindex(assign.index).fillna(0.0).groupby(assign).sum() / speed
                wn = ln.reindex(assign.index).fillna(0.0).groupby(assign).sum() / speed
                wbar = lbar.reindex(assign.index).fillna(0.0).groupby(assign).sum() / speed
                w_te = w_te.reindex(stations.index).fillna(0.0)
                w_tr = w_tr.reindex(stations.index).fillna(0.0)
                wn = wn.reindex(stations.index).fillna(0.0)
                wbar = wbar.reindex(stations.index).fillna(0.0)
                phi_count = assign.groupby(assign).size().reindex(stations.index).fillna(0).astype(int)

                ratio_asrun = w_te / t_stored
                ratio_norm = w_te / tn
                ratio_norm_equiv = wn / tn_equiv
                share = w_te / w_te.sum()
                viol_asrun = int((w_te > t_stored).sum())
                viol_norm = int((w_te > tn).sum())
                viol_norm_equiv = int((wn > tn_equiv).sum())
                train_viol = int((w_tr > t_stored).sum())
                imbalance = float(share.max() * n_stations)
                bindingness = tot_te / (speed * n_stations * float(t_stored.iloc[0]))
                excess = float(np.maximum(w_te - tn, 0.0).sum() / w_te.sum())

                # ---- sanity 1: as-run violations must equal stored wl_broken ----
                stored_wl = int(stored.loc[(fi, k), "wl_broken"])
                s1_ok = viol_asrun == stored_wl
                # ---- sanity 2: train feasibility (Hexaly hard constraint) ----
                s2_ok = train_viol == 0
                # ---- sanity 3: normalized-unit violations match ratio_norm > 1 ----
                set_norm = set(stations.index[(w_te > tn)])
                set_norm_eq = set(stations.index[(wn > tn_equiv)])
                s3_ok = set_norm == set_norm_eq
                sanity_all_ok &= s1_ok and s2_ok and s3_ok
                sanity_rows.append(
                    dict(family=fam_name, fold=fold, k=k,
                         viol_asrun=viol_asrun, stored_wl_broken=stored_wl,
                         asrun_matches_stored=s1_ok,
                         train_viol=train_viol, train_feasible=s2_ok,
                         viol_norm=viol_norm, viol_norm_equiv=viol_norm_equiv,
                         norm_sets_match=s3_ok,
                         norm_mismatch_stations=";".join(sorted(set_norm ^ set_norm_eq)))
                )

                for s in stations.index:
                    per_station_rows.append(
                        dict(family=fam_name, fold=fold, k=k, station=s,
                             n_products=int(phi_count[s]),
                             W_tr=float(w_tr[s]), W_te=float(w_te[s]),
                             T_s_stored=float(t_stored[s]), Tn=tn,
                             Wbar=float(wbar[s]), Wn=float(wn[s]), Tn_equiv=tn_equiv,
                             ratio_asrun=float(ratio_asrun[s]),
                             ratio_norm=float(ratio_norm[s]),
                             ratio_norm_equiv=float(ratio_norm_equiv[s]),
                             share=float(share[s]),
                             viol_asrun_flag=bool(w_te[s] > t_stored[s]),
                             viol_norm_flag=bool(w_te[s] > tn),
                             train_ok=bool(w_tr[s] <= t_stored[s]))
                    )

                per_fold_rows.append(
                    dict(family=fam_name, fold=fold, k=k,
                         viol_asrun=viol_asrun, stored_wl_broken=stored_wl,
                         viol_norm=viol_norm,
                         max_ratio_asrun=float(ratio_asrun.max()),
                         max_ratio_norm=float(ratio_norm.max()),
                         imbalance=imbalance, B=bindingness, X=excess,
                         tot_te_lines=tot_te, tot_tr_lines=tot_tr,
                         lam=lam, Tn=tn, Tn_equiv=tn_equiv,
                         T_s_stored=float(t_stored.iloc[0]),
                         train_viol=train_viol)
                )

                # ---- Gamma per station and model ----
                for model, lhat in lhat_models.items():
                    for s in stations.index:
                        phi = assign.index[assign.values == s]
                        lh = np.sort(lhat.reindex(phi).fillna(0.0).values)[::-1]
                        cs = np.cumsum(lh)
                        g_cover = min_gamma(float(wbar[s]), float(wn[s]), cs, speed, strict=False)
                        g_bind = min_gamma(float(wbar[s]), float(t_stored[s]), cs, speed, strict=True)
                        n_phi = len(phi)
                        gamma_rows.append(
                            dict(family=fam_name, fold=fold, k=k, station=s, model=model,
                                 n_products=n_phi,
                                 GammaCover=g_cover,
                                 GammaCover_frac=(g_cover / n_phi if n_phi and math.isfinite(g_cover) else math.inf),
                                 GammaBind=g_bind,
                                 GammaBind_frac=(g_bind / n_phi if n_phi and math.isfinite(g_bind) else math.inf),
                                 Wbar=float(wbar[s]), Wn=float(wn[s]),
                                 T_s_stored=float(t_stored[s]),
                                 viol_asrun_flag=bool(w_te[s] > t_stored[s]),
                                 viol_norm_flag=bool(w_te[s] > tn))
                        )

                # ---- concentration on violating stations (ratio_norm>1, k=1) ----
                if k == 1:
                    for s in stations.index:
                        if not (w_te[s] > tn):
                            continue
                        phi = assign.index[assign.values == s]
                        d = np.maximum(delta.reindex(phi).fillna(0.0).values, 0.0)
                        d_sorted = np.sort(d)[::-1]
                        tot_pos = float(d_sorted.sum())
                        row = dict(family=fam_name, fold=fold, k=k, station=s,
                                   n_products=len(phi),
                                   n_pos=int((d_sorted > 0).sum()),
                                   total_pos_dev=tot_pos,
                                   gini_pos=gini(d_sorted[d_sorted > 0]))
                        for j in TOP_J:
                            row[f"top{j}_share"] = (
                                float(d_sorted[:j].sum() / tot_pos) if tot_pos > 0 else float("nan")
                            )
                        conc_rows.append(row)

    per_station = pd.DataFrame(per_station_rows)
    per_fold = pd.DataFrame(per_fold_rows)
    fits = pd.DataFrame(fit_rows)
    gammas = pd.DataFrame(gamma_rows)
    conc = pd.DataFrame(conc_rows)
    sanity = pd.DataFrame(sanity_rows)

    per_station.to_csv(os.path.join(OUT_DIR, "per_station.csv"), index=False)
    per_fold.to_csv(os.path.join(OUT_DIR, "per_fold.csv"), index=False)
    fits.to_csv(os.path.join(OUT_DIR, "gamma_fits.csv"), index=False)
    gammas.to_csv(os.path.join(OUT_DIR, "gamma_station.csv"), index=False)
    conc.to_csv(os.path.join(OUT_DIR, "concentration.csv"), index=False)
    sanity.to_csv(os.path.join(OUT_DIR, "sanity_report.csv"), index=False)

    print("\n===== SANITY =====")
    print(sanity.to_string(index=False))
    if not bool(sanity["asrun_matches_stored"].all()):
        bad = sanity[~sanity["asrun_matches_stored"]]
        raise AssertionError(f"as-run violations != stored wl_broken:\n{bad}")
    if not bool(sanity["train_feasible"].all()):
        print("WARNING: train-side workload constraint violated somewhere (unexpected).")
    print(f"ALL SANITY OK: {bool(sanity_all_ok)}")

    # ---- headline digests ----
    print("\n===== PER-FOLD SUMMARY =====")
    cols = ["family", "fold", "k", "viol_asrun", "viol_norm", "max_ratio_asrun",
            "max_ratio_norm", "imbalance", "B", "X", "lam"]
    print(per_fold[cols].to_string(index=False))

    print("\n===== FITS (median across folds) =====")
    med = fits.groupby(["family", "model", "q"], dropna=False)[["c", "coverage_weighted"]].median()
    print(med.to_string())

    print("\n===== GammaCover on as-run violating stations (k=1) =====")
    gv = gammas[(gammas["k"] == 1) & gammas["viol_asrun_flag"]]
    if len(gv):
        print(gv.groupby(["family", "model"])[["GammaCover", "GammaCover_frac"]]
              .agg(["median", "mean", "max"]).to_string())
        print(gv[["family", "fold", "station", "model", "GammaCover", "GammaCover_frac"]]
              .to_string(index=False))

    print("\n===== GammaBind (k=1, min / median across stations per family+model) =====")
    gb = gammas[gammas["k"] == 1].copy()
    print(gb.groupby(["family", "model"])[["GammaBind", "GammaBind_frac"]]
          .agg(["min", "median"]).to_string())

    print("\n===== CONCENTRATION (violating stations, k=1) =====")
    if len(conc):
        print(conc.to_string(index=False))
    print("\nDone. Outputs in", OUT_DIR)


if __name__ == "__main__":
    main()
