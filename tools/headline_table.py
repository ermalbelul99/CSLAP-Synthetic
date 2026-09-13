"""Build the headline comparison table. Committed so it is not hand-assembled.

Reports every arm against the INCUMBENT on both axes at once: station visits
(the study's objective) and share-band violations (the constraint). Writes
results/z_contract/headline_vs_incumbent.csv.

Two things this file is careful about, both raised in review:

* An arm that did not solve on every fold is rebased onto the folds it DID
  solve, and the fold list is written into the CSV. A row over 2 folds is not
  comparable with a row over 4, and the reader must be able to see that.
* Arm names differ between results.csv (gamma0/tight1.02) and the layout and
  metrics files (g0/b1.02). An unmatched name used to drop a whole arm
  silently; it now raises.
"""
from __future__ import annotations

import os
import sys

import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "Baselines"))
import evaluate_layout_robust as ev                      # noqa: E402
from milp_highs_robust import read_data                  # noqa: E402

FOLDS = os.path.join(REPO, "data", "derived", "berner_daily_folds")
ZDIR = os.path.join(REPO, "results", "z_contract")
ARM = {"gamma0": "g0", "gamma1": "g1", "gamma2": "g2", "gamma4": "g4",
       "tight1.02": "b1.02", "tight1.05": "b1.05"}


def incumbent_visits() -> pd.DataFrame:
    rows = []
    for f in range(4):
        tag = f"berner_daily_r0f{f}"
        d = os.path.join(FOLDS, tag)
        tr_op, stations, _p, _l = read_data(tag + "_train", d)
        tro = pd.read_csv(os.path.join(d, f"{tag}_train_orders.csv"), sep=";")
        teo = pd.read_csv(os.path.join(d, f"{tag}_test_orders.csv"), sep=";")
        te_op = teo.groupby("ORDER")["PRODUCT"].apply(list).to_dict()
        tr_lines = tro.groupby("PRODUCT").size().astype(float).to_dict()
        te_lines = teo.groupby("PRODUCT").size().astype(float).to_dict()
        pr = pd.read_csv(os.path.join(d, f"{tag}_train_products.csv"), sep=";")
        inc = {f"PROD_{r.PRODUCT_ID}": str(r.WARM_STATION)
               for r in pr.itertuples()}
        rows.append({"fold": f, "arm": "incumbent",
                     "V_tr": ev.evaluate_layout(inc, tr_op, stations,
                                                tr_lines)["total_visits"],
                     "V_te": ev.evaluate_layout(inc, te_op, stations,
                                                te_lines)["total_visits"]})
    return pd.DataFrame(rows)


def main() -> None:
    INC = incumbent_visits()
    INC.to_csv(os.path.join(ZDIR, "incumbent_visits.csv"), index=False)
    out = []
    for z in (3, 4, 6):
        g = pd.read_csv(os.path.join(ZDIR, f"z{z}", "results.csv"))
        m = pd.read_csv(os.path.join(ZDIR, f"metrics_z{z}.csv"))
        te = m[m.role == "test"]
        unknown = set(g.arm.unique()) - set(ARM)
        if unknown:
            raise SystemExit(f"z={z}: unmapped arm names {sorted(unknown)} - "
                             f"they would be dropped from the headline "
                             f"silently; extend ARM instead")
        iv = te[te.arm == "incumbent"]
        out.append({"z": z, "arm": "incumbent", "folds": 4,
                    "fold_ids": "0;1;2;3", "visits_vs_incumbent_pct": 0.0,
                    "test_days_violated": int(iv.days_violated.sum()),
                    "test_days": int(iv.n_days.sum()),
                    "worst_day_ratio": round(float(iv.worst_day_ratio.max()), 4),
                    "comparable_to_incumbent_row": True})
        for a, lab in ARM.items():
            s = g[(g.arm == a) & (g.feasible_model.astype(bool))]
            if s.empty:
                continue
            fl = sorted(int(x) for x in s.fold.unique())
            base = INC[INC.fold.isin(fl)].V_te.sum()
            t = te[(te.arm == lab) & (te.fold.isin(fl))]
            out.append({
                "z": z, "arm": lab, "folds": len(fl),
                "fold_ids": ";".join(str(x) for x in fl),
                "visits_vs_incumbent_pct": round(
                    100 * (s.V_te.sum() - base) / base, 3),
                "test_days_violated": int(t.days_violated.sum()),
                "test_days": int(t.n_days.sum()),
                "worst_day_ratio": round(float(t.worst_day_ratio.max()), 4),
                # False means the violation count is over a DIFFERENT fold set
                # from the incumbent row above and must not be read beside it.
                "comparable_to_incumbent_row": len(fl) == 4,
            })
    df = pd.DataFrame(out)
    df.to_csv(os.path.join(ZDIR, "headline_vs_incumbent.csv"), index=False)
    print(df.to_string(index=False))
    bad = df[~df.comparable_to_incumbent_row]
    if len(bad):
        print(f"\nNOT comparable with the incumbent row (partial fold set): "
              f"{bad[['z', 'arm', 'fold_ids']].to_dict('records')}")


if __name__ == "__main__":
    main()
