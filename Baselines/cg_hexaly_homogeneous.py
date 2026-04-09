import pandas as pd
import numpy as np
import os
import time
import random
import argparse
import math
import heapq
import itertools
from collections import defaultdict
from itertools import combinations
import copy

from scipy.optimize import linprog
import scipy.sparse as sp

import hexaly.optimizer as hexaly
hexaly.HxVersion.license_content = "LICENSE_KEY = ED3A-2222-89F4B124-770D-60A55B936308D780-9506208B36204986-9B3E-E289-C66E"

def read_data(prefix, data_dir):
    orders_df = pd.read_csv(os.path.join(data_dir, f"{prefix}_orders.csv"), sep=";")
    stations_df = pd.read_csv(os.path.join(data_dir, f"{prefix}_stations.csv"), sep=";")
    products_df = pd.read_csv(os.path.join(data_dir, f"{prefix}_products.csv"), sep=";")
    prod_lines = orders_df.groupby("PRODUCT").size().to_dict()
    order_prods = orders_df.groupby("ORDER")["PRODUCT"].apply(list).to_dict()
    stations = stations_df.to_dict(orient="records")
    products = products_df["PRODUCT_ID"].apply(lambda x: f"PROD_{x}").tolist()
    return order_prods, stations, products, prod_lines

def build_instance(order_prods, products, capacities):
    if not capacities:
        K = 20
    else:
        K = list(capacities.values())[0]
    print(f"Capacity K: {K}")

    item_to_idx = {p: i for i, p in enumerate(products)}
    idx_to_item = {i: p for p, i in item_to_idx.items()}

    S = list(order_prods.keys())
    order_to_idx = {o: s_idx for s_idx, o in enumerate(S)}
    idx_to_order = {s_idx: o for o, s_idx in order_to_idx.items()}
    S_indices = list(order_to_idx.values())

    I_s = {}
    S_i = {i: [] for i in range(len(products))}

    for o, prods in order_prods.items():
        s_idx = order_to_idx[o]
        I_s[s_idx] = []
        for p in prods:
            if p in item_to_idx:
                i_idx = item_to_idx[p]
                I_s[s_idx].append(i_idx)
                S_i[i_idx].append(s_idx)

    return {
        'K': K,
        'I': list(idx_to_item.keys()),
        'S': S_indices,
        'I_s': {s: set(items) for s, items in I_s.items()},
        'S_i': {i: set(samples) for i, samples in S_i.items()},
        'idx_to_item': idx_to_item,
        'idx_to_order': idx_to_order,
        'item_to_idx': item_to_idx
    }

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
        print(f"    St {sid}: {st_count[sid]}/{capacities[sid]} items, WL: {st_workload[sid]:.1f}/{time_caps[sid]}")

    return assigned

def compute_h_mappings(H, I, S, I_s):
    H_i = {i: [] for i in I}
    for h_index, h_set in enumerate(H):
        for i in h_set:
            if i in H_i:
                H_i[i].append(h_index)

    H_s = {s: [] for s in S}
    for s in S:
        h_indices = set()
        for i in I_s[s]:
            h_indices.update(H_i[i])
        H_s[s] = list(h_indices)

    return H_i, H_s

def generate_initial_h_smart(S, I, k, I_s):
    added_patterns = set()

    def add_pattern(pattern):
        p_set = frozenset(pattern)
        if p_set not in added_patterns:
            added_patterns.add(p_set)

    for i_item in I:
        add_pattern({i_item})

    for s in S:
        s_list = sorted(list(I_s[s]))

        for chunk_start in range(0, len(s_list), k):
            chunk = s_list[chunk_start:chunk_start + k]
            if 1 <= len(chunk) <= k:
                add_pattern(chunk)

    return [list(x) for x in added_patterns]

def is_integer(x_vals, tol=1e-6):
    for val in x_vals:
        if tol < val < 1 - tol:
            return False
    return True

def solve_rmp(H, instance, H_i, H_s):
    N_vars = len(H) + 1
    P_idx = len(H)
    
    c = np.zeros(N_vars)
    c[P_idx] = 1.0
    
    A_eq_rows = []
    A_eq_cols = []
    A_eq_vals = []
    b_eq = np.ones(len(instance['I']))
    
    for row_idx, i in enumerate(instance['I']):
        for j in H_i[i]:
            A_eq_rows.append(row_idx)
            A_eq_cols.append(j)
            A_eq_vals.append(1.0)
            
    if len(A_eq_vals) == 0:
        return None, None, None, None
        
    A_eq = sp.coo_matrix((A_eq_vals, (A_eq_rows, A_eq_cols)), shape=(len(instance['I']), N_vars))
    
    A_ub_rows = []
    A_ub_cols = []
    A_ub_vals = []
    b_ub = np.zeros(len(instance['S']))
    
    for row_idx, s in enumerate(instance['S']):
        for j in H_s[s]:
            A_ub_rows.append(row_idx)
            A_ub_cols.append(j)
            A_ub_vals.append(1.0)
        A_ub_rows.append(row_idx)
        A_ub_cols.append(P_idx)
        A_ub_vals.append(-1.0)
        
    if len(A_ub_vals) == 0:
        return None, None, None, None
        
    A_ub = sp.coo_matrix((A_ub_vals, (A_ub_rows, A_ub_cols)), shape=(len(instance['S']), N_vars))
    
    # bounds
    bounds = (0, None)
    
    # We use scipy interior point or highs
    res = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method='highs')
    
    if not res.success:
        return None, None, None, None
        
    P_val = res.fun
    x_vals = res.x[:-1]
    
    duals_alpha = {i: res.eqlin.marginals[idx] for idx, i in enumerate(instance['I'])}
    duals_beta = {s: res.ineqlin.marginals[idx] for idx, s in enumerate(instance['S'])}
    
    return P_val, x_vals, duals_alpha, duals_beta

def solve_pricing_problem_hexaly(instance, constraints, duals_alpha, duals_beta):
    with hexaly.HexalyOptimizer() as optimizer:
        model = optimizer.model
        optimizer.param.verbosity = 0
        optimizer.param.time_limit = 5
        
        z = {i: model.bool() for i in instance['I']}
        
        relevant_samples = set()
        for i in instance['I']:
            relevant_samples.update(instance['S_i'][i])
            
        w = {s: model.bool() for s in relevant_samples}
        
        # size limit
        model.constraint(model.sum(z[i] for i in instance['I']) <= instance['K'])
        
        # link constraints
        for i in instance['I']:
            for s in instance['S_i'][i]:
                model.constraint(w[s] >= z[i])
                
        # branch and price tree constraints
        if constraints:
            for c in constraints:
                if c[0] == 'join':
                    i, j = c[1]
                    model.constraint(z[i] == z[j])
                elif c[0] == 'disjoint':
                    i, j = c[1]
                    model.constraint(z[i] + z[j] <= 1)
                    
        # Objective: Maximize \sum duals_alpha * z + \sum duals_beta * w
        obj_expr = model.sum(duals_alpha[i] * z[i] for i in instance['I']) + \
                   model.sum(duals_beta[s] * w[s] for s in relevant_samples)
        
        model.maximize(obj_expr)
        model.close()
        optimizer.solve()
        
        if optimizer.solution.status != hexaly.HxSolutionStatus.OPTIMAL and \
           optimizer.solution.status != hexaly.HxSolutionStatus.FEASIBLE:
            return 0, None
            
        obj_val = optimizer.solution.get_value(model.objectives[0])
        
        if obj_val <= 1e-4:
            return 0, None
            
        selected_items = {i for i in instance['I'] if optimizer.solution.get_value(z[i]) == 1}
        return obj_val, selected_items


def compute_join_groups(previous_constraints):
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]

    def union(x, y):
        parent.setdefault(x, x)
        parent.setdefault(y, y)
        parent[find(x)] = find(y)

    for c in previous_constraints:
        if c[0] == 'join':
            union(c[1][0], c[1][1])

    groups = defaultdict(set)
    for x in parent:
        groups[find(x)].add(x)

    return groups


def get_join_groups(constraints):
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        parent.setdefault(x, x)
        parent.setdefault(y, y)
        parent[find(x)] = find(y)

    for c_type, (u, v) in constraints:
        if c_type == 'join':
            union(u, v)

    groups = defaultdict(set)
    for x in list(parent.keys()):
        groups[find(x)].add(x)

    def get_group(item):
        if item not in parent:
            return frozenset({item})
        return frozenset(groups[find(item)])

    return get_group


def generate_left_h(H, a, b, K, previous_constraints):
    get_group = get_join_groups(previous_constraints)

    group_a = get_group(a)
    group_b = get_group(b)
    merged = group_a | group_b

    if len(merged) > K:
        return None

    temp_constraints = previous_constraints + [('join', (a, b))]
    get_group_new = get_join_groups(temp_constraints)

    H_new = set()

    for h in H:
        h_set = frozenset(h)

        touched_groups = {}
        for item in h_set:
            g = get_group_new(item)
            rep = min(g)
            touched_groups[rep] = g

        new_h = set()
        for rep, group in touched_groups.items():
            new_h |= group

        if len(new_h) <= K:
            H_new.add(frozenset(new_h))
        else:
            for rep, group in touched_groups.items():
                if len(group) <= K:
                    H_new.add(frozenset(group))

    H_new.add(frozenset(merged))
    result = [list(h) for h in H_new]
    return result

def generate_right_h(H, a, b, previous_constraints):
    temp_constraints = previous_constraints + [('disjoint', (a, b))]
    get_group = get_join_groups(previous_constraints)

    group_a = get_group(a)
    group_b = get_group(b)

    if group_a & group_b:
        return None

    H_new = set()

    for h in H:
        h_set = frozenset(h)

        has_a_group = bool(h_set & group_a)
        has_b_group = bool(h_set & group_b)

        if not (has_a_group and has_b_group):
            H_new.add(h_set)
        else:
            h_without_b = h_set - group_b
            if h_without_b:
                H_new.add(frozenset(h_without_b))

            h_without_a = h_set - group_a
            if h_without_a:
                H_new.add(frozenset(h_without_a))

    result = [list(h) for h in H_new]
    return result


def simple_prune_H(H, x_vals):
    pruned_H = []
    for h_idx, h in enumerate(H):
        if x_vals[h_idx] > 1e-6:
            pruned_H.append(h)
    return pruned_H


def column_generation(instance, H, iterations=1500, constraints=None):
    rmp_time = 0
    pricing_time = 0
    adding_time = 0

    begin_column = time.time()
    iteration = 0
    
    rmp_obj = float('inf')
    x_vals = None

    for iteration in range(iterations):
        start = time.time()
        H_i, H_s = compute_h_mappings(H, instance['I'], instance['S'], instance['I_s'])
        P_val, x, duals_alpha, duals_beta = solve_rmp(H, instance, H_i, H_s)
        rmp_time += time.time() - start

        if P_val is None:
            print(f"      [CG] Iteration {iteration}: RMP is intrinsically infeasible.")
            return None, None, None, None, 0, float('inf'), H, 0, {}

        start = time.time()
        pricing_obj, new_h = solve_pricing_problem_hexaly(instance, constraints, duals_alpha, duals_beta)
        pricing_time += time.time() - start

        if iteration % 10 == 0:
            print(f"      [CG] Iteration {iteration:>3} | RMP Obj (P): {P_val:.6f} | Max Reduced Cost (Pricing): {pricing_obj if pricing_obj else 0.0:.6f} | Total Patterns (H): {len(H)}")

        if pricing_obj is None or pricing_obj <= 1e-4:
            rmp_obj = P_val
            x_vals = x
            print(f"      [CG] Optimal continuous solution reached at iteration {iteration}. Final Obj: {rmp_obj:.6f}")
            break

        start = time.time()
        H.append(new_h)
        adding_time += time.time() - start

    end_column = time.time() - begin_column
    # updating_time is 0
    return rmp_time, 0, pricing_time, adding_time, end_column, rmp_obj, H, iteration, x_vals

def select_pair_to_branch_on(x_vals, H, strategy='most_fractional', previous_constraints=None):
    already_constrained = set()
    if previous_constraints:
        groups = compute_join_groups(previous_constraints)
        disjoint_pairs = {frozenset(c[1]) for c in previous_constraints if c[0] == 'disjoint'}

        for members in groups.values():
            for a, b in combinations(members, 2):
                already_constrained.add(frozenset((a, b)))
        already_constrained.update(disjoint_pairs)

    scores = defaultdict(float)
    for h_idx, h in enumerate(H):
        x_val = x_vals[h_idx]
        if x_val <= 1e-6:
            continue
        items_in_h = list(h)
        for a in range(len(items_in_h)):
            for b in range(a + 1, len(items_in_h)):
                i, j = items_in_h[a], items_in_h[b]
                if frozenset((i, j)) not in already_constrained:
                    scores[(i, j)] += x_val

    if not scores:
        return None

    if strategy == 'most_fractional':
        return min(scores, key=lambda pair: abs(scores[pair] - 0.5))
    elif strategy == 'max_score':
        return max(scores, key=scores.get)
    elif strategy == 'min_score':
        return min(scores, key=scores.get)
    return None

class Node:
    def __init__(self, bound, H, constraint, depth):
        self.bound = bound
        self.H = H
        self.constraint = constraint
        self.depth = depth

class SolutionNode(Node):
    def __init__(self, bound, H, constraint, results, depth):
        super().__init__(bound, H, constraint, depth=depth)
        self.results = results


def evaluate_total_visits(instance, active_patterns_h):
    total_visits = 0
    for s_idx in instance['S']:
        visited = set()
        s_items = instance['I_s'][s_idx]
        for p_idx, pattern_items in enumerate(active_patterns_h):
            if any(item in pattern_items for item in s_items):
                visited.add(p_idx)
        total_visits += len(visited)
    return total_visits

def evaluate_max_visits(instance, active_patterns_h):
    max_visits = 0
    for s_idx in instance['S']:
        visits = 0
        s_items = instance['I_s'][s_idx]
        for pattern_items in active_patterns_h:
            if any(item in pattern_items for item in s_items):
                visits += 1
        if visits > max_visits:
            max_visits = visits
    return max_visits


def evaluate_station_workloads(instance, active_patterns_h, prod_lines):
    workloads = []
    for pattern_items in active_patterns_h:
        w = 0.0
        for i_idx in pattern_items:
            p_name = instance['idx_to_item'][i_idx]
            w += prod_lines.get(p_name, 0)
        workloads.append(w)
    
    if not workloads:
        return 0.0, 0.0
    return float(np.max(workloads)), float(np.std(workloads))

counter = itertools.count()
join_tree = []
disjoint_tree = []
best_tree = []

def push(node, type=1):
    depth = node.depth if hasattr(node, 'depth') else 0
    priority = -depth 
    if type==1:
        heapq.heappush(join_tree, (priority, next(counter), node))
    elif type == 2:
        heapq.heappush(disjoint_tree, (-priority, next(counter), node))
    else:
        heapq.heappush(best_tree, (node.bound, next(counter), node))

def pop():
    if join_tree:
        _, _, node = heapq.heappop(join_tree)
    elif disjoint_tree:
        _, _, node = heapq.heappop(disjoint_tree)
    else:
        _, _, node = heapq.heappop(best_tree)
    return node

def tree_empty():
    return not join_tree and not best_tree and not disjoint_tree

def solve_final_imp_hexaly(instance, H):
    """
    If the time limit ends, we must use Hexaly to find an integer solution 
    among the currently established columns if the root hasn't naturally integers.
    """
    H_i, H_s = compute_h_mappings(H, instance['I'], instance['S'], instance['I_s'])
    
    with hexaly.HexalyOptimizer() as optimizer:
        model = optimizer.model
        optimizer.param.verbosity = 0
        optimizer.param.time_limit = 10
        
        y = [model.bool() for _ in range(len(H))]
        P = model.int(0, 5000)
        
        # Partition
        for i in instance['I']:
            model.constraint(model.sum(y[j] for j in H_i[i]) == 1)
            
        for s in instance['S']:
            model.constraint(model.sum(y[h] for h in H_s[s]) <= P)
            
        model.minimize(P)
        model.close()
        optimizer.solve()
        
        if optimizer.solution.status != hexaly.HxSolutionStatus.OPTIMAL and \
           optimizer.solution.status != hexaly.HxSolutionStatus.FEASIBLE:
            return None, None
            
        P_val = optimizer.solution.get_value(model.objectives[0])
        x_vals = [optimizer.solution.get_value(y[j]) for j in range(len(H))]
        return P_val, x_vals


def start_branch_and_price(instance, prod_lines, assigned, time_limit):
    global join_tree, disjoint_tree, best_tree, counter
    join_tree, disjoint_tree, best_tree = [], [], []
    counter = itertools.count()

    H = generate_initial_h_smart(instance['S'], instance['I'], instance['K'], instance['I_s'])
    
    # Translate LPT warmstart assignment into Master columns (patterns)
    print("  CG [Warmstart]: Translating LPT heuristic assignment into exact patterns...")
    station_to_items = defaultdict(list)
    for prod, sid in assigned.items():
        if prod in instance['item_to_idx']: # Ensure product exists in instance indices
            station_to_items[sid].append(instance['item_to_idx'][prod])
            
    existing_sets = {frozenset(h) for h in H}
    warmstart_patterns_added = 0
    
    warmstart_h_list = []
    
    for items in station_to_items.values():
        if items and len(items) <= instance['K']:
            items_set = frozenset(items)
            warmstart_h_list.append(list(items_set))
            if items_set not in existing_sets:
                H.append(list(items_set))
                existing_sets.add(items_set)
                warmstart_patterns_added += 1
                
    warmstart_p_val = evaluate_max_visits(instance, warmstart_h_list)
    print(f"  CG [Warmstart]: Initial Feasible Integer Objective (Max Visits P) = {warmstart_p_val}")
    print(f"  CG [Warmstart]: Successfully injected {warmstart_patterns_added} new heuristic columns. Total H patterns: {len(H)}")

    previous_constraints = []

    print("  CG (Hexaly+Scipy): Starting Root Node Evaluation...")
    root_results = column_generation(instance, H, constraints=previous_constraints)
    if root_results[5] == float('inf'):
        print("  CG (Hexaly+Scipy): Root node is infeasible.")
        return None, None, None, None, None, None, None
        
    print(f"  CG: Root node evaluation finished. Continuous Bound: {root_results[5]:.6f}")
        
    H = simple_prune_H(H, root_results[8])

    root = Node(bound=root_results[5], H=H, constraint=previous_constraints, depth=0)
    root.results = root_results
    push(root, type=3)

    best_solution = SolutionNode(bound=warmstart_p_val, H=warmstart_h_list, constraint=[], results=None, depth=0)
    best_lower_bound = math.ceil(root_results[5])
    start_tree_exploration = time.time()

    nodes_processed = 0

    def get_global_lower_bound():
        # If the queues are empty, the LB has met the UB
        if tree_empty():
            return best_solution.bound 
            
        lowest_bound = float('inf')
        
        # Scan all waiting nodes in the 3 queues
        for q in [join_tree, disjoint_tree, best_tree]:
            for item in q:
                node = item[2] # The node object is the 3rd element in the tuple
                if node.bound < lowest_bound:
                    lowest_bound = node.bound
                    
        # Because station visits must be integers, we can safely round up the continuous LB!
        return math.ceil(lowest_bound - 1e-6)

    while not tree_empty():
        
        elapsed = time.time() - start_tree_exploration
        if elapsed > time_limit:
            print(f"  CG: Time limit ({time_limit}s) reached during Branch and Price!")
            break

        node = pop()
        nodes_processed += 1

        # Calculate Dynamic Bounds
        current_global_lb = get_global_lower_bound()
        current_ub = best_solution.bound
        
        # Calculate Gap (Protect against infinity at the start)
        if current_ub == float('inf'):
            gap_str = "Infinity"
        else:
            gap_pct = ((current_ub - current_global_lb) / current_ub) * 100
            gap_str = f"{gap_pct:.2f}%"

        print(f"\n  [B&P] Subproblem #{nodes_processed} | Depth: {node.depth}")
        print(f"    -> Floor (Global LB): {current_global_lb:.2f}")
        print(f"    -> Ceiling (Incumbent UB): {current_ub:.2f}")
        print(f"    -> Optimality Gap: {gap_str}")

        if math.ceil(node.bound) >= best_solution.bound:
            print(f"    -> [Prune] Parent Bound {math.ceil(node.bound):.2f} >= Incumbent {best_solution.bound:.2f}. Pruning before CG.")
            continue

        results = column_generation(instance, node.H, constraints=node.constraint)
        node.bound = results[5]

        if results[5] == float('inf'):
            print(f"    -> [Prune] Node formulation is INFEASIBLE.")
            continue

        print(f"    -> [CG Resolved] Node exact bound returned: {node.bound:.6f}")

        if math.ceil(node.bound - 1e-6) >= best_solution.bound:
            print(f"    -> [Prune] Node Bound {math.ceil(node.bound - 1e-6):.2f} >= Incumbent {best_solution.bound:.2f}. Pruning after CG.")
            continue

        if is_integer(results[8]):
            print(f"    -> [NEW INCUMBENT] Found an exact integer solution at depth {node.depth}! Old bound {best_solution.bound:.2f} -> New bound {results[5]:.2f}")
            best_solution = SolutionNode(
                bound=results[5], H=node.H,
                constraint=node.constraint.copy(), results=results, depth=node.depth
            )
            if best_solution.bound <= best_lower_bound + 1e-4:
                print("  [B&P] Optimal integer solution provably found. Best bound equals root lower bound!")
                break
            continue

        pair = select_pair_to_branch_on(results[8], results[6], previous_constraints=node.constraint)

        if pair is None:
            print("    -> [Warning] Tree could not find branching pair on non-integers. (Fractional state undifferentiable).")
            continue

        print(f"    -> [Branching] Branching linearly on item pair (JOIN / DISJOINT): {pair}")
        left_constraint  = node.constraint.copy() + [('join', pair)]
        right_constraint = node.constraint.copy() + [('disjoint', pair)]
        current_depth = node.depth + 1

        H_left = generate_left_h(copy.deepcopy(node.H), pair[0], pair[1], instance['K'], left_constraint)
        if H_left:
            left_node = Node(bound=node.bound, H=H_left, constraint=left_constraint, depth=current_depth)
            push(left_node, type=1)

        H_right = generate_right_h(node.H.copy(), pair[0], pair[1], right_constraint)
        if H_right:
            right_node = Node(bound=node.bound, H=H_right, constraint=right_constraint, depth=current_depth)
            if node.bound <= (best_solution.bound - 1) + 1e-6:
                push(right_node, type=2)
            else:
                push(right_node, type=3)

    bp_time = time.time() - start_tree_exploration
    print(f"  CG: Branch-and-Price completed. Nodes processed: {nodes_processed}")

    active_patterns = []
    
    if best_solution.bound != float('inf') and best_solution.results is None:
        print("  CG: Tree finished/timed out. Best solution was the initial Heuristic Warmstart!")
        active_patterns = best_solution.H
    elif best_solution.results is not None:
        x_vals = best_solution.results[8]
        H_final = best_solution.results[6]
        for h_idx, h_set in enumerate(H_final):
            if x_vals[h_idx] > 0.5:
                active_patterns.append(h_set)
    else:
        print("  CG: No feasible integer solution naturally found in BP, and no warmstart provided. Running Final IMP constraint set resolver...")
        # Resolve via Hexaly final IMP
        imp_p, imp_x = solve_final_imp_hexaly(instance, H)
        if imp_p is not None:
            for h_idx, h_set in enumerate(H):
                if imp_x[h_idx] > 0.5:
                    active_patterns.append(h_set)
        else:
            return None, None, bp_time, None, None, None, None

    best_assignment = {}
    for p_idx, p_items in enumerate(active_patterns):
        station_id = p_idx 
        for i_item in p_items:
            best_assignment[instance['idx_to_item'][i_item]] = station_id
            
    total_visits = evaluate_total_visits(instance, active_patterns)
    max_wl, std_wl = evaluate_station_workloads(instance, active_patterns, prod_lines)
    
    cap_broken = sum(1 for p in active_patterns if len(p) > instance['K'])
    wl_broken = 0 
    
    return best_assignment, total_visits, bp_time, max_wl, std_wl, cap_broken, wl_broken


import builtins

def setup_logger(prefix):
    log_filename = f"cg_hexaly_run_{prefix}.log"
    log_file = open(log_filename, "w", encoding="utf-8")
    original_print = builtins.print
    def custom_print(*args, **kwargs):
        sep = kwargs.get('sep', ' ')
        end = kwargs.get('end', '\\n')
        message = sep.join(map(str, args)) + end
        original_print(*args, **kwargs)
        try:
            log_file.write(message)
            log_file.flush()
        except:
            pass
    builtins.print = custom_print
    return log_filename

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CG CSLAP (Homogeneous Set Partitioning, Hexaly)")
    parser.add_argument("--prefix", type=str, required=True)
    parser.add_argument("--dir",    type=str, default="synthetic_datasets")
    parser.add_argument("--time",   type=int, default=72000)
    args = parser.parse_args()

    log_filename = setup_logger(args.prefix)
    print(f"Log initialized: {log_filename}")
    
    print(f"Running Homogeneous CG on {args.prefix}...")
    order_prods, stations, products, prod_lines = read_data(args.prefix, args.dir)
    
    capacities = {s["STATION_ID"]: s["CAPACITY"] for s in stations}
    instance = build_instance(order_prods, products, capacities)
    
    # Generate warm start using Longest Processing Time logic
    print("  Generating Feasible Start (LPT Heuristic)...")
    assigned_warmstart = generate_feasible_start(products, stations, prod_lines)
    
    out = start_branch_and_price(instance, prod_lines, assigned_warmstart, time_limit=args.time)
    
    if out[0] is not None:
        best_assignment, total_visits, elapsed, max_workload, workload_std_dev, cap_broken, wl_broken = out
        print(f"  CG Done: Visits={total_visits}, Time={elapsed:.2f}s, "
              f"WL_Std={workload_std_dev:.4f}, Max_WL={max_workload:.4f}, "
              f"Cap_Broken={cap_broken}, WL_Broken={wl_broken}")

        # Save to benchmark CSV
        csv_file = f"results_{args.prefix}.csv"
        file_exists = os.path.isfile(csv_file)
        
        with open(csv_file, 'a') as f:
            if not file_exists:
                f.write("Method,visits,gap_pct,lb_gurobi,time,time_limit,max_workload,avg_workload_assign,avg_workload_max,workload_std_dev,cap_broken,wl_broken,num_orders,num_skus,num_stations\\n")
            
            num_orders = len(instance['S'])
            num_skus = len(instance['I'])
            num_stations = "" # Explicit station count isn't modeled directly in homogeneous patterns
            
            f.write(f"CG Hexaly Homogeneous Exact,{total_visits},,,{elapsed:.2f},{args.time},{max_workload},,,{workload_std_dev},{cap_broken},{wl_broken},{num_orders},{num_skus},{num_stations}\\n")
        print(f"  Saved benchmark metrics to {csv_file}")
    else:
        print(f"  CG Failed: Time={out[2]:.2f}s")
