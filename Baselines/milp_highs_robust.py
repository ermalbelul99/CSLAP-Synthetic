r"""Bertsimas--Sim budgeted-uncertainty robust CSLAP placement MILP (HiGHS backend).

Implements the exact linear robust counterpart derived in
``reports/12_workload_feasibility/tex/section_theory.tex`` (Proposition 1 there):
the budgeted uncertainty set on per-product pick-lines
:math:`\tilde L_p \in [\bar L_p - \hat L_p,\, \bar L_p + \hat L_p]`, with at most
:math:`\Gamma` products deviating simultaneously per station, dualised into a
polynomial-size MILP. :math:`\Gamma = 0` recovers the nominal placement model
(same solver, same settings), which is the paired baseline arm of the
experiment harness ``run_bs_robust_experiment.py``.

Mathematical model
------------------
Sets: products :math:`p \in P`, stations :math:`s \in S`, weighted distinct
multi-item order supports :math:`o \in O` (weight :math:`w_o` = number of train
orders sharing the support; size-1 orders contribute a constant 1 visit each and
are dropped, mirroring the project's placement pipeline).

Variables:
    :math:`x_{ps} \in \{0,1\}`   product-to-station assignment;
    :math:`y_{os} \in [0,1]`     station-visit indicator (continuous is exact:
                                 for fixed integral :math:`x` the minimal
                                 :math:`y_{os} = \max_{p \in o} x_{ps}` is 0/1);
    :math:`\theta_s \ge 0`, :math:`\mu_{ps} \ge 0`  duals of the inner
                                 adversarial LP (budget row / box rows).

.. math::
    \min \sum_{o \in O} w_o \sum_{s \in S} y_{os}
    \quad \text{s.t.} \quad
    \sum_s x_{ps} = 1 \;\; \forall p, \qquad
    y_{os} \ge x_{ps} \;\; \forall o,\, p \in o,\, s, \qquad
    \sum_p x_{ps} \le C_s \;\; \forall s,

.. math::
    \sum_p \frac{\bar L_p}{V_s} x_{ps} + \Gamma\,\theta_s + \sum_p \mu_{ps}
        \le T_s \;\; \forall s, \qquad
    \theta_s + \mu_{ps} \ge \frac{\hat L_p}{V_s}\, x_{ps} \;\; \forall p, s.

For :math:`\Gamma = 0` the dual block is omitted entirely (pure nominal MILP).

Backend and warm start
----------------------
HiGHS via ``highspy`` (no commercial solver on this machine). The MIP is warm
started with a feasibility-first greedy assignment (best-fit decreasing on the
robust station load, swap-repair until the robust constraint holds), completed
to a full primal vector with the closed-form inner-LP duals
:math:`\theta_s = a_{(\Gamma)}(s)` (the :math:`\Gamma`-th largest
:math:`a_p = \hat L_p / V_s` at station ``s``) and
:math:`\mu_{ps} = \max(0, a_p - \theta_s)` — so the incumbent exists from
second zero and HiGHS only improves it. ``y`` continuous keeps the binary count
at :math:`|P||S|`.

CLI (project code standards):
    python milp_highs_robust.py --prefix iscf480_r0f0_train --dir <folds_dir>
        --time 150 --gamma 8 --lhat-json lhat.json --out layout.json
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from scipy import sparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from paths import ISCF_INSTANCES  # noqa: E402


# ---------------------------------------------------------------------------
#  DATA LOADING (standard CSLAP schema, semicolon-separated)
# ---------------------------------------------------------------------------
def read_data(
    prefix: str, data_dir: str
) -> Tuple[Dict[str, List[str]], List[dict], List[str], Dict[str, float]]:
    """Load one instance following the ``milp_gurobi_synthetic.py`` pattern.

    Args:
        prefix: Dataset prefix (``{prefix}_orders.csv`` etc.).
        data_dir: Directory containing the semicolon-separated CSVs.

    Returns:
        ``(order_prods, stations, products, prod_lines)``: orders as
        ``{order_id: [product, ...]}``, station records, product token list,
        and the kappa-invariant real pick-lines ``REAL_LINES`` per product.
    """
    orders_df = pd.read_csv(os.path.join(data_dir, f"{prefix}_orders.csv"), sep=";")
    stations_df = pd.read_csv(os.path.join(data_dir, f"{prefix}_stations.csv"), sep=";")
    products_df = pd.read_csv(os.path.join(data_dir, f"{prefix}_products.csv"), sep=";")

    order_prods = orders_df.groupby("ORDER")["PRODUCT"].apply(list).to_dict()
    stations = stations_df.to_dict(orient="records")
    products = ("PROD_" + products_df["PRODUCT_ID"].astype(str)).tolist()
    prod_lines = {
        f"PROD_{pid}": float(n)
        for pid, n in zip(products_df["PRODUCT_ID"], products_df["REAL_LINES"])
    }
    return order_prods, stations, products, prod_lines


def build_supports(
    order_prods: Dict[str, List[str]], top_n: int
) -> List[Tuple[Tuple[str, ...], int]]:
    """Aggregate multi-item orders into the ``top_n`` weighted distinct supports.

    Size-1 orders are dropped (constant one visit regardless of the layout);
    ties in frequency are broken lexicographically for determinism.

    Args:
        order_prods: ``{order_id: [product, ...]}`` train orders.
        top_n: Number of most frequent distinct supports to keep.

    Returns:
        List of ``(support_tuple, weight)`` sorted by descending weight.
    """
    counts: Dict[Tuple[str, ...], int] = {}
    for prods in order_prods.values():
        support = tuple(sorted(set(prods)))
        if len(support) < 2:
            continue
        counts[support] = counts.get(support, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return ranked[:top_n]


# ---------------------------------------------------------------------------
#  WARM START (feasibility-first greedy + swap repair, closed-form duals)
# ---------------------------------------------------------------------------
def _protection(devs: List[float], gamma: int) -> float:
    """Sum of the ``gamma`` largest values in ``devs`` (0 for gamma <= 0)."""
    if gamma <= 0 or not devs:
        return 0.0
    return float(np.sum(sorted(devs, reverse=True)[: int(gamma)]))


def greedy_start(
    products: List[str],
    lbar: np.ndarray,
    lhat_v: np.ndarray,
    speeds: np.ndarray,
    caps: np.ndarray,
    time_caps: np.ndarray,
    gamma: int,
    max_swap_iters: int = 4000,
    max_seconds: float = 20.0,
    init_assign: Optional[np.ndarray] = None,
) -> Tuple[np.ndarray, bool]:
    r"""Feasibility-first greedy assignment for the robust placement model.

    Best-fit decreasing on the ROBUST station load (nominal + top-:math:`\Gamma`
    protection), then steepest swap-descent repair on the total robust-constraint
    violation. Slot capacities are respected by construction.

    Args:
        products: Product tokens (indexing convention of the MILP).
        lbar: Nominal pick-lines per product.
        lhat_v: Deviations per product (zeros when gamma == 0).
        speeds: Station speeds.
        caps: Station slot capacities.
        time_caps: Workload ceilings :math:`T_s`.
        gamma: Budget.
        init_assign: Optional incumbent (e.g. the industrial warm-start layout)
            to repair instead of constructing one from scratch. Essential on
            instances whose ceilings are calibrated ON an existing layout: there
            a feasible solution provably exists but a from-scratch greedy may
            fail to rediscover it, which would read as a false infeasibility.
        max_swap_iters: Swap-repair iteration cap.

    Returns:
        ``(assign_idx, feasible)``: station index per product and whether the
        robust constraint holds at every station.
    """
    n_p, n_s = len(products), len(speeds)
    assign = np.full(n_p, -1, dtype=int)
    members: List[List[int]] = [[] for _ in range(n_s)]

    if init_assign is not None:
        assign = np.asarray(init_assign, dtype=int).copy()
        for i in range(n_p):
            members[assign[i]].append(i)
        order = np.array([], dtype=int)  # nothing to construct
    else:
        order = np.argsort(-(lbar + lhat_v))

    def lhs(s: int, extra_p: Optional[int] = None) -> float:
        idx = members[s] + ([extra_p] if extra_p is not None else [])
        nom = float(np.sum(lbar[idx]) / speeds[s]) if idx else 0.0
        prot = _protection([lhat_v[i] / speeds[s] for i in idx], gamma)
        return nom + prot

    for p in order:
        best_s, best_val = -1, float("inf")
        for s in range(n_s):
            if len(members[s]) >= caps[s]:
                continue
            val = lhs(s, p)
            penal = 0.0 if val <= time_caps[s] else (val - time_caps[s]) * 1e3
            if val + penal < best_val:
                best_val, best_s = val + penal, s
        assign[p] = best_s
        members[best_s].append(p)

    def total_violation() -> float:
        return sum(max(0.0, lhs(s) - time_caps[s]) for s in range(n_s))

    t_repair = time.time()
    viol = total_violation()
    it = 0
    while viol > 1e-9 and it < max_swap_iters:
        if time.time() - t_repair > max_seconds:
            break  # bail out; the HiGHS probe decides true feasibility
        it += 1
        s_bad = int(np.argmax([lhs(s) - time_caps[s] for s in range(n_s)]))
        best_delta, best_pair = -1e-9, None
        # NB: iterate over SNAPSHOTS — the trial swap mutates the live lists.
        for p in list(members[s_bad]):
            for t in range(n_s):
                if t == s_bad:
                    continue
                for q in list(members[t]):
                    old = max(0.0, lhs(s_bad) - time_caps[s_bad]) + max(
                        0.0, lhs(t) - time_caps[t]
                    )
                    members[s_bad].remove(p)
                    members[t].remove(q)
                    members[s_bad].append(q)
                    members[t].append(p)
                    new = max(0.0, lhs(s_bad) - time_caps[s_bad]) + max(
                        0.0, lhs(t) - time_caps[t]
                    )
                    delta = old - new
                    if delta > best_delta:
                        best_delta, best_pair = delta, (p, t, q)
                    # undo
                    members[s_bad].remove(q)
                    members[t].remove(p)
                    members[s_bad].append(p)
                    members[t].append(q)
        if best_pair is None:
            break
        p, t, q = best_pair
        members[s_bad].remove(p)
        members[t].remove(q)
        members[s_bad].append(q)
        members[t].append(p)
        assign[p], assign[q] = t, s_bad
        viol = total_violation()

    return assign, bool(viol <= 1e-9)


def local_search_visits(
    assign0: np.ndarray,
    supports: List[Tuple[Tuple[str, ...], int]],
    p_idx: Dict[str, int],
    lbar: np.ndarray,
    lhat_v: np.ndarray,
    speeds: np.ndarray,
    time_caps: np.ndarray,
    gamma: int,
    time_budget: float,
    seed: int = 0,
    max_passes: int = 4,
    caps: Optional[np.ndarray] = None,
) -> np.ndarray:
    r"""Visit-minimising swap local search under the hard robust constraint.

    First-improvement over shuffled products, with two neighbourhoods: single
    MOVES (only legal when the target station has slot slack, e.g. the exp02a
    50-SKU family; on exactly binding instances like iscf480 no legal move
    exists and the neighbourhood degenerates to swaps as before) and pairwise
    SWAPS. The weighted-visit delta of a swap is evaluated
    incrementally on the support-count matrix ``cnt[o, s]`` (only the supports
    containing the two products are touched); the robust constraint
    :math:`\bar W_s + \mathrm{prot}_\Gamma(s) \le T_s` is re-checked exactly on
    the two stations involved via ``np.partition``.

    Args:
        assign0: Feasible start (station index per product).
        supports: Weighted distinct supports (objective terms).
        p_idx: Product token -> index.
        lbar: Nominal pick-lines.
        lhat_v: Deviations (zeros for gamma == 0).
        speeds: Station speeds.
        time_caps: Workload ceilings.
        gamma: Budget.
        time_budget: Wall-clock seconds for the search.
        seed: Shuffle seed (determinism).

    Returns:
        Improved assignment (station index per product).
    """
    t0 = time.time()
    n_p, n_s = len(assign0), len(speeds)
    n_o = len(supports)
    assign = assign0.copy()
    w = np.array([wt for _, wt in supports], dtype=float)

    # Support membership structures.
    memb: List[List[int]] = [[] for _ in range(n_p)]  # product -> support rows
    rows_p: List[np.ndarray] = []
    for o, (support, _wt) in enumerate(supports):
        for prod in support:
            i = p_idx.get(prod)
            if i is not None:
                memb[i].append(o)
    for i in range(n_p):
        rows_p.append(np.array(memb[i], dtype=np.int32))

    cnt = np.zeros((n_o, n_s), dtype=np.int16)
    for o, (support, _wt) in enumerate(supports):
        for prod in support:
            i = p_idx.get(prod)
            if i is not None:
                cnt[o, assign[i]] += 1

    nominal = np.zeros(n_s)
    for i in range(n_p):
        nominal[assign[i]] += lbar[i] / speeds[assign[i]]
    counts = np.bincount(assign, minlength=n_s)
    caps_v = caps if caps is not None else counts.astype(float)  # no slack default

    def prot(s: int, member_mask: np.ndarray) -> float:
        if gamma <= 0:
            return 0.0
        devs = lhat_v[member_mask] / speeds[s]
        if len(devs) <= gamma:
            return float(devs.sum())
        return float(np.partition(devs, -gamma)[-gamma:].sum())

    members_of = [np.where(assign == s)[0] for s in range(n_s)]

    def swap_delta_visits(p: int, q: int, s: int, t: int) -> float:
        rp, rq = rows_p[p], rows_p[q]
        d = 0.0
        # p: s -> t ; q: t -> s. Handle shared supports jointly.
        shared = np.intersect1d(rp, rq, assume_unique=False)
        only_p = np.setdiff1d(rp, shared, assume_unique=False)
        only_q = np.setdiff1d(rq, shared, assume_unique=False)
        if len(only_p):
            d += float(np.sum(w[only_p] * ((cnt[only_p, t] == 0).astype(float)
                                           - (cnt[only_p, s] == 1).astype(float))))
        if len(only_q):
            d += float(np.sum(w[only_q] * ((cnt[only_q, s] == 0).astype(float)
                                           - (cnt[only_q, t] == 1).astype(float))))
        # shared supports: p leaves s & q arrives s => net cnt[s] -1+1 = 0; same at t.
        # visits unchanged there.
        return d

    def move_delta_visits(p: int, s: int, t: int) -> float:
        rp = rows_p[p]
        if not len(rp):
            return 0.0
        return float(np.sum(w[rp] * ((cnt[rp, t] == 0).astype(float)
                                     - (cnt[rp, s] == 1).astype(float))))

    def robust_ok_move(p: int, s: int, t: int) -> bool:
        # station s loses p; station t gains p. s only sheds load -> always ok.
        new_nom = nominal[t] + lbar[p] / speeds[t]
        mask = members_of[t]
        devs = np.append(lhat_v[mask], lhat_v[p]) / speeds[t]
        if gamma > 0:
            if len(devs) <= gamma:
                pr = float(devs.sum())
            else:
                pr = float(np.partition(devs, -gamma)[-gamma:].sum())
        else:
            pr = 0.0
        return new_nom + pr <= time_caps[t] + 1e-9

    def robust_ok_after(p: int, q: int, s: int, t: int) -> bool:
        # station s loses p gains q; station t loses q gains p.
        for st, out_p, in_p in ((s, p, q), (t, q, p)):
            new_nom = nominal[st] - lbar[out_p] / speeds[st] + lbar[in_p] / speeds[st]
            mask = members_of[st][members_of[st] != out_p]
            devs = np.append(lhat_v[mask], lhat_v[in_p]) / speeds[st]
            if gamma > 0:
                if len(devs) <= gamma:
                    pr = float(devs.sum())
                else:
                    pr = float(np.partition(devs, -gamma)[-gamma:].sum())
            else:
                pr = 0.0
            if new_nom + pr > time_caps[st] + 1e-9:
                return False
        return True

    # Determinism: the search is budgeted in PASSES (seeded permutations and
    # candidate samples), so identical inputs give identical outputs across
    # processes; time_budget is only a generous safety net.
    rng = np.random.RandomState(seed)
    improved_total = 0.0
    passes = 0
    while passes < max_passes and time.time() - t0 < time_budget:
        passes += 1
        perm = rng.permutation(n_p)
        any_improve = False
        for p in perm:
            s = assign[p]
            # MOVE neighbourhood (legal only where the target has slot slack).
            best_d, best_q, best_t = -1e-9, -1, -1
            for t in range(n_s):
                if t == s or counts[t] >= caps_v[t]:
                    continue
                d = move_delta_visits(p, s, t)
                if d < best_d and robust_ok_move(p, s, t):
                    best_d, best_q, best_t = d, -1, t
            # SWAP neighbourhood: sample partners per pass to bound cost.
            cand = rng.choice(n_p, size=min(96, n_p), replace=False)
            for q in cand:
                t = assign[q]
                if t == s:
                    continue
                d = swap_delta_visits(p, q, s, t)
                if d < best_d:
                    if robust_ok_after(p, q, s, t):
                        best_d, best_q, best_t = d, q, t
            if best_t >= 0 and best_q == -1:
                # apply MOVE p: s -> best_t
                t = best_t
                for o in rows_p[p]:
                    cnt[o, s] -= 1
                    cnt[o, t] += 1
                nominal[s] -= lbar[p] / speeds[s]
                nominal[t] += lbar[p] / speeds[t]
                counts[s] -= 1
                counts[t] += 1
                assign[p] = t
                members_of[s] = np.where(assign == s)[0]
                members_of[t] = np.where(assign == t)[0]
                improved_total += best_d
                any_improve = True
            elif best_q >= 0:
                q = best_q
                t = assign[q]
                # apply swap on cnt
                for o in rows_p[p]:
                    cnt[o, s] -= 1
                    cnt[o, t] += 1
                for o in rows_p[q]:
                    cnt[o, t] -= 1
                    cnt[o, s] += 1
                nominal[s] += (lbar[q] - lbar[p]) / speeds[s]
                nominal[t] += (lbar[p] - lbar[q]) / speeds[t]
                assign[p], assign[q] = t, s
                members_of[s] = np.where(assign == s)[0]
                members_of[t] = np.where(assign == t)[0]
                improved_total += best_d
                any_improve = True
        if not any_improve:
            break
    return assign


# ---------------------------------------------------------------------------
#  CORE SOLVER
# ---------------------------------------------------------------------------
def run_milp_highs(
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
) -> Tuple[Optional[Dict[str, str]], float, float, float, float, int, int, float]:
    r"""Solve the (robust) placement MILP with HiGHS, warm started.

    Pipeline: feasibility-first greedy -> visit-minimising local search
    (``ls_time`` seconds, robust constraint hard) -> HiGHS MILP warm started
    with that incumbent (``time_limit`` seconds, yields the dual bound and any
    further improvement).

    Args:
        order_prods: Train orders ``{order_id: [product, ...]}``.
        stations: Station records (``STATION_ID``/``CAPACITY``/
            ``TIME_CAPACITY``/``SPEED``).
        products: Product tokens to place (the layout domain).
        prod_lines: Nominal pick-lines :math:`\bar L_p` (``REAL_LINES``).
        lhat: Deviations :math:`\hat L_p`; required when ``gamma > 0``.
        gamma: Uncertainty budget :math:`\Gamma` (uniform across stations).
        time_limit: HiGHS wall-clock limit in seconds.
        top_n: Number of weighted distinct supports in the visit objective.
        mip_rel_gap: Relative MIP gap tolerance (0 = prove optimality).
        start_assignment: Optional ``{product: station}`` incumbent to repair
            and improve instead of building one greedily (see ``greedy_start``).
        verbose: Print solve milestones.

    Returns:
        Standard project tuple ``(assignment, total_visits, elapsed_time,
        util_variance, max_util, cap_broken, wl_broken, best_bound)`` where
        ``total_visits`` is the support-weighted objective value,
        ``util_*``/``*_broken`` are computed on the TRAIN nominal workload, and
        ``best_bound`` is the HiGHS dual bound. ``assignment`` is ``None`` when
        the model is infeasible (or no incumbent exists, which the warm start
        makes impossible unless the start itself was rejected).
    """
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

    # Variable layout: x (P*S bin) | y (O*S cont) | theta (S) | mu (P*S) if robust.
    nx, ny = n_p * n_s, n_o * n_s
    n_var = nx + ny + (n_s + n_p * n_s if use_dual else 0)
    off_y, off_th = nx, nx + ny
    off_mu = off_th + n_s

    c = np.zeros(n_var)
    weights = np.array([w for _, w in supports], dtype=float)
    for o in range(n_o):
        c[off_y + o * n_s : off_y + (o + 1) * n_s] = weights[o]

    lb = np.zeros(n_var)
    ub = np.full(n_var, np.inf)
    ub[:nx] = 1.0
    ub[off_y : off_y + ny] = 1.0

    rows: List[int] = []
    cols: List[int] = []
    vals: List[float] = []
    c_lb: List[float] = []
    c_ub: List[float] = []
    r = 0

    def add_entry(row: int, col: int, val: float) -> None:
        rows.append(row)
        cols.append(col)
        vals.append(val)

    # (1) assignment: sum_s x_ps = 1
    for p in range(n_p):
        for s in range(n_s):
            add_entry(r, p * n_s + s, 1.0)
        c_lb.append(1.0)
        c_ub.append(1.0)
        r += 1

    # (2) visit linking: y_os - x_ps >= 0 for each o, p in o, s
    for o, (support, _w) in enumerate(supports):
        for prod in support:
            p = p_idx.get(prod)
            if p is None:
                continue
            for s in range(n_s):
                add_entry(r, off_y + o * n_s + s, 1.0)
                add_entry(r, p * n_s + s, -1.0)
                c_lb.append(0.0)
                c_ub.append(np.inf)
                r += 1

    # (3) slot capacity: sum_p x_ps <= C_s
    for s in range(n_s):
        for p in range(n_p):
            add_entry(r, p * n_s + s, 1.0)
        c_lb.append(-np.inf)
        c_ub.append(caps[s])
        r += 1

    # (4) workload: sum_p (Lbar_p/V_s) x_ps [+ Gamma theta_s + sum_p mu_ps] <= T_s
    for s in range(n_s):
        for p in range(n_p):
            add_entry(r, p * n_s + s, lbar[p] / speeds[s])
        if use_dual:
            add_entry(r, off_th + s, float(gamma_i))
            for p in range(n_p):
                add_entry(r, off_mu + p * n_s + s, 1.0)
        c_lb.append(-np.inf)
        c_ub.append(time_caps[s])
        r += 1

    # (5) dual feasibility: theta_s + mu_ps - (Lhat_p/V_s) x_ps >= 0
    if use_dual:
        for p in range(n_p):
            if lhat_v[p] <= 0.0:
                continue  # constraint vacuous when hat L_p = 0
            for s in range(n_s):
                add_entry(r, off_th + s, 1.0)
                add_entry(r, off_mu + p * n_s + s, 1.0)
                add_entry(r, p * n_s + s, -lhat_v[p] / speeds[s])
                c_lb.append(0.0)
                c_ub.append(np.inf)
                r += 1

    a_csc = sparse.csr_matrix(
        (vals, (rows, cols)), shape=(r, n_var), dtype=float
    ).tocsc()

    t_build = time.time() - t0

    # ---- warm start ------------------------------------------------------
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
    t_greedy = time.time() - t0 - t_build

    def _obj_of(assign_vec: np.ndarray) -> float:
        cnt = np.zeros((n_o, n_s), dtype=np.int16)
        for o, (support, _w) in enumerate(supports):
            for prod in support:
                i = p_idx.get(prod)
                if i is not None:
                    cnt[o, assign_vec[i]] += 1
        return float(np.sum(weights * (cnt > 0).sum(axis=1)))

    if start_feasible and ls_time > 0:
        # Multi-restart LS (deterministic seeds); keep the best incumbent.
        n_restarts = 3
        best_assign, best_obj = None, float("inf")
        for seed in range(n_restarts):
            cand = local_search_visits(
                assign0, supports, p_idx, lbar, lhat_v, speeds, time_caps,
                gamma_i, time_budget=ls_time, seed=seed, caps=caps,
            )
            obj_c = _obj_of(cand)
            if obj_c < best_obj:
                best_obj, best_assign = obj_c, cand
        assign0 = best_assign
    t_ls = time.time() - t0 - t_build - t_greedy
    x0 = np.zeros(n_var)
    for p in range(n_p):
        x0[p * n_s + assign0[p]] = 1.0
    for o, (support, _w) in enumerate(supports):
        for s in set(assign0[p_idx[prod]] for prod in support if prod in p_idx):
            x0[off_y + o * n_s + s] = 1.0
    if use_dual:
        for s in range(n_s):
            a_vals = sorted(
                (lhat_v[p] / speeds[s] for p in range(n_p) if assign0[p] == s),
                reverse=True,
            )
            theta = a_vals[gamma_i - 1] if len(a_vals) >= gamma_i else 0.0
            x0[off_th + s] = theta
            for p in range(n_p):
                if assign0[p] == s:
                    x0[off_mu + p * n_s + s] = max(
                        0.0, lhat_v[p] / speeds[s] - theta
                    )
    start_obj = float(c @ x0)

    if verbose:
        print(
            f"[milp_highs_robust] gamma={gamma_i} vars={n_var} (bin={nx}) "
            f"constraints={r} supports={n_o} start_obj={start_obj:.0f} "
            f"start_feasible={start_feasible} build={t_build:.1f}s "
            f"greedy={t_greedy:.1f}s ls={t_ls:.1f}s",
            flush=True,
        )

    if time_limit <= 0:
        # Metaheuristic-only mode: return the greedy+LS incumbent, no bound.
        if not start_feasible:
            print(
                f"[milp_highs_robust] gamma={gamma_i} greedy start infeasible "
                f"and MILP polish disabled -> reporting infeasible",
                flush=True,
            )
            return None, float("inf"), time.time() - t0, 0.0, 0.0, 0, 0, float("nan")
        assign_idx = assign0
        assignment = {
            products[p]: station_ids[assign_idx[p]] for p in range(n_p)
        }
        station_load = np.zeros(n_s)
        station_cnt = np.zeros(n_s)
        for p in range(n_p):
            s = assign_idx[p]
            station_load[s] += lbar[p] / speeds[s]
            station_cnt[s] += 1
        elapsed = time.time() - t0
        if verbose:
            print(
                f"[milp_highs_robust] gamma={gamma_i} obj={start_obj:.0f} "
                f"(greedy+LS, no MILP polish) elapsed={elapsed:.1f}s",
                flush=True,
            )
        return (
            assignment,
            start_obj,
            elapsed,
            float(np.var(station_load / time_caps)),
            float(np.max(station_load / time_caps)),
            int(np.sum(station_cnt > caps)),
            int(np.sum(station_load > time_caps)),
            float("nan"),
        )

    # ---- HiGHS model -----------------------------------------------------
    import highspy  # lazy: keeps the shared helpers importable without HiGHS
    lp = highspy.HighsLp()
    lp.num_col_ = n_var
    lp.num_row_ = r
    lp.col_cost_ = c
    lp.col_lower_ = lb
    lp.col_upper_ = ub
    lp.row_lower_ = np.array(c_lb)
    lp.row_upper_ = np.array(c_ub)
    lp.a_matrix_.format_ = highspy.MatrixFormat.kColwise
    lp.a_matrix_.start_ = a_csc.indptr
    lp.a_matrix_.index_ = a_csc.indices
    lp.a_matrix_.value_ = a_csc.data
    integrality = np.full(
        n_var, highspy.HighsVarType.kContinuous, dtype=object
    )
    integrality[:nx] = highspy.HighsVarType.kInteger
    lp.integrality_ = list(integrality)

    h = highspy.Highs()
    h.setOptionValue("output_flag", False)
    h.setOptionValue("time_limit", float(time_limit))
    h.setOptionValue("mip_rel_gap", float(mip_rel_gap))
    t_pass0 = time.time()
    h.passModel(lp)
    sol0 = highspy.HighsSolution()
    sol0.col_value = x0
    h.setSolution(sol0)
    t_pass = time.time() - t_pass0
    t_run0 = time.time()
    h.run()
    t_run = time.time() - t_run0
    if verbose:
        print(
            f"[milp_highs_robust] gamma={gamma_i} pass={t_pass:.1f}s "
            f"run={t_run:.1f}s (limit {time_limit}s)",
            flush=True,
        )

    status = h.getModelStatus()
    status_str = h.modelStatusToString(status)
    info = h.getInfo()
    best_bound = float(info.mip_dual_bound)
    elapsed = time.time() - t0

    if status_str.lower().startswith("infeasible"):
        print(
            f"[milp_highs_robust] gamma={gamma_i} MODEL INFEASIBLE (proven) "
            f"elapsed={elapsed:.1f}s",
            flush=True,
        )
        # best_bound = +inf signals PROVEN infeasibility to the caller
        # (a no-incumbent timeout keeps its finite/nan bound instead).
        return None, float("inf"), elapsed, 0.0, 0.0, 0, 0, float("inf")

    sol = h.getSolution()
    has_incumbent = int(info.primal_solution_status) == 2  # kSolutionStatusFeasible
    xv = np.array(sol.col_value) if has_incumbent else x0
    if not has_incumbent and not start_feasible:
        print(
            f"[milp_highs_robust] gamma={gamma_i} NO incumbent and greedy start "
            f"infeasible (status={status_str}) elapsed={elapsed:.1f}s",
            flush=True,
        )
        return None, float("inf"), elapsed, 0.0, 0.0, 0, 0, best_bound

    x = xv[:nx].reshape(n_p, n_s)
    assign_idx = np.argmax(x, axis=1)
    assignment = {products[p]: station_ids[assign_idx[p]] for p in range(n_p)}
    total_visits = float(c @ xv)

    # Train-side diagnostics on the rounded assignment (nominal workload).
    station_load = np.zeros(n_s)
    station_cnt = np.zeros(n_s)
    for p in range(n_p):
        s = assign_idx[p]
        station_load[s] += lbar[p] / speeds[s]
        station_cnt[s] += 1
    cap_broken = int(np.sum(station_cnt > caps))
    wl_broken = int(np.sum(station_load > time_caps))

    if verbose:
        gap = (
            (total_visits - best_bound) / total_visits if total_visits else np.nan
        )
        print(
            f"[milp_highs_robust] gamma={gamma_i} obj={total_visits:.0f} "
            f"bound={best_bound:.1f} gap={100 * gap:.2f}% status={status_str} "
            f"incumbent={'HiGHS' if has_incumbent else 'greedy'} "
            f"elapsed={elapsed:.1f}s cap_broken={cap_broken} wl_broken={wl_broken}",
            flush=True,
        )
    return (
        assignment,
        total_visits,
        elapsed,
        float(np.var(station_load / time_caps)),
        float(np.max(station_load / time_caps)),
        cap_broken,
        wl_broken,
        best_bound,
    )


def robust_lhs(
    assignment: Dict[str, str],
    stations: List[dict],
    prod_lines: Dict[str, float],
    lhat: Dict[str, float],
    gamma: int,
) -> Dict[str, float]:
    """Exact robust LHS per station: nominal load + sum of Gamma largest hat L.

    Independent of the dualisation — used to verify a solved layout satisfies
    the original (pre-dualisation) robust constraint.

    Args:
        assignment: ``{product: station}`` layout.
        stations: Station records.
        prod_lines: Nominal pick-lines.
        lhat: Deviations.
        gamma: Budget.

    Returns:
        ``{station_id: robust LHS value}``.
    """
    speeds = {s["STATION_ID"]: float(s["SPEED"]) for s in stations}
    nominal: Dict[str, float] = {s["STATION_ID"]: 0.0 for s in stations}
    devs: Dict[str, List[float]] = {s["STATION_ID"]: [] for s in stations}
    for p, sid in assignment.items():
        v = speeds[sid]
        nominal[sid] += prod_lines.get(p, 0.0) / v
        devs[sid].append(lhat.get(p, 0.0) / v)
    out = {}
    for sid in nominal:
        top = sorted(devs[sid], reverse=True)[: max(int(gamma), 0)]
        out[sid] = nominal[sid] + float(np.sum(top))
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Bertsimas-Sim robust CSLAP placement MILP (HiGHS)"
    )
    parser.add_argument("--prefix", type=str, required=True)
    parser.add_argument("--dir", type=str, default=ISCF_INSTANCES)
    parser.add_argument("--time", type=int, default=120)
    parser.add_argument("--gamma", type=float, default=0.0)
    parser.add_argument("--lhat-json", type=str, default=None,
                        help="JSON {product: hat L_p}; required when --gamma > 0")
    parser.add_argument("--topn", type=int, default=3000)
    parser.add_argument("--out", type=str, default=None,
                        help="Path to persist the layout JSON")
    args = parser.parse_args()

    ops, sts, prods, lines = read_data(args.prefix, args.dir)
    lh = None
    if args.lhat_json:
        with open(args.lhat_json) as fh:
            lh = {k: float(v) for k, v in json.load(fh).items()}
    result = run_milp_highs(
        ops, sts, prods, lines, lhat=lh, gamma=args.gamma, time_limit=args.time,
        top_n=args.topn,
    )
    if result[0] is not None and args.out:
        with open(args.out, "w") as fh:
            json.dump(result[0], fh)
        print(f"[milp_highs_robust] layout written to {args.out}", flush=True)
