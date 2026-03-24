import pandas as pd
import numpy as np
import os
import sys

def load_industrial_data(filepath="Heuristic_Connex_Set_Project/data/BERNER_ORDER_LINES_09-12.csv"):
    """
    Parses and cleans the industrial dataset, mimicking the logic from Berner_Hexaly_Solution_Sets_v1.ipynb.
    Returns the partial datasets suitable for the CG/MILP/GA solvers, and the full structures
    needed for final metric evaluation.
    """
    print("Loading industrial data...")
    # 1. Read input
    data_df_initial = pd.read_csv(filepath, sep=';')[['PRODUCT','ORDER','STATION']].drop_duplicates().dropna()

    # 2. Fix multiple stations for the same product (use last seen order station)
    unique_counts = data_df_initial[['PRODUCT','STATION']].groupby('PRODUCT')['STATION'].nunique().reset_index(name='numb_stat_per_prod')
    data_df_initial = data_df_initial.merge(unique_counts, on='PRODUCT', how='left')

    products_with_multiple_stations = data_df_initial[data_df_initial['numb_stat_per_prod'] > 1]['PRODUCT'].unique()
    max_order_stations = data_df_initial[data_df_initial['PRODUCT'].isin(products_with_multiple_stations)] \
        .sort_values(by='ORDER', ascending=False) \
        .drop_duplicates(subset=['PRODUCT'], keep='first')[['PRODUCT', 'STATION']]

    data_df_initial = data_df_initial.merge(max_order_stations, on='PRODUCT', how='left', suffixes=('', '_max_order'))
    data_df_initial['STATION'] = data_df_initial.apply(lambda x: x['STATION_max_order'] if pd.notna(x['STATION_max_order']) else x['STATION'], axis=1)
    data_df_initial.drop(columns=['STATION_max_order', 'numb_stat_per_prod'], inplace=True)

    data_df_new = data_df_initial.copy()

    # 3. Filter unwanted stations
    stations_not_included = ['01.Z8','01.15','01.GED']
    data_df_new = data_df_new[~(data_df_new['STATION'].isin(stations_not_included))]
    data_df_new.loc[data_df_new['STATION'] == '01.GE4', 'STATION'] = '01.E4'

    # Calculate global locations per station (before unique orders filter)
    total_number_of_location_per_station = data_df_new.groupby('STATION')['PRODUCT'].nunique().to_dict()

    # 4. Filter out orders with 5 or fewer unique products
    data_df_full = data_df_new.copy()
    order_product_counts = data_df_new.groupby('ORDER')['PRODUCT'].nunique()
    orders_to_keep = order_product_counts[order_product_counts > 5].index
    data_df_new = data_df_new[data_df_new['ORDER'].isin(orders_to_keep)]
    data_df_new['Product_Frequency'] = data_df_new.groupby('PRODUCT')['ORDER'].transform('count')
    
    stations_array = data_df_new['STATION'].unique().astype(str)

    # 5. Determine Station Speeds
    static_stations = ['01.E4','01.31','01.30']
    palette_stations = ['01.01','01.02','01.03','01.04','01.05']
    union_stat = static_stations + palette_stations
    dynamic_stations = [s for s in stations_array if s not in union_stat]

    STATIC_SPEED = 37700
    PALETTE_SPEED = 57200
    DYNAMIC_SPEED = 83200

    speed = {}
    for s in stations_array:
        locs = total_number_of_location_per_station.get(s, 1)
        if s in static_stations:
            speed[s] = STATIC_SPEED / locs
        elif s in palette_stations:
            speed[s] = PALETTE_SPEED / locs
        else:
            speed[s] = DYNAMIC_SPEED / locs

    # 6. Group by Product and identify the "Low Frequency" static products to filter out
    df_product = data_df_new.groupby('PRODUCT').agg({
        'ORDER': list,
        'STATION': 'first'
    }).reset_index().rename(columns={'ORDER': 'ORDER_LIST'})
    df_product['Product_Frequency'] = df_product['ORDER_LIST'].apply(len)
    df_product = df_product.sort_values(by='Product_Frequency', ascending=False)
    df_product.set_index('PRODUCT', inplace=True)

    low_freq_prod = df_product[(df_product['Product_Frequency'] <= 5) & (df_product['STATION'].isin(static_stations))].index
    
    # Separate into Kept and Filtered
    df_product_filtered = df_product[df_product.index.isin(low_freq_prod)]
    static_assignment = df_product_filtered['STATION'].to_dict()

    # Include products that were entirely dropped by the order filter
    dropped_products = set(data_df_full['PRODUCT']) - set(data_df_new['PRODUCT'])
    if dropped_products:
        df_full_dropped = data_df_full[data_df_full['PRODUCT'].isin(dropped_products)].groupby('PRODUCT').agg({'STATION': 'first'})
        static_assignment.update(df_full_dropped['STATION'].to_dict())

    df_product_kept = df_product[~df_product.index.isin(low_freq_prod)]

    # 7. Physical/Time Capacity allocations based purely on Kept products
    total_number_of_location_per_station_2 = df_product_kept.groupby('STATION').size().to_dict()
    
    pr_solver = list(df_product_kept.index)
    product_frequency = df_product_kept['Product_Frequency'].to_dict()
    product_to_station = df_product_kept['STATION'].to_dict()

    total_length = {s: 0.0 for s in stations_array}
    for p in pr_solver:
        s = product_to_station[p]
        total_length[s] += product_frequency[p] / speed[s]

    # Build the station dictionaries
    st_solver = []
    for s in stations_array:
        cap = total_number_of_location_per_station_2.get(s, 0)
        time_cap = total_length[s]
        # Only add stations that actually have capacity allocated (to avoid solver issues)
        if cap > 0:
            st_solver.append({
                "STATION_ID": s,
                "CAPACITY": cap,
                "TIME_CAPACITY": time_cap,
                "SPEED": speed[s]
            })
            
    # Filter the exact ones just to match
    valid_station_ids = {s["STATION_ID"] for s in st_solver}

    # Build op_solver, pl_solver
    pl_solver = product_frequency
    
    # We must restrict the orders dataframe to only kept products for the solvers
    data_df_solver = data_df_new[data_df_new['PRODUCT'].isin(pr_solver) & data_df_new['STATION'].isin(valid_station_ids)]
    op_solver = data_df_solver.groupby('ORDER')['PRODUCT'].apply(list).to_dict()
    
    # Also provide the warm start assignment (the original assigned station for kept products)
    warm_start_assignment = product_to_station
    
    # --- For Final Evaluation ---
    # We need the full op and pl, spanning BOTH kept and filtered products, including all dropped small orders
    op_full = data_df_full.groupby('ORDER')['PRODUCT'].apply(list).to_dict()
    pl_full = data_df_full.groupby('PRODUCT')['ORDER'].nunique().to_dict()
    
    # For full metric tracking, we need full station list including those that might only have filtered products
    # For the FULL evaluation, the capacity is literally the total number of locations on each station,
    # and time_capacity is the actual time capacity total across ALL orders.
    full_caps = data_df_full.groupby('STATION')['PRODUCT'].nunique().to_dict()
    
    full_prod_freq = data_df_full.groupby('PRODUCT').size().to_dict()
    full_prod_station = data_df_full.groupby('PRODUCT')['STATION'].first().to_dict()
    full_time_caps = {s: 0.0 for s in stations_array}
    for p, freq in full_prod_freq.items():
        s = full_prod_station.get(p)
        if s in speed:
            full_time_caps[s] += freq / speed[s]

    st_full = []
    for s in stations_array:
        st_full.append({
            "STATION_ID": s,
            "CAPACITY": full_caps.get(s, 0),
            "TIME_CAPACITY": full_time_caps[s],
            "SPEED": speed[s]
        })

    return {
        "op_solver": op_solver,
        "st_solver": st_solver,
        "pr_solver": pr_solver,
        "pl_solver": pl_solver,
        "odf_solver": data_df_solver,
        "warm_start_assignment": warm_start_assignment,
        "static_assignment": static_assignment,
        "op_full": op_full,
        "st_full": st_full,
        "pl_full": pl_full
    }
