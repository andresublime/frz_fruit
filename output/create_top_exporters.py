#!/usr/bin/env python3
"""
Create top 20 exporters table by total export volume.
Date range: October 2024 to October 2025
"""

import sqlite3
import csv
from pathlib import Path

# Configuration
DB_PATH = Path(__file__).parent.parent / "Export-Data" / "exports.db"
OUTPUT_PATH = Path(__file__).parent / "top_20_exporters.csv"

# Date range
START_DATE = "2024-10-01"
END_DATE = "2025-10-31"

def main():
    print("Connecting to database...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Query top exporters by total volume
    query = """
    SELECT
        Exporter,
        SUM(net_weight_mt) as total_export_mt
    FROM exports
    WHERE Date >= ?
        AND Date <= ?
        AND Exporter IS NOT NULL
        AND net_weight_mt IS NOT NULL
        AND net_weight_mt > 0
    GROUP BY Exporter
    ORDER BY total_export_mt DESC
    LIMIT 20
    """

    print(f"Querying top 20 exporters from {START_DATE} to {END_DATE}...")
    cursor.execute(query, (START_DATE, END_DATE))
    rows = cursor.fetchall()
    conn.close()

    # Convert to list of dicts
    results = [{'Exporter': r[0], 'Total Export MT': round(r[1], 2)} for r in rows]

    # Save to CSV
    print(f"\nSaving to {OUTPUT_PATH}...")
    with open(OUTPUT_PATH, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['Exporter', 'Total Export MT'])
        writer.writeheader()
        writer.writerows(results)

    # Display summary
    print("\n" + "="*80)
    print("TOP 20 EXPORTERS (Oct 2024 - Oct 2025)")
    print("="*80)
    print(f"\nDate range: {START_DATE} to {END_DATE}")
    total_vol = sum(r['Total Export MT'] for r in results)
    print(f"Total volume (top 20): {total_vol:,.2f} MT")
    print(f"\nTop 20 Exporters:")
    print(f"\n{'Rank':<6} {'Exporter':<60} {'Total Export MT':>20}")
    print("-" * 90)
    for i, r in enumerate(results, 1):
        print(f"{i:<6} {r['Exporter']:<60} {r['Total Export MT']:>20,.2f}")
    print("\n" + "="*80)
    print(f"\nFile saved: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
