"""
SA-C: Simulated Annealing with Correlated Interchange for CSLAP
Based on Kim & Smith (2012) and Zhang et al. (2019).

Features:
- COI (Cube-per-Order Index) initialization
- Correlated SKU pair list L(k) sorted by co-occurrence C(i,j)
- Correlated interchange neighborhood operator
- Dispersion tie-breaking secondary objective
- Boltzmann cooling schedule
"""

import numpy as np
import pandas as pd
import math
import random
import argparse
import os
import time
from collections import defaultdict


# ----------------------------------------------------------------
#  DATA LOADING
# ----------------------------------------------------------------
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

    # Product pick-line counts
    prod_lines = orders_df.groupby("PRODUCT").size().to_dict()

    # Orders -> list of products
    order_prods = orders_df.groupby("ORDER")["PRODUCT"].apply(list).to_dict()

    # Station list
    stations = stations_df.to_dict(orient="records")

    # Product list
    products = products_df["PRODUCT_ID"].apply(lambda x: f"PROD_{x}").tolist()

    return order_prods, stations, products, prod_lines


# ----------------------------------------------------------------
#  CO-OCCURRENCE MATRIX  &  CORRELATED PAIR LIST
# ----------------------------------------------------------------
def build_cooccurrence(order_prods, products):
    """Build symmetric co-occurrence counts C(i,j)."""
    cooc = defaultdict(int)
    for o, prods in order_prods.items():
        unique = list(set(prods))
        for i in range(len(unique)):
            for j in range(i + 1, len(unique)):
                a, b = unique[i], unique[j]
                key = (min(a, b), max(a, b))
                cooc[key] += 1
    return cooc


def build_correlated_list(cooc, K=10):
    """
    Sort all pairs by descending C(i,j) and partition into K groups.
    Returns list of groups, each a list of (p1, p2) tuples.
    """
    sorted_pairs = sorted(cooc.items(), key=lambda x: -x[1])
    pairs = [pair for pair, _ in sorted_pairs]
    if not pairs:
        return [[]]
    chunk_size = max(1, len(pairs) // K)
    groups = []
    for i in range(0, len(pairs), chunk_size):
        groups.append(pairs[i: i + chunk_size])
    return groups


# ----------------------------------------------------------------
#  COI INITIALIZATION
# ----------------------------------------------------------------
def coi_initialization(products, stations, prod_lines):
    """
    Cube-per-Order Index: sort products by descending pick frequency.
    Assign most-picked products to station 1, next batch to station 2, etc.
    """
    # Sort products by descending frequency
    freq_sorted = sorted(products, key=lambda p: prod_lines.get(p, 0), reverse=True)

    state = {}
    station_caps = {s["STATION_ID"]: s["CAPACITY"] for s in stations}
    station_ids = sorted(station_caps.keys())
    remaining = {s: station_caps[s] for s in station_ids}

    idx = 0
    for p in freq_sorted:
        # Find next station with capacity
        while idx < len(station_ids) and remaining[station_ids[idx]] <= 0:
            idx += 1
        if idx >= len(station_ids):
            # Wrap around (shouldn't happen if capacities sum >= N)
            idx = 0
        sid = station_ids[idx]
        state[p] = sid
        remaining[sid] -= 1

    return state


# ----------------------------------------------------------------
#  OBJECTIVE FUNCTION
# ----------------------------------------------------------------
def calculate_objective(state, order_prods, stations, prod_lines,
                        cooc=None, w_penalty=1000, w_disp=0.01):
    """
    Primary:   total station visits (sum of unique stations per order)
    Secondary: dispersion penalty (tie-breaker) - measures how spread
               correlated items are across zones.
    Penalty:   capacity / workload violations.
    """
    # --- Primary: station visits ---
    total_visits = 0
    for o, prods in order_prods.items():
        visited = set()
        for p in prods:
            if p in state:
                visited.add(state[p])
        total_visits += len(visited)

    # --- Constraint violations ---
    station_counts = defaultdict(int)
    station_workload = defaultdict(float)
    speeds = {s["STATION_ID"]: s["SPEED"] for s in stations}
    for p, sid in state.items():
        station_counts[sid] += 1
        station_workload[sid] += prod_lines.get(p, 0) / speeds.get(sid, 1.0) if speeds.get(sid, 1.0) > 0 else 0

    penalty = 0.0
    for s in stations:
        sid = s["STATION_ID"]
        cap = s["CAPACITY"]
        time_cap = s["TIME_CAPACITY"]
        
        if station_counts[sid] > cap:
            penalty += w_penalty * (station_counts[sid] - cap)
            
        wl = station_workload.get(sid, 0.0)
        if wl > time_cap:
            penalty += w_penalty * (wl - time_cap)

    # --- Secondary: dispersion of correlated items ---
    dispersion = 0.0
    if cooc:
        for (p1, p2), cnt in cooc.items():
            if p1 in state and p2 in state:
                if state[p1] != state[p2]:
                    dispersion += cnt  # penalise splits weighted by co-occurrence

    energy = total_visits + penalty + w_disp * dispersion
    return energy, total_visits


# ----------------------------------------------------------------
#  CORRELATED INTERCHANGE NEIGHBOR
# ----------------------------------------------------------------
def correlated_neighbor(state, correlated_groups, products, rng):
    """
    Select random group k from correlated list L(k).
    Pick a random pair from that group and swap their assignments.
    Strictly uses the correlated group unless the list is entirely empty.
    """
    new_state = state.copy()

    # Strictly use correlated swaps as per Kim & Smith (2012)
    if correlated_groups:
        k = rng.randint(0, len(correlated_groups))
        group = correlated_groups[k]
        if group:
            pair = group[rng.randint(0, len(group))]
            p1, p2 = pair
            if p1 in new_state and p2 in new_state:
                new_state[p1], new_state[p2] = new_state[p2], new_state[p1]
                return new_state

    # Fallback: purely random swap only if correlated groups are empty/malformed
    p1, p2 = rng.choice(products, size=2, replace=False)
    if p1 in new_state and p2 in new_state:
        new_state[p1], new_state[p2] = new_state[p2], new_state[p1]

    return new_state


# ----------------------------------------------------------------
#  SA-C MAIN LOOP
# ----------------------------------------------------------------
def simulated_annealing_correlated(
    order_prods, stations, products, prod_lines,
    T0=800, T_min=1, cooling_rate=0.95, sa_iter_factor=2,
    K_groups=10, time_limit=72000, quick=False,
    warm_start_assignment=None
):
    """
    SA with Correlated Interchange.

    Parameters
    ----------
    T0 : float           Initial temperature
    T_min : float         Terminal temperature (set to 1 as per Zhang et al. 2019)
    cooling_rate : float  Geometric cooling alpha
    sa_iter_factor : int  Inner loop = N * sa_iter_factor
    K_groups : int        Number of correlated pair groups
    time_limit : int      Maximum execution time in seconds
    quick : bool          Reduced iterations for smoke testing
    """
    rng = np.random.RandomState(42)
    N = len(products)

    # Build co-occurrence and correlated list
    print("  Building co-occurrence matrix...")
    cooc = build_cooccurrence(order_prods, products)
    correlated_groups = build_correlated_list(cooc, K=K_groups)
    print(f"  Co-occurrence pairs: {len(cooc)}, Groups: {len(correlated_groups)}")

    if warm_start_assignment is not None:
        print("  Using supplied warm start assignment...")
        state = warm_start_assignment.copy()
    else:
        # COI initialization
        print("  COI initialization...")
        state = coi_initialization(products, stations, prod_lines)

    current_energy, current_visits = calculate_objective(
        state, order_prods, stations, prod_lines, cooc
    )
    best_state = state.copy()
    best_energy = current_energy
    best_visits = current_visits

    T = T0
    inner_iters = min(N * sa_iter_factor, 1000)
    if quick:
        inner_iters = min(inner_iters, 200)
        T_min = max(T_min, T0 * (cooling_rate ** 20))  # max 20 temp steps

    total_iters = 0
    start_time = time.time()

    print(f"  SA-C starting: T0={T0}, T_min={T_min}, alpha={cooling_rate}, "
          f"inner={inner_iters}")

    while T > T_min:
        elapsed = time.time() - start_time
        if elapsed > time_limit:
            print(f"  SA-C: Time limit reached at T={T:.1f}")
            break

        for _ in range(inner_iters):
            neighbor = correlated_neighbor(state, correlated_groups, products, rng)
            neighbor_energy, neighbor_visits = calculate_objective(
                neighbor, order_prods, stations, prod_lines, cooc
            )

            delta = neighbor_energy - current_energy
            if delta < 0 or rng.random() < math.exp(-delta / T):
                state = neighbor
                current_energy = neighbor_energy
                current_visits = neighbor_visits

                if current_energy < best_energy:
                    best_energy = current_energy
                    best_visits = current_visits
                    best_state = state.copy()

            total_iters += 1

        T *= cooling_rate

        elapsed = time.time() - start_time
        print(f"    T={T:.1f} | Energy={current_energy:.1f} | "
              f"Best Visits={best_visits} | Iter={total_iters} | "
              f"Time={elapsed:.1f}s")

    elapsed = time.time() - start_time

    # --- Workload distribution tracking ---
    station_counts = defaultdict(int)
    station_actions = defaultdict(float)
    speeds = {s["STATION_ID"]: s["SPEED"] for s in stations}
    
    for p, sid in best_state.items():
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

    if not quick:
        print(f"  SA-C Done: Best Visits={best_visits}, "
              f"Time={elapsed:.2f}s, WL_Std={workload_std_dev:.4f}, Max_WL={max_workload:.4f}")
              
    return best_state, best_visits, elapsed, max_workload, workload_std_dev, cap_broken, wl_broken


# ----------------------------------------------------------------
#  CLI
# ----------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SA-C for CSLAP")
    parser.add_argument("--prefix", type=str, required=True)
    parser.add_argument("--dir", type=str, default="synthetic_datasets")
    parser.add_argument("--time", type=int, default=72000)
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args()

    print(f"Running SA-C on {args.prefix}...")
    order_prods, stations, products, prod_lines = read_data(args.prefix, args.dir)
    simulated_annealing_correlated(
        order_prods, stations, products, prod_lines, time_limit=args.time, quick=args.quick
    )
