r"""
P-K Covering Construction operator :math:`C_k^{var}` for CSLAP robustness.

This module ports the verified P-K Set-Cover column-generation logic of the
reference notebooks ``new_alban_version_exact.ipynb`` (exact / partition variant)
and ``new_alban_version.ipynb`` (cover / :math:`\ge 1` variant) from CPLEX/docplex
to an **open, license-free linear-algebra backend**, preserving the
master/pricing formulation **exactly**. It is the Stage-3 implementation of
contract item F.1 and of the construction operator defined in Method Report
(``reports/2_method_report.md``) Section C.2, equations (6)-(9).

Solver backend (environment-driven, Stage-3 decision)
-----------------------------------------------------
The reference notebooks solve the master LP and the pricing MIP with CPLEX via
``docplex``. In the deployment environment (conda ``savoye2023``, Python 3.10):

* **Gurobi is unavailable** as a licensed solver (project directive: no Gurobi
  license is held) and is therefore not used.
* **CPLEX runtime is unavailable** (``docplex`` imports but raises
  ``no CPLEX runtime found`` on solve), so the notebook's native backend cannot
  run here.
* **Hexaly** is licensed and works, but it is a local-search engine that exposes
  **no LP dual values**; column generation requires the master's dual prices
  :math:`\alpha_p, \beta_o`, so Hexaly cannot drive the master LP.
* **HiGHS via SciPy** (:func:`scipy.optimize.linprog` with ``method="highs"`` and
  :func:`scipy.optimize.milp`) is open source, license-free, and returns exact
  LP duals through ``result.eqlin.marginals`` / ``result.ineqlin.marginals``.

Accordingly the committed backend is:

* ``"highs"`` (default, primary): the master LP **and** the pricing MIP are both
  solved with HiGHS. Duals come from HiGHS; this is the only fully self-contained
  CG path and is exact for the formulation (6)-(9).
* ``"hexaly"`` (optional): the master LP is **still** solved with HiGHS (duals are
  mandatory and Hexaly cannot provide them); only the pricing MIP is delegated to
  Hexaly. Offered as a cross-check arm, not the default.

The selector is ``--backend {auto,highs,hexaly}`` (``auto`` resolves to
``highs``). This replaces the dual Gurobi/CPLEX backend of the prior session,
which is not runnable under the present licensing.

Mathematical formulation (Method Report eqs. 6-9)
-------------------------------------------------
Master problem (integer phase, :math:`x_q \in \{0,1\}` selects pattern
:math:`q \subseteq P` with :math:`1 \le |q| \le k`):

.. math::
    \min\ \Pi                                                         \tag{6}
.. math::
    \text{s.t.}\quad \sum_{q \ni p} x_q = 1 \quad \forall p \in P
    \qquad (\text{exact variant; } \ge 1 \text{ in the cover variant})  \tag{7}
.. math::
    \sum_{q :\, q \cap P_o \neq \emptyset} x_q \le \Pi
    \quad \forall o \in O^{tr}_{\neq}                                  \tag{8}

where :math:`O^{tr}_{\neq}` denotes the **distinct** order supports (duplicate
supports yield identical constraints (8); deduplication is exact for (6)-(9) and
is the scaling lever for full-size training sets, Method Report C.2).

Pricing subproblem (duals :math:`\alpha_p` from (7), :math:`\beta_o \le 0` from
(8); column :math:`q` accepted iff its score :math:`> 10^{-6}`):

.. math::
    \max_{z,w}\ \sum_{p \in P} \alpha_p z_p + \sum_o \beta_o w_o
    \quad \text{s.t.}\quad \sum_p z_p \le k,\ \ \sum_p z_p \ge 1,\ \
    w_o \ge z_p\ \forall o,\,\forall p \in P_o,\ \ z, w \in \{0,1\}.       \tag{9}

The score of an accepted column equals
:math:`\sum_{p \in q}\alpha_p + \sum_{o:\,q \cap P_o \neq \emptyset}\beta_o`,
i.e. the negated reduced cost (objective coefficient of any pattern is 0; only
:math:`\Pi` is in the objective). The achieved bottleneck value
:math:`\Pi^* = \max_{o} |\{q \in Q^* : q \cap P_o \neq \emptyset\}|` is the
worst-case number of patterns any training order touches.

Pipeline role
-------------
Output :math:`(Q^*, \Pi^*)` is consumed by ``pk_instance_robust.py`` (transform
:math:`\mathcal{T}`, Method Report C.3) to build the enlarged CSLAP instance that
the unchanged baseline solvers then optimize.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import random
import time
from itertools import combinations
from typing import Dict, FrozenSet, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

# NOTE: SciPy (HiGHS backend) and docplex (CPLEX backend) are imported **lazily**
# inside the backend-specific functions, not at module load. This lets the module
# be imported in an environment that has only one of the two solver stacks -- e.g.
# the CPLEX virtual env (docplex, no scipy) used for the exact cover in plan.md
# Phase B, or the HiGHS/Hexaly env (scipy, no docplex).

# Column-acceptance threshold (negated reduced cost), identical to the notebook.
COLUMN_EPS: float = 1e-6


# ---------------------------------------------------------------------------
#  DATA LOADING
# ---------------------------------------------------------------------------
def read_supports_from_instance(
    prefix: str,
    data_dir: str,
    max_orders: Optional[int] = None,
    max_order_size: Optional[int] = None,
) -> Tuple[List[FrozenSet[str]], List[str], List[FrozenSet[str]]]:
    r"""Read the training order supports from a standard CSLAP instance.

    Builds the observed order family :math:`O^{tr}` (Method Report C.1) from
    ``{prefix}_orders.csv`` (semicolon schema ``ORDER;PRODUCT;QTY;STATION``) and
    the universe :math:`P` from ``{prefix}_products.csv``.

    Args:
        prefix: Dataset prefix (e.g. ``syn_50sku``).
        data_dir: Directory holding the semicolon-separated CSV files.
        max_orders: Optional cap on the number of orders retained (notebook
            artifact only; ``None`` = keep all).
        max_order_size: Optional cap on order size; orders with more than this
            many distinct products are skipped (notebook artifact only).

    Returns:
        A triple ``(supports, universe, distinct_supports)`` where ``supports``
        is one frozenset per retained training order (duplicates kept, for the
        pricing linking constraints), ``universe`` is the sorted list of product
        tokens (``PROD_*``), and ``distinct_supports`` is the deduplicated list
        used to build constraint (8).
    """
    orders_df = pd.read_csv(os.path.join(data_dir, f"{prefix}_orders.csv"), sep=";")
    products_df = pd.read_csv(
        os.path.join(data_dir, f"{prefix}_products.csv"), sep=";"
    )
    universe = products_df["PRODUCT_ID"].apply(lambda v: f"PROD_{v}").tolist()

    order_groups = orders_df.groupby("ORDER")["PRODUCT"].apply(
        lambda s: frozenset(s)
    )
    supports: List[FrozenSet[str]] = []
    for support in order_groups:
        if max_order_size is not None and len(support) > max_order_size:
            continue
        if not support:
            continue
        supports.append(support)
        if max_orders is not None and len(supports) >= max_orders:
            break

    distinct_supports = _distinct(supports)
    return supports, universe, distinct_supports


def read_supports_from_orders_csv(
    csv_path: str,
    max_orders: Optional[int] = None,
    max_order_size: Optional[int] = None,
) -> Tuple[List[FrozenSet[str]], List[str], List[FrozenSet[str]]]:
    r"""Read order supports from the notebook ``filtered_dataset.csv`` format.

    The file has columns ``ORDER`` and ``PRODUCT_LIST`` where ``PRODUCT_LIST`` is
    a Python-literal list string (e.g. ``"['1000270', '406645']"``). This mode
    exists so the acceptance test (Method Report F.1) can run on the exact
    notebook slice. The notebook keeps orders with ``1 <= |order| <= 12`` and
    retains the first 400 such orders.

    Args:
        csv_path: Path to the ``filtered_dataset.csv``-style file.
        max_orders: Optional cap on retained orders (notebook used 400).
        max_order_size: Optional max order size (notebook used 12).

    Returns:
        ``(supports, universe, distinct_supports)`` as in
        :func:`read_supports_from_instance`. The universe equals the union of
        all retained supports.
    """
    df = pd.read_csv(csv_path)
    supports: List[FrozenSet[str]] = []
    for product_str in df["PRODUCT_LIST"]:
        product_list = ast.literal_eval(product_str)
        if max_order_size is not None and not (1 <= len(product_list) <= max_order_size):
            continue
        if not product_list:
            continue
        supports.append(frozenset(str(p) for p in product_list))
        if max_orders is not None and len(supports) >= max_orders:
            break

    universe_set: set = set()
    for support in supports:
        universe_set |= support
    universe = sorted(universe_set)
    distinct_supports = _distinct(supports)
    return supports, universe, distinct_supports


def _distinct(supports: List[FrozenSet[str]]) -> List[FrozenSet[str]]:
    """Return the deduplicated list of order supports (order preserved)."""
    seen: set = set()
    out: List[FrozenSet[str]] = []
    for support in supports:
        if support not in seen:
            seen.add(support)
            out.append(support)
    return out


# ---------------------------------------------------------------------------
#  INITIAL COLUMN POOL (mirrors notebook seeding strategy)
# ---------------------------------------------------------------------------
def _greedy_cooccurrence_merges(
    distinct_supports: List[FrozenSet[str]],
    universe: List[str],
    k: int,
    top_pairs: int = 4000,
) -> List[FrozenSet[str]]:
    r"""Seed coarse patterns from frequent co-occurrence merges of sizes 2..k.

    Stage-5 reviewer item 2 (k=4 fix). The default chunk seeding (step (b) of
    :func:`_seed_initial_columns`) and a capped random :math:`k`-combination pool
    can leave the integer master with no *coarse* column that genuinely merges
    co-ordered SKUs, so the binary master falls back to a singleton-equivalent
    partition (the degenerate k=4 arm the reviewer caught). This routine builds
    an explicit pool of high-value coarse patterns by **agglomerative
    co-occurrence merging**: it ranks SKU pairs by training co-occurrence count,
    then greedily grows each frequent pair into groups of size 3, ..., k by
    repeatedly absorbing the SKU most co-ordered with the current group. Every
    intermediate group size (2, 3, ..., k) is emitted as a candidate pattern, so
    the master can select genuinely multi-item patterns and the closures grow.

    Args:
        distinct_supports: Distinct training order supports.
        universe: Product universe :math:`P`.
        k: Maximum pattern size.
        top_pairs: Number of highest-co-occurrence seed pairs to grow.

    Returns:
        Deduplicated list of coarse candidate patterns of sizes 2..k.
    """
    if k < 2:
        return []
    # Pairwise co-occurrence counts over distinct supports.
    pair_count: Dict[Tuple[str, str], int] = {}
    item_count: Dict[str, int] = {p: 0 for p in universe}
    for support in distinct_supports:
        members = sorted(support)
        for item in members:
            if item in item_count:
                item_count[item] += 1
        for a, b in combinations(members, 2):
            key = (a, b) if a < b else (b, a)
            pair_count[key] = pair_count.get(key, 0) + 1
    if not pair_count:
        return []

    # Neighbour co-occurrence map for the greedy growth step.
    neighbours: Dict[str, Dict[str, int]] = {p: {} for p in universe}
    for (a, b), c in pair_count.items():
        neighbours.setdefault(a, {})[b] = c
        neighbours.setdefault(b, {})[a] = c

    ranked_pairs = sorted(pair_count.items(), key=lambda kv: kv[1], reverse=True)
    ranked_pairs = ranked_pairs[:top_pairs]

    seeds: List[FrozenSet[str]] = []
    seen: set = set()

    def _emit(group: List[str]) -> None:
        fs = frozenset(group)
        if 2 <= len(fs) <= k and fs not in seen:
            seen.add(fs)
            seeds.append(fs)

    for (a, b), _c in ranked_pairs:
        group = [a, b]
        _emit(group)
        # Greedily absorb the SKU most co-ordered with the current group.
        while len(group) < k:
            agg: Dict[str, int] = {}
            for member in group:
                for nb, cnt in neighbours.get(member, {}).items():
                    if nb not in group:
                        agg[nb] = agg.get(nb, 0) + cnt
            if not agg:
                break
            best = max(agg.items(), key=lambda kv: kv[1])[0]
            group.append(best)
            _emit(group)
    return seeds


def _seed_initial_columns(
    distinct_supports: List[FrozenSet[str]],
    universe: List[str],
    k: int,
    max_combo_columns: int = 50_000,
    cooccurrence_pairs: int = 0,
    seed_chunks: bool = True,
) -> List[FrozenSet[str]]:
    r"""Seed the initial pattern pool exactly as the reference notebooks do.

    Seeds (a) all singletons (guarantees feasibility of the exact-cover
    constraint (7)), (b) size-:math:`k` chunks of every distinct support, and
    (c) all :math:`k`-combinations of small supports (sampled for large ones).
    This reproduces the ``add_pattern`` seeding of ``new_alban_version_exact``.

    **Scaling control (Deviation U7a).** At high :math:`k` the exhaustive
    :math:`k`-combination enumeration in step (c) explodes (e.g.
    :math:`\binom{15}{6}=5005` per support), producing hundreds of thousands of
    columns and rendering the binary integer master intractable under HiGHS. To
    keep the restricted master tractable we cap the **total** number of
    step-(c) combination columns at ``max_combo_columns`` via a deterministic
    (``seed=42``) reservoir sample. Singletons (a) and size-:math:`k` chunks (b)
    are always kept in full, so feasibility of (7)/(8) is preserved and the CG
    pricing can still discover any missing high-value column. The cap only bounds
    the *initial* pool, not the reachable column set.

    Args:
        distinct_supports: Distinct order supports.
        universe: Product universe :math:`P`.
        k: Maximum pattern size.
        max_combo_columns: Hard cap on step-(c) combination columns (U7a).

    Returns:
        Deduplicated list of seed patterns (frozensets).
    """
    seeds: List[FrozenSet[str]] = []
    seen: set = set()

    def _add(pattern: FrozenSet[str]) -> None:
        if pattern and pattern not in seen:
            seen.add(pattern)
            seeds.append(pattern)

    # (a) Singletons over the full universe.
    for item in universe:
        _add(frozenset({item}))

    # (b) Size-k chunks of each support. Skipped when seed_chunks is False: at
    #     high distinct-support counts (e.g. tens of thousands of ISCF orders)
    #     the chunk pool floods the master with ~10^5 columns, making each LP
    #     re-solve heavy. With chunks off, the master starts from singletons (+
    #     optional co-occurrence merges) and the exact CPLEX pricing generates the
    #     needed multi-item columns on demand -- proper column generation.
    if seed_chunks:
        for support in distinct_supports:
            ordered = sorted(support)
            for start in range(0, len(ordered), k):
                chunk = ordered[start:start + k]
                if 1 <= len(chunk) <= k:
                    _add(frozenset(chunk))

    # (c) k-combinations of supports (sampled when large), as in the notebook,
    #     with a deterministic global cap (U7a) to bound the initial pool.
    #     When co-occurrence seeding (step d, reviewer item 2) is active the
    #     coarse merges replace this flood with far fewer, higher-value columns,
    #     so step (c) is SUPPRESSED -- it was the dominant source of the 50k+
    #     column blow-up that timed out the k=4 integer master.
    if k >= 2 and cooccurrence_pairs == 0:
        rng = random.Random(42)
        combo_seeds: List[FrozenSet[str]] = []
        combo_seen: set = set()
        for support in distinct_supports:
            members = list(support)
            if len(members) <= 50:
                pool = combinations(members, min(k, len(members)))
            else:
                sampled = rng.sample(members, min(30, len(members)))
                pool = combinations(sampled, min(k, len(sampled)))
            for combo in pool:
                fc = frozenset(combo)
                if fc and fc not in combo_seen and fc not in seen:
                    combo_seen.add(fc)
                    combo_seeds.append(fc)
        if len(combo_seeds) > max_combo_columns:
            idx = rng.sample(range(len(combo_seeds)), max_combo_columns)
            combo_seeds = [combo_seeds[i] for i in idx]
        for fc in combo_seeds:
            _add(fc)

    # (d) Greedy co-occurrence merges of sizes 2..k (reviewer item 2). These
    #     coarse, data-driven patterns are what let the integer master escape the
    #     singleton-equivalent partition that produced the degenerate k=4 arm.
    if cooccurrence_pairs > 0 and k >= 2:
        for fc in _greedy_cooccurrence_merges(
            distinct_supports, universe, k, top_pairs=cooccurrence_pairs
        ):
            _add(fc)
    return seeds


# ---------------------------------------------------------------------------
#  PRICING SUBPROBLEM (Method Report eq. 9)
# ---------------------------------------------------------------------------
class _HighsPricing:
    r"""Pricing MIP (eq. 9) solved with HiGHS via :func:`scipy.optimize.milp`.

    Maximises :math:`\sum_p \alpha_p z_p + \sum_o \beta_o w_o` subject to
    :math:`1 \le \sum_p z_p \le k` and the linking constraints
    :math:`w_o \ge z_p\ \forall o,\,\forall p \in P_o`, all variables binary.

    The constraint matrix (size, min-one, and the linking inequalities) is fixed
    across CG iterations and is built once as a sparse matrix; only the objective
    vector changes each iteration, exactly mirroring the notebook's reusable
    ``build_pricing_model`` / ``solve_pricing_minmax`` pair.
    """

    def __init__(
        self,
        distinct_supports: List[FrozenSet[str]],
        universe: List[str],
        k: int,
        time_limit: float,
    ) -> None:
        from scipy.optimize import Bounds, LinearConstraint
        from scipy.sparse import csr_matrix

        self.universe = universe
        self.supports = distinct_supports
        self.k = k
        self.time_limit = time_limit
        self.n_items = len(universe)
        self.n_supp = len(distinct_supports)
        self.item_idx = {p: i for i, p in enumerate(universe)}
        n_var = self.n_items + self.n_supp  # [z_0..z_{m-1}, w_0..w_{S-1}]

        # Variable layout: z occupies [0, n_items), w occupies [n_items, n_var).
        self.integrality = np.ones(n_var, dtype=int)
        self.bounds = Bounds(np.zeros(n_var), np.ones(n_var))

        # Sparse COO assembly: row 0 is the size limit, the rest are linking rows.
        rows_i: List[int] = []
        cols_j: List[int] = []
        data: List[float] = []
        lb: List[float] = []
        ub: List[float] = []

        # Size limit:  1 <= sum_p z_p <= k  (min-one merged into the same row).
        for i in range(self.n_items):
            rows_i.append(0); cols_j.append(i); data.append(1.0)
        lb.append(1.0)
        ub.append(float(k))

        # Linking:  w_o - z_p >= 0  for each o and each p in support_o.
        r = 1
        for s_idx, support in enumerate(distinct_supports):
            w_col = self.n_items + s_idx
            for item in support:
                rows_i.append(r); cols_j.append(w_col); data.append(1.0)
                rows_i.append(r); cols_j.append(self.item_idx[item]); data.append(-1.0)
                lb.append(0.0)
                ub.append(np.inf)
                r += 1

        A = csr_matrix((data, (rows_i, cols_j)), shape=(r, n_var))
        self.constraint = LinearConstraint(A, np.array(lb), np.array(ub))

    def solve(
        self, alpha: Dict[str, float], beta: Dict[int, float]
    ) -> Optional[Tuple[float, FrozenSet[str]]]:
        r"""Solve eq. (9) for the given duals; return ``(score, pattern)`` if the
        column's score exceeds :data:`COLUMN_EPS`, else ``None``.

        ``scipy.optimize.milp`` minimises, so the objective vector is negated.
        """
        from scipy.optimize import milp

        c = np.zeros(self.n_items + self.n_supp)
        for p, i in self.item_idx.items():
            c[i] = -alpha.get(p, 0.0)
        for s_idx in range(self.n_supp):
            c[self.n_items + s_idx] = -beta.get(s_idx, 0.0)

        options = {"time_limit": self.time_limit, "mip_rel_gap": 0.01}
        res = milp(
            c=c,
            constraints=[self.constraint],
            integrality=self.integrality,
            bounds=self.bounds,
            options=options,
        )
        if not res.success or res.x is None:
            return None
        zvals = res.x[: self.n_items]
        pattern = frozenset(
            self.universe[i] for i in range(self.n_items) if zvals[i] > 0.5
        )
        if not pattern:
            return None
        return _score(pattern, alpha, beta, self.supports), pattern


class _HexalyPricing:
    r"""Pricing MIP (eq. 9) solved with the Hexaly local-search optimizer.

    Provided as an optional cross-check backend (``--backend hexaly``). The
    master LP is **never** solved by Hexaly because it cannot return the duals
    :math:`\alpha_p, \beta_o` required by column generation; only this pricing
    subproblem is delegated. Hexaly is rebuilt per call (its models are sealed by
    ``model.close()``), which is acceptable since pricing dominates neither the
    iteration count nor the wall-clock budget at the scales exercised here.
    """

    def __init__(
        self,
        distinct_supports: List[FrozenSet[str]],
        universe: List[str],
        k: int,
        time_limit: float,
    ) -> None:
        import hexaly.optimizer as hexaly  # noqa: F401  (license set in module)

        _ensure_hexaly_license()
        self.hexaly = hexaly
        self.universe = universe
        self.supports = distinct_supports
        self.k = k
        self.time_limit = max(1, int(round(time_limit)))
        self.item_idx = {p: i for i, p in enumerate(universe)}

    def solve(
        self, alpha: Dict[str, float], beta: Dict[int, float]
    ) -> Optional[Tuple[float, FrozenSet[str]]]:
        r"""Solve eq. (9) with Hexaly; same accept rule as the HiGHS backend."""
        hexaly = self.hexaly
        n = len(self.universe)
        with hexaly.HexalyOptimizer() as opt:
            model = opt.model
            z = [model.bool() for _ in range(n)]
            # 1 <= sum z <= k.
            size = model.sum(z)
            model.constraint(size <= self.k)
            model.constraint(size >= 1)
            # w_o = max over p in P_o of z_p  (linking, eq. 9).
            obj = model.sum(alpha.get(p, 0.0) * z[self.item_idx[p]] for p in self.universe)
            for s_idx, support in enumerate(self.supports):
                b = beta.get(s_idx, 0.0)
                if b == 0.0:
                    continue
                idxs = [self.item_idx[p] for p in support if p in self.item_idx]
                if not idxs:
                    continue
                w_o = model.or_(*[z[i] for i in idxs])
                obj = obj + b * w_o
            model.maximize(obj)
            model.close()
            opt.param.verbosity = 0
            opt.param.time_limit = self.time_limit
            opt.solve()
            pattern = frozenset(
                self.universe[i] for i in range(n) if z[i].value > 0.5
            )
        if not pattern:
            return None
        return _score(pattern, alpha, beta, self.supports), pattern


def _score(
    pattern: FrozenSet[str],
    alpha: Dict[str, float],
    beta: Dict[int, float],
    supports: Sequence[FrozenSet[str]],
) -> float:
    r"""Compute a column's score :math:`\sum_{p\in q}\alpha_p +
    \sum_{o:\,q\cap P_o\neq\emptyset}\beta_o` (the negated reduced cost).

    The caller applies the accept rule (score :math:`> 10^{-6}`).
    """
    score = sum(alpha.get(p, 0.0) for p in pattern)
    for s_idx, support in enumerate(supports):
        if pattern & support:
            score += beta.get(s_idx, 0.0)
    return score


_HEXALY_LICENSE_SET = False


def _ensure_hexaly_license() -> None:
    """Inject the project Hexaly license key once (matches the baselines)."""
    global _HEXALY_LICENSE_SET
    if _HEXALY_LICENSE_SET:
        return
    import hexaly.optimizer as hexaly

    hexaly.HxVersion.license_content = (
        "LICENSE_KEY = ED3A-2222-89F4B124-770D-"
        "60A55B936308D780-9506208B36204986-9B3E-E289-C66E"
    )
    _HEXALY_LICENSE_SET = True


# ---------------------------------------------------------------------------
#  CPLEX BACKEND  (docplex) -- the exact backend for plan.md Phase B
# ---------------------------------------------------------------------------
# This is the native backend of the reference P-K notebooks
# (``new_alban_version_exact.ipynb``), restored now that a working CPLEX runtime
# is available (``Virtual_Environment_CPLEX_1``). It solves the master LP (eqs.
# 6-8) for exact duals :math:`\alpha_p, \beta_o`, the pricing MIP (eq. 9), and the
# binary integer master -- all with CPLEX via ``docplex``. Unlike the HiGHS
# fallback it certifies the integer master to optimality at scale, so the achieved
# bottleneck :math:`\Pi^*` is the **true** min-max value (closes plan.md gaps
# G1/G2: no subsampling, reproduces the notebook's :math:`\Pi^* = 6` acceptance).
class _CplexPricing:
    r"""Pricing MIP (eq. 9) solved with CPLEX via :mod:`docplex`.

    Maximises :math:`\sum_p \alpha_p z_p + \sum_o \beta_o w_o` subject to
    :math:`1 \le \sum_p z_p \le k` and the linking :math:`w_o \ge z_p\
    \forall p \in P_o`, all variables binary. Since every :math:`\beta_o \le 0`
    (dual of a :math:`\le` row in a minimisation), only supports with a **nonzero**
    dual contribute, so the model is rebuilt per call over just those supports --
    far smaller than the full linking set and matching the Hexaly backend's
    ``beta == 0`` skip.
    """

    def __init__(
        self,
        distinct_supports: List[FrozenSet[str]],
        universe: List[str],
        k: int,
        time_limit: float,
    ) -> None:
        from docplex.mp.model import Model  # noqa: F401  (import probe)

        self.universe = universe
        self.supports = distinct_supports
        self.k = k
        self.time_limit = time_limit
        self.item_idx = {p: i for i, p in enumerate(universe)}
        # Per-support item indices (restricted to the universe), precomputed once.
        self.support_items: List[List[int]] = [
            [self.item_idx[p] for p in support if p in self.item_idx]
            for support in distinct_supports
        ]

    def solve(
        self, alpha: Dict[str, float], beta: Dict[int, float]
    ) -> Optional[Tuple[float, FrozenSet[str]]]:
        r"""Solve eq. (9) for the given duals; same accept rule as HiGHS."""
        from docplex.mp.model import Model

        n = len(self.universe)
        mdl = Model(name="pk_pricing")
        mdl.parameters.timelimit = float(self.time_limit)
        z = mdl.binary_var_list(n, name="z")

        size = mdl.sum(z)
        mdl.add_constraint(size <= self.k)
        mdl.add_constraint(size >= 1)

        obj = mdl.sum(
            alpha.get(self.universe[i], 0.0) * z[i]
            for i in range(n)
            if alpha.get(self.universe[i], 0.0) != 0.0
        )
        # w_o = OR_{p in support_o} z_p, only where beta_o < 0 (strictly binding).
        for s_idx, b in beta.items():
            if b >= 0.0:
                continue
            items = self.support_items[s_idx]
            if not items:
                continue
            w = mdl.binary_var(name=f"w_{s_idx}")
            for i in items:
                mdl.add_constraint(w >= z[i])
            obj = obj + b * w

        mdl.maximize(obj)
        sol = mdl.solve(log_output=False)
        if sol is None:
            mdl.end()
            return None
        pattern = frozenset(
            self.universe[i] for i in range(n) if z[i].solution_value > 0.5
        )
        mdl.end()
        if not pattern:
            return None
        return _score(pattern, alpha, beta, self.supports), pattern


class _CplexMasterLP:
    r"""Incremental CPLEX master (eqs. 6-8) via the low-level ``cplex`` API.

    Built **once**: variable 0 is :math:`\Pi`; the cover rows (7, one per item,
    sense ``E`` for the exact variant / ``G`` for the cover variant, rhs 1) and the
    sample rows (8, one per distinct support, ``sum x - \Pi \le 0``) are created up
    front, with :math:`\Pi` carrying coefficient :math:`-1` in every sample row.
    Pattern columns are then inserted **in place** with :func:`add_column` (the
    classic column-generation interface ``variables.add(columns=[SparsePair...])``),
    so each CG iteration only re-solves a warm-started LP instead of rebuilding the
    whole model. This is what makes the full-support ISCF cover tractable -- the
    ~109k sample rows are assembled once, not per iteration.

    Duals follow CPLEX's reduced-cost identity
    :math:`\bar c_q = c_q - \sum_i a_{iq} y_i`: with :math:`c_q = 0` and unit
    coefficients, :math:`\bar c_q = -(\sum_{p\in q}\alpha_p + \sum_{o}\beta_o)`,
    so the score :math:`\sum\alpha + \sum\beta` (>``COLUMN_EPS`` to accept) equals
    the negated reduced cost -- identical to the HiGHS path and the notebook.
    """

    def __init__(
        self,
        columns: List[FrozenSet[str]],
        universe: List[str],
        distinct_supports: List[FrozenSet[str]],
        variant: str,
        item_support_index: Dict[str, List[int]],
        objective: str = "minmax",
    ) -> None:
        import cplex

        self.cplex = cplex
        self.objective = objective
        self.universe = universe
        self.distinct_supports = distinct_supports
        self.item_support_index = item_support_index
        self.item_row = {p: i for i, p in enumerate(universe)}
        self.n_items = len(universe)
        self.n_supp = len(distinct_supports)
        self.sample_row0 = self.n_items  # sample rows live after the cover rows
        self.columns: List[FrozenSet[str]] = []

        cpx = cplex.Cplex()
        cpx.set_log_stream(None)
        cpx.set_error_stream(None)
        cpx.set_warning_stream(None)
        cpx.set_results_stream(None)
        cpx.objective.set_sense(cpx.objective.sense.minimize)

        # Variable 0 = Pi. In the min-max objective it carries the cost (obj 1) and
        # the bottleneck rows; in the min-sum objective it is an unused dummy
        # (obj 0) and the cost is carried by each pattern column's coefficient c_q
        # (the number of distinct supports it hits), with NO bottleneck rows.
        pi_obj = 1.0 if objective == "minmax" else 0.0
        cpx.variables.add(obj=[pi_obj], lb=[0.0], ub=[cplex.infinity], names=["Pi"])

        cover_sense = "E" if variant == "exact" else "G"
        cpx.linear_constraints.add(
            rhs=[1.0] * self.n_items,
            senses=[cover_sense] * self.n_items,
            names=[f"cov_{i}" for i in range(self.n_items)],
        )
        if objective == "minmax":
            cpx.linear_constraints.add(
                rhs=[0.0] * self.n_supp,
                senses=["L"] * self.n_supp,
                names=[f"smp_{j}" for j in range(self.n_supp)],
            )
            # Pi (col 0) carries coefficient -1 in every sample row.
            if self.n_supp:
                cpx.linear_constraints.set_coefficients(
                    [(self.sample_row0 + j, 0, -1.0) for j in range(self.n_supp)]
                )
        self.cpx = cpx
        for col in columns:
            self.add_column(col)

    def add_column(self, col: FrozenSet[str]) -> None:
        """Insert one pattern column into the cover/sample rows it participates in."""
        rows: List[int] = []
        vals: List[float] = []
        for item in col:
            ri = self.item_row.get(item)
            if ri is not None:
                rows.append(ri)
                vals.append(1.0)
        hit: set = set()
        for item in col:
            hit.update(self.item_support_index.get(item, ()))
        # min-max: the pattern participates (coef 1) in the bottleneck row of every
        # support it hits, and carries no objective cost. min-sum: no bottleneck
        # rows; the objective coefficient is c_q = #distinct supports the pattern
        # hits, so minimising sum_q c_q x_q minimises total pattern-order hits.
        obj_coef = 0.0
        if self.objective == "minmax":
            for sj in hit:
                rows.append(self.sample_row0 + sj)
                vals.append(1.0)
        else:  # minsum
            obj_coef = float(len(hit))
        self.cpx.variables.add(
            obj=[obj_coef], lb=[0.0], ub=[1.0],
            columns=[self.cplex.SparsePair(ind=rows, val=vals)],
        )
        self.columns.append(col)

    def solve_lp(self) -> Tuple[float, Dict[str, float], Dict[int, float], bool]:
        r"""Solve the relaxed master; return ``(obj, alpha, beta, ok)``.

        ``obj`` is the relaxed :math:`\Pi` (min-max) or the relaxed total hits
        (min-sum). ``alpha`` are the partition-row duals. ``beta`` are the
        bottleneck-row duals (min-max) or the implicit unit hit cost
        :math:`\beta_o \equiv -1` (min-sum), so the same pricing MIP serves both.
        """
        self.cpx.set_problem_type(self.cpx.problem_type.LP)
        self.cpx.solve()
        if self.cpx.solution.get_status() not in (
            self.cpx.solution.status.optimal,
            self.cpx.solution.status.optimal_infeasible,
        ):
            try:
                _ = float(self.cpx.solution.get_objective_value())
            except Exception:  # noqa: BLE001
                return float("nan"), {}, {}, False
        obj_val = float(self.cpx.solution.get_objective_value())
        duals = self.cpx.solution.get_dual_values()
        alpha = {self.universe[i]: float(duals[i]) for i in range(self.n_items)}
        if self.objective == "minmax":
            beta = {
                j: float(duals[self.sample_row0 + j]) for j in range(self.n_supp)
            }
        else:  # minsum: every hit costs 1
            beta = {j: -1.0 for j in range(self.n_supp)}
        return obj_val, alpha, beta, True

    def solve_integer(
        self, time_limit: float
    ) -> Tuple[List[FrozenSet[str]], float, bool]:
        r"""Flip pattern vars to binary and solve the integer master (eqs. 6-8).

        Returns ``(selected_patterns, objective, optimal_flag)``. The singleton
        partition is a guaranteed-feasible fallback if no incumbent is found.
        """
        n = len(self.columns)
        idxs = list(range(1, 1 + n))  # var 0 is Pi (stays continuous)
        self.cpx.variables.set_types(
            [(i, self.cpx.variables.type.binary) for i in idxs]
        )
        self.cpx.parameters.timelimit.set(float(time_limit))
        self.cpx.parameters.mip.tolerances.mipgap.set(0.0)
        self.cpx.solve()
        sol = self.cpx.solution
        # CPLEX raises (error 1217) on get_values when NO incumbent exists, so
        # probe feasibility first rather than relying on a None return.
        has_incumbent = False
        try:
            has_incumbent = bool(sol.is_primal_feasible())
        except Exception:  # noqa: BLE001
            has_incumbent = False
        if not has_incumbent:
            import sys as _sys
            print(
                "  [WARN] CPLEX integer master found no incumbent in "
                f"{time_limit:.0f}s over {n} columns; falling back to the "
                "SINGLETON partition (DEGENERATE).",
                file=_sys.stderr, flush=True,
            )
            singletons = [frozenset({item}) for item in self.universe]
            if self.objective == "minmax":
                obj_fallback = float(
                    max((len(s) for s in self.distinct_supports), default=0)
                )
            else:  # minsum: singleton partition's total hits = sum of support sizes
                obj_fallback = float(sum(len(s) for s in self.distinct_supports))
            return singletons, obj_fallback, False

        xvals = sol.get_values(idxs)
        selected = [self.columns[i] for i in range(n) if xvals[i] > 0.5]
        obj = float(sol.get_objective_value())
        try:
            gap = sol.MIP.get_mip_relative_gap()
        except Exception:  # noqa: BLE001
            gap = None
        optimal = bool(gap is not None and gap <= 1e-9)
        return selected, obj, optimal

    def end(self) -> None:
        """Release the CPLEX problem object."""
        try:
            self.cpx.end()
        except Exception:  # noqa: BLE001
            pass


# ---------------------------------------------------------------------------
#  MASTER LP / MIP  (HiGHS via SciPy)
# ---------------------------------------------------------------------------
def _build_item_support_index(
    universe: List[str],
    distinct_supports: List[FrozenSet[str]],
) -> Dict[str, List[int]]:
    r"""Inverted index ``item -> [support indices containing item]``.

    Built once per construction run so the master assembly can map a column to
    the supports it hits in :math:`O(|q|)` lookups instead of scanning every
    support, which removes the dominant :math:`O(|Q| \cdot |O^{tr}_{\neq}|)` cost.
    """
    index: Dict[str, List[int]] = {p: [] for p in universe}
    for s_idx, support in enumerate(distinct_supports):
        for item in support:
            if item in index:
                index[item].append(s_idx)
    return index


def _build_master_matrices(
    columns: List[FrozenSet[str]],
    universe: List[str],
    distinct_supports: List[FrozenSet[str]],
    variant: str,
    item_support_index: Dict[str, List[int]],
) -> Tuple[csr_matrix, csr_matrix, np.ndarray]:
    r"""Assemble the master constraint blocks for the current column pool.

    Variable layout is ``[Pi, x_0, ..., x_{C-1}]`` with ``Pi`` at index 0.

    Returns:
        ``(A_sample, A_cover, cover_rhs)`` where ``A_sample`` encodes eq. (8)
        rows :math:`\sum_{q\cap P_o\neq\emptyset} x_q - \Pi \le 0` and ``A_cover``
        encodes eq. (7) rows :math:`\sum_{q \ni p} x_q\ (=|\ge)\ 1`.
    """
    from scipy.sparse import csr_matrix

    n_col = len(columns)
    n_var = 1 + n_col
    item_to_cols: Dict[str, List[int]] = {p: [] for p in universe}
    supp_to_cols: List[List[int]] = [[] for _ in distinct_supports]

    for c_idx, col in enumerate(columns):
        hit_supports: set = set()
        for item in col:
            if item in item_to_cols:
                item_to_cols[item].append(c_idx)
            hit_supports.update(item_support_index.get(item, ()))
        for s_idx in hit_supports:
            supp_to_cols[s_idx].append(c_idx)

    # Sample rows (eq. 8):  sum x_q - Pi <= 0.
    s_rows, s_cols, s_data = [], [], []
    for r, cols in enumerate(supp_to_cols):
        s_rows.append(r); s_cols.append(0); s_data.append(-1.0)  # -Pi
        for c_idx in cols:
            s_rows.append(r); s_cols.append(1 + c_idx); s_data.append(1.0)
    A_sample = csr_matrix(
        (s_data, (s_rows, s_cols)), shape=(len(distinct_supports), n_var)
    )

    # Cover rows (eq. 7):  sum x_q (== | >=) 1.
    c_rows, c_cols, c_data = [], [], []
    for r, item in enumerate(universe):
        for c_idx in item_to_cols[item]:
            c_rows.append(r); c_cols.append(1 + c_idx); c_data.append(1.0)
    A_cover = csr_matrix(
        (c_data, (c_rows, c_cols)), shape=(len(universe), n_var)
    )
    cover_rhs = np.ones(len(universe))
    return A_sample, A_cover, cover_rhs


def _solve_master_lp(
    columns: List[FrozenSet[str]],
    universe: List[str],
    distinct_supports: List[FrozenSet[str]],
    variant: str,
    item_support_index: Dict[str, List[int]],
) -> Tuple[float, Dict[str, float], Dict[int, float], bool]:
    r"""Solve the continuous master (eqs. 6-8 relaxed) with HiGHS; return duals.

    Returns:
        ``(pi_value, alpha, beta, ok)`` where ``alpha[p]`` is the dual of the
        cover constraint (7) for item ``p`` and ``beta[s_idx]`` the dual of the
        sample constraint (8). HiGHS reports constraint marginals; the signs are
        normalised so that ``beta <= 0`` and the score reproduces the notebook's
        negated reduced cost.
    """
    from scipy.optimize import linprog

    n_col = len(columns)
    n_var = 1 + n_col
    A_sample, A_cover, cover_rhs = _build_master_matrices(
        columns, universe, distinct_supports, variant, item_support_index
    )

    # Objective: minimise Pi (index 0).
    c = np.zeros(n_var)
    c[0] = 1.0

    # Sample rows: A_sample x <= 0  -> ineqlin.
    b_ub = np.zeros(A_sample.shape[0])

    # Cover rows: equality (exact) or >= 1 (cover).
    if variant == "exact":
        A_eq, b_eq = A_cover, cover_rhs
        A_ub = A_sample
        b_ub_full = b_ub
        eq_rows = A_cover.shape[0]
    else:
        # Cover variant: sum >= 1  ->  -sum <= -1, stack under ineqlin.
        from scipy.sparse import vstack

        A_ub = vstack([A_sample, -A_cover]).tocsr()
        b_ub_full = np.concatenate([b_ub, -cover_rhs])
        A_eq, b_eq = None, None
        eq_rows = 0

    bounds = [(0.0, None)] + [(0.0, 1.0)] * n_col  # Pi >= 0, 0 <= x <= 1
    res = linprog(
        c=c,
        A_ub=A_ub,
        b_ub=b_ub_full,
        A_eq=A_eq,
        b_eq=b_eq,
        bounds=bounds,
        method="highs",
    )
    if not res.success:
        return float("nan"), {}, {}, False

    pi_value = float(res.x[0])

    # Dual extraction. SciPy/HiGHS: marginals are d(obj)/d(rhs).
    n_sample = A_sample.shape[0]
    ineq_marg = np.atleast_1d(res.ineqlin.marginals)
    beta = {s_idx: float(ineq_marg[s_idx]) for s_idx in range(n_sample)}

    if variant == "exact":
        eq_marg = np.atleast_1d(res.eqlin.marginals)
        alpha = {universe[r]: float(eq_marg[r]) for r in range(eq_rows)}
    else:
        # Cover-rows live in the tail of ineqlin with sign flipped (>= written
        # as <=); recover the >= dual as the negated marginal.
        alpha = {
            universe[r]: -float(ineq_marg[n_sample + r])
            for r in range(A_cover.shape[0])
        }
    return pi_value, alpha, beta, True


def _solve_master_integer(
    columns: List[FrozenSet[str]],
    universe: List[str],
    distinct_supports: List[FrozenSet[str]],
    variant: str,
    time_limit: float,
    item_support_index: Dict[str, List[int]],
) -> Tuple[List[FrozenSet[str]], float, bool]:
    r"""Integer master re-solve (eqs. 6-8, :math:`x_q \in \{0,1\}`) via HiGHS milp.

    Returns ``(selected_patterns, objective, optimal_flag)``.
    """
    from scipy.optimize import Bounds, LinearConstraint, milp

    n_col = len(columns)
    n_var = 1 + n_col
    A_sample, A_cover, cover_rhs = _build_master_matrices(
        columns, universe, distinct_supports, variant, item_support_index
    )

    c = np.zeros(n_var)
    c[0] = 1.0
    integrality = np.zeros(n_var, dtype=int)
    integrality[1:] = 1  # x binary; Pi continuous

    constraints = [LinearConstraint(A_sample, -np.inf, 0.0)]  # eq. (8)
    if variant == "exact":
        constraints.append(LinearConstraint(A_cover, cover_rhs, cover_rhs))
    else:
        constraints.append(LinearConstraint(A_cover, cover_rhs, np.inf))

    ub = np.concatenate([[np.inf], np.ones(n_col)])
    bounds = Bounds(np.zeros(n_var), ub)
    options = {"time_limit": time_limit, "mip_rel_gap": 0.0}
    res = milp(
        c=c,
        constraints=constraints,
        integrality=integrality,
        bounds=bounds,
        options=options,
    )
    if res.x is None:
        # Deviation U7b (documented fallback): HiGHS found no incumbent for the
        # binary set-partition within the budget (column-explosion at scale). The
        # singleton partition {p}, p in P, is *always* feasible for the exact
        # variant -- each item covered exactly once and (8) reduces to
        # |support| <= Pi, satisfied by Pi = max_o |support_o|. For the cover
        # variant the same singleton family is a valid (>=1) cover. We return this
        # guaranteed-feasible incumbent rather than crashing the pipeline.
        import sys as _sys
        print(
            "  [WARN U7b] integer master found no incumbent in "
            f"{time_limit:.0f}s over {n_col} columns; falling back to the "
            "SINGLETON partition (DEGENERATE: closures collapse to identity, "
            "k>1 behaves like k=1). Reduce --cover-max-supports to recover "
            "non-trivial patterns.",
            file=_sys.stderr, flush=True,
        )
        singletons = [frozenset({item}) for item in universe]
        pi_fallback = max((len(s) for s in distinct_supports), default=0)
        return singletons, float(pi_fallback), False

    xvals = res.x[1:]
    selected = [columns[i] for i in range(n_col) if xvals[i] > 0.5]
    optimal = bool(res.status == 0)
    return selected, float(res.fun), optimal


# ---------------------------------------------------------------------------
#  CONSTRUCTION OPERATOR  C_k^{var}  (Method Report eqs. 6-9)
# ---------------------------------------------------------------------------
def run_pk_cover(
    supports: List[FrozenSet[str]],
    universe: List[str],
    distinct_supports: List[FrozenSet[str]],
    k: int = 6,
    variant: str = "exact",
    master_time_limit: float = 600.0,
    pricing_time_limit: float = 30.0,
    backend: str = "highs",
    max_iter: int = 10_000_000,
    cooccurrence_pairs: int = 0,
    seed_chunks: bool = True,
    objective: str = "minmax",
    verbose: bool = True,
) -> Tuple[List[FrozenSet[str]], int, Dict[str, float]]:
    r"""Run the P-K column generation :math:`C_k^{var}` (Method Report eqs. 6-9).

    Performs the LP phase (continuous master + pricing loop) then re-solves the
    deduplicated columns as a binary master (integer phase), exactly mirroring
    the notebook two-phase logic. The returned patterns are the support of the
    integer solution :math:`Q^*`; :math:`\Pi^*` is the achieved bottleneck.

    Args:
        supports: Training order supports (duplicates kept; only used to verify
            the achieved :math:`\Pi^*`).
        universe: Product universe :math:`P`.
        distinct_supports: Deduplicated supports :math:`O^{tr}_{\neq}` driving (8).
        k: Maximum pattern size (conservatism knob; Method Report A.3).
        variant: ``"exact"`` for the partition (:math:`=1`) cover of (7), or
            ``"cover"`` for the redundant (:math:`\ge 1`) cover (sensitivity arm).
        master_time_limit: Wall-clock budget (s) shared by the CG loop and the
            integer re-solve.
        pricing_time_limit: Wall-clock budget (s) for each pricing MIP solve.
        backend: ``"cplex"`` (master LP + pricing + integer master all via CPLEX/
            docplex, the exact backend of plan.md Phase B), ``"highs"`` (all via
            HiGHS/SciPy), or ``"hexaly"`` (master LP via HiGHS, pricing via
            Hexaly). ``"auto"`` -> ``"highs"``.
        max_iter: Hard cap on CG iterations.
        verbose: Whether to print progress to the console.

    Returns:
        ``(patterns, pi_star, timing)`` where ``patterns`` is :math:`Q^*` (list of
        frozensets), ``pi_star`` is :math:`\Pi^*` (int), and ``timing`` is a
        breakdown mirroring the notebook's timing dict.
    """
    if variant not in ("exact", "cover"):
        raise ValueError(f"variant must be 'exact' or 'cover', got {variant!r}")
    if objective not in ("minmax", "minsum"):
        raise ValueError(f"objective must be 'minmax' or 'minsum', got {objective!r}")
    if backend == "auto":
        backend = "highs"
    if backend not in ("highs", "hexaly", "cplex"):
        raise ValueError(
            f"backend must be highs|hexaly|cplex|auto, got {backend!r}"
        )
    if objective == "minsum" and backend != "cplex":
        raise ValueError("objective='minsum' is implemented for backend='cplex' only")

    timing = {
        "model_building": 0.0,
        "relaxed_solving": 0.0,
        "lp_solve_time": 0.0,
        "pricing_time": 0.0,
        "column_adding_time": 0.0,
        "deduplication_time": 0.0,
        "integer_solving": 0.0,
        "num_iterations": 0,
        "backend": backend,
        "total": 0.0,
    }
    phase_start = time.time()

    # ---- Seed columns and the item->supports inverted index. ---------------
    build_start = time.time()
    columns: List[FrozenSet[str]] = _seed_initial_columns(
        distinct_supports, universe, k, cooccurrence_pairs=cooccurrence_pairs,
        seed_chunks=seed_chunks,
    )
    column_set = set(columns)
    item_support_index = _build_item_support_index(universe, distinct_supports)
    timing["model_building"] = time.time() - build_start
    if verbose:
        print(f"Initial columns: {len(columns)} | backend={backend}")

    # ---- Pricing engine + (CPLEX) the persistent incremental master. -------
    cplex_master: Optional[_CplexMasterLP] = None
    if backend == "hexaly":
        pricing: object = _HexalyPricing(
            distinct_supports, universe, k, pricing_time_limit
        )
    elif backend == "cplex":
        pricing = _CplexPricing(
            distinct_supports, universe, k, pricing_time_limit
        )
        cplex_master = _CplexMasterLP(
            columns, universe, distinct_supports, variant, item_support_index,
            objective=objective,
        )
    else:
        pricing = _HighsPricing(
            distinct_supports, universe, k, pricing_time_limit
        )

    # ---- Column-generation loop (LP phase). --------------------------------
    relaxed_start = time.time()
    iteration = 0
    pi_value = float("nan")
    while iteration < max_iter:
        iteration += 1

        lp_start = time.time()
        if backend == "cplex":
            assert cplex_master is not None
            pi_value, alpha, beta, ok = cplex_master.solve_lp()
        else:
            pi_value, alpha, beta, ok = _solve_master_lp(
                columns, universe, distinct_supports, variant, item_support_index
            )
        timing["lp_solve_time"] += time.time() - lp_start
        if not ok:
            if verbose:
                print("Master LP not solvable. Aborting CG loop.")
            break

        pricing_start = time.time()
        result = pricing.solve(alpha, beta)
        timing["pricing_time"] += time.time() - pricing_start

        if result is None or result[0] is None or result[0] <= COLUMN_EPS:
            if verbose:
                print(f"No improving column found at iteration {iteration}.")
            break

        add_start = time.time()
        _, new_col = result
        if new_col not in column_set:
            columns.append(new_col)
            column_set.add(new_col)
            if cplex_master is not None:
                cplex_master.add_column(new_col)
        else:
            # Pricing returned an existing column: CG has stalled.
            timing["column_adding_time"] += time.time() - add_start
            if verbose:
                print(f"Pricing returned a known column at iter {iteration}; stop.")
            break
        timing["column_adding_time"] += time.time() - add_start

        if verbose and iteration % 50 == 0:
            print(f"Iteration {iteration}: Pi={pi_value:.3f}, columns={len(columns)}")

        if time.time() - relaxed_start > master_time_limit:
            if verbose:
                print("Master time budget exhausted during CG loop.")
            break

    timing["relaxed_solving"] = time.time() - relaxed_start
    timing["num_iterations"] = iteration
    if verbose:
        print(
            f"\n==== RELAXED SOLUTION ====\n"
            f"Iterations: {iteration}, Columns: {len(columns)}, "
            f"Relaxed Pi = {pi_value:.6f}\n"
            f"  LP {timing['lp_solve_time']:.1f}s, "
            f"Pricing {timing['pricing_time']:.1f}s, "
            f"AddCol {timing['column_adding_time']:.1f}s"
        )

    # ---- Deduplicate columns. ----------------------------------------------
    dedup_start = time.time()
    unique_patterns = _distinct(columns)
    timing["deduplication_time"] = time.time() - dedup_start

    # ---- Integer phase. ----------------------------------------------------
    int_start = time.time()
    remaining = max(10.0, master_time_limit - (time.time() - relaxed_start))
    if backend == "cplex":
        assert cplex_master is not None
        selected, int_obj, int_optimal = cplex_master.solve_integer(remaining)
        cplex_master.end()
    else:
        selected, int_obj, int_optimal = _solve_master_integer(
            unique_patterns, universe, distinct_supports, variant, remaining,
            item_support_index,
        )
    timing["integer_solving"] = time.time() - int_start

    # Achieved Pi* = max over training orders of #patterns hitting that order;
    # total_hits = sum over orders of that count (the min-sum objective value).
    pi_star = 0
    total_hits = 0
    for support in distinct_supports:
        hits = sum(1 for col in selected if col & support)
        total_hits += hits
        pi_star = max(pi_star, hits)

    # Pattern-size histogram + total set count (user-requested cover composition).
    from collections import Counter as _Counter
    size_hist = {int(s): int(c) for s, c in
                 sorted(_Counter(len(p) for p in selected).items())}

    timing["total"] = time.time() - phase_start
    timing["int_obj"] = round(int_obj)
    timing["int_optimal"] = int_optimal
    timing["lp_pi"] = float(pi_value)
    timing["objective"] = objective
    timing["num_patterns"] = len(selected)
    timing["total_hits"] = int(total_hits)
    timing["pattern_size_histogram"] = size_hist

    if verbose:
        headline = (f"total_hits = {total_hits}" if objective == "minsum"
                    else f"Objective (Pi) = {timing['int_obj']}")
        print(
            f"\n==== INTEGER SOLUTION ({objective}) ====\n"
            f"Patterns selected: {len(selected)}  size_hist={size_hist}\n"
            f"{headline}  (achieved Pi* = {pi_star}, total_hits = {total_hits}, "
            f"{'optimal' if int_optimal else 'incumbent only'})\n"
            f"Total time: {timing['total']:.1f}s "
            f"(int phase {timing['integer_solving']:.1f}s)"
        )
    return selected, pi_star, timing


# ---------------------------------------------------------------------------
#  BRUTE-FORCE PARTITION / Pi CHECKER  (independent verification)
# ---------------------------------------------------------------------------
def check_partition_and_pi(
    patterns: List[FrozenSet[str]],
    universe: List[str],
    distinct_supports: List[FrozenSet[str]],
    variant: str,
) -> Dict[str, object]:
    r"""Independently verify a CG solution against eqs. (6)-(8).

    Recomputes, from scratch (no solver), whether ``patterns`` cover the universe
    in the required sense and what bottleneck :math:`\Pi` they achieve. Used by
    the self-tests (Method Report F.1 substitute validations) to confirm the CG
    output without trusting the optimizer.

    Args:
        patterns: Selected pattern family :math:`Q^*`.
        universe: Product universe :math:`P`.
        distinct_supports: Distinct order supports :math:`O^{tr}_{\neq}`.
        variant: ``"exact"`` (partition: each item covered exactly once) or
            ``"cover"`` (each item covered at least once).

    Returns:
        Dict with keys ``valid`` (bool), ``pi`` (int, the recomputed
        :math:`\Pi^*`), ``uncovered`` (items with zero cover), ``overcovered``
        (items covered more than once; only a violation for ``exact``), and
        ``max_pattern_size``.
    """
    cover_count: Dict[str, int] = {p: 0 for p in universe}
    for q in patterns:
        for item in q:
            if item in cover_count:
                cover_count[item] += 1

    uncovered = sorted(p for p, c in cover_count.items() if c == 0)
    overcovered = sorted(p for p, c in cover_count.items() if c > 1)

    if variant == "exact":
        valid = (not uncovered) and (not overcovered)
    else:
        valid = not uncovered

    pi = 0
    for support in distinct_supports:
        hits = sum(1 for q in patterns if q & support)
        pi = max(pi, hits)

    max_pattern_size = max((len(q) for q in patterns), default=0)
    return {
        "valid": valid,
        "pi": pi,
        "uncovered": uncovered,
        "overcovered": overcovered,
        "max_pattern_size": max_pattern_size,
    }


# ---------------------------------------------------------------------------
#  CLI
# ---------------------------------------------------------------------------
def main() -> None:
    """CLI entry point: run :math:`C_k^{var}` and dump patterns JSON + log."""
    parser = argparse.ArgumentParser(
        description="P-K covering construction C_k^var (Method Report eqs. 6-9)."
    )
    parser.add_argument("--prefix", type=str, default=None,
                        help="Dataset prefix for the standard CSLAP schema.")
    parser.add_argument("--dir", type=str, default="synthetic_datasets")
    parser.add_argument("--time", type=int, default=600,
                        help="Master CG + integer time budget in seconds.")
    parser.add_argument("--pricing-time", type=float, default=30.0)
    parser.add_argument("--k", type=int, default=6)
    parser.add_argument("--variant", type=str, default="exact",
                        choices=["exact", "cover"])
    parser.add_argument("--objective", type=str, default="minmax",
                        choices=["minmax", "minsum"],
                        help="Cover objective: 'minmax' minimises the worst-order "
                             "pattern bottleneck Pi; 'minsum' minimises the total "
                             "pattern-order hits (cplex backend only).")
    parser.add_argument("--backend", type=str, default="auto",
                        choices=["auto", "highs", "hexaly", "cplex"],
                        help="Master/pricing solver: 'cplex' (docplex, exact, "
                             "plan.md Phase B), 'highs' (SciPy fallback), "
                             "'hexaly' (pricing only). 'auto'->'highs'.")
    parser.add_argument("--max-orders", type=int, default=None)
    parser.add_argument("--max-order-size", type=int, default=None)
    parser.add_argument("--cooccurrence-pairs", type=int, default=0,
                        help="Reviewer item 2: seed N greedy co-occurrence "
                             "merges of sizes 2..k (0=off).")
    parser.add_argument("--no-chunk-seed", action="store_true",
                        help="Skip the size-k chunk seeding (step b). Use for "
                             "large distinct-support instances (ISCF): start the "
                             "master from singletons + co-occurrence merges and "
                             "let CPLEX pricing generate columns (lean CG).")
    parser.add_argument("--orders-csv", type=str, default=None,
                        help="Path to a notebook-style filtered_dataset.csv "
                             "(ORDER, PRODUCT_LIST). Overrides --prefix.")
    parser.add_argument("--out", type=str, default=None,
                        help="Output JSON path for patterns + Pi (defaults to "
                             "logs/pk_cover_{tag}_k{k}_{variant}.json).")
    parser.add_argument("--check", action="store_true",
                        help="Run the brute-force partition/Pi checker on output.")
    args = parser.parse_args()

    if args.orders_csv:
        supports, universe, distinct = read_supports_from_orders_csv(
            args.orders_csv, args.max_orders, args.max_order_size
        )
        tag = os.path.splitext(os.path.basename(args.orders_csv))[0]
    elif args.prefix:
        supports, universe, distinct = read_supports_from_instance(
            args.prefix, args.dir, args.max_orders, args.max_order_size
        )
        tag = args.prefix
    else:
        parser.error("one of --prefix or --orders-csv is required")

    print(
        f"P-K construction | tag={tag} k={args.k} variant={args.variant} "
        f"backend={args.backend} | |P|={len(universe)} "
        f"orders={len(supports)} distinct={len(distinct)}"
    )
    patterns, pi_star, timing = run_pk_cover(
        supports, universe, distinct,
        k=args.k, variant=args.variant,
        master_time_limit=float(args.time),
        pricing_time_limit=args.pricing_time,
        backend=args.backend,
        cooccurrence_pairs=args.cooccurrence_pairs,
        seed_chunks=not args.no_chunk_seed,
        objective=args.objective,
    )

    check_result = None
    if args.check:
        check_result = check_partition_and_pi(
            patterns, universe, distinct, args.variant
        )
        print(
            f"[checker] valid={check_result['valid']} pi={check_result['pi']} "
            f"uncovered={len(check_result['uncovered'])} "
            f"overcovered={len(check_result['overcovered'])}"
        )

    out_path = args.out or os.path.join(
        "logs", f"pk_cover_{tag}_k{args.k}_{args.variant}.json"
    )
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    payload = {
        "tag": tag,
        "k": args.k,
        "variant": args.variant,
        "objective": args.objective,
        "backend": timing.get("backend"),
        "pi_star": pi_star,
        "int_obj": timing.get("int_obj"),
        "int_optimal": timing.get("int_optimal"),
        "lp_pi": timing.get("lp_pi"),
        "num_patterns": len(patterns),
        "pattern_size_histogram": timing.get("pattern_size_histogram"),
        "total_hits": timing.get("total_hits"),
        "universe_size": len(universe),
        "num_orders": len(supports),
        "num_distinct": len(distinct),
        "patterns": [sorted(p) for p in patterns],
        "timing": {key: val for key, val in timing.items()},
        "check": check_result,
    }
    with open(out_path, "w") as fh:
        json.dump(payload, fh, indent=2)
    print(f"Pi* = {pi_star} | patterns written to {out_path}")


if __name__ == "__main__":
    main()
