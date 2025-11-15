#!/usr/bin/env python3
"""
Create a simplified pricing summary by fruit with quartile statistics
"""

import csv
from collections import defaultdict

def percentile(data, p):
    """Calculate percentile p (0-100) of sorted data"""
    if not data:
        return 0
    data_sorted = sorted(data)
    k = (len(data_sorted) - 1) * p / 100
    f = int(k)
    c = k - f
    if f + 1 < len(data_sorted):
        return data_sorted[f] + c * (data_sorted[f + 1] - data_sorted[f])
    else:
        return data_sorted[f]

def median(data):
    """Calculate median of data"""
    return percentile(data, 50)

# Read the raw shipment data
print("Reading raw shipment data...")
prices_by_fruit = defaultdict(list)
volume_by_fruit = defaultdict(float)

with open('/Users/andresublime/Documents/Claude files/Peru-Frozen-Fruit-Analysis/output/europe_fruit_exports_clean.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        fruit = row['fruit_name']
        try:
            price = float(row['usd_per_mt_fob'])
            volume = float(row['net_weight_mt'])
            prices_by_fruit[fruit].append(price)
            volume_by_fruit[fruit] += volume
        except (ValueError, KeyError):
            continue

print(f"Loaded data for {len(prices_by_fruit)} different fruits")

# Calculate statistics for each fruit
summary_data = []
for fruit in prices_by_fruit:
    prices = prices_by_fruit[fruit]
    q1 = percentile(prices, 25)
    med = median(prices)
    q3 = percentile(prices, 75)
    total_vol = volume_by_fruit[fruit]

    summary_data.append({
        'Producto': fruit,
        'Precio LOW (Q1 - 25th percentile price)': round(q1, 2),
        'Precio MID (Median price)': round(med, 2),
        'Precio HIGH (Q3 - 75th percentile price)': round(q3, 2),
        'Total Export MT': round(total_vol, 2)
    })

# Sort by total volume descending
summary_data.sort(key=lambda x: x['Total Export MT'], reverse=True)

# Write to CSV
output_path = '/Users/andresublime/Documents/Claude files/Peru-Frozen-Fruit-Analysis/output/europe_pricing_summary.csv'
fieldnames = ['Producto', 'Precio LOW (Q1 - 25th percentile price)', 'Precio MID (Median price)',
              'Precio HIGH (Q3 - 75th percentile price)', 'Total Export MT']

with open(output_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(summary_data)

print(f"\nSummary written to: {output_path}")
print(f"Total fruits: {len(summary_data)}")
print("\nTop 10 fruits by export volume:")
print("-" * 80)
print(f"{'Producto':<20} {'Q1 Price':>12} {'Median':>12} {'Q3 Price':>12} {'Volume MT':>12}")
print("-" * 80)
for row in summary_data[:10]:
    print(f"{row['Producto']:<20} ${row['Precio LOW (Q1 - 25th percentile price)']:>10,.2f} "
          f"${row['Precio MID (Median price)']:>10,.2f} ${row['Precio HIGH (Q3 - 75th percentile price)']:>10,.2f} "
          f"{row['Total Export MT']:>11,.2f}")

print("\n" + "=" * 80)
print("\nDetailed summary by fruit (sorted by export volume):")
print("=" * 80)
for row in summary_data:
    print(f"\n{row['Producto'].upper()}")
    print(f"  Price Range: ${row['Precio LOW (Q1 - 25th percentile price)']:.2f} (Q1) → "
          f"${row['Precio MID (Median price)']:.2f} (Median) → "
          f"${row['Precio HIGH (Q3 - 75th percentile price)']:.2f} (Q3) per MT")
    print(f"  Total Volume: {row['Total Export MT']:.2f} MT")
