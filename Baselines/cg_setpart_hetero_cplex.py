r"""
Heterogeneous-station Set-Partitioning Column Generation for CSLAP (CPLEX).

Industrial extension of :mod:`cg_setpart_cplex` (the flat-warehouse
price-and-complete matheuristic) to warehouses whose stations differ in slot
capacity :math:`\zeta_s`, speed :math:`V_s` and workload cap :math:`T_s`
(Company~A / BERNER: 24 active stations, every one its own type).

Master (RMP), continuous relaxation
-----------------------------------
Columns are station-TAGGED bundles :math:`(s, q)`:

.. math::
    \min \sum_{(s,q)} c_q x_{sq}
    \;\; \text{s.t.} \;\;
    \sum_{(s,q) \ni p} x_{sq} \ge 1 \;(\sigma_p) \;\forall p, \qquad
    \sum_{q} x_{sq} \le 1 \;(\mu_s \le 0) \;\forall s, \qquad 0 \le x \le 1,

with the same aggregated cost :math:`c_q = \sum_u w_u \mathbf{1}[q\cap u\neq
\emptyset]` over DISTINCT weighted supports. Capacity is tight per station
(:math:`\sum_s \zeta_s = |P|`, each station's cap equals its current SKU
count), so integer solutions are exact partitions matching the slot profile.

Pricing (ONE persistent MILP for all stations)
----------------------------------------------
Reduced cost of a bundle for station :math:`s`:
:math:`c_q - \sum_{p\in q}\sigma_p - \mu_s`. The linking matrix
(:math:`z_u \ge a_p`) is station- and dual-independent; only TWO right-hand
sides are station-dependent once the workload row is scaled by the speed:

.. math::
    \sum_p a_p \le \zeta_s, \qquad \sum_p L_p\, a_p \le T_s V_s .

So a single persistent model serves all 24 stations: each call rewrites the
objective coefficients (duals) and the two RHS values. A full bound pass
(price every station at ONE dual vector) then costs 24 RHS swaps with no
objective rewrite, giving the per-station Farley/convexity bound

.. math::
    \mathrm{LB} = z_{RMP} + \sum_s \min(0,\ \mathrm{rc^{lb}_s}),

valid because every station's convexity row has RHS 1 and
:math:`\mathrm{rc^{lb}_s}` is the pricing MIP dual bound minus :math:`\mu_s`.

Matheuristic drive (same components as the flat solver, station-aware)
----------------------------------------------------------------------
warm start = the ORIGINAL industrial layout (identical seed to every other
method in the industrial protocol) polished by the penalized swap descent;
round-robin target station per iteration; dual-guided greedy pricing first,
exact pricing fallback; each priced bundle completed into a full feasible
layout by max-co-occurrence affinity packing; feasible bundles enter the
master station-tagged; integer master over the pool; explicit deduplication
(dormant under tight caps); final descent on the leftover budget. Workload
uses station speeds throughout (:math:`W_s = \sum_{p\to s} L_p / V_s`).
"""

from __future__ import annotations

import argparse
import random
import time
from collections import defaultdict
from typing import Dict, FrozenSet, List, Optional, Sequence, Tuple

import numpy as np

import cplex

from cg_setpart_cplex import SupportIndex, aggregate_supports, evaluate_assignment

EPS_RC = -1e-6


# ---------------------------------------------------------------------------
#  STATION DATA
# ---------------------------------------------------------------------------
class Stations:
    """Per-station capacity/speed/workload-cap arrays (heterogeneous)."""

    def __init__(self, stations: List[dict]) -> None:
        self.ids: List[str] = [str(s["STATION_ID"]) for s in stations]
        self.n = len(self.ids)
        self.cap = np.array([int(s["CAPACITY"]) for s in stations])
        self.tcap = np.array([float(s["TIME_CAPACITY"]) for s in stations])
        # Optional workload FLOOR (equilibrium band): lo <= W_s <= tcap.
        self.lo = np.array([float(s.get("TIME_CAPACITY_LO", 0.0)) for s in stations])
        self.speed = np.array([float(s["SPEED"]) for s in stations])
        self.idx = {sid: i for i, sid in enumerate(self.ids)}

    def wl(self, p_lines: float, s: int) -> float:
        """Workload (time) of a product with `p_lines` order lines at station s."""
        return p_lines / self.speed[s] if self.speed[s] > 0 else 0.0


def layout_loads(
    bins: List[List[str]], st: Stations, prod_lines: Dict[str, int]
) -> np.ndarray:
    """Per-station workload (time units) of a full layout."""
    return np.array([
        sum(st.wl(prod_lines.get(p, 0), i) for p in bins[i]) for i in range(st.n)
    ])


# ---------------------------------------------------------------------------
#  PENALIZED SWAP DESCENT (station-aware speeds)
# ---------------------------------------------------------------------------
def swap_descent_hetero(
    bins: List[List[str]],
    sidx: SupportIndex,
    prod_lines: Dict[str, int],
    st: Stations,
    deadline: float,
    rng: random.Random,
    overload_penalty: float,
) -> List[List[str]]:
    """First-improvement product-swap descent on visits + overload penalty.

    Identical acceptance rule to the flat solver, but workload deltas use each
    station's own speed: moving p from i to j changes loads by
    -L_p/V_i and +L_p/V_j. Slot counts are preserved by swapping, matching the
    tight per-station capacity profile.
    """
    bins = [list(b) for b in bins]
    cnt = np.zeros((st.n, sidx.n), dtype=np.int32)
    load = layout_loads(bins, st, prod_lines)
    pos: Dict[str, int] = {}
    for i, b in enumerate(bins):
        for p in b:
            idx = sidx.prod_to_sup.get(p)
            if idx is not None:
                cnt[i][idx] += 1
            pos[p] = i
    w = sidx.weights

    def move_delta_apply(p: str, src: int, dst: int) -> Tuple[float, float]:
        """Apply move; return (visit delta, overload delta) separately."""
        d = 0.0
        idx = sidx.prod_to_sup.get(p)
        if idx is not None:
            c_src, c_dst = cnt[src][idx], cnt[dst][idx]
            d -= float(w[idx[c_src == 1]].sum())
            d += float(w[idx[c_dst == 0]].sum())
            cnt[src][idx] -= 1
            cnt[dst][idx] += 1
        lines = prod_lines.get(p, 0)

        def band_over(i: int) -> float:
            return (max(0.0, load[i] - st.tcap[i])
                    + max(0.0, st.lo[i] - load[i]))

        old_over = band_over(src) + band_over(dst)
        load[src] -= st.wl(lines, src)
        load[dst] += st.wl(lines, dst)
        new_over = band_over(src) + band_over(dst)
        return d, new_over - old_over

    prods = list(pos.keys())
    n = len(prods)
    n_partners = n if n <= 300 else (48 if n <= 5000 else 24)
    while time.time() < deadline:
        rng.shuffle(prods)
        improved = False
        for a in range(n - 1):
            if a % 64 == 0 and time.time() > deadline:
                break
            p = prods[a]
            partners = (range(a + 1, n) if n_partners >= n
                        else rng.sample(range(n), n_partners))
            for b_i in partners:
                q = prods[b_i]
                if q == p:
                    continue
                i, j = pos[p], pos[q]
                if i == j:
                    continue
                d1, o1 = move_delta_apply(p, i, j)
                d2, o2 = move_delta_apply(q, j, i)
                d, over = d1 + d2, o1 + o2
                # Lexicographic acceptance: feasibility strictly first (an
                # overload increase is NEVER bought with visits, unlike a
                # finite penalty, which lets micro-overloads accumulate on
                # zero-slack industrial caps), then visits.
                if over < -1e-9 or (over <= 1e-9 and d < -1e-9):
                    bins[i].remove(p); bins[j].append(p)
                    bins[j].remove(q); bins[i].append(q)
                    pos[p], pos[q] = j, i
                    improved = True
                    break
                move_delta_apply(q, i, j)
                move_delta_apply(p, j, i)
        if not improved:
            break
    return bins


def bins_feasible(
    bins: List[List[str]], st: Stations, prod_lines: Dict[str, int]
) -> Tuple[bool, np.ndarray]:
    """(all stations within slots + the [lo, tcap] workload band, loads)."""
    load = layout_loads(bins, st, prod_lines)
    ok = all(len(bins[i]) <= st.cap[i]
             and st.lo[i] - 1e-6 <= load[i] <= st.tcap[i] + 1e-6
             for i in range(st.n))
    return ok, load


# ---------------------------------------------------------------------------
#  HEURISTIC PRICING (per target station)
# ---------------------------------------------------------------------------
def heuristic_pricing_hetero(
    s: int,
    sidx: SupportIndex,
    products: List[str],
    sigma: Dict[str, float],
    mu_s: float,
    prod_lines: Dict[str, int],
    st: Stations,
) -> Tuple[Optional[List[str]], float]:
    """Best-prefix dual greedy for station s (caps zeta_s, T_s, speed V_s)."""
    best_pat: Optional[List[str]] = None
    best_rc = 0.0
    cands = [p for p in products if sigma.get(p, 0.0) > 1e-9]
    if not cands:
        return None, 0.0
    orderings = [
        sorted(cands, key=lambda p: -sigma[p]),
        sorted(cands, key=lambda p: -sigma[p] / max(st.wl(prod_lines.get(p, 0), s), 1e-9)),
    ]
    for ordering in orderings:
        covered = np.zeros(sidx.n, dtype=bool)
        rc = -mu_s
        tload = 0.0
        pat: List[str] = []
        cur_best_rc, cur_best_len = rc, 0
        for p in ordering:
            if len(pat) >= st.cap[s]:
                break
            wl = st.wl(prod_lines.get(p, 0), s)
            if tload + wl > st.tcap[s]:
                continue
            idx = sidx.prod_to_sup.get(p)
            new_w = 0.0
            if idx is not None:
                newly = idx[~covered[idx]]
                new_w = float(sidx.weights[newly].sum())
                covered[newly] = True
            rc += new_w - sigma[p]
            pat.append(p)
            tload += wl
            # A prefix is a candidate column only once the workload floor
            # (equilibrium band) of the target station is reached.
            if tload >= st.lo[s] and rc < cur_best_rc:
                cur_best_rc, cur_best_len = rc, len(pat)
        if cur_best_len > 0 and cur_best_rc < best_rc:
            best_rc = cur_best_rc
            best_pat = pat[:cur_best_len]
    return best_pat, best_rc


# ---------------------------------------------------------------------------
#  PARTITION COMPLETION (fills every station to its own cap profile)
# ---------------------------------------------------------------------------
def complete_layout(
    seed_station: int,
    seed_bundle: Sequence[str],
    products: List[str],
    sidx: SupportIndex,
    prod_lines: Dict[str, int],
    st: Stations,
) -> List[List[str]]:
    """Complete a priced (station, bundle) seed into a full feasible layout.

    Remaining products, heaviest first, join the feasible station of maximum
    co-occurrence affinity (weight of the product's supports already touched
    by that station). Workload-infeasible leftovers go to the least-loaded
    station with a free slot; the swap descent repairs afterwards.
    """
    bins: List[List[str]] = [[] for _ in range(st.n)]
    bins[seed_station] = list(seed_bundle)[: int(st.cap[seed_station])]
    assigned = set(bins[seed_station])
    load = np.zeros(st.n)
    touched = [np.zeros(sidx.n, dtype=bool) for _ in range(st.n)]
    for p in bins[seed_station]:
        load[seed_station] += st.wl(prod_lines.get(p, 0), seed_station)
        idx = sidx.prod_to_sup.get(p)
        if idx is not None:
            touched[seed_station][idx] = True
    remaining = [p for p in products if p not in assigned]
    for p in sorted(remaining, key=lambda q: -prod_lines.get(q, 0)):
        lines = prod_lines.get(p, 0)
        idx = sidx.prod_to_sup.get(p)
        best_i, best_aff = -1, -1.0
        fb_i, fb_load = -1, float("inf")
        for i in range(st.n):
            if len(bins[i]) >= st.cap[i]:
                continue
            if load[i] + st.wl(lines, i) <= st.tcap[i]:
                aff = (float(sidx.weights[idx[touched[i][idx]]].sum())
                       if idx is not None else 0.0)
                if aff > best_aff:
                    best_aff, best_i = aff, i
            rel = load[i] / max(st.tcap[i], 1e-9)
            if rel < fb_load:
                fb_load, fb_i = rel, i
        tgt = best_i if best_i >= 0 else fb_i
        if tgt < 0:
            continue
        bins[tgt].append(p)
        load[tgt] += st.wl(lines, tgt)
        if idx is not None:
            touched[tgt][idx] = True
    return bins


def recomplete_from_incumbent(
    inc_bins: List[List[str]],
    seed_station: int,
    seed_bundle: Sequence[str],
    sidx: SupportIndex,
    prod_lines: Dict[str, int],
    st: Stations,
) -> List[List[str]]:
    """Install a priced bundle into the INCUMBENT layout (ejection style).

    The bundle's products are evicted from wherever they sit, the target
    station is rebuilt as the bundle, and the displaced former occupants of
    the target station are reinserted, heaviest first, into the freed slots by
    maximum co-occurrence affinity. Slot conservation holds because the bundle
    frees exactly as many slots elsewhere as the displacement creates. This
    preserves the incumbent everywhere the bundle does not touch, unlike a
    from-scratch completion.
    """
    bundle = list(seed_bundle)[: int(st.cap[seed_station])]
    bset = set(bundle)
    bins = [[p for p in b if p not in bset] for b in inc_bins]
    displaced = [p for p in bins[seed_station]]
    bins[seed_station] = bundle
    load = layout_loads(bins, st, prod_lines)
    touched = [np.zeros(sidx.n, dtype=bool) for _ in range(st.n)]
    for i in range(st.n):
        for p in bins[i]:
            idx = sidx.prod_to_sup.get(p)
            if idx is not None:
                touched[i][idx] = True
    for p in sorted(displaced, key=lambda q: -prod_lines.get(q, 0)):
        lines = prod_lines.get(p, 0)
        idx = sidx.prod_to_sup.get(p)
        best_i, best_aff = -1, -1.0
        fb_i, fb_rel = -1, float("inf")
        for i in range(st.n):
            if len(bins[i]) >= st.cap[i]:
                continue
            if load[i] + st.wl(lines, i) <= st.tcap[i]:
                aff = (float(sidx.weights[idx[touched[i][idx]]].sum())
                       if idx is not None else 0.0)
                if aff > best_aff:
                    best_aff, best_i = aff, i
            rel = load[i] / max(st.tcap[i], 1e-9)
            if rel < fb_rel:
                fb_rel, fb_i = rel, i
        tgt = best_i if best_i >= 0 else fb_i
        if tgt < 0:
            continue
        bins[tgt].append(p)
        load[tgt] += st.wl(lines, tgt)
        if idx is not None:
            touched[tgt][idx] = True
    return bins


# ---------------------------------------------------------------------------
#  EXACT PRICER (one persistent MILP; per-station RHS swap)
# ---------------------------------------------------------------------------
class ExactPricerHetero:
    """Persistent pricing MILP shared by all stations.

    Station-independent: the z/link block and the L_p coefficients of the
    workload row. Per call: objective coefficients (duals) and the two RHS
    values (zeta_s, T_s*V_s). A bound pass reuses one dual vector and only
    swaps RHS 24 times.
    """

    def __init__(
        self,
        sidx: SupportIndex,
        products: List[str],
        prod_lines: Dict[str, int],
        threads: int,
        pool_cap: int = 10,
    ) -> None:
        self.products = products
        m = cplex.Cplex()
        for stream in (m.set_log_stream, m.set_results_stream, m.set_warning_stream):
            stream(None)
        m.parameters.threads.set(threads)
        m.parameters.mip.pool.capacity.set(pool_cap)
        m.objective.set_sense(m.objective.sense.minimize)
        n_p, n_u = len(products), sidx.n
        m.variables.add(obj=[0.0] * n_p, lb=[0] * n_p, ub=[1] * n_p,
                        types=["B"] * n_p)
        m.variables.add(obj=list(sidx.weights), lb=[0.0] * n_u, ub=[1.0] * n_u)
        self.z_off = n_p
        pidx = {p: j for j, p in enumerate(products)}
        rows, senses, rhs = [], [], []
        for u, sup in enumerate(sidx.supports):
            for p in sup:
                j = pidx.get(p)
                if j is not None:
                    rows.append(cplex.SparsePair([self.z_off + u, j], [1.0, -1.0]))
                    senses.append("G")
                    rhs.append(0.0)
        rows.append(cplex.SparsePair(list(range(n_p)), [1.0] * n_p))
        senses.append("L")
        rhs.append(1.0)  # placeholder: zeta_s per call
        wl_coef = [float(prod_lines.get(p, 0)) for p in products]
        rows.append(cplex.SparsePair(list(range(n_p)), wl_coef))
        senses.append("L")
        rhs.append(1.0)  # placeholder: T_s * V_s per call
        rows.append(cplex.SparsePair(list(range(n_p)), wl_coef))
        senses.append("G")
        rhs.append(0.0)  # placeholder: lo_s * V_s per call (workload floor)
        m.linear_constraints.add(lin_expr=rows, senses=senses, rhs=rhs)
        self.cap_row = len(rhs) - 3
        self.wl_row = len(rhs) - 2
        self.wl_lo_row = len(rhs) - 1
        self.m = m

    def set_duals(self, sigma: Dict[str, float]) -> None:
        """Rewrite objective coefficients once per dual vector."""
        self.m.objective.set_linear(
            [(j, -float(sigma.get(p, 0.0))) for j, p in enumerate(self.products)]
        )

    def price_station(
        self, s: int, st: Stations, mu_s: float, time_limit: float
    ) -> Tuple[List[Tuple[List[str], float]], float, bool]:
        """Solve pricing for station s at the currently set duals."""
        m = self.m
        m.linear_constraints.set_rhs(
            [(self.cap_row, float(st.cap[s])),
             (self.wl_row, float(st.tcap[s] * st.speed[s])),
             (self.wl_lo_row, float(st.lo[s] * st.speed[s]))]
        )
        m.parameters.timelimit.set(max(1.0, time_limit))
        m.solve()
        status = m.solution.get_status()
        optimal = status in (
            m.solution.status.MIP_optimal,
            getattr(m.solution.status, "optimal_tolerance", -1),
        )
        try:
            rc_lb = m.solution.MIP.get_best_objective() - mu_s
        except cplex.exceptions.CplexError:
            rc_lb = -float("inf")
        cols: List[Tuple[List[str], float]] = []
        try:
            n_sol = m.solution.pool.get_num()
        except cplex.exceptions.CplexError:
            n_sol = 0
        n_p = len(self.products)
        seen = set()
        for i in range(n_sol):
            rc = m.solution.pool.get_objective_value(i) - mu_s
            if rc < EPS_RC:
                vals = m.solution.pool.get_values(i, list(range(n_p)))
                pat = [self.products[j] for j, v in enumerate(vals) if v > 0.5]
                key = frozenset(pat)
                if pat and key not in seen:
                    seen.add(key)
                    cols.append((pat, rc))
        return cols, rc_lb, optimal


# ---------------------------------------------------------------------------
#  MASTER (covering + per-station convexity rows)
# ---------------------------------------------------------------------------
class MasterHetero:
    """Incremental RMP with station-tagged columns."""

    def __init__(self, products: List[str], st: Stations, threads: int) -> None:
        m = cplex.Cplex()
        for stream in (m.set_log_stream, m.set_results_stream, m.set_warning_stream):
            stream(None)
        m.parameters.threads.set(threads)
        m.objective.set_sense(m.objective.sense.minimize)
        self.products = products
        self.pidx = {p: i for i, p in enumerate(products)}
        n_p = len(products)
        m.linear_constraints.add(
            lin_expr=[cplex.SparsePair([], [])] * n_p,
            senses=["G"] * n_p, rhs=[1.0] * n_p,
        )
        m.linear_constraints.add(
            lin_expr=[cplex.SparsePair([], [])] * st.n,
            senses=["L"] * st.n, rhs=[1.0] * st.n,
        )
        self.pat_row0 = n_p
        self.st = st
        self.m = m
        self.patterns: List[Tuple[int, List[str]]] = []  # (station, products)
        self.costs: List[float] = []
        self.keys: set = set()

    def add_column(self, s: int, pattern: Sequence[str], cost: float) -> bool:
        key = (s, frozenset(pattern))
        if not pattern or key in self.keys:
            return False
        self.keys.add(key)
        rows = [self.pidx[p] for p in pattern] + [self.pat_row0 + s]
        vals = [1.0] * len(pattern) + [1.0]
        self.m.variables.add(obj=[cost], lb=[0.0], ub=[1.0],
                             columns=[cplex.SparsePair(rows, vals)])
        self.patterns.append((s, list(pattern)))
        self.costs.append(cost)
        return True

    def solve_lp(self) -> Tuple[float, Dict[str, float], np.ndarray]:
        self.m.set_problem_type(self.m.problem_type.LP)
        self.m.solve()
        obj = self.m.solution.get_objective_value()
        duals = self.m.solution.get_dual_values()
        sigma = {p: max(0.0, duals[i]) for p, i in self.pidx.items()}
        mu = np.minimum(0.0, np.array(
            duals[self.pat_row0:self.pat_row0 + self.st.n]))
        return obj, sigma, mu

    def solve_ip(self, time_limit: float) -> List[int]:
        n = len(self.patterns)
        self.m.variables.set_types([(j, "B") for j in range(n)])
        self.m.parameters.timelimit.set(max(10.0, time_limit))
        self.m.parameters.mip.tolerances.mipgap.set(1e-6)
        self.m.solve()
        vals = self.m.solution.get_values()
        return [j for j in range(n) if vals[j] > 0.5]


# ---------------------------------------------------------------------------
#  MAIN SOLVER
# ---------------------------------------------------------------------------
def run_cg_setpart_hetero(
    order_prods: Dict[str, List[str]],
    stations: List[dict],
    products: List[str],
    prod_lines: Dict[str, int],
    time_limit: int = 36000,
    threads: int = 4,
    warm_start_assignment: Optional[Dict[str, str]] = None,
    exact_call_cap: float = 300.0,
    bound_call_cap: float = 150.0,
    seed: int = 42,
    verbose: bool = True,
) -> Tuple[Optional[Dict[str, str]], Optional[int], float,
           Optional[float], Optional[float], Optional[int], Optional[int],
           Optional[float]]:
    """Heterogeneous price-and-complete CG; returns the standard 8-tuple.

    ``assignment`` maps product -> STATION_ID (solver products only; the
    caller merges statically fixed SKUs before full evaluation). Visits are
    counted on the solver order stream; ``best_bound`` is the per-station
    Farley bound from the final bound pass (or None).
    """
    t0 = time.time()
    rng = random.Random(seed)
    st = Stations(stations)
    supports, weights = aggregate_supports(order_prods)
    sidx = SupportIndex(supports, weights)
    overload_penalty = float(sidx.weights.sum())
    if verbose:
        print(f"  CG-H: |P|={len(products)} |S|={st.n} |U|={sidx.n} "
              f"caps[{st.cap.min()},{st.cap.max()}] tl={time_limit}s", flush=True)

    # ---- warm start = original industrial layout ---------------------------
    if warm_start_assignment:
        bins: List[List[str]] = [[] for _ in range(st.n)]
        for p in products:
            sid = warm_start_assignment.get(p)
            i = st.idx.get(str(sid), None)
            if i is None:
                i = int(np.argmin([len(b) for b in bins]))
            bins[i].append(p)
    else:
        order = sorted(products, key=lambda q: -prod_lines.get(q, 0))
        bins = [[] for _ in range(st.n)]
        load = np.zeros(st.n)
        for p in order:
            feas = [i for i in range(st.n) if len(bins[i]) < st.cap[i]]
            tgt = min(feas, key=lambda i: load[i] / max(st.tcap[i], 1e-9))
            bins[tgt].append(p)
            load[tgt] += st.wl(prod_lines.get(p, 0), tgt)

    polish_end = t0 + min(0.05 * time_limit, 1800.0)
    bins = swap_descent_hetero(bins, sidx, prod_lines, st, polish_end, rng,
                               overload_penalty)
    inc_bins = [list(b) for b in bins]
    inc_assign = {p: i for i, b in enumerate(bins) for p in b}
    inc_visits = evaluate_assignment(inc_assign, order_prods)
    if verbose:
        print(f"  CG-H: polished warm start visits={inc_visits} "
              f"({round(time.time()-t0,1)}s)", flush=True)

    master = MasterHetero(products, st, threads)
    for i, b in enumerate(bins):
        master.add_column(i, b, sidx.column_cost(b))

    t_build = time.time()
    pricer = ExactPricerHetero(sidx, products, prod_lines, threads)
    if verbose:
        print(f"  CG-H: pricing MILP built once ({round(time.time()-t_build,1)}s)",
              flush=True)

    # ---- CG loop (round-robin target station) ------------------------------
    cg_deadline = t0 + 0.62 * time_limit
    it = n_exact = n_heur_cols = 0
    target = 0
    while time.time() < cg_deadline:
        it += 1
        rmp_obj, sigma, mu = master.solve_lp()
        if verbose and (it <= 3 or it % 5 == 0):
            print(f"  it{it}: RMP={rmp_obj:.0f} cols={len(master.patterns)} "
                  f"inc={inc_visits} ({round(time.time()-t0,1)}s)", flush=True)
        s = target % st.n
        target += 1

        added = False
        # Bonus heuristic column (cheap; never gates the exact pricer).
        pat, rc = heuristic_pricing_hetero(s, sidx, products, sigma,
                                           float(mu[s]), prod_lines, st)
        if pat is not None and rc < EPS_RC:
            if master.add_column(s, pat, sidx.column_cost(pat)):
                added = True
                n_heur_cols += 1

        # Exact pricing EVERY iteration on the target station.
        n_exact += 1
        budget = min(exact_call_cap, max(10.0, cg_deadline - time.time()))
        pricer.set_duals(sigma)
        cols, _rc_lb, _opt = pricer.price_station(s, st, float(mu[s]), budget)
        for cpat, _crc in cols:
            if master.add_column(s, cpat, sidx.column_cost(cpat)):
                added = True
        new_bundle: Optional[List[str]] = cols[0][0] if cols else (
            pat if (pat is not None and rc < EPS_RC) else None)

        if new_bundle is not None:
            # Ejection-style install into the incumbent (preserves context).
            part = recomplete_from_incumbent(inc_bins, s, new_bundle,
                                             sidx, prod_lines, st)
            part = swap_descent_hetero(
                part, sidx, prod_lines, st,
                time.time() + min(90.0, 0.01 * time_limit), rng,
                overload_penalty)
            feas, load = bins_feasible(part, st, prod_lines)
            for i, b in enumerate(part):
                if (b and len(b) <= st.cap[i]
                        and load[i] <= st.tcap[i] + 1e-6):
                    if master.add_column(i, b, sidx.column_cost(b)):
                        added = True
            if feas:
                pa = {p: i for i, b in enumerate(part) for p in b}
                pv = evaluate_assignment(pa, order_prods)
                if pv < inc_visits:
                    inc_visits, inc_assign, inc_bins = pv, pa, part
                    if verbose:
                        print(f"  it{it}: new incumbent visits={pv}", flush=True)
        if not added:
            if verbose:
                print("  CG-H: no new column this iteration; continue cycle",
                      flush=True)

    # ---- bound pass: all stations priced at ONE dual vector ----------------
    best_lb: Optional[float] = None
    bound_deadline = t0 + 0.74 * time_limit
    if time.time() < bound_deadline - 30:
        rmp_obj, sigma, mu = master.solve_lp()
        pricer.set_duals(sigma)
        rc_lbs: List[float] = []
        all_valid = True
        for s in range(st.n):
            budget = min(bound_call_cap, max(5.0, bound_deadline - time.time()))
            if budget <= 5.0 and s < st.n - 1:
                all_valid = False
                break
            _cols, rc_lb, _opt = pricer.price_station(s, st, float(mu[s]), budget)
            if rc_lb == -float("inf"):
                all_valid = False
                break
            rc_lbs.append(min(0.0, rc_lb))
        if all_valid and len(rc_lbs) == st.n:
            best_lb = rmp_obj + float(np.sum(rc_lbs))
            if verbose:
                print(f"  CG-H: bound pass LB={best_lb:.0f} "
                      f"(RMP={rmp_obj:.0f})", flush=True)
        elif verbose:
            print("  CG-H: bound pass incomplete; no valid LB reported", flush=True)

    # ---- integer master + dedup + final polish ------------------------------
    imp_budget = max(30.0, t0 + 0.82 * time_limit - time.time())
    chosen = master.solve_ip(imp_budget)
    ip_bins: List[List[str]] = [[] for _ in range(st.n)]
    placed: Dict[str, int] = {}
    for j in chosen:
        s, pat = master.patterns[j]
        for p in pat:
            if p in placed:   # dedup: keep max co-occurrence home
                idx = sidx.prod_to_sup.get(p, np.zeros(0, dtype=np.int64))
                def aff(stn: int) -> float:
                    t = np.zeros(sidx.n, dtype=bool)
                    for q in ip_bins[stn]:
                        qi = sidx.prod_to_sup.get(q)
                        if qi is not None:
                            t[qi] = True
                    return float(sidx.weights[idx[t[idx]]].sum())
                if aff(s) > aff(placed[p]):
                    ip_bins[placed[p]].remove(p)
                    ip_bins[s].append(p)
                    placed[p] = s
                continue
            ip_bins[s].append(p)
            placed[p] = s
    missing = [p for p in products if p not in placed]
    for p in missing:
        feas = [i for i in range(st.n) if len(ip_bins[i]) < st.cap[i]]
        tgt = feas[0] if feas else int(np.argmin([len(b) for b in ip_bins]))
        ip_bins[tgt].append(p)
        placed[p] = tgt
    ip_assign = {p: i for i, b in enumerate(ip_bins) for p in b}
    ip_visits = evaluate_assignment(ip_assign, order_prods)
    if ip_visits < inc_visits:
        feas_ip, _ = bins_feasible(ip_bins, st, prod_lines)
        if feas_ip:
            inc_visits, inc_assign, inc_bins = ip_visits, ip_assign, ip_bins

    final_deadline = t0 + time_limit - 60.0
    if time.time() < final_deadline:
        fb = swap_descent_hetero(inc_bins, sidx, prod_lines, st,
                                 final_deadline, rng, overload_penalty)
        fa = {p: i for i, b in enumerate(fb) for p in b}
        fv = evaluate_assignment(fa, order_prods)
        if fv < inc_visits:
            inc_visits, inc_assign, inc_bins = fv, fa, fb

    _feas, load = bins_feasible(inc_bins, st, prod_lines)
    cap_broken = sum(1 for i in range(st.n) if len(inc_bins[i]) > st.cap[i])
    wl_broken = sum(1 for i in range(st.n) if load[i] > st.tcap[i] + 1e-6)
    elapsed = time.time() - t0
    if verbose:
        print(f"  CG-H done: visits={inc_visits} LB={best_lb} it={it} "
              f"cols={len(master.patterns)} exact={n_exact} heur={n_heur_cols} "
              f"{elapsed:.0f}s cap_broken={cap_broken} wl_broken={wl_broken}",
              flush=True)
    assignment = {p: st.ids[i] for p, i in inc_assign.items()}
    return (assignment, inc_visits, elapsed, float(np.var(load)),
            float(load.max()), cap_broken, wl_broken, best_lb)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Heterogeneous set-partitioning CG for CSLAP (CPLEX)")
    parser.add_argument("--prefix", type=str, required=True)
    parser.add_argument("--dir", type=str, default="exp02a_instances")
    parser.add_argument("--time", type=int, default=3600)
    args = parser.parse_args()
    from cg_setpart_cplex import read_data
    op, stns, pr, pl = read_data(args.prefix, args.dir)
    run_cg_setpart_hetero(op, stns, pr, pl, time_limit=args.time)
