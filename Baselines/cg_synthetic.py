"""
Column Generation for CSLAP using Hexaly Optimizer (Synthetic Data Adapter)

Implements the CG framework from the paper:
- Master problem: pattern selection (solved as MILP via Hexaly)
- Pricing subproblems: one per station, generating new patterns
- Final binary resolution step

Enhancements (Price-and-Branch matheuristic, adapted for Hexaly):
  1. Basis Enrichment   : enrich_warm_start() mutates the warm-start assignment
                          to create diverse initial patterns before the CG loop.
  2. Two-Phase Pricing  : heuristic_pricing() uses the spec-aligned dual-aware
                          score (sigma / time_cost) with greedy pattern building.
  3. Perturbation Pool  : After each Hexaly master solve, generate up to 5
                          perturbations of selected patterns and inject them as
                          new columns (analogue of Gurobi PoolSearchMode=2).
"""

import numpy as np
import pandas as pd
import hexaly.optimizer as hexaly
import os
import time
import random
import argparse
from collections import defaultdict

hexaly.HxVersion.license_content = "LICENSE_KEY = ED3A-2222-89F4B124-770D-60A55B936308D780-9506208B36204986-9B3E-E289-C66E"


def read_data(prefix, data_dir):
    orders_df = pd.read_csv(
        os.path.join(data_dir, f"{prefix}_orders.csv"), sep=";"
    )
    stations_df = pd.read_csv(
        os.path.join(data_dir, f"{prefix}_stations.csv"), sep=";"
    )
    products_df = pd.read_csv(
        os.path.join(data_dir, f"{prefix}_products.csv"), sep=";"
    )
    prod_lines = orders_df.groupby("PRODUCT").size().to_dict()
    order_prods = orders_df.groupby("ORDER")["PRODUCT"].apply(list).to_dict()
    stations = stations_df.to_dict(orient="records")
    products = products_df["PRODUCT_ID"].apply(lambda x: f"PROD_{x}").tolist()
    return order_prods, stations, products, prod_lines


# ---------------------------------------------------------------------------
#  INITIAL PATTERN: distribute products round-robin
# ---------------------------------------------------------------------------
def generate_initial_patterns(products, stations, prod_lines):
    station_ids = [s["STATION_ID"] for s in stations]
    capacities  = {s["STATION_ID"]: s["CAPACITY"]     for s in stations}
    time_caps   = {s["STATION_ID"]: s["TIME_CAPACITY"] for s in stations}
    speeds      = {s["STATION_ID"]: s["SPEED"]         for s in stations}

    sorted_prods = sorted(products, key=lambda p: prod_lines.get(p, 0), reverse=True)
    patterns = {s: [] for s in station_ids}

    rem_cap  = dict(capacities)
    rem_time = dict(time_caps)
    idx = 0

    for p in sorted_prods:
        placed = False
        workload_cost = prod_lines.get(p, 0)

        for attempt in range(len(station_ids)):
            sid = station_ids[(idx + attempt) % len(station_ids)]
            time_cost = workload_cost / speeds[sid] if speeds[sid] > 0 else 0

            if rem_cap[sid] > 0 and rem_time[sid] >= time_cost:
                patterns[sid].append(p)
                rem_cap[sid]  -= 1
                rem_time[sid] -= time_cost
                idx = (idx + attempt + 1) % len(station_ids)
                placed = True
                break

        if not placed:
            best_sid = min(station_ids,
                           key=lambda s: (workload_cost / speeds[s]) - rem_time[s])
            patterns[best_sid].append(p)

    return patterns


# ---------------------------------------------------------------------------
#  EVALUATE TOTAL VISITS FOR AN ASSIGNMENT
# ---------------------------------------------------------------------------
def evaluate_assignment(assignment, order_prods):
    total_visits = 0
    for o, prods in order_prods.items():
        visited = set()
        for p in prods:
            if p in assignment:
                visited.add(assignment[p])
        total_visits += len(visited)
    return total_visits


# ---------------------------------------------------------------------------
# TASK 1 — BASIS ENRICHMENT
# ---------------------------------------------------------------------------

def enrich_warm_start(warm_start_assignment, products, stations, prod_lines,
                      num_mutations=10):
    """
    Take the warm-start assignment and create `num_mutations` additional
    feasible patterns per station by randomly displacing 5‑10% of products
    and reassigning them greedily (same logic as Gurobi version).

    Returns
    -------
    extra_patterns : dict  {station_id: [list_of_pattern_lists]}
    """
    station_ids = [s["STATION_ID"] for s in stations]
    capacities  = {s["STATION_ID"]: s["CAPACITY"]     for s in stations}
    time_caps   = {s["STATION_ID"]: s["TIME_CAPACITY"] for s in stations}
    speeds      = {s["STATION_ID"]: s["SPEED"]         for s in stations}

    # Build base dict: station -> list of products
    base = defaultdict(list)
    for p, sid in warm_start_assignment.items():
        if sid in capacities:
            base[sid].append(p)

    extra_patterns = {s: [] for s in station_ids}

    for _ in range(num_mutations):
        current = {s: list(base[s]) for s in station_ids}

        all_assigned  = [(p, s) for s in station_ids for p in current[s]]
        n_displace    = max(1, int(len(all_assigned) * random.uniform(0.05, 0.10)))
        displaced_pairs = random.sample(all_assigned, min(n_displace, len(all_assigned)))

        displaced_prods = []
        for p, s in displaced_pairs:
            current[s].remove(p)
            displaced_prods.append(p)

        random.shuffle(displaced_prods)
        station_order = list(station_ids)

        for p in displaced_prods:
            pl = prod_lines.get(p, 0)
            placed = False
            random.shuffle(station_order)
            for sid in station_order:
                cur_time = sum(prod_lines.get(q, 0) / speeds[sid]
                               for q in current[sid]) if speeds[sid] > 0 else 0
                time_cost = pl / speeds[sid] if speeds[sid] > 0 else 0
                if (len(current[sid]) < capacities[sid] and
                        cur_time + time_cost <= time_caps[sid]):
                    current[sid].append(p)
                    placed = True
                    break
            if not placed:
                for sid in station_order:
                    if len(current[sid]) < capacities[sid]:
                        current[sid].append(p)
                        placed = True
                        break

        for s in station_ids:
            if current[s]:
                extra_patterns[s].append(list(current[s]))

    return extra_patterns


# ---------------------------------------------------------------------------
# TASK 2 — DUAL-AWARE HEURISTIC PRICING
# ---------------------------------------------------------------------------

def heuristic_pricing(station_id, products, order_prods, prod_lines,
                      station_cap, station_speed, station_time_cap,
                      sigma_p, pi_s):
    """
    Dual-aware greedy pricing heuristic.

    Score for product p:  score_p = sigma_p[p] / time_cost_p
        where  time_cost_p = prod_lines[p] / station_speed   (0 → very large score)

    Greedily builds a pattern respecting CAPACITY and TIME_CAPACITY, then
    computes the exact reduced cost:
        RC = Σ_{o : pattern covers o} z_o  −  Σ_{p in pattern} sigma_p[p]  −  pi_s

    Returns
    -------
    pattern : list[str]  if RC < -1e-4, else None
    """
    scored = []
    for p in products:
        pl = prod_lines.get(p, 0)
        time_cost = pl / station_speed if station_speed > 0 else 0
        if time_cost == 0:
            score = 1e9 * sigma_p.get(p, 0)
        else:
            score = sigma_p.get(p, 0) / time_cost
        scored.append((p, score, pl, time_cost))

    scored.sort(key=lambda x: -x[1])

    pattern    = []
    total_time = 0.0
    for p, score, pl, tc in scored:
        if len(pattern) >= station_cap:
            break
        if total_time + tc <= station_time_cap:
            pattern.append(p)
            total_time += tc

    if not pattern:
        return None

    pattern_set = set(pattern)
    z_count = sum(
        1 for o, prods in order_prods.items()
        if any(pp in pattern_set for pp in prods)
    )
    rc = z_count - sum(sigma_p.get(p, 0) for p in pattern) - pi_s

    if rc < -1e-4:
        return pattern
    return None


# ---------------------------------------------------------------------------
# TASK 3 (adapted) — PERTURBATION POOL
# ---------------------------------------------------------------------------

def perturbation_pool(s, selected_pattern, products, prod_lines,
                      capacities, time_caps, speeds,
                      num_perturb=5):
    """
    Generate up to `num_perturb` neighbourhood perturbations of `selected_pattern`
    for station `s` by randomly swapping one product in/out while respecting
    CAPACITY and TIME_CAPACITY.

    This is the Hexaly analogue of Gurobi's PoolSearchMode=2 / PoolSolutions.

    Returns
    -------
    perturbed : list[list[str]]
    """
    cap      = capacities[s]
    time_cap = time_caps[s]
    speed    = speeds[s]

    def pattern_time(pat):
        return sum(prod_lines.get(p, 0) / speed for p in pat) if speed > 0 else 0

    not_in = [p for p in products if p not in set(selected_pattern)]
    perturbed = []

    for _ in range(num_perturb * 4):          # try more times than needed
        if len(perturbed) >= num_perturb:
            break
        new_pat = list(selected_pattern)
        action  = random.choice(["swap", "remove", "add"])

        if action == "swap" and new_pat and not_in:
            out_p  = random.choice(new_pat)
            in_p   = random.choice(not_in)
            new_pat.remove(out_p)
            new_pat.append(in_p)

        elif action == "remove" and len(new_pat) > 1:
            new_pat.remove(random.choice(new_pat))

        elif action == "add" and not_in:
            cand = random.choice(not_in)
            new_pat.append(cand)

        # Validate
        if (len(new_pat) <= cap and
                pattern_time(new_pat) <= time_cap and
                new_pat):
            perturbed.append(new_pat)

    return perturbed


# ---------------------------------------------------------------------------
#  COLUMN GENERATION MAIN
# ---------------------------------------------------------------------------
def column_generation_hexaly(
    order_prods, stations, products, prod_lines,
    time_limit=300, max_cg_iterations=50, pricing_time_limit=30,
    warm_start_assignment=None, scenario_name="unknown"
):
    """
    CG framework (Hexaly, Price-and-Branch adapted):
    1. Basis Enrichment: enrich warm-start with mutated patterns
    2. Solve master (MILP via Hexaly) — extract selected patterns
    3. Two-Phase Pricing: dual-aware heuristic first
    4. Perturbation Pool: perturb selected patterns and inject new columns
    5. Repeat until convergence or time limit
    """
    start_time = time.time()

    station_ids = [s["STATION_ID"] for s in stations]
    capacities  = {s["STATION_ID"]: s["CAPACITY"]     for s in stations}
    time_caps   = {s["STATION_ID"]: s["TIME_CAPACITY"] for s in stations}
    speeds      = {s["STATION_ID"]: s["SPEED"]         for s in stations}
    orders      = list(order_prods.keys())

    # -----------------------------------------------------------------------
    # --- Initial patterns (with optional basis enrichment) ---
    # -----------------------------------------------------------------------
    if warm_start_assignment is not None:
        print("  CG (Hexaly): Using provided warm start assignment for initial patterns...")
        init_patterns = {s["STATION_ID"]: [] for s in stations}
        for p, s in warm_start_assignment.items():
            if s in init_patterns:
                init_patterns[s].append(p)

        # TASK 1: Enrich with mutated patterns
        print("  CG (Hexaly): Enriching warm start with basis mutations...")
        extra = enrich_warm_start(
            warm_start_assignment, products, stations, prod_lines,
            num_mutations=10
        )
    else:
        print("  CG (Hexaly): Generating initial patterns...")
        init_patterns = generate_initial_patterns(products, stations, prod_lines)
        extra = None

    # K_s: map station -> list of pattern IDs
    K_s = {s: [] for s in station_ids}
    all_patterns = {}

    def _register_pattern(s, pattern):
        """Add pattern to K_s / all_patterns; return pid or None if dup/empty."""
        new_set = set(pattern)
        if not new_set:
            return None
        for k in K_s[s]:
            if set(all_patterns[k]) == new_set:
                return None
        pid = f"k_{s}_{len(K_s[s]) + 1}"
        K_s[s].append(pid)
        all_patterns[pid] = list(pattern)
        return pid

    # Register base patterns
    for s in station_ids:
        pid = _register_pattern(s, init_patterns[s])
        if pid is None and init_patterns[s]:
            pid = f"k_{s}_1"
            K_s[s].append(pid)
            all_patterns[pid] = list(init_patterns[s])

    # Inject enriched patterns
    if extra is not None:
        n_enriched = 0
        for s in station_ids:
            for mut_pattern in extra[s]:
                pid = _register_pattern(s, mut_pattern)
                if pid is not None:
                    n_enriched += 1
        print(f"  CG (Hexaly): Injected {n_enriched} enriched patterns.")

    # Precompute delta and z_osk
    delta = {}
    z_osk = {}

    def update_pattern_data(s, k, pattern):
        pattern_set = set(pattern)
        for p in products:
            delta[(p, s, k)] = 1 if p in pattern_set else 0
        for o in orders:
            prods_set = set(order_prods[o])
            z_osk[(o, s, k)] = 1 if bool(prods_set & pattern_set) else 0

    for s in station_ids:
        for k in K_s[s]:
            update_pattern_data(s, k, all_patterns[k])

    best_assignment = None
    best_visits     = float("inf")

    log_data = {
        "scenario_name": scenario_name,
        "num_orders": len(orders),
        "num_products": len(products),
        "num_stations": len(stations),
        "station_capacity": capacities[station_ids[0]],
        "station_time_capacity": time_caps[station_ids[0]],
        "starting_master_obj": None,
        "total_iterations": 0,
        "heuristic_pricing_calls": 0,
        "exact_pricing_calls": 0,  # Corresponds to perturbation pool calls in Hexaly
        "lower_bound": "Not available (Hexaly gives UBs, no exact duals for LP bounds)"
    }

    for iteration in range(1, max_cg_iterations + 1):
        log_data["total_iterations"] = iteration
        elapsed = time.time() - start_time
        if elapsed > time_limit:
            print(f"  CG: Time limit reached at iteration {iteration}")
            break

        print(f"  CG Iteration {iteration}...")

        # -------------------------------------------------------------------
        # Solve master problem with Hexaly (binary selection of patterns)
        # -------------------------------------------------------------------
        remaining_time = max(10, int(time_limit - elapsed) // 3)

        selected = {}   # station -> pattern_id of selected pattern
        try:
            with hexaly.HexalyOptimizer() as optimizer:
                model = optimizer.model
                optimizer.param.verbosity  = 0
                optimizer.param.time_limit = min(remaining_time, 60)

                y = {}
                for s in station_ids:
                    for k in K_s[s]:
                        y[(s, k)] = model.bool()

                for s in station_ids:
                    model.constraint(
                        model.sum(y[(s, k)] for k in K_s[s]) <= 1
                    )

                for p in products:
                    model.constraint(
                        model.sum(
                            delta.get((p, s, k), 0) * y[(s, k)]
                            for s in station_ids for k in K_s[s]
                        ) >= 1
                    )

                obj = model.sum(
                    z_osk.get((o, s, k), 0) * y[(s, k)]
                    for o in orders for s in station_ids for k in K_s[s]
                )
                model.minimize(obj)
                model.close()
                optimizer.solve()

                master_val = optimizer.solution.get_value(model.objectives[0])
                print(f"    Master objective: {master_val}")

                if log_data["starting_master_obj"] is None:
                    log_data["starting_master_obj"] = master_val

                for s in station_ids:
                    for k in K_s[s]:
                        if optimizer.solution.get_value(y[(s, k)]) >= 0.5:
                            selected[s] = k

                assignment = {}
                for s, k in selected.items():
                    for p in all_patterns[k]:
                        assignment[p] = s

                visits = evaluate_assignment(assignment, order_prods)
                if visits < best_visits:
                    best_visits     = visits
                    best_assignment = assignment.copy()

        except Exception as e:
            print(f"    Master solve error: {e}")
            break

        # -------------------------------------------------------------------
        # TASK 2 — Dual-aware heuristic pricing
        # Approximate duals: sigma_p ≈ prod_lines[p] / |orders|
        #   (true LP duals unavailable from Hexaly MILP)
        # pi_s ≈ −1.0 (pattern selection dual approximation)
        # -------------------------------------------------------------------
        sigma_p = {p: prod_lines.get(p, 0) / max(len(orders), 1)
                   for p in products}

        new_patterns_found = False

        for s_info in stations:
            s    = s_info["STATION_ID"]
            pi_s = -1.0

            log_data["heuristic_pricing_calls"] += 1
            new_pattern = heuristic_pricing(
                s, products, order_prods, prod_lines,
                capacities[s], speeds[s], time_caps[s],
                sigma_p, pi_s,
            )

            if new_pattern is not None:
                pid = _register_pattern(s, new_pattern)
                if pid is not None:
                    update_pattern_data(s, pid, new_pattern)
                    new_patterns_found = True
                    print(f"    [Heuristic] Added {pid} for st. {s} "
                          f"({len(new_pattern)} products)")

        # -------------------------------------------------------------------
        # TASK 3 — Perturbation pool from selected patterns
        # -------------------------------------------------------------------
        for s, k in selected.items():
            log_data["exact_pricing_calls"] += 1
            sel_pattern = all_patterns[k]
            perturbed   = perturbation_pool(
                s, sel_pattern, products, prod_lines,
                capacities, time_caps, speeds, num_perturb=5
            )
            for pp in perturbed:
                pid = _register_pattern(s, pp)
                if pid is not None:
                    update_pattern_data(s, pid, pp)
                    new_patterns_found = True
                    print(f"    [Pool perturb] Added {pid} for st. {s}")

        if not new_patterns_found:
            print("  CG: No new patterns found. Converged.")
            break

    elapsed = time.time() - start_time

    # Fallback if no assignment was obtained
    if best_assignment is None:
        best_assignment = {}
        for s in station_ids:
            for p in init_patterns[s]:
                best_assignment[p] = s
        best_visits = evaluate_assignment(best_assignment, order_prods)

    # --- Workload distribution tracking ---
    station_counts  = defaultdict(int)
    station_actions = defaultdict(float)

    for p, sid in best_assignment.items():
        station_counts[sid]  += 1
        station_actions[sid] += prod_lines.get(p, 0)

    cap_broken = sum(1 for sid in station_ids
                     if station_counts[sid] > capacities[sid])

    actual_workloads = []
    for sid in station_ids:
        time_spent = (station_actions[sid] / speeds[sid]
                      if speeds[sid] > 0 else 0)
        actual_workloads.append(time_spent)

    wl_broken        = sum(1 for i, sid in enumerate(station_ids)
                           if actual_workloads[i] > time_caps[sid])
    max_workload     = float(np.max(actual_workloads)) if actual_workloads else 0.0
    workload_std_dev = float(np.std(actual_workloads)) if actual_workloads else 0.0

    print(f"  CG Done: Visits={best_visits}, Time={elapsed:.2f}s, "
          f"WL_Std={workload_std_dev:.4f}, Max_WL={max_workload:.4f}")

    # Save the log
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    timestamp = time.strftime("%Y%md_%H%M%S")
    log_file = os.path.join(log_dir, f"cg_hexaly_scenario_log_{scenario_name}_{timestamp}.txt")
    with open(log_file, "w") as f:
        for k, v in log_data.items():
            f.write(f"{k}: {v}\n")

    return best_assignment, best_visits, elapsed, max_workload, workload_std_dev, cap_broken, wl_broken


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CG CSLAP (Hexaly, synthetic)")
    parser.add_argument("--prefix", type=str, required=True)
    parser.add_argument("--dir",    type=str, default="synthetic_datasets")
    parser.add_argument("--time",   type=int, default=300)
    args = parser.parse_args()

    print(f"Running CG on {args.prefix}...")
    order_prods, stations, products, prod_lines = read_data(args.prefix, args.dir)
    column_generation_hexaly(
        order_prods, stations, products, prod_lines, time_limit=args.time,
        scenario_name=args.prefix
    )
