r"""Hexaly backend for the daily workload-feasibility study.

Two deliberate differences from :mod:`milp_cplex_robust`, both requested and
both documented here because they change what the arm means.

**1. Scenario-exact per-day workload rows (assumption A1).**
The CPLEX/HiGHS twin imposes one workload row per station,

.. math:: \sum_p \bar L_p / V_s \, x_{ps} \le T_s ,

where :math:`\bar L_p` is a per-*day mean* (``daily_folds.py``: ``lbar =
tr_lines / tr_days``) while :math:`T_s` is a *max*-day ceiling
(``_ceiling_from_loads``). A mean-day load compared against a max-day ceiling
does not constrain any real day, and the optimised layouts consequently broke
the daily ceiling on 53-92% of their own training days while the model reported
them feasible. This backend instead imposes one row per (station, training day)
using that day's *actual* lines:

.. math:: \sum_p L_{pd} / V_s \, x_{ps} + \Gamma\theta_s + \sum_p \mu_{ps}
          \le T_s \quad \forall d .

Units match ``_ceiling_from_loads`` exactly: it sets
:math:`T_s = q_d(\text{lines}_{sd}) / V_s`, so at ``q=max`` the incumbent
satisfies every row by construction, which makes the incumbent-vs-optimised
comparison well posed rather than tautological in the wrong direction.

**2. Hexaly cannot prove infeasibility.**
It is a local-search solver. ``HxSolutionStatus.INCONSISTENT`` means the model
was *proved* contradictory and is mapped to the project's proven-infeasible
convention (``best_bound = +inf``). ``INFEASIBLE`` means only that no feasible
solution was found within the budget and is mapped to *undetermined*
(``best_bound = nan``). No row may claim a proven infeasibility that Hexaly did
not actually prove.

The warm start is used directly rather than being passed through
``greedy_start``/``local_search_visits``: those repair against the mean-day
notion of feasibility this module exists to replace, so running them would
reintroduce the defect at the seed. ``ls_time`` is therefore accepted and
ignored, and that is reported in the log line.
"""

from __future__ import annotations

import os
import sys
import time
from typing import Dict, List, Optional, Tuple

import numpy as np

# Reuse the EXACT shared pipeline for supports and objective accounting so the
# visit objective is comparable arm-for-arm with the CPLEX twin.
from milp_highs_robust import build_supports

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _visits_of(assign_vec, supports, p_idx, n_s) -> float:
    """Support-weighted visit objective (identical to the CPLEX twin)."""
    n_o = len(supports)
    weights = np.array([w for _, w in supports], dtype=float)
    cnt = np.zeros((n_o, n_s), dtype=np.int16)
    for o, (support, _w) in enumerate(supports):
        for prod in support:
            i = p_idx.get(prod)
            if i is not None:
                cnt[o, assign_vec[i]] += 1
    return float(np.sum(weights * (cnt > 0).sum(axis=1)))


def run_milp_hexaly(
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
    daily_lines: Optional[np.ndarray] = None,
    day_allowance: int = 0,
) -> Tuple[Optional[Dict[str, str]], float, float, float, float, int, int, float]:
    r"""Solve the (robust) placement model with Hexaly, scenario-exact per day.

    Args:
        daily_lines: ``(n_days, n_products)`` matrix of realised training-day
            line counts, column-aligned to ``products``. When ``None`` the
            module falls back to the single mean-day row and says so, so a
            missing matrix can never masquerade as a per-day solve.
        day_allowance: How many training days may breach the ceiling
            (*coverage* semantics for assumption A2). ``0`` requires every
            observed day to fit. A positive value admits that many days,
            chosen by the solver, via one indicator per day.

            This exists because holding :math:`T_s` at a sub-max quantile while
            demanding that *every* day fit is provably infeasible: the ceiling
            is itself a quantile of observed daily loads, so
            :math:`\sum_s T_s V_s < \max_d \sum_p L_{pd}` at ``q<max`` and no
            assignment can fit the busiest day. Sweeping coverage instead of
            ceiling height keeps the sensitivity axis well posed and keeps the
            incumbent feasible at every level.

    Returns:
        ``(assignment, total_visits, elapsed, util_variance, max_util,
        cap_broken, wl_broken, best_bound)``. ``assignment=None`` with
        ``best_bound=+inf`` is PROVEN infeasible; with ``nan`` it is
        undetermined within the budget.
    """
    import hexaly.optimizer as hexaly  # lazy: only needed on the Hexaly path

    if gamma > 0 and lhat is None:
        raise ValueError("gamma > 0 requires lhat deviations")
    gamma_i = int(round(gamma))

    t0 = time.time()
    supports = build_supports(order_prods, top_n)
    n_p, n_s, n_o = len(products), len(stations), len(supports)
    p_idx = {p: i for i, p in enumerate(products)}
    station_ids = [str(s["STATION_ID"]) for s in stations]
    speeds = np.array([float(s["SPEED"]) for s in stations])
    caps = np.array([float(s["CAPACITY"]) for s in stations])
    time_caps = np.array([float(s["TIME_CAPACITY"]) for s in stations])
    lbar = np.array([prod_lines.get(p, 0.0) for p in products])
    lhat_v = (
        np.array([float(lhat.get(p, 0.0)) for p in products])
        if lhat is not None else np.zeros(n_p)
    )
    use_dual = gamma_i > 0 and lhat is not None

    if daily_lines is None:
        rows = lbar.reshape(1, n_p)
        mode = "MEAN-DAY FALLBACK (no daily matrix supplied)"
    else:
        rows = np.asarray(daily_lines, dtype=float)
        if rows.ndim != 2 or rows.shape[1] != n_p:
            raise ValueError(
                f"daily_lines must be (n_days, {n_p}); got {rows.shape}")
        mode = "per-day"
    n_d = rows.shape[0]

    # Only products that actually appear on a day contribute to its row; the
    # matrix is sparse in practice and this keeps the model buildable.
    nz = [np.nonzero(rows[d])[0] for d in range(n_d)]

    t_build0 = time.time()
    with hexaly.HexalyOptimizer() as opt:
        model = opt.model
        x = [[model.bool() for _s in range(n_s)] for _p in range(n_p)]

        # (1) every product has exactly one home (A5)
        for p in range(n_p):
            model.constraint(model.sum(x[p][s] for s in range(n_s)) == 1)

        # (2) slot capacity
        for s in range(n_s):
            model.constraint(
                model.sum(x[p][s] for p in range(n_p)) <= float(caps[s]))

        # Bertsimas-Sim duals. The bounds are the tight analytic ones, not a
        # nominal 1e9: at optimality theta_s never exceeds the largest per-unit
        # deviation on station s (beyond that every mu is zero and raising
        # theta only inflates the row), and mu_ps never exceeds a_ps. A 1e9 box
        # hands a local-search solver 48,000 continuous decisions with a range
        # ~6.4e7 times wider than needed; tightening cuts nothing off the
        # optimum and is the difference between finding a feasible point and
        # not.
        a = (lhat_v[:, None] / np.maximum(speeds, 1e-12)[None, :]
             if use_dual else None)                       # a[p, s]
        if use_dual:
            a_max = a.max(axis=0)                         # per station
            th = [model.float(0.0, float(a_max[s])) for s in range(n_s)]
            mu = [[model.float(0.0, float(a[p, s])) for s in range(n_s)]
                  for p in range(n_p)]
        else:
            th = mu = None

        # Coverage indicators: z[d] = 1 lets day d breach at any station.
        # Bounding sum(z) is what makes q a coverage level rather than a
        # ceiling height.
        allow = max(0, int(day_allowance))
        z = None
        if allow > 0:
            z = [model.bool() for _d in range(n_d)]
            model.constraint(model.sum(z) <= allow)
        # Big-M per station: the most any station could carry on the busiest
        # day, so an admitted day is genuinely unconstrained and never a
        # silently tighter bound.
        day_tot = rows.sum(axis=1)
        big_m = float(day_tot.max()) / np.maximum(speeds, 1e-12)

        # (3) workload, one row per (station, day) -- the whole point of this
        #     module. Protection is day-independent, so this is equivalent to
        #     bounding the worst admitted day plus the budgeted deviation.
        for s in range(n_s):
            inv_v = 1.0 / max(float(speeds[s]), 1e-12)
            prot = None
            if use_dual:
                prot = gamma_i * th[s] + model.sum(mu[p][s] for p in range(n_p))
            for d in range(n_d):
                idx = nz[d]
                if idx.size == 0:
                    continue
                load = model.sum(
                    float(rows[d, p] * inv_v) * x[p][s] for p in idx)
                if prot is not None:
                    load = load + prot
                cap = float(time_caps[s])
                if z is not None:
                    model.constraint(load <= cap + float(big_m[s]) * z[d])
                else:
                    model.constraint(load <= cap)

        # (4) Bertsimas-Sim dual feasibility (skip vacuous hat L_p = 0 rows)
        if use_dual:
            for p in range(n_p):
                if lhat_v[p] <= 0.0:
                    continue
                for s in range(n_s):
                    coef = float(lhat_v[p] / max(float(speeds[s]), 1e-12))
                    model.constraint(th[s] + mu[p][s] >= coef * x[p][s])

        # (5) visit objective: a station is visited for an order when it holds
        #     any product of that order's support.
        terms = []
        for support, w in supports:
            members = [p_idx[q] for q in support if q in p_idx]
            if not members:
                continue
            for s in range(n_s):
                if len(members) == 1:
                    terms.append(float(w) * x[members[0]][s])
                else:
                    terms.append(float(w) * model.or_(
                        *(x[p][s] for p in members)))
        model.minimize(model.sum(terms))
        model.close()

        # Warm start: injected after close, as Hexaly requires.
        #
        # The duals MUST be seeded alongside x. Seeding x alone leaves
        # theta = mu = 0, which violates the dual-feasibility row
        # theta_s + mu_ps >= a_ps * x_ps for every seeded product with
        # lhat_p > 0 -- roughly 2,000 violated rows per fold. The solver then
        # starts from an infeasible point at every Gamma >= 1 and has to
        # repair it before it can improve anything, which is why Gamma >= 2
        # previously returned "no feasible solution found" at full coverage.
        # The closed form below is the Bertsimas-Sim optimum for a FIXED
        # assignment (identical to the CPLEX twin): theta_s is the Gamma-th
        # largest per-unit deviation on the station, and each mu absorbs only
        # the excess above it.
        seeded = 0
        assign0 = np.full(n_p, -1, dtype=int)
        if start_assignment:
            s_idx = {sid: i for i, sid in enumerate(station_ids)}
            for prod, sid in start_assignment.items():
                i, j = p_idx.get(prod), s_idx.get(str(sid))
                if i is None or j is None:
                    continue
                for s in range(n_s):
                    x[i][s].value = 1 if s == j else 0
                assign0[i] = j
                seeded += 1

            if use_dual and seeded:
                for s in range(n_s):
                    own = np.flatnonzero(assign0 == s)
                    vals = np.sort(a[own, s])[::-1] if own.size else np.empty(0)
                    theta = float(vals[gamma_i - 1]) if vals.size >= gamma_i \
                        else 0.0
                    theta = min(theta, float(a_max[s]))
                    th[s].value = theta
                    for p in own:
                        mu[p][s].value = float(
                            min(max(0.0, a[p, s] - theta), a[p, s]))

        opt.param.time_limit = int(max(1, time_limit))
        opt.param.verbosity = 0
        if threads:
            opt.param.nb_threads = int(threads)
        t_build = time.time() - t_build0

        if verbose:
            duals = ("duals seeded" if (use_dual and seeded)
                     else ("duals N/A (gamma=0)" if not use_dual
                           else "duals NOT seeded"))
            print(f"[milp_hexaly_robust] gamma={gamma_i} vars~{n_p * n_s} "
                  f"{duals} rows={mode} days={n_d} coverage_allowance={allow} "
                  f"seeded={seeded} build={t_build:.1f}s (ls_time={ls_time:g} "
                  f"ignored: the mean-day repair is what this backend "
                  f"replaces)", flush=True)

        opt.solve()
        elapsed = time.time() - t0
        status = opt.solution.status

        if status == hexaly.HxSolutionStatus.INCONSISTENT:
            # Hexaly PROVED the model contradictory.
            print(f"[milp_hexaly_robust] gamma={gamma_i} MODEL INFEASIBLE "
                  f"(proven) status='inconsistent' elapsed={elapsed:.1f}s",
                  flush=True)
            return None, float("inf"), elapsed, 0.0, 0.0, 0, 0, float("inf")

        if status == hexaly.HxSolutionStatus.INFEASIBLE:
            # No feasible solution found. NOT a proof -- Hexaly is a local
            # search and cannot certify infeasibility.
            print(f"[milp_hexaly_robust] gamma={gamma_i} no feasible solution "
                  f"found (status='infeasible'; NOT proven) "
                  f"elapsed={elapsed:.1f}s", flush=True)
            return None, float("inf"), elapsed, 0.0, 0.0, 0, 0, float("nan")

        assign_vec = np.zeros(n_p, dtype=int)
        for p in range(n_p):
            for s in range(n_s):
                if x[p][s].value > 0.5:
                    assign_vec[p] = s
                    break

        try:
            bound = float(opt.solution.get_objective_bound(0))
        except Exception:
            bound = float("nan")
        obj = _visits_of(assign_vec, supports, p_idx, n_s)

        # Diagnostics against the MEAN row, kept for column compatibility with
        # the CPLEX twin; the per-day verdict is computed below.
        station_load = np.zeros(n_s)
        station_cnt = np.zeros(n_s)
        for p in range(n_p):
            station_load[assign_vec[p]] += lbar[p] / speeds[assign_vec[p]]
            station_cnt[assign_vec[p]] += 1
        uv = float(np.var(station_load / np.maximum(time_caps, 1e-12)))
        mu_ = float(np.max(station_load / np.maximum(time_caps, 1e-12)))
        cb = int(np.sum(station_cnt > caps))

        # wl_broken is reported on the PER-DAY criterion: the number of
        # (station, day) pairs that exceed the ceiling under this layout.
        onehot = np.zeros((n_p, n_s))
        onehot[np.arange(n_p), assign_vec] = 1.0
        day_station = rows @ onehot                     # (n_d, n_s) in lines
        day_station = day_station / np.maximum(speeds, 1e-12)
        wb = int(np.sum(day_station > time_caps[None, :] + 1e-6))
        days_over = int(np.sum(
            (day_station > time_caps[None, :] + 1e-6).any(axis=1)))

        if verbose:
            gap_txt = "n/a" if not np.isfinite(bound) else f"{bound:.1f}"
            print(f"[milp_hexaly_robust] gamma={gamma_i} obj={obj:.0f} "
                  f"bound={gap_txt} status='{status}' elapsed={elapsed:.1f}s "
                  f"cap_broken={cb} station_days_over={wb} "
                  f"days_breached={days_over}/{n_d} (allowed {allow})",
                  flush=True)
            if days_over > allow:
                print(f"[milp_hexaly_robust] WARNING gamma={gamma_i} "
                      f"coverage violated: {days_over} days breached but only "
                      f"{allow} allowed", flush=True)

        assignment = {products[p]: station_ids[int(assign_vec[p])]
                      for p in range(n_p)}
        return assignment, obj, elapsed, uv, mu_, cb, wb, bound
