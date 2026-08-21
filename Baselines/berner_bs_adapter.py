r"""Adapter: BERNER industrial instance -> temporal folds for the BS harness.

Builds a *partial re-optimization* sub-instance of the real warehouse from
``data_loader_industrial.load_industrial_data``: the ``top_n`` most frequent
kept SKUs are freed for placement, every other kept SKU stays frozen at its
warm-start station, and the station budgets handed to the solver are the
**residual** ones left after the frozen SKUs have taken their share.

Why residual budgets
--------------------
The industrial ceilings are descriptive, not engineered:
:math:`T_s` equals the warm-start layout's realized workload and
:math:`\zeta_s` its slot count, both to machine precision -- the incumbent sits
exactly ON both constraints with zero headroom. Writing
:math:`\beta` for a capacity-slack multiplier, the budget offered to the placed
SKUs at station ``s`` on the train window is

.. math::
    T^{res}_s(\beta) = \beta\,T^{tr}_s - \sum_{p \in F_s} L^{tr}_p / V_s,
    \qquad
    \zeta^{res}_s = \zeta_s - |F_s|,

where :math:`F_s` are the frozen SKUs at ``s`` and
:math:`T^{tr}_s = \sum_{p\ \mathrm{at}\ s} L^{tr}_p / V_s` is the warm start's
realized workload restricted to the train window (so train and test windows are
measured on the same basis). At :math:`\beta = 1` the residual budget is
exactly the warm start's own placed-load, i.e. the incumbent is feasible with
**zero slack** -- the faithful reading of the industrial contract. Values
:math:`\beta > 1` buy headroom and make the robustness question well posed.

Station heterogeneity is preserved verbatim (24 stations, 23 distinct speeds
spanning ~1700x); the harness's per-station normalized ceiling
:math:`T^{\mathrm n}_s = T_s\lambda` handles it.

Output per (top_n, beta): one temporal cut in the harness's fold layout,

    {out}/{tag}/{tag}_r0f0_{train|test}_{orders|products|stations}.csv

with ``PRODUCT`` tokens prefixed ``PROD_`` and ``REAL_LINES`` = train pick-lines.

CLI:
    python berner_bs_adapter.py --data <BERNER csv> --out <folds root>
        --top-n 2000 --train-frac 0.75 --betas 1.0,1.05,1.10,1.20
"""
from __future__ import annotations

import argparse
import os
import sys
from collections import defaultdict
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

BASE: str = os.path.dirname(os.path.abspath(__file__))
_ROOT: str = os.path.dirname(BASE)
sys.path.insert(0, BASE)
sys.path.insert(0, _ROOT)

# ``data_loader_industrial`` sits at the repository root here, not alongside this
# file as it did upstream, so _ROOT must be on the path before the import.
from data_loader_industrial import load_industrial_data  # noqa: E402
from paths import BERNER_CSV, DERIVED  # noqa: E402

DEFAULT_DATA: str = BERNER_CSV
DEFAULT_OUT: str = os.path.join(DERIVED, "berner_bs_folds")


def build_folds(
    data_path: str,
    out_root: str,
    top_n: int,
    train_frac: float,
    betas: List[float],
) -> List[str]:
    """Build one temporal fold per beta for the industrial sub-instance.

    Args:
        data_path: Raw BERNER order-lines CSV.
        out_root: Root output directory.
        top_n: Number of most frequent kept SKUs freed for placement.
        train_frac: Early fraction of distinct ORDER ids used for training.
        betas: Capacity-slack multipliers on the station ceilings.

    Returns:
        The instance tags written (one per beta).
    """
    data = load_industrial_data(data_path)
    odf: pd.DataFrame = data["odf_solver"]          # deduped PRODUCT/ORDER/STATION
    pl: Dict[str, int] = data["pl_solver"]          # full-window frequency
    warm: Dict[str, str] = data["warm_start_assignment"]
    st_solver: List[dict] = data["st_solver"]

    # Station ids are prefixed: raw BERNER ids such as "01.07" / "01.E4" are
    # parsed by pandas as floats (1.07 / 1.0e4) on re-read, which silently
    # breaks every join against them (station ids, warm-start layout).
    def sid_of(raw: object) -> str:
        return f"ST_{raw}"

    speeds = {sid_of(s["STATION_ID"]): float(s["SPEED"]) for s in st_solver}
    caps = {sid_of(s["STATION_ID"]): int(s["CAPACITY"]) for s in st_solver}
    sids = [sid_of(s["STATION_ID"]) for s in st_solver]

    # --- free the top_n SKUs, freeze the rest -----------------------------
    ranked = sorted(pl.items(), key=lambda kv: (-kv[1], str(kv[0])))
    placed = [p for p, _ in ranked[:top_n]]
    placed_set = set(placed)
    frozen = [p for p, _ in ranked[top_n:]]

    # --- temporal split on the ORDER ids (dense sequential ERP counter) ----
    order_ids = np.array(sorted(odf["ORDER"].unique()))
    n_tr = int(round(train_frac * len(order_ids)))
    train_ids = set(order_ids[:n_tr].tolist())
    tr_df = odf[odf["ORDER"].isin(train_ids)]
    te_df = odf[~odf["ORDER"].isin(train_ids)]

    # Train-window pick-lines (deduped frame -> distinct-order counts).
    tr_lines_all = tr_df.groupby("PRODUCT").size().to_dict()

    # Frozen share of each station's train-window budget.
    frozen_load: Dict[str, float] = defaultdict(float)
    frozen_slots: Dict[str, int] = defaultdict(int)
    for p in frozen:
        s = sid_of(warm.get(p))
        if s in speeds:
            frozen_load[s] += tr_lines_all.get(p, 0) / speeds[s]
            frozen_slots[s] += 1
    # Warm-start realized workload on the TRAIN window (all kept SKUs).
    warm_load_tr: Dict[str, float] = defaultdict(float)
    for p, s_raw in warm.items():
        s = sid_of(s_raw)
        if s in speeds:
            warm_load_tr[s] += tr_lines_all.get(p, 0) / speeds[s]

    # Placed-only orders, both windows.
    tr_p = tr_df[tr_df["PRODUCT"].isin(placed_set)]
    te_p = te_df[te_df["PRODUCT"].isin(placed_set)]
    tr_lines = tr_p.groupby("PRODUCT").size().to_dict()

    tags: List[str] = []
    for beta in betas:
        tag = f"bern{top_n}_b{beta:g}"
        out_dir = os.path.join(out_root, tag)
        os.makedirs(out_dir, exist_ok=True)
        fold = f"{tag}_r0f0"

        rows = []
        for s in sids:
            t_res = beta * warm_load_tr[s] - frozen_load[s]
            z_res = caps[s] - frozen_slots[s]
            if z_res <= 0:
                continue  # station fully taken by frozen SKUs
            rows.append({
                "STATION_ID": s,
                "CAPACITY": z_res,
                "TIME_CAPACITY": max(t_res, 0.0),
                "SPEED": speeds[s],
            })
        st_df = pd.DataFrame(rows)

        prod_df = pd.DataFrame({
            "PRODUCT_ID": placed,
            "REAL_LINES": [int(tr_lines.get(p, 0)) for p in placed],
            "WARM_STATION": [sid_of(warm.get(p, "")) for p in placed],
        })

        for role, df in (("train", tr_p), ("test", te_p)):
            out = pd.DataFrame({
                "ORDER": df["ORDER"].to_numpy(),
                "PRODUCT": "PROD_" + df["PRODUCT"].astype(str),
                "STATION": ["ST_" + str(v) for v in df["STATION"].to_numpy()],
            })
            out.to_csv(os.path.join(out_dir, f"{fold}_{role}_orders.csv"),
                       index=False, sep=";")
            prod_df.to_csv(os.path.join(out_dir, f"{fold}_{role}_products.csv"),
                           index=False, sep=";")
            st_df.to_csv(os.path.join(out_dir, f"{fold}_{role}_stations.csv"),
                         index=False, sep=";")

        slack_tot = float(st_df["TIME_CAPACITY"].sum())
        placed_tot = sum(tr_lines.get(p, 0) / speeds[sid_of(warm[p])]
                         for p in placed if sid_of(warm.get(p)) in speeds)
        print(f"[berner_bs_adapter] {tag}: stations={len(st_df)} "
              f"placed_slots={int(st_df['CAPACITY'].sum())} "
              f"budget={slack_tot:.1f} warm_placed_load={placed_tot:.1f} "
              f"headroom={100 * (slack_tot / placed_tot - 1):.2f}%", flush=True)
        tags.append(tag)

    print(f"[berner_bs_adapter] kept SKUs={len(pl)} placed={len(placed)} "
          f"frozen={len(frozen)} | orders train={len(train_ids)} "
          f"test={len(order_ids) - len(train_ids)} | "
          f"train lines(placed)={sum(tr_lines.values())} "
          f"test lines(placed)={len(te_p)}", flush=True)
    return tags


def main() -> None:
    """Build the industrial folds (CLI)."""
    ap = argparse.ArgumentParser(description="BERNER -> BS harness fold adapter")
    ap.add_argument("--data", type=str, default=DEFAULT_DATA)
    ap.add_argument("--out", type=str, default=DEFAULT_OUT)
    ap.add_argument("--top-n", type=int, default=2000)
    ap.add_argument("--train-frac", type=float, default=0.75)
    ap.add_argument("--betas", type=str, default="1.0,1.05,1.10,1.20")
    args = ap.parse_args()
    betas = [float(b) for b in args.betas.split(",")]
    build_folds(args.data, args.out, args.top_n, args.train_frac, betas)


if __name__ == "__main__":
    main()
