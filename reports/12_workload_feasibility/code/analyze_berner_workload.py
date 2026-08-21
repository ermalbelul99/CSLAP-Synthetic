r"""BERNER workload-feasibility audit + bindingness quantification (CSV-only).

FAMILY = BERNER (industrial, 24 heterogeneous stations, 2,000 top-train SKUs).
No layouts were persisted by any BERNER script (grep-verified in the code audit),
so realized per-station test workloads W_s cannot be recomputed. Instead:

(a) Tabulate every wl/cap feasibility column of the three as-run result CSVs
    (``berner_decompose_result.csv``, ``berner_decompose_cprime_result.csv``,
    ``berner_clean_comparison_result.csv``) into one audit table, annotating each
    arm with its capacity semantics (real vs recalibrated ceiling handed to the
    Hexaly placement) and deployability status w.r.t. the REAL per-station
    contract, per the authoritative code-audit inventory.

(b) Quantify how *binding* the workload checks could have been, from the
    ``berner_topn`` instance files alone. Per station s (|S| = 24):

    - stored ceiling  T_s = ceil(1.20 * W^{pin,tr}_s)  where
      W^{pin,tr}_s = sum_{p: a0(p)=s} REAL_LINES_p / V_s  (berner_adapter.py:110-114),
      a0 = PINNED_STATION (latest-train-order station);
    - identity (pinned) assignment test workload
      W^{pin,te}_s = sum_{p: a0(p)=s} te_lines[p] / V_s  with
      te_lines = test_orders.groupby('PRODUCT').size()  (raw lines, duplicates
      counted -- the exact as-run test-demand semantics, berner_decompose.py:127);
    - train-frequency-proportional split: station s receives test lines
      proportional to its pinned TRAIN line share,
      W^{tfp,te}_s = L_te * (l^{tr}_s / L_tr^{pin}) / V_s;
    - lines-equal fair share  fair_te_s = L_te / (V_s * |S|)  and the
      bindingness ratio  B_s = fair_te_s / T_s  (the stated study formula);
    - fluid perfectly-balanced workload  W* = L_te / sum_s V_s  (equal-workload
      split, the minimal achievable makespan in the fluid relaxation) and
      ratio_pb_s = W* / T_s;
    plus the aggregate volume-feasibility index
      B_agg = L / sum_s (V_s * T_s)   for L in {train, test} line totals
    (> 1 would mean NO assignment can satisfy all ceilings, even fractionally).

Sanity: the audit table is re-read and compared cell-by-cell against the three
source CSVs; the report-11 quote (Cprime/Dprime real_wl_broken in 6..9 of 24,
max ratio up to ~5.5x) is verified against the cprime CSV; the products-file
REAL_LINES column is verified to equal the recomputed distinct-train-order
counts.

Outputs (semicolon-free, comma CSV):
    STUDY/data/berner/berner_feasibility_audit.csv
    STUDY/data/berner/berner_bindingness.csv
"""

from __future__ import annotations

import math
import os
import sys
from typing import Dict, Tuple

import numpy as np
import pandas as pd

BASE = (r"C:\Users\Nico\PycharmProjects\CSLAP_Problem\Different_Solution_Approaches"
        r"\Full_Package_Code_With_All_Approaches\CSLAP-Synthetic\Baselines")
TOPN = os.path.join(BASE, "berner_topn")
STUDY = r"C:\Users\Nico\PycharmProjects\CSLAP_Problem\reports\12_workload_feasibility"
OUT_DIR = os.path.join(STUDY, "data", "berner")

SRC_DECOMPOSE = os.path.join(BASE, "berner_decompose_result.csv")
SRC_CPRIME = os.path.join(BASE, "berner_decompose_cprime_result.csv")
SRC_CLEAN = os.path.join(BASE, "berner_clean_comparison_result.csv")

# ---------------------------------------------------------------------------
# Arm semantics (from the authoritative code-audit inventory).
# ---------------------------------------------------------------------------
DECOMPOSE_SEM: Dict[str, Tuple[str, str]] = {
    # arm -> (capacity_semantics, deployability)
    "A_baseline": (
        "REAL per-station heterogeneous T_s enforced HARD by Hexaly on train "
        "REAL_LINES (kappa-invariant).",
        "DEPLOYABLE by construction (placed under the real contract)."),
    "B_preproc": (
        "REAL per-station T_s enforced HARD; only the ORDERS are enlarged to "
        "closures (preprocess-only arm).",
        "DEPLOYABLE by construction (placed under the real contract)."),
    "C_v2full": (
        "RECALIBRATED flat loose T_s (eq.10 average from closure line counts) "
        "handed to Hexaly; workload SIGNAL still real REAL_LINES.",
        "NOT guaranteed deployable (placed under a loosened contract); "
        "as-run recheck vs real stations happened to pass on test demand."),
    "D_caponly": (
        "RECALIBRATED flat loose T_s (eq.10) with NOMINAL orders "
        "(capacity-only control); workload SIGNAL real REAL_LINES.",
        "NOT guaranteed deployable (placed under a loosened contract); "
        "as-run recheck vs real stations happened to pass on test demand."),
}
DECOMPOSE_CHECK = (
    "wl_broken/cap_broken recomputed for EVERY arm against the REAL train "
    "stations with TEST demand = te.groupby('PRODUCT').size() (raw order-lines, "
    "duplicates counted; berner_decompose.py:127,139-140,178-179). Test window "
    "is ~3 weeks vs the 10-week train calibration of T_s, so this check is "
    "volume-slack (see bindingness B_agg).")

CPRIME_SEM: Dict[str, Tuple[str, str]] = {
    "Cprime_closures": (
        "Closure objective + INFLATED bar_L workload signal + loose flat recal "
        "cap (berner_decompose_cprime.py:121-122); placement never saw the real "
        "per-station contract.",
        "NOT DEPLOYABLE: real_wl_broken stations under the TRAIN-demand real "
        "contract (real_feasibility(), :49-64)."),
    "Dprime_nominal": (
        "Nominal objective + INFLATED bar_L workload signal + loose flat recal "
        "cap; placement never saw the real per-station contract.",
        "NOT DEPLOYABLE: real_wl_broken stations under the TRAIN-demand real "
        "contract."),
}
CPRIME_CHECK = (
    "real_cap_broken/real_wl_broken/real_wl_max_ratio from real_feasibility() "
    "(berner_decompose_cprime.py:49-64,137): layout vs REAL per-product "
    "REAL_LINES (= TRAIN distinct-order demand) and REAL per-station T_s -- a "
    "TRAIN-demand deployability check, NOT a test-workload check. N/V vs real "
    "stations as in decompose.")

CLEAN_SEM: Dict[str, Tuple[str, str]] = {
    "A_baseline": (
        "REAL regime: per-station heterogeneous T_s (120% slack) enforced HARD.",
        "DEPLOYABLE by construction; TRAIN-demand real check confirms 0 broken."),
    "B_closures": (
        "REAL regime: per-station T_s enforced HARD, closure orders.",
        "DEPLOYABLE by construction; TRAIN-demand real check confirms 0 broken "
        "(max ratio ~1.0 => the real ceiling is BINDING at placement)."),
    "Cpp_closures": (
        "FAIR-INFLATED regime: per-station T_s^fair = ceil(1.20 * "
        "sum_{p:a0(p)=s} bar_L_p / V_s) built from PINNED_STATION a0 with "
        "closure line counts bar_L (berner_clean_comparison.py).",
        "NOT DEPLOYABLE when real_wl_broken > 0 (TRAIN-demand real check)."),
    "Dpp_nominal": (
        "FAIR-INFLATED regime: same per-station T_s^fair, nominal orders.",
        "NOT DEPLOYABLE when real_wl_broken > 0 (TRAIN-demand real check)."),
    "oldD_slack": (
        "LOOSE reference: flat eq.10 recalibrated cap (the old D arm).",
        "NOT DEPLOYABLE when real_wl_broken > 0 (TRAIN-demand real check)."),
}
CLEAN_CHECK = (
    "real_cap_broken/real_wl_broken/real_wl_max_ratio: every arm re-checked for "
    "REAL feasibility (TRAIN-demand REAL_LINES vs the REAL per-station T_s), "
    "same semantics as the cprime real_feasibility check.")


def load_semicolon(path: str) -> pd.DataFrame:
    """Read one of the berner_topn instance CSVs (semicolon-separated)."""
    return pd.read_csv(path, sep=";")


def build_feasibility_audit() -> pd.DataFrame:
    """Deliverable (a): unified feasibility table across the three result CSVs."""
    rows = []
    dec = pd.read_csv(SRC_DECOMPOSE)
    for _, r in dec.iterrows():
        cap_sem, deploy = DECOMPOSE_SEM[r["arm"]]
        rows.append({
            "source_csv": "berner_decompose_result.csv",
            "k": int(r["k"]), "arm": r["arm"], "regime": "",
            "orders": r["orders"], "capacity": r["capacity"],
            "N": int(r["N"]), "V": int(r["V"]),
            "PoR_pct": float(r["PoR_pct"]), "G_pct": float(r["G_pct"]),
            "cap_broken": int(r["cap_broken"]), "wl_broken": int(r["wl_broken"]),
            "real_cap_broken": np.nan, "real_wl_broken": np.nan,
            "real_wl_max_ratio": np.nan,
            "c_bar": float(r["c_bar"]),
            "feasibility_check_semantics": DECOMPOSE_CHECK,
            "capacity_semantics": cap_sem, "deployability": deploy,
        })
    cpr = pd.read_csv(SRC_CPRIME)
    for _, r in cpr.iterrows():
        cap_sem, deploy = CPRIME_SEM[r["arm"]]
        rows.append({
            "source_csv": "berner_decompose_cprime_result.csv",
            "k": int(r["k"]), "arm": r["arm"], "regime": "",
            "orders": "closures" if "closures" in r["arm"] else "nominal",
            "capacity": "recal-loose (bar_L signal)",
            "N": int(r["N"]), "V": int(r["V"]),
            "PoR_pct": float(r["PoR_pct"]), "G_pct": float(r["G_pct"]),
            "cap_broken": np.nan, "wl_broken": np.nan,
            "real_cap_broken": int(r["real_cap_broken"]),
            "real_wl_broken": int(r["real_wl_broken"]),
            "real_wl_max_ratio": float(r["real_wl_max_ratio"]),
            "c_bar": float(r["c_bar"]),
            "feasibility_check_semantics": CPRIME_CHECK,
            "capacity_semantics": cap_sem, "deployability": deploy,
        })
    cln = pd.read_csv(SRC_CLEAN)
    for _, r in cln.iterrows():
        cap_sem, deploy = CLEAN_SEM[r["arm"]]
        rows.append({
            "source_csv": "berner_clean_comparison_result.csv",
            "k": int(r["k"]), "arm": r["arm"], "regime": r["regime"],
            "orders": "closures" if "closures" in r["arm"] else "nominal",
            "capacity": r["regime"],
            "N": int(r["N"]), "V": int(r["V"]),
            "PoR_pct": float(r["PoR_pct"]), "G_pct": float(r["G_pct"]),
            "cap_broken": np.nan, "wl_broken": np.nan,
            "real_cap_broken": int(r["real_cap_broken"]),
            "real_wl_broken": int(r["real_wl_broken"]),
            "real_wl_max_ratio": float(r["real_wl_max_ratio"]),
            "c_bar": float(r["c_bar"]),
            "feasibility_check_semantics": CLEAN_CHECK,
            "capacity_semantics": cap_sem, "deployability": deploy,
        })
    return pd.DataFrame(rows)


def sanity_audit(audit: pd.DataFrame) -> list[str]:
    """Cell-by-cell comparison of the audit table against the source CSVs."""
    msgs: list[str] = []
    dec = pd.read_csv(SRC_DECOMPOSE)
    cpr = pd.read_csv(SRC_CPRIME)
    cln = pd.read_csv(SRC_CLEAN)

    a_dec = audit[audit.source_csv == "berner_decompose_result.csv"].reset_index(drop=True)
    for col in ["k", "arm", "orders", "capacity", "N", "V", "PoR_pct", "G_pct",
                "cap_broken", "wl_broken", "c_bar"]:
        src = dec[col].tolist()
        tab = a_dec[col].tolist()
        ok = all((s == t) or (float(s) == float(t)) for s, t in zip(src, tab))
        if not ok or len(src) != len(tab):
            msgs.append(f"MISMATCH decompose col {col}: src={src} tab={tab}")

    a_cpr = audit[audit.source_csv == "berner_decompose_cprime_result.csv"].reset_index(drop=True)
    for col in ["k", "arm", "N", "V", "PoR_pct", "G_pct", "real_cap_broken",
                "real_wl_broken", "real_wl_max_ratio", "c_bar"]:
        src = cpr[col].tolist()
        tab = a_cpr[col].tolist()
        ok = all((s == t) or (float(s) == float(t)) for s, t in zip(src, tab))
        if not ok or len(src) != len(tab):
            msgs.append(f"MISMATCH cprime col {col}: src={src} tab={tab}")

    a_cln = audit[audit.source_csv == "berner_clean_comparison_result.csv"].reset_index(drop=True)
    for col in ["k", "arm", "regime", "N", "V", "PoR_pct", "G_pct",
                "real_cap_broken", "real_wl_broken", "real_wl_max_ratio", "c_bar"]:
        src = cln[col].tolist()
        tab = a_cln[col].tolist()
        ok = all((s == t) or (float(s) == float(t)) for s, t in zip(src, tab))
        if not ok or len(src) != len(tab):
            msgs.append(f"MISMATCH clean col {col}: src={src} tab={tab}")

    # Report-11 quote verification on the cprime CSV.
    lo, hi = int(cpr.real_wl_broken.min()), int(cpr.real_wl_broken.max())
    cmax = float(cpr.loc[cpr.arm == "Cprime_closures", "real_wl_max_ratio"].max())
    dmax = float(cpr.loc[cpr.arm == "Dprime_nominal", "real_wl_max_ratio"].max())
    if not (lo == 6 and hi == 9):
        msgs.append(f"MISMATCH report-11 quote: real_wl_broken range = [{lo},{hi}], expected [6,9]")
    if abs(cmax - 5.488) > 1e-9:
        msgs.append(f"MISMATCH report-11 quote: Cprime max ratio = {cmax}, expected 5.488")
    print(f"[quote-check] cprime real_wl_broken range = [{lo},{hi}] (report 11: 6-9 of 24)  "
          f"Cprime max ratio = {cmax} (report 11: ~5.5x)  Dprime max ratio = {dmax}")
    return msgs


def build_bindingness() -> Tuple[pd.DataFrame, Dict[str, float], list[str]]:
    """Deliverable (b): per-station bindingness bounds from the instance files."""
    msgs: list[str] = []
    stations = load_semicolon(os.path.join(TOPN, "bern_train_stations.csv"))
    products = load_semicolon(os.path.join(TOPN, "bern_train_products.csv"))
    tr = load_semicolon(os.path.join(TOPN, "bern_train_orders.csv"))
    te = load_semicolon(os.path.join(TOPN, "bern_test_orders.csv"))
    n_stations = len(stations)
    print(f"[load] stations={n_stations}  products={len(products)}  "
          f"train rows={len(tr):,}  test rows={len(te):,}")

    # As-run demand semantics: raw line counts (duplicates counted) via groupby size.
    tr_raw = tr.groupby("PRODUCT").size()
    te_raw = te.groupby("PRODUCT").size()
    # Distinct-order counts (REAL_LINES semantics) for cross-check / reference.
    tr_distinct = tr.groupby("PRODUCT")["ORDER"].nunique()
    te_distinct = te.groupby("PRODUCT")["ORDER"].nunique()

    prod_tok = "PROD_" + products["PRODUCT_ID"].astype(str)
    real_lines = pd.Series(products["REAL_LINES"].values, index=prod_tok)
    pinned = pd.Series(products["PINNED_STATION"].values, index=prod_tok)

    # REAL_LINES must equal recomputed distinct-train-order counts.
    rec = tr_distinct.reindex(real_lines.index).fillna(0).astype(int)
    n_bad = int((rec != real_lines).sum())
    if n_bad:
        msgs.append(f"MISMATCH REAL_LINES vs recomputed distinct train lines on {n_bad} products")
    print(f"[check] REAL_LINES == recomputed distinct train lines for all "
          f"{len(real_lines)} products: {n_bad == 0}")

    L_tr_raw, L_te_raw = int(tr_raw.sum()), int(te_raw.sum())
    L_tr_dis, L_te_dis = int(tr_distinct.sum()), int(te_distinct.sum())
    L_tr_real = int(real_lines.sum())
    print(f"[totals] train raw={L_tr_raw:,} distinct={L_tr_dis:,} REAL_LINES sum={L_tr_real:,} | "
          f"test raw={L_te_raw:,} distinct={L_te_dis:,}")

    rows = []
    for _, st in stations.iterrows():
        s = int(st.STATION_ID)
        V = float(st.SPEED)
        T = float(st.TIME_CAPACITY)
        mask = pinned == s
        prods_s = real_lines.index[mask]
        # Train pinned workload (REAL_LINES / V) -- the calibration base of T_s.
        w_tr_pin = float(real_lines[mask].sum()) / V
        # Identity (pinned) assignment on TEST demand, as-run raw-line semantics.
        w_te_pin = float(te_raw.reindex(prods_s).fillna(0).sum()) / V
        w_te_pin_dis = float(te_distinct.reindex(prods_s).fillna(0).sum()) / V
        # Train-frequency-proportional split of total test lines.
        share_tr = float(real_lines[mask].sum()) / L_tr_real
        w_te_tfp = L_te_raw * share_tr / V
        # Lines-equal fair shares and the stated B formula.
        fair_tr = L_tr_real / (V * n_stations)
        fair_te = L_te_raw / (V * n_stations)
        rows.append({
            "station": s, "capacity_slots": int(st.CAPACITY),
            "T_s_stored": int(st.TIME_CAPACITY), "speed": V,
            "n_pinned": int(mask.sum()),
            "W_tr_pinned": round(w_tr_pin, 3),
            "ratio_tr_pinned": round(w_tr_pin / T, 4),
            "W_te_pinned": round(w_te_pin, 3),
            "ratio_te_pinned": round(w_te_pin / T, 4),
            "viol_te_pinned": int(w_te_pin > T),
            "W_te_pinned_distinct": round(w_te_pin_dis, 3),
            "ratio_te_pinned_distinct": round(w_te_pin_dis / T, 4),
            "train_share_pinned": round(share_tr, 5),
            "W_te_trainprop": round(w_te_tfp, 3),
            "ratio_te_trainprop": round(w_te_tfp / T, 4),
            "fair_share_tr_lines": round(fair_tr, 3),
            "fair_share_te_lines": round(fair_te, 3),
            "B_tr": round(fair_tr / T, 4),
            "B_te": round(fair_te / T, 4),
        })
    bind = pd.DataFrame(rows)

    # Fluid perfectly-balanced workload (equal-workload split of test lines).
    sumV = float(stations.SPEED.sum())
    w_star_te = L_te_raw / sumV
    w_star_tr = L_tr_real / sumV
    bind["W_star_te_fluid"] = round(w_star_te, 3)
    bind["ratio_pb_fluid"] = (w_star_te / bind["T_s_stored"]).round(4)

    # Aggregate volume-feasibility indices.
    cap_volume = float((stations.SPEED * stations.TIME_CAPACITY).sum())
    agg = {
        "n_stations": n_stations,
        "L_tr_raw": L_tr_raw, "L_tr_distinct": L_tr_dis, "L_tr_REAL_LINES": L_tr_real,
        "L_te_raw": L_te_raw, "L_te_distinct": L_te_dis,
        "sum_Vs_Ts_lines_capacity": cap_volume,
        "B_agg_train": L_tr_real / cap_volume,
        "B_agg_test": L_te_raw / cap_volume,
        "test_to_train_volume_ratio": L_te_raw / L_tr_real,
        "n_viol_te_pinned": int(bind.viol_te_pinned.sum()),
        "max_ratio_te_pinned": float(bind.ratio_te_pinned.max()),
        "max_ratio_tr_pinned": float(bind.ratio_tr_pinned.max()),
        "max_B_te": float(bind.B_te.max()),
        "max_ratio_te_trainprop": float(bind.ratio_te_trainprop.max()),
        "max_ratio_pb_fluid": float(bind.ratio_pb_fluid.max()),
    }

    # Calibration identity check: T_s == ceil(1.20 * W_tr_pinned) per adapter.
    recal = [int(math.ceil(1.20 * r.W_tr_pinned)) for r in bind.itertuples()]
    n_calib_bad = sum(int(a != b) for a, b in zip(recal, bind.T_s_stored))
    if n_calib_bad:
        msgs.append(f"MISMATCH T_s calibration identity on {n_calib_bad} stations: "
                    f"recomputed={recal} stored={bind.T_s_stored.tolist()}")
    print(f"[check] T_s == ceil(1.20 * pinned train workload) for all stations: "
          f"{n_calib_bad == 0}")
    return bind, agg, msgs


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    print("=== BERNER feasibility audit ===")
    audit = build_feasibility_audit()
    msgs = sanity_audit(audit)
    audit_path = os.path.join(OUT_DIR, "berner_feasibility_audit.csv")
    audit.to_csv(audit_path, index=False)
    print(f"[write] {audit_path}  ({len(audit)} rows)")

    print("=== BERNER bindingness ===")
    bind, agg, msgs2 = build_bindingness()
    msgs += msgs2
    bind_path = os.path.join(OUT_DIR, "berner_bindingness.csv")
    bind.to_csv(bind_path, index=False)
    print(f"[write] {bind_path}  ({len(bind)} rows)")

    print("--- aggregate bindingness ---")
    for key, val in agg.items():
        print(f"  {key} = {val}")
    print("--- per-station extremes (identity/pinned test assignment) ---")
    top = bind.sort_values("ratio_te_pinned", ascending=False).head(5)
    print(top[["station", "T_s_stored", "W_tr_pinned", "ratio_tr_pinned",
               "W_te_pinned", "ratio_te_pinned", "B_te"]].to_string(index=False))

    if msgs:
        print("SANITY FAIL:")
        for m in msgs:
            print("  " + m)
        sys.exit(1)
    print("SANITY PASS: audit table matches source CSVs cell-by-cell; report-11 "
          "quote verified; REAL_LINES and T_s calibration identities verified.")


if __name__ == "__main__":
    main()
