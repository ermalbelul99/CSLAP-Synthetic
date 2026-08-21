r"""CPLEX (docplex) backend for the Bertsimas--Sim robust CSLAP placement MILP.

Drop-in twin of ``milp_highs_robust.run_milp_highs``: identical model
(Proposition 1 of ``reports/12_workload_feasibility/tex/section_theory.tex``),
identical warm start (feasibility greedy + deterministic visit local search,
imported verbatim from ``milp_highs_robust``), identical return contract. Only
the MILP solve swaps HiGHS -> CPLEX so the two backends can be compared
arm-for-arm on the SAME instance/fold/gamma with everything else held fixed.

Why an exact solver here: on the identical stations of the ISCF cells HiGHS
stalls on symmetry and returns a ~30% dual-bound gap (report, Section 5.4), so
the reported PoR/G rest on the metaheuristic incumbent. CPLEX either closes that
gap or confirms the metaheuristic was already good -- either way it removes the
"incumbent quality" caveat from the second-instance replication test.

Model (same symbols as the HiGHS twin)
--------------------------------------
.. math::
    \min \sum_{o} w_o \sum_s y_{os}
    \;\; s.t. \;\;
    \sum_s x_{ps}=1,\;\; y_{os}\ge x_{ps},\;\; \sum_p x_{ps}\le C_s,
.. math::
    \sum_p \tfrac{\bar L_p}{V_s} x_{ps} + \Gamma\theta_s + \sum_p \mu_{ps} \le T_s,
    \qquad \theta_s + \mu_{ps} \ge \tfrac{\hat L_p}{V_s} x_{ps}.

CLI mirrors ``milp_highs_robust``:
    python milp_cplex_robust.py --prefix iscf480_r0f0_train --dir <folds>
        --time 150 --gamma 8 --lhat-json lhat.json --out layout.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Dict, List, Optional, Tuple

import numpy as np

# Reuse the EXACT shared pipeline (data, supports, warm start, verification).
from milp_highs_robust import (
    build_supports,
    greedy_start,
    local_search_visits,
    read_data,
    robust_lhs,
)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from paths import ISCF_INSTANCES  # noqa: E402


def _obj_of(
    assign_vec: np.ndarray,
    supports: List[Tuple[Tuple[str, ...], int]],
    p_idx: Dict[str, int],
    n_s: int,
) -> float:
    """Support-weighted visit objective of an assignment (same as the HiGHS twin)."""
    n_o = len(supports)
    weights = np.array([w for _, w in supports], dtype=float)
    cnt = np.zeros((n_o, n_s), dtype=np.int16)
    for o, (support, _w) in enumerate(supports):
        for prod in support:
            i = p_idx.get(prod)
            if i is not None:
                cnt[o, assign_vec[i]] += 1
    return float(np.sum(weights * (cnt > 0).sum(axis=1)))


def run_milp_cplex(
    order_prods: Dict[str, List[str]],
    stations: List[dict],
    products: List[str],
    prod_lines: Dict[str, float],
    lhat: Optional[Dict[str, float]] = None,
    gamma: float = 0.0,
    time_limit: int = 120,
    top_n: int = 3000,
    mip_rel_gap: float = 0.0,
    ls_time: float = 45.0,
    start_assignment: Optional[Dict[str, str]] = None,
    verbose: bool = True,
    threads: int = 0,
) -> Tuple[Optional[Dict[str, str]], float, float, float, float, int, int, float]:
    r"""Solve the (robust) placement MILP with CPLEX, warm started.

    Returns the project-standard tuple ``(assignment, total_visits, elapsed,
    util_variance, max_util, cap_broken, wl_broken, best_bound)``. Conventions
    match ``run_milp_highs`` exactly: ``assignment=None`` and ``best_bound=+inf``
    signal PROVEN infeasibility; ``assignment=None`` with a finite/nan bound is a
    no-incumbent timeout (undetermined-within-budget).
    """
    from docplex.mp.model import Model  # lazy: only needed on the CPLEX path

    if gamma > 0 and lhat is None:
        raise ValueError("gamma > 0 requires lhat deviations")
    gamma_i = int(round(gamma))

    t0 = time.time()
    supports = build_supports(order_prods, top_n)
    n_p, n_s, n_o = len(products), len(stations), len(supports)
    p_idx = {p: i for i, p in enumerate(products)}
    station_ids = [s["STATION_ID"] for s in stations]
    speeds = np.array([float(s["SPEED"]) for s in stations])
    caps = np.array([float(s["CAPACITY"]) for s in stations])
    time_caps = np.array([float(s["TIME_CAPACITY"]) for s in stations])
    lbar = np.array([prod_lines.get(p, 0.0) for p in products])
    lhat_v = (
        np.array([float(lhat.get(p, 0.0)) for p in products])
        if gamma_i > 0
        else np.zeros(n_p)
    )
    use_dual = gamma_i > 0
    weights = np.array([w for _, w in supports], dtype=float)

    # ---- warm start (identical to the HiGHS twin) ------------------------
    t_build0 = time.time()
    # Seeding matters wherever the ceilings were calibrated ON an existing
    # layout: a from-scratch greedy can miss the only feasible region and
    # report an infeasibility that is an artefact of the construction order.
    init_arr = None
    if start_assignment is not None:
        sid_pos = {sid: i for i, sid in enumerate(station_ids)}
        init_arr = np.array([
            sid_pos.get(start_assignment.get(p, station_ids[0]), 0)
            for p in products
        ], dtype=int)
    assign0, start_feasible = greedy_start(
        products, lbar, lhat_v, speeds, caps, time_caps, gamma_i,
        init_assign=init_arr,
    )
    if start_feasible and ls_time > 0:
        best_assign, best_obj = assign0, _obj_of(assign0, supports, p_idx, n_s)
        for seed in range(3):
            cand = local_search_visits(
                assign0, supports, p_idx, lbar, lhat_v, speeds, time_caps,
                gamma_i, time_budget=ls_time, seed=seed, caps=caps,
            )
            obj_c = _obj_of(cand, supports, p_idx, n_s)
            if obj_c < best_obj:
                best_obj, best_assign = obj_c, cand
        assign0 = best_assign
    start_obj = _obj_of(assign0, supports, p_idx, n_s) if start_feasible else float("inf")
    t_warm = time.time() - t_build0

    # ---- build CPLEX model ----------------------------------------------
    m = Model(name=f"bs_robust_g{gamma_i}")
    m.context.cplex_parameters.threads = int(threads)  # 0 = CPLEX default
    x = m.binary_var_matrix(range(n_p), range(n_s), name="x")
    y = m.continuous_var_matrix(range(n_o), range(n_s), lb=0, ub=1, name="y")
    th = m.continuous_var_list(n_s, lb=0, name="th") if use_dual else None
    mu = (
        m.continuous_var_matrix(range(n_p), range(n_s), lb=0, name="mu")
        if use_dual else None
    )

    # (1) assignment
    m.add_constraints(m.sum(x[p, s] for s in range(n_s)) == 1 for p in range(n_p))
    # (2) visit linking (disaggregated)
    m.add_constraints(
        y[o, s] >= x[p_idx[prod], s]
        for o, (support, _w) in enumerate(supports)
        for prod in support if prod in p_idx
        for s in range(n_s)
    )
    # (3) slot capacity
    m.add_constraints(
        m.sum(x[p, s] for p in range(n_p)) <= caps[s] for s in range(n_s)
    )
    # (4) robust workload row  (+ Gamma*theta + sum mu when robust)
    for s in range(n_s):
        expr = m.sum((lbar[p] / speeds[s]) * x[p, s] for p in range(n_p))
        if use_dual:
            expr = expr + gamma_i * th[s] + m.sum(mu[p, s] for p in range(n_p))
        m.add_constraint(expr <= time_caps[s])
    # (5) dual feasibility (skip vacuous hat L_p = 0 rows, as in the HiGHS twin)
    if use_dual:
        m.add_constraints(
            th[s] + mu[p, s] >= (lhat_v[p] / speeds[s]) * x[p, s]
            for p in range(n_p) if lhat_v[p] > 0.0
            for s in range(n_s)
        )

    m.minimize(m.sum(weights[o] * y[o, s] for o in range(n_o) for s in range(n_s)))

    # ---- MIP start from the warm incumbent ------------------------------
    if start_feasible:
        warm = m.new_solution()
        for p in range(n_p):
            warm.add_var_value(x[p, int(assign0[p])], 1.0)
        if use_dual:
            for s in range(n_s):
                a_vals = sorted(
                    (lhat_v[p] / speeds[s] for p in range(n_p) if assign0[p] == s),
                    reverse=True,
                )
                theta = a_vals[gamma_i - 1] if len(a_vals) >= gamma_i else 0.0
                warm.add_var_value(th[s], theta)
                for p in range(n_p):
                    if assign0[p] == s:
                        warm.add_var_value(
                            mu[p, s], max(0.0, lhat_v[p] / speeds[s] - theta)
                        )
        m.add_mip_start(warm)

    m.parameters.timelimit = float(time_limit)
    m.parameters.mip.tolerances.mipgap = float(mip_rel_gap)
    t_build = time.time() - t_build0 - t_warm

    if verbose:
        print(
            f"[milp_cplex_robust] gamma={gamma_i} vars~{n_p * n_s + n_o * n_s} "
            f"start_obj={start_obj:.0f} start_feasible={start_feasible} "
            f"warm={t_warm:.1f}s build={t_build:.1f}s",
            flush=True,
        )

    sol = m.solve(log_output=False)
    sd = m.solve_details
    status = (sd.status or "").lower()
    best_bound = (
        float(sd.best_bound) if sd.best_bound is not None else float("nan")
    )
    elapsed = time.time() - t0

    def _diag(assign_idx: np.ndarray):
        station_load = np.zeros(n_s)
        station_cnt = np.zeros(n_s)
        for p in range(n_p):
            s = int(assign_idx[p])
            station_load[s] += lbar[p] / speeds[s]
            station_cnt[s] += 1
        return (
            float(np.var(station_load / time_caps)),
            float(np.max(station_load / time_caps)),
            int(np.sum(station_cnt > caps)),
            int(np.sum(station_load > time_caps)),
        )

    if sol is None:
        if "infeasible" in status:
            print(f"[milp_cplex_robust] gamma={gamma_i} MODEL INFEASIBLE (proven) "
                  f"status='{status}' elapsed={elapsed:.1f}s", flush=True)
            m.end()
            return None, float("inf"), elapsed, 0.0, 0.0, 0, 0, float("inf")
        if start_feasible:
            # timeout, no CPLEX incumbent -> fall back to the warm start (paired).
            uv, mu_, cb, wb = _diag(assign0)
            assignment = {products[p]: station_ids[int(assign0[p])] for p in range(n_p)}
            print(f"[milp_cplex_robust] gamma={gamma_i} NO CPLEX incumbent "
                  f"(status='{status}') -> warm start obj={start_obj:.0f} "
                  f"elapsed={elapsed:.1f}s", flush=True)
            m.end()
            return assignment, start_obj, elapsed, uv, mu_, cb, wb, best_bound
        print(f"[milp_cplex_robust] gamma={gamma_i} NO incumbent and greedy "
              f"infeasible (status='{status}') elapsed={elapsed:.1f}s", flush=True)
        m.end()
        return None, float("inf"), elapsed, 0.0, 0.0, 0, 0, best_bound

    xval = sol.get_value_dict(x, keep_zeros=False)
    assign_idx = np.zeros(n_p, dtype=int)
    for p in range(n_p):
        best_s, best_v = 0, -1.0
        for s in range(n_s):
            v = xval.get((p, s), 0.0)
            if v > best_v:
                best_v, best_s = v, s
        assign_idx[p] = best_s
    assignment = {products[p]: station_ids[assign_idx[p]] for p in range(n_p)}
    total_visits = float(sol.objective_value)
    uv, mu_, cb, wb = _diag(assign_idx)

    if verbose:
        gap = (total_visits - best_bound) / total_visits if total_visits else np.nan
        print(f"[milp_cplex_robust] gamma={gamma_i} obj={total_visits:.0f} "
              f"bound={best_bound:.1f} gap={100 * gap:.2f}% status='{status}' "
              f"elapsed={elapsed:.1f}s cap_broken={cb} wl_broken={wb}", flush=True)
    m.end()
    return assignment, total_visits, elapsed, uv, mu_, cb, wb, best_bound


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Bertsimas-Sim robust CSLAP placement MILP (CPLEX/docplex)"
    )
    parser.add_argument("--prefix", type=str, required=True)
    parser.add_argument("--dir", type=str, default=ISCF_INSTANCES)
    parser.add_argument("--time", type=int, default=120)
    parser.add_argument("--gamma", type=float, default=0.0)
    parser.add_argument("--lhat-json", type=str, default=None)
    parser.add_argument("--topn", type=int, default=3000)
    parser.add_argument("--out", type=str, default=None)
    args = parser.parse_args()

    ops, sts, prods, lines = read_data(args.prefix, args.dir)
    lh = None
    if args.lhat_json:
        with open(args.lhat_json) as fh:
            lh = {k: float(v) for k, v in json.load(fh).items()}
    result = run_milp_cplex(
        ops, sts, prods, lines, lhat=lh, gamma=args.gamma, time_limit=args.time,
        top_n=args.topn,
    )
    if result[0] is not None and args.out:
        with open(args.out, "w") as fh:
            json.dump(result[0], fh)
        print(f"[milp_cplex_robust] layout written to {args.out}", flush=True)
