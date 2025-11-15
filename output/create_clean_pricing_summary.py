#!/usr/bin/env python3
"""
Create clean Europe pricing summary with data quality filters applied.

Filters:
- Date range: November 1, 2024 to October 31, 2025 (last 12 months)
- Exclude samples (MUESTRA, SIN VALOR COMERCIAL)
- Exclude small shipments (< 100kg)
- Exclude unrealistic prices (fruit-specific thresholds)
"""

import sqlite3
import csv
from pathlib import Path
from collections import defaultdict

# Configuration
DB_PATH = Path(__file__).parent.parent / "Export-Data" / "exports.db"
OUTPUT_PATH = Path(__file__).parent / "pricing_summary_worldwide.csv"

# Date range (last 12 months)
START_DATE = "2024-11-01"
END_DATE = "2025-10-31"

# Minimum price thresholds by fruit (USD/MT)
PRICE_THRESHOLDS = {
    'acai': 1000,
    'avocado': 2000,
    'banana': 800,
    'blueberry': 1800,
    'golden_berry': 1000,
    'grape': 800,
    'mango': 1500,
    'pineapple': 1000,
    'strawberry': 1500,
    # Other fruits use default minimum
    'default': 500
}

# Minimum shipment size (MT)
MIN_SHIPMENT_SIZE = 0.1  # 100 kg

def get_price_threshold(fruit_name):
    """Get minimum price threshold for a fruit."""
    return PRICE_THRESHOLDS.get(fruit_name, PRICE_THRESHOLDS['default'])

def calculate_percentile(data, p):
    """Calculate percentile p (0-1) from sorted data."""
    if not data:
        return 0
    data = sorted(data)
    k = (len(data) - 1) * p
    f = int(k)
    c = k - f
    if f + 1 < len(data):
        return data[f] + c * (data[f + 1] - data[f])
    return data[f]

def is_sample(description):
    """Check if product description indicates a sample."""
    if not description:
        return False
    desc_upper = description.upper()
    sample_keywords = ['MUESTRA', 'SIN VALOR COMERCIAL', 'SIN VALOR', 'SAMPLE', 'TEST']
    return any(keyword in desc_upper for keyword in sample_keywords)

def main():
    print("Connecting to database...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Query ALL exports worldwide with all necessary fields
    query = """
    SELECT
        fruit_name,
        usd_per_mt_fob as price,
        net_weight_mt as volume,
        "Commercial Description" as description
    FROM exports
    WHERE Date >= ?
        AND Date <= ?
        AND fruit_name IS NOT NULL
        AND fruit_name != 'unknown'
        AND usd_per_mt_fob IS NOT NULL
        AND usd_per_mt_fob > 0
        AND net_weight_mt IS NOT NULL
        AND net_weight_mt > 0
    ORDER BY fruit_name, usd_per_mt_fob
    """

    print(f"Querying data from {START_DATE} to {END_DATE}...")
    cursor.execute(query, (START_DATE, END_DATE))
    rows = cursor.fetchall()
    conn.close()

    # Convert to list of dicts for easier processing
    records = [{'fruit_name': r[0], 'price': r[1], 'volume': r[2], 'description': r[3]}
               for r in rows]

    initial_count = len(records)
    initial_volume = sum(r['volume'] for r in records)
    print(f"Initial records: {initial_count:,}")
    print(f"Initial volume: {initial_volume:,.2f} MT")

    # Apply filters
    print("\nApplying data quality filters...")

    # Filter 1: Exclude samples
    excluded_samples = [r for r in records if is_sample(r['description'])]
    records = [r for r in records if not is_sample(r['description'])]
    excluded_samples_vol = sum(r['volume'] for r in excluded_samples)
    print(f"  - Excluded {len(excluded_samples):,} samples ({excluded_samples_vol:,.2f} MT)")

    # Filter 2: Exclude small shipments
    excluded_small = [r for r in records if r['volume'] < MIN_SHIPMENT_SIZE]
    records = [r for r in records if r['volume'] >= MIN_SHIPMENT_SIZE]
    excluded_small_vol = sum(r['volume'] for r in excluded_small)
    print(f"  - Excluded {len(excluded_small):,} shipments < {MIN_SHIPMENT_SIZE} MT ({excluded_small_vol:,.2f} MT)")

    # Filter 3: Apply fruit-specific price thresholds
    excluded_price = []
    filtered_records = []

    for record in records:
        fruit = record['fruit_name']
        threshold = get_price_threshold(fruit)
        if record['price'] < threshold:
            excluded_price.append(record)
        else:
            filtered_records.append(record)

    records = filtered_records

    # Count excluded by fruit
    excluded_by_fruit = defaultdict(lambda: {'count': 0, 'volume': 0})
    for r in excluded_price:
        excluded_by_fruit[r['fruit_name']]['count'] += 1
        excluded_by_fruit[r['fruit_name']]['volume'] += r['volume']

    for fruit in sorted(excluded_by_fruit.keys()):
        info = excluded_by_fruit[fruit]
        threshold = get_price_threshold(fruit)
        print(f"  - Excluded {info['count']:,} {fruit} shipments < ${threshold}/MT ({info['volume']:,.2f} MT)")

    excluded_price_vol = sum(r['volume'] for r in excluded_price)
    if excluded_price:
        print(f"  - Total excluded for price: {len(excluded_price):,} shipments ({excluded_price_vol:,.2f} MT)")

    filtered_count = len(records)
    filtered_volume = sum(r['volume'] for r in records)
    print(f"\nFiltered records: {filtered_count:,}")
    print(f"Filtered volume: {filtered_volume:,.2f} MT")
    print(f"Records excluded: {len(excluded_samples) + len(excluded_small) + len(excluded_price):,}")

    # Calculate statistics by fruit
    print("\nCalculating pricing statistics...")

    # Group by fruit
    fruit_data = defaultdict(lambda: {'prices': [], 'volume': 0})
    for record in records:
        fruit = record['fruit_name']
        fruit_data[fruit]['prices'].append(record['price'])
        fruit_data[fruit]['volume'] += record['volume']

    results = []
    for fruit in sorted(fruit_data.keys()):
        data = fruit_data[fruit]
        prices = data['prices']

        if not prices:
            continue

        q1 = calculate_percentile(prices, 0.25)
        median = calculate_percentile(prices, 0.50)
        q3 = calculate_percentile(prices, 0.75)
        total_volume = data['volume']

        results.append({
            'Producto': fruit,
            'Precio LOW': round(q1, 2),
            'Precio MID': round(median, 2),
            'Precio HIGH': round(q3, 2),
            'Total Export MT': round(total_volume, 2)
        })

    # Sort by volume (descending)
    results.sort(key=lambda x: x['Total Export MT'], reverse=True)

    # Save to CSV
    print(f"\nSaving to {OUTPUT_PATH}...")
    with open(OUTPUT_PATH, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['Producto', 'Precio LOW', 'Precio MID', 'Precio HIGH', 'Total Export MT'])
        writer.writeheader()
        writer.writerows(results)

    # Display summary
    print("\n" + "="*80)
    print("WORLDWIDE PRICING SUMMARY (Last 12 Months: Nov 2024 - Oct 2025)")
    print("="*80)
    print(f"\nDate range: {START_DATE} to {END_DATE}")
    print(f"Total products: {len(results)}")
    total_vol = sum(r['Total Export MT'] for r in results)
    print(f"Total volume: {total_vol:,.2f} MT")
    print(f"\nData quality filters applied:")
    print(f"  - Excluded samples: {len(excluded_samples):,} shipments")
    print(f"  - Excluded small shipments (< {MIN_SHIPMENT_SIZE} MT): {len(excluded_small):,} shipments")
    print(f"  - Excluded low prices: {len(excluded_price):,} shipments")
    print(f"\nTop 10 products by volume:")
    print(f"\n{'Producto':<20} {'LOW':>10} {'MID':>10} {'HIGH':>10} {'Volume (MT)':>15}")
    print("-" * 80)
    for r in results[:10]:
        print(f"{r['Producto']:<20} ${r['Precio LOW']:>9,.2f} ${r['Precio MID']:>9,.2f} ${r['Precio HIGH']:>9,.2f} {r['Total Export MT']:>14,.2f}")
    print("\n" + "="*80)
    print(f"\nFile saved: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
