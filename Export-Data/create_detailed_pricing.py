import sqlite3
import pandas as pd
import numpy as np
import json

def detect_outliers_iqr(data, multiplier=1.5):
    """Detect outliers using IQR method"""
    if len(data) < 4:
        return np.zeros(len(data), dtype=bool)

    q1 = np.percentile(data, 25)
    q3 = np.percentile(data, 75)
    iqr = q3 - q1

    lower_bound = q1 - (multiplier * iqr)
    upper_bound = q3 + (multiplier * iqr)

    return (data < lower_bound) | (data > upper_bound)

def detect_outliers_zscore(data, threshold=3):
    """Detect outliers using Z-score method"""
    if len(data) < 3:
        return np.zeros(len(data), dtype=bool)

    mean = np.mean(data)
    std = np.std(data)

    if std == 0:
        return np.zeros(len(data), dtype=bool)

    z_scores = np.abs((data - mean) / std)
    return z_scores > threshold

def main():
    # Connect to database
    conn = sqlite3.connect('exports.db')

    # Query all European exports with relevant fields
    query = """
    SELECT
        fruit_name,
        Exporter,
        format_type,
        variety,
        is_organic,
        is_conventional,
        is_iqf,
        is_aseptic,
        certification,
        net_weight_mt,
        usd_per_mt_fob,
        Date,
        "Destination Country",
        destination_country_en,
        Importer,
        "Commercial Description"
    FROM exports
    WHERE region = 'Europe'
        AND fruit_name IS NOT NULL
        AND fruit_name <> 'unknown'
        AND usd_per_mt_fob IS NOT NULL
        AND usd_per_mt_fob > 0
        AND net_weight_mt IS NOT NULL
        AND net_weight_mt > 0
    ORDER BY fruit_name, Exporter, format_type
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    print(f"Total records loaded: {len(df)}")

    # Add outlier detection columns
    df['is_outlier_iqr'] = False
    df['is_outlier_zscore'] = False
    df['is_outlier_combined'] = False

    # Detect outliers by fruit + format combination for more granular detection
    for (fruit, format_type) in df.groupby(['fruit_name', 'format_type']).groups.keys():
        mask = (df['fruit_name'] == fruit) & (df['format_type'] == format_type)
        group_data = df[mask]

        if len(group_data) < 5:
            continue

        prices = group_data['usd_per_mt_fob'].values

        # Detect outliers using both methods
        outliers_iqr = detect_outliers_iqr(prices)
        outliers_zscore = detect_outliers_zscore(prices)
        outliers_combined = outliers_iqr & outliers_zscore

        # Update dataframe
        df.loc[mask, 'is_outlier_iqr'] = outliers_iqr
        df.loc[mask, 'is_outlier_zscore'] = outliers_zscore
        df.loc[mask, 'is_outlier_combined'] = outliers_combined

    # Clean dataset
    df_clean = df[~df['is_outlier_combined']].copy()

    print(f"Clean records (outliers removed): {len(df_clean)}")
    print(f"Outliers identified: {df['is_outlier_combined'].sum()}")

    # Create detailed pricing by Fruit -> Exporter -> Format
    print("\n" + "="*80)
    print("Creating detailed pricing tables...")
    print("="*80)

    # 1. Full detail: Fruit -> Exporter -> Format with all statistics
    detailed_pricing = df_clean.groupby(['fruit_name', 'Exporter', 'format_type']).agg({
        'usd_per_mt_fob': ['count', 'mean', 'median', 'std', 'min', 'max'],
        'net_weight_mt': 'sum',
        'destination_country_en': lambda x: ', '.join(sorted(set(x))),
        'is_organic': lambda x: 'Yes' if x.any() else 'No',
        'is_iqf': lambda x: 'Yes' if x.any() else 'No',
        'certification': lambda x: ', '.join(sorted(set(str(v) for v in x if pd.notna(v) and str(v) != 'unknown')))
    }).round(2)

    detailed_pricing.columns = [
        'Shipments',
        'Avg Price USD/MT',
        'Median Price USD/MT',
        'Std Dev',
        'Min Price USD/MT',
        'Max Price USD/MT',
        'Total Volume MT',
        'Destination Countries',
        'Organic',
        'IQF',
        'Certifications'
    ]

    # Sort by fruit, then exporter, then format
    detailed_pricing = detailed_pricing.sort_index()

    # Save detailed pricing
    detail_file = '../output/europe_detailed_pricing_by_exporter_format.csv'
    detailed_pricing.to_csv(detail_file)
    print(f"\n✓ Detailed pricing saved to: {detail_file}")
    print(f"  Columns: Fruit | Exporter | Format | Shipments | Avg/Median/Min/Max Prices | Volume | Countries | Specs")

    # 2. Pivot table: Rows = Exporter+Format, Columns = Fruit (easier for comparison)
    pivot_avg = df_clean.pivot_table(
        values='usd_per_mt_fob',
        index=['Exporter', 'format_type'],
        columns='fruit_name',
        aggfunc='median'
    ).round(2)

    pivot_file = '../output/europe_pricing_pivot_exporter_format.csv'
    pivot_avg.to_csv(pivot_file)
    print(f"\n✓ Pivot table (Median prices) saved to: {pivot_file}")
    print(f"  Format: Rows = Exporter + Format | Columns = Each fruit")

    # 3. Summary by Fruit and Exporter (all formats aggregated per exporter)
    exporter_summary = df_clean.groupby(['fruit_name', 'Exporter']).agg({
        'usd_per_mt_fob': ['count', 'mean', 'median', 'min', 'max'],
        'net_weight_mt': 'sum',
        'format_type': lambda x: ', '.join(sorted(set(str(v) for v in x if pd.notna(v))))
    }).round(2)

    exporter_summary.columns = [
        'Shipments',
        'Avg Price USD/MT',
        'Median Price USD/MT',
        'Min Price USD/MT',
        'Max Price USD/MT',
        'Total Volume MT',
        'Formats Offered'
    ]

    exporter_summary = exporter_summary.sort_values(
        ['fruit_name', 'Total Volume MT'],
        ascending=[True, False]
    )

    exporter_file = '../output/europe_pricing_by_exporter.csv'
    exporter_summary.to_csv(exporter_file)
    print(f"\n✓ Exporter summary (all formats) saved to: {exporter_file}")

    # 4. Summary by Fruit and Format (all exporters aggregated per format)
    format_summary = df_clean.groupby(['fruit_name', 'format_type']).agg({
        'usd_per_mt_fob': ['count', 'mean', 'median', 'min', 'max'],
        'net_weight_mt': 'sum',
        'Exporter': 'nunique'
    }).round(2)

    format_summary.columns = [
        'Shipments',
        'Avg Price USD/MT',
        'Median Price USD/MT',
        'Min Price USD/MT',
        'Max Price USD/MT',
        'Total Volume MT',
        'Number of Exporters'
    ]

    format_summary = format_summary.sort_values(
        ['fruit_name', 'Total Volume MT'],
        ascending=[True, False]
    )

    format_file = '../output/europe_pricing_by_format.csv'
    format_summary.to_csv(format_file)
    print(f"\n✓ Format summary (all exporters) saved to: {format_file}")

    # 5. Create per-fruit detailed files for easier analysis
    print(f"\n{'='*80}")
    print("Creating individual fruit files with exporter x format pricing...")
    print('='*80)

    import os
    fruit_dir = '../output/by_fruit'
    os.makedirs(fruit_dir, exist_ok=True)

    for fruit in sorted(df_clean['fruit_name'].unique()):
        fruit_data = detailed_pricing.loc[fruit]

        fruit_file = f'{fruit_dir}/{fruit}_exporter_format_pricing.csv'
        fruit_data.to_csv(fruit_file)

        record_count = len(fruit_data)
        exporter_count = fruit_data.index.get_level_values(0).nunique()
        format_count = fruit_data.index.get_level_values(1).nunique()

        print(f"  ✓ {fruit}: {record_count} combinations ({exporter_count} exporters × {format_count} formats)")

    # 6. Price range reference by fruit and format (for quick lookup)
    print(f"\n{'='*80}")
    print("RECOMMENDED PRICE RANGES BY FRUIT AND FORMAT")
    print('='*80)
    print(f"{'Fruit':<20} {'Format':<20} {'Records':<10} {'Median Price':<15} {'Min-Max Range':<30}")
    print('-'*95)

    for (fruit, format_type) in format_summary.index:
        row = format_summary.loc[(fruit, format_type)]
        print(f"{fruit:<20} {format_type if format_type else 'Unknown':<20} "
              f"{int(row['Shipments']):<10} "
              f"${row['Median Price USD/MT']:>12,.2f} "
              f"${row['Min Price USD/MT']:>10,.2f} - ${row['Max Price USD/MT']:>10,.2f}")

    print(f"\n{'='*80}")
    print("FILES GENERATED")
    print('='*80)
    print(f"1. {detail_file}")
    print(f"   → Complete detail: Fruit | Exporter | Format with all price stats")
    print(f"\n2. {pivot_file}")
    print(f"   → Pivot view: Exporters×Formats as rows, Fruits as columns")
    print(f"\n3. {exporter_file}")
    print(f"   → By exporter: Shows all formats they offer per fruit")
    print(f"\n4. {format_file}")
    print(f"   → By format: Shows pricing across all exporters")
    print(f"\n5. {fruit_dir}/")
    print(f"   → Individual files per fruit with exporter×format matrix")

    print(f"\n{'='*80}")
    print(f"Total exporters: {df_clean['Exporter'].nunique()}")
    print(f"Total formats: {df_clean['format_type'].nunique()}")
    print(f"Total fruit types: {df_clean['fruit_name'].nunique()}")
    print(f"Total unique combinations: {len(detailed_pricing)}")

if __name__ == '__main__':
    main()
