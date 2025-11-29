import csv

filepath = "germany_energy_supply.csv"

rows = []

def tj_to_twh(tj):
    return tj / 3600

with open(filepath, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        row["Value"] = float(row["Value"])
        rows.append(row)

# Calculate total energy supply in TJ
total = sum(r["Value"] for r in rows)

print("Energy Supply Percentages (Germany, 2024)\n")
print(f"Total energy supply: {total:,.0f} TJ  ({tj_to_twh(total):,.2f} TWh)\n")

# Column name in CSV
column_name = "Total energy supply, Germany, 2024"

for r in rows:
    name = r[column_name]
    value_tj = r["Value"]
    value_twh = tj_to_twh(value_tj)
    pct = (value_tj / total) * 100

    print(f"{name:35s}: {pct:6.2f}%   {value_tj:12,.0f} TJ   ({value_twh:6.2f} TWh)")
