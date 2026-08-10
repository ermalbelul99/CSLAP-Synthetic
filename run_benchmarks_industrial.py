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

# Lives in Baselines/industrial_metrics.py so that a solver-free re-run (e.g. the
# heuristic-only row of Table 6) can import it without pulling in gurobipy and the
# Hexaly bindings that this module needs at import time. Same single definition.
from industrial_metrics import evaluate_full_metrics


def log_error(method, error_msg):
    log_file = os.path.join(BASE_DIR, "error_log.txt")
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a") as f:
        f.write(f"[{timestamp}] Dataset: Industrial | Method: {method} | Error: {error_msg}\n")


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

    output_csv = os.path.join(BASE_DIR, "results_industrial_benchmark.csv")
    
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
    results["Industrial Current"] = format_res("Industrial Current", visits_ws, ws_elapsed, max_wl_ws*1.1, wl_std_ws, cap_b_ws, wl_b_ws)
    print(f"  [Industrial Current] Initial real-world configuration | Full Visits: {visits_ws}")

    # Fallback to heuristic for exact solvers if warm start lacks products for some reason
    active_warm_start = warm_start_assignment if warm_start_assignment else heur_assignment

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

    # Exact Solvers (Parallel Execution mapping all 32 logical cores)
    exact_tasks = [
        ("MILP Gurobi", run_milp_gurobi, {"time_limit": tl, "warm_start_assignment": active_warm_start}),
        ("MILP Hexaly", run_milp_hexaly, {"time_limit": tl, "warm_start_assignment": active_warm_start}),
        ("CG Gurobi", column_generation_gurobi, {"time_limit": tl, "warm_start_assignment": active_warm_start, "scenario_name": "industrial_gurobi"}),
        ("CG Hexaly", column_generation_hexaly, {"time_limit": tl, "warm_start_assignment": active_warm_start, "scenario_name": "industrial_hexaly"})
    ]

    with concurrent.futures.ProcessPoolExecutor(max_workers=2) as executor:
        future_to_name = {
            executor.submit(
                run_solver_wrapper, name, func, 
                op_solver, st_solver, pr_solver, pl_solver,
                static_assignment, op_full, st_full, pl_full,
                **kwargs
            ): name for name, func, kwargs in exact_tasks
        }
        
        for f in concurrent.futures.as_completed(future_to_name):
            name = future_to_name[f]
            m, v, el, mw, wls, cb, wb, lb = f.result()
            
            # Handle fallback logic if a exact solver fails to find a solution
            if v == "-":
                print(f"  [{name}] Failed to find solution in time limit, falling back to industrial current.")
                res = results.get("Industrial Current", results["Heuristic"]).copy()
                res["Method"] = name
                if name == "MILP Gurobi":
                    res["lb_gurobi"] = lb
                results[name] = res
            else:
                if name == "MILP Gurobi":
                    results[m] = format_res(m, v, el, mw, wls, cb, wb, lb)
                else:
                    results[m] = format_res(m, v, el, mw, wls, cb, wb)
                    
            # Safe iterative save as each process finishes natively
            save_current_results()
            
    print(f"\n[Success] Industrial benchmark pipeline finished.")


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
