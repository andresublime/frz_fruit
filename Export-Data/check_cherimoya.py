import gzip
import csv
from collections import defaultdict

# Read the enriched CSV to check for cherimoya/soursop
with gzip.open('data/peru_frozen_fruit_exports_enriched.csv.gz', 'rt', encoding='utf-8') as f:
    reader = csv.DictReader(f)

    cherimoya_records = []
    soursop_records = []

    for row in reader:
        fruit = row.get('fruit_name', '').lower()
        if fruit == 'cherimoya':
            cherimoya_records.append(row)
        elif fruit == 'soursop':
            soursop_records.append(row)

    print(f'Cherimoya records found: {len(cherimoya_records)}')
    print(f'Soursop records found: {len(soursop_records)}')

    # Aggregate by exporter for cherimoya
    if len(cherimoya_records) > 0:
        print('\n=== CHERIMOYA EXPORTS ===')
        exporter_data = defaultdict(lambda: {'mt': 0, 'shipments': 0, 'prices': []})

        for rec in cherimoya_records:
            exporter = rec.get('Exporter', 'Unknown')
            try:
                mt = float(rec.get('net_weight_mt', 0) or 0)
                price = float(rec.get('usd_per_mt_fob', 0) or 0)
            except:
                mt = 0
                price = 0

            exporter_data[exporter]['mt'] += mt
            exporter_data[exporter]['shipments'] += 1
            if price > 0:
                exporter_data[exporter]['prices'].append(price)

        # Sort by volume
        sorted_exporters = sorted(exporter_data.items(), key=lambda x: x[1]['mt'], reverse=True)

        print(f"\n{'Exporter':<40} {'Volume (MT)':<15} {'Shipments':<12} {'Avg Price ($/MT)':<20}")
        print("-" * 90)

        total_mt = 0
        for exporter, data in sorted_exporters:
            avg_price = sum(data['prices']) / len(data['prices']) if data['prices'] else 0
            print(f"{exporter:<40} {data['mt']:<15.2f} {data['shipments']:<12} ${avg_price:<19,.2f}")
            total_mt += data['mt']

        print("-" * 90)
        print(f"{'TOTAL':<40} {total_mt:<15.2f} {len(cherimoya_records):<12}")

    # Aggregate by exporter for soursop
    if len(soursop_records) > 0:
        print('\n\n=== SOURSOP EXPORTS ===')
        exporter_data = defaultdict(lambda: {'mt': 0, 'shipments': 0, 'prices': []})

        for rec in soursop_records:
            exporter = rec.get('Exporter', 'Unknown')
            try:
                mt = float(rec.get('net_weight_mt', 0) or 0)
                price = float(rec.get('usd_per_mt_fob', 0) or 0)
            except:
                mt = 0
                price = 0

            exporter_data[exporter]['mt'] += mt
            exporter_data[exporter]['shipments'] += 1
            if price > 0:
                exporter_data[exporter]['prices'].append(price)

        # Sort by volume
        sorted_exporters = sorted(exporter_data.items(), key=lambda x: x[1]['mt'], reverse=True)

        print(f"\n{'Exporter':<40} {'Volume (MT)':<15} {'Shipments':<12} {'Avg Price ($/MT)':<20}")
        print("-" * 90)

        total_mt = 0
        for exporter, data in sorted_exporters:
            avg_price = sum(data['prices']) / len(data['prices']) if data['prices'] else 0
            print(f"{exporter:<40} {data['mt']:<15.2f} {data['shipments']:<12} ${avg_price:<19,.2f}")
            total_mt += data['mt']

        print("-" * 90)
        print(f"{'TOTAL':<40} {total_mt:<15.2f} {len(soursop_records):<12}")

    if len(cherimoya_records) == 0 and len(soursop_records) == 0:
        print('\nNo cherimoya or soursop records found in the dataset.')
