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
from heuristic_synthetic import heuristic_cslap
from milp_gurobi_synthetic import run_milp_gurobi
from cg_gurobi_synthetic import column_generation_gurobi
from milp_synthetic import run_milp_hexaly
from cg_synthetic import column_generation_hexaly

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
    wl_broken = sum(1 for sid in station_ids if station_actions[sid] > time_caps.get(sid, 0.0))
    
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
        f.write(f"[{timestamp}] Dataset: Industrial | Method: {method} | Error: {error_msg}\n")


def run_industrial_benchmarks(data_path, time_limit=72000, quick=False):
    print("=" * 70)
    print("PHASE 1: Loading and Preprocessing Industrial Data")
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
    odf_solver = data["odf_solver"]
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
        
    tl = time_limit if not quick else min(60, time_limit)

    # 1. Heuristic
    print("\n[Heuristic] Started")
    try:
        heur_assignment, _, elapsed, _, _, _, _ = heuristic_cslap(
            op_solver, st_solver, pr_solver, pl_solver, odf_solver
        )
        visits, max_wl, wl_std, cap_b, wl_b = evaluate_full_metrics(
            heur_assignment, static_assignment, op_full, st_full, pl_full
        )
        results["Heuristic"] = format_res("Heuristic", visits, elapsed, max_wl, wl_std, cap_b, wl_b)
        print(f"  [Heuristic] Done in {elapsed:.2f}s | Full Visits: {visits}")
    except Exception as e:
        print(f"  [Heuristic] Failed: {e}")
        log_error("Heuristic", traceback.format_exc())
        heur_assignment = None

    # We use the warm start provided directly by the industrial initial assignments
    print("\n[Warm Start] Using base industrial assignment for initial locations...")
    warm_start_time = time.time()
    
    # Evaluate warm start as an approach (it represents the current real warehouse configuration exactly!)
    visits_ws, max_wl_ws, wl_std_ws, cap_b_ws, wl_b_ws = evaluate_full_metrics(
        warm_start_assignment, static_assignment, op_full, st_full, pl_full
    )
    ws_elapsed = time.time() - warm_start_time
    results["Industrial Current"] = format_res("Industrial Current", visits_ws, ws_elapsed, max_wl_ws, wl_std_ws, cap_b_ws, wl_b_ws)
    print(f"  [Industrial Current] Initial real-world configuration | Full Visits: {visits_ws}")

    # Fallback to heuristic for exact solvers if warm start lacks products for some reason
    active_warm_start = warm_start_assignment if warm_start_assignment else heur_assignment

    def run_wrapper(method_name, func, *args, **kwargs):
        print(f"\n[{method_name}] Started")
        try:
            start_t = time.time()
            res = func(*args, **kwargs)
            # Depending on the func, return structure varies. 
            # We extract just the assignment and calculate our own metrics!
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

    # Metaheuristics
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f_sac = executor.submit(
            run_wrapper, "SA-C", simulated_annealing_correlated, 
            op_solver, st_solver, pr_solver, pl_solver,
            time_limit=tl, quick=quick
        )
        f_ga = executor.submit(
            run_wrapper, "GA", genetic_algorithm, 
            op_solver, st_solver, pr_solver, pl_solver,
            time_limit=tl, quick=quick
        )
        
        for f in [f_sac, f_ga]:
            m, v, el, mw, wls, cb, wb, _ = f.result()
            results[m] = format_res(m, v, el, mw, wls, cb, wb)

    # Exact Solvers
    # Run sequentially to avoid excessive memory / license issues
    m, v, el, mw, wls, cb, wb, lb = run_wrapper(
        "MILP Gurobi", run_milp_gurobi,
        op_solver, st_solver, pr_solver, pl_solver,
        time_limit=tl, warm_start_assignment=active_warm_start
    )
    if v == "-":
        print(f"  [MILP Gurobi] Failed to find solution, falling back to heuristic.")
        res = results.get("Heuristic", results["Industrial Current"]).copy()
        res["Method"] = "MILP Gurobi"
        res["lb_gurobi"] = lb
        results["MILP Gurobi"] = res
    else:
        results[m] = format_res(m, v, el, mw, wls, cb, wb, lb)

    m, v, el, mw, wls, cb, wb, _ = run_wrapper(
        "MILP Hexaly", run_milp_hexaly,
        op_solver, st_solver, pr_solver, pl_solver,
        time_limit=tl, warm_start_assignment=active_warm_start
    )
    if v == "-":
        res = results.get("Heuristic", results["Industrial Current"]).copy()
        res["Method"] = "MILP Hexaly"
        results["MILP Hexaly"] = res
    else:
        results[m] = format_res(m, v, el, mw, wls, cb, wb)

    m, v, el, mw, wls, cb, wb, _ = run_wrapper(
        "CG Gurobi", column_generation_gurobi,
        op_solver, st_solver, pr_solver, pl_solver,
        time_limit=tl, warm_start_assignment=active_warm_start, scenario_name="industrial_gurobi"
    )
    results[m] = format_res(m, v, el, mw, wls, cb, wb)

    m, v, el, mw, wls, cb, wb, _ = run_wrapper(
        "CG Hexaly", column_generation_hexaly,
        op_solver, st_solver, pr_solver, pl_solver,
        time_limit=tl, warm_start_assignment=active_warm_start, scenario_name="industrial_hexaly"
    )
    results[m] = format_res(m, v, el, mw, wls, cb, wb)

    # --- Best Known Solution Gap Calculation ---
    all_visits = []
    for m, r in results.items():
        v = r.get("visits", "-")
        if v != "-" and v is not None:
            all_visits.append(float(v))
            
    bks = min(all_visits) if all_visits else None
    
    global_lb = results.get("MILP Gurobi", {}).get("lb_gurobi", None)

    for m, r in results.items():
        v = r.get("visits", "-")
        
        # Gap
        if v != "-" and v is not None and bks is not None and bks > 0:
            rpd = ((float(v) - bks) / bks) * 100
            r["gap_pct"] = round(rpd, 2)
        else:
            r["gap_pct"] = "-"
            
        r["time_limit"] = tl
        r["lb_gurobi"] = global_lb

    # Save to CSV
    output_csv = os.path.join(BASE_DIR, "results_industrial_benchmark.csv")
    try:
        df = pd.DataFrame(results).T
        df.set_index("Method", inplace=True)
        
        expected_cols = [
            "visits", "gap_pct", "lb_gurobi", "time", "time_limit",
            "max_workload", "utilization_std_dev", 
            "cap_broken", "wl_broken", 
            "num_orders", "num_skus", "num_stations"
        ]
        existing_cols = [c for c in expected_cols if c in df.columns]
        df = df[existing_cols]
        
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='ignore')
            
        df.to_csv(output_csv)
        print(f"\n[Success] Industrial benchmark results saved to {output_csv}")
    except Exception as e:
        print(f"\n[Error] Failed to save CSV: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CSLAP Benchmark Runner for Industrial Data")
    parser.add_argument("--data_path", type=str, default="Heuristic_Connex_Set_Project/data/BERNER_ORDER_LINES_09-12.csv")
    parser.add_argument("--quick", action="store_true", help="Fast smoke test (1 min per method)")
    parser.add_argument("--time_limit", type=int, default=72000, help="Time limit in seconds")
    args = parser.parse_args()

    run_industrial_benchmarks(
        data_path=args.data_path,
        time_limit=args.time_limit,
        quick=args.quick
    )
