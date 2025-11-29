# scripts/forecast_battery_cost_curv.py
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import csv

# Historical data
years = np.array([2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019,
                  2020, 2021, 2022, 2023, 2024])
cost_usd_per_kwh = np.array([2571, 1450, 1370, 1130, 1180, 1050, 750, 540, 480, 230,
                             220, 210, 300, 140, 192])

# Exponential decay function
def exp_decay(x, a, b, c):
    return a * np.exp(-b * (x - 2010)) + c

# Fit curve using historical data
params, covariance = curve_fit(exp_decay, years, cost_usd_per_kwh, p0=(2500, 0.1, 100))

# Forecast for 2025 to 2035
future_years = np.arange(2025, 2036)
predicted_costs = exp_decay(future_years, *params)

# Combine 2024 actual with forecast
all_years = np.concatenate(([2024], future_years))
all_costs = np.concatenate(([192], predicted_costs))

# Calculate year-over-year improvement (positive for cost reduction)
yoy_improvement = [None]  # No improvement for 2024
for i in range(1, len(all_costs)):
    improvement = (all_costs[i-1] - all_costs[i]) / all_costs[i-1] * 100
    yoy_improvement.append(round(improvement, 2))

# Plot results
plt.figure(figsize=(10,6))
# Historical data as a connected line
plt.plot(years, cost_usd_per_kwh, 'purple', marker='o', label='Historical Cost')
# Forecast data as a dashed line
plt.plot(all_years, all_costs, 'r--', marker='o', label='Forecasted Cost')
plt.xlabel('Year')
plt.ylabel('Battery Cost (USD/kWh)')
plt.title('Battery Cost Forecast 2024-2035')
plt.legend()
plt.grid(True)
plt.show()

# Save forecast to CSV including YoY improvement
csv_filename = "battery_cost_forecast.csv"
with open(csv_filename, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Year", "Predicted_Cost_USD_per_kWh", "YoY_Improvement_%"])
    for year, cost, improvement in zip(all_years, all_costs, yoy_improvement):
        writer.writerow([year, round(cost, 2), improvement])

print(f"Forecast saved to {csv_filename}")
