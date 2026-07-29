r"""
Aggregated Set-Partitioning Column Generation for flat-warehouse CSLAP (CPLEX).

Direct-solver reformulation of the CG approach: on a FLAT warehouse (all
stations identical: same slot capacity :math:`C`, speed :math:`V`, workload cap
:math:`T`), columns are station-agnostic product bundles and the master is a
pure set-covering/partitioning LP with a SINGLE cardinality (convexity) row and
a SINGLE pricing subproblem -- instead of one pattern family and one pricing
MILP per station. This removes the two structural defects identified in the
scientific review of the per-station CG: per-station pricing multiplicity and
the symmetric, degenerate per-station convexity rows.

Master (RMP), continuous relaxation
-----------------------------------
.. math::
    \min \sum_{q \in Q'} c_q\, x_q
    \quad\text{s.t.}\quad
    \sum_{q \ni p} x_q \ge 1 \;(\sigma_p \ge 0) \;\; \forall p \in P, \qquad
    \sum_{q \in Q'} x_q \le |S| \;(\mu \le 0), \qquad 0 \le x_q \le 1,

with column cost :math:`c_q = \sum_{u \in U} w_u\, \mathbf{1}[q \cap u \neq
\emptyset]` where :math:`U` is the set of DISTINCT multi-item order supports
and :math:`w_u` their multiplicities (order aggregation).  Since every station
is identical, :math:`\sum_o \text{visits}(o) = \sum_q c_q x_q` for a partition:
the master objective IS the CSLAP objective.  With tight capacity
(:math:`|P| = |S| \cdot C`, as in all exp02a instances) any integer covering
solution is automatically an exact partition into :math:`|S|` full bundles.

Pricing (single subproblem; built ONCE, re-priced by objective update)
----------------------------------------------------------------------
.. math::
    \min\; \sum_{u \in U} w_u z_u - \sum_{p \in P} \sigma_p a_p - \mu
    \quad\text{s.t.}\quad
    z_u \ge a_p \;\forall u, p \in u; \;\;
    \sum_p a_p \le C; \;\;
    \sum_p \tfrac{L_p}{V} a_p \le T; \;\; a_p \in \{0,1\},\; z_u \in [0,1].

Because the constraint matrix is dual-independent, the pricing MILP is
constructed a single time and each exact call only rewrites the linear
objective coefficients of the :math:`a_p` variables -- this is what makes exact
pricing affordable at ~67k distinct supports (2000-SKU instances).

Acceleration (kept from the reviewed design, defects fixed)
-----------------------------------------------------------
* Two-phase pricing: an incremental dual-greedy heuristic (best-prefix reduced
  cost, two candidate orderings) runs first; the exact CPLEX MILP (solution
  pool <= ``pool_cap`` columns) is the fallback and the sole convergence proof.
* Heuristic pricing always evaluated at the TRUE duals; a stall trigger forces
  the exact pricer whenever the RMP value stops improving, so degenerate
  heuristic columns cannot starve the exact phase (convergence is only ever
  declared from an EXACT pricing solve at true duals).
* Farley/convexity Lagrangian bound  :math:`LB = z_{RMP} + |S|\cdot
  \min(0, rc^*)`  tracked ONLY when the exact pricing solved to proven
  optimality; the returned ``best_bound`` is therefore always valid.
* Final integer master (price-and-branch) over the generated pool, followed by
  an explicit duplicate-coverage repair (never the silent dict overwrite of the
  per-station implementation); all reported visits are re-counted on the REAL
  orders from the repaired assignment.

CLI
---
``--prefix`` / ``--dir`` / ``--time`` per code-standards, plus solver knobs.
Returns the standard 8-tuple
``(assignment, total_visits, elapsed, util_variance, max_util, cap_broken,
wl_broken, best_bound)``.
"""

from __future__ import annotations

import argparse
import os
import random
import time
from collections import defaultdict
from typing import Dict, FrozenSet, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

import cplex  # IBM CPLEX python API (Virtual_Environment_CPLEX_1)

Pattern = FrozenSet[str]
EPS_RC = -1e-6


# ---------------------------------------------------------------------------
#  DATA
# ---------------------------------------------------------------------------
def read_data(
    prefix: str, data_dir: str
) -> Tuple[Dict[str, List[str]], List[dict], List[str], Dict[str, int]]:
    """Read the standard semicolon CSLAP CSVs (same schema as the baselines)."""
    orders_df = pd.read_csv(os.path.join(data_dir, f"{prefix}_orders.csv"), sep=";")
    stations_df = pd.read_csv(os.path.join(data_dir, f"{prefix}_stations.csv"), sep=";")
    products_df = pd.read_csv(os.path.join(data_dir, f"{prefix}_products.csv"), sep=";")
    prod_lines = orders_df.groupby("PRODUCT").size().to_dict()
    order_prods = orders_df.groupby("ORDER")["PRODUCT"].apply(list).to_dict()
    stations = stations_df.to_dict(orient="records")
    products = products_df["PRODUCT_ID"].apply(lambda x: f"PROD_{x}").tolist()
    return order_prods, stations, products, prod_lines


def check_flat(stations: List[dict]) -> Tuple[int, int, float, float]:
    """Assert the warehouse is flat; return (n_stations, C, T, V)."""
    caps = {s["CAPACITY"] for s in stations}
    tcs = {s["TIME_CAPACITY"] for s in stations}
    spd = {s["SPEED"] for s in stations}
    if len(caps) > 1 or len(tcs) > 1 or len(spd) > 1:
        raise ValueError(
            "cg_setpart_cplex requires a FLAT warehouse (identical stations); "
            f"got CAPACITY={caps}, TIME_CAPACITY={tcs}, SPEED={spd}"
        )
    return len(stations), int(caps.pop()), float(tcs.pop()), float(spd.pop())


def aggregate_supports(
    order_prods: Dict[str, List[str]]
) -> Tuple[List[FrozenSet[str]], List[int]]:
    """Distinct multi-item supports U with multiplicity weights w_u."""
    cnt: Dict[FrozenSet[str], int] = defaultdict(int)
    for prods in order_prods.values():
        s = frozenset(prods)
        if len(s) >= 2:
            cnt[s] += 1
    supports = list(cnt.keys())
    weights = [cnt[s] for s in supports]
    return supports, weights


# ---------------------------------------------------------------------------
#  EVALUATION (real orders, real assignment)
# ---------------------------------------------------------------------------
def evaluate_assignment(
    assignment: Dict[str, int], order_prods: Dict[str, List[str]]
) -> int:
    """Total station visits of the REAL order stream under the assignment."""
    total = 0
    for prods in order_prods.values():
        total += len({assignment[p] for p in prods if p in assignment})
    return total


def workload_stats(
    assignment: Dict[str, int],
    prod_lines: Dict[str, int],
    n_stations: int,
    cap: int,
    time_cap: float,
    speed: float,
) -> Tuple[float, float, int, int]:
    """Per-station (util_variance, max_util, cap_broken, wl_broken)."""
    load = [0.0] * n_stations
    slots = [0] * n_stations
    for p, s in assignment.items():
        load[s] += prod_lines.get(p, 0) / speed
        slots[s] += 1
    cap_broken = sum(1 for c in slots if c > cap)
    wl_broken = sum(1 for w in load if w > time_cap + 1e-9)
    return float(np.var(load)), float(max(load)), cap_broken, wl_broken


# ---------------------------------------------------------------------------
#  INITIAL COLUMNS (feasible warm start + mutations)
# ---------------------------------------------------------------------------
def warm_start_partition(
    products: List[str],
    prod_lines: Dict[str, int],
    n_stations: int,
    cap: int,
    time_cap: float,
    speed: float,
) -> List[List[str]]:
    """LPT-style feasible partition: heaviest product to least-loaded open station."""
    bins: List[List[str]] = [[] for _ in range(n_stations)]
    load = [0.0] * n_stations
    for p in sorted(products, key=lambda q: -prod_lines.get(q, 0)):
        w = prod_lines.get(p, 0) / speed
        cands = [i for i in range(n_stations) if len(bins[i]) < cap]
        feas = [i for i in cands if load[i] + w <= time_cap]
        tgt = min(feas or cands, key=lambda i: load[i])
        bins[tgt].append(p)
        load[tgt] += w
    return bins


def mutate_partition(
    bins: List[List[str]],
    prod_lines: Dict[str, int],
    cap: int,
    time_cap: float,
    speed: float,
    rng: random.Random,
    n_rounds: int,
) -> List[List[str]]:
    """Displace 5-10% of products, reassign greedily; STRICT cap+workload.

    Products that cannot be feasibly re-placed are dropped from the mutated
    bundle (columns need not be partitions), so no infeasible column is ever
    injected -- fixes review findings F5/F6 of the per-station CG code.
    """
    out: List[List[str]] = []
    n_st = len(bins)
    for _ in range(n_rounds):
        cur = [list(b) for b in bins]
        load = [sum(prod_lines.get(p, 0) / speed for p in b) for b in cur]
        pairs = [(p, i) for i in range(n_st) for p in cur[i]]
        k = max(1, int(len(pairs) * rng.uniform(0.05, 0.10)))
        moved = rng.sample(pairs, min(k, len(pairs)))
        pool: List[str] = []
        for p, i in moved:
            cur[i].remove(p)
            load[i] -= prod_lines.get(p, 0) / speed
            pool.append(p)
        rng.shuffle(pool)
        for p in pool:
            w = prod_lines.get(p, 0) / speed
            order = list(range(n_st))
            rng.shuffle(order)
            for i in order:
                if len(cur[i]) < cap and load[i] + w <= time_cap:
                    cur[i].append(p)
                    load[i] += w
                    break
            # else: dropped (feasibility over coverage for mutated columns)
        out.extend([b for b in cur if b])
    return out


# ---------------------------------------------------------------------------
#  COLUMN COST
# ---------------------------------------------------------------------------
class SupportIndex:
    """Inverted index product -> support ids, and support weights."""

    def __init__(self, supports: List[FrozenSet[str]], weights: List[int]) -> None:
        self.supports = supports
        self.weights = np.asarray(weights, dtype=np.float64)
        self.n = len(supports)
        self.prod_to_sup: Dict[str, np.ndarray] = {}
        tmp: Dict[str, List[int]] = defaultdict(list)
        for i, s in enumerate(supports):
            for p in s:
                tmp[p].append(i)
        for p, lst in tmp.items():
            self.prod_to_sup[p] = np.asarray(lst, dtype=np.int64)

    def column_cost(self, pattern: Sequence[str]) -> float:
        """c_q = sum of w_u over supports touched by the pattern."""
        touched = np.zeros(self.n, dtype=bool)
        for p in pattern:
            idx = self.prod_to_sup.get(p)
            if idx is not None:
                touched[idx] = True
        return float(self.weights[touched].sum())


# ---------------------------------------------------------------------------
#  HEURISTIC PRICING (incremental best-prefix reduced cost)
# ---------------------------------------------------------------------------
def heuristic_pricing(
    sidx: SupportIndex,
    products: List[str],
    sigma: Dict[str, float],
    mu: float,
    prod_lines: Dict[str, int],
    cap: int,
    time_cap: float,
    speed: float,
) -> Tuple[Optional[List[str]], float]:
    """Greedy pricing; returns (pattern, rc) of the best PREFIX found.

    Tries two candidate orderings (sigma desc; sigma/time desc) and tracks the
    exact reduced cost incrementally after each addition, returning the prefix
    with the minimum rc (fixes review finding F12: no blind fill-up).
    """
    best_pat: Optional[List[str]] = None
    best_rc = 0.0
    cands = [p for p in products if sigma.get(p, 0.0) > 1e-9]
    if not cands:
        return None, 0.0
    orderings = [
        sorted(cands, key=lambda p: -sigma[p]),
        sorted(cands, key=lambda p: -sigma[p] / max(prod_lines.get(p, 0) / speed, 1e-9)),
    ]
    for ordering in orderings:
        covered = np.zeros(sidx.n, dtype=bool)
        rc = -mu
        tload = 0.0
        pat: List[str] = []
        cur_best_rc, cur_best_len = rc, 0
        for p in ordering:
            if len(pat) >= cap:
                break
            w = prod_lines.get(p, 0) / speed
            if tload + w > time_cap:
                continue
            idx = sidx.prod_to_sup.get(p)
            new_w = 0.0
            if idx is not None:
                newly = idx[~covered[idx]]
                new_w = float(sidx.weights[newly].sum())
                covered[newly] = True
            rc += new_w - sigma[p]
            pat.append(p)
            tload += w
            if rc < cur_best_rc:
                cur_best_rc, cur_best_len = rc, len(pat)
        if cur_best_len > 0 and cur_best_rc < best_rc:
            best_rc = cur_best_rc
            best_pat = pat[:cur_best_len]
    return best_pat, best_rc


# ---------------------------------------------------------------------------
#  PARTITION COMPLETION (coordinated columns + primal incumbent)
# ---------------------------------------------------------------------------
def complete_partition(
    seeds: List[List[str]],
    products: List[str],
    sidx: SupportIndex,
    prod_lines: Dict[str, int],
    n_st: int,
    cap: int,
    time_cap: float,
    speed: float,
) -> List[List[str]]:
    """Complete disjoint seed bundles into a full feasible partition.

    Remaining products (heaviest first) go to the feasible bin with maximum
    co-occurrence overlap: the bin whose already-touched supports overlap most
    with the product's supports (= minimum marginal visit cost). The master's
    cardinality row makes single columns useless without compatible
    complements; completed partitions give the RMP/IMP coordinated column sets
    and yield a feasible incumbent every iteration.
    """
    bins: List[List[str]] = [list(b) for b in seeds[:n_st]]
    while len(bins) < n_st:
        bins.append([])
    assigned = {p for b in bins for p in b}
    load = [sum(prod_lines.get(p, 0) / speed for p in b) for b in bins]
    touched = [np.zeros(sidx.n, dtype=bool) for _ in range(n_st)]
    for i, b in enumerate(bins):
        for p in b:
            idx = sidx.prod_to_sup.get(p)
            if idx is not None:
                touched[i][idx] = True
    remaining = [p for p in products if p not in assigned]
    for p in sorted(remaining, key=lambda q: -prod_lines.get(q, 0)):
        w = prod_lines.get(p, 0) / speed
        idx = sidx.prod_to_sup.get(p)
        best_i, best_aff = -1, -1.0
        fallback_i, fallback_load = -1, float("inf")
        for i in range(n_st):
            if len(bins[i]) >= cap:
                continue
            if load[i] + w <= time_cap:
                aff = (float(sidx.weights[idx[touched[i][idx]]].sum())
                       if idx is not None else 0.0)
                if aff > best_aff:
                    best_aff, best_i = aff, i
            if load[i] < fallback_load:
                fallback_load, fallback_i = load[i], i
        tgt = best_i if best_i >= 0 else fallback_i
        if tgt < 0:  # no slot anywhere (cannot happen with |P| <= S*C)
            continue
        bins[tgt].append(p)
        load[tgt] += w
        if idx is not None:
            touched[tgt][idx] = True
    return [b for b in bins if b]


# ---------------------------------------------------------------------------
#  PENALIZED SWAP DESCENT (polish + workload repair)
# ---------------------------------------------------------------------------
def swap_descent(
    bins: List[List[str]],
    sidx: SupportIndex,
    prod_lines: Dict[str, int],
    time_cap: float,
    speed: float,
    deadline: float,
    rng: random.Random,
    overload_penalty: float,
) -> List[List[str]]:
    """First-improvement product-swap descent on visits + overload penalty.

    Objective: :math:`\\sum_u w_u |\\{i : q_i \\cap u \\neq \\emptyset\\}| +
    \\rho \\sum_i \\max(0, W_i - T)`.  Swap deltas are computed incrementally
    from a per-bin support-count matrix (``cnt[i][u]`` = products of bin i in
    support u), so one swap costs O(deg(p)+deg(q)).  Slot counts are preserved
    by swapping, and the overload penalty both repairs workload-infeasible
    partitions and never accepts a feasibility regression.
    """
    n_st = len(bins)
    bins = [list(b) for b in bins]
    cnt = np.zeros((n_st, sidx.n), dtype=np.int32)
    load = np.zeros(n_st)
    pos: Dict[str, int] = {}
    for i, b in enumerate(bins):
        for p in b:
            idx = sidx.prod_to_sup.get(p)
            if idx is not None:
                cnt[i][idx] += 1
            load[i] += prod_lines.get(p, 0) / speed
            pos[p] = i
    w = sidx.weights

    def move_delta_apply(p: str, src: int, dst: int) -> float:
        """Apply move p src->dst on cnt/load; return visit-cost delta."""
        d = 0.0
        idx = sidx.prod_to_sup.get(p)
        if idx is not None:
            c_src, c_dst = cnt[src][idx], cnt[dst][idx]
            d -= float(w[idx[c_src == 1]].sum())
            d += float(w[idx[c_dst == 0]].sum())
            cnt[src][idx] -= 1
            cnt[dst][idx] += 1
        wp = prod_lines.get(p, 0) / speed
        old_over = max(0.0, load[src] - time_cap) + max(0.0, load[dst] - time_cap)
        load[src] -= wp
        load[dst] += wp
        new_over = max(0.0, load[src] - time_cap) + max(0.0, load[dst] - time_cap)
        return d + overload_penalty * (new_over - old_over)

    prods = list(pos.keys())
    passes = 0
    n = len(prods)
    # Full pairwise scan is O(n^2); above ~300 products sample partners instead.
    n_partners = n if n <= 300 else 48
    while time.time() < deadline:
        passes += 1
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
                d = move_delta_apply(p, i, j)
                d += move_delta_apply(q, j, i)
                if d < -1e-9:
                    bins[i].remove(p); bins[j].append(p)
                    bins[j].remove(q); bins[i].append(q)
                    pos[p], pos[q] = j, i
                    improved = True
                    break  # first improvement: restart p's scan from new state
                # revert
                move_delta_apply(q, i, j)
                move_delta_apply(p, j, i)
        if not improved:
            break
    return bins


def bin_feasible(
    b: Sequence[str], prod_lines: Dict[str, int], cap: int,
    time_cap: float, speed: float,
) -> bool:
    """Slot + workload feasibility of a single bundle/column."""
    return (len(b) <= cap and
            sum(prod_lines.get(p, 0) / speed for p in b) <= time_cap + 1e-9)


# ---------------------------------------------------------------------------
#  EXACT PRICING (CPLEX MILP, built once)
# ---------------------------------------------------------------------------
class ExactPricer:
    """Persistent pricing MILP; per call only the objective is rewritten."""

    def __init__(
        self,
        sidx: SupportIndex,
        products: List[str],
        prod_lines: Dict[str, int],
        cap: int,
        time_cap: float,
        speed: float,
        threads: int,
        pool_cap: int,
    ) -> None:
        self.products = products
        self.pool_cap = pool_cap
        m = cplex.Cplex()
        for st in (m.set_log_stream, m.set_results_stream, m.set_warning_stream):
            st(None)
        m.parameters.threads.set(threads)
        m.parameters.mip.pool.capacity.set(pool_cap)
        m.parameters.mip.pool.intensity.set(2)
        m.objective.set_sense(m.objective.sense.minimize)

        n_p, n_u = len(products), sidx.n
        # a_p binary, z_u continuous [0,1]; z objective coeff = w_u (constant).
        m.variables.add(
            obj=[0.0] * n_p, lb=[0] * n_p, ub=[1] * n_p, types=["B"] * n_p,
            names=[f"a{j}" for j in range(n_p)],
        )
        m.variables.add(
            obj=list(sidx.weights), lb=[0.0] * n_u, ub=[1.0] * n_u,
            names=[f"z{u}" for u in range(n_u)],
        )
        self.a_off, self.z_off = 0, n_p
        pidx = {p: j for j, p in enumerate(products)}

        rows, senses, rhs = [], [], []
        for u, s in enumerate(sidx.supports):
            for p in s:
                j = pidx.get(p)
                if j is not None:
                    rows.append(cplex.SparsePair([self.z_off + u, j], [1.0, -1.0]))
                    senses.append("G")
                    rhs.append(0.0)
        rows.append(cplex.SparsePair(list(range(n_p)), [1.0] * n_p))
        senses.append("L")
        rhs.append(float(cap))
        rows.append(
            cplex.SparsePair(
                list(range(n_p)),
                [prod_lines.get(p, 0) / speed for p in products],
            )
        )
        senses.append("L")
        rhs.append(float(time_cap))
        m.linear_constraints.add(lin_expr=rows, senses=senses, rhs=rhs)
        self.m = m

    def price(
        self, sigma: Dict[str, float], mu: float, time_limit: float
    ) -> Tuple[List[Tuple[List[str], float]], float, bool]:
        """Solve pricing for duals (sigma, mu).

        Returns ``(cols, rc_lb, optimal)``: the negative-rc patterns harvested
        from the solution pool CPLEX fills during branch-and-cut, the VALID
        lower bound on the minimum reduced cost (MIP best bound minus mu --
        valid even on timeout, feeding the Farley bound), and whether the
        pricing was solved to proven optimality.
        """
        m = self.m
        m.objective.set_linear(
            [(j, -float(sigma.get(p, 0.0))) for j, p in enumerate(self.products)]
        )
        m.parameters.timelimit.set(max(1.0, time_limit))
        m.solve()
        status = m.solution.get_status()
        optimal = status in (
            m.solution.status.MIP_optimal,
            getattr(m.solution.status, "optimal_tolerance", -1),
        )
        try:
            rc_lb = m.solution.MIP.get_best_objective() - mu
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
            rc = m.solution.pool.get_objective_value(i) - mu
            if rc < EPS_RC:
                vals = m.solution.pool.get_values(i, list(range(n_p)))
                pat = [self.products[j] for j, v in enumerate(vals) if v > 0.5]
                key = frozenset(pat)
                if pat and key not in seen:
                    seen.add(key)
                    cols.append((pat, rc))
        return cols, rc_lb, optimal


# ---------------------------------------------------------------------------
#  MASTER (incremental CPLEX LP)
# ---------------------------------------------------------------------------
class Master:
    """Covering + single-cardinality restricted master, incremental columns."""

    def __init__(self, products: List[str], n_stations: int, threads: int) -> None:
        m = cplex.Cplex()
        for st in (m.set_log_stream, m.set_results_stream, m.set_warning_stream):
            st(None)
        m.parameters.threads.set(threads)
        m.objective.set_sense(m.objective.sense.minimize)
        self.products = products
        self.pidx = {p: i for i, p in enumerate(products)}
        n_p = len(products)
        m.linear_constraints.add(
            lin_expr=[cplex.SparsePair([], [])] * n_p,
            senses=["G"] * n_p,
            rhs=[1.0] * n_p,
            names=[f"cov{i}" for i in range(n_p)],
        )
        m.linear_constraints.add(
            lin_expr=[cplex.SparsePair([], [])],
            senses=["L"],
            rhs=[float(n_stations)],
            names=["card"],
        )
        self.card_row = n_p
        self.m = m
        self.patterns: List[List[str]] = []
        self.costs: List[float] = []
        self.keys: set = set()

    def add_column(self, pattern: Sequence[str], cost: float) -> bool:
        key = frozenset(pattern)
        if not pattern or key in self.keys:
            return False
        self.keys.add(key)
        rows = [self.pidx[p] for p in pattern] + [self.card_row]
        vals = [1.0] * len(pattern) + [1.0]
        self.m.variables.add(
            obj=[cost], lb=[0.0], ub=[1.0],
            columns=[cplex.SparsePair(rows, vals)],
        )
        self.patterns.append(list(pattern))
        self.costs.append(cost)
        return True

    def solve_lp(self) -> Tuple[float, Dict[str, float], float]:
        """Solve LP relaxation; return (obj, sigma, mu)."""
        self.m.set_problem_type(self.m.problem_type.LP)
        self.m.solve()
        obj = self.m.solution.get_objective_value()
        duals = self.m.solution.get_dual_values()
        sigma = {p: max(0.0, duals[i]) for p, i in self.pidx.items()}
        mu = min(0.0, duals[self.card_row])
        return obj, sigma, mu

    def solve_ip(self, time_limit: float) -> Tuple[List[int], float]:
        """Final integer master over the pool; returns (chosen ids, best bound)."""
        n = len(self.patterns)
        self.m.variables.set_types([(j, "B") for j in range(n)])
        self.m.parameters.timelimit.set(max(5.0, time_limit))
        self.m.parameters.mip.tolerances.mipgap.set(1e-6)
        self.m.solve()
        vals = self.m.solution.get_values()
        chosen = [j for j in range(n) if vals[j] > 0.5]
        return chosen, self.m.solution.MIP.get_best_objective()


# ---------------------------------------------------------------------------
#  DUPLICATE-COVERAGE REPAIR (explicit; replaces silent dict overwrite)
# ---------------------------------------------------------------------------
def build_assignment(
    chosen_patterns: List[List[str]],
    sidx: SupportIndex,
) -> Dict[str, int]:
    """Assign products to stations from the selected columns, deduplicating.

    A product covered by several selected columns is kept in the column whose
    other products share the most order-weight with it (max co-occurrence),
    and removed from the rest -- removals can only reduce visits.
    """
    where: Dict[str, List[int]] = defaultdict(list)
    for s, pat in enumerate(chosen_patterns):
        for p in pat:
            where[p].append(s)
    assignment: Dict[str, int] = {}
    for p, sts in where.items():
        if len(sts) == 1:
            assignment[p] = sts[0]
            continue
        p_sup = sidx.prod_to_sup.get(p, np.zeros(0, dtype=np.int64))
        p_mask = np.zeros(sidx.n, dtype=bool)
        p_mask[p_sup] = True
        best_s, best_w = sts[0], -1.0
        for s in sts:
            wsum = 0.0
            for q in chosen_patterns[s]:
                if q == p:
                    continue
                q_sup = sidx.prod_to_sup.get(q)
                if q_sup is not None:
                    wsum += float(sidx.weights[q_sup[p_mask[q_sup]]].sum())
            if wsum > best_w:
                best_w, best_s = wsum, s
        assignment[p] = best_s
    return assignment


# ---------------------------------------------------------------------------
#  MAIN SOLVER
# ---------------------------------------------------------------------------
def run_cg_setpart(
    order_prods: Dict[str, List[str]],
    stations: List[dict],
    products: List[str],
    prod_lines: Dict[str, int],
    time_limit: int = 120,
    threads: int = 4,
    pool_cap: int = 10,
    n_mutations: int = 20,
    imp_frac: float = 0.30,
    seed: int = 42,
    verbose: bool = True,
) -> Tuple[
    Optional[Dict[str, str]], Optional[int], float,
    Optional[float], Optional[float], Optional[int], Optional[int], Optional[float],
]:
    """Aggregated set-partitioning CG; returns the standard 8-tuple.

    ``(assignment, total_visits, elapsed, util_variance, max_util, cap_broken,
    wl_broken, best_bound)`` -- visits counted on the REAL orders,
    ``best_bound`` = max(valid Lagrangian bounds, IP best bound at proven LP
    optimum), or None when nothing was proven.
    """
    t0 = time.time()
    rng = random.Random(seed)
    n_st, cap, tcap, speed = check_flat(stations)
    supports, weights = aggregate_supports(order_prods)
    sidx = SupportIndex(supports, weights)
    n_single = sum(1 for pr in order_prods.values() if len(set(pr)) < 2)

    if verbose:
        print(f"  CG-SP: |P|={len(products)} |S|={n_st} C={cap} T={tcap} "
              f"|U|={sidx.n} (weights sum {int(sidx.weights.sum())}, "
              f"+{n_single} singleton orders)")

    # ---- initial feasible columns -----------------------------------------
    overload_penalty = float(sidx.weights.sum())
    ws_bins = warm_start_partition(products, prod_lines, n_st, cap, tcap, speed)
    ws_bins = swap_descent(ws_bins, sidx, prod_lines, tcap, speed,
                           time.time() + min(15.0, 0.08 * time_limit),
                           rng, overload_penalty)
    master = Master(products, n_st, threads)
    for b in ws_bins:
        master.add_column(b, sidx.column_cost(b))
    for b in mutate_partition(ws_bins, prod_lines, cap, tcap, speed, rng, n_mutations):
        master.add_column(b, sidx.column_cost(b))
    ws_assign = {p: i for i, b in enumerate(ws_bins) for p in b}
    ws_visits = evaluate_assignment(ws_assign, order_prods)
    if verbose:
        print(f"  CG-SP: polished warm start visits={ws_visits}, initial pool="
              f"{len(master.patterns)} cols")

    pricer = ExactPricer(sidx, products, prod_lines, cap, tcap, speed,
                         threads, pool_cap)
    if verbose:
        print(f"  CG-SP: pricing MILP built once ({round(time.time()-t0,1)}s)")

    # ---- CG loop -----------------------------------------------------------
    cg_deadline = t0 + time_limit * (1.0 - imp_frac)
    best_lb: Optional[float] = None
    root_lp: Optional[float] = None
    converged = False
    it = n_exact = n_heur_cols = 0
    inc_assign: Dict[str, int] = dict(ws_assign)  # best feasible partition so far
    inc_visits: int = ws_visits

    while time.time() < cg_deadline:
        it += 1
        rmp_obj, sigma, mu = master.solve_lp()
        root_lp = rmp_obj
        if verbose and (it <= 3 or it % 10 == 0):
            print(f"  it{it}: RMP={rmp_obj:.1f} cols={len(master.patterns)} "
                  f"LB={'-' if best_lb is None else f'{best_lb:.1f}'}", flush=True)

        # Bonus heuristic column at the true duals (cheap, never a proof).
        added = False
        pat, rc = heuristic_pricing(sidx, products, sigma, mu,
                                    prod_lines, cap, tcap, speed)
        if pat is not None and rc < EPS_RC:
            if master.add_column(pat, sidx.column_cost(pat)):
                added = True
                n_heur_cols += 1

        # Exact pricing every iteration (persistent model; sole proof + LB).
        n_exact += 1
        budget = min(max(10.0, time_limit / 10.0),
                     max(5.0, cg_deadline - time.time()))
        cols, rc_lb, optimal = pricer.price(sigma, mu, budget)
        for cpat, _crc in cols:
            if master.add_column(cpat, sidx.column_cost(cpat)):
                added = True
        # Farley bound: valid for ANY rc lower bound (also on pricing timeout).
        if rc_lb > -float("inf"):
            lb = rmp_obj + n_st * min(0.0, rc_lb)
            if best_lb is None or lb > best_lb:
                best_lb = lb
        if optimal and not cols:
            converged = True
            best_lb = rmp_obj  # LP optimum proven (rc* >= -eps)
            if verbose:
                print(f"  CG-SP: converged at LP opt {rmp_obj:.1f} (it {it})")
            break

        # Coordinated columns: complete the priced bundles into a full feasible
        # partition (cardinality-tight master needs compatible column SETS) and
        # keep it as a primal incumbent.
        seed_pats = [c[0] for c in sorted(cols, key=lambda c: c[1])]
        if pat is not None and rc < EPS_RC:
            seed_pats.append(pat)
        seeds: List[List[str]] = []
        used: set = set()
        for sp in seed_pats:
            if len(seeds) >= n_st:
                break
            if not used.intersection(sp):
                seeds.append(list(sp))
                used.update(sp)
        if seeds:
            part = complete_partition(seeds, products, sidx, prod_lines,
                                      n_st, cap, tcap, speed)
            part = swap_descent(part, sidx, prod_lines, tcap, speed,
                                time.time() + min(2.0, 0.02 * time_limit),
                                rng, overload_penalty)
            all_feas = True
            for b in part:
                if bin_feasible(b, prod_lines, cap, tcap, speed):
                    if master.add_column(b, sidx.column_cost(b)):
                        added = True
                else:
                    all_feas = False
            if all_feas:
                part_assign = {p: i for i, b in enumerate(part) for p in b}
                part_visits = evaluate_assignment(part_assign, order_prods)
                if part_visits < inc_visits:
                    inc_visits, inc_assign = part_visits, part_assign
                    if verbose:
                        print(f"  it{it}: new incumbent partition "
                              f"visits={part_visits}", flush=True)

        if not added:
            if verbose:
                print("  CG-SP: no new column (duplicates/timeout); stop loop")
            break

    # ---- final integer master + repair --------------------------------------
    polish_reserve = 0.15 * time_limit
    imp_budget = max(10.0, t0 + time_limit - polish_reserve - time.time())
    chosen, _ip_bound = master.solve_ip(imp_budget)  # pool-restricted bound: NOT globally valid
    chosen_pats = [master.patterns[j] for j in chosen]
    assignment_idx = build_assignment(chosen_pats, sidx)

    # Safety: any uncovered product (cannot happen with covering rows) -> spread.
    missing = [p for p in products if p not in assignment_idx]
    if missing:
        slots = defaultdict(int)
        for p, s in assignment_idx.items():
            slots[s] += 1
        for p in missing:
            tgt = min(range(len(chosen_pats) or n_st), key=lambda s: slots[s])
            assignment_idx[p] = tgt
            slots[tgt] += 1

    total_visits = evaluate_assignment(assignment_idx, order_prods)
    if total_visits >= inc_visits:  # never worse than the best incumbent partition
        assignment_idx, total_visits = inc_assign, inc_visits

    # Final polish: swap descent on the chosen partition with leftover budget.
    n_bins = max((s for s in assignment_idx.values()), default=0) + 1
    final_bins: List[List[str]] = [[] for _ in range(max(n_bins, n_st))]
    for p, s in assignment_idx.items():
        final_bins[s].append(p)
    final_deadline = t0 + time_limit - 1.0
    if time.time() < final_deadline:
        final_bins = swap_descent(final_bins, sidx, prod_lines, tcap, speed,
                                  final_deadline, rng, overload_penalty)
        polished_assign = {p: i for i, b in enumerate(final_bins) for p in b}
        polished_visits = evaluate_assignment(polished_assign, order_prods)
        if polished_visits < total_visits:
            assignment_idx, total_visits = polished_assign, polished_visits

    util_var, max_util, cap_broken, wl_broken = workload_stats(
        assignment_idx, prod_lines, max(len(final_bins), n_st), cap, tcap, speed
    )
    elapsed = time.time() - t0
    bound = best_lb  # valid Lagrangian / converged-LP bound only (or None)

    if verbose:
        gap = ("-" if not bound else f"{(total_visits - bound) / total_visits:.3%}")
        print(f"  CG-SP done: visits={total_visits} LB={bound} gap={gap} "
              f"it={it} cols={len(master.patterns)} exact={n_exact} "
              f"heurcols={n_heur_cols} conv={converged} {elapsed:.1f}s "
              f"cap_broken={cap_broken} wl_broken={wl_broken}")

    station_ids = [str(s["STATION_ID"]) for s in stations]
    assignment = {p: station_ids[s % n_st] for p, s in assignment_idx.items()}
    return (assignment, total_visits, elapsed, util_var, max_util,
            cap_broken, wl_broken, bound)


# ---------------------------------------------------------------------------
#  CLI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Aggregated set-partitioning CG for flat-warehouse CSLAP (CPLEX)"
    )
    parser.add_argument("--prefix", type=str, required=True)
    parser.add_argument("--dir", type=str, default="synthetic_datasets")
    parser.add_argument("--time", type=int, default=120)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--pool-cap", type=int, default=10)
    parser.add_argument("--mutations", type=int, default=20)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    print(f"Running CG-SetPart (CPLEX) on {args.prefix}...")
    op, st, pr, pl = read_data(args.prefix, args.dir)
    run_cg_setpart(op, st, pr, pl, time_limit=args.time, threads=args.threads,
                   pool_cap=args.pool_cap, n_mutations=args.mutations,
                   seed=args.seed)
