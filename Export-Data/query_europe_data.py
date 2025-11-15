#!/usr/bin/env python3
"""
Quick query tool for Europe frozen fruit export data
Usage: python3 query_europe_data.py [fruit_name]
"""

import sqlite3
import sys
import json

def format_currency(value):
    """Format value as USD"""
    if value is None:
        return "N/A"
    return f"${value:,.2f}"

def query_fruit(fruit_name=None):
    """Query detailed information for a specific fruit or all fruits"""
    conn = sqlite3.connect('exports.db')
    cursor = conn.cursor()

    if fruit_name:
        # Specific fruit query
        fruit_name = fruit_name.lower().strip()

        print(f"\n{'='*80}")
        print(f"EXPORT ANALYSIS: {fruit_name.upper()}")
        print('='*80)

        # Basic statistics
        query = """
        SELECT
            COUNT(*) as records,
            COUNT(DISTINCT Exporter) as exporters,
            COUNT(DISTINCT format_type) as formats,
            COUNT(DISTINCT destination_country_en) as countries,
            SUM(net_weight_mt) as total_volume_mt,
            AVG(usd_per_mt_fob) as avg_price,
            MIN(usd_per_mt_fob) as min_price,
            MAX(usd_per_mt_fob) as max_price
        FROM exports
        WHERE region = 'Europe'
            AND fruit_name = ?
            AND usd_per_mt_fob > 0
        """

        cursor.execute(query, (fruit_name,))
        row = cursor.fetchone()

        if row[0] == 0:
            print(f"\nNo data found for fruit: {fruit_name}")
            print("\nAvailable fruits:")
            cursor.execute("""
                SELECT DISTINCT fruit_name
                FROM exports
                WHERE region = 'Europe'
                    AND fruit_name IS NOT NULL
                    AND fruit_name != 'unknown'
                ORDER BY fruit_name
            """)
            for (fruit,) in cursor.fetchall():
                print(f"  - {fruit}")
            conn.close()
            return

        print(f"\nOverall Statistics:")
        print(f"  Export Records: {row[0]:,}")
        print(f"  Exporters: {row[1]}")
        print(f"  Format Types: {row[2]}")
        print(f"  Destination Countries: {row[3]}")
        print(f"  Total Volume: {row[4]:,.2f} MT")
        print(f"  Avg Price: {format_currency(row[5])}/MT")
        print(f"  Price Range: {format_currency(row[6])} - {format_currency(row[7])}/MT")

        # Top exporters
        print(f"\nTop 10 Exporters:")
        query = """
        SELECT
            Exporter,
            COUNT(*) as shipments,
            SUM(net_weight_mt) as total_mt,
            AVG(usd_per_mt_fob) as avg_price
        FROM exports
        WHERE region = 'Europe'
            AND fruit_name = ?
            AND usd_per_mt_fob > 0
        GROUP BY Exporter
        ORDER BY total_mt DESC
        LIMIT 10
        """

        cursor.execute(query, (fruit_name,))
        print(f"{'Rank':<6} {'Company':<50} {'Shipments':<12} {'Volume (MT)':<15} {'Avg Price':<15}")
        print('-' * 100)

        for idx, (company, shipments, volume, avg_price) in enumerate(cursor.fetchall(), 1):
            print(f"{idx:<6} {company[:48]:<50} {shipments:<12} {volume:>13,.2f} {format_currency(avg_price):>15}")

        # By format
        print(f"\nBy Format:")
        query = """
        SELECT
            COALESCE(format_type, 'Unknown') as format,
            COUNT(*) as records,
            SUM(net_weight_mt) as total_mt,
            AVG(usd_per_mt_fob) as avg_price,
            MIN(usd_per_mt_fob) as min_price,
            MAX(usd_per_mt_fob) as max_price
        FROM exports
        WHERE region = 'Europe'
            AND fruit_name = ?
            AND usd_per_mt_fob > 0
        GROUP BY format_type
        ORDER BY total_mt DESC
        """

        cursor.execute(query, (fruit_name,))
        print(f"{'Format':<20} {'Records':<10} {'Volume (MT)':<15} {'Avg Price':<15} {'Price Range':<30}")
        print('-' * 100)

        for (format_name, records, volume, avg_price, min_price, max_price) in cursor.fetchall():
            price_range = f"{format_currency(min_price)} - {format_currency(max_price)}"
            print(f"{format_name[:18]:<20} {records:<10} {volume:>13,.2f} {format_currency(avg_price):>15} {price_range:<30}")

        # Top destinations
        print(f"\nTop Destination Countries:")
        query = """
        SELECT
            destination_country_en,
            COUNT(*) as shipments,
            SUM(net_weight_mt) as total_mt,
            AVG(usd_per_mt_fob) as avg_price
        FROM exports
        WHERE region = 'Europe'
            AND fruit_name = ?
            AND usd_per_mt_fob > 0
        GROUP BY destination_country_en
        ORDER BY total_mt DESC
        LIMIT 10
        """

        cursor.execute(query, (fruit_name,))
        print(f"{'Country':<25} {'Shipments':<12} {'Volume (MT)':<15} {'Avg Price':<15}")
        print('-' * 70)

        for (country, shipments, volume, avg_price) in cursor.fetchall():
            print(f"{country[:23]:<25} {shipments:<12} {volume:>13,.2f} {format_currency(avg_price):>15}")

    else:
        # Summary of all fruits
        print(f"\n{'='*80}")
        print("EUROPE EXPORT SUMMARY - ALL FRUITS")
        print('='*80)

        query = """
        SELECT
            fruit_name,
            COUNT(*) as records,
            COUNT(DISTINCT Exporter) as exporters,
            SUM(net_weight_mt) as total_mt,
            AVG(usd_per_mt_fob) as avg_price,
            MIN(usd_per_mt_fob) as min_price,
            MAX(usd_per_mt_fob) as max_price
        FROM exports
        WHERE region = 'Europe'
            AND fruit_name IS NOT NULL
            AND fruit_name != 'unknown'
            AND usd_per_mt_fob > 0
        GROUP BY fruit_name
        ORDER BY total_mt DESC
        """

        cursor.execute(query)

        print(f"\n{'Fruit':<20} {'Records':<10} {'Exporters':<12} {'Volume (MT)':<15} {'Avg Price':<15} {'Price Range':<35}")
        print('-' * 115)

        for (fruit, records, exporters, volume, avg_price, min_price, max_price) in cursor.fetchall():
            price_range = f"{format_currency(min_price)} - {format_currency(max_price)}"
            print(f"{fruit:<20} {records:<10} {exporters:<12} {volume:>13,.2f} {format_currency(avg_price):>15} {price_range:<35}")

        print(f"\nTo see details for a specific fruit, run:")
        print(f"  python3 query_europe_data.py <fruit_name>")
        print(f"\nExample:")
        print(f"  python3 query_europe_data.py mango")

    conn.close()

def main():
    if len(sys.argv) > 1:
        fruit = sys.argv[1]
        query_fruit(fruit)
    else:
        query_fruit()

if __name__ == '__main__':
    main()
