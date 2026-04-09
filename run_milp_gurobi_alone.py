"""
Runner for MILP Gurobi Synthetic Data Alone.
===================================
Runs only the MILP Gurobi baseline on a specific synthetic dataset,
including the LPT Feasible warm start evaluation, and saves the results
with exactly the same metrics as the main benchmark script.

Usage:
    python run_milp_gurobi_alone.py --size 1000
    python run_milp_gurobi_alone.py --size 2000 --time_limit 72000
"""

import sys
import os
import time
import argparse
import numpy as np
import pandas as pd
import traceback

# Add project paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "Data_Generators"))
sys.path.insert(0, os.path.join(BASE_DIR, "Baselines"))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from heuristic_synthetic import read_data as heur_read_data
from milp_gurobi_synthetic import read_data as milp_read_data, run_milp_gurobi

def log_error(prefix, method, error_msg):
    log_file = os.path.join(BASE_DIR, "error_log.txt")
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a") as f:
        f.write(f"[{timestamp}] Dataset: {prefix} | Method: {method} | Error: {error_msg}\n")

def generate_feasible_start(products_list, stations, prod_lines):
    """
    Generate a strictly feasible {product: station_ID} assignment using
    Longest Processing Time (LPT) load balancing. Guarantees:
      - EXACT physical capacity per station (num_skus // num_stations)
      - Balanced TIME_CAPACITY constraints
    """
    station_ids = [s["STATION_ID"] for s in stations]
    capacities  = {s["STATION_ID"]: s["CAPACITY"]     for s in stations}
    time_caps   = {s["STATION_ID"]: s["TIME_CAPACITY"] for s in stations}
    speeds      = {s["STATION_ID"]: s["SPEED"]         for s in stations}

    assigned = {}
    st_count = {sid: 0 for sid in station_ids}
    st_workload = {sid: 0.0 for sid in station_ids}

    avg_speed = sum(speeds.values()) / len(speeds) if speeds else 1.0
    sorted_prods = sorted(
        products_list,
        key=lambda p: prod_lines.get(p, 0) / avg_speed,
        reverse=True
    )

    for p in sorted_prods:
        freq = prod_lines.get(p, 0)
        best_sid = None
        min_curr_wl = float('inf')

        for sid in station_ids:
            if st_count[sid] >= capacities[sid]:
                continue
            
            if st_workload[sid] < min_curr_wl:
                min_curr_wl = st_workload[sid]
                best_sid = sid
        
        if best_sid is None:
            best_sid = station_ids[0]
            
        assigned[p] = best_sid
        st_count[best_sid] += 1
        st_workload[best_sid] += freq / speeds.get(best_sid, 1.0)
        
    print(f"  [Feasible Start] LPT generated for {len(products_list)} items.")
    for sid in station_ids:
        print(f"    St {sid}: {st_count[sid]}/{capacities[sid]} items, "
              f"WL: {st_workload[sid]:.1f}/{time_caps[sid]}")

    return assigned

def do_milp_gurobi(N, prefix, data_dir, tl, heur_assignment, num_orders, num_skus, num_stations):
    print(f"\n[{prefix}] MILP Gurobi Started")
    try:
        op, st, pr, pl = milp_read_data(prefix, data_dir)
        milp_assignment, visits, elapsed, max_wl, wl_var, cap_broken, wl_broken, best_bound = run_milp_gurobi(
            op, st, pr, pl, time_limit=tl, warm_start_assignment=heur_assignment
        )
        print(f"  [{prefix}] MILP Gurobi Done ({elapsed:.2f}s)")
        res = {
            "visits": visits, "time": elapsed, 
            "max_workload": max_wl, "workload_std_dev": wl_var,
            "cap_broken": cap_broken, "wl_broken": wl_broken, 
            "num_orders": num_orders, "num_skus": num_skus, "num_stations": num_stations
        }
        return res, milp_assignment, best_bound
    except Exception as e:
        print(f"  [{prefix}] MILP Gurobi failed: {e}")
        log_error(prefix, "MILP Gurobi Single", f"{e}\n{traceback.format_exc()}")
        res = {
            "visits": "-", "time": "-", 
            "max_workload": "-", "workload_std_dev": "-",
            "cap_broken": "-", "wl_broken": "-", 
            "num_orders": num_orders, "num_skus": num_skus, "num_stations": num_stations
        }
        return res, None, None

def run_gurobi_alone(size, data_dir="synthetic_datasets", time_limit=72000):
    N = size
    prefix = f"syn_{N}sku"
    print("=" * 70)
    print(f"RUNNING MILP GUROBI ONLY: N = {N} SKUs ({prefix})")
    print("=" * 70)
    
    results = {N: {}}
    
    # Pre-read data to get dimensions once
    try:
        op_dim, st_dim, pr_dim, pl_dim, odf_dim = heur_read_data(prefix, data_dir)
        num_orders = len(op_dim)
        num_skus = len(pr_dim)
        num_stations = len(st_dim)
    except Exception as e:
        print(f"Failed to read data for {prefix}: {e}")
        return

    # Generate LPT Feasible Warm Start
    print("\n[Warm Start] Generating feasibility-only (LPT) warm start...")
    fs_start_time = time.time()
    feasible_warm_start = generate_feasible_start(pr_dim, st_dim, pl_dim)
    fs_elapsed = time.time() - fs_start_time
    
    # Evaluate Feasible Warm Start as an approach
    fs_visits = 0
    for o, prods in op_dim.items():
        visited = set()
        for p in prods:
            if p in feasible_warm_start:
                visited.add(feasible_warm_start[p])
        fs_visits += len(visited)
    
    st_ids = [s["STATION_ID"] for s in st_dim]
    caps = {s["STATION_ID"]: s["CAPACITY"] for s in st_dim}
    time_caps = {s["STATION_ID"]: s["TIME_CAPACITY"] for s in st_dim}
    spds = {s["STATION_ID"]: s["SPEED"] for s in st_dim}
    
    fc_count = {sid: 0 for sid in st_ids}
    fc_wl = {sid: 0.0 for sid in st_ids}
    for p, sid in feasible_warm_start.items():
        fc_count[sid] += 1
        fc_wl[sid] += pl_dim.get(p, 0) / spds.get(sid, 1.0)
        
    fs_cap_broken = sum(1 for sid in st_ids if fc_count[sid] > caps[sid])
    fs_actual_wls = [fc_wl[sid] for sid in st_ids]
    fs_wl_broken = sum(1 for idx, sid in enumerate(st_ids) if fs_actual_wls[idx] > time_caps[sid])
    fs_max_wl = float(np.max(fs_actual_wls)) if fs_actual_wls else 0.0
    fs_wl_std = float(np.std(fs_actual_wls)) if fs_actual_wls else 0.0

    results[N]["Feasible Start"] = {
        "visits": fs_visits,
        "time": fs_elapsed,
        "max_workload": fs_max_wl,
        "workload_std_dev": fs_wl_std,
        "cap_broken": fs_cap_broken,
        "wl_broken": fs_wl_broken,
        "num_orders": num_orders,
        "num_skus": num_skus,
        "num_stations": num_stations
    }

    # Phase B: MILP Gurobi
    res_milp_g, milp_g_assignment, best_bound = do_milp_gurobi(
        N, prefix, data_dir, time_limit, feasible_warm_start, num_orders, num_skus, num_stations
    )
    
    # Fallback to Feasible Start metrics if MILP Gurobi returns an empty visits result (e.g. timeout without improving incmb)
    if res_milp_g["visits"] == "-":
        print(f"  [{prefix}] MILP Gurobi failed to find solution, falling back to heuristic.")
        res_milp_g["visits"] = fs_visits
        res_milp_g["max_workload"] = fs_max_wl
        res_milp_g["workload_std_dev"] = fs_wl_std
        res_milp_g["cap_broken"] = fs_cap_broken
        res_milp_g["wl_broken"] = fs_wl_broken
        log_error(prefix, "MILP Gurobi Single", "Fell back to Feasible Start warm start due to no solution found within limit.")

    global_lb = best_bound if best_bound is not None and best_bound > 0 else None
    results[N]["MILP Gurobi"] = res_milp_g

    # Calculate global workload metrics once per dataset
    total_workload = sum(pl_dim.values())
    avg_wl_assign_global = total_workload / num_stations if num_stations > 0 else 0.0
    avg_wl_max_global = st_dim[0]['TIME_CAPACITY'] if st_dim else 0.0
    
    # Inject global metrics into all results
    for method in results[N]:
        results[N][method]["time_limit"] = time_limit
        results[N][method]["avg_workload_assign"] = avg_wl_assign_global
        results[N][method]["avg_workload_max"] = avg_wl_max_global
        results[N][method]["lb_gurobi"] = global_lb

    # --- Best Known Solution Gap Calculation ---
    all_visits = []
    for method, metrics in results[N].items():
        v = metrics.get("visits", "-")
        if v != "-" and v is not None:
            all_visits.append(float(v))

    bks = min(all_visits) if all_visits else None

    for method, metrics in results[N].items():
        v = metrics.get("visits", "-")
        if v != "-" and v is not None and bks is not None and bks > 0:
            rpd = ((float(v) - bks) / bks) * 100
            metrics["gap_pct"] = round(rpd, 2)
        else:
            metrics["gap_pct"] = "-"

    # Save results to a standalone CSV file to prevent overwriting the full benchmark
    output_csv = os.path.join(BASE_DIR, f"results_gurobi_alone_{prefix}.csv")
    try:
        df = pd.DataFrame(results[N]).T
        df.index.name = "Method"
        
        expected_cols = [
            "visits", "gap_pct", "lb_gurobi", "time", "time_limit",
            "max_workload", "avg_workload_assign", "avg_workload_max", "workload_std_dev", 
            "cap_broken", "wl_broken", 
            "num_orders", "num_skus", "num_stations"
        ]
        # Keep only cols we have defined
        existing_cols = [c for c in expected_cols if c in df.columns]
        df = df[existing_cols]
        
        # Formatting exactly as in original run_benchmarks.py
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='ignore')
            
        if "time" in df.columns:
            df["time"] = df["time"].apply(lambda x: round(float(x), 2) if isinstance(x, (int, float)) and not pd.isna(x) else x)
            
        for col in df.select_dtypes(include=[np.number]).columns:
            if col != "time":
                df[col] = df[col].apply(lambda x: round(float(x), 5) if isinstance(x, (int, float)) and not pd.isna(x) else x)
        
        df.to_csv(output_csv)
        print(f"  [Results saved to {output_csv}]")
    except Exception as e:
        print(f"  [Failed to save CSV for {prefix}: {e}]")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run solely MILP Gurobi for a specific synthetic data size.")
    parser.add_argument("--size", type=int, required=True, help="Number of SKUs (e.g. 1000 or 2000)")
    parser.add_argument("--data_dir", type=str, default="synthetic_datasets", help="Path to synthetic datasets folder")
    parser.add_argument("--time_limit", type=int, default=72000, help="Time limit in seconds for MILP Gurobi")
    args = parser.parse_args()

    run_gurobi_alone(
        size=args.size,
        data_dir=args.data_dir,
        time_limit=args.time_limit
    )

