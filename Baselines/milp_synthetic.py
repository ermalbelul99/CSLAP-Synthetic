"""
MILP for CSLAP using Hexaly Optimizer (Synthetic Data Adapter)
Matches the paper's formulation: binary x_{ps}, continuous z_{os}.
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


def run_milp_hexaly(
    order_prods, stations, products, prod_lines,
    time_limit=120, verbosity=0, warm_start_assignment=None
):
    """
    Solve CSLAP MILP using Hexaly with set decision variables.
    Uses the same formulation as Sub-approach 4 in the paper.
    """
    start_time = time.time()

    orders = list(order_prods.keys())
    station_ids = [s["STATION_ID"] for s in stations]
    capacities = {s["STATION_ID"]: s["CAPACITY"] for s in stations}
    time_caps = {s["STATION_ID"]: s["TIME_CAPACITY"] for s in stations}
    speeds = {s["STATION_ID"]: s["SPEED"] for s in stations}

    product_to_index = {p: idx for idx, p in enumerate(products)}
    N = len(products)

    with hexaly.HexalyOptimizer() as optimizer:
        model = optimizer.model
        optimizer.param.verbosity = verbosity
        optimizer.param.time_limit = time_limit

        # Set decision variables: station_products[s] = set of product indices at s
        station_products = {s: model.set(N) for s in station_ids}

        # Constraint: products partitioned (each assigned to exactly one station)
        model.constraint(
            model.partition([station_products[s] for s in station_ids])
        )

        # Constraint: capacity limits
        for s in station_ids:
            model.constraint(
                model.count(station_products[s]) <= capacities[s]
            )

        # Constraint: workload limits
        for s in station_ids:
            workload = model.sum(
                (prod_lines.get(p, 0) / speeds[s])
                * model.contains(station_products[s], product_to_index[p])
                for p in products
            )
            model.constraint(workload <= time_caps[s])

        # Objective: minimize total station visits
        objective = model.sum(
            model.or_(
                *(
                    model.contains(station_products[s], product_to_index[p])
                    for p in order_prods[o]
                    if p in product_to_index
                )
            )
            for o in orders
            for s in station_ids
        )
        model.minimize(objective)
        model.close()

        # Inject warm start if available (MUST be done after model.close() in Hexaly)
        if warm_start_assignment:
            print("  MILP (Hexaly): Injecting initial heuristic assignment as warm start...")
            for p, s in warm_start_assignment.items():
                if p in product_to_index and s in station_products:
                    idx = product_to_index[p]
                    station_products[s].value.add(idx)

        print(f"  MILP: Solving with Hexaly (time_limit={time_limit}s)...")
        optimizer.solve()

        elapsed = time.time() - start_time

        try:
            val = optimizer.solution.get_objective_bound(0) if optimizer.solution.status == hexaly.HxSolutionStatus.OPTIMAL else optimizer.solution.get_value(model.objectives[0])
            total_visits = int(val)
            
            # --- Workload distribution tracking ---
            assignment = {}
            station_counts = defaultdict(int)
            station_actions = defaultdict(float)
            
            for s in station_ids:
                # Extract indices from Hexaly set
                indices = station_products[s].value
                for idx in indices:
                    p = products[idx]
                    assignment[p] = s
                    station_counts[s] += 1
                    qty = prod_lines.get(p, 0)
                    station_actions[s] += qty
            
            cap_broken = sum(1 for sid in station_ids if station_counts[sid] > capacities[sid])
            wl_broken = sum(1 for sid in station_ids if station_actions[sid] > time_caps[sid])
            
            actual_workloads = [station_actions[sid] for sid in station_ids]
            max_workload = float(np.max(actual_workloads)) if actual_workloads else 0.0
            workload_std_dev = float(np.std(actual_workloads)) if actual_workloads else 0.0

            print(f"  MILP Done: Visits={total_visits}, Time={elapsed:.2f}s, "
                  f"WL_Std={workload_std_dev:.4f}, Max_WL={max_workload:.4f}")
                  
            return assignment, total_visits, elapsed, max_workload, workload_std_dev, cap_broken, wl_broken

        except Exception as e:
            print(f"  MILP: No feasible solution found or error during extraction ({e})")
            return None, None, elapsed, None, None, None, None, None, None

    return None, None, elapsed, None, None, None, None, None, None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MILP CSLAP (Hexaly, synthetic)")
    parser.add_argument("--prefix", type=str, required=True)
    parser.add_argument("--dir", type=str, default="synthetic_datasets")
    parser.add_argument("--time", type=int, default=120)
    args = parser.parse_args()

    print(f"Running MILP on {args.prefix}...")
    order_prods, stations, products, prod_lines = read_data(args.prefix, args.dir)
    run_milp_hexaly(
        order_prods, stations, products, prod_lines, time_limit=args.time
    )
