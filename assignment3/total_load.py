import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# === Load the CSV files ===
germany_file = 'Total_Load_Day_Ahead_Actual_2024_Germany.csv'
uk_file = 'Total_Load_Day_Ahead_Actual_2024_UK.csv'

df_de = pd.read_csv(germany_file)
df_uk = pd.read_csv(uk_file)

print(f"Germany data loaded: {len(df_de)} rows")
print(f"UK data loaded: {len(df_uk)} rows")

# === Rename columns for clarity ===
df_de.columns = ['Time', 'Forecast_DE', 'Actual_DE']
df_uk.columns = ['Time', 'Forecast_UK', 'Actual_UK']

# === Parse time strings to datetime ===
def parse_time(time_str):
    """Extract start datetime from interval string."""
    start = time_str.split(' - ')[0]
    return datetime.strptime(start, '%d.%m.%Y %H:%M')

df_de['Datetime'] = df_de['Time'].apply(parse_time)
df_uk['Datetime'] = df_uk['Time'].apply(parse_time)

# Set Datetime as index
df_de.set_index('Datetime', inplace=True)
df_uk.set_index('Datetime', inplace=True)

# Drop original Time column
df_de.drop('Time', axis=1, inplace=True)
df_uk.drop('Time', axis=1, inplace=True)

# === Convert to numeric and handle "N/A" ===
df_de = df_de.apply(pd.to_numeric, errors='coerce')
df_uk = df_uk.apply(pd.to_numeric, errors='coerce')

# === Resample to hourly resolution (for combined dataframe) ===
df_de_hourly = df_de.resample('H').mean()
df_uk_hourly = df_uk.resample('H').mean()

# === Combine into one tidy dataframe ===
common_index = df_de_hourly.index.intersection(df_uk_hourly.index)
df_combined = pd.DataFrame(index=common_index)
df_combined['Actual_DE'] = df_de_hourly.loc[common_index, 'Actual_DE']
df_combined['Actual_UK'] = df_uk_hourly.loc[common_index, 'Actual_UK']
df_combined['Forecast_DE'] = df_de_hourly.loc[common_index, 'Forecast_DE']
df_combined['Forecast_UK'] = df_uk_hourly.loc[common_index, 'Forecast_UK']
df_combined['Total_Actual'] = df_combined['Actual_DE'] + df_combined['Actual_UK']

df_combined.to_csv('tidy_combined_dataframe.csv')
print(f"\n✅ Tidy combined DataFrame saved to 'tidy_combined_dataframe.csv' ({len(df_combined)} hourly rows)")
print("\nFirst 5 rows:")
print(df_combined.head())

# === Total yearly demand ===
# Germany: 15-min intervals = 0.25h
df_de['Energy_DE_GWh'] = df_de['Actual_DE'] * 0.25 / 1000  # MW * 0.25h = MWh → /1000 = GWh
total_de_twh = df_de['Energy_DE_GWh'].sum() / 1000         # GWh → TWh

# UK: 30-min intervals = 0.5h
df_uk['Energy_UK_GWh'] = df_uk['Actual_UK'] * 0.5 / 1000  # MW * 0.5h = MWh → /1000 = GWh
total_uk_twh = df_uk['Energy_UK_GWh'].sum() / 1000         # GWh → TWh

total_combined_twh = total_de_twh + total_uk_twh

print(f"\n🔹 Total yearly demand Germany: {total_de_twh:.2f} TWh")
print(f"🔹 Total yearly demand UK: {total_uk_twh:.2f} TWh")
print(f"🔹 Combined total demand: {total_combined_twh:.2f} TWh")

# === Hourly total demand ===
hourly_total = df_combined[['Total_Actual']].copy()
hourly_total.to_csv('hourly_total_demand.csv')
print(f"\n✅ Hourly total demand saved to 'hourly_total_demand.csv' ({len(hourly_total)} rows)")

# === Max and min demand ===
max_demand = df_combined['Total_Actual'].max()
max_time = df_combined['Total_Actual'].idxmax()
min_demand = df_combined['Total_Actual'].min()
min_time = df_combined['Total_Actual'].idxmin()

print(f"\n📈 Highest hourly demand: {max_demand:.0f} MW at {max_time.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"📉 Lowest hourly demand: {min_demand:.0f} MW at {min_time.strftime('%Y-%m-%d %H:%M:%S')}")

# === Data quality issues ===
na_de_actual = df_de['Actual_DE'].isna().sum()
na_uk_actual = df_uk['Actual_UK'].isna().sum()
date_range_de = (df_de.index.min(), df_de.index.max())
date_range_uk = (df_uk.index.min(), df_uk.index.max())

print("\n⚠️ Data quality checks:")
print(f"- Germany missing Actual_DE: {na_de_actual} rows")
print(f"- UK missing Actual_UK: {na_uk_actual} rows")
print(f"- Date range Germany: {date_range_de[0].strftime('%Y-%m-%d')} → {date_range_de[1].strftime('%Y-%m-%d')}")
print(f"- Date range UK: {date_range_uk[0].strftime('%Y-%m-%d')} → {date_range_uk[1].strftime('%Y-%m-%d')}")
print("- Interval mismatch: DE = 15-min, UK = 30-min → resampled to hourly")
print("- UK forecast often missing (NaN)")
