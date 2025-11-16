"""Analyze importer name variations in the database."""

import sqlite3
from collections import defaultdict
import re

def normalize_for_comparison(name):
    """Normalize name for comparison (remove punctuation, extra spaces, lowercase)."""
    if not name:
        return "UNKNOWN"
    # Remove punctuation
    name = re.sub(r'[^\w\s]', ' ', name)
    # Normalize spaces
    name = ' '.join(name.split())
    return name.upper()

def analyze_importers():
    conn = sqlite3.connect('exports.db')
    cursor = conn.cursor()

    # Get all importers with counts
    cursor.execute('''
        SELECT importer, COUNT(*) as count
        FROM exports
        GROUP BY importer
        ORDER BY count DESC
    ''')

    importers = cursor.fetchall()

    print(f"Total distinct importer names: {len(importers)}\n")
    print("Top 50 importers by shipment count:")
    print("=" * 80)

    for i, (name, count) in enumerate(importers[:50], 1):
        normalized = normalize_for_comparison(name)
        display_name = name if name else "(empty)"
        print(f"{i:2d}. {count:4d} shipments  {display_name:50s} [{normalized}]")

    # Group similar names
    print("\n\nGrouping similar importer names:")
    print("=" * 80)

    groups = defaultdict(list)
    for name, count in importers:
        normalized = normalize_for_comparison(name)
        groups[normalized].append((name, count))

    # Show groups with multiple variations
    duplicates = {k: v for k, v in groups.items() if len(v) > 1}

    print(f"\nFound {len(duplicates)} importer groups with variations:\n")

    for normalized, variations in sorted(duplicates.items(),
                                        key=lambda x: sum(c for _, c in x[1]),
                                        reverse=True)[:30]:
        total = sum(count for _, count in variations)
        print(f"\n{normalized} ({total} total shipments):")
        for name, count in sorted(variations, key=lambda x: x[1], reverse=True):
            print(f"  {count:4d}  {name}")

    conn.close()

if __name__ == '__main__':
    analyze_importers()
