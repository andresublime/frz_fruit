import pandas as pd

# Read the detailed file
df = pd.read_csv('../output/europe_detailed_pricing_by_exporter_format.csv')

# Create simplified master file with just the key columns
master = df[[
    'fruit_name',
    'Exporter',
    'format_type',
    'Shipments',
    'Median Price USD/MT',
    'Avg Price USD/MT',
    'Min Price USD/MT',
    'Max Price USD/MT',
    'Total Volume MT',
    'Destination Countries'
]].copy()

# Rename columns for clarity
master.columns = [
    'Fruit',
    'Exporter',
    'Format',
    'Shipments',
    'Median Price (USD/MT)',
    'Average Price (USD/MT)',
    'Min Price (USD/MT)',
    'Max Price (USD/MT)',
    'Volume (MT)',
    'Destinations'
]

# Sort by fruit, then volume descending
master = master.sort_values(['Fruit', 'Volume (MT)'], ascending=[True, False])

# Save
output_file = '../output/MASTER_europe_exporter_fruit_format_prices.csv'
master.to_csv(output_file, index=False)

print(f"Master file created: {output_file}")
print(f"\nTotal combinations: {len(master):,}")
print(f"Fruits: {master['Fruit'].nunique()}")
print(f"Exporters: {master['Exporter'].nunique()}")
print(f"Formats: {master['Format'].nunique()}")

print("\n" + "="*80)
print("SAMPLE DATA")
print("="*80)
print(master.head(20).to_string(index=False))

print("\n" + "="*80)
print("Summary by Fruit")
print("="*80)
summary = master.groupby('Fruit').agg({
    'Exporter': 'nunique',
    'Format': 'nunique',
    'Shipments': 'sum',
    'Volume (MT)': 'sum'
}).round(2)
summary.columns = ['Exporters', 'Formats', 'Total Shipments', 'Total Volume MT']
print(summary.to_string())
