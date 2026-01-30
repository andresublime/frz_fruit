#!/usr/bin/env python3
"""Query database for products categorized as unknown."""

import sqlite3
import json

def get_unknown_products(limit=20):
    """Get commercial descriptions for products categorized as unknown."""

    # Connect to database
    conn = sqlite3.connect('data/exports.db')
    cursor = conn.cursor()

    # Query for products where fruit_name is 'unknown'
    query = """
    SELECT
        "Commercial Description",
        "HTS Code",
        "HTS Code Description",
        fruit_name,
        format_type
    FROM exports
    WHERE fruit_name = 'unknown' OR format_type = 'unknown'
    LIMIT ?
    """

    cursor.execute(query, (limit,))
    rows = cursor.fetchall()

    # Build results
    unknown_products = []
    for row in rows:
        unknown_products.append({
            'commercial_description': row[0],
            'hts_code': row[1],
            'hts_description': row[2],
            'fruit_name': row[3] if row[3] else 'N/A',
            'format_type': row[4] if row[4] else 'N/A'
        })

    conn.close()
    return unknown_products

if __name__ == "__main__":
    products = get_unknown_products(20)

    print(f"Found {len(products)} unknown products:\n")

    for i, product in enumerate(products, 1):
        print(f"{i}. {product['commercial_description']}")
        print(f"   HTS Code: {product['hts_code']}")
        print(f"   HTS Description: {product['hts_description']}")
        print(f"   Fruit: {product['fruit_name']}, Format: {product['format_type']}")
        print()
