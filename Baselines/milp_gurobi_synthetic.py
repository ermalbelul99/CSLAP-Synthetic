"""
MILP for CSLAP using Gurobi Optimizer (Synthetic Data Adapter)
Matches the paper's formulation: binary x_{ps}, continuous z_{os}.
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


def run_milp_gurobi(
    order_prods, stations, products, prod_lines,
    time_limit=120, verbosity=0, warm_start_assignment=None
):
    """
    Solve CSLAP MILP using Gurobi.
    Uses the same formulation as Sub-approach 4 in the paper.
    """
    start_time = time.time()

    orders = list(order_prods.keys())
    station_ids = [s["STATION_ID"] for s in stations]
    capacities = {s["STATION_ID"]: s["CAPACITY"] for s in stations}
    time_caps = {s["STATION_ID"]: s["TIME_CAPACITY"] for s in stations}
    speeds = {s["STATION_ID"]: s["SPEED"] for s in stations}

    N_p = len(products)
    N_s = len(station_ids)
    N_o = len(orders)
    
    # Create environment and model
    env = gp.Env(empty=True)
    if verbosity == 0:
        env.setParam("OutputFlag", 0)
    env.start()
    
    model = gp.Model("CSLAP_MILP", env=env)
    model.setParam("TimeLimit", time_limit)
    model.setParam("MIPFocus", 1)  # Prioritize finding feasible solutions
    
    print(f"  MILP: Solving with Gurobi (time_limit={time_limit}s)...")

    # Decision variables
    # x[p, s]: 1 if product p assigned to station s
    x = model.addVars(products, station_ids, vtype=GRB.BINARY, name="x")

    # Inject warm start if available
    if warm_start_assignment:
        print("  MILP: Injecting initial heuristic assignment as MIP start...")
        for p in products:
            if p in warm_start_assignment:
                best_s = warm_start_assignment[p]
                for s in station_ids:
                    x[p, s].Start = 1.0 if s == best_s else 0.0
    
    # z[o, s]: 1 if order o visits station s
    # Can be relaxed to continuous [0,1] since minimization will push it down
    z = model.addVars(orders, station_ids, lb=0.0, ub=1.0, vtype=GRB.CONTINUOUS, name="z")
    
    # Constraint 1: Partition (each product exactly once)
    model.addConstrs(
        (x.sum(p, '*') == 1 for p in products),
        name="partition"
    )
    
    # Constraint 2: Capacity limit
    model.addConstrs(
        (x.sum('*', s) <= capacities[s] for s in station_ids),
        name="capacity"
    )
    
    # Constraint 3: Workload limit
    for s in station_ids:
        model.addConstr(
            gp.quicksum((prod_lines.get(p, 0) / speeds[s]) * x[p, s] for p in products) <= time_caps[s],
            name=f"workload_{s}"
        )
        
    # Constraint 4: Order visit linking
    for o in orders:
        prods_in_o = order_prods[o]
        for s in station_ids:
            for p in prods_in_o:
                if p in products:
                    model.addConstr(z[o, s] >= x[p, s], name=f"link_{o}_{s}_{p}")
                    
    # Objective: minimize total visits
    model.setObjective(gp.quicksum(z[o, s] for o in orders for s in station_ids), GRB.MINIMIZE)
    
    # Solve
    model.optimize()
    elapsed = time.time() - start_time
    
    if model.Status == GRB.OPTIMAL or model.Status == GRB.TIME_LIMIT:
        try:
            best_bound = model.ObjBound
        except AttributeError:
            best_bound = None

        if model.SolCount > 0:
            total_visits = round(model.ObjVal)
            
            # Extract assignment
            assignment = {}
            station_counts = defaultdict(int)
            station_workload = defaultdict(float)
            for p in products:
                for s in station_ids:
                    if x[p, s].X > 0.5:
                        assignment[p] = s
                        station_counts[s] += 1
                        station_workload[s] += prod_lines.get(p, 0)
                        
            cap_broken = sum(1 for s in station_ids if station_counts[s] > capacities[s])
                        
            util_values = []
            for sid in station_ids:
                time_spent = station_workload[sid] / speeds[sid] if speeds[sid] > 0 else 0
                utilization = time_spent / time_caps[sid] if time_caps[sid] > 0 else 0
                util_values.append(utilization)
                
            util_variance = float(np.var(util_values)) if util_values else 0.0
            max_util = float(np.max(util_values)) if util_values else 0.0
            wl_broken = sum(1 for u in util_values if u > 1.0)

            print(f"  MILP Done: Visits={total_visits}, Time={elapsed:.2f}s, Util_Var={util_variance:.4f}, Max_Util={max_util:.4f}, Cap_Broken={cap_broken}, WL_Broken={wl_broken}, BestBound={best_bound}")
            return assignment, total_visits, elapsed, util_variance, max_util, cap_broken, wl_broken, best_bound
    
    try:
        best_bound = model.ObjBound
    except AttributeError:
        best_bound = None

    print(f"  MILP: No feasible solution found in {time_limit}s.")
    return None, None, elapsed, None, None, None, None, best_bound


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MILP CSLAP (Gurobi, synthetic)")
    parser.add_argument("--prefix", type=str, required=True)
    parser.add_argument("--dir", type=str, default="synthetic_datasets")
    parser.add_argument("--time", type=int, default=120)
    args = parser.parse_args()

    print(f"Running MILP on {args.prefix}...")
    order_prods, stations, products, prod_lines = read_data(args.prefix, args.dir)
    run_milp_gurobi(
        order_prods, stations, products, prod_lines, time_limit=args.time, verbosity=1
    )
