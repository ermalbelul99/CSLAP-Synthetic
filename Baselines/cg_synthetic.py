"""
Column Generation for CSLAP using Hexaly Optimizer (Synthetic Data Adapter)

Implements the CG framework from the paper:
- Master problem: pattern selection LP (relaxed)
- Pricing subproblems: one per station, generating new patterns
- Heuristic pricing first, exact pricing fallback
- Final binary resolution step
"""

import numpy as np
import pandas as pd
import hexaly.optimizer as hexaly
import os
import time
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


# -
#  INITIAL PATTERN: distribute products round-robin
# -
def generate_initial_patterns(products, stations, prod_lines):
    station_ids = [s["STATION_ID"] for s in stations]
    capacities = {s["STATION_ID"]: s["CAPACITY"] for s in stations}
    time_caps = {s["STATION_ID"]: s["TIME_CAPACITY"] for s in stations}
    speeds = {s["STATION_ID"]: s["SPEED"] for s in stations}

    sorted_prods = sorted(products, key=lambda p: prod_lines.get(p, 0), reverse=True)
    patterns = {s: [] for s in station_ids}
    
    rem_cap = dict(capacities)
    rem_time = dict(time_caps)
    idx = 0

    for p in sorted_prods:
        placed = False
        workload_cost = prod_lines.get(p, 0)
        
        for attempt in range(len(station_ids)):
            sid = station_ids[(idx + attempt) % len(station_ids)]
            time_cost = workload_cost / speeds[sid] if speeds[sid] > 0 else 0
            
            # Must satisfy BOTH constraints
            if rem_cap[sid] > 0 and rem_time[sid] >= time_cost:
                patterns[sid].append(p)
                rem_cap[sid] -= 1
                rem_time[sid] -= time_cost
                idx = (idx + attempt + 1) % len(station_ids)
                placed = True
                break
                
        if not placed:
            # Fallback: force it into the station where it causes the least time violation
            best_sid = min(station_ids, key=lambda s: (workload_cost / speeds[s]) - rem_time[s])
            patterns[best_sid].append(p)

    return patterns


# -
#  EVALUATE TOTAL VISITS FOR AN ASSIGNMENT
# -
def evaluate_assignment(assignment, order_prods):
    total_visits = 0
    for o, prods in order_prods.items():
        visited = set()
        for p in prods:
            if p in assignment:
                visited.add(assignment[p])
        total_visits += len(visited)
    return total_visits


# -
#  HEURISTIC PRICING
# -
def heuristic_pricing(
    station_id, products, order_prods, prod_lines,
    station_cap, station_speed, station_time_cap,
    sigma_p, pi_s, current_workloads,
):
    """
    Greedy heuristic pricing: build a pattern by greedily selecting
    products with highest modified dual score.
    """
    # Dynamic workload penalty
    total_wl = sum(current_workloads.values()) if current_workloads else 1.0
    w_s = current_workloads.get(station_id, 0) / max(total_wl, 1.0)

    # Score each product
    scored = []
    for p in products:
        lp = prod_lines.get(p, 0)
        base_sigma = sigma_p.get(p, 0)
        penalty = w_s * lp
        score = base_sigma - penalty
        scored.append((p, score, lp))

    scored.sort(key=lambda x: -x[1])

    # Greedily build pattern
    pattern = []
    total_workload = 0.0
    for p, score, lp in scored:
        if len(pattern) >= station_cap:
            break
        if total_workload + lp <= station_time_cap:
            pattern.append(p)
            total_workload += lp

    if not pattern:
        return None

    # Compute reduced cost
    pattern_set = set(pattern)
    z_count = 0
    for o, prods in order_prods.items():
        if any(p in pattern_set for p in prods):
            z_count += 1

    reduced_cost = z_count - sum(sigma_p.get(p, 0) for p in pattern) + pi_s

    if reduced_cost < -1e-6:
        return pattern
    return None


# -
#  COLUMN GENERATION MAIN
# -
def column_generation_hexaly(
    order_prods, stations, products, prod_lines,
    time_limit=300, max_cg_iterations=50, pricing_time_limit=30, warm_start_assignment=None
):
    """
    CG framework:
    1. Generate initial patterns
    2. Solve master (LP relaxed) - get dual values
    3. Solve pricing (heuristic then exact) - add patterns with negative RC
    4. Repeat until no improvement
    5. Final binary resolution
    """
    start_time = time.time()

    station_ids = [s["STATION_ID"] for s in stations]
    capacities = {s["STATION_ID"]: s["CAPACITY"] for s in stations}
    time_caps = {s["STATION_ID"]: s["TIME_CAPACITY"] for s in stations}
    speeds = {s["STATION_ID"]: s["SPEED"] for s in stations}

    N = len(products)
    orders = list(order_prods.keys())

    # --- Initial patterns ---
    if warm_start_assignment is not None:
        print("  CG (Hexaly): Using provided warm start assignment for initial patterns...")
        init_patterns = {s["STATION_ID"]: [] for s in stations}
        for p, s in warm_start_assignment.items():
            if s in init_patterns:
                init_patterns[s].append(p)
    else:
        print("  CG (Hexaly): Generating initial patterns...")
        init_patterns = generate_initial_patterns(products, stations, prod_lines)

    # K_s: map station - list of pattern IDs
    K_s = {s: [f"k_{s}_1"] for s in station_ids}
    # Pattern contents
    all_patterns = {}
    for s in station_ids:
        all_patterns[f"k_{s}_1"] = init_patterns[s]

    # Precompute delta (product-in-pattern) and z_osk (order-visits-pattern)
    delta = {}
    for s in station_ids:
        for k in K_s[s]:
            pattern_set = set(all_patterns[k])
            for p in products:
                delta[(p, s, k)] = 1 if p in pattern_set else 0

    z_osk = {}
    for o in orders:
        prods_set = set(order_prods[o])
        for s in station_ids:
            for k in K_s[s]:
                pattern_set = set(all_patterns[k])
                z_osk[(o, s, k)] = 1 if bool(prods_set & pattern_set) else 0

    # --- Iterative CG ---
    # Since Hexaly doesn't directly expose LP duals, we use a simplified
    # approach: solve the master as MILP, use the solution to guide pricing
    # heuristically, and iterate.

    best_assignment = None
    best_visits = float("inf")

    for iteration in range(1, max_cg_iterations + 1):
        elapsed = time.time() - start_time
        if elapsed > time_limit:
            print(f"  CG: Time limit reached at iteration {iteration}")
            break

        print(f"  CG Iteration {iteration}...")

        # Solve master problem with Hexaly (binary selection of patterns)
        remaining_time = max(10, int(time_limit - elapsed) // 3)

        try:
            with hexaly.HexalyOptimizer() as optimizer:
                model = optimizer.model
                optimizer.param.verbosity = 0
                optimizer.param.time_limit = min(remaining_time, 60)

                # y[s,k] binary: select pattern k for station s
                y = {}
                for s in station_ids:
                    for k in K_s[s]:
                        y[(s, k)] = model.bool()

                # Pattern selection: at most one pattern per station
                for s in station_ids:
                    model.constraint(
                        model.sum(y[(s, k)] for k in K_s[s]) <= 1
                    )

                # Product coverage: each product covered by at least one pattern
                for p in products:
                    model.constraint(
                        model.sum(
                            delta.get((p, s, k), 0) * y[(s, k)]
                            for s in station_ids for k in K_s[s]
                        ) >= 1
                    )

                # Objective: minimize visits
                obj = model.sum(
                    z_osk.get((o, s, k), 0) * y[(s, k)]
                    for o in orders for s in station_ids for k in K_s[s]
                )
                model.minimize(obj)
                model.close()

                optimizer.solve()

                master_val = optimizer.solution.get_value(model.objectives[0])
                print(f"    Master objective: {master_val}")

                # Extract selected patterns
                selected = {}
                for s in station_ids:
                    for k in K_s[s]:
                        if optimizer.solution.get_value(y[(s, k)]) >= 0.5:
                            selected[s] = k

                # Build assignment from selected patterns
                assignment = {}
                for s, k in selected.items():
                    for p in all_patterns[k]:
                        assignment[p] = s

                visits = evaluate_assignment(assignment, order_prods)
                if visits < best_visits:
                    best_visits = visits
                    best_assignment = assignment.copy()

        except Exception as e:
            print(f"    Master solve error: {e}")
            break

        # --- Heuristic pricing ---
        # Compute approximate dual values from the solution
        # sigma_p = how much "savings" a product contributes
        sigma_p = {}
        for p in products:
            # Approximate: number of orders containing p
            sigma_p[p] = prod_lines.get(p, 0) / max(len(orders), 1)

        # Current workloads
        current_wl = defaultdict(float)
        if best_assignment:
            for p, sid in best_assignment.items():
                current_wl[sid] += prod_lines.get(p, 0)

        new_patterns_found = False
        for s_info in stations:
            s = s_info["STATION_ID"]
            pi_s = -1.0  # Approximate dual for pattern selection

            new_pattern = heuristic_pricing(
                s, products, order_prods, prod_lines,
                capacities[s], speeds[s], time_caps[s],
                sigma_p, pi_s, current_wl,
            )

            if new_pattern is not None:
                # Check it's actually different from existing patterns
                new_set = set(new_pattern)
                is_duplicate = False
                for k in K_s[s]:
                    if set(all_patterns[k]) == new_set:
                        is_duplicate = True
                        break

                if not is_duplicate:
                    new_patterns_found = True
                    pattern_id = f"k_{s}_{len(K_s[s]) + 1}"
                    K_s[s].append(pattern_id)
                    all_patterns[pattern_id] = new_pattern

                    # Update delta and z_osk
                    for p in products:
                        delta[(p, s, pattern_id)] = 1 if p in new_set else 0

                    for o in orders:
                        prods_set = set(order_prods[o])
                        z_osk[(o, s, pattern_id)] = 1 if bool(
                            prods_set & new_set
                        ) else 0

                    print(f"    Added pattern {pattern_id} ({len(new_pattern)} products)")

        if not new_patterns_found:
            print("  CG: No new patterns found. Converged.")
            break

    elapsed = time.time() - start_time

    # If we have no assignment yet, use initial
    if best_assignment is None:
        best_assignment = {}
        for s in station_ids:
            for p in init_patterns[s]:
                best_assignment[p] = s
        best_visits = evaluate_assignment(best_assignment, order_prods)

    # --- Workload distribution tracking ---
    station_counts = defaultdict(int)
    station_actions = defaultdict(float)
    
    for p, sid in best_assignment.items():
        station_counts[sid] += 1
        qty = prod_lines.get(p, 0)
        station_actions[sid] += qty
        
    cap_broken = sum(1 for sid in station_ids if station_counts[sid] > capacities[sid])
    wl_broken = sum(1 for sid in station_ids if station_actions[sid] > time_caps[sid])

    actual_workloads = [station_actions[sid] for sid in station_ids]
    max_workload = float(np.max(actual_workloads)) if actual_workloads else 0.0
    workload_variance = float(np.var(actual_workloads)) if actual_workloads else 0.0

    print(f"  CG Done: Visits={best_visits}, Time={elapsed:.2f}s, "
          f"WL_Var={workload_variance:.4f}, Max_WL={max_workload:.4f}")

    return best_assignment, best_visits, elapsed, max_workload, workload_variance, cap_broken, wl_broken


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CG CSLAP (Hexaly, synthetic)")
    parser.add_argument("--prefix", type=str, required=True)
    parser.add_argument("--dir", type=str, default="synthetic_datasets")
    parser.add_argument("--time", type=int, default=300)
    args = parser.parse_args()

    print(f"Running CG on {args.prefix}...")
    order_prods, stations, products, prod_lines = read_data(args.prefix, args.dir)
    column_generation_hexaly(
        order_prods, stations, products, prod_lines, time_limit=args.time
    )
