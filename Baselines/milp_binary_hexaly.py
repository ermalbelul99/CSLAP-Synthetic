r"""
Binary formulation of CSLAP solved by Hexaly (the set-variable model's twin).

This exists to justify the reformulation claim of Section 3.4 with a controlled
comparison rather than an assertion. It is ``milp_synthetic.py`` with exactly one
thing changed, the decision representation:

    set-variable   station_products[s] = model.set(N), tied by model.partition
    binary (here)  x[p][s] = model.bool(), tied by sum_s x[p][s] == 1

Everything else is identical and deliberately so: the same engine, the same
capacity and workload rows, the same visit objective written with the same
``model.or_`` encoding, the same LPT warm start, and the same wall-clock budget.
Any difference in the result is therefore attributable to how the decision is
represented, not to the solver, the objective, or the starting point.

Note on faithfulness: the manuscript writes the visit count with auxiliary
variables z_os in [0,1] and the linking rows x_ps <= z_os. Those variables are
fully determined by x and are dropped here in favour of the same ``or_``
expression the set-variable model uses. That gives the binary formulation the
more compact of the two encodings, so the comparison does not handicap it.

Usage:
    from milp_binary_hexaly import run_milp_binary_hexaly
"""

from __future__ import annotations

import time
from collections import defaultdict

import hexaly.optimizer as hexaly

hexaly.HxVersion.license_content = (
    "LICENSE_KEY = ED3A-2222-89F4B124-770D-60A55B936308D780-"
    "9506208B36204986-9B3E-E289-C66E"
)


def run_milp_binary_hexaly(
    order_prods, stations, products, prod_lines,
    time_limit=120, verbosity=0, warm_start_assignment=None,
):
    """Solve the binary formulation with Hexaly.

    Returns ``(assignment, visits, elapsed, max_workload, workload_std_dev,
    cap_broken, wl_broken, moved_off_warm_start)``. Visits are recounted on the
    raw orders by the caller; the value returned here is the model objective.
    """
    start_time = time.time()

    station_ids = [s["STATION_ID"] for s in stations]
    capacities = {s["STATION_ID"]: s["CAPACITY"] for s in stations}
    time_caps = {s["STATION_ID"]: s["TIME_CAPACITY"] for s in stations}
    speeds = {s["STATION_ID"]: s["SPEED"] for s in stations}
    orders = list(order_prods.keys())
    prod_set = set(products)

    with hexaly.HexalyOptimizer() as optimizer:
        model = optimizer.model
        optimizer.param.verbosity = verbosity
        optimizer.param.time_limit = time_limit

        # THE difference: one boolean per (product, station) instead of one set
        # per station. Feasibility of the assignment must now be imposed.
        x = {p: {s: model.bool() for s in station_ids} for p in products}

        for p in products:
            model.constraint(model.sum(x[p][s] for s in station_ids) == 1)

        for s in station_ids:
            model.constraint(
                model.sum(x[p][s] for p in products) <= capacities[s])

        for s in station_ids:
            workload = model.sum(
                (prod_lines.get(p, 0) / speeds[s]) * x[p][s] for p in products)
            model.constraint(workload <= time_caps[s])

        # Same objective encoding as the set-variable model.
        terms = []
        for o in orders:
            members = [p for p in order_prods[o] if p in prod_set]
            if not members:
                continue
            for s in station_ids:
                terms.append(model.or_(*(x[p][s] for p in members)))
        model.minimize(model.sum(terms))
        model.close()

        # Same LPT warm start, injected after close as Hexaly requires.
        if warm_start_assignment:
            for p, s0 in warm_start_assignment.items():
                if p in x and s0 in station_ids:
                    for s in station_ids:
                        x[p][s].value = 1 if s == s0 else 0

        optimizer.solve()
        elapsed = time.time() - start_time

        assignment = {}
        station_counts = defaultdict(int)
        station_actions = defaultdict(float)
        for p in products:
            for s in station_ids:
                if x[p][s].value > 0.5:
                    assignment[p] = s
                    station_counts[s] += 1
                    station_actions[s] += prod_lines.get(p, 0) / (speeds[s] or 1.0)
                    break

        cap_broken = sum(1 for s in station_ids
                         if station_counts[s] > capacities[s])
        wl_broken = sum(1 for s in station_ids
                        if station_actions[s] > time_caps[s] + 1e-6)
        loads = [station_actions[s] for s in station_ids]
        max_wl = max(loads) if loads else 0.0
        mean = sum(loads) / len(loads) if loads else 0.0
        wl_std = (sum((l - mean) ** 2 for l in loads) / len(loads)) ** 0.5 if loads else 0.0

        visits = int(optimizer.solution.get_value(model.objectives[0]))
        moved = None
        if warm_start_assignment:
            moved = sum(1 for p, s in assignment.items()
                        if warm_start_assignment.get(p) != s)

        return (assignment, visits, elapsed, max_wl, wl_std,
                cap_broken, wl_broken, moved)
