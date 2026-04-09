import pandas as pd

def calculate_workload_capacities(filepath="Heuristic_Connex_Set_Project/data/BERNER_ORDER_LINES_09-12.csv"):
    print(f"Loading industrial data from {filepath}...")
    
    # Read the data the same way as the data loader
    data_df = pd.read_csv(filepath, sep=';')[['PRODUCT', 'ORDER', 'STATION']].drop_duplicates().dropna()
    
    # 1. Resolve products with multiple stations (use the station from the last seen order)
    unique_counts = data_df.groupby('PRODUCT')['STATION'].nunique().reset_index(name='numb_stat_per_prod')
    data_df = data_df.merge(unique_counts, on='PRODUCT', how='left')

    products_with_multi = data_df[data_df['numb_stat_per_prod'] > 1]['PRODUCT'].unique()
    max_order_stations = data_df[data_df['PRODUCT'].isin(products_with_multi)] \
        .sort_values(by='ORDER', ascending=False) \
        .drop_duplicates(subset=['PRODUCT'], keep='first')[['PRODUCT', 'STATION']]

    data_df = data_df.merge(max_order_stations, on='PRODUCT', how='left', suffixes=('', '_max_order'))
    data_df['STATION'] = data_df.apply(
        lambda x: x['STATION_max_order'] if pd.notna(x['STATION_max_order']) else x['STATION'], axis=1
    )
    data_df.drop(columns=['STATION_max_order', 'numb_stat_per_prod'], inplace=True)

    # 2. Filter unwanted stations and clean station names (consistent with project logic)
    stations_not_included = ['01.Z8', '01.15', '01.GED']
    data_df = data_df[~data_df['STATION'].isin(stations_not_included)]
    data_df.loc[data_df['STATION'] == '01.GE4', 'STATION'] = '01.E4'

    # Calculate number of unique products (locations) per station
    locations_per_station = data_df.groupby('STATION')['PRODUCT'].nunique().to_dict()

    stations_array = data_df['STATION'].unique().astype(str)

    # 3. Determine Station Speeds 
    static_stations = ['01.E4', '01.31', '01.30']
    palette_stations = ['01.01', '01.02', '01.03', '01.04', '01.05']
    union_stat = static_stations + palette_stations

    STATIC_SPEED = 37700
    PALETTE_SPEED = 57200
    DYNAMIC_SPEED = 83200

    speed = {}
    for s in stations_array:
        locs = locations_per_station.get(s, 1)
        if s in static_stations:
            speed[s] = STATIC_SPEED / locs
        elif s in palette_stations:
            speed[s] = PALETTE_SPEED / locs
        else:
            speed[s] = DYNAMIC_SPEED / locs

    # 4. Calculate Workload Capacity
    prod_freq = data_df.groupby('PRODUCT').size().to_dict()
    prod_station = data_df.groupby('PRODUCT')['STATION'].first().to_dict()
    
    time_caps = {s: 0.0 for s in stations_array}
    raw_visits = {s: 0 for s in stations_array}
    
    for p, freq in prod_freq.items():
        s = prod_station.get(p)
        if s in speed:
            time_caps[s] += freq / speed[s]
            raw_visits[s] += freq
            
    # 5. Output results
    results = []
    for s in stations_array:
        results.append({
            "Station": s,
            "Total_Order_Lines": raw_visits[s],
            "Unique_Products": locations_per_station.get(s, 0),
            "Speed": round(speed[s], 2) if s in speed else 0,
            "Workload_Capacity": round(time_caps[s], 4)
        })
        
    df_results = pd.DataFrame(results).sort_values(by="Station", ascending=True)
    
    print("\n--- Workload Capacities based on Original Assignment ---")
    print(df_results.to_string(index=False))
    
    output_path = "original_workload_capacities.csv"
    df_results.to_csv(output_path, index=False)
    print(f"\nResults saved to {output_path}")

if __name__ == "__main__":
    calculate_workload_capacities()
