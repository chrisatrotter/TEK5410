import csv
from collections import defaultdict

# Path to your CSV file
filepath = "germany_electricity_supply.csv"

# Grouping rules to match germany_energy_supply.csv categories
GROUPS = {
    "Coal": "Coal and coal products",
    "Oil": "Oil and oil products",
    "Natural gas": "Natural gas",
    "Hydropower": "Hydropower",
    "Nuclear": "Nuclear",

    # Solar, wind, geothermal, other renewables, biofuels, waste → same category
    "Wind": "Solar, wind and other renewables",
    "Solar PV": "Solar, wind and other renewables",
    "Solar thermal": "Solar, wind and other renewables",
    "Geothermal": "Solar, wind and other renewables",
    "Other sources": "Solar, wind and other renewables",

    # Biofuels + Waste → merged
    "Biofuels": "Biofuels and waste",
    "Waste": "Biofuels and waste",
}

totals_2024 = defaultdict(float)

with open(filepath, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        source = row['electricity generation sources in Germany'].strip('"')
        year = int(row["Year"])
        value_str = row["Value"].strip()

        # skip empty values
        if value_str == "":
            continue

        value = float(value_str)

        # process only 2024
        if year == 2024:
            if source in GROUPS:
                group = GROUPS[source]
                totals_2024[group] += value

# Calculate total electricity generation in 2024
grand_total = sum(totals_2024.values())

# Print grouped percentages
print("Electricity Supply Percentages by Group (Germany, 2024)\n")
for group, value in totals_2024.items():
    pct = (value / grand_total) * 100
    print(f"{group:35s}: {pct:.2f}%   ({value:.0f} GWh)")

print(f"\nTotal (2024): {grand_total:.0f} GWh")
