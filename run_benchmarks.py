"""
Unified Benchmark Runner for CSLAP
===================================
Orchestrates all 5 methods across all synthetic dataset sizes,
captures metrics, and outputs a formatted LaTeX table with analysis.

Usage:
    python run_benchmarks.py
    python run_benchmarks.py --sizes 500 1000
    python run_benchmarks.py --quick          # fast smoke test
"""

import sys
import os
import time
import argparse
import numpy as np
from collections import defaultdict

# Add project paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "Data_Generators"))
sys.path.insert(0, os.path.join(BASE_DIR, "Baselines"))

# Load environment variables (makes sure GRB_LICENSE_FILE is picked up from .env)
from dotenv import load_dotenv
load_dotenv()

# Removed Hexaly license as we are switching exact methods to Gurobi.
# Gurobi license is managed via GRB_LICENSE_FILE environment variable.

from synthetic_data_zhang import generate_synthetic_data_zhang
from sa_correlated import read_data as sa_read_data, simulated_annealing_correlated
from ga_baseline import read_data as ga_read_data, genetic_algorithm
from heuristic_synthetic import (
    read_data as heur_read_data,
    heuristic_cslap,
)
from milp_gurobi_synthetic import read_data as milp_read_data, run_milp_gurobi
from cg_gurobi_synthetic import read_data as cg_read_data, column_generation_gurobi
from milp_synthetic import read_data as milp_hexaly_read_data, run_milp_hexaly
from cg_synthetic import read_data as cg_hexaly_read_data, column_generation_hexaly


import concurrent.futures
import traceback

# -
#  ERROR LOGGING
# -
def log_error(prefix, method, error_msg):
    log_file = os.path.join(BASE_DIR, "error_log.txt")
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a") as f:
        f.write(f"[{timestamp}] Dataset: {prefix} | Method: {method} | Error: {error_msg}\n")

# -
#  CONCURRENT WORKERS
# -
def do_sac(N, prefix, data_dir, tl, quick, num_orders, num_skus, num_stations):
    print(f"\n[{prefix}] SA-C Started")
    try:
        op, st, pr, pl = sa_read_data(prefix, data_dir)
        _, visits, elapsed, util_var, max_util, cap_broken, wl_broken = simulated_annealing_correlated(op, st, pr, pl, time_limit=tl, quick=quick)
        print(f"  [{prefix}] SA-C Done ({elapsed:.2f}s)")
        return {"visits": visits, "time": elapsed, "util_var": util_var, "max_util": max_util, "cap_broken": cap_broken, "wl_broken": wl_broken, "num_orders": num_orders, "num_skus": num_skus, "num_stations": num_stations}
    except Exception as e:
        print(f"  [{prefix}] SA-C failed: {e}")
        log_error(prefix, "SA-C", f"{e}\n{traceback.format_exc()}")
        return {"visits": "-", "time": "-", "util_var": "-", "max_util": "-", "cap_broken": "-", "wl_broken": "-", "num_orders": num_orders, "num_skus": num_skus, "num_stations": num_stations}

def do_ga(N, prefix, data_dir, tl, quick, num_orders, num_skus, num_stations):
    print(f"\n[{prefix}] GA Started")
    try:
        op, st, pr, pl = ga_read_data(prefix, data_dir)
        _, visits, elapsed, util_var, max_util, cap_broken, wl_broken = genetic_algorithm(op, st, pr, pl, time_limit=tl, quick=quick)
        print(f"  [{prefix}] GA Done ({elapsed:.2f}s)")
        return {"visits": visits, "time": elapsed, "util_var": util_var, "max_util": max_util, "cap_broken": cap_broken, "wl_broken": wl_broken, "num_orders": num_orders, "num_skus": num_skus, "num_stations": num_stations}
    except Exception as e:
        print(f"  [{prefix}] GA failed: {e}")
        log_error(prefix, "GA", f"{e}\n{traceback.format_exc()}")
        return {"visits": "-", "time": "-", "util_var": "-", "max_util": "-", "cap_broken": "-", "wl_broken": "-", "num_orders": num_orders, "num_skus": num_skus, "num_stations": num_stations}

def do_heur(N, prefix, data_dir, num_orders, num_skus, num_stations):
    print(f"\n[{prefix}] Heuristic Started")
    try:
        op, st, pr, pl, odf = heur_read_data(prefix, data_dir)
        heur_assignment, visits, elapsed, util_var, max_util, cap_broken, wl_broken = heuristic_cslap(op, st, pr, pl, odf)
        print(f"  [{prefix}] Heuristic Done ({elapsed:.2f}s)")
        return {"visits": visits, "time": elapsed, "util_var": util_var, "max_util": max_util, "cap_broken": cap_broken, "wl_broken": wl_broken, "num_orders": num_orders, "num_skus": num_skus, "num_stations": num_stations}, heur_assignment
    except Exception as e:
        print(f"  [{prefix}] Heuristic failed: {e}")
        log_error(prefix, "Heuristic", f"{e}\n{traceback.format_exc()}")
        return {"visits": "-", "time": "-", "util_var": "-", "max_util": "-", "cap_broken": "-", "wl_broken": "-", "num_orders": num_orders, "num_skus": num_skus, "num_stations": num_stations}, None

def do_milp_gurobi(N, prefix, data_dir, tl, heur_assignment, num_orders, num_skus, num_stations):
    print(f"\n[{prefix}] MILP Gurobi Started")
    try:
        op, st, pr, pl = milp_read_data(prefix, data_dir)
        milp_assignment, visits, elapsed, util_var, max_util, cap_broken, wl_broken, best_bound = run_milp_gurobi(
            op, st, pr, pl, time_limit=tl, warm_start_assignment=heur_assignment
        )
        print(f"  [{prefix}] MILP Gurobi Done ({elapsed:.2f}s)")
        res = {
            "visits": visits if visits is not None else "-",
            "time": elapsed,
            "util_var": util_var if util_var is not None else "-",
            "max_util": max_util if max_util is not None else "-",
            "cap_broken": cap_broken if cap_broken is not None else "-",
            "wl_broken": wl_broken if wl_broken is not None else "-",
            "num_orders": num_orders, "num_skus": num_skus, "num_stations": num_stations
        }
        return res, milp_assignment, best_bound
    except Exception as e:
        print(f"  [{prefix}] MILP Gurobi failed: {e}")
        log_error(prefix, "MILP Gurobi", f"{e}\n{traceback.format_exc()}")
        return {"visits": "-", "time": "-", "util_var": "-", "max_util": "-", "cap_broken": "-", "wl_broken": "-", "num_orders": num_orders, "num_skus": num_skus, "num_stations": num_stations}, None, None

def do_milp_hexaly(N, prefix, data_dir, tl, heur_assignment, num_orders, num_skus, num_stations):
    print(f"\n[{prefix}] MILP Hexaly Started")
    try:
        op, st, pr, pl = milp_hexaly_read_data(prefix, data_dir)
        milp_hexaly_assignment, visits, elapsed, util_var, max_util, cap_broken, wl_broken = run_milp_hexaly(
            op, st, pr, pl, time_limit=tl, warm_start_assignment=heur_assignment
        )
        print(f"  [{prefix}] MILP Hexaly Done ({elapsed:.2f}s)")
        res = {
            "visits": visits if visits is not None else "-",
            "time": elapsed,
            "util_var": util_var if util_var is not None else "-",
            "max_util": max_util if max_util is not None else "-",
            "cap_broken": cap_broken if cap_broken is not None else "-",
            "wl_broken": wl_broken if wl_broken is not None else "-",
            "num_orders": num_orders, "num_skus": num_skus, "num_stations": num_stations
        }
        return res, milp_hexaly_assignment
    except Exception as e:
        print(f"  [{prefix}] MILP Hexaly failed: {e}")
        log_error(prefix, "MILP Hexaly", f"{e}\n{traceback.format_exc()}")
        return {"visits": "-", "time": "-", "util_var": "-", "max_util": "-", "cap_broken": "-", "wl_broken": "-", "num_orders": num_orders, "num_skus": num_skus, "num_stations": num_stations}, None

def do_cg_gurobi(N, prefix, data_dir, tl, warm_start, num_orders, num_skus, num_stations):
    print(f"\n[{prefix}] CG Gurobi Started")
    try:
        op, st, pr, pl = cg_read_data(prefix, data_dir)
        _, visits, elapsed, util_var, max_util, cap_broken, wl_broken = column_generation_gurobi(
            op, st, pr, pl, time_limit=tl, warm_start_assignment=warm_start
        )
        print(f"  [{prefix}] CG Gurobi Done ({elapsed:.2f}s)")
        return {
            "visits": visits if visits is not None else "-", "time": elapsed,
            "util_var": util_var if util_var is not None else "-",
            "max_util": max_util if max_util is not None else "-",
            "cap_broken": cap_broken if cap_broken is not None else "-",
            "wl_broken": wl_broken if wl_broken is not None else "-",
            "num_orders": num_orders, "num_skus": num_skus, "num_stations": num_stations
        }
    except Exception as e:
        print(f"  [{prefix}] CG Gurobi failed: {e}")
        log_error(prefix, "CG Gurobi", f"{e}\n{traceback.format_exc()}")
        return {"visits": "-", "time": "-", "util_var": "-", "max_util": "-", "cap_broken": "-", "wl_broken": "-", "num_orders": num_orders, "num_skus": num_skus, "num_stations": num_stations}

def do_cg_hexaly(N, prefix, data_dir, tl, warm_start, num_orders, num_skus, num_stations):
    print(f"\n[{prefix}] CG Hexaly Started")
    try:
        op, st, pr, pl = cg_hexaly_read_data(prefix, data_dir)
        _, visits, elapsed, util_var, max_util, cap_broken, wl_broken = column_generation_hexaly(
            op, st, pr, pl, time_limit=tl, warm_start_assignment=warm_start
        )
        print(f"  [{prefix}] CG Hexaly Done ({elapsed:.2f}s)")
        return {
            "visits": visits if visits is not None else "-", "time": elapsed,
            "util_var": util_var if util_var is not None else "-",
            "max_util": max_util if max_util is not None else "-",
            "cap_broken": cap_broken if cap_broken is not None else "-",
            "wl_broken": wl_broken if wl_broken is not None else "-",
            "num_orders": num_orders, "num_skus": num_skus, "num_stations": num_stations
        }
    except Exception as e:
        print(f"  [{prefix}] CG Hexaly failed: {e}")
        log_error(prefix, "CG Hexaly", f"{e}\n{traceback.format_exc()}")
        return {"visits": "-", "time": "-", "util_var": "-", "max_util": "-", "cap_broken": "-", "wl_broken": "-", "num_orders": num_orders, "num_skus": num_skus, "num_stations": num_stations}

# -
#  RUNNER
# -
def run_all_benchmarks(
    sizes=None,
    data_dir="synthetic_datasets",
    quick=False,
    regenerate=False,
    time_limit=72000,
):
    if sizes is None:
        sizes = [500, 1000, 2000, 5000]

    results = {}  # {N: {method: {visits, time, wl_var}}}

    # - Phase 1: Generate data -
    print("=" * 70)
    print("PHASE 1: Synthetic Data Generation (Zhang et al. 2019)")
    print("=" * 70)
    for N in sizes:
        prefix = f"syn_{N}sku"
        orders_path = os.path.join(data_dir, f"{prefix}_orders.csv")
        if regenerate or not os.path.exists(orders_path):
            generate_synthetic_data_zhang(
                num_skus=N, alpha=0.7, seed=42, output_dir=data_dir
            )
        else:
            print(f"[Exists] {prefix} data already generated, skipping.\n")

    # - Phase 2-3: Run Methods -
    for N in sizes:
        prefix = f"syn_{N}sku"
        results[N] = {}
        print("=" * 70)
        print(f"BENCHMARKING: N = {N} SKUs ({prefix})")
        print("=" * 70)

        # Pre-read data to get dimensions once
        try:
            op_dim, st_dim, pr_dim, pl_dim, odf_dim = heur_read_data(prefix, data_dir)
            num_orders = len(op_dim)
            num_skus = len(pr_dim)
            num_stations = len(st_dim)
        except Exception:
            num_orders, num_skus, num_stations = "-", "-", "-"

        # Launch independent tasks with ThreadPoolExecutor
        print("\n[Phase A] Launching SA-C, GA, and Heuristic concurrently...")
        tl = time_limit if not quick else min(60, time_limit)
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            future_sac = executor.submit(do_sac, N, prefix, data_dir, tl, quick, num_orders, num_skus, num_stations)
            future_ga = executor.submit(do_ga, N, prefix, data_dir, tl, quick, num_orders, num_skus, num_stations)
            future_heur = executor.submit(do_heur, N, prefix, data_dir, num_orders, num_skus, num_stations)

            # Heuristic assignment is needed for Phase B
            res_heur, heur_assignment = future_heur.result()
            results[N]["Heuristic"] = res_heur

            # Phase B: MILPs
            print("\n[Phase B] Heuristic finished. Launching exact MILPs concurrently...")
            future_milp_g = executor.submit(do_milp_gurobi, N, prefix, data_dir, tl, heur_assignment, num_orders, num_skus, num_stations)
            future_milp_h = executor.submit(do_milp_hexaly, N, prefix, data_dir, tl, heur_assignment, num_orders, num_skus, num_stations)

            res_milp_g, milp_g_assignment, best_bound = future_milp_g.result()
            res_milp_h, milp_h_assignment = future_milp_h.result()
            
            # --- Fallback: If MILP failed to find improvement, return Heuristic ---
            if res_milp_g["visits"] == "-":
                print(f"  [{prefix}] MILP Gurobi failed to find solution, falling back to heuristic warm start.")
                res_milp_g["visits"] = res_heur["visits"]
                res_milp_g["util_var"] = res_heur["util_var"]
                res_milp_g["max_util"] = res_heur["max_util"]
                res_milp_g["cap_broken"] = res_heur["cap_broken"]
                res_milp_g["wl_broken"] = res_heur["wl_broken"]
                milp_g_assignment = heur_assignment
                log_error(prefix, "MILP Gurobi", "Fell back to Heuristic warm start due to no solution found within limit.")

            if res_milp_h["visits"] == "-":
                print(f"  [{prefix}] MILP Hexaly failed to find solution, falling back to heuristic warm start.")
                res_milp_h["visits"] = res_heur["visits"]
                res_milp_h["util_var"] = res_heur["util_var"]
                res_milp_h["max_util"] = res_heur["max_util"]
                res_milp_h["cap_broken"] = res_heur["cap_broken"]
                res_milp_h["wl_broken"] = res_heur["wl_broken"]
                milp_h_assignment = heur_assignment
                log_error(prefix, "MILP Hexaly", "Fell back to Heuristic warm start due to no solution found within limit.")

            global_lb = best_bound if best_bound is not None and best_bound > 0 else None
            
            results[N]["MILP Gurobi"] = res_milp_g
            results[N]["MILP Hexaly"] = res_milp_h

            # Phase C: CGs
            print("\n[Phase C] MILPs finished. Launching CG Solvers concurrently...")
            warm_start_g = milp_g_assignment if milp_g_assignment is not None else heur_assignment
            warm_start_h = milp_h_assignment if milp_h_assignment is not None else heur_assignment

            future_cg_g = executor.submit(do_cg_gurobi, N, prefix, data_dir, tl, warm_start_g, num_orders, num_skus, num_stations)
            future_cg_h = executor.submit(do_cg_hexaly, N, prefix, data_dir, tl, warm_start_h, num_orders, num_skus, num_stations)

            results[N]["CG Gurobi"] = future_cg_g.result()
            results[N]["CG Hexaly"] = future_cg_h.result()

            # Wait for Phase A non-blocking tasks to finish safely
            results[N]["SA-C"] = future_sac.result()
            results[N]["GA"] = future_ga.result()

        # --- Optimality Gap Calculation ---
        for method, metrics in results[N].items():
            v = metrics.get("visits", "-")
            if v != "-" and v is not None and global_lb is not None and global_lb > 0:
                try:
                    gap = ((float(v) - global_lb) / global_lb)
                    metrics["gap_pct"] = round(gap, 2)
                except Exception:
                    metrics["gap_pct"] = "-"
            else:
                metrics["gap_pct"] = "-"

        # Save results for this dataset to a CSV file
        output_csv = os.path.join(BASE_DIR, f"results_{prefix}.csv")
        try:
            import pandas as pd
            df = pd.DataFrame(results[N]).T
            df.index.name = "Method"
            # Reorder columns for readability if possible
            expected_cols = ["visits", "gap_pct", "time", "util_var", "max_util", "cap_broken", "wl_broken", "num_orders", "num_skus", "num_stations"]
            existing_cols = [c for c in expected_cols if c in df.columns]
            df = df[existing_cols]
            
            # Convert and round columns
            for col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='ignore')
                
            if "time" in df.columns:
                df["time"] = df["time"].apply(lambda x: round(float(x), 2) if isinstance(x, (int, float)) and not pd.isna(x) else x)
                
            for col in df.select_dtypes(include=[np.number]).columns:
                if col != "time":
                    df[col] = df[col].apply(lambda x: round(float(x), 5) if isinstance(x, (int, float)) and not pd.isna(x) else x)
            
            df.to_csv(output_csv)
            print(f"  [Results for {prefix} saved to {output_csv} with Gaps]")
        except Exception as e:
            print(f"  [Failed to save CSV for {prefix}: {e}]")

    return results


# -
#  MAIN
# -
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="CSLAP Benchmark Runner (Gurobi exact solvers)"
    )
    parser.add_argument(
        "--sizes", nargs="+", type=int, default=[500, 1000, 2000, 5000]
    )
    parser.add_argument("--data_dir", type=str, default="synthetic_datasets")
    parser.add_argument("--quick", action="store_true", help="Fast smoke test")
    parser.add_argument("--regenerate", action="store_true", help="Regenerate data")
    parser.add_argument("--time_limit", type=int, default=72000, help="Global time limit in seconds for all non-heuristic methods")
    args = parser.parse_args()

    results = run_all_benchmarks(
        sizes=args.sizes,
        data_dir=args.data_dir,
        quick=args.quick,
        regenerate=args.regenerate,
        time_limit=args.time_limit,
    )

    print("\n" + "=" * 70)
    print("ALL BENCHMARKS COMPLETED.")
    print("Granular results have been saved to CSV files (e.g., results_syn_500sku.csv).")
    print("=" * 70)
