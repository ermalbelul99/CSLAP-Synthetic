r"""
BERNER preprocess-vs-capacity decomposition (the one open confound).

The earlier BERNER run was the only place a positive out-of-sample gain appeared,
but it changed TWO things at once: the covering **enlargement** (closures) AND a
looser **time-capacity** (the robust arm rebuilt T_s from inflated closure line
counts, eq. 10 of pk_instance_robust). This script separates them with a 2x2 of
{nominal | closures} x {real capacity | recalibrated capacity}, placing every arm
with the SAME unmodified Hexaly model and counting visits on the SAME real orders:

    A = nominal orders,  real capacity              (baseline, k=1)
    B = closures,        real (kappa-invariant) cap (PREPROCESS-ONLY)   <- decisive
    C = closures,        recalibrated (loose) cap   (the v2 robust arm)
    D = nominal orders,  recalibrated (loose) cap   (CAPACITY-ONLY control)

Decomposition of the out-of-sample gain G (vs A), per enlargement level k:
    G(B)            = the outer-approximation's own effect
    G(C) - G(B)     = the extra from loosening capacity, with closures
    G(D)            = the capacity loosening's own effect, without closures
If G(B) <= 0 < G(C), the BERNER "win" was the capacity side-channel, not the
preprocess -- consistent with the clean ISCF negative. If G(B) > 0, the
outer-approximation genuinely helps on BERNER's structure (escalate to full scale).

Recalibration is exact and cheap: the cover is a PARTITION, so an order's closure
is the union of its products' patterns, and bar_L_p (orders whose closure contains
p) equals the popularity of p's pattern. Hexaly placement uses the real per-product
pick-lines as the kappa-invariant workload in every arm; only T_s differs B vs C.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from collections import Counter, defaultdict
from typing import Dict, FrozenSet, List, Optional, Tuple

import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)


def _supports(orders: pd.DataFrame) -> Dict[str, FrozenSet[str]]:
    return {str(o): frozenset(g) for o, g in orders.groupby("ORDER")["PRODUCT"]}


def _top_supports(order_sets: Dict[str, FrozenSet[str]], top_n: int) -> List[FrozenSet[str]]:
    cnt = Counter(s for s in order_sets.values() if len(s) >= 2)
    items = cnt.most_common(top_n) if top_n else list(cnt.items())
    return [s for s, _ in items]


def _prod2pat(patterns: List[FrozenSet[str]]) -> Dict[str, int]:
    p2p: Dict[str, int] = {}
    for j, q in enumerate(patterns):
        for p in q:
            p2p[p] = j
    return p2p


def _closure(support: FrozenSet[str], p2p: Dict[str, int],
             patterns: List[FrozenSet[str]]) -> List[str]:
    pats = {p2p[p] for p in support if p in p2p}
    out: set = set(support)
    for j in pats:
        out |= patterns[j]
    return sorted(out)


def _recalibrated_stations(
    order_sets: Dict[str, FrozenSet[str]], patterns: List[FrozenSet[str]],
    p2p: Dict[str, int], stations: List[dict], universe: List[str], slack: float,
) -> List[dict]:
    """eq. 10 recalibrated T_s from closure line counts bar_L_p (partition fast path)."""
    pat_pop = [0] * len(patterns)
    for s in order_sets.values():
        for j in {p2p[p] for p in s if p in p2p}:
            pat_pop[j] += 1
    bar_L = {p: pat_pop[p2p[p]] for p in universe if p in p2p}
    n_s = len(stations)
    recal: List[dict] = []
    for srec in stations:
        v = float(srec["SPEED"]) if float(srec["SPEED"]) > 0 else 1.0
        load = sum(bar_L.get(p, 0) / v for p in universe)
        new = dict(srec)
        new["TIME_CAPACITY"] = int(math.ceil(slack * load / n_s))
        recal.append(new)
    return recal


def _place(op: Dict[str, List[str]], stations: List[dict], products: List[str],
           prod_lines: Dict[str, int], t: int) -> Optional[Dict[str, str]]:
    import milp_synthetic as M
    res = M.run_milp_hexaly(op, stations, products, prod_lines, time_limit=t, verbosity=0)
    a = res[0]
    return {str(p): str(s) for p, s in a.items()} if a is not None else None


def _eval(layout: Dict[str, str], order_prods: Dict[str, List[str]],
          stations: List[dict], lines: Dict[str, int]) -> Tuple[int, int, int]:
    import evaluate_layout_robust as ev
    m = ev.evaluate_layout(layout, order_prods, stations, lines)
    return int(m["total_visits"]), int(m["cap_broken"]), int(m["wl_broken"])


def run(fold_dir: str, prefix: str, cover_dir: str, k_grid: List[int],
        top_supports: int, place_time: int, slack: float, out_csv: str) -> None:
    tr = pd.read_csv(os.path.join(fold_dir, f"{prefix}_train_orders.csv"), sep=";")
    te = pd.read_csv(os.path.join(fold_dir, f"{prefix}_test_orders.csv"), sep=";")
    pdf = pd.read_csv(os.path.join(fold_dir, f"{prefix}_train_products.csv"), sep=";")
    sdf = pd.read_csv(os.path.join(fold_dir, f"{prefix}_train_stations.csv"), sep=";")

    products = ("PROD_" + pdf["PRODUCT_ID"].astype(str)).tolist()
    universe = products
    prod_lines = {f"PROD_{i}": int(n) for i, n in zip(pdf["PRODUCT_ID"], pdf["REAL_LINES"])}
    real_stations = sdf.to_dict(orient="records")

    tr_sets = _supports(tr)
    tr_op = {o: list(s) for o, s in tr_sets.items()}
    te_op = te.groupby("ORDER")["PRODUCT"].apply(list).to_dict()
    tr_lines = prod_lines
    te_lines = te.groupby("PRODUCT").size().to_dict()
    base_supports = _top_supports(tr_sets, top_supports)
    print(f"[decompose] train={len(tr_op)} test={len(te_op)} |P|={len(products)} "
          f"placement_supports={len(base_supports)} stations={len(real_stations)}", flush=True)

    rows: List[Dict[str, object]] = []

    # --- Arm A: nominal orders, real capacity (k=1 baseline). ----------------
    opA = {f"D{i}": sorted(s) for i, s in enumerate(base_supports)}
    t0 = time.time()
    layA = _place(opA, real_stations, products, prod_lines, place_time)
    assert layA is not None, "Arm A (baseline) infeasible -- raise --slack"
    NA, _, _ = _eval(layA, tr_op, real_stations, tr_lines)
    VA, capA, wlA = _eval(layA, te_op, real_stations, te_lines)
    print(f"  A k=1 nominal/realcap: N={NA} V={VA} cap_br={capA} wl_br={wlA} "
          f"({time.time()-t0:.0f}s)", flush=True)
    rows.append({"k": 1, "arm": "A_baseline", "orders": "nominal", "capacity": "real",
                 "N": NA, "V": VA, "PoR_pct": 0.0, "G_pct": 0.0, "cap_broken": capA,
                 "wl_broken": wlA, "c_bar": 1.0})

    for k in k_grid:
        cpath = os.path.join(cover_dir, f"cover_{prefix}_k{k}.json")
        if not os.path.exists(cpath):
            print(f"  [skip k={k}] no cover {cpath}", flush=True)
            continue
        with open(cpath) as fh:
            payload = json.load(fh)
        patterns = [frozenset(p) for p in payload["patterns"]]
        c_bar = float(payload.get("c_bar", 0.0))
        p2p = _prod2pat(patterns)
        opC = {f"D{i}": _closure(s, p2p, patterns) for i, s in enumerate(base_supports)}
        recal_stations = _recalibrated_stations(tr_sets, patterns, p2p, real_stations,
                                                universe, slack)
        rT = recal_stations[0]["TIME_CAPACITY"]; aT = real_stations[0]["TIME_CAPACITY"]

        # B: closures, real cap (preprocess-only).
        layB = _place(opC, real_stations, products, prod_lines, place_time)
        # C: closures, recalibrated cap (v2 robust arm).
        layC = _place(opC, recal_stations, products, prod_lines, place_time)
        # D: nominal, recalibrated cap (capacity-only control).
        layD = _place(opA, recal_stations, products, prod_lines, place_time)

        for arm, lay, ordr, cap in (("B_preproc", layB, "closures", "real"),
                                    ("C_v2full", layC, "closures", "recal"),
                                    ("D_caponly", layD, "nominal", "recal")):
            if lay is None:
                print(f"  [{arm} k={k}] INFEASIBLE", flush=True)
                rows.append({"k": k, "arm": arm, "orders": ordr, "capacity": cap,
                             "N": None, "V": None, "PoR_pct": None, "G_pct": None,
                             "cap_broken": None, "wl_broken": None, "c_bar": c_bar})
                continue
            N, _, _ = _eval(lay, tr_op, real_stations, tr_lines)
            V, cb, wb = _eval(lay, te_op, real_stations, te_lines)
            por = 100.0 * (N - NA) / NA
            g = 100.0 * (VA - V) / VA
            print(f"  {arm} k={k}: N={N} V={V} PoR={por:+.2f}% G={g:+.2f}% "
                  f"cap_br={cb} wl_br={wb} (T_s {aT}->{rT if cap=='recal' else aT})",
                  flush=True)
            rows.append({"k": k, "arm": arm, "orders": ordr, "capacity": cap,
                         "N": N, "V": V, "PoR_pct": round(por, 3), "G_pct": round(g, 3),
                         "cap_broken": cb, "wl_broken": wb, "c_bar": c_bar})

    out = pd.DataFrame(rows)
    out.to_csv(out_csv, index=False)
    print(f"\n[decompose] wrote {out_csv}")
    # Headline decomposition per k.
    print("\n=== DECOMPOSITION (G vs baseline A) ===")
    print(f'{"k":>3} {"c_bar":>5} | {"G(B) preproc":>13} | {"G(C) v2full":>12} | '
          f'{"G(D) caponly":>12} | capacity_share')
    for k in k_grid:
        sub = out[out.k == k]
        gb = sub[sub.arm == "B_preproc"]["G_pct"]
        gc = sub[sub.arm == "C_v2full"]["G_pct"]
        gd = sub[sub.arm == "D_caponly"]["G_pct"]
        if len(gb) and gb.iloc[0] is not None:
            cb = float(sub["c_bar"].iloc[0])
            gbv = gb.iloc[0]; gcv = gc.iloc[0] if len(gc) else float("nan")
            gdv = gd.iloc[0] if len(gd) else float("nan")
            print(f'{k:>3} {cb:>5.2f} | {gbv:>+12.2f}% | {gcv:>+11.2f}% | {gdv:>+11.2f}% | '
                  f'{"preprocess" if gbv>0.01 else "capacity/none"}')


def main() -> None:
    p = argparse.ArgumentParser(description="BERNER preprocess-vs-capacity decomposition.")
    p.add_argument("--fold-dir", default="berner_topn")
    p.add_argument("--prefix", default="bern")
    p.add_argument("--cover-dir", default="berner_covers")
    p.add_argument("--k", nargs="+", type=int, default=[2, 3, 4, 6, 10])
    p.add_argument("--top-supports", type=int, default=4000)
    p.add_argument("--place-time", type=int, default=120)
    p.add_argument("--slack", type=float, default=1.10)
    p.add_argument("--out-csv", default="berner_decompose_result.csv")
    args = p.parse_args()
    run(args.fold_dir, args.prefix, args.cover_dir, args.k, args.top_supports,
        args.place_time, args.slack, args.out_csv)


if __name__ == "__main__":
    main()
