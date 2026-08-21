r"""Experiment harness: Bertsimas--Sim robust workload placement on iscf480-temporal.

Paired design: for each temporal fold, the SAME MILP solver (``milp_highs_robust``,
HiGHS backend) is run over a :math:`\Gamma` grid; :math:`\Gamma = 0` is the
nominal arm. Everything except :math:`\Gamma` (supports, time budget, deviations
:math:`\hat L_p`, capacities) is held fixed within a fold, so visit-price and
feasibility deltas are attributable to the budget alone.

Leakage-free calibration (planner-available data only)
-------------------------------------------------------
PRIMARY: model M3 of the feasibility study, per product —
:math:`\hat L_p = \min(\sigma_p, \bar L_p)` where :math:`\sigma_p` is the
sample std (ddof=1) of the block line counts over ``N_BLOCKS = 5`` equal
temporal blocks of the TRAIN orders (by ORDER_ID rank), each rescaled to
full-train volume (``scale_b = total_train_lines / block_total_lines``).
Per-product deviations keep stable SKUs cheap to protect and price lumpy SKUs
individually.

DIAGNOSTIC (recorded, not used): the global-c M2 fit
:math:`\hat L_p = c\sqrt{\bar L_p}` with ``c`` = the :math:`\bar L_p`-weighted
``Q_HEADLINE = 90``-th percentile of the pooled block-deviation ratios.
On iscf480 this fit DEGENERATES: temporally concentrated (lumpy) SKUs dominate
the weighted quantile (c approx 70), so with the :math:`\hat L_p \le \bar L_p`
cap the uncertainty set collapses to the full box for ~all SKUs and the robust
model is infeasible already at small :math:`\Gamma` — a calibration-practice
finding reported in the study. Both fits use only train-internal data
(deliberately different from the study's diagnostic fit on realized
train-to-test deviations, which is not available at decision time).

Metrics per (fold, gamma)
-------------------------
Train/test visits on the REAL full order sets (``evaluate_layout_robust``),
as-run wl check vs the stored train ceiling ``T_s``, volume-normalized check
(``Tn = ceil(1.10 * sum_p L_p^{te} / (V |S|))``, ``ratio_norm``, ``viol_norm``,
excess fraction ``X``, ``imbalance``), price of robustness
``PoR = (V_tr(G) - V_tr(0)) / V_tr(0)``, out-of-sample gain
``G = (V_te(0) - V_te(G)) / V_te(0)``, solver stats (objective, dual bound,
gap, runtime, status) and an arithmetic verification that the layout satisfies
the ORIGINAL (pre-dualisation) robust constraint via the sorted top-Gamma sum.
The stored Hexaly ``k=1`` layout is re-evaluated per fold as an external
reference row (``arm = hexaly_k1``).

Outputs: ``results.csv``, ``calibration.csv``, ``per_station.csv``, layout and
``lhat`` JSONs under ``reports/12_workload_feasibility/data/experiment/``.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

BASE: str = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import evaluate_layout_robust as ev  # noqa: E402
from milp_highs_robust import (  # noqa: E402
    build_supports,
    local_search_visits,
    read_data,
    robust_lhs,
    run_milp_highs,
)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from paths import DERIVED, RESULTS  # noqa: E402

SLACK: float = 1.10
N_BLOCKS: int = 5
Q_HEADLINE: float = 90.0


def weighted_quantile(values: np.ndarray, weights: np.ndarray, q: float) -> float:
    """Weighted q-th percentile (q in [0, 100]) of ``values``.

    Args:
        values: Sample values.
        weights: Nonnegative weights, same shape.
        q: Percentile in [0, 100].

    Returns:
        Smallest value v such that the weight fraction of samples <= v is >= q/100.
    """
    order = np.argsort(values)
    v, w = values[order], weights[order]
    cum = np.cumsum(w)
    cutoff = q / 100.0 * cum[-1]
    return float(v[np.searchsorted(cum, cutoff)])


def calibrate_lhat(
    train_orders: pd.DataFrame, lbar: Dict[str, float], q: float = Q_HEADLINE
) -> Tuple[Dict[str, float], float]:
    r"""Train-internal calibration: M3 block-std deviations (primary) + M2 c fit.

    PRIMARY (returned as ``lhat``): :math:`\hat L_p = \min(\sigma_p, \bar L_p)`
    with :math:`\sigma_p` the ddof=1 std of the volume-rescaled block line
    counts of product ``p`` over ``N_BLOCKS`` temporal train blocks. The cap
    :math:`\hat L_p \le \bar L_p` restricts the uncertainty interval to
    :math:`[0, 2\bar L_p]` (pick-line counts are nonnegative).

    DIAGNOSTIC (returned as ``c``): the global M2 sqrt-model coefficient, the
    :math:`\bar L_p`-weighted q-th percentile of the pooled deviation ratios
    :math:`|scale_b L_{pb} - \bar L_p| / \sqrt{\bar L_p}` — recorded to document
    its degeneracy on lumpy demand, not used to build ``lhat``.

    Args:
        train_orders: Fold train orders (columns ORDER, PRODUCT).
        lbar: Nominal pick-lines :math:`\bar L_p` (REAL_LINES).
        q: Coverage percentile for the diagnostic c fit.

    Returns:
        ``(lhat, c)``.
    """
    order_ids = train_orders["ORDER"].unique()  # file order = temporal order (U1)
    blocks = np.array_split(order_ids, N_BLOCKS)
    total_lines = float(len(train_orders))

    prods = list(lbar.keys())
    lbar_v = np.array([lbar[p] for p in prods])
    scaled_blocks: List[np.ndarray] = []
    ratios: List[np.ndarray] = []
    weights: List[np.ndarray] = []
    by_order = train_orders.set_index("ORDER")

    for block_ids in blocks:
        block_df = by_order.loc[by_order.index.isin(set(block_ids))]
        block_lines = block_df.groupby("PRODUCT").size()
        scale = total_lines / float(len(block_df)) if len(block_df) else 1.0
        scaled = np.array([scale * float(block_lines.get(p, 0.0)) for p in prods])
        scaled_blocks.append(scaled)
        mask = lbar_v > 0
        ratios.append(np.abs(scaled[mask] - lbar_v[mask]) / np.sqrt(lbar_v[mask]))
        weights.append(lbar_v[mask])

    sigma = np.std(np.vstack(scaled_blocks), axis=0, ddof=1)
    lhat = {
        p: float(min(sigma[i], lbar[p])) if lbar[p] > 0 else 0.0
        for i, p in enumerate(prods)
    }
    c = weighted_quantile(np.concatenate(ratios), np.concatenate(weights), q)
    return lhat, c


def normalized_metrics(
    assignment: Dict[str, str],
    stations: List[dict],
    te_lines: Dict[str, float],
    tr_total_lines: Optional[float] = None,
) -> Dict[str, object]:
    r"""Volume-normalized feasibility metrics of a layout on a test order set.

    Two equivalent formulations of the counterfactual ceiling:

    * **Homogeneous** (``tr_total_lines is None``, uniform speeds -- ISCF,
      exp02a): a single scalar
      :math:`T^{\mathrm n} = \lceil \sigma \sum_p L^{te}_p/(V|S|)\rceil`
      (equal fair share of the test volume).
    * **General / heterogeneous** (``tr_total_lines`` given -- BERNER, where the
      24 stations span a ~1700x speed range and carry station-specific
      ceilings): the station's OWN train ceiling rescaled to the test volume,
      :math:`T^{\mathrm n}_s = T_s \cdot \lambda`, with
      :math:`\lambda = \sum_p L^{te}_p / \sum_p L^{tr}_p`. This keeps each
      station's engineered share intact while removing the volume artifact,
      and reduces **exactly** to the homogeneous formula whenever :math:`T_s`
      itself follows the same slack rule on the train volume.

    Args:
        assignment: ``{product: station}`` layout.
        stations: Station records (train stations file, as in the as-run check).
        te_lines: Test per-product line counts.
        tr_total_lines: Total train pick-lines; switches on the per-station
            (heterogeneous-safe) ceiling. Required when speeds are not uniform.

    Returns:
        Dict with ``Tn`` (scalar summary), ``viol_norm``, ``max_ratio_norm``,
        ``imbalance``, ``X`` and the per-station loads/ratios.
    """
    speeds = {s["STATION_ID"]: float(s["SPEED"]) for s in stations}
    sids = [s["STATION_ID"] for s in stations]
    n_s = len(sids)
    total = float(sum(te_lines.values()))
    homogeneous = len(set(speeds.values())) == 1

    load: Dict[str, float] = {sid: 0.0 for sid in sids}
    for p, sid in assignment.items():
        load[sid] += te_lines.get(p, 0.0) / speeds[sid]
    loads = np.array([load[sid] for sid in sids])
    tot_w = float(loads.sum())

    if tr_total_lines is None:
        assert homogeneous, (
            "heterogeneous station speeds require tr_total_lines (per-station "
            "ceiling T_s * lambda); pass it explicitly"
        )
        v0 = speeds[sids[0]]
        tn_arr = np.full(n_s, float(math.ceil(SLACK * total / (v0 * n_s))))
        imbalance = float(loads.max() / tot_w * n_s) if tot_w > 0 else 0.0
    else:
        lam = total / float(tr_total_lines) if tr_total_lines else 1.0
        tn_arr = np.array([float(s["TIME_CAPACITY"]) * lam for s in stations])
        # Peak load relative to the station's own no-slack share; reduces to the
        # homogeneous max/mean ratio when every T_s is the same slack rule.
        shares = tn_arr / SLACK
        imbalance = float(np.max(loads / np.where(shares > 0, shares, np.inf)))

    ratios = loads / np.where(tn_arr > 0, tn_arr, np.inf)
    return {
        "Tn": float(tn_arr[0]) if homogeneous else float(np.median(tn_arr)),
        "viol_norm": int(np.sum(loads > tn_arr)),
        "max_ratio_norm": float(ratios.max()),
        "imbalance": imbalance,
        "X": (float(np.sum(np.maximum(loads - tn_arr, 0.0)) / tot_w)
              if tot_w > 0 else 0.0),
        "station_loads": {sid: float(load[sid]) for sid in sids},
        "station_ratios": {sid: float(r) for sid, r in zip(sids, ratios)},
    }


def polish_with_ls(
    assignment: Dict[str, str],
    tr_op: Dict[str, List[str]],
    stations: List[dict],
    products: List[str],
    lbar: Dict[str, float],
    lhat: Optional[Dict[str, float]],
    gamma: float,
    ls_time: float,
    top_n: int,
) -> Tuple[Dict[str, str], float]:
    """LS-polish a feasible layout (e.g. from a HiGHS probe) for paired quality.

    Args:
        assignment: Feasible ``{product: station}`` layout.
        tr_op: Train orders.
        stations: Station records used in TRAINING (ceiling of the arm).
        products: Product tokens.
        lbar: Nominal pick-lines.
        lhat: Deviations (None for gamma == 0).
        gamma: Budget.
        ls_time: LS seconds.
        top_n: Supports in the objective.

    Returns:
        ``(improved_assignment, weighted_visit_objective)``.
    """
    supports = build_supports(tr_op, top_n)
    p_idx = {p: i for i, p in enumerate(products)}
    station_ids = [s["STATION_ID"] for s in stations]
    sid_idx = {sid: i for i, sid in enumerate(station_ids)}
    speeds = np.array([float(s["SPEED"]) for s in stations])
    time_caps = np.array([float(s["TIME_CAPACITY"]) for s in stations])
    lbar_v = np.array([lbar.get(p, 0.0) for p in products])
    lhat_v = (
        np.array([float(lhat.get(p, 0.0)) for p in products])
        if lhat is not None
        else np.zeros(len(products))
    )
    assign0 = np.array([sid_idx[assignment[p]] for p in products])
    caps_v = np.array([float(s["CAPACITY"]) for s in stations])
    improved = local_search_visits(
        assign0, supports, p_idx, lbar_v, lhat_v, speeds, time_caps,
        int(round(gamma)), time_budget=ls_time, caps=caps_v,
    )
    n_s = len(stations)
    cnt = np.zeros((len(supports), n_s), dtype=np.int16)
    for o, (support, _w) in enumerate(supports):
        for prod in support:
            i = p_idx.get(prod)
            if i is not None:
                cnt[o, improved[i]] += 1
    w = np.array([wt for _, wt in supports], dtype=float)
    obj = float(np.sum(w * (cnt > 0).sum(axis=1)))
    print(f"[polish_with_ls] gamma={gamma} polished obj={obj:.0f}", flush=True)
    return (
        {products[i]: station_ids[improved[i]] for i in range(len(products))},
        obj,
    )


def eval_arm(
    assignment: Dict[str, str],
    tr_op: Dict[str, List[str]],
    te_op: Dict[str, List[str]],
    tr_lines: Dict[str, float],
    te_lines: Dict[str, float],
    stations: List[dict],
) -> Dict[str, object]:
    """Train+test evaluation of one layout (visits, as-run and normalized checks)."""
    m_tr = ev.evaluate_layout(assignment, tr_op, stations, tr_lines)
    m_te = ev.evaluate_layout(assignment, te_op, stations, te_lines)
    # Heterogeneous stations (BERNER) need the per-station ceiling T_s * lambda;
    # uniform-speed instances keep the original scalar formula byte-for-byte.
    heterogeneous = len({float(s["SPEED"]) for s in stations}) > 1
    nm = normalized_metrics(
        assignment, stations, te_lines,
        tr_total_lines=float(sum(tr_lines.values())) if heterogeneous else None,
    )
    return {
        "V_tr": m_tr["total_visits"],
        "V_te": m_te["total_visits"],
        "cap_broken": m_te["cap_broken"],
        "wl_broken_asrun": m_te["wl_broken"],
        "max_workload_te": m_te["max_workload"],
        "Tn": nm["Tn"],
        "viol_norm": nm["viol_norm"],
        "max_ratio_norm": nm["max_ratio_norm"],
        "imbalance": nm["imbalance"],
        "X": nm["X"],
        "station_ratios": nm["station_ratios"],
    }


def main() -> None:
    """Run the Gamma-sweep experiment (CLI)."""
    parser = argparse.ArgumentParser(
        description="Bertsimas-Sim robust workload experiment (iscf480 temporal)"
    )
    parser.add_argument("--prefix", type=str, default="iscf480")
    parser.add_argument("--dir", type=str,
                        default=os.path.join(DERIVED, "iscf_folds_temporal"))
    parser.add_argument("--layouts-dir", type=str,
                        default=os.path.join(DERIVED, "iscf_layouts_temporal"))
    parser.add_argument("--time", type=int, default=150)
    parser.add_argument("--folds", type=str, default="0,1,2,3,4")
    parser.add_argument("--gammas", type=str, default="0,1,2,3,4,6,8")
    parser.add_argument("--betas", type=str, default="1.05,1.02",
                        help="Tightened-nominal competitor arms: train with "
                             "T_s(beta)=ceil(beta*sum(Lbar)/(V*|S|)), Gamma=0")
    parser.add_argument("--lhat-scale", type=float, default=1.0,
                        help="Partial-insurance factor alpha: protect against "
                             "alpha*Lhat_p (full-sigma protection does not fit "
                             "the 10%% slack contract on iscf480)")
    parser.add_argument("--topn", type=int, default=3000)
    parser.add_argument("--ls-time", type=float, default=45.0,
                        help="Local-search seconds before the MILP polish")
    parser.add_argument("--probe-time", type=int, default=180,
                        help="HiGHS feasibility-probe seconds when the "
                             "constructive pipeline finds no layout")
    parser.add_argument("--backend", type=str, default="highs",
                        choices=["highs", "cplex"],
                        help="MILP backend for the placement solve/polish. "
                             "'cplex' (docplex) is exact -> removes the HiGHS "
                             "symmetry-stall gap; everything else is identical.")
    parser.add_argument("--out", type=str,
                        default=os.path.join(RESULTS, "experiment"))
    args = parser.parse_args()

    # Backend dispatch: rebinding the solver name routes ALL four solve sites
    # (gamma main/probe, beta main/probe) to CPLEX with zero other changes, so
    # the two backends are paired arm-for-arm on identical inputs.
    run_milp_highs = globals()["run_milp_highs"]  # bind name into local scope
    if args.backend == "cplex":
        from milp_cplex_robust import run_milp_cplex
        run_milp_highs = run_milp_cplex
    print(f"[run_bs_robust_experiment] backend={args.backend}", flush=True)

    folds = [int(f) for f in args.folds.split(",")]
    gammas = [int(g) for g in args.gammas.split(",")]
    betas = (
        [float(b) for b in args.betas.split(",")]
        if args.betas and args.betas.lower() not in ("", "-", "none")
        else []
    )
    assert 0 in gammas, "--gammas must include 0 (the paired nominal base arm)"
    os.makedirs(args.out, exist_ok=True)
    layouts_out = os.path.join(args.out, "layouts")
    os.makedirs(layouts_out, exist_ok=True)

    rows: List[Dict[str, object]] = []
    cal_rows: List[Dict[str, object]] = []
    st_rows: List[Dict[str, object]] = []

    def persist() -> None:
        """Crash-safe incremental persistence (after every arm)."""
        pd.DataFrame(rows).to_csv(os.path.join(args.out, "results.csv"), index=False)
        pd.DataFrame(cal_rows).to_csv(
            os.path.join(args.out, "calibration.csv"), index=False
        )
        pd.DataFrame(st_rows).to_csv(
            os.path.join(args.out, "per_station.csv"), index=False
        )

    for f in folds:
        tag = f"{args.prefix}_r0f{f}"
        tr_prefix, te_prefix = f"{tag}_train", f"{tag}_test"
        tr_op, stations, products, lbar = read_data(tr_prefix, args.dir)
        tr_orders = pd.read_csv(
            os.path.join(args.dir, f"{tr_prefix}_orders.csv"), sep=";"
        )
        te_orders = pd.read_csv(
            os.path.join(args.dir, f"{te_prefix}_orders.csv"), sep=";"
        )
        te_op = te_orders.groupby("ORDER")["PRODUCT"].apply(list).to_dict()
        tr_lines = tr_orders.groupby("PRODUCT").size().astype(float).to_dict()
        te_lines = te_orders.groupby("PRODUCT").size().astype(float).to_dict()
        t_s = float(stations[0]["TIME_CAPACITY"])

        # Industrial folds carry the incumbent layout (WARM_STATION); using it
        # as the construction seed is required there, since the ceilings are
        # calibrated ON that layout (a from-scratch greedy can miss the only
        # feasible region and report a false infeasibility).
        tr_products_df = pd.read_csv(
            os.path.join(args.dir, f"{tr_prefix}_products.csv"), sep=";")
        warm_start = None
        if "WARM_STATION" in tr_products_df.columns:
            cand = {
                f"PROD_{pid}": str(sid)
                for pid, sid in zip(tr_products_df["PRODUCT_ID"],
                                    tr_products_df["WARM_STATION"])
                if pd.notna(sid) and str(sid)
            }
            # Guard: a partial seed would silently dump the unmapped products
            # onto one station. Use it only if it covers the whole catalogue.
            if len(cand) == len(tr_products_df):
                warm_start = cand
                print(f"[fold {f}] warm start: {len(warm_start)} products seeded",
                      flush=True)
            else:
                print(f"[fold {f}] WARM_STATION covers {len(cand)}/"
                      f"{len(tr_products_df)} products -> IGNORED (greedy start)",
                      flush=True)

        lhat, c_fit = calibrate_lhat(tr_orders, lbar)
        alpha = float(args.lhat_scale)
        suffix = f"_a{alpha:g}" if alpha != 1.0 else ""
        if alpha != 1.0:
            lhat = {p: alpha * v for p, v in lhat.items()}
        with open(os.path.join(args.out, f"lhat_{tag}{suffix}.json"), "w") as fh:
            json.dump(lhat, fh)
        lhat_v = np.array(sorted(lhat.values(), reverse=True))
        cal_rows.append({
            "fold": f, "c_fit_q90": c_fit, "T_s": t_s, "lhat_scale": alpha,
            "lhat_max": float(lhat_v[0]), "lhat_top8_sum": float(lhat_v[:8].sum()),
            "lhat_total": float(lhat_v.sum()),
            "n_train_orders": len(tr_op), "n_test_orders": len(te_op),
        })
        print(f"[fold {f}] c_q90={c_fit:.3f} T_s={t_s:.0f} "
              f"lhat_max={lhat_v[0]:.1f}", flush=True)

        base_v_tr: Optional[float] = None
        base_v_te: Optional[float] = None

        for gamma in gammas:
            t0 = time.time()
            assignment, obj, elapsed, _uv, _mu, cb, wb, bound = run_milp_highs(
                tr_op, stations, products, lbar,
                lhat=lhat if gamma > 0 else None, gamma=float(gamma),
                time_limit=args.time, top_n=args.topn, mip_rel_gap=0.005,
                ls_time=args.ls_time, start_assignment=warm_start, verbose=True,
            )
            if assignment is None and args.time <= 0:
                # Greedy start failed in metaheuristic-only mode: let HiGHS
                # decide whether this Gamma is genuinely infeasible.
                print(f"[fold {f} gamma={gamma}] greedy failed -> HiGHS "
                      f"feasibility probe ({args.probe_time}s)", flush=True)
                assignment, obj, elapsed, _uv, _mu, cb, wb, bound = run_milp_highs(
                    tr_op, stations, products, lbar,
                    lhat=lhat if gamma > 0 else None, gamma=float(gamma),
                    time_limit=args.probe_time, top_n=args.topn,
                    mip_rel_gap=0.005, ls_time=0.0, verbose=True,
                )
                if assignment is not None:
                    # Probe found a feasible layout: LS-polish it so the arm's
                    # visit quality is comparable (paired) with greedy+LS arms.
                    assignment, obj = polish_with_ls(
                        assignment, tr_op, stations, products, lbar,
                        lhat if gamma > 0 else None, float(gamma),
                        ls_time=args.ls_time, top_n=args.topn,
                    )
            arm_name = "gamma0" if gamma == 0 else f"gamma{gamma}{suffix}"
            row: Dict[str, object] = {
                "fold": f, "arm": arm_name, "gamma": gamma, "alpha": alpha,
                "solver_obj": obj, "solver_bound": bound,
                "solver_gap": (obj - bound) / obj if obj not in (0.0, float("inf")) else np.nan,
                "solve_time": elapsed, "feasible_model": assignment is not None,
                "c_fit_q90": c_fit,
            }
            if assignment is None:
                row["proven_infeasible"] = bool(np.isinf(bound))
                rows.append(row)
                persist()
                verdict = "PROVEN infeasible" if row["proven_infeasible"] \
                    else "UNDETERMINED (no incumbent in limit)"
                print(f"[fold {f} gamma={gamma}] {verdict}", flush=True)
                continue

            with open(os.path.join(layouts_out,
                                   f"layout_{tag}_g{gamma}{suffix}.json"), "w") as fh:
                json.dump(assignment, fh)

            m = eval_arm(assignment, tr_op, te_op, tr_lines, te_lines, stations)
            station_ratios = m.pop("station_ratios")
            row.update(m)

            # Verify the ORIGINAL robust constraint arithmetically (top-Gamma
            # sum), per station against that station's own ceiling.
            lhs = robust_lhs(assignment, stations, lbar, lhat, gamma)
            tcaps = {s["STATION_ID"]: float(s["TIME_CAPACITY"]) for s in stations}
            row["robust_lhs_max"] = max(lhs.values())
            row["robust_ok"] = bool(
                all(lhs[sid] <= tcaps[sid] + 1e-6 for sid in lhs)
            )

            if gamma == 0:
                base_v_tr, base_v_te = float(m["V_tr"]), float(m["V_te"])
            row["PoR_pct"] = (
                100.0 * (m["V_tr"] - base_v_tr) / base_v_tr
                if base_v_tr else np.nan
            )
            row["G_pct"] = (
                100.0 * (base_v_te - m["V_te"]) / base_v_te
                if base_v_te else np.nan
            )
            rows.append(row)
            for sid, ratio in station_ratios.items():
                st_rows.append({
                    "fold": f, "arm": arm_name, "gamma": gamma,
                    "station": sid, "ratio_norm": ratio,
                })
            persist()
            print(f"[fold {f} gamma={gamma}] V_tr={m['V_tr']} V_te={m['V_te']} "
                  f"PoR={row['PoR_pct']:.2f}% G={row['G_pct']:.2f}% "
                  f"viol_norm={m['viol_norm']} max_ratio={m['max_ratio_norm']:.2f} "
                  f"robust_ok={row['robust_ok']} ({time.time() - t0:.0f}s)", flush=True)

        # Tightened-nominal competitor arms: uniform slack reduction instead of
        # targeted budgeted protection; trained with T_s(beta), evaluated on the
        # SAME 1.10-rule contract as every other arm.
        total_lbar = float(sum(lbar.values()))
        speed0 = float(stations[0]["SPEED"])
        n_st = len(stations)
        for beta in betas:
            t_beta = math.ceil(beta * total_lbar / (speed0 * n_st))
            stations_beta = [dict(s, TIME_CAPACITY=t_beta) for s in stations]
            assignment, obj, elapsed, _uv, _mu, cb, wb, bound = run_milp_highs(
                tr_op, stations_beta, products, lbar,
                lhat=None, gamma=0.0,
                time_limit=args.time, top_n=args.topn, mip_rel_gap=0.005,
                ls_time=args.ls_time, start_assignment=warm_start, verbose=True,
            )
            if assignment is None and args.time <= 0:
                print(f"[fold {f} beta={beta}] greedy failed -> HiGHS "
                      f"feasibility probe (180s)", flush=True)
                assignment, obj, elapsed, _uv, _mu, cb, wb, bound = run_milp_highs(
                    tr_op, stations_beta, products, lbar,
                    lhat=None, gamma=0.0,
                    time_limit=180, top_n=args.topn, mip_rel_gap=0.005,
                    ls_time=0.0, verbose=True,
                )
            row = {
                "fold": f, "arm": f"tight{beta}", "gamma": np.nan,
                "beta": beta, "T_s_train": t_beta,
                "solver_obj": obj, "solver_bound": bound,
                "solve_time": elapsed, "feasible_model": assignment is not None,
                "c_fit_q90": c_fit,
            }
            if assignment is None:
                rows.append(row)
                persist()
                print(f"[fold {f} beta={beta}] INFEASIBLE", flush=True)
                continue
            with open(os.path.join(layouts_out,
                                   f"layout_{tag}_b{beta}.json"), "w") as fh:
                json.dump(assignment, fh)
            m = eval_arm(assignment, tr_op, te_op, tr_lines, te_lines, stations)
            station_ratios = m.pop("station_ratios")
            row.update(m)
            row["PoR_pct"] = (
                100.0 * (m["V_tr"] - base_v_tr) / base_v_tr if base_v_tr else np.nan
            )
            row["G_pct"] = (
                100.0 * (base_v_te - m["V_te"]) / base_v_te if base_v_te else np.nan
            )
            rows.append(row)
            for sid, ratio in station_ratios.items():
                st_rows.append({
                    "fold": f, "arm": f"tight{beta}", "gamma": np.nan,
                    "station": sid, "ratio_norm": ratio,
                })
            persist()
            print(f"[fold {f} beta={beta}] V_tr={m['V_tr']} V_te={m['V_te']} "
                  f"PoR={row['PoR_pct']:.2f}% G={row['G_pct']:.2f}% "
                  f"viol_norm={m['viol_norm']} "
                  f"max_ratio={m['max_ratio_norm']:.2f}", flush=True)

        # External reference: stored Hexaly k=1 layout.
        hex_path = os.path.join(args.layouts_dir, f"layout_{tag}_k1.json")
        if os.path.exists(hex_path):
            with open(hex_path) as fh:
                hex_layout = json.load(fh)
            m = eval_arm(hex_layout, tr_op, te_op, tr_lines, te_lines, stations)
            station_ratios = m.pop("station_ratios")
            row = {
                "fold": f, "arm": "hexaly_k1", "gamma": np.nan, "c_fit_q90": c_fit,
                "feasible_model": True,
            }
            row.update(m)
            row["PoR_pct"] = (
                100.0 * (m["V_tr"] - base_v_tr) / base_v_tr if base_v_tr else np.nan
            )
            row["G_pct"] = (
                100.0 * (base_v_te - m["V_te"]) / base_v_te if base_v_te else np.nan
            )
            rows.append(row)
            for sid, ratio in station_ratios.items():
                st_rows.append({
                    "fold": f, "arm": "hexaly_k1", "gamma": np.nan,
                    "station": sid, "ratio_norm": ratio,
                })

        persist()

    print(f"[run_bs_robust_experiment] DONE: {len(rows)} rows -> {args.out}", flush=True)


if __name__ == "__main__":
    main()
