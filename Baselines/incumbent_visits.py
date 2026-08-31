"""Visits carried by the INCUMBENT layout, the study's actual objective.

The grid reports V_tr/V_te only for optimised arms, and PoR is measured
against gamma0. Comparing the incumbent's contract violations with the
optimised arms' is therefore only half the picture: the reason to optimise at
all is to cut station visits. This evaluates the incumbent through the SAME
path the driver uses for every arm (evaluate_layout_robust), so the numbers are
directly comparable.
"""
import json, os, sys
import pandas as pd
REPO = r"C:\ermal\CSLAP_Full_Project\CSLAP-Synthetic"
sys.path.insert(0, os.path.join(REPO, "Baselines"))
import evaluate_layout_robust as ev            # noqa: E402
from milp_highs_robust import read_data        # noqa: E402

FOLDS = os.path.join(REPO, "data", "derived", "berner_daily_folds")
rows = []
for f in range(4):
    tag = f"berner_daily_r0f{f}"
    d = os.path.join(FOLDS, tag)
    tr_op, stations, products, lbar = read_data(tag + "_train", d)
    tro = pd.read_csv(os.path.join(d, f"{tag}_train_orders.csv"), sep=";")
    teo = pd.read_csv(os.path.join(d, f"{tag}_test_orders.csv"), sep=";")
    te_op = teo.groupby("ORDER")["PRODUCT"].apply(list).to_dict()
    tr_lines = tro.groupby("PRODUCT").size().astype(float).to_dict()
    te_lines = teo.groupby("PRODUCT").size().astype(float).to_dict()
    pr = pd.read_csv(os.path.join(d, f"{tag}_train_products.csv"), sep=";")
    inc = {f"PROD_{r.PRODUCT_ID}": str(r.WARM_STATION) for r in pr.itertuples()}
    m_tr = ev.evaluate_layout(inc, tr_op, stations, tr_lines)
    m_te = ev.evaluate_layout(inc, te_op, stations, te_lines)
    rows.append({"fold": f, "arm": "incumbent",
                 "V_tr": m_tr["total_visits"], "V_te": m_te["total_visits"]})
inc = pd.DataFrame(rows)
print("INCUMBENT visits (same evaluator the driver uses for every arm)")
print(inc.to_string(index=False))
print(f"\npooled V_tr={inc.V_tr.sum():.0f}  V_te={inc.V_te.sum():.0f}\n")
for z in (3, 4, 6):
    g = pd.read_csv(os.path.join(REPO, "results", "z_contract", f"z{z}",
                                 "results.csv"))
    print(f"z={z}:")
    for arm, lab in (("gamma0", "g0"), ("gamma1", "g1"), ("gamma2", "g2"),
                     ("gamma4", "g4"), ("tight1.02", "b1.02"),
                     ("tight1.05", "b1.05")):
        s = g[(g.arm == arm) & (g.feasible_model.astype(bool))]
        if s.empty:
            continue
        fl = sorted(s.fold.unique())
        base = inc[inc.fold.isin(fl)]
        d_tr = 100 * (s.V_tr.sum() - base.V_tr.sum()) / base.V_tr.sum()
        d_te = 100 * (s.V_te.sum() - base.V_te.sum()) / base.V_te.sum()
        print(f"   {lab:6} folds={fl} visits vs INCUMBENT: "
              f"train {d_tr:+6.2f}%   test {d_te:+6.2f}%")
    print()
