import pandas as pd
import matplotlib.pyplot as plt

# Load the CSV
df = pd.read_csv("assignment5_results.csv")

# Filter only transmission flow rows
df_tx = df[df['Type'] == 'Flow']

# Ensure Hour is numeric
df_tx['Hour'] = pd.to_numeric(df_tx['Hour'])

# Plot
plt.figure(figsize=(12,5))
plt.plot(df_tx['Hour'], df_tx['Value'], label='Transmission Flow (MW)')
plt.xlabel('Hour')
plt.ylabel('Power Flow North → South (MW)')
plt.title('Hourly Transmission Flow')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
