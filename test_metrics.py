import pandas as pd
import numpy as np
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "Baselines"))

from data_loader_industrial import load_industrial_data
from collections import defaultdict

def evaluate_full_metrics(partial_assignment, static_assignment, op_full, st_full, pl_full):
    if partial_assignment is None:
        return "-", "-", "-", "-", "-"
        
    final_assignment = partial_assignment.copy()
    final_assignment.update(static_assignment)
    
    total_visits = 0
    for o, prods in op_full.items():
        visited = set()
        for p in prods:
            if p in final_assignment:
                visited.add(final_assignment[p])
        total_visits += len(visited)
        
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
    workload_std_dev = float(np.std(actual_workloads)) if actual_workloads else 0.0
    
    return total_visits, max_workload, workload_std_dev, cap_broken, wl_broken

filepath="Heuristic_Connex_Set_Project/data/BERNER_ORDER_LINES_09-12.csv"
data = load_industrial_data(filepath)

print(f"Number of orders in op_full: {len(data['op_full'])}")
print(f"Number of products in pl_full: {len(data['pl_full'])}")
print(f"Number of static assigned products: {len(data['static_assignment'])}")
print(f"Number of solver products: {len(data['pr_solver'])}")

visits_ws, max_wl_ws, wl_std_ws, cap_b_ws, wl_b_ws = evaluate_full_metrics(
    data['warm_start_assignment'], data['static_assignment'], data['op_full'], data['st_full'], data['pl_full']
)
print("--- FULL EVALUATION METRICS ON ALL ORDERS ---")
print(f"Total Visits: {visits_ws}")
print(f"Max Workload: {max_wl_ws:.2f}")
print(f"Workload Std Dev: {wl_std_ws:.2f}")
print(f"Capacity Broken: {cap_b_ws}")
print(f"Workload Limit Broken: {wl_b_ws}")
