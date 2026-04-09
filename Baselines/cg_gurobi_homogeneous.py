import pandas as pd
import numpy as np
import gurobipy as gp
from gurobipy import GRB
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
    # P represents upper bound on Max visits initially.
    # We will compute K from capacities. (Assuming homogeneous, picking the first station's capacity).
    if not capacities:
        K = 20 # fallback
    else:
        K = list(capacities.values())[0]

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
        'P': 1000, # A safe big-M equivalent value for start, though RMP sets P to infinity inherently
        'I': list(idx_to_item.keys()),
        'S': S_indices,
        'I_s': {s: set(items) for s, items in I_s.items()},
        'S_i': {i: set(samples) for i, samples in S_i.items()},
        'idx_to_item': idx_to_item,
        'idx_to_order': idx_to_order
    }

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

def generate_initial_h(I):
    return [[i] for i in I]

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

        if k >= 2:
            if len(s_list) <= 50:
                for combo in combinations(s_list, min(k, len(s_list))):
                    add_pattern(combo)
            else:
                random.seed(42)
                sampled = random.sample(s_list, min(30, len(s_list)))
                for combo in combinations(sampled, min(k, len(sampled))):
                    add_pattern(combo)

    return [list(x) for x in added_patterns]

def is_integer(x, tol=1e-6):
    for x_h in x.values():
        if tol < x_h.X < 1 - tol:
            return False
    return True

def setup_rmp(model, instance, H, H_i, H_s):
    x = {}
    for j in range(len(H)):
        x[j] = model.addVar(lb=0.0, ub=1.0, vtype=GRB.CONTINUOUS, name=f'x_{j}')
    P = model.addVar(lb=0.0, name='P')

    constraints_alpha = {}
    for i in instance['I']:
        constraints_alpha[i] = model.addConstr(gp.quicksum(x[j] for j in H_i[i]) == 1, name=f'cover_item_{i}')

    constraints_beta = {}
    for s in instance['S']:
        # To minimize P bounds the maximum times ANY order is split across patterns
        constraints_beta[s] = model.addConstr(gp.quicksum(x[h] for h in H_s[s]) <= P, name=f'price_order_{s}')

    model.setObjective(1.0 * P, GRB.MINIMIZE)

    return x, P, constraints_alpha, constraints_beta

def add_new_pattern_to_rmp(model, H, new_h, x, constraints_alpha, constraints_beta, instance):
    new_h_index = len(H)
    H.append(new_h)
    
    col = gp.Column()
    covered_samples = set()
    for i in new_h:
        col.addTerms(1.0, constraints_alpha[i])
        covered_samples.update(instance['S_i'][i])

    for s in covered_samples:
        col.addTerms(1.0, constraints_beta[s])

    x[new_h_index] = model.addVar(lb=0.0, ub=1.0, vtype=GRB.CONTINUOUS, name=f'x_{new_h_index}', column=col)

def setup_pricing_problem(model, instance, constraints=None):
    model.setParam('TimeLimit', 60)
    model.setParam('Threads', 1)
    model.setParam('MIPGap', 0.01)
    model.setParam('MIPFocus', 1)

    z = {i: model.addVar(vtype=GRB.BINARY, name=f"z_{i}") for i in instance['I']}

    relevant_samples = set()
    for i in instance['I']:
        relevant_samples.update(instance['S_i'][i])

    w = {s: model.addVar(vtype=GRB.BINARY, name=f"w_{s}") for s in relevant_samples}

    model.addConstr(gp.quicksum(z[i] for i in instance['I']) <= instance['K'], name="size_limit")

    for i in instance['I']:
        for s in instance['S_i'][i]:
            model.addConstr(w[s] >= z[i], name=f"link_{s}_{i}")

    if constraints:
        for c in constraints:
            if c[0] == 'join':
                i, j = c[1]
                model.addConstr(z[i] == z[j], name=f"join_{i}_{j}")
            elif c[0] == 'disjoint':
                i, j = c[1]
                model.addConstr(z[i] + z[j] <= 1, name=f"disjoint_{i}_{j}")

    return z, w

def update_pricing_problem(model, instance, duals_alpha, duals_beta, z, w):
    # duals_alpha holds Pi for "== 1" cover constraint (could be anything)
    # duals_beta holds Pi for "<= P", so it will be <= 0 in Gurobi (dual variable for <= in min problem is <=0)
    obj_expr = gp.quicksum(duals_alpha[i] * z[i] for i in instance['I']) + gp.quicksum(duals_beta[s] * w[s] for s in w)
    model.setObjective(obj_expr, GRB.MAXIMIZE)

def solve_rmp(model, constraints_alpha, constraints_beta, instance):
    model.optimize()

    if model.Status != GRB.OPTIMAL:
        return None, None, None

    duals_alpha = {i: constraints_alpha[i].Pi for i in instance['I']}
    duals_beta  = {s: constraints_beta[s].Pi for s in instance['S']}

    return model.ObjVal, duals_alpha, duals_beta

def solve_pricing_problem(model, z):
    model.optimize()
    if model.Status not in [GRB.OPTIMAL, GRB.TIME_LIMIT] or model.SolCount == 0:
        return 0, None
    if model.ObjVal <= 1e-6:
        return 0, None
    selected_items = {i for i, var in z.items() if var.X > 0.5}
    return model.ObjVal, selected_items

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

def simple_prune_H(H, x):
    pruned_H = []
    for h_idx, h in enumerate(H):
        if x[h_idx].X > 1e-6:
            pruned_H.append(h)
    return pruned_H

def set_models_parameters(rmp_model, pricing_model):
    rmp_model.setParam('Method', 2)
    rmp_model.setParam('Presolve', 1)
    rmp_model.setParam('OutputFlag', 0)
    pricing_model.setParam('OutputFlag', 0)

def column_generation(instance, H, iterations=1500, constraints=None):
    H_i, H_s = compute_h_mappings(H, instance['I'], instance['S'], instance['I_s'])

    env = gp.Env(empty=True)
    env.setParam("OutputFlag", 0)
    env.start()

    model_rmp = gp.Model("RMP", env=env)
    x, P, constraints_alpha, constraints_beta = setup_rmp(model_rmp, instance, H, H_i, H_s)

    model_pricing = gp.Model("Pricing", env=env)
    z, w = setup_pricing_problem(model_pricing, instance, constraints)

    set_models_parameters(model_rmp, model_pricing)

    rmp_time = 0
    updating_time = 0
    pricing_time = 0
    adding_time = 0

    begin_column = time.time()
    iteration = 0
    
    rmp_obj = float('inf')

    for iteration in range(iterations):
        start = time.time()
        rmp_obj, duals_alpha, duals_beta = solve_rmp(model_rmp, constraints_alpha, constraints_beta, instance)
        rmp_time += time.time() - start

        if rmp_obj is None:
            return None, None, None, None, 0, float('inf'), H, 0, {}

        start = time.time()
        update_pricing_problem(model_pricing, instance, duals_alpha, duals_beta, z, w)
        updating_time += time.time() - start
        
        start = time.time()
        pricing_obj, new_h = solve_pricing_problem(model_pricing, z)
        pricing_time += time.time() - start

        if pricing_obj is None or pricing_obj <= 1e-6:
            break

        start = time.time()
        add_new_pattern_to_rmp(model_rmp, H, new_h, x, constraints_alpha, constraints_beta, instance)
        adding_time += time.time() - start

    end_column = time.time() - begin_column
    return rmp_time, updating_time, pricing_time, adding_time, end_column, rmp_obj, H, iteration, x

def select_pair_to_branch_on(x, H, strategy='most_fractional', previous_constraints=None):
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
        x_val = x[h_idx].X
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
    # active_patterns_h is a list of sets of items
    total_visits = 0
    for s_idx in instance['S']:
        visited = set()
        s_items = instance['I_s'][s_idx]
        for p_idx, pattern_items in enumerate(active_patterns_h):
            if any(item in pattern_items for item in s_items):
                visited.add(p_idx)
        total_visits += len(visited)
    return total_visits

def evaluate_station_workloads(instance, active_patterns_h, prod_lines):
    # Assuming any pattern goes to any identical station
    workloads = []
    for pattern_items in active_patterns_h:
        w = 0.0
        for i_idx in pattern_items:
            p_name = instance['idx_to_item'][i_idx]
            w += prod_lines.get(p_name, 0)
        # Assuming speed is 1 for workload calculations (time = items basically)
        # OR we could just count the frequency limits. Since we dropped time_capacity,
        # Max workload could just be the max sum of prod frequencies per pattern.
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

def print_result(results):
    print("  Root Column Generation results:")
    print(f"  RMP solving time: {results[0]:.2f}s, Pricing time: {results[2]:.2f}s, CG total time: {results[4]:.2f}s")
    print(f"  Root CG Iterations: {results[7]}")
    print(f"  Root Bound (Min-Max P) : {results[5]:.4f}")

def start_branch_and_price(instance, prod_lines, time_limit):
    global join_tree, disjoint_tree, best_tree, counter
    
    join_tree = []
    disjoint_tree = []
    best_tree = []
    counter = itertools.count()

    H = generate_initial_h_smart(instance['S'], instance['I'], instance['K'], instance['I_s'])
    previous_constraints = []

    print("  CG: Starting Root Node Evaluation...")
    root_results = column_generation(instance, H, constraints=previous_constraints)
    if root_results[5] == float('inf'):
        print("  CG: Root node is infeasible.")
        return None, None, None, None, None
        
    H = simple_prune_H(H, root_results[8])

    root = Node(bound=root_results[5], H=H, constraint=previous_constraints, depth=0)
    root.results = root_results
    push(root, type=3)
    print_result(root_results)

    best_solution = SolutionNode(bound=float('inf'), H=[], constraint=[], results=None, depth=0)
    best_lower_bound = math.ceil(root_results[5])
    start_tree_exploration = time.time()

    nodes_processed = 0

    while not tree_empty():
        
        # Verify global timeout
        elapsed = time.time() - start_tree_exploration
        if elapsed > time_limit:
            print(f"  CG: Time limit ({time_limit}s) reached during Branch and Price!")
            break

        node = pop()
        nodes_processed += 1

        if math.ceil(node.bound) >= best_solution.bound:
            continue

        results = column_generation(instance, node.H, constraints=node.constraint)
        node.bound = results[5]

        if results[5] == float('inf'):
            continue

        if math.ceil(node.bound - 1e-6) >= best_solution.bound:
            continue

        if is_integer(results[8]):
            # print(f"  Integer solution found! P={results[5]:.4f}")
            best_solution = SolutionNode(
                bound=results[5], H=node.H,
                constraint=node.constraint.copy(), results=results, depth=node.depth
            )
            if best_solution.bound <= best_lower_bound + 1e-4:
                print("  CG: Optimal integer solution found early, terminating.")
                break
            continue

        pair = select_pair_to_branch_on(results[8], results[6], previous_constraints=node.constraint)

        if pair is None:
            continue

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
    print(f"  CG: Branch-and-Price completed in {bp_time:.2f} seconds. Nodes processed: {nodes_processed}")

    if best_solution.results is not None:
        # Extract best objective
        x = best_solution.results[8]
        H_final = best_solution.results[6]
        active_patterns = []
        best_assignment = {}
        for h_idx, h_set in enumerate(H_final):
            if x[h_idx].X > 0.5:
                active_patterns.append(h_set)
                
        # Remap assignments back
        # The identical stations: we basically iterate active patterns and assign arbitrarily
        for p_idx, p_items in enumerate(active_patterns):
            station_id = p_idx # each pattern is a mapped to a unique station ID
            for i_item in p_items:
                best_assignment[instance['idx_to_item'][i_item]] = station_id
                
        total_visits = evaluate_total_visits(instance, active_patterns)
        max_wl, std_wl = evaluate_station_workloads(instance, active_patterns, prod_lines)
        
        # Determine strict violations
        cap_broken = sum(1 for p in active_patterns if len(p) > instance['K'])
        wl_broken = 0 # Explicitly ignoring time_caps
        
        return best_assignment, total_visits, bp_time, max_wl, std_wl, cap_broken, wl_broken
    else:
        print("  CG: No feasible integer solution found within limits.")
        return None, None, bp_time, None, None, None, None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CG CSLAP (Homogeneous Set Partitioning, synthetic)")
    parser.add_argument("--prefix", type=str, required=True)
    parser.add_argument("--dir",    type=str, default="synthetic_datasets")
    parser.add_argument("--time",   type=int, default=300)
    args = parser.parse_args()

    print(f"Running Homogeneous CG on {args.prefix}...")
    order_prods, stations, products, prod_lines = read_data(args.prefix, args.dir)
    
    capacities = {s["STATION_ID"]: s["CAPACITY"] for s in stations}
    instance = build_instance(order_prods, products, capacities)
    
    out = start_branch_and_price(instance, prod_lines, time_limit=args.time)
    
    if out[0] is not None:
        best_assignment, total_visits, elapsed, max_workload, workload_std_dev, cap_broken, wl_broken = out
        print(f"  CG Done: Visits={total_visits}, Time={elapsed:.2f}s, "
              f"WL_Std={workload_std_dev:.4f}, Max_WL={max_workload:.4f}, "
              f"Cap_Broken={cap_broken}, WL_Broken={wl_broken}")
    else:
        print(f"  CG Failed: Time={out[2]:.2f}s")
