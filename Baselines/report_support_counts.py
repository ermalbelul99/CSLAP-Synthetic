r"""
Distinct-support (|U|) and pricing-model-size report for the IJPR revision.

Reviewer Q1 asks how large the set U of distinct multi-item order supports
becomes, and what that implies for the pricing model. This script recomputes,
with the exact semantics of ``cg_setpart_cplex.aggregate_supports`` (frozenset
of an order's products, kept when it has >= 2 items, multiplicity = number of
orders sharing the support), the following for (a) each exp02a synthetic
instance and (b) the industrial solver instance produced by
``data_loader_industrial.load_industrial_data``:

* ``num_supports``      |U|, the number of distinct multi-item supports;
* ``multi_item_orders`` total weight sum(w_u) (multi-item orders);
* ``linking_rows``      sum_u |u|, the number of z_u >= a_p linking rows the
                        persistent pricing MILP carries;
* ``num_skus``          |P| (a_p variables in the pricing model).

The pricing model therefore has |U| + |P| variables and linking_rows + 2
constraints (capacity + workload). Aggregates per synthetic size are written
next to the per-instance rows.

Usage (env savoye2023; run from the CSLAP-Synthetic root):
    python Baselines/report_support_counts.py
Writes exp02a_results/support_counts.csv and prints a summary.
"""

from __future__ import annotations

import os
import re
import sys
from collections import defaultdict

import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _HERE)
sys.path.insert(0, _ROOT)

from data_loader_industrial import load_industrial_data  # noqa: E402

INSTANCE_DIR = os.path.join(_ROOT, "exp02a_instances")
OUT_CSV = os.path.join(_ROOT, "exp02a_results", "support_counts.csv")


def support_stats(order_prods) -> dict:
    """|U|, weight total, and linking-row count, mirroring aggregate_supports."""
    cnt = defaultdict(int)
    for prods in order_prods.values():
        s = frozenset(prods)
        if len(s) >= 2:
            cnt[s] += 1
    linking_rows = sum(len(s) for s in cnt)
    return {
        "num_supports": len(cnt),
        "multi_item_orders": sum(cnt.values()),
        "linking_rows": linking_rows,
    }


def main() -> None:
    rows = []

    pat = re.compile(r"syn_(\d+)sku_seed(\d+)")
    for d in sorted(os.listdir(INSTANCE_DIR)):
        m = pat.fullmatch(d)
        if not m:
            continue
        size, iseed = int(m.group(1)), int(m.group(2))
        prefix = f"syn_{size}sku"
        orders_df = pd.read_csv(
            os.path.join(INSTANCE_DIR, d, f"{prefix}_orders.csv"), sep=";")
        order_prods = orders_df.groupby("ORDER")["PRODUCT"].apply(list).to_dict()
        stats = support_stats(order_prods)
        rows.append({
            "instance": d, "size_n": size, "instance_seed": iseed,
            "num_orders": len(order_prods),
            "num_skus": orders_df["PRODUCT"].nunique(),
            **stats,
        })
        print(f"{d}: |U|={stats['num_supports']:,} "
              f"linking_rows={stats['linking_rows']:,}", flush=True)

    data = load_industrial_data(
        os.path.join(_ROOT, "Heuristic_Connex_Set_Project", "data",
                     "BERNER_ORDER_LINES_09-12.csv"))
    op_solver = data["op_solver"]
    stats = support_stats(op_solver)
    rows.append({
        "instance": "industrial_solver(BERNER pruned)", "size_n": "",
        "instance_seed": "",
        "num_orders": len(op_solver),
        "num_skus": len(data["pr_solver"]),
        **stats,
    })
    print(f"industrial solver instance: |P|={len(data['pr_solver']):,} "
          f"orders={len(op_solver):,} |U|={stats['num_supports']:,} "
          f"linking_rows={stats['linking_rows']:,}", flush=True)
    full_stats = support_stats(data["op_full"])
    rows.append({
        "instance": "industrial_full(BERNER all orders)", "size_n": "",
        "instance_seed": "",
        "num_orders": len(data["op_full"]),
        "num_skus": len(data["pr_solver"]) + len(data["static_assignment"]),
        **full_stats,
    })

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)

    syn = df[df["size_n"] != ""]
    agg = syn.groupby("size_n")[["num_supports", "linking_rows"]].mean().round(0)
    print("\nPer-size means (synthetic):")
    print(agg.to_string())
    print(f"\nwrote {OUT_CSV}")


if __name__ == "__main__":
    main()
