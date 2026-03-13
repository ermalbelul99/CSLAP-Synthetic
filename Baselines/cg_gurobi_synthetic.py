"""
Column Generation for CSLAP using Gurobi Optimizer (Synthetic Data Adapter)

Implements the CG framework from the paper:
- Master problem: pattern selection LP (relaxed)
- Exact pricing subproblems via Gurobi: one per station, generating new patterns
- Final binary resolution step
"""

import numpy as np
import pandas as pd
import gurobipy as gp
from gurobipy import GRB
import os
import time
import argparse
from collections import defaultdict


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


def generate_initial_patterns(products, stations, prod_lines):
    """
    Generate one initial pattern per station by distributing products
    in order of descending frequency, respecting capacity.
    """
    station_ids = [s["STATION_ID"] for s in stations]
    capacities = {s["STATION_ID"]: s["CAPACITY"] for s in stations}

    sorted_prods = sorted(products, key=lambda p: prod_lines.get(p, 0), reverse=True)

    patterns = {s: [] for s in station_ids}
    remaining = dict(capacities)
    idx = 0

    for p in sorted_prods:
        placed = False
        for attempt in range(len(station_ids)):
            sid = station_ids[(idx + attempt) % len(station_ids)]
            if remaining[sid] > 0:
                patterns[sid].append(p)
                remaining[sid] -= 1
                idx = (idx + attempt + 1) % len(station_ids)
                placed = True
                break
        if not placed:
            for sid in station_ids:
                patterns[sid].append(p)
                break
    return patterns


def evaluate_assignment(assignment, order_prods):
    total_visits = 0
    for o, prods in order_prods.items():
        visited = set()
        for p in prods:
            if p in assignment:
                visited.add(assignment[p])
        total_visits += len(visited)
    return total_visits


def column_generation_gurobi(
    order_prods, stations, products, prod_lines,
    time_limit=300, max_cg_iterations=50, warm_start_assignment=None
):
    """
    CG framework with Gurobi:
    1. Generate initial patterns
    2. Solve master (LP relaxed) -> get exact dual values (sigma_p, pi_s)
    3. Solve exact pricing -> add patterns with negative RC
    4. Repeat until no improvement
    5. Final binary resolution
    """
    start_time = time.time()

    station_ids = [s["STATION_ID"] for s in stations]
    capacities = {s["STATION_ID"]: s["CAPACITY"] for s in stations}
    time_caps = {s["STATION_ID"]: s["TIME_CAPACITY"] for s in stations}
    speeds = {s["STATION_ID"]: s["SPEED"] for s in stations}
    orders = list(order_prods.keys())

    # --- Initial patterns ---
    if warm_start_assignment is not None:
        print("  CG: Using provided warm start assignment for initial patterns...")
        init_patterns = {s["STATION_ID"]: [] for s in stations}
        for p, s in warm_start_assignment.items():
            if s in init_patterns:
                init_patterns[s].append(p)
    else:
        print("  CG: Generating initial patterns (frequency heuristic)...")
        init_patterns = generate_initial_patterns(products, stations, prod_lines)
    
    K_s = {s: [f"k_{s}_1"] for s in station_ids}
    all_patterns = {}
    for s in station_ids:
        all_patterns[f"k_{s}_1"] = init_patterns[s]

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
        update_pattern_data(s, K_s[s][0], all_patterns[K_s[s][0]])

    env = gp.Env(empty=True)
    env.setParam("OutputFlag", 0)
    env.start()
    
    for iteration in range(1, max_cg_iterations + 1):
        elapsed = time.time() - start_time
        if elapsed > time_limit:
            print(f"  CG: Time limit reached at iteration {iteration}")
            break

        print(f"  CG Iteration {iteration}...")

        # --- Master Problem (LP Relaxation) ---
        rmp = gp.Model("RMP", env=env)
        rmp.setParam('OutputFlag', 0)
        
        y = {}
        for s in station_ids:
            for k in K_s[s]:
                y[(s, k)] = rmp.addVar(lb=0.0, ub=1.0, vtype=GRB.CONTINUOUS, name=f"y_{s}_{k}")
                
        # Objective
        rmp.setObjective(
            gp.quicksum(z_osk.get((o, s, k), 0) * y[(s, k)] for o in orders for s in station_ids for k in K_s[s]),
            GRB.MINIMIZE
        )
        
        # Constraints
        # 1. Product coverage
        cov_constrs = {}
        for p in products:
            cov_constrs[p] = rmp.addConstr(
                gp.quicksum(delta.get((p, s, k), 0) * y[(s, k)] for s in station_ids for k in K_s[s]) >= 1,
                name=f"cov_{p}"
            )
            
        # 2. At most one pattern per station
        pat_constrs = {}
        for s in station_ids:
            pat_constrs[s] = rmp.addConstr(
                gp.quicksum(y[(s, k)] for k in K_s[s]) <= 1,
                name=f"pat_{s}"
            )
            
        rmp.optimize()
        
        if rmp.Status != GRB.OPTIMAL:
            print(f"    RMP failed with status {rmp.Status}")
            break
            
        print(f"    Master objective (LP): {rmp.ObjVal:.3f}")
        
        # Get duals
        sigma = {p: cov_constrs[p].Pi for p in products}
        pi = {s: pat_constrs[s].Pi for s in station_ids}

        # --- Pricing Subproblems ---
        new_patterns_found = False
        remaining_time_for_pricing = max(5, int(time_limit - (time.time() - start_time)) // len(station_ids))
        
        for s in station_ids:
            sp = gp.Model(f"Pricing_{s}", env=env)
            sp.setParam('OutputFlag', 0)
            sp.setParam('TimeLimit', remaining_time_for_pricing)
            
            # Variables
            a = sp.addVars(products, vtype=GRB.BINARY, name="a")
            z_sp = sp.addVars(orders, lb=0.0, ub=1.0, vtype=GRB.CONTINUOUS, name="z")
            
            # Constraints
            sp.addConstr(a.sum() <= capacities[s], name="cap")
            sp.addConstr(
                gp.quicksum((prod_lines.get(p, 0) / speeds[s]) * a[p] for p in products) <= time_caps[s],
                name="workload"
            )
            
            for o in orders:
                for p in order_prods[o]:
                    if p in products:
                        sp.addConstr(z_sp[o] >= a[p], name=f"link_{o}_{p}")
                        
            # Objective: min sum_o z_o - sum_p sigma_p * a_p - pi_s
            # We want to find patterns with negative reduced cost
            sp.setObjective(
                gp.quicksum(z_sp[o] for o in orders) - gp.quicksum(sigma[p] * a[p] for p in products) - pi[s],
                GRB.MINIMIZE
            )
            
            sp.optimize()
            
            if sp.Status == GRB.OPTIMAL or (sp.Status == GRB.TIME_LIMIT and sp.SolCount > 0):
                rc = sp.ObjVal
                if rc < -1e-4:  # Negative reduced cost
                    new_pattern = [p for p in products if a[p].X > 0.5]
                    
                    # Avoid duplicates
                    new_set = set(new_pattern)
                    is_duplicate = any(set(all_patterns[k]) == new_set for k in K_s[s])
                    
                    if not is_duplicate and len(new_pattern) > 0:
                        new_patterns_found = True
                        pattern_id = f"k_{s}_{len(K_s[s]) + 1}"
                        K_s[s].append(pattern_id)
                        all_patterns[pattern_id] = new_pattern
                        update_pattern_data(s, pattern_id, new_pattern)
                        print(f"    Added pattern {pattern_id} for st. {s} (RC={rc:.3f})")

        if not new_patterns_found:
            print("  CG: No negative reduced cost patterns found. Converged.")
            break

    # --- Final Binary Resolution ---
    print("  CG: Solving final Integer Master Problem...")
    imp = gp.Model("IMP", env=env)
    imp.setParam('OutputFlag', 0)
    imp.setParam('TimeLimit', max(10, time_limit - (time.time() - start_time)))
    
    y = {}
    for s in station_ids:
        for k in K_s[s]:
            y[(s, k)] = imp.addVar(vtype=GRB.BINARY, name=f"y_{s}_{k}")
            
    imp.setObjective(
        gp.quicksum(z_osk.get((o, s, k), 0) * y[(s, k)] for o in orders for s in station_ids for k in K_s[s]),
        GRB.MINIMIZE
    )
    
    for p in products:
        imp.addConstr(
            gp.quicksum(delta.get((p, s, k), 0) * y[(s, k)] for s in station_ids for k in K_s[s]) >= 1,
            name=f"cov_{p}"
        )
        
    for s in station_ids:
        imp.addConstr(gp.quicksum(y[(s, k)] for k in K_s[s]) <= 1, name=f"pat_{s}")
        
    imp.optimize()
    elapsed = time.time() - start_time
    
    best_assignment = {}
    best_visits = float('inf')
    util_variance = 0.0
    
    if imp.Status in [GRB.OPTIMAL, GRB.TIME_LIMIT] and imp.SolCount > 0:
        for s in station_ids:
            for k in K_s[s]:
                if y[(s, k)].X > 0.5:
                    for p in all_patterns[k]:
                        best_assignment[p] = s
                        
        best_visits = evaluate_assignment(best_assignment, order_prods)
        
        station_counts = defaultdict(int)
        station_workload = defaultdict(float)
        for p, sid in best_assignment.items():
            station_counts[sid] += 1
            station_workload[sid] += prod_lines.get(p, 0)
            
        cap_broken = sum(1 for sid in station_ids if station_counts[sid] > capacities[sid])
            
        util_values = []
        for sid in station_ids:
            time_spent = station_workload[sid] / speeds[sid] if speeds[sid] > 0 else 0
            utilization = time_spent / time_caps[sid] if time_caps[sid] > 0 else 0
            util_values.append(utilization)
            
        util_variance = float(np.var(util_values)) if util_values else 0.0
        max_util = float(np.max(util_values)) if util_values else 0.0
        wl_broken = sum(1 for u in util_values if u > 1.0)
    else:
        print("  CG: IMP failed, falling back to initial patterns.")
        for s in station_ids:
            for p in init_patterns[s]:
                best_assignment[p] = s
        best_visits = evaluate_assignment(best_assignment, order_prods)
        max_util = 0.0
        cap_broken = 0
        wl_broken = 0

    print(f"  CG Done: Visits={best_visits}, Time={elapsed:.2f}s, Util_Var={util_variance:.4f}, Max_Util={max_util:.4f}, Cap_Broken={cap_broken}, WL_Broken={wl_broken}")
    return best_assignment, best_visits, elapsed, util_variance, max_util, cap_broken, wl_broken


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CG CSLAP (Gurobi, synthetic)")
    parser.add_argument("--prefix", type=str, required=True)
    parser.add_argument("--dir", type=str, default="synthetic_datasets")
    parser.add_argument("--time", type=int, default=300)
    args = parser.parse_args()

    print(f"Running CG on {args.prefix}...")
    order_prods, stations, products, prod_lines = read_data(args.prefix, args.dir)
    column_generation_gurobi(
        order_prods, stations, products, prod_lines, time_limit=args.time
    )
