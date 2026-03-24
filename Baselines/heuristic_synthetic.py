"""
Heuristic for CSLAP (Synthetic Data Adapter)
Lightweight adaptation of the greedy product clustering approach.

Steps:
1. Pair generation from multi-item orders
2. Community formation (greedy clustering)
3. Station assignment (majority-preference)
"""

import numpy as np
import pandas as pd
import os
import time
import argparse
from collections import defaultdict
from itertools import combinations


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
    return order_prods, stations, products, prod_lines, orders_df


def heuristic_cslap(order_prods, stations, products, prod_lines, orders_df):
    """
    Greedy product clustering and station assignment.
    Auto-scales parameters to dataset size.
    """
    start_time = time.time()
    N = len(products)

    # --- Auto-scale parameters ---
    MIN_FREQ_PREPROC = max(2, N // 100)
    MIN_FREQ = max(2, N // 50)
    RATIO_TO_KEEP = 0.1
    MNOPPC = max(5, min(15, N // 20))  # community size limit

    # --- Step 1: Preprocessing & Pair Generation ---
    # Filter products by minimum frequency
    P_star = {p for p, freq in prod_lines.items() if freq >= MIN_FREQ_PREPROC}

    # Generate co-occurrence pairs from multi-item orders
    pair_counts = defaultdict(int)
    for o, prods in order_prods.items():
        filtered = [p for p in set(prods) if p in P_star]
        if len(filtered) < 2:
            continue
        for p1, p2 in combinations(sorted(filtered), 2):
            pair_counts[(p1, p2)] += 1

    # Filter by MIN_FREQ
    pair_counts = {k: v for k, v in pair_counts.items() if v >= MIN_FREQ}

    # Filter by RATIO_TO_KEEP
    filtered_pairs = {}
    for (p1, p2), cnt in pair_counts.items():
        freq1 = prod_lines.get(p1, 1)
        ratio = cnt / freq1
        if ratio >= RATIO_TO_KEEP:
            filtered_pairs[(p1, p2)] = cnt

    # Sort descending
    sorted_pairs = sorted(filtered_pairs.items(), key=lambda x: -x[1])

    # --- Step 2: Community Formation ---
    communities = []
    assigned = set()

    for (pa, pb), cnt in sorted_pairs:
        if pa in assigned or pb in assigned:
            continue

        community = {pa, pb}
        assigned.add(pa)
        assigned.add(pb)

        # Expand community
        while len(community) < MNOPPC:
            best_candidate = None
            best_score = -1

            for (p1, p2), c in sorted_pairs:
                if p1 in assigned and p2 in assigned:
                    continue
                if p1 in community and p2 not in assigned:
                    candidate = p2
                elif p2 in community and p1 not in assigned:
                    candidate = p1
                else:
                    continue

                # Score: total co-occurrence with community members
                score = sum(
                    filtered_pairs.get(tuple(sorted([candidate, m])), 0)
                    for m in community
                )
                if score > best_score:
                    best_score = score
                    best_candidate = candidate

            if best_candidate is None or best_score <= 0:
                break

            community.add(best_candidate)
            assigned.add(best_candidate)

        communities.append(community)

    # --- Step 3: Post-processing (unassigned products) ---
    unassigned = [p for p in products if p not in assigned]
    # Group unassigned into communities of MNOPPC
    for i in range(0, len(unassigned), MNOPPC):
        communities.append(set(unassigned[i: i + MNOPPC]))

    # --- Step 4: Station Assignment ---
    # Sort communities by total frequency (most impactful first)
    communities.sort(
        key=lambda c: sum(prod_lines.get(p, 0) for p in c), reverse=True
    )

    station_caps = {s["STATION_ID"]: s["CAPACITY"] for s in stations}
    remaining_cap = dict(station_caps)
    assignment = {}

    # Compute historical preference (from original STATION in orders_df)
    prod_station_pref = defaultdict(lambda: defaultdict(int))
    for _, row in orders_df.iterrows():
        prod_station_pref[row["PRODUCT"]][row["STATION"]] += 1

    for community in communities:
        # Aggregate station preference for the community
        station_scores = defaultdict(int)
        for p in community:
            for sid, cnt in prod_station_pref[p].items():
                station_scores[sid] += cnt

        # Sort stations by preference
        preferred = sorted(station_scores.keys(), key=lambda s: -station_scores[s])
        # Add remaining stations
        all_stations = preferred + [
            s for s in remaining_cap if s not in preferred
        ]

        placed = False
        for sid in all_stations:
            if remaining_cap.get(sid, 0) >= len(community):
                for p in community:
                    assignment[p] = sid
                remaining_cap[sid] -= len(community)
                placed = True
                break

        if not placed:
            # Split across stations
            items_left = list(community)
            for sid in all_stations:
                while items_left and remaining_cap.get(sid, 0) > 0:
                    p = items_left.pop()
                    assignment[p] = sid
                    remaining_cap[sid] -= 1

    elapsed = time.time() - start_time

    # --- Evaluate ---
    total_visits = 0
    for o, prods in order_prods.items():
        visited = set()
        for p in prods:
            if p in assignment:
                visited.add(assignment[p])
        total_visits += len(visited)

    # --- Workload distribution tracking ---
    station_counts = defaultdict(int)
    station_actions = defaultdict(float)
    speeds = {s["STATION_ID"]: s["SPEED"] for s in stations}
    
    for p, sid in assignment.items():
        station_counts[sid] += 1
        qty = prod_lines.get(p, 0)
        station_actions[sid] += qty / speeds.get(sid, 1.0) if speeds.get(sid, 1.0) > 0 else 0
        
    station_ids = [s["STATION_ID"] for s in stations]
    station_caps = {s["STATION_ID"]: s["CAPACITY"] for s in stations}
    time_caps = {s["STATION_ID"]: s["TIME_CAPACITY"] for s in stations}
    
    cap_broken = sum(1 for sid in station_ids if station_counts[sid] > station_caps[sid])
    wl_broken = sum(1 for sid in station_ids if station_actions[sid] > time_caps[sid])

    actual_workloads = [station_actions[sid] for sid in station_ids]
    max_workload = float(np.max(actual_workloads)) if actual_workloads else 0.0
    workload_std_dev = float(np.std(actual_workloads)) if actual_workloads else 0.0

    print(f"  Heuristic Done: Visits={total_visits}, "
          f"Time={elapsed:.2f}s, WL_Std={workload_std_dev:.4f}, Max_WL={max_workload:.4f}")

    return assignment, total_visits, elapsed, max_workload, workload_std_dev, cap_broken, wl_broken


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Heuristic CSLAP (synthetic)")
    parser.add_argument("--prefix", type=str, required=True)
    parser.add_argument("--dir", type=str, default="synthetic_datasets")
    args = parser.parse_args()

    print(f"Running Heuristic on {args.prefix}...")
    order_prods, stations, products, prod_lines, orders_df = read_data(
        args.prefix, args.dir
    )
    heuristic_cslap(order_prods, stations, products, prod_lines, orders_df)
