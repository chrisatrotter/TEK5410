#!/usr/bin/env python3
import pandas as pd
import numpy as np

# 1. Create hourly timestamps for 2024 (leap year → 8784 hours)
n = 8784
t = np.arange(n)

# --- Demand ---
base_demand = 18000
daily_cycle = 3000 * np.sin(2 * np.pi * t / 24 + 5)
weekly_cycle = 1500 * np.sin(2 * np.pi * t / (24*7))
noise = np.random.normal(0, 800, n)
demand = np.clip(base_demand + daily_cycle + weekly_cycle + noise, 12000, 25000)

# --- Wind capacity factor ---
wind_season = 0.35 + 0.15 * np.sin(2 * np.pi * t / (24*366))
cf_wind = np.clip(wind_season + np.random.normal(0, 0.08, n), 0, 1)

# --- Solar capacity factor ---
hour_of_day = t % 24
solar_potential = np.where((hour_of_day >= 6) & (hour_of_day <= 18),
                           np.sin(np.pi * (hour_of_day - 6) / 12),
                           0)
solar_season = 0.6 + 0.4 * np.cos(2 * np.pi * t / (24*366) - np.pi/6)
cf_solar = np.clip(solar_potential * solar_season + np.random.normal(0, 0.03, n), 0, 1)

# --- Gas ---
cf_gas = np.ones(n)

# --- CO₂ emissions intensity (tCO₂/MWh) ---
emissions_gas = np.full(n, 0.40)  # tCO₂ per MWh of gas generation

# --- Hour labels ---
h = [f"h{i+1}" for i in range(n)]

# --- DataFrame ---
df = pd.DataFrame({
    'demand': np.round(demand, 1),
    'cf_wind': np.round(cf_wind, 3),
    'cf_solar': np.round(cf_solar, 3),
    'cf_gas': cf_gas,
    'co2_gas': np.round(emissions_gas, 3)
}, index=h)

# -------------------------------------------------
# 1. Save as CSV (for Python/PuLP)
# -------------------------------------------------
csv_file = 'baseline_data.csv'
df.to_csv(csv_file)
print(f"baseline_data.csv generated → {csv_file}")

# -------------------------------------------------
# 2. Save as GAMS-compatible text table
# -------------------------------------------------
gams_file = 'baseline_data_gams.txt'
with open(gams_file, 'w') as f:
    # Header
    f.write("'demand' 'cf_wind' 'cf_solar' 'cf_gas' 'co2_gas'\n")
    # Data rows
    for idx, row in df.iterrows():
        f.write(f"{idx} {row['demand']:.1f} {row['cf_wind']:.3f} "
                f"{row['cf_solar']:.3f} {row['cf_gas']:.1f} {row['co2_gas']:.3f}\n")

print(f"GAMS table generated → {gams_file}")
print("→ Ready for assignment5.py (CSV) and GAMS (TXT)")