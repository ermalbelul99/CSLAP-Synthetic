import pandas as pd
import numpy as np
from itertools import combinations
from collections import defaultdict
import os

def process_metrics(name, df):
    print(f"==============================")
    print(f"--- Processing {name} ---")
    
    # Get total SKUs N
    N = df['PRODUCT'].nunique()
    print(f"Total Products (N): {N}")
    
    # 1. Order Size Distribution
    order_sizes = df.groupby('ORDER')['PRODUCT'].nunique()
    print(f"Order Size Distribution:")
    print(f"  Mean: {order_sizes.mean():.2f}")
    print(f"  Median: {order_sizes.median():.2f}")
    print(f"  90th Percentile: {np.percentile(order_sizes, 90):.2f}")
    
    # 2. Co-occurrence Matrix
    print("Building pair combinations... (this might take a few seconds)")
    pair_counts = defaultdict(int)
    prod_counts = defaultdict(int)
    
    op_items = df.groupby('ORDER')['PRODUCT'].apply(list).to_dict()
    
    for o, prods in op_items.items():
        unique_prods = list(set(prods))
        for p in unique_prods:
            prod_counts[p] += 1
            
        if len(unique_prods) < 2:
            continue
            
        for p1, p2 in combinations(sorted(unique_prods), 2):
            pair_counts[(p1, p2)] += 1
            
    # Metric 1: Sparsity
    unique_pairs_observed = len(pair_counts)
    total_possible_pairs = (N * (N - 1)) / 2
    density = unique_pairs_observed / total_possible_pairs if total_possible_pairs > 0 else 0
    print(f"Network Sparsity (Density): {density:.6f} ({density*100:.4f}%)")
    
    # Metric 2: Top-Tier Affinity
    if not pair_counts:
        print("No pairs found!")
        return
        
    sorted_pairs = sorted(pair_counts.items(), key=lambda x: -x[1])
    # Top 1% of OBSERVED pairs
    top_1_pct_count = max(1, int(len(sorted_pairs) * 0.01))
    top_pairs = sorted_pairs[:top_1_pct_count]
    
    affinities = []
    for (p1, p2), count in top_pairs:
        c1 = prod_counts[p1]
        c2 = prod_counts[p2]
        # Affinity defined as the conditional probability if you buy the rarer item, you'll buy the counterpart.
        prob = count / min(c1, c2) 
        affinities.append(prob)
        
    print(f"Top 1% Affinity (Conditional Probability): {np.mean(affinities)*100:.2f}%")
    print(f"==============================\n")


def main():
    # 1. Load Synthetic 2000 SKUs
    syn_path = "synthetic_datasets/syn_2000sku_orders.csv"
    if os.path.exists(syn_path):
        df_syn = pd.read_csv(syn_path, sep=";")
        process_metrics("Synthetic (2000 SKUs)", df_syn)
    else:
        print(f"Could not find synthetic data at {syn_path}")
        
    # 2. Load Industrial DataFrame
    ind_path = "Heuristic_Connex_Set_Project/data/BERNER_ORDER_LINES_09-12.csv"
    if os.path.exists(ind_path):
        print("Loading Industrial Data...")
        df_ind = pd.read_csv(ind_path, sep=';', low_memory=False)
        
        # We should apply the order filter > 5 to match the operational condition
        order_product_counts = df_ind.groupby('ORDER')['PRODUCT'].nunique()
        orders_to_keep = order_product_counts[order_product_counts > 5].index
        df_ind = df_ind[df_ind['ORDER'].isin(orders_to_keep)]
        
        process_metrics("Industrial Data (Filtered >5 items)", df_ind)
    else:
        print(f"Could not find Industrial data at {ind_path}")

if __name__ == "__main__":
    main()
