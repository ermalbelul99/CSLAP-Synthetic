import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from matplotlib.patches import Rectangle
import matplotlib.ticker as ticker
import os

# Set working directory to the data location
os.chdir(r'c:\Users\ebelul\Downloads\CSLAP_Project_All')

# Set seaborn theme for academic plotting
sns.set_theme(style="whitegrid")

# Define all methods in a specific order
methods = ['Heuristic', 'Feasible Start', 'MILP Gurobi', 'MILP Hexaly', 
           'CG Gurobi', 'CG Hexaly', 'SA-C', 'GA']

cb = sns.color_palette("colorblind", 10)

# Map styles - Ensure Heuristic is distinctly red and others are colorblind-friendly
color_map = {
    'Heuristic': '#E31A1C',   # Distinct Red
    'Feasible Start': cb[0],  # Blue
    'MILP Gurobi': cb[1],     # Orange
    'MILP Hexaly': cb[2],     # Green
    'CG Gurobi': cb[4],       # Purple
    'CG Hexaly': cb[5],       # Brown
    'SA-C': cb[7],            # Grey
    'GA': cb[9]               # Cyan
}

marker_map = {
    'Heuristic': 'X',
    'Feasible Start': 'o',
    'MILP Gurobi': 's',
    'MILP Hexaly': 'D',
    'CG Gurobi': '^',
    'CG Hexaly': 'v',
    'SA-C': '<',
    'GA': '>'
}

linestyle_map = {
    'Heuristic': '--',
    'Feasible Start': '-',
    'MILP Gurobi': '-',
    'MILP Hexaly': '-',
    'CG Gurobi': '-',
    'CG Hexaly': '-',
    'SA-C': '-',
    'GA': '-'
}

# 1. Load Data
files = ['results_syn_50sku.csv', 'results_syn_500sku.csv', 'results_syn_1000sku.csv', 'results_syn_2000sku.csv']
dfs = []
for f in files:
    try:
        df_part = pd.read_csv(f)
        dfs.append(df_part)
    except FileNotFoundError:
        print(f"Warning: File {f} not found.")

df = pd.concat(dfs, ignore_index=True)

# Clean and convert columns
df.replace('-', np.nan, inplace=True)
for col in ['time', 'visits', 'workload_std_dev', 'num_skus']:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# 2. Setup Figure
fig, axes = plt.subplots(1, 2, figsize=(15, 6), dpi=300)

# ==========================================
# Graph 1: Scalability Ceiling
# ==========================================
ax1 = axes[0]
for method in methods:
    df_m = df[df['Method'] == method].sort_values('num_skus')
    if df_m.empty:
        continue
    # Dropna to naturally break the line when missing
    df_m_clean = df_m.dropna(subset=['time'])
    
    ax1.plot(df_m_clean['num_skus'], df_m_clean['time'], 
             color=color_map[method], marker=marker_map[method], 
             linestyle=linestyle_map[method], linewidth=2.5, markersize=8, 
             label=method)

ax1.set_yscale('log')
ax1.set_xscale('log')
scales = [50, 500, 1000, 2000]
ax1.set_xticks(scales)
ax1.get_xaxis().set_major_formatter(ticker.ScalarFormatter())

# Formatting labels and titles
ax1.set_xlabel('Problem Scale (Number of SKUs)', fontsize=12, fontweight='bold')
ax1.set_ylabel('Computation Time (seconds) [Log Scale]', fontsize=12, fontweight='bold')
ax1.set_title('Computational Scalability by Approach', fontsize=14, fontweight='bold', pad=15)

# ==========================================
# Graph 2: Pareto Trade-off
# ==========================================
ax2 = axes[1]
df_2000 = df[df['num_skus'] == 2000].dropna(subset=['workload_std_dev', 'visits']).copy()

plotted_points = {}

for method in methods:
    m_data = df_2000[df_2000['Method'] == method]
    if m_data.empty:
        continue
    ax2.scatter(m_data['workload_std_dev'], m_data['visits'], 
                color=color_map[method], marker=marker_map[method], 
                s=150, zorder=5, edgecolors='black', linewidth=0.5)
    
    # Text Annotation
    for _, row in m_data.iterrows():
        m_name = row['Method']
        x, y = row['workload_std_dev'], row['visits']
        
        # Identify unique coordinate key (rounded relative to graph limits to avoid small diffs)
        coord_key = (round(x, 1), round(y, 1))
        
        # Count how many points are at this exact coordinate
        offset_y = 0
        if coord_key in plotted_points:
            offset_y = -14 * plotted_points[coord_key]
            plotted_points[coord_key] += 1
        else:
            plotted_points[coord_key] = 1
            
        ax2.annotate(m_name, 
                     (x, y),
                     xytext=(10, offset_y), textcoords='offset points',
                     fontsize=9, weight='bold',
                     verticalalignment='center' if offset_y == 0 else 'top', zorder=10)

ax2.set_xlabel('Workload Standard Deviation (Spreadness)', fontsize=12, fontweight='bold')
ax2.set_ylabel('Total Station Visits (Objective)', fontsize=12, fontweight='bold')
ax2.set_title('Pareto Trade-off Analysis (2000 SKUs)', fontsize=14, fontweight='bold', pad=15)

# Shade the "Ideal" quadrant
# We will explicitly draw from the plot minimums
ax2.figure.canvas.draw()
xmin, xmax = ax2.get_xlim()
ymin, ymax = ax2.get_ylim()

width = (xmax - xmin) * 0.5
height = (ymax - ymin) * 0.5

# Ensure rectangle acts as a visually distinct "quadrant" shading
rect = Rectangle((xmin, ymin), width, height, 
                 linewidth=0, facecolor='#2ca02c', alpha=0.15, zorder=0)
ax2.add_patch(rect)
# Add small label for ideal quadrant
ax2.text(xmin + width*0.05, ymin + height*0.05, "Ideal Region\n(Low Visits & Variance)", 
         fontsize=10, color='darkgreen', weight='bold', alpha=0.8)

# Ensure limits remain fixed if the rectangle pushed them
ax2.set_xlim(xmin, xmax)
ax2.set_ylim(ymin, ymax)

# ==========================================
# Unified Legend
# ==========================================
handles, labels = ax1.get_legend_handles_labels()
fig.legend(handles, labels, loc='lower center', bbox_to_anchor=(0.5, -0.05), 
           ncol=4, fontsize=11, frameon=True, shadow=True, fancybox=True)

plt.tight_layout()
plt.subplots_adjust(bottom=0.2) # Provide ample room for legend

# Save the plot
output_file = 'plot_algorithm_benchmarks.png'
plt.savefig(output_file, dpi=300, bbox_inches='tight')
print(f"Plot successfully saved to {os.path.abspath(output_file)}")
