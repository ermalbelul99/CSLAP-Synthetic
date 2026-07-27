r"""
Total-cost-over-horizon boundary analysis for the affinity-drift stress-test.

Answers the reviewer's question: did the robust layout's insurance pay off over the
*whole operating horizon*, not just survive the shift? The warehouse is slotted once
on historical (regime-A) data, operated for a fraction ``tau`` of the horizon under
A (robust pays its price ``dN``), then an unforeseeable break to regime B for the
rest (robust may save ``dV``). With per-order visit rates:

    dN = n_rob(A) - n_nom(A)   (price/order on A, >= 0 at optimality)
    dV = v_nom(B) - v_rob(B)   (saving/order on B)
    Net(alpha, tau) = (1 - tau) * dV - tau * dN
    robust wins  <=>  Net > 0  <=>  tau < tau*(alpha) = dV / (dV + dN)   (needs dV > 0)

Inputs: the fold manifest (``mode``/``alpha``/order counts per tag) and the
``per_fold.csv`` produced by ``run_robustness_iscf.py evaluate`` (per-tag N on the
train=regime-A and V on the test=regime-B for k=1 nominal and k=10 robust). Outputs
per-(mode, alpha) dN/dV with CIs, the ``tau*(alpha)`` curve, and an ``(alpha, tau)``
win-region heatmap per drift mode.
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Dict, List

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def _ci(a: np.ndarray) -> tuple:
    a = np.asarray(a, dtype=float)
    m = float(a.mean())
    if len(a) < 2:
        return m, float("nan"), float("nan")
    from scipy import stats as st
    h = st.sem(a) * st.t.ppf(0.975, len(a) - 1)
    return m, m - h, m + h


def run(manifest_path: str, per_fold_csv: str, fig_dir: str, k_rob: int = 10) -> None:
    os.makedirs(fig_dir, exist_ok=True)
    with open(manifest_path) as fh:
        manifest = json.load(fh)
    meta = {f["tag"]: f for f in manifest["folds"]}
    pf = pd.read_csv(per_fold_csv)

    rows: List[Dict[str, object]] = []
    for tag, m in meta.items():
        sub = pf[pf.tag == tag]
        s1 = sub[sub.k == 1]; sk = sub[sub.k == k_rob]
        if len(s1) == 0 or len(sk) == 0:
            continue
        ntr, nte = m["n_train_orders"], m["n_test_orders"]
        n_nom = s1["N_train_visits"].iloc[0] / ntr
        n_rob = sk["N_train_visits"].iloc[0] / ntr
        v_nom = s1["V_test_visits"].iloc[0] / nte
        v_rob = sk["V_test_visits"].iloc[0] / nte
        dN = n_rob - n_nom
        dV = v_nom - v_rob
        rows.append({"mode": m["mode"], "alpha": m["alpha"], "repeat": m["repeat"],
                     "dN": dN, "dV": dV,
                     "tau_star": dV / (dV + dN) if (dV + dN) > 0 else float("-inf")})
    df = pd.DataFrame(rows)

    # --- per (mode, alpha) aggregate. ---------------------------------------
    print("=== AFFINITY-DRIFT BOUNDARY (per-order price dN, saving dV; tau* = win-tenure) ===")
    print(f'{"mode":>9} {"alpha":>5} | {"dN/order":>9} | {"dV/order [95% CI]":>26} | {"tau*(alpha)":>16} | robust wins?')
    agg: Dict[tuple, Dict[str, float]] = {}
    for (mode, alpha), g in df.groupby(["mode", "alpha"]):
        dN_m = float(g["dN"].mean())
        dV_m, dV_lo, dV_hi = _ci(g["dV"].values)
        ts_m, ts_lo, ts_hi = _ci(g["tau_star"].replace(-np.inf, 0).values)
        agg[(mode, alpha)] = {"dN": dN_m, "dV": dV_m, "dV_lo": dV_lo, "dV_hi": dV_hi,
                              "tau_star": ts_m}
        wins = "YES (tau<%.2f)" % ts_m if dV_m > 0 and dV_lo > 0 else ("marginal" if dV_m > 0 else "no (dV<=0)")
        print(f'{mode:>9} {alpha:>5.2f} | {dN_m:>+9.4f} | {dV_m:>+8.4f} [{dV_lo:+.4f},{dV_hi:+.4f}] | '
              f'{ts_m:>16.3f} | {wins}')

    # --- Fig A: dV (saving) vs alpha per mode, with CI. ---------------------
    plt.figure(figsize=(7, 4.5))
    for mode in sorted(df["mode"].unique()):
        a = sorted({al for (mm, al) in agg if mm == mode})
        y = [agg[(mode, al)]["dV"] for al in a]
        lo = [agg[(mode, al)]["dV_lo"] for al in a]
        hi = [agg[(mode, al)]["dV_hi"] for al in a]
        plt.plot(a, y, marker="o", label=f"{mode} dV")
        plt.fill_between(a, lo, hi, alpha=0.2)
    plt.axhline(0, color="gray", ls="--", lw=1)
    plt.xlabel("drift magnitude alpha"); plt.ylabel("dV = saving/order on regime B (robust better if >0)")
    plt.title("Does robust beat nominal on the shifted future?"); plt.legend(); plt.grid(alpha=0.3)
    plt.tight_layout(); plt.savefig(os.path.join(fig_dir, "fig5_affinity_dV.png"), dpi=130); plt.close()

    # --- Fig B: win-region heatmap (alpha x tau) per mode. ------------------
    taus = np.linspace(0, 1, 101)
    for mode in sorted(df["mode"].unique()):
        a = sorted({al for (mm, al) in agg if mm == mode})
        Z = np.zeros((len(a), len(taus)))
        for i, al in enumerate(a):
            dN, dV = agg[(mode, al)]["dN"], agg[(mode, al)]["dV"]
            Z[i, :] = (1 - taus) * dV - taus * dN  # Net
        plt.figure(figsize=(7, 4.2))
        vmax = np.nanmax(np.abs(Z)) or 1.0
        plt.imshow(Z, aspect="auto", origin="lower", cmap="RdYlGn",
                   vmin=-vmax, vmax=vmax,
                   extent=[0, 1, min(a), max(a)])
        plt.colorbar(label="Net (per order); >0 = robust insurance pays off")
        plt.xlabel("stable tenure tau (fraction of horizon before the break)")
        plt.ylabel("drift magnitude alpha")
        plt.title(f"Win region: {mode} drift  (green = robust wins over horizon)")
        plt.tight_layout()
        plt.savefig(os.path.join(fig_dir, f"fig6_winregion_{mode}.png"), dpi=130); plt.close()

    print(f"\nfigures written to {fig_dir}")


def main() -> None:
    p = argparse.ArgumentParser(description="Affinity-drift total-cost-over-horizon analysis.")
    p.add_argument("--manifest", required=True)
    p.add_argument("--per-fold", required=True)
    p.add_argument("--fig-dir", default="../../../../reports/figures")
    p.add_argument("--k-rob", type=int, default=10)
    args = p.parse_args()
    run(args.manifest, args.per_fold, args.fig_dir, args.k_rob)


if __name__ == "__main__":
    main()
