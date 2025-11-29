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

# --- Hour labels ---
h = [f"h{i+1}" for i in range(n)]

# --- DataFrame ---
df = pd.DataFrame({
    'demand': np.round(demand, 1),
    'cf_wind': np.round(cf_wind, 3),
    'cf_solar': np.round(cf_solar, 3),
    'cf_gas': cf_gas
}, index=h)

# --- Write GAMS-compatible table ---
with open('baseline_data_gams.txt', 'w') as f:
    # Column headers as quoted symbols
    f.write("'demand' 'cf_wind' 'cf_solar' 'cf_gas'\n")
    for idx, row in df.iterrows():
        # Ensure all numbers have a dot decimal
        f.write(f"{idx} {row['demand']:.1f} {row['cf_wind']:.3f} {row['cf_solar']:.3f} {row['cf_gas']:.1f}\n")

print("baseline_data_gams.txt generated successfully!")
