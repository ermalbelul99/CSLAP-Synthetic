"""
Synthetic Data Generator for CSLAP Benchmarking
Strict implementation of Zhang et al. (2019) "Common Itemset" generation.
"""

import numpy as np
import pandas as pd
import os
import argparse

def generate_synthetic_data_zhang(
    num_skus,
    theta=0.7,
    seed=42,
    output_dir="synthetic_datasets",
):
    rng = np.random.RandomState(seed)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # --- 1. SKU Pool ---
    products = np.arange(1, num_skus + 1)

    # --- 2. Common Itemsets ---
    # Number of common itemsets is proportional to N: N * U[0.1, 0.5]
    num_itemsets = int(num_skus * rng.uniform(0.1, 0.5))
    num_itemsets = max(num_itemsets, 1)

    itemsets = []
    for _ in range(num_itemsets):
        # Size of common itemset: U[2, 5]
        size = rng.randint(2, 6)
        itemset = rng.choice(products, size=size, replace=False).tolist()
        itemsets.append(itemset)

    # --- 3. Orders ---
    # Number of orders is proportional to N: N * U[30, 50]
    num_orders = int(num_skus * rng.uniform(30.0, 50.0))

    # --- 4. Stations (Flat Setup) ---
    num_stations = max(5, num_skus // 100)
    
    # Exact slot capacity to ensure uniform product counts across stations
    base_cap = num_skus // num_stations
    capacities = np.full(num_stations, base_cap)
    
    station_ids = np.arange(1, num_stations + 1)
    # Uniform speeds for all stations
    speeds = np.ones(num_stations)

    # --- 5. Generate Orders with Batch Correlation Injection ---
    order_data = []
    
    for order_id in range(1, num_orders + 1):
        # Size of an order: U[5, 15]
        target_size = rng.randint(5, 16)
        current_order_items = []

        # A decimal within [0, 1] is randomly generated
        prob = rng.uniform(0.0, 1.0)

        # If decimal is less than theta, one to three common itemsets are picked
        if prob < theta:
            num_sets_to_add = rng.randint(1, 4)
            for _ in range(num_sets_to_add):
                chosen_set = itemsets[rng.randint(0, len(itemsets))]
                current_order_items.extend(chosen_set)
                if len(current_order_items) >= target_size:
                    break

        # If the order is not fulfilled, fill with random items from N
        while len(current_order_items) < target_size:
            current_order_items.append(rng.choice(products))

        # Truncate in case bulk itemset addition exceeded target_size
        current_order_items = current_order_items[:target_size]

        # Zhang et al. notes an item can appear more than once in an order
        for prod in current_order_items:
            original_station = rng.randint(1, num_stations + 1)
            order_data.append({
                "ORDER": f"ORD_{order_id}",
                "PRODUCT": f"PROD_{prod}",
                "QTY": int(rng.randint(1, 10)),
                "STATION": original_station,
            })

    df_orders = pd.DataFrame(order_data)

    # --- 6. Products DataFrame ---
    prod_freq = df_orders.groupby("PRODUCT").size().reset_index(name="FREQUENCY")
    all_prods = pd.DataFrame({"PRODUCT_ID": products})
    all_prods["PRODUCT"] = all_prods["PRODUCT_ID"].apply(lambda x: f"PROD_{x}")
    all_prods = all_prods.merge(prod_freq, on="PRODUCT", how="left")
    all_prods["FREQUENCY"] = all_prods["FREQUENCY"].fillna(0).astype(int)
    all_prods["CATEGORY"] = rng.randint(0, max(5, num_skus // 25), size=num_skus)
    all_prods["POPULARITY"] = all_prods["FREQUENCY"]

    df_products = all_prods[["PRODUCT_ID", "CATEGORY", "POPULARITY"]].copy()

    # --- 6.5. Constructive Feasibility for Workload Capacity ---
    # We guarantee feasibility by enforcing a flat workload ceiling across all stations.
    # Total workload = sum of all product frequencies
    total_workload = all_prods["FREQUENCY"].sum()
    
    # Mathematical average if spread perfectly
    target_workload_per_station = total_workload / num_stations
    
    # Calculate a dynamic slack factor between 10% and 30% depending on constraints
    #slack_factor = max(1.10, min(1.30, 20 / num_stations))
    slack_factor = 1.10 
    # Fix the workload capacity identical across all stations
    flat_time_cap = int(np.ceil(target_workload_per_station * slack_factor))
    time_capacities = np.full(num_stations, flat_time_cap)

    df_stations = pd.DataFrame({
        "STATION_ID": station_ids,
        "CAPACITY": capacities,
        "TIME_CAPACITY": time_capacities,
        "SPEED": speeds,
    })

    # --- 7. Save ---
    prefix = f"syn_{num_skus}sku"
    df_orders.to_csv(os.path.join(output_dir, f"{prefix}_orders.csv"), index=False, sep=";")
    df_stations.to_csv(os.path.join(output_dir, f"{prefix}_stations.csv"), index=False, sep=";")
    df_products.to_csv(os.path.join(output_dir, f"{prefix}_products.csv"), index=False, sep=";")

    print(f"[Zhang Generator] N={num_skus} | Orders: {num_orders} | Itemsets: {num_itemsets}")
    return df_orders, df_stations, df_products

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sizes", nargs="+", type=int, default=[500, 1000, 2000, 5000])
    parser.add_argument("--theta", type=float, default=0.7)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output_dir", type=str, default="synthetic_datasets")
    args = parser.parse_args()

    for sku_size in args.sizes:
        generate_synthetic_data_zhang(
            num_skus=sku_size,
            theta=args.theta,
            seed=args.seed,
            output_dir=args.output_dir,
        )