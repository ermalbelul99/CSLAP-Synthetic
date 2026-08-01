"""
Numerically verify the LP relaxation value of the binary CSLAP formulation.

Claim: the LP relaxation of (obj, assign, cap, link, wl, dom) has value exactly
|O|, the number of orders, whenever the uniform fractional point x_ps = 1/|S|
is feasible. Two halves:

  lower bound  for any order o pick any p* in P_o; z_os >= x_{p*s} and
               sum_s x_{p*s} = 1, so sum_s z_os >= 1. Summing gives obj >= |O|.
  upper bound  x_ps = 1/|S| forces z_os = 1/|S| at optimum, giving obj = |O|,
               and that point satisfies capacity when |P|/|S| <= zeta_s and
               workload when the instance carries any positive slack.

If true, branch-and-bound starts from the trivial bound "every order visits at
least one station" on every instance, independent of correlation structure.

Run: python lp_bound_check.py
"""

import os
import sys

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix

ROOT = ("c:/Users/ebelul/OneDrive - SAVOYE/Desktop/PhD_Work_2023-2026/CSLAP_Problem/"
        "Different_Solution_Approaches/Full_Package_Code_With_All_Approaches/CSLAP-Synthetic")
sys.path.insert(0, os.path.join(ROOT, "Baselines"))
from milp_gurobi_synthetic import read_data  # noqa: E402


def lp_value(inst_dir, prefix):
    order_prods, stations, products, prod_lines = read_data(prefix, inst_dir)
    sids = [s["STATION_ID"] for s in stations]
    caps = {s["STATION_ID"]: s["CAPACITY"] for s in stations}
    tcaps = {s["STATION_ID"]: s["TIME_CAPACITY"] for s in stations}
    speeds = {s["STATION_ID"]: s["SPEED"] for s in stations}
    orders = list(order_prods.keys())
    nP, nS, nO = len(products), len(sids), len(orders)

    pidx = {p: i for i, p in enumerate(products)}
    sidx = {s: j for j, s in enumerate(sids)}
    # variable layout: x[p,s] then z[o,s]
    def xv(p, s): return pidx[p] * nS + sidx[s]
    def zv(o, s): return nP * nS + o * nS + sidx[s]
    nvar = nP * nS + nO * nS

    c = np.zeros(nvar)
    for o in range(nO):
        for s in sids:
            c[zv(o, s)] = 1.0

    # equality: sum_s x_ps = 1
    er, ec, ev = [], [], []
    for p in products:
        for s in sids:
            er.append(pidx[p]); ec.append(xv(p, s)); ev.append(1.0)
    Aeq = coo_matrix((ev, (er, ec)), shape=(nP, nvar))
    beq = np.ones(nP)

    ir, ic, iv, bub = [], [], [], []
    row = 0
    for s in sids:                                   # capacity
        for p in products:
            ir.append(row); ic.append(xv(p, s)); iv.append(1.0)
        bub.append(float(caps[s])); row += 1
    for s in sids:                                   # workload
        for p in products:
            ir.append(row); ic.append(xv(p, s))
            iv.append(prod_lines.get(p, 0) / (speeds[s] or 1.0))
        bub.append(float(tcaps[s])); row += 1
    for oi, o in enumerate(orders):                  # link: x_ps - z_os <= 0
        for p in set(order_prods[o]):
            if p not in pidx:
                continue
            for s in sids:
                ir += [row, row]; ic += [xv(p, s), zv(oi, s)]; iv += [1.0, -1.0]
                bub.append(0.0); row += 1
    Aub = coo_matrix((iv, (ir, ic)), shape=(row, nvar))

    res = linprog(c, A_ub=Aub, b_ub=np.array(bub), A_eq=Aeq, b_eq=beq,
                  bounds=(0, 1), method="highs")
    return res, nO, nP, nS, row


if __name__ == "__main__":
    for seed in ("1001", "1002"):
        d = os.path.join(ROOT, "exp02a_instances", f"syn_50sku_seed{seed}")
        res, nO, nP, nS, nrows = lp_value(d, "syn_50sku")
        print(f"--- syn_50sku_seed{seed}: |P|={nP} |S|={nS} |O|={nO}, "
              f"LP rows={nrows}")
        if not res.success:
            print("   LP failed:", res.message)
            continue
        print(f"   LP relaxation optimum = {res.fun:.6f}")
        print(f"   number of orders |O|  = {nO}")
        print(f"   equal to |O|? {abs(res.fun - nO) < 1e-4}")
