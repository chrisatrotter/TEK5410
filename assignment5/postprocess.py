#!/usr/bin/env python3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

sns.set_style("whitegrid")
plt.rcParams['font.size'] = 11

# -------------------------------------------------
# 1) Load CSV
# -------------------------------------------------
csv_file = "assignment5_results.csv"
if not os.path.exists(csv_file):
    raise FileNotFoundError(f"{csv_file} not found!")

df = pd.read_csv(csv_file)
df.columns = [c.strip() for c in df.columns]
print(f"Loaded {len(df)} rows from {csv_file}")

# -------------------------------------------------
# 2) Extract data
# -------------------------------------------------
# --- Capacities ---
cap_df = df[df['Type'].str.strip() == 'Capacity'].copy()
if cap_df.empty:
    raise ValueError("No capacity data found!")
cap_pivot = cap_df.pivot(index='Technology', columns='Node', values='Value').fillna(0)
cap_pivot = cap_pivot.reindex(columns=['north', 'south'], fill_value=0)

# --- Transmission capacity ---
tx_row = df[df['Type'].str.strip() == 'TransmissionCapacity']
tx_cap = tx_row['Value'].iloc[0] if not tx_row.empty else 5000  # default

# --- Flow ---
flow_df = df[df['Type'].str.strip() == 'Flow'].copy()
if not flow_df.empty:
    flow_df['Hour'] = pd.to_numeric(flow_df['Hour'], errors='coerce')
    flow_df = flow_df.dropna(subset=['Hour'])
    flow_df['Hour'] = flow_df['Hour'].astype(int)
    flow = flow_df.set_index('Hour')['Value']
else:
    flow = pd.Series()

# --- Cost & CO₂ ---
cost_row = df[df['Type'].str.strip() == 'COST']
co2_row = df[df['Type'].str.strip() == 'CO2']
cost_val = cost_row['Value'].iloc[0] if not cost_row.empty else np.nan
co2_val = co2_row['Value'].iloc[0] if not co2_row.empty else np.nan

# -------------------------------------------------
# 3) Figure 1: Capacity map (stacked bar) – FIXED LABELING
# -------------------------------------------------
tech_order = ['wind', 'solar', 'gas', 'batt']
tech_labels = {
    'wind': 'Wind',
    'solar': 'Solar',
    'gas': 'Gas',
    'batt': 'Battery'
}
colors = {
    'wind': '#1f77b4',
    'solar': '#ff7f0e',
    'gas': '#2ca02c',
    'batt': '#d62728'
}

fig, ax = plt.subplots(figsize=(8, 5))

# Bottom of each stack
bottom_n = 0.0
bottom_s = 0.0

# First pass: draw the bars (no legend yet)
for tech in tech_order:
    if tech not in cap_pivot.index:
        continue
    n = cap_pivot.loc[tech, 'north']
    s = cap_pivot.loc[tech, 'south']
    ax.bar('North', n, bottom=bottom_n, color=colors[tech])
    ax.bar('South', s, bottom=bottom_s, color=colors[tech])
    bottom_n += n
    bottom_s += s

# Second pass: add a *single* legend entry for each technology
# (use a proxy artist with the correct colour and label)
handles = [plt.Rectangle((0,0),1,1, color=colors[t], label=tech_labels[t]) for t in tech_order
           if t in cap_pivot.index]
ax.legend(handles=handles, title='Technology', loc='upper left', frameon=True)

ax.set_ylabel('Installed Capacity (MW)')
ax.set_title('Optimal Capacity by Region and Technology')
plt.tight_layout()
plt.savefig("capacity_map.pdf", dpi=300, bbox_inches='tight')
plt.close()
print("→ capacity_map.pdf created")

# -------------------------------------------------
# 4) Figure 2: Transmission flow
# -------------------------------------------------
if not flow.empty:
    plt.figure(figsize=(12, 4))
    plt.plot(flow.index, flow.values, label='Flow (North → South)', color='tab:blue', alpha=0.8)
    plt.axhline(tx_cap, color='red', linestyle='--', linewidth=1.5, label=f"Limit: {tx_cap/1000:.1f} GW")
    plt.axhline(-tx_cap, color='red', linestyle='--', linewidth=1.5)
    plt.xlabel("Hour of Year")
    plt.ylabel("Power Flow (MW)")
    plt.title("Hourly Transmission Flow")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("transmission_flow.pdf", dpi=300, bbox_inches='tight')
    plt.close()
    print("→ transmission_flow.pdf created")
else:
    print("Warning: No flow data → transmission_flow.pdf NOT created")

# -------------------------------------------------
# 5) Figure 3: Cost & CO₂ Emissions (dual-axis bar) – FIXED LABELING
# -------------------------------------------------
if pd.notna(cost_val) or pd.notna(co2_val):
    x = np.arange(2)          # 0 = Cost, 1 = CO₂
    width = 0.4               # wider bars for clarity

    fig, ax1 = plt.subplots(figsize=(6, 4.5))

    # ---------- Cost bar ----------
    if pd.notna(cost_val):
        bar1 = ax1.bar(x[0], cost_val, width,
                       label='System Cost', color='#1f77b4')
        ax1.set_ylabel('Total Cost (M€)', color='#1f77b4', fontsize=11)
        ax1.tick_params(axis='y', labelcolor='#1f77b4')
        # value on top
        ax1.text(x[0], cost_val + cost_val*0.02,
                 f"{cost_val:,.0f}", ha='center', va='bottom',
                 fontsize=10, fontweight='bold')

    # ---------- CO₂ bar ----------
    ax2 = ax1.twinx()
    if pd.notna(co2_val):
        bar2 = ax2.bar(x[1], co2_val, width,
                       label='CO₂ Emissions', color='#ff7f0e')
        ax2.set_ylabel('CO₂ Emissions (kt)', color='#ff7f0e', fontsize=11)
        ax2.tick_params(axis='y', labelcolor='#ff7f0e')
        # value on top
        ax2.text(x[1], co2_val + co2_val*0.02,
                 f"{co2_val:,.0f}", ha='center', va='bottom',
                 fontsize=10, fontweight='bold', color='#ff7f0e')

    # ---------- X-axis ----------
    ax1.set_xticks(x)
    ax1.set_xticklabels(['System Cost', 'CO₂ Emissions'])

    # ---------- Title ----------
    ax1.set_title('Total System Cost and CO₂ Emissions', pad=12)

    # ---------- Combined legend ----------
    handles1, labels1 = ax1.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(handles1 + handles2, labels1 + labels2,
               loc='upper center', ncol=2, frameon=True)

    plt.tight_layout()
    plt.savefig("cost_emissions.pdf", dpi=300, bbox_inches='tight')
    plt.close()
    print("→ cost_emissions.pdf created")
else:
    print("Warning: No cost or CO₂ data → cost_emissions.pdf NOT created")
    
print("\nAll done! Check the three PDF figures.")