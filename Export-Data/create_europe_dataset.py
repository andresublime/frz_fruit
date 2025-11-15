import sqlite3
import pandas as pd
import numpy as np
import json

def detect_outliers_iqr(data, multiplier=1.5):
    """Detect outliers using IQR method"""
    if len(data) < 4:  # Need at least 4 points for meaningful IQR
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
    print(f"Fruits: {df['fruit_name'].nunique()}")
    print(f"Exporters: {df['Exporter'].nunique()}")
    print(f"Date range: {df['Date'].min()} to {df['Date'].max()}")

    # Add outlier detection columns
    df['is_outlier_iqr'] = False
    df['is_outlier_zscore'] = False
    df['is_outlier_combined'] = False

    # Statistics dictionary
    price_stats = {}

    # Detect outliers by fruit (grouping similar products)
    for fruit in df['fruit_name'].unique():
        fruit_mask = df['fruit_name'] == fruit
        fruit_data = df[fruit_mask]

        if len(fruit_data) < 5:  # Skip outlier detection for very small samples
            price_stats[fruit] = {
                'count': len(fruit_data),
                'mean': fruit_data['usd_per_mt_fob'].mean(),
                'median': fruit_data['usd_per_mt_fob'].median(),
                'std': fruit_data['usd_per_mt_fob'].std(),
                'min': fruit_data['usd_per_mt_fob'].min(),
                'max': fruit_data['usd_per_mt_fob'].max(),
                'q1': fruit_data['usd_per_mt_fob'].quantile(0.25),
                'q3': fruit_data['usd_per_mt_fob'].quantile(0.75),
                'outliers_iqr': 0,
                'outliers_zscore': 0,
                'outliers_combined': 0,
                'clean_count': len(fruit_data),
                'clean_mean': float(fruit_data['usd_per_mt_fob'].mean()),
                'clean_median': float(fruit_data['usd_per_mt_fob'].median()),
                'clean_std': float(fruit_data['usd_per_mt_fob'].std()),
                'recommended_min': fruit_data['usd_per_mt_fob'].min(),
                'recommended_max': fruit_data['usd_per_mt_fob'].max()
            }
            continue

        prices = fruit_data['usd_per_mt_fob'].values

        # Detect outliers using both methods
        outliers_iqr = detect_outliers_iqr(prices)
        outliers_zscore = detect_outliers_zscore(prices)

        # Combined: outlier if detected by BOTH methods (more conservative)
        outliers_combined = outliers_iqr & outliers_zscore

        # Update dataframe
        df.loc[fruit_mask, 'is_outlier_iqr'] = outliers_iqr
        df.loc[fruit_mask, 'is_outlier_zscore'] = outliers_zscore
        df.loc[fruit_mask, 'is_outlier_combined'] = outliers_combined

        # Calculate statistics excluding combined outliers
        clean_prices = prices[~outliers_combined]

        if len(clean_prices) > 0:
            q1 = np.percentile(clean_prices, 25)
            q3 = np.percentile(clean_prices, 75)
            iqr = q3 - q1
            recommended_min = max(clean_prices.min(), q1 - 1.5 * iqr)
            recommended_max = min(clean_prices.max(), q3 + 1.5 * iqr)
        else:
            recommended_min = prices.min()
            recommended_max = prices.max()

        price_stats[fruit] = {
            'count': len(prices),
            'mean': prices.mean(),
            'median': np.median(prices),
            'std': prices.std(),
            'min': prices.min(),
            'max': prices.max(),
            'q1': np.percentile(prices, 25),
            'q3': np.percentile(prices, 75),
            'outliers_iqr': int(outliers_iqr.sum()),
            'outliers_zscore': int(outliers_zscore.sum()),
            'outliers_combined': int(outliers_combined.sum()),
            'clean_count': len(clean_prices),
            'clean_mean': float(clean_prices.mean()) if len(clean_prices) > 0 else None,
            'clean_median': float(np.median(clean_prices)) if len(clean_prices) > 0 else None,
            'clean_std': float(clean_prices.std()) if len(clean_prices) > 0 else None,
            'recommended_min': float(recommended_min),
            'recommended_max': float(recommended_max)
        }

    # Save full dataset
    output_file = '../output/europe_fruit_exports_full.csv'
    df.to_csv(output_file, index=False)
    print(f"\nFull dataset saved to: {output_file}")

    # Save clean dataset (excluding combined outliers)
    df_clean = df[~df['is_outlier_combined']].copy()
    clean_file = '../output/europe_fruit_exports_clean.csv'
    df_clean.to_csv(clean_file, index=False)
    print(f"Clean dataset saved to: {clean_file}")

    # Save price statistics
    stats_file = '../output/europe_price_statistics.json'
    with open(stats_file, 'w') as f:
        json.dump(price_stats, f, indent=2)
    print(f"Price statistics saved to: {stats_file}")

    # Create summary report
    print("\n" + "="*80)
    print("PRICE RANGE SUMMARY BY FRUIT (Excluding Outliers)")
    print("="*80)
    print(f"{'Fruit':<20} {'Records':<10} {'Outliers':<10} {'Min USD/MT':<12} {'Max USD/MT':<12} {'Median':<12}")
    print("-"*80)

    for fruit in sorted(price_stats.keys()):
        stats = price_stats[fruit]
        print(f"{fruit:<20} {stats['count']:<10} {stats['outliers_combined']:<10} "
              f"${stats['recommended_min']:>10,.0f} ${stats['recommended_max']:>10,.0f} "
              f"${stats['clean_median']:>10,.0f}" if stats['clean_median'] else f"${stats['median']:>10,.0f}")

    # Summary by format
    print("\n" + "="*80)
    print("SUMMARY BY FRUIT AND FORMAT")
    print("="*80)

    format_summary = df_clean.groupby(['fruit_name', 'format_type']).agg({
        'usd_per_mt_fob': ['count', 'mean', 'median', 'min', 'max'],
        'net_weight_mt': 'sum',
        'Exporter': 'nunique'
    }).round(0)

    format_summary.columns = ['Records', 'Avg Price', 'Median Price', 'Min Price', 'Max Price', 'Total Volume MT', 'Exporters']
    format_summary = format_summary.sort_values(['fruit_name', 'Records'], ascending=[True, False])

    format_file = '../output/europe_format_summary.csv'
    format_summary.to_csv(format_file)
    print(f"Format summary saved to: {format_file}")

    # Top exporters summary
    exporter_summary = df_clean.groupby(['fruit_name', 'Exporter']).agg({
        'net_weight_mt': 'sum',
        'usd_per_mt_fob': 'mean',
        'format_type': lambda x: ', '.join(sorted(set(str(v) for v in x if pd.notna(v))))
    }).round(0)

    exporter_summary.columns = ['Total Volume MT', 'Avg Price USD/MT', 'Formats']
    exporter_summary = exporter_summary.sort_values(['fruit_name', 'Total Volume MT'], ascending=[True, False])

    exporter_file = '../output/europe_exporter_summary.csv'
    exporter_summary.to_csv(exporter_file)
    print(f"Exporter summary saved to: {exporter_file}")

    print("\n" + "="*80)
    print("DATASET CREATION COMPLETE")
    print("="*80)
    print(f"Total records: {len(df):,}")
    print(f"Clean records (outliers removed): {len(df_clean):,}")
    print(f"Outliers identified: {df['is_outlier_combined'].sum():,} ({df['is_outlier_combined'].sum()/len(df)*100:.1f}%)")
    print(f"Fruits: {df['fruit_name'].nunique()}")
    print(f"Exporters: {df['Exporter'].nunique()}")
    print(f"Formats: {df['format_type'].nunique()}")

if __name__ == '__main__':
    main()
