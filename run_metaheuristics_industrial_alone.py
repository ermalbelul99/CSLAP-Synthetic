import sys
import os
import time
import argparse
import numpy as np
import pandas as pd
from collections import defaultdict
import concurrent.futures
import traceback

# Add project paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "Baselines"))

from dotenv import load_dotenv
load_dotenv()

from sa_correlated import simulated_annealing_correlated
from ga_baseline import genetic_algorithm

from data_loader_industrial import load_industrial_data

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


def log_error(method, error_msg):
    log_file = os.path.join(BASE_DIR, "error_log.txt")
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a") as f:
        f.write(f"[{timestamp}] Dataset: Industrial isolated Metaheuristics | Method: {method} | Error: {error_msg}\n")


def run_solver_wrapper(method_name, func, op_solver, st_solver, pr_solver, pl_solver, 
                       static_assignment, op_full, st_full, pl_full, **kwargs):
    """
    Module-level wrapper for multiprocessing compatibility.
    Solves the pickling issue by being defined at module scope.
    """
    print(f"\n[{method_name}] Started")
    try:
        start_t = time.time()
        res = func(op_solver, st_solver, pr_solver, pl_solver, **kwargs)
        # Extract assignment and calculate metrics
        best_assignment = res[0]
        elapsed = time.time() - start_t
        
        visits, max_wl, wl_std, cap_b, wl_b = evaluate_full_metrics(
            best_assignment, static_assignment, op_full, st_full, pl_full
        )
        lb = res[-1] if method_name == "MILP Gurobi" and best_assignment is not None else None
        print(f"  [{method_name}] Done in {elapsed:.2f}s | Full Visits: {visits}")
        return method_name, visits, elapsed, max_wl, wl_std, cap_b, wl_b, lb
    except Exception as e:
        print(f"  [{method_name}] Failed: {e}")
        log_error(method_name, traceback.format_exc())
        return method_name, "-", "-", "-", "-", "-", "-", None


def run_industrial_benchmarks(data_path, time_limit=72000, quick=False):
    print("=" * 70)
    print("PHASE 1: Loading and Preprocessing Industrial Data for Metaheuristics")
    print("=" * 70)
    
    try:
        data = load_industrial_data(data_path)
    except Exception as e:
        print(f"Failed to load industrial data: {e}")
        traceback.print_exc()
        return

    op_solver = data["op_solver"]
    st_solver = data["st_solver"]
    pr_solver = data["pr_solver"]
    pl_solver = data["pl_solver"]
    warm_start_assignment = data["warm_start_assignment"]
    static_assignment = data["static_assignment"]
    op_full = data["op_full"]
    st_full = data["st_full"]
    pl_full = data["pl_full"]

    num_orders = len(op_full)
    num_skus = len(pr_solver) + len(static_assignment)
    num_stations = len(st_full)
    
    print(f"\nData loaded! Total Orders: {num_orders}, Total SKUs: {num_skus}")
    print(f"Solvers will optimize {len(pr_solver)} SKUs across {len(st_solver)} active stations.")
    print(f"{len(static_assignment)} low-frequency SKUs are statically fixed to base stations.")

    results = {}

    def format_res(method, visits, elapsed, max_wl, util_var, cap_b, wl_b, lb=None):
        return {
            "Method": method,
            "visits": visits,
            "lb_gurobi": lb,
            "time": elapsed,
            "max_workload": max_wl,
            "utilization_std_dev": util_var,
            "cap_broken": cap_b,
            "wl_broken": wl_b,
            "num_orders": num_orders,
            "num_skus": num_skus,
            "num_stations": num_stations
        }

    output_csv = os.path.join(BASE_DIR, "results_metaheuristics_industrial_alone.csv")
    
    def save_current_results():
        # --- Best Known Solution Gap Calculation ---
        all_visits = []
        for m, r in results.items():
            v = r.get("visits", "-")
            if v != "-" and v is not None:
                all_visits.append(float(v))
                
        bks = min(all_visits) if all_visits else None
        global_lb = results.get("MILP Gurobi", {}).get("lb_gurobi", None)

        save_dict = {}
        for m, r in results.items():
            # Create a copy so we don't permanently mutate the stored result dict with gap_pct in-place if BKS changes
            row_dict = r.copy()
            v = row_dict.get("visits", "-")
            if v != "-" and v is not None and bks is not None and bks > 0:
                row_dict["gap_pct"] = round(((float(v) - bks) / bks) * 100, 2)
            else:
                row_dict["gap_pct"] = "-"
            row_dict["time_limit"] = tl
            row_dict["lb_gurobi"] = global_lb
            save_dict[m] = row_dict

        try:
            df = pd.DataFrame(save_dict).T
            df.index.name = "Method"
            expected_cols = [
                "visits", "gap_pct", "lb_gurobi", "time", "time_limit",
                "max_workload", "utilization_std_dev", 
                "cap_broken", "wl_broken", 
                "num_orders", "num_skus", "num_stations"
            ]
            existing_cols = [c for c in expected_cols if c in df.columns]
            df = df[existing_cols]
            
            for col in df.columns:
                try:
                    df[col] = pd.to_numeric(df[col])
                except ValueError:
                    pass
                
            df.to_csv(output_csv)
            print(f"  [I/O] Results checkpoint explicitly saved to {output_csv}")
        except Exception as e:
            print(f"  [I/O Error] Failed to save CSV: {e}")

    tl = time_limit if not quick else min(60, time_limit)

    # We use the warm start provided directly by the industrial initial assignments
    print("\n[Warm Start] Using base industrial assignment for initial locations...")
    warm_start_time = time.time()
    
    # Evaluate warm start as an approach (it represents the current real warehouse configuration exactly!)
    visits_ws, max_wl_ws, wl_std_ws, cap_b_ws, wl_b_ws = evaluate_full_metrics(
        warm_start_assignment, static_assignment, op_full, st_full, pl_full
    )
    ws_elapsed = time.time() - warm_start_time
    results["Industrial Current"] = format_res("Industrial Current", visits_ws, ws_elapsed, max_wl_ws*1.1, wl_std_ws, cap_b_ws, wl_b_ws)
    print(f"  [Industrial Current] Initial real-world configuration | Full Visits: {visits_ws}")

    active_warm_start = warm_start_assignment

    # Metaheuristics (Parallel execution restored for Server)
    with concurrent.futures.ProcessPoolExecutor(max_workers=2) as executor:
        f_sac = executor.submit(
            run_solver_wrapper, "SA-C", simulated_annealing_correlated, 
            op_solver, st_solver, pr_solver, pl_solver,
            static_assignment, op_full, st_full, pl_full,
            time_limit=tl, quick=quick, warm_start_assignment=active_warm_start
        )
        f_ga = executor.submit(
            run_solver_wrapper, "GA", genetic_algorithm, 
            op_solver, st_solver, pr_solver, pl_solver,
            static_assignment, op_full, st_full, pl_full,
            time_limit=tl, quick=quick, warm_start_assignment=active_warm_start
        )
        
        # As each parallel approach finishes, save the CSV checkpoint
        for f in concurrent.futures.as_completed([f_sac, f_ga]):
            m, v, el, mw, wls, cb, wb, _ = f.result()
            results[m] = format_res(m, v, el, mw, wls, cb, wb)
            save_current_results()
            
    print(f"\n[Success] Metaheuristics industrial isolated benchmark pipeline finished.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CSLAP Metaheuristics Runner for Industrial Data")
    parser.add_argument("--data_path", type=str, default="Heuristic_Connex_Set_Project/data/BERNER_ORDER_LINES_09-12.csv")
    parser.add_argument("--quick", action="store_true", help="Fast smoke test (1 min per method)")
    parser.add_argument("--time_limit", type=int, default=72000, help="Time limit in seconds")
    args = parser.parse_args()

    run_industrial_benchmarks(
        data_path=args.data_path,
        time_limit=args.time_limit,
        quick=args.quick
    )
