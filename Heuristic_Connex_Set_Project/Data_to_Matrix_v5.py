import pandas as pd
import numpy as np
import itertools
import matplotlib.pyplot as plt
from tqdm import tqdm
from matplotlib import cm
from matplotlib.colors import Normalize
import os
import warnings
warnings.filterwarnings('ignore')



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

#function to read the input file
def read_input_file(INPUT_FILE):
    # Read the input file into a Pandas DataFrame
    df_input_file = pd.read_csv(INPUT_FILE, sep=';')
    #reduce memory usage
    df_input_file = reduce_mem_usage(df_input_file)
    return df_input_file


def prepare_order_data(INPUT_FILE):
    #read the input file
    df_order = read_input_file(INPUT_FILE)
    df_order = df_order[['PRODUCT','ORDER','STATION']].drop_duplicates().dropna()
    #remove duplicates, empty fields and filter out the chemical products
    df_order = df_order[df_order['STATION']!='01.Z8']
    df_order.loc[df_order['STATION'] == '01.GE4', 'STATION'] = '01.E4'
    df_order.rename(columns={'PRODUCT':'Product'}, inplace=True)
    df_order = reduce_mem_usage(df_order)

    #fix the staation id of products that are assigned in multiple stations
    #Calculate the unique number of product per station
    unique_counts_old = df_order[['Product','STATION']].groupby('Product')['STATION'].nunique().reset_index(name='numb_stat_per_prod')
    #Merging the count back to the original dataframe
    df_order = df_order.merge(unique_counts_old, on='Product', how='left')

    #Updating the product assignment with the last station they correspond
    # Step 1: Identify products with numb_stat_per_prod > 1.
    products_with_multiple_stations = df_order[df_order['numb_stat_per_prod'] > 1]['Product'].unique()

    # Step 2: For these products, find the maximum order ID and the corresponding station ID.
    max_order_stations = df_order[df_order['Product'].isin(products_with_multiple_stations)] \
        .sort_values(by='ORDER', ascending=False) \
        .drop_duplicates(subset=['Product'], keep='first')[['Product', 'STATION']]

    # Step 3: Update the station ID for all occurrences of these products.
    # First, merge this information back to the original df_order.
    df_order = df_order.merge(max_order_stations, on='Product', how='left', suffixes=('', '_max_order'))

    # If STATION_max_order is not NaN (i.e., for products with multiple stations), update the STATION column.
    df_order['STATION'] = df_order.apply(lambda x: x['STATION_max_order'] if pd.notna(x['STATION_max_order']) else x['STATION'], axis=1)

    # Drop the temporary STATION_max_order column as it's no longer needed.
    df_order.drop(columns=['STATION_max_order'], inplace=True)

    return df_order

#filter the data we need to process 
def filter_data_to_process(df_order):
    df_order_1 = df_order.copy()
    df_order_1['cnt'] = df_order_1[['Product','ORDER']].groupby('ORDER').transform('count')
    df_order_1 = df_order_1[df_order_1['cnt']>1][['ORDER','Product']]
    return df_order_1

#calculate the total stations of the initial solution
def calculate_total_stations_initial(df_order):
    df_order_s1 = df_order[['STATION','ORDER']].drop_duplicates()
    df_order_s1['cnt'] = df_order_s1.groupby('ORDER').transform('count')
    df_order_s1 = df_order_s1[['ORDER','cnt']].drop_duplicates()
    s1 = df_order_s1['cnt'].sum()
    m1 = df_order_s1['cnt'].mean()
    return s1,m1
# # Creating the list of total combinations
 
#creating the big list of all combination of 2 pairs of products from all orders in the dataframe
def combinations_dataframe(df_order_1):
    sets_tmp = df_order_1.groupby('ORDER')['Product'].progress_apply(lambda x : list(itertools.permutations(x, 2))).explode().tolist()
    sets = pd.DataFrame(sets_tmp)
    sets.rename(columns={0:'p1', 1:'p2'}, inplace=True)
    #remove pairs of products with themselfs
    sets = sets[~(sets['p1']==sets['p2'])]
    return sets



# ### PREPROCESS
def preprocess(sets,MIN_FREQ_PREPROC,RATIO_TO_KEEP,NAME_OF_RUN):
    #count the occurance of products in column p1
    sets['cnt_left'] = sets.groupby('p1').transform('count')
    #count the occurrance of the pair
    sets['cnt'] = sets.groupby(['p1','p2']).transform('count')
    #calculate the ratio of the number of times the pair appears divided by the number of times product on p1 appears
    sets['freq_ratio'] = sets['cnt']/sets['cnt_left']
    #get rid of the pairs which are not present enough times and their ratio is below required ratio
    sets_to_keep = sets[(sets['cnt_left']>MIN_FREQ_PREPROC)&(sets['freq_ratio']>=RATIO_TO_KEEP)]
    #sort in descending order of freq_ratio
    sets_to_keep.sort_values('freq_ratio', ascending=False, inplace=True)
    sets=sets[['p1', 'p2','cnt']]
    #save the file
    sets_to_keep.to_csv(NAME_OF_RUN+'_'+'preprocess_connectivity_couples.csv')
    return sets_to_keep


# ### PROCESS
def format_data_for_main_process(sets,MIN_FREQ):
    #keep only one order of pair
    sets_new = sets[sets['p1']<sets['p2']].drop_duplicates()
    #sort in descending order of pair count
    sets_new.sort_values('cnt', ascending=False, inplace=True)
    #filter to get only product that are above the threshold
    sets_new=sets_new[sets_new['cnt']>=MIN_FREQ]
    return sets_new


def main_procees(sets,MIN_FREQ,MAXIMUM_NUMBER_OF_PRODUCT_PER_COMMUNITY):
    #read the pairs entering to the main process
    sets_new = format_data_for_main_process(sets,MIN_FREQ)
    #dictionary to save the subsets
    paths = {'path':[]}
    #keep track of the process with tqdm
    cur_leng = len(sets_new)
    pbar = tqdm(total=len(sets_new))
    #start looping until all pairs are processed and dataframe becomes empty
    while (len(sets_new)>0):
        #start with the max weight pair (first index on dataframe since dataframe is sorted)
        max_edge_row = sets_new.iloc[0]
        #to make sure we don't get the same row over and over again
        sets_new.drop(sets_new.index[0], inplace=True)
        #forming the subset through this path variable
        path=[max_edge_row['p1'], max_edge_row['p2']]
        #variable to keep track when to get out of the second while loop
        test_v =True    
        while test_v:
            # Find the neighbors of the nodes of the current path
            nbr_tmp = sets_new[
                    (sets_new['p1'].isin(path)) | 
                    (sets_new['p2'].isin(path))
                ].head(1)
            #drop the neighbor from the dataframe
            sets_new.drop(nbr_tmp.index, inplace=True)
            # break adding values to the path if it can't find a neighbor 
            if nbr_tmp.empty or len(path)>=MAXIMUM_NUMBER_OF_PRODUCT_PER_COMMUNITY:
                
                test_v =False
            else:
                #add the new node (product) to the path
                node = nbr_tmp['p1'].values[0] if nbr_tmp['p2'].values[0] in path else nbr_tmp['p2'].values[0]
                #check for the following neighbor of the node
                other_nbr = sets_new[
                    (sets_new['p1']==node) | 
                    (sets_new['p2']==node)
                ].head(1)
                #check if the node we are adding is the last node that can enter in the community, 
                # if so check if the connection of the last node to be added with its following neighbor (MAXIMUM_NUMBER_OF_PRODUCT_PER_COMMUNITY +1 ) is stronger then the current connection (MAXIMUM_NUMBER_OF_PRODUCT_PER_COMMUNITY - 1)
                #if yes then break here and don't add the last neighbor in this community
                if len(path)+1==MAXIMUM_NUMBER_OF_PRODUCT_PER_COMMUNITY and len(other_nbr)>0 and other_nbr['cnt'].values[0]>nbr_tmp['cnt'].values[0]:
                    test_v = False
                #adding up the respective node neighbor to the path
                else:
                    path.append(node)      
                    #remove the added node from the path                    
                    mask = ~(((sets_new['p1']==node) & (sets_new['p2'].isin(path)))|
                        ((sets_new['p2']==node) & (sets_new['p1'].isin(path))))
                    sets_new = sets_new[mask]
                    #update the tqdm process
                    counter = cur_leng - len(sets_new)
                    cur_leng = len(sets_new)
                    pbar.update(counter)


        # Remove the nodes added to the path
        mask = ~((sets_new['p1'].isin(path)) | (sets_new['p2'].isin(path)))
        sets_new = sets_new[mask]
        # Creating the list of paths(our subsets of products)
        paths['path'].append(path)
        #update the tqdm process
        counter = cur_leng - len(sets_new)
        cur_leng = len(sets_new)
        pbar.update(counter)
        
    pbar.close()
    #transform the community dictionary into a data frame
    community_df = pd.DataFrame({'Product' : [], 'Community' : []})
    index1=0
    for pa in paths['path']:
        for pr in pa:
            community_df=pd.concat([community_df,pd.DataFrame({'Product': [pr], 'Community': [index1]})])
        index1+=1  
    return community_df,index1


# ### POSTPROCESS

def postprocess(sets,MAXIMUM_NUMBER_OF_PRODUCT_PER_COMMUNITY,MIN_FREQ,MIN_FREQ_PREPROC,RATIO_TO_KEEP,NAME_OF_RUN):
    #get sets generated from the preprocess
    sets_to_keep = preprocess(sets,MIN_FREQ_PREPROC,RATIO_TO_KEEP,NAME_OF_RUN)
    #get the community data frame formed in the main process and its last index community 
    community_df,index1 = main_procees(sets,MIN_FREQ,MAXIMUM_NUMBER_OF_PRODUCT_PER_COMMUNITY)
    #track the process
    pbar = tqdm(total=len(sets_to_keep))
    #start looping until all pairs in the preprocess that are not included in the main process are processed and dataframe becomes empty
    while len(sets_to_keep)>0:
        #start with the highest weight pair in sets_to_keep (first element since it is ordered)
        cur_edge = sets_to_keep.head(1)
        ##this check is because in the main process we have already checked the direction p1;p2 and now we are checking only the direction p2;p1 with a relative strong relation    
        #check if the second product of the pair (column p2) is already in any community
        if len(community_df[community_df['Product']==cur_edge['p2'].values[0]])>0:
            #check if first product in the pair (column p1) is not in any community, if so add product in p1 add the community where the product p2 is
            if len(community_df[community_df['Product']==cur_edge['p1'].values[0]])==0:
                community_df=pd.concat([community_df, pd.DataFrame({'Product': [cur_edge['p1'].values[0]],
                    'Community': [community_df[community_df['Product']==cur_edge['p2'].values[0]]['Community'].values[0]]})])            
            #else:
                #that can't happen
        #check the case where second product of the pair (column p2) not in any community
        else:
            #check if the first product of the pair (column p1) is allready in a community,if so add product in p2 add the community where the product p1 is
            if len(community_df[community_df['Product']==cur_edge['p1'].values[0]])>0:
                community_df=pd.concat([community_df, pd.DataFrame({'Product': [cur_edge['p2'].values[0]],
                    'Community': [community_df[community_df['Product']==cur_edge['p1'].values[0]]['Community'].values[0]]})])            
            
            #if none of the products in the pair are not part of a communiyt, then they form a new community together
            else:
                community_df=pd.concat([community_df, pd.DataFrame({'Product': [cur_edge['p1'].values[0]],
                                                'Community': [index1]})])
                community_df=pd.concat([community_df, pd.DataFrame({'Product': [cur_edge['p2'].values[0]],
                                            'Community': [index1]})])
            index1 += 1
        sets_to_keep.drop(cur_edge.index, inplace=True)
        pbar.update(1)
    pbar.close()     
    #print(community_df)
    return community_df
    
#calculate the majority stations we are going to put the products of a community
def calculate_the_new_assignment(community_df,df_com_stat):
    df_com_stat['MAJ_STAT'] = df_com_stat[['Community','STATION']].groupby('Community').transform(lambda x: x.mode().values[0])
    df_com_stat_maj = df_com_stat[['Community','MAJ_STAT']].drop_duplicates()
    df_prod_maj = community_df.merge(df_com_stat_maj, on='Community')[['Product','MAJ_STAT']].drop_duplicates()
    return df_prod_maj

#produce the new data frame with the new mapping of assignment of products
def produce_the_new_assignment(df_order,df_prod_maj):
    df_order_2 = df_order.merge(df_prod_maj, on='Product', how='left')
    df_order_2['MAJ_STAT'] = df_order_2['MAJ_STAT'].fillna(df_order_2['STATION'])
    return df_order_2

#calculate the total stations of the initial solution
def calculate_total_stations_new(df_order_2):
    df_order_s2 = df_order_2[['ORDER', 'MAJ_STAT']].drop_duplicates()
    df_order_s2['cnt'] = df_order_s2.groupby('ORDER').transform('count')
    df_order_s2 = df_order_s2[['ORDER','cnt']].drop_duplicates()
    s2 = df_order_s2['cnt'].sum()
    m2 = df_order_s2['cnt'].mean()
    return s2, m2

#GRAPH that presents on how many stations each set passes
def graph_visual1(df_order,community_df,INPUT_FILE,NAME_OF_RUN):
    df_com_stat = community_df.copy()
    #read the input file to keep track of the stations
    df_stat = df_order[['Product','STATION']].drop_duplicates()
    #keep as assignment the last station a product appears
    df_stat['STATION'] = df_stat.groupby('Product').transform('last')
    #merge station and comminities
    df_com_stat = df_com_stat.merge(df_stat, on='Product',how='left')
    df_com_stat = df_com_stat[['Community','STATION']].drop_duplicates()
    #count stations for each community
    df_com_stat['cnt'] = df_com_stat.groupby('Community').transform('count')
    tmp = df_com_stat[['Community','cnt']].drop_duplicates()['cnt'].value_counts(dropna=False)
    plt.figure(figsize=(10, 5))
    plt.xlabel('Number of stations')
    plt.ylabel('Number of sets')
    plt.title('Number of sets per station number')
    plt.bar(tmp.index, tmp.values)
    plt.savefig(NAME_OF_RUN+'_'+'number_of_sets_per_number_of_stations.jpg')
    return df_com_stat

#GRAPH that presents the number of lines per community and the color presents the number of products in each community
def graph_visual2(community_df,INPUT_FILE,NAME_OF_RUN):
    #count products for each community
    community_df['cnt'] = community_df.groupby('Community')['Product'].transform('count')
    #read the input file to keep track of the orders
    df_line = read_input_file(INPUT_FILE)
    df_line.rename(columns={'PRODUCT' : 'Product'}, inplace=True)
    #merge orders and communities
    df_line = df_line.merge(community_df, on='Product', how='left')
    #counting the number of lines
    df_line['cnt'] = df_line[['Community','Product']].groupby('Community').transform('count')
    #Keeping track of the number of products for community saving it as cnt_prod
    df_tmp1 = community_df[['Community','cnt']].drop_duplicates()
    df_tmp1.rename(columns={'cnt':'cnt_prod'}, inplace=True)
    #form the final dataframe to plot with the information for each commuinty on the number of lines and number of products on that commuinty
    df_line = df_line.merge(df_tmp1, on='Community')
    df_to_plot = df_line[['Community', 'cnt', 'cnt_prod']].drop_duplicates().sort_values('cnt').reset_index(drop=True)
    #presenting in colors the number of products on each community
    cmap = cm.rainbow
    norm = Normalize(vmin=df_to_plot['cnt_prod'].min(), vmax=df_to_plot['cnt_prod'].max())
    plt.figure(figsize=(10,6))
    #potting the the number of lines per community
    plt.bar(df_to_plot.index,df_to_plot['cnt'], color=cmap(norm(df_to_plot['cnt_prod'])))
    plt.xlabel('Communitiy indexes')
    plt.ylabel('Number of lines')
    plt.title('Number of lines for each set index')
    plt.savefig(NAME_OF_RUN+'_'+'number_of_lines_per_sets.jpg')



def graph_comparisson_plot(indices,all_indices,tmp,tmp2,NAME_OF_RUN,NAME_OF_FILE, NAME_OF_GRAPH,NAME_OF_X,NAME_OF_Y):
    # Set up the figure and axis
    plt.figure(figsize=(10, 5))
    ax = plt.gca()

    # Width of the bars
    width = 0.35

    # Plotting
    rects1 = ax.bar(indices - width/2, tmp, width, label='OLD', alpha=0.6)
    rects2 = ax.bar(indices + width/2, tmp2, width, label='NEW', alpha=0.6)

    # Add labels and title
    plt.xlabel(NAME_OF_X)
    plt.ylabel(NAME_OF_Y)
    plt.title(NAME_OF_GRAPH)

    # Add x-ticks and labels
    plt.xticks(indices, all_indices, rotation=45)
    # Add a legend
    plt.legend()
    plt.savefig(NAME_OF_RUN+'_'+NAME_OF_FILE)


def graph_visual3(df_order_2,NAME_OF_RUN):
    tmp = df_order_2[['ORDER','STATION']].drop_duplicates()
    #count number of stations per order (OLD)
    tmp['cnt'] = tmp.groupby('ORDER').transform('count')
    #make as index the count of stations and as its value the number of orders that pass through this respective count of stations (OLD)
    tmp = tmp[['ORDER','cnt']].drop_duplicates()['cnt'].value_counts(dropna=False)

    tmp2 = df_order_2[['ORDER','MAJ_STAT']].drop_duplicates()
    #count number of stations per order (NEW)
    tmp2['cnt'] = tmp2.groupby('ORDER').transform('count')
    #make as index the count of stations and as its value the number of orders that pass through this respective count of stations (NEW)
    tmp2 = tmp2[['ORDER','cnt']].drop_duplicates()['cnt'].value_counts(dropna=False)
    # Align the indices
    all_indices = sorted(set(tmp.index) | set(tmp2.index))  # Union of indices from both datasets
    # Positions for the bars
    indices = np.arange(len(all_indices))
    tmp = tmp.reindex(all_indices).fillna(0)  # Reindex and fill missing values with 0
    tmp2 = tmp2.reindex(all_indices).fillna(0)  # Reindex and fill missing values with 0
    NAME_OF_FILE = 'number_of_orders_per_number_of_stations.png'
    NAME_OF_GRAPH = 'Number of Orders per Number of Stations'
    NAME_OF_X = 'Number of Stations'
    NAME_OF_Y = 'Number of Orders'
    graph_comparisson_plot(indices,all_indices,tmp,tmp2,NAME_OF_RUN,NAME_OF_FILE,NAME_OF_GRAPH,NAME_OF_X,NAME_OF_Y)
    
def graph_visual4(df_order_2,NAME_OF_RUN):
    df_order_last_plot = df_order_2.copy() 
    df_order_last_plot['cnt_lines_MAJ'] = df_order_last_plot[['Product','MAJ_STAT']].groupby('MAJ_STAT').transform('count')
    df_order_last_plot['cnt_lines'] = df_order_2[['Product','STATION']].groupby('STATION').transform('count')
    tmp_final = df_order_last_plot[['MAJ_STAT','cnt_lines_MAJ']].drop_duplicates()
    tmp_final.rename(columns={'MAJ_STAT':'STATION'}, inplace=True)
    tmp_final = tmp_final.merge(df_order_last_plot[['STATION','cnt_lines']].drop_duplicates(), on='STATION', how='outer')
    tmp_final.sort_values('cnt_lines', inplace=True)
    # Positions for the bars
    all_indices = tmp_final['STATION'].astype(str).values
    indices = np.arange(len(all_indices))
    NAME_OF_FILE ='number_of_lines_per_station.png'
    NAME_OF_GRAPH = 'Number of Lines per Station Index'
    NAME_OF_Y = 'Number of Lines'
    NAME_OF_X = 'Station Name'
    graph_comparisson_plot(indices,all_indices,tmp_final['cnt_lines'], tmp_final['cnt_lines_MAJ'],NAME_OF_RUN,NAME_OF_FILE,NAME_OF_GRAPH,NAME_OF_X,NAME_OF_Y)

def graph_visual5(df_order_2,NAME_OF_RUN):
    df_order_last_plot_2 = df_order_2.copy() 
    df_order_last_plot_2['cnt_refs_MAJ'] = df_order_last_plot_2[['Product','MAJ_STAT']].groupby('MAJ_STAT').transform('nunique')
    df_order_last_plot_2['cnt_refs'] = df_order_2[['Product','STATION']].groupby('STATION').transform('nunique')
    tmp_final_2 = df_order_last_plot_2[['MAJ_STAT','cnt_refs_MAJ']].drop_duplicates()
    tmp_final_2.rename(columns={'MAJ_STAT':'STATION'}, inplace=True)
    tmp_final_2 = tmp_final_2.merge(df_order_last_plot_2[['STATION','cnt_refs']].drop_duplicates(), on='STATION', how='outer')
    tmp_final_2.sort_values('cnt_refs', inplace=True)
    #print(tmp_final_2)
    # Positions for the bars
    all_indices = tmp_final_2['STATION'].astype(str).values
    indices = np.arange(len(all_indices))
    NAME_OF_FILE = 'number_of_refs_per_station.png'
    NAME_OF_GRAPH = 'Number of Products on each Station'
    NAME_OF_Y = 'Number of References'
    NAME_OF_X = 'Stations Name'
    graph_comparisson_plot(indices,all_indices,tmp_final_2['cnt_refs_MAJ'], tmp_final_2['cnt_refs'],NAME_OF_RUN,NAME_OF_FILE,NAME_OF_GRAPH,NAME_OF_X,NAME_OF_Y)


#final output
def generate_final_output(INPUT_FILE,NAME_OF_RUN,MAXIMUM_NUMBER_OF_PRODUCT_PER_COMMUNITY,MIN_FREQ,MIN_FREQ_PREPROC,RATIO_TO_KEEP):    
    print('Process started')
    tqdm.pandas()
    directory = os.path.dirname(NAME_OF_RUN)
    # Check if the directory exists, and create it if not
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(directory,'created')
    
    #read the input file
    df_order = prepare_order_data(INPUT_FILE)
    #Filter input data
    df_order_1 = filter_data_to_process(df_order)
    #generate all the sets possiblebased on the orderes
    sets = combinations_dataframe(df_order_1)
    #generate the final dataframe of sets
    community_df=postprocess(sets,MAXIMUM_NUMBER_OF_PRODUCT_PER_COMMUNITY,MIN_FREQ,MIN_FREQ_PREPROC,RATIO_TO_KEEP,NAME_OF_RUN)
    #save it to the corresponding directory with the other files
    community_df[['Product','Community']].to_csv(NAME_OF_RUN+'_'+'sets.csv')
    #make a dataframme holding the infomration on the parameters used in the current run and save it to the directory with the other files
    pd.DataFrame({'MAXIMUM_NUMBER_OF_PRODUCT_PER_COMMUNITY' : [MAXIMUM_NUMBER_OF_PRODUCT_PER_COMMUNITY],
             'MIN_NUMBER_OF_TIME_A_PRODUCT_APPEARS_IN_HISTORICAL_DATA_TO_BE_KEPT' : [MIN_FREQ],
             'MIN_NUMBER_OF_TIME_A_PRODUCT_APPEARS_IN_HISTORICAL_DATA_TO_BE_KEPT_FOR_PREPROCESS' : [MIN_FREQ_PREPROC],
             'RATIO_TO_CONSIDER_STRONG_CONNEXITY_IN_PREPROCESS':[RATIO_TO_KEEP]}).to_csv(NAME_OF_RUN+'_'+'parameters.csv')

    #produce the new assignment solution
    df_com_stat = graph_visual1(df_order,community_df,INPUT_FILE,NAME_OF_RUN)
    df_prod_maj = calculate_the_new_assignment(community_df,df_com_stat)
    df_order_2 = produce_the_new_assignment(df_order,df_prod_maj)
    #calculate the initial total stations orders pass through
    s1,m1 = calculate_total_stations_initial(df_order)
    #calculate the new total stations orders pass through
    s2,m2 =calculate_total_stations_new(df_order_2)
    print('s1', s1, 'm1',m1)
    print('s2', s2, 'm2',m2)
    
    #save the graph plots in the corresponding directory with the other files
    graph_visual2(community_df,INPUT_FILE,NAME_OF_RUN)
    graph_visual3(df_order_2,NAME_OF_RUN)
    graph_visual4(df_order_2,NAME_OF_RUN)
    graph_visual5(df_order_2,NAME_OF_RUN)





