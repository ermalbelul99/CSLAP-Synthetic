
# --- Cell 0 ---
import pandas as pd
import numpy as np
from tqdm import tqdm
from time import time
import hexaly.optimizer as hexaly
from itertools import product
import sys
# --- Cell 1 ---
start_time = time()
# --- Cell 2 ---
hexaly.HxVersion.license_content = "LICENSE_KEY = ED3A-2222-89F4B124-770D-60A55B936308D780-9506208B36204986-9B3E-E289-C66E"
# --- Cell 3 ---
def display_callback(optimizer, event_type):
    if event_type == hexaly.HxCallbackType.DISPLAY:
        solution = optimizer.solution
        if optimizer.model.nb_objectives > 0:
            objective_expr = optimizer.model.objectives[0]
            objective_value = solution.get_value(objective_expr)
            objective_bound = solution.get_objective_bound(0)
            optimality_gap = solution.get_objective_gap(0)
            print(f"Objective Value: {objective_value}")
            print(f"Objective Bound: {objective_bound}")
            print(f"Optimality Gap: {optimality_gap}")
        else:
            print("No objectives defined in the model.")
# --- Cell 5 ---
#GLOBAL VARIABLES
STATIC_SPEED = 37700
PALETTE_SPEED = 57200
DYNAMIC_SPEED = 83200
# --- Cell 7 ---
#function  to reduce the memory usage
def reduce_mem_usage(df, verbose=False):
    numerics = ['int16', 'int32', 'int64', 'float16', 'float32', 'float64']
    start_mem = df.memory_usage().sum() / 1024**2
    for col in df.columns:
        col_type = df[col].dtypes
        if col_type in numerics:
            c_min = df[col].min()
            c_max = df[col].max()
            if str(col_type)[:3] == 'int':
                if c_min > np.iinfo(np.int8).min and c_max < np.iinfo(np.int8).max:
                    df[col] = df[col].astype(np.int8)
                elif c_min > np.iinfo(np.int16).min and c_max < np.iinfo(np.int16).max:
                    df[col] = df[col].astype(np.int16)
                elif c_min > np.iinfo(np.int32).min and c_max < np.iinfo(np.int32).max:
                    df[col] = df[col].astype(np.int32)
                elif c_min > np.iinfo(np.int64).min and c_max < np.iinfo(np.int64).max:
                    df[col] = df[col].astype(np.int64)  
            else:
                if c_min > np.finfo(np.float32).min and c_max < np.finfo(np.float32).max:
                    df[col] = df[col].astype(np.float32)
                else:
                    df[col] = df[col].astype(np.float64)    
    end_mem = df.memory_usage().sum() / 1024**2
    if verbose:
        print('Mem. usage decreased to {:5.2f} Mb ({:.1f}% reduction)'.format(end_mem, 100 * (start_mem - end_mem) / start_mem))
    return df
# --- Cell 9 ---
data_df_initial= pd.read_csv(r"C:\Users\ebelul\Downloads\CSLAP_Project_All\Heuristic_Connex_Set_Project\data\BERNER_ORDER_LINES_09-12.csv", sep=';')[['PRODUCT','ORDER','STATION']].drop_duplicates().dropna()#, nrows=20000)


#Calculate the unique number of product per station
unique_counts = data_df_initial[['PRODUCT','STATION']].groupby('PRODUCT')['STATION'].nunique().reset_index(name='numb_stat_per_prod')
#Merging the count back to the original dataframe
data_df_initial = data_df_initial.merge(unique_counts, on='PRODUCT', how='left')

#Updating the product assignment with the last station they correspond
# Step 1: Identify products with numb_stat_per_prod > 1.
products_with_multiple_stations = data_df_initial[data_df_initial['numb_stat_per_prod'] > 1]['PRODUCT'].unique()

# Step 2: For these products, find the maximum order ID and the corresponding station ID.
max_order_stations = data_df_initial[data_df_initial['PRODUCT'].isin(products_with_multiple_stations)] \
    .sort_values(by='ORDER', ascending=False) \
    .drop_duplicates(subset=['PRODUCT'], keep='first')[['PRODUCT', 'STATION']]

# Step 3: Update the station ID for all occurrences of these products.
# First, merge this information back to the original df_order.
data_df_initial = data_df_initial.merge(max_order_stations, on='PRODUCT', how='left', suffixes=('', '_max_order'))

# If STATION_max_order is not NaN (i.e., for products with multiple stations), update the STATION column.
data_df_initial['STATION'] = data_df_initial.apply(lambda x: x['STATION_max_order'] if pd.notna(x['STATION_max_order']) else x['STATION'], axis=1)

# Drop the temporary STATION_max_order column as it's no longer needed.
data_df_initial.drop(columns=['STATION_max_order', 'numb_stat_per_prod'], inplace=True)

data_df_new = data_df_initial.copy()
# --- Cell 10 ---
print(data_df_new)
# --- Cell 12 ---
stations_not_included =  ['01.Z8','01.15','01.GED']
#Filter and count occurrences at the same time
data_df_new = data_df_new[~(data_df_new['STATION'].isin(stations_not_included))]
data_df_new.loc[data_df_new['STATION'] == '01.GE4', 'STATION'] = '01.E4'
# Calculate the total number of unique orders for setting the threshold
total_unique_orders = data_df_new['ORDER'].nunique()

#Calculate the frequency for each product
data_df_new['Product_Frequency'] = data_df_new.groupby('PRODUCT')['ORDER'].transform('count')

# data_df_new.rename(columns={'STATION':'OldStationID'},inplace=True)
# uniquestations = data_df_new['OldStationID'].unique().astype(str)
stations = data_df_new['STATION'].unique().astype(str)
# --- Cell 14 ---
# mapping_dict = {station: f'S_{i}' for i, station in enumerate(uniquestations, start=1)}
# data_df_new['STATION'] = data_df_new['OldStationID'].map(mapping_dict)
# print(mapping_dict)
# stations_not_included = ['S_26','S_25']
# #Filter and count occurrences at the same time
# data_df_new = data_df_new[~(data_df_new['STATION'].isin(stations_not_included))
# static_stations = ['S_1','S_2','S_4']
# palette_stations = ['S_19','S_3','S_18','S_8','S_5']
# union_stat = static_stations + palette_stations
# dynamic_stations = np.array(data_df_new[~(data_df_new['STATION'].isin(union_stat))]['STATION'].drop_duplicates())
# --- Cell 15 ---
# Count the number of 'Location_ID' for each STATION
#Calculate the unique number of product per station
total_number_of_location_per_station = data_df_new.groupby('STATION')['PRODUCT'].nunique().to_dict()

# Count the number of initial lines for each STATION
#Calculate number of product per station
station_lines_initial = data_df_new.groupby('STATION')['PRODUCT'].count().to_dict()
# --- Cell 16 ---
# Calculate the number of unique 'PRODUCT' values for each 'ORDER'
order_product_counts = data_df_new.groupby('ORDER')['PRODUCT'].nunique()

# Filter 'ORDER's where the count of unique 'PRODUCT' values is more than 3
orders_to_keep = order_product_counts[order_product_counts > 5].index

# Filter the original DataFrame to keep only those rows with 'ORDER's in 'orders_to_keep'
data_df_new = data_df_new[data_df_new['ORDER'].isin(orders_to_keep)]
# --- Cell 18 ---
static_stations = ['01.E4','01.31','01.30']
palette_stations = ['01.01','01.02','01.03','01.04','01.05']
union_stat = static_stations + palette_stations
dynamic_stations = np.array(data_df_new[~(data_df_new['STATION'].isin(union_stat))]['STATION'].drop_duplicates())
# --- Cell 20 ---
speed = {s:STATIC_SPEED/total_number_of_location_per_station[s] for s in static_stations if s in stations}
speed.update({s:PALETTE_SPEED/total_number_of_location_per_station[s] for s in palette_stations if s in stations})
speed.update({s:DYNAMIC_SPEED/total_number_of_location_per_station[s] for s in dynamic_stations if s in stations})
# --- Cell 21 ---
print(len(data_df_new))
print(len(np.unique(data_df_new['PRODUCT'].values)))
print(len(np.unique(data_df_new['ORDER'].values)))
print(len(np.unique(data_df_new['STATION'].values)))
print(sum(list(total_number_of_location_per_station.values())))
# --- Cell 23 ---
# data_df_new = pd.read_csv("..\Data\df_order_new.csv")[['Product','ORDER','MAJ_STAT']].drop_duplicates().dropna()
# data_df_new.rename(columns= {'Product': 'PRODUCT', 'MAJ_STAT':'STATION'}, inplace=True)
# data_df_new = reduce_mem_usage(data_df_new, verbose=False)
# --- Cell 24 ---
df_product = data_df_new.groupby('PRODUCT').agg({
    'ORDER': list,  # Aggregate orders into a list
    'STATION': 'first'  # Assuming each product is assigned to a unique station, we take the first occurrence
}).reset_index().rename(columns={'ORDER': 'ORDER_LIST'})
df_product['Product_Frequency'] = df_product['ORDER_LIST'].apply(len)
df_product = df_product.sort_values(by='Product_Frequency', ascending=False)
df_product.set_index('PRODUCT',inplace=True)
print(df_product)
# --- Cell 25 ---
low_freq_prod = df_product[(df_product['Product_Frequency']<=5) & (df_product['STATION'].isin(static_stations))].index
#low_freq_prod = df_product[(df_product['Product_Frequency']<=179)].index
df_product = df_product[~df_product.index.isin(low_freq_prod)]
print(len(low_freq_prod))
# --- Cell 26 ---
print(len(df_product))
# --- Cell 28 ---
data_df_new2 = data_df_new[['PRODUCT','ORDER']].drop_duplicates()
df_order = data_df_new2[data_df_new2['PRODUCT'].isin(df_product.index)].groupby('ORDER')['PRODUCT'].apply(list).reset_index(name='PRODUCT_LIST')
df_order.set_index('ORDER',inplace=True)
# --- Cell 30 ---
data_df_new3 = data_df_new[['PRODUCT','STATION']].drop_duplicates()
df_station = data_df_new3[data_df_new3['PRODUCT'].isin(df_product.index)].groupby('STATION')['PRODUCT'].apply(list).reset_index(name='PRODUCT_ASSIGNED')
df_station.set_index('STATION',inplace=True)
# --- Cell 32 ---
total_number_of_location_per_station_2 = df_product.groupby('STATION').size().to_dict()
print(total_number_of_location_per_station_2)
# --- Cell 33 ---
# Convert df_product and speed data into dictionaries for quick lookup
product_frequency = (
    df_product[['Product_Frequency']]
    .set_index(df_product.index)['Product_Frequency']
    .to_dict()
)
# Assuming data_df_new contains PRODUCT and STATION mapping directly
product_to_station = (
    df_product[['STATION']]
    .set_index(df_product.index)['STATION']
    .to_dict()
)
# --- Cell 34 ---
print(len(product_frequency))
print(len(product_to_station))
# --- Cell 36 ---
products = df_product.index
orders = list(df_product['ORDER_LIST'].explode().unique())
data_group = data_df_new[data_df_new['PRODUCT'].isin(df_product.index)]
# --- Cell 37 ---
total_length = {s:0 for s in stations}
count = {s:0 for s in stations}
for p in products:
    for s in stations:
        if product_to_station[p] == s:
                    total_length[s] += product_frequency[p] / speed[s]
                    count[s]+=1

print(total_length)
# --- Cell 38 ---
print(sum(total_length[s] for s in stations))
print(sum(count[s] for s in stations))
print(sum(total_number_of_location_per_station_2[s] for s in stations))
# --- Cell 39 ---
#Scale the workload coefficent to aviod numerical instabilities in the solver process
# Define scaling factors to normalize the right-hand side to 1.
# We also avoid division by zero by using a small tolerance.
#scaling = { s: (1.0 / total_length[s] if total_length[s] > 1e-12 else 1.0) for s in stations }
# --- Cell 41 ---
def generate_mip_start(df_station,product_to_index):
    # Approach is to initialize initial_solution_product_station and initial_solution_order_station
    initial_station_assignments_named = df_station['PRODUCT_ASSIGNED'].to_dict()

    initial_station_assignments_indices = {
    s: [product_to_index[p] for p in products]
    for s, products in initial_station_assignments_named.items()
    }
    
    return initial_station_assignments_indices
# --- Cell 43 ---
with hexaly.HexalyOptimizer() as optimizer:
    optimizer.param.time_limit = 72000
    model = optimizer.model
    optimizer.param.verbosity = 1
    optimizer.param.set_time_between_displays(60)
    optimizer.add_callback(hexaly.HxCallbackType.DISPLAY, display_callback)
    #optimizer.param.set_nb_threads(8)
    #change from product names to indexes to fit in the set variable 
    product_to_index = {p: idx for idx, p in enumerate(products)}

    
    # Set decision variable that shows the set of products assigned to each s
    station_products = {s: model.set(len(products)) for s in stations}

    # Constraint: Products assigned exactly once (partition)
    model.constraint(model.partition([station_products[s] for s in stations]))

    # Constraint: Maximum products per station
    for s in tqdm(stations):
        model.constraint(model.count(station_products[s]) <= total_number_of_location_per_station_2.get(s, 0))

    # Constraint: Workload limits per station
    for s in  tqdm(stations):
        workload_expr = model.sum(df_product.loc[p]['Product_Frequency']/speed[s] * model.contains(station_products[s], product_to_index[p]) for p in products)
        model.constraint(workload_expr <= total_length[s])

    # Objective: Minimize total number of station visits per order
    pbar = tqdm(total=len(orders) * len(stations), desc='Inner loop', leave=True)
    objective = 0
    for o in orders:
        prods_in_o = df_order.loc[o]['PRODUCT_LIST']
        for s in stations:   
            objective += model.sum(
                model.or_(*(model.contains(station_products[s], product_to_index[p]) for p in prods_in_o))
            )
            pbar.update(1)
    model.minimize(objective)

    model.close()

    # Generate the initial solution
    initial_station_assignments_indices = generate_mip_start(df_station,product_to_index)

    # Assign MIP start values to Hexaly variables
    for s in stations:
        for idx in initial_station_assignments_indices.get(s, []):
            station_products[s].value.add(idx) 
        
    optimizer.solve()

    station_assignment_results = {
    s: station_products[s].value for s in stations
    }
    
    index_to_product = {idx: p for p, idx in product_to_index.items()}
    
    station_assignments_named = {
        s: [index_to_product[idx] for idx in station_assignment_results[s]]
        for s in stations
    }
# --- Cell 45 ---
df_assignments = pd.DataFrame([
    {'PRODUCT_ID': product, 'STATION': station}
    for station, products in station_assignments_named.items()
    for product in products
])
# --- Cell 46 ---
df_assignments.to_csv('product_assignment_Hexaly_set_v1.csv')
# --- Cell 47 ---
end_time = time() - start_time
print(end_time)
# --- Cell 48 ---
stations_not_included = ['01.Z8']
#Filter and count occurrences at the same time
data_df_initial = data_df_initial[~(data_df_initial['STATION'].isin(stations_not_included))]
data_df_initial.loc[data_df_initial['STATION'] == '01.GE4', 'STATION'] = '01.E4'
# data_df_initial.rename(columns={'STATION':'OldStationID'},inplace=True)
# data_df_initial['STATION'] = data_df_initial['OldStationID'].map(mapping_dict)

data_df_initial['Product_Frequency'] = data_df_initial.groupby('PRODUCT')['ORDER'].transform('count')
# --- Cell 49 ---
print(len(np.unique(data_df_initial['ORDER'])))
print(len(np.unique(data_df_initial['PRODUCT'])))
print(len(np.unique(data_df_initial['STATION'])))
# --- Cell 50 ---
print(df_assignments)
# --- Cell 52 ---
product_station_df = df_assignments.copy()
product_station_df.rename(columns={"STATION":"StationID_P","PRODUCT_ID":"PRODUCT"},inplace=True)
product_station_df.head(5)
# --- Cell 53 ---
df_final = pd.merge(data_df_initial,product_station_df, on='PRODUCT',how='left')[['PRODUCT','STATION','StationID_P','ORDER','Product_Frequency']]
df_final['StationID_P'].fillna(df_final['STATION'], inplace=True)
print(df_final)
# --- Cell 56 ---
df_order_s1 = df_final[['STATION','ORDER']].drop_duplicates()
df_order_s1['cnt'] = df_order_s1.groupby('ORDER')['STATION'].transform('nunique')
df_order_s1_cnt = df_order_s1[['cnt','ORDER']].drop_duplicates()
s1 = df_order_s1_cnt['cnt'].sum()
m1 = df_order_s1_cnt['cnt'].mean()
print(s1,m1)
# --- Cell 58 ---
df_order_s2 = df_final[['StationID_P','ORDER']].drop_duplicates()
df_order_s2['cnt'] = df_order_s2.groupby('ORDER')['StationID_P'].transform('nunique')
df_order_s2_cnt = df_order_s2[['cnt','ORDER']].drop_duplicates()
s2 = df_order_s2_cnt['cnt'].sum()
m2 = df_order_s2_cnt['cnt'].mean()
print(s2,m2)
# --- Cell 59 ---
df_order_s1_cnt = df_order_s1_cnt['cnt'].value_counts(dropna=False)
df_order_s2_cnt = df_order_s2_cnt['cnt'].value_counts(dropna=False)
# --- Cell 61 ---
import matplotlib.pyplot as plt
# Align the indices
all_indices = sorted(set(df_order_s1_cnt.index) | set(df_order_s2_cnt.index))  # Union of indices from both datasets
df_order_s1_cnt = df_order_s1_cnt.reindex(all_indices).fillna(0)  # Reindex and fill missing values with 0
df_order_s2_cnt = df_order_s2_cnt.reindex(all_indices).fillna(0)  # Reindex and fill missing values with 0

print(all_indices)
# Set up the figure and axis
plt.figure(figsize=(10, 5))
ax = plt.gca()


# Width of the bars
width = 0.35


# Positions for the bars
indices = np.arange(len(all_indices))


# Plotting
rects1 = ax.bar(indices - width/2, df_order_s1_cnt, width, label='Original', alpha=0.6)
rects2 = ax.bar(indices + width/2, df_order_s2_cnt, width, label='Our Solution', alpha=0.6)


# Add labels and title
plt.xlabel('Number of Stations')
plt.ylabel('Number of Orders')
plt.title('Number of Orders per Stations Numbers')


# Add x-ticks and labels
plt.xticks(indices, all_indices)
# Add a legend
plt.legend()
plt.savefig('Hexaly'+'_'+'number_of_orders_per_station_numbers.png')


plt.show()
# --- Cell 63 ---
def plot_final(tmp_final,xlabel,ylabel,title, sort_by='STATION', ascending=True):


    # Set up the figure and axis
    plt.figure(figsize=(10, 5))
    ax = plt.gca()


    # Width of the bars
    width = 0.35
    
    # Sorting tmp_final based on the specified sort_by column
    tmp_final_sorted = tmp_final.sort_values(by=sort_by, ascending=ascending)


    # Positions for the bars
    stations = tmp_final['STATION'].astype(str).values
    indices = np.arange(len(stations))


    # Plotting
    rects1 = ax.bar(indices - width/2, tmp_final['cnt_lines'], width, label='Original', alpha=0.6)
    rects2 = ax.bar(indices + width/2, tmp_final['cnt_lines_New'], width, label='Our Solution', alpha=0.6)


    # Add labels and title
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)


    # Add x-ticks and labels
    plt.xticks(indices, stations, rotation=45)


    # Add a legend
    plt.legend()


    plt.savefig('Hexaly'+'_'+'number_of_lines_per_station.png')
    plt.show()
# --- Cell 64 ---
df_order_lines_plot = df_final.copy()
df_order_lines_plot['cnt_lines_New'] = df_order_lines_plot[['PRODUCT','StationID_P']].groupby('StationID_P').transform('count')
df_order_lines_plot['cnt_lines'] = df_order_lines_plot[['PRODUCT','STATION']].groupby('STATION').transform('count')
tmp_lines = df_order_lines_plot[['StationID_P','cnt_lines_New']].drop_duplicates()
tmp_lines.rename(columns={'StationID_P':'STATION'}, inplace=True)
tmp_lines = tmp_lines.merge(df_order_lines_plot[['STATION','cnt_lines']].drop_duplicates(), on='STATION', how='outer').fillna(0)
tmp_lines.sort_values(by='cnt_lines', ascending=True, inplace=True)
xlabel = 'Station ID'
ylabel = 'Number of lines'
title = 'Number of Lines per Station'
plot_final(tmp_lines, xlabel, ylabel, title, sort_by='cnt_lines', ascending=False)
# --- Cell 66 ---
df_order_ref_plot = df_final.copy()
df_order_ref_plot['cnt_lines_New'] = df_order_ref_plot[['PRODUCT','StationID_P']].groupby('StationID_P').transform('nunique')
df_order_ref_plot['cnt_lines'] = df_order_ref_plot[['PRODUCT','STATION']].groupby('STATION').transform('nunique')
tmp_refs = df_order_ref_plot[['StationID_P','cnt_lines_New']].drop_duplicates()
tmp_refs.rename(columns={'StationID_P':'STATION'}, inplace=True)
tmp_refs = tmp_refs.merge(df_order_ref_plot[['STATION','cnt_lines']].drop_duplicates(), on='STATION', how='outer').fillna(0)
tmp_refs.sort_values(by='cnt_lines', ascending=True, inplace=True)
xlabel = 'Station ID'
ylabel = 'Number of references'
title = 'Number of Products per Station'
plot_final(tmp_refs, xlabel, ylabel, title, sort_by='cnt_lines', ascending=False)
# --- Cell 67 ---
print(tmp_refs)
# --- Cell 68 ---
product_frequency = df_final[['PRODUCT','Product_Frequency']].drop_duplicates().set_index('PRODUCT')['Product_Frequency'].to_dict()
station_product_initial = df_final.groupby('STATION')['PRODUCT'].apply(set).to_dict()
station_product_solution = df_final.groupby('StationID_P')['PRODUCT'].apply(set).to_dict()
# --- Cell 69 ---
total_length_initial={s:0 for s in stations}
total_length_solution={s:0 for s in stations}

for s in stations:
    for p1 in station_product_initial[s]:
        total_length_initial[s] += product_frequency[p1]/speed[s]
        
    for p2 in station_product_solution[s]:
        total_length_solution[s] += product_frequency[p2]/speed[s]

    print(f"Length constraint value = {total_length_solution[s]}, Limit = {total_length_initial[s]}, on station {s}")
# --- Cell 70 ---
print(np.sum(total_length_solution[s] for s in stations))
# --- Cell 71 ---
print(np.sum(total_length_initial[s] for s in stations))