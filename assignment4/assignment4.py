import pulp
import pandas as pd

#-------------------  INPUT DATA -------------------
raw_data = pd.read_csv('baseline_data.csv', header=0)
hours = range(len(raw_data))
technologies = ['wind', 'solar', 'gas', 'batt']
storage_tech = ['batt']

demand = {h: raw_data.loc[h, 'demand']*1.2 for h in hours}  # +20% demand
cf = {('wind',h): raw_data.loc[h,'cf_wind'] for h in hours}
cf.update({('solar',h): raw_data.loc[h,'cf_solar'] for h in hours})
cf.update({('gas',h): raw_data.loc[h,'cf_gas'] for h in hours})
cf.update({('batt',h): 1.0 for h in hours})

a = {'wind': 67.653, 'solar': 48.140, 'gas': 52.041, 'batt': 80 + 320/4}
vom = {'wind': 2.3, 'solar': 0.01, 'gas': 4.0, 'batt': 0.0}
fuel = {'wind': 0.0, 'solar': 0.0, 'gas': 21.6, 'batt': 0.0}
co2 = {'wind': 0.0, 'solar': 0.0, 'gas': 0.202, 'batt': 0.0}
eta_stor = {'batt': 0.9}
dur_stor = {'batt': 4}

#-------------------  VARIABLES -------------------
prob = pulp.LpProblem("HighRES", pulp.LpMinimize)
CAP = {t: pulp.LpVariable(f"CAP_{t}", lowBound=0) for t in technologies}
GEN = {(t,h): pulp.LpVariable(f"GEN_{t}_{h}", lowBound=0) for t in technologies for h in hours}
CHARGE = {(t,h): pulp.LpVariable(f"CHARGE_{t}_{h}", lowBound=0) for t in storage_tech for h in hours}
STO = {(t,h): pulp.LpVariable(f"STO_{t}_{h}", lowBound=0) for t in storage_tech for h in hours}
STO0 = {t: pulp.LpVariable(f"STO0_{t}", lowBound=0) for t in storage_tech}

#-------------------  OBJECTIVE -------------------
prob += (
    pulp.lpSum([a[t]*CAP[t] for t in technologies]) +
    pulp.lpSum([(vom[t]+fuel[t])*GEN[(t,h)] for t in technologies for h in hours]) +
    pulp.lpSum([vom[t]*CHARGE[(t,h)] for t in storage_tech for h in hours])
), "TotalCost"

#-------------------  CONSTRAINTS -------------------
for h in hours:
    prob += (pulp.lpSum([GEN[(t,h)] for t in technologies]) +
             pulp.lpSum([CHARGE[(t,h)] for t in storage_tech]) == demand[h], f"Balance_{h}")

for t in ['wind','solar','gas']:
    for h in hours:
        prob += GEN[(t,h)] <= CAP[t]*cf[(t,h)], f"CapLim_{t}_{h}"

for t in storage_tech:
    for h in hours:
        if h == 0:
            prob += STO[(t,h)] == eta_stor[t]*CHARGE[(t,h)] - GEN[(t,h)], f"StorBal_{t}_{h}"
        else:
            prob += STO[(t,h)] == STO[(t,h-1)] + eta_stor[t]*CHARGE[(t,h)] - GEN[(t,h)], f"StorBal_{t}_{h}"
        prob += STO[(t,h)] <= dur_stor[t]*CAP[t], f"StorSoc_{t}_{h}"
        prob += GEN[(t,h)] + CHARGE[(t,h)] <= CAP[t], f"StorPower_{t}_{h}"

for t in storage_tech:
    prob += STO0[t] == 0, f"InitSOC_{t}"

#-------------------  CASE 1: WITHOUT BATTERY -------------------
CAP['batt'].upBound = 0
prob.solve()

res_no_batt = {
    'CAP': {t: CAP[t].varValue for t in ['wind','solar','gas']},
    'COST': pulp.value(prob.objective),
    'EMIS': sum(co2['gas']*GEN[('gas',h)].varValue for h in hours)
}

#-------------------  CASE 2: WITH BATTERY -------------------
CAP['batt'].upBound = None
prob.solve()

res_with_batt = {
    'CAP': {t: CAP[t].varValue for t in technologies},
    'COST': pulp.value(prob.objective),
    'EMIS': sum(co2['gas']*GEN[('gas',h)].varValue for h in hours),
    'Energy_batt': sum(GEN[('batt',h)].varValue for h in hours)
}

#-------------------  EXPORT RESULTS TO CSV -------------------
# Case 1: without battery
df_no_batt = pd.DataFrame.from_dict({
    'Technology': list(res_no_batt['CAP'].keys()) + ['COST','EMIS'],
    'Value': list(res_no_batt['CAP'].values()) + [res_no_batt['COST'], res_no_batt['EMIS']]
})
df_no_batt.to_csv('res_no_batt.csv', index=False)

# Case 2: with battery
df_with_batt = pd.DataFrame.from_dict({
    'Technology': list(res_with_batt['CAP'].keys()) + ['COST','EMIS','Energy_batt'],
    'Value': list(res_with_batt['CAP'].values()) + [res_with_batt['COST'], res_with_batt['EMIS'], res_with_batt['Energy_batt']]
})
df_with_batt.to_csv('res_with_batt.csv', index=False)

#-------------------  DISPLAY RESULTS -------------------
print("=== CASE 1: WITHOUT BATTERY ===")
print(res_no_batt)
print("\n=== CASE 2: WITH BATTERY ===")
print(res_with_batt)
