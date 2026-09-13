r"""Score stored layouts against the volume-normalised share contract.

    W_s(d)  <=  ( mu_s + z * sigma_s ) * L(d) / beta

``mu_s`` and ``sigma_s`` are fitted on TRAINING days under the incumbent and
then FROZEN. Only ``L(d)``, the realised daily volume, changes between the
train and test call -- legitimate, because the contract grants a share of
whatever arrives and the layout cannot influence how much arrives.

Why this replaces ``daily_metrics.py`` for share-contract runs
--------------------------------------------------------------

* ``daily_metrics.py`` scores against a frozen per-station ceiling, which is a
  different contract from the one these layouts were optimised against.
* The columns ``robust_ok``, ``viol_norm``, ``max_ratio_norm`` and ``X`` in
  ``results.csv`` are computed from the mean-day ``lbar`` against the old
  revealed-peak ceiling. Under ``--share-z`` they describe a contract the model
  is not solving and must not be interpreted.
* ``daily_metrics.py`` globs layouts tree-wide and keys arms by FILENAME, so
  identical arm names in different directories collide and the
  alphabetically-last path silently wins. This script takes exactly ONE
  results directory and refuses to recurse, so that defect cannot recur.

Two diagnostics the study's own theory defines
----------------------------------------------

``gamma_bind``  the smallest budget at which the robust row would start to cut
   off THIS layout on the training data. Below it, raising Gamma changes
   nothing at that station; at or above it, the optimiser is forced to
   rebalance. It says where protection begins to bite.

``gamma_cover`` the smallest budget whose protection would have absorbed the
   station's realised TEST overshoot. Zero when the station never overshot.
   It says how much protection the future actually asked for.

Reporting both is what lets the paper say WHERE protection is useful, rather
than only whether one arm beat another.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from milp_highs_robust import read_data                      # noqa: E402
from share_contract import (allowance_lines, check_identities,  # noqa: E402
                            fit_share_band, onehot_from_assignment)


def _day_matrix(orders: pd.DataFrame, products: List[str]) -> np.ndarray:
    piv = (orders.assign(_P=orders["PRODUCT"].astype(str))
           .groupby(["DELIVERY_DATE", "_P"]).size().unstack(fill_value=0))
    return piv.reindex(columns=[str(p) for p in products],
                       fill_value=0).to_numpy(float)


def load_fold(fold_dir: str) -> dict:
    tag = os.path.basename(fold_dir.rstrip("/\\"))
    st = pd.read_csv(os.path.join(fold_dir, tag + "_train_stations.csv"),
                     sep=";")
    pr = pd.read_csv(os.path.join(fold_dir, tag + "_train_products.csv"),
                     sep=";")
    tro = pd.read_csv(os.path.join(fold_dir, tag + "_train_orders.csv"),
                      sep=";")
    teo = pd.read_csv(os.path.join(fold_dir, tag + "_test_orders.csv"), sep=";")
    _o, _s, products, _l = read_data(tag + "_train", fold_dir)
    sids = [str(s) for s in st["STATION_ID"]]
    incumbent = {f"PROD_{r.PRODUCT_ID}": str(r.WARM_STATION)
                 for r in pr.itertuples()}
    return {
        "tag": tag, "products": list(products), "sids": sids,
        "incumbent": incumbent,
        "Dtr": _day_matrix(tro, products), "Dte": _day_matrix(teo, products),
    }


def gamma_bind(D: np.ndarray, onehot: np.ndarray, lhat: np.ndarray,
               rhs: np.ndarray, gmax: int = 64) -> np.ndarray:
    """Smallest Gamma at which the robust row cuts off this layout, per station.

    ``gmax + 1`` means no budget in range binds.
    """
    load = D @ onehot                                  # (days, stations)
    headroom = (rhs - load).min(axis=0)                # worst day per station
    out = np.full(onehot.shape[1], gmax + 1, dtype=int)
    for s in range(onehot.shape[1]):
        own = np.sort(lhat[onehot[:, s] > 0.5])[::-1]
        if own.size == 0:
            out[s] = 0 if headroom[s] < 0 else gmax + 1
            continue
        run = np.cumsum(own[:gmax])
        hit = np.nonzero(run > headroom[s])[0]
        if headroom[s] < 0:
            out[s] = 0                                 # already infeasible
        elif hit.size:
            out[s] = int(hit[0]) + 1
    return out


def gamma_cover(Dte: np.ndarray, onehot: np.ndarray, lhat: np.ndarray,
                rhs_te: np.ndarray, gmax: int = 64) -> np.ndarray:
    """Smallest Gamma whose protection covers the realised TEST overshoot."""
    load = Dte @ onehot
    excess = np.maximum(load - rhs_te, 0.0).max(axis=0)
    out = np.zeros(onehot.shape[1], dtype=int)
    for s in range(onehot.shape[1]):
        if excess[s] <= 0:
            continue
        own = np.sort(lhat[onehot[:, s] > 0.5])[::-1]
        if own.size == 0:
            out[s] = gmax + 1
            continue
        run = np.cumsum(own[:gmax])
        hit = np.nonzero(run >= excess[s])[0]
        out[s] = int(hit[0]) + 1 if hit.size else gmax + 1
    return out


def score(D: np.ndarray, onehot: np.ndarray, mu: np.ndarray, sd: np.ndarray,
          z: float, beta: float = 1.0) -> Tuple[dict, np.ndarray]:
    rhs = allowance_lines(mu, sd, z, D.sum(axis=1), beta)
    load = D @ onehot
    over = load > rhs + 1e-9
    ratio = np.where(rhs > 0, load / np.maximum(rhs, 1e-12), 0.0)
    return {
        "n_days": int(D.shape[0]),
        "days_violated": int(over.any(axis=1).sum()),
        "station_days_over": int(over.sum()),
        "worst_day_ratio": float(ratio.max()) if ratio.size else 0.0,
        "mean_daily_ratio": float(ratio.max(axis=1).mean()) if ratio.size else 0.0,
        "stations_over": int(over.any(axis=0).sum()),
    }, rhs


def arm_of(path: str, tag: str) -> Optional[str]:
    base = os.path.basename(path)
    stem = base[len(f"layout_{tag}_"):-len(".json")] if base.startswith(
        f"layout_{tag}_") else None
    return stem


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--folds", required=True, help="fold root")
    ap.add_argument("--results", required=True,
                    help="ONE results directory (never a tree; see module "
                         "docstring for why recursion is refused)")
    ap.add_argument("--z", type=float, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--per-station-out", default=None)
    ap.add_argument("--gmax", type=int, default=64)
    a = ap.parse_args()

    lay_dir = os.path.join(a.results, "layouts")
    if not os.path.isdir(lay_dir):
        raise SystemExit(f"no layouts/ under {a.results}")

    rows, st_rows = [], []
    fold_dirs = sorted(d for d in glob.glob(os.path.join(a.folds, "*"))
                       if os.path.isfile(os.path.join(d, "fold_meta.json")))
    if not fold_dirs:
        raise SystemExit(f"no folds under {a.folds}")

    for fd in fold_dirs:
        f = load_fold(fd)
        tag, prods, sids = f["tag"], f["products"], f["sids"]
        oh_inc = onehot_from_assignment(f["incumbent"], prods, sids)
        mu, sd, shares = fit_share_band(f["Dtr"], oh_inc)
        check_identities(mu, sd, a.z, shares)

        lhat_path = os.path.join(a.results, f"lhat_{tag}.json")
        if os.path.isfile(lhat_path):
            lh = json.load(open(lhat_path, encoding="utf-8"))
            lhat = np.array([float(lh.get(p, 0.0)) for p in prods])
            lhat_src = "harness"
        else:
            lhat = f["Dtr"].std(axis=0, ddof=1)
            lhat_src = "recomputed"

        arms: Dict[str, np.ndarray] = {"incumbent": oh_inc}
        for p in sorted(glob.glob(os.path.join(lay_dir,
                                               f"layout_{tag}_*.json"))):
            arm = arm_of(p, tag)
            if arm is None:
                continue
            lay = json.load(open(p, encoding="utf-8"))
            arms[arm] = onehot_from_assignment(lay, prods, sids)

        for arm, oh in arms.items():
            # beta is a TRAINING device, not the operating requirement. Every
            # arm is judged against the SAME contract (beta = 1); scoring a
            # tightened arm against its own tighter band would penalise it for
            # being conservative and can invert the comparison outright.
            train_beta = 1.0
            if arm.startswith("b"):
                try:
                    train_beta = float(arm[1:])
                except ValueError:
                    train_beta = 1.0
            for role, D in (("train", f["Dtr"]), ("test", f["Dte"])):
                m, rhs = score(D, oh, mu, sd, a.z, beta=1.0)
                m.update({"fold": int(tag[-1]), "z": a.z, "arm": arm,
                          "train_beta": train_beta, "role": role,
                          "lhat_source": lhat_src})
                rows.append(m)
            _mtr, rhs_tr = score(f["Dtr"], oh, mu, sd, a.z, beta=1.0)
            _mte, rhs_te = score(f["Dte"], oh, mu, sd, a.z, beta=1.0)
            gb = gamma_bind(f["Dtr"], oh, lhat, rhs_tr, a.gmax)
            gc = gamma_cover(f["Dte"], oh, lhat, rhs_te, a.gmax)
            for i, sid in enumerate(sids):
                st_rows.append({"fold": int(tag[-1]), "z": a.z, "arm": arm,
                                "station": sid, "mu": float(mu[i]),
                                "sigma": float(sd[i]),
                                "gamma_bind": int(gb[i]),
                                "gamma_cover": int(gc[i])})

    df = pd.DataFrame(rows)
    df.to_csv(a.out, index=False)
    print(f"[daily_metrics_share] {len(df)} rows -> {a.out}")
    st = pd.DataFrame(st_rows)
    if a.per_station_out:
        st.to_csv(a.per_station_out, index=False)
        print(f"[daily_metrics_share] {len(st)} station rows -> "
              f"{a.per_station_out}")

    te = df[df.role == "test"]
    print(f"\nTEST window, share contract at z={a.z:g} (all folds pooled)")
    g = (te.groupby("arm")
         .agg(days_viol=("days_violated", "sum"), days=("n_days", "sum"),
              worst=("worst_day_ratio", "max"),
              mean_ratio=("mean_daily_ratio", "mean"),
              folds=("fold", "nunique")).reset_index())
    print(g.to_string(index=False))
    if not st.empty:
        print(f"\ngamma_bind (where protection starts to bite) and "
              f"gamma_cover (what the future asked for), median over stations:")
        gg = (st.groupby("arm")
              .agg(bind_med=("gamma_bind", "median"),
                   bind_min=("gamma_bind", "min"),
                   cover_med=("gamma_cover", "median"),
                   cover_max=("gamma_cover", "max")).reset_index())
        print(gg.to_string(index=False))


if __name__ == "__main__":
    main()
