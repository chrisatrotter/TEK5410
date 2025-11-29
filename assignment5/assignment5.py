#!/usr/bin/env python3
import pulp
import pandas as pd

# ------------------------------------------------------------------
# 1. Load data
# ------------------------------------------------------------------
raw_data = pd.read_csv('baseline_data.csv')
hours = range(len(raw_data))
nodes = ['north', 'south']
technologies = ['wind', 'solar', 'gas', 'batt']   # batt = storage
storage_tech = ['batt']

# ------------------------------------------------------------------
# 2. Parameters
# ------------------------------------------------------------------
demand_scale = {'north': 0.8, 'south': 1.2}
wind_scale   = {'north': 1.2, 'south': 0.6}
solar_scale  = {'north': 0.8, 'south': 1.5}

a    = {'wind':67.653, 'solar':48.140, 'gas':52.041, 'batt':80+320/4}
vom  = {'wind':2.3,   'solar':0.01,  'gas':4.0,   'batt':0.0}
fuel = {'wind':0.0,   'solar':0.0,   'gas':21.6,  'batt':0.0}
eta  = {'batt':0.9}
dur  = {'batt':4}

# CO₂ intensity (tCO₂/MWh) – constant for gas, 0 for others
co2_intensity = {
    'wind': 0.0,
    'solar':0.0,
    'gas'  : raw_data['co2_gas'].iloc[0],
    'batt' : 0.0
}

# Transmission
tx_cost = 30.0                     # €/MW
tx_cap  = pulp.LpVariable("CAP_TX", lowBound=0)
flow    = {h: pulp.LpVariable(f"FLOW_{h}", lowBound=-1e6, upBound=1e6) for h in hours}

# ------------------------------------------------------------------
# 3. Model
# ------------------------------------------------------------------
prob = pulp.LpProblem("TwoNode_System", pulp.LpMinimize)

# Variables
CAP     = {(t,n): pulp.LpVariable(f"CAP_{t}_{n}", lowBound=0) for t in technologies for n in nodes}
GEN     = {(t,n,h): pulp.LpVariable(f"GEN_{t}_{n}_{h}", lowBound=0) for t in technologies for n in nodes for h in hours}
CHARGE  = {(n,h): pulp.LpVariable(f"CHARGE_{n}_{h}", lowBound=0) for n in nodes for h in hours}
DISCHARGE = {(n,h): pulp.LpVariable(f"DISCHARGE_{n}_{h}", lowBound=0) for n in nodes for h in hours}
STO     = {(n,h): pulp.LpVariable(f"STO_{n}_{h}", lowBound=0) for n in nodes for h in hours}

# ------------------------------------------------------------------
# 4. Objective
# ------------------------------------------------------------------
prob += (
    pulp.lpSum(a[t]*CAP[t,n] for t in technologies for n in nodes) +
    tx_cost*tx_cap +
    pulp.lpSum((vom[t]+fuel[t])*GEN[t,n,h] for t in technologies for n in nodes for h in hours)
), "TotalSystemCost"

# ------------------------------------------------------------------
# 5. Energy balance (per node & hour)
# ------------------------------------------------------------------
for n in nodes:
    for h in hours:
        demand   = raw_data.loc[h, 'demand'] * demand_scale[n]
        cf_wind  = raw_data.loc[h, 'cf_wind']  * wind_scale[n]
        cf_solar = raw_data.loc[h, 'cf_solar'] * solar_scale[n]

        net_flow = flow[h] if n == 'south' else -flow[h]

        prob += (
            GEN['wind',n,h] + GEN['solar',n,h] + GEN['gas',n,h] +
            DISCHARGE[n,h] + net_flow
            == demand + CHARGE[n,h],
            f"Balance_{n}_{h}"
        )

        # Generation limits
        prob += GEN['wind',n,h]  <= CAP['wind',n]  * cf_wind
        prob += GEN['solar',n,h] <= CAP['solar',n] * cf_solar
        prob += GEN['gas',n,h]   <= CAP['gas',n]

        # Battery power limit (charge + discharge ≤ capacity)
        prob += CHARGE[n,h] + DISCHARGE[n,h] <= CAP['batt',n]

# ------------------------------------------------------------------
# 6. Storage dynamics
# ------------------------------------------------------------------
for n in nodes:
    # Initial SOC = 0
    prob += STO[n,0] == 0, f"STO_init_{n}"

    for h in hours:
        # SOC transition
        if h == 0:
            prev = STO[n, hours[-1]]   # wrap-around (optional)
        else:
            prev = STO[n, h-1]

        prob += STO[n,h] == prev + eta['batt']*CHARGE[n,h] - DISCHARGE[n,h], f"SOC_{n}_{h}"

        # Energy capacity limit (4-hour battery)
        prob += STO[n,h] <= dur['batt'] * CAP['batt',n]

# ------------------------------------------------------------------
# 7. Transmission limits
# ------------------------------------------------------------------
for h in hours:
    prob += flow[h] <= tx_cap
    prob += flow[h] >= -tx_cap

# ------------------------------------------------------------------
# 8. Solve
# ------------------------------------------------------------------
prob.solve()
print("Status:", pulp.LpStatus[prob.status])
total_cost = pulp.value(prob.objective)
print("Total cost (M€):", total_cost)
print("Transmission capacity (MW):", tx_cap.varValue)

# ------------------------------------------------------------------
# 9. CO₂ emissions (only from gas)
# ------------------------------------------------------------------
total_co2 = sum(
    co2_intensity['gas'] * GEN['gas', n, h].varValue
    for n in nodes for h in hours
) / 1000.0
print("Total CO₂ emissions (kt):", total_co2)

# ------------------------------------------------------------------
# 10. Export results
# ------------------------------------------------------------------
results = []

# --- Capacities ---
for t in technologies:
    for n in nodes:
        results.append({
            'Type': 'Capacity',
            'Technology': t,
            'Node': n,
            'Hour': '-',
            'Value': CAP[t,n].varValue
        })

# --- Generation, charge, discharge, SOC, flow ---
for h in hours:
    # Generation (including battery discharge)
    for t in technologies:
        for n in nodes:
            results.append({
                'Type': 'Generation',
                'Technology': t,
                'Node': n,
                'Hour': h,
                'Value': GEN[t,n,h].varValue
            })

    # Battery charge & discharge
    for n in nodes:
        results.append({
            'Type': 'Charge',
            'Technology': 'batt',
            'Node': n,
            'Hour': h,
            'Value': CHARGE[n,h].varValue
        })
        results.append({
            'Type': 'Discharge',
            'Technology': 'batt',
            'Node': n,
            'Hour': h,
            'Value': DISCHARGE[n,h].varValue
        })
        results.append({
            'Type': 'Storage',
            'Technology': 'batt',
            'Node': n,
            'Hour': h,
            'Value': STO[n,h].varValue
        })

    # Transmission flow
    results.append({
        'Type': 'Flow',
        'Technology': 'TX',
        'Node': 'North-South',
        'Hour': h,
        'Value': flow[h].varValue
    })

# --- Transmission capacity ---
results.append({
    'Type': 'TransmissionCapacity',
    'Technology': 'TX',
    'Node': 'North-South',
    'Hour': '-',
    'Value': tx_cap.varValue
})

# --- Totals ---
results.append({'Type': 'COST', 'Technology': '-', 'Node': '-', 'Hour': '-', 'Value': total_cost})
results.append({'Type': 'CO2',  'Technology': '-', 'Node': '-', 'Hour': '-', 'Value': total_co2})

pd.DataFrame(results).to_csv('assignment5_results.csv', index=False)
print("Results written to assignment5_results.csv")