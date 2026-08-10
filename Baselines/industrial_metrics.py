"""Full-instance evaluation of an industrial layout.

Extracted verbatim from ``run_benchmarks_industrial.py`` so that it can be reused
without importing that module, whose top-level ``import gurobipy`` / Hexaly
bindings are absent on some machines and would otherwise make a solver-free
re-run impossible. ``run_benchmarks_industrial`` imports the function back from
here, so there is exactly one implementation and the reported metrics keep their
single definition.
"""

from __future__ import annotations

from collections import defaultdict

import numpy as np


def evaluate_full_metrics(partial_assignment, static_assignment, op_full, st_full, pl_full):
    """
    Evaluates final constraints and objective across the FULL product base
    (both filtered products fixed to original locations and solver-assigned products).
    """
    if partial_assignment is None:
        return "-", "-", "-", "-", "-"

    final_assignment = partial_assignment.copy()
    final_assignment.update(static_assignment)

    # 1. Total Visits
    total_visits = 0
    for o, prods in op_full.items():
        visited = set()
        for p in prods:
            if p in final_assignment:
                visited.add(final_assignment[p])
        total_visits += len(visited)

    # 2. Workloads & Capacities
    station_counts = defaultdict(int)
    station_actions = defaultdict(float)
    speeds = {s["STATION_ID"]: s["SPEED"] for s in st_full}
    caps = {s["STATION_ID"]: s["CAPACITY"] for s in st_full}
    time_caps = {s["STATION_ID"]: s["TIME_CAPACITY"] for s in st_full}

    for p, sid in final_assignment.items():
        station_counts[sid] += 1
        qty = pl_full.get(p, 0)
        station_actions[sid] += qty / speeds.get(sid, 1.0) if speeds.get(sid, 1.0) > 0 else 0

    station_ids = [s["STATION_ID"] for s in st_full]
    cap_broken = sum(1 for sid in station_ids if station_counts[sid] > caps.get(sid, 0))
    wl_broken = sum(1 for sid in station_ids if station_actions[sid] > time_caps.get(sid, 0.0) + 1e-5)

    actual_workloads = [station_actions[sid] for sid in station_ids]
    max_workload = float(np.max(actual_workloads)) if actual_workloads else 0.0

    # Calculate utilization % for heterogeneous stations
    utilization_pcts = []
    for sid in station_ids:
        max_cap = time_caps.get(sid, 0.0)
        if max_cap > 0:
            utilization_pcts.append((station_actions[sid] / max_cap) * 100.0)
        else:
            utilization_pcts.append(0.0)

    utilization_std_dev = float(np.std(utilization_pcts)) if utilization_pcts else 0.0

    return total_visits, max_workload, utilization_std_dev, cap_broken, wl_broken
