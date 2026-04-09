"""
GA Baseline: Standard Genetic Algorithm for CSLAP
Implements PMX (Partially Mapped Crossover) preserving correlated SKU grouping.

Features:
- Feasible random initialization respecting station capacities
- PMX crossover adapted for station-assignment representation
- Swap mutation
- Tournament selection
- Dual objective: station visits + dispersion tie-breaking
"""

import numpy as np
import pandas as pd
import math
import random
import argparse
import os
import time
from collections import defaultdict


# -
#  DATA LOADING  (shared interface)
# -
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


# -
#  CO-OCCURRENCE
# -
def build_cooccurrence(order_prods):
    cooc = defaultdict(int)
    for o, prods in order_prods.items():
        unique = list(set(prods))
        for i in range(len(unique)):
            for j in range(i + 1, len(unique)):
                a, b = unique[i], unique[j]
                key = (min(a, b), max(a, b))
                cooc[key] += 1
    return cooc


# -
#  FITNESS
# -
def fitness(chromosome, products, order_prods, stations, prod_lines,
            cooc, w_penalty=1000, w_disp=0.01):
    """
    Evaluate a chromosome (product-station mapping).
    Returns (energy, visits) where energy includes penalties and dispersion.
    """
    # Build state dict
    state = {products[i]: chromosome[i] for i in range(len(products))}

    # Station visits
    total_visits = 0
    for o, prods in order_prods.items():
        visited = set()
        for p in prods:
            if p in state:
                visited.add(state[p])
        total_visits += len(visited)

    # Capacity / workload violations
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

    # Dispersion
    dispersion = 0.0
    for (p1, p2), cnt in cooc.items():
        if p1 in state and p2 in state:
            if state[p1] != state[p2]:
                dispersion += cnt

    energy = total_visits + penalty + w_disp * dispersion
    return energy, total_visits


# -
#  INITIALIZATION
# -
def random_feasible(products, stations, rng):
    """Create a random feasible chromosome respecting capacity constraints."""
    N = len(products)
    slots = []
    for s in stations:
        slots.extend([s["STATION_ID"]] * s["CAPACITY"])
    # Trim to exactly N slots
    slots = slots[:N]
    if len(slots) < N:
        # Fill remaining with last station
        last = stations[-1]["STATION_ID"]
        slots.extend([last] * (N - len(slots)))
    rng.shuffle(slots)
    return np.array(slots)


# -
#  PMX CROSSOVER (adapted for assignment)
# -
def pmx_crossover(parent1, parent2, rng):
    """
    Partially Mapped Crossover adapted for station-assignment vectors.
    Selects a segment and swaps station assignments, then repairs
    capacity violations.
    """
    N = len(parent1)
    child1 = parent1.copy()
    child2 = parent2.copy()

    # Select crossover segment
    cx1 = rng.randint(0, N)
    cx2 = rng.randint(0, N)
    if cx1 > cx2:
        cx1, cx2 = cx2, cx1
    cx2 = min(cx2, cx1 + N // 4)  # Limit segment size

    # Swap the segment
    child1[cx1:cx2] = parent2[cx1:cx2]
    child2[cx1:cx2] = parent1[cx1:cx2]

    return child1, child2


def repair_capacity(chromosome, stations):
    """Repair a chromosome to respect station capacity constraints."""
    cap = {s["STATION_ID"]: s["CAPACITY"] for s in stations}
    station_ids = sorted(cap.keys())

    # Count current assignments
    counts = defaultdict(int)
    for sid in chromosome:
        counts[sid] += 1

    # Find overfull and underfull stations
    overfull = {s: counts[s] - cap[s] for s in station_ids if counts[s] > cap[s]}
    underfull = {s: cap[s] - counts[s] for s in station_ids if counts[s] < cap[s]}

    if not overfull:
        return chromosome

    # Indices of products in overfull stations
    indices = list(range(len(chromosome)))
    np.random.shuffle(indices)

    for idx in indices:
        sid = chromosome[idx]
        if sid in overfull and overfull[sid] > 0:
            # Move to an underfull station
            for target, space in underfull.items():
                if space > 0:
                    chromosome[idx] = target
                    overfull[sid] -= 1
                    underfull[target] -= 1
                    if overfull[sid] == 0:
                        del overfull[sid]
                    if underfull[target] == 0:
                        del underfull[target]
                    break
        if not overfull:
            break

    return chromosome


# -
#  MUTATION
# -
def swap_mutation(chromosome, rng):
    """Swap two random products' station assignments."""
    child = chromosome.copy()
    i, j = rng.choice(len(child), size=2, replace=False)
    child[i], child[j] = child[j], child[i]
    return child


# -
#  TOURNAMENT SELECTION
# -
def tournament_select(population, fitnesses, rng, k=2):
    """Binary tournament selection."""
    candidates = rng.choice(len(population), size=k, replace=False)
    best = min(candidates, key=lambda c: fitnesses[c])
    return population[best].copy()


# -
#  GA MAIN LOOP
# -
def genetic_algorithm(
    order_prods, stations, products, prod_lines,
    pop_size=50, generations=200, cx_rate=0.8, mut_rate=0.1,
    time_limit=72000, quick=False,
    warm_start_assignment=None
):
    rng = np.random.RandomState(42)
    N = len(products)

    if quick:
        pop_size = min(pop_size, 20)
        generations = min(generations, 10)

    print(f"  GA starting: pop={pop_size}, gens={generations}, "
          f"cx={cx_rate}, mut={mut_rate}")

    # Build co-occurrence
    print("  Building co-occurrence matrix...")
    cooc = build_cooccurrence(order_prods)

    # Initialize population
    print("  Initializing population...")
    population = [random_feasible(products, stations, rng) for _ in range(pop_size)]

    if warm_start_assignment is not None:
        print("  Injecting warm start assignment into population[0]...")
        # Chromosome is an array of station IDs parallel to the products list
        ws_chrom = np.array([warm_start_assignment.get(p, population[0][i]) for i, p in enumerate(products)])
        population[0] = ws_chrom

    # Evaluate initial fitness
    fit_vals = []
    visit_vals = []
    for chrom in population:
        e, v = fitness(chrom, products, order_prods, stations, prod_lines, cooc)
        fit_vals.append(e)
        visit_vals.append(v)

    best_idx = int(np.argmin(fit_vals))
    best_chrom = population[best_idx].copy()
    best_energy = fit_vals[best_idx]
    best_visits = visit_vals[best_idx]

    start_time = time.time()

    for gen in range(generations):
        
        elapsed = time.time() - start_time
        if elapsed > time_limit:
            print(f"  GA: Time limit reached at generation {gen}")
            break

        new_pop = []
        new_fit = []
        new_vis = []

        # Elitism: keep best
        new_pop.append(best_chrom.copy())
        new_fit.append(best_energy)
        new_vis.append(best_visits)

        while len(new_pop) < pop_size:
            # Selection
            p1 = tournament_select(population, fit_vals, rng)
            p2 = tournament_select(population, fit_vals, rng)

            # Crossover
            if rng.random() < cx_rate:
                c1, c2 = pmx_crossover(p1, p2, rng)
                c1 = repair_capacity(c1, stations)
                c2 = repair_capacity(c2, stations)
            else:
                c1, c2 = p1.copy(), p2.copy()

            # Mutation
            if rng.random() < mut_rate:
                c1 = swap_mutation(c1, rng)
            if rng.random() < mut_rate:
                c2 = swap_mutation(c2, rng)

            for child in [c1, c2]:
                if len(new_pop) < pop_size:
                    e, v = fitness(
                        child, products, order_prods, stations, prod_lines, cooc
                    )
                    new_pop.append(child)
                    new_fit.append(e)
                    new_vis.append(v)

        population = new_pop
        fit_vals = new_fit
        visit_vals = new_vis

        gen_best_idx = int(np.argmin(fit_vals))
        if fit_vals[gen_best_idx] < best_energy:
            best_energy = fit_vals[gen_best_idx]
            best_visits = visit_vals[gen_best_idx]
            best_chrom = population[gen_best_idx].copy()

        if (gen + 1) % max(1, generations // 10) == 0:
            elapsed = time.time() - start_time
            print(f"    Gen {gen+1}/{generations} | Best Energy={best_energy:.1f} | "
                  f"Best Visits={best_visits} | Time={elapsed:.1f}s")

    elapsed = time.time() - start_time

    # --- Workload distribution tracking ---
    state = {products[i]: best_chrom[i] for i in range(N)}
    
    station_counts = defaultdict(int)
    station_actions = defaultdict(float)
    speeds = {s["STATION_ID"]: s["SPEED"] for s in stations}
    
    for p, sid in state.items():
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
        print(f"  GA Done: Best Visits={best_visits}, "
              f"Time={elapsed:.2f}s, WL_Std={workload_std_dev:.4f}, Max_WL={max_workload:.4f}")

    return state, best_visits, elapsed, max_workload, workload_std_dev, cap_broken, wl_broken


# -
#  CLI
# -
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GA baseline for CSLAP")
    parser.add_argument("--prefix", type=str, required=True)
    parser.add_argument("--dir", type=str, default="synthetic_datasets")
    parser.add_argument("--time", type=int, default=72000)
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args()

    print(f"Running GA on {args.prefix}...")
    order_prods, stations, products, prod_lines = read_data(args.prefix, args.dir)
    genetic_algorithm(order_prods, stations, products, prod_lines, time_limit=args.time, quick=args.quick)
