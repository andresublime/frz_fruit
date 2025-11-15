import sqlite3
import pandas as pd
import numpy as np

def main():
    # Connect to database
    conn = sqlite3.connect('exports.db')

    # Query all European exports
    query = """
    SELECT
        fruit_name,
        Exporter,
        format_type,
        net_weight_mt,
        usd_per_mt_fob,
        destination_country_en
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

    # Calculate better statistics with quartiles
    master = df.groupby(['fruit_name', 'Exporter', 'format_type']).agg({
        'usd_per_mt_fob': [
            'count',
            'median',
            'mean',
            lambda x: np.percentile(x, 25),  # Q1
            lambda x: np.percentile(x, 75),  # Q3
        ],
        'net_weight_mt': 'sum',
        'destination_country_en': lambda x: ', '.join(sorted(set(x)))
    }).round(2)

    # Flatten column names
    master.columns = [
        'Shipments',
        'Median Price (USD/MT)',
        'Average Price (USD/MT)',
        'Q1 Price (USD/MT)',
        'Q3 Price (USD/MT)',
        'Volume (MT)',
        'Destinations'
    ]

    # Reset index to make fruit/exporter/format regular columns
    master = master.reset_index()

    # Rename for clarity
    master.rename(columns={
        'fruit_name': 'Fruit',
        'Exporter': 'Exporter',
        'format_type': 'Format'
    }, inplace=True)

    # Calculate price range width (Q3 - Q1) as indicator of variability
    master['Price Range Width'] = (master['Q3 Price (USD/MT)'] - master['Q1 Price (USD/MT)']).round(2)

    # Reorder columns for better readability
    master = master[[
        'Fruit',
        'Exporter',
        'Format',
        'Shipments',
        'Median Price (USD/MT)',
        'Q1 Price (USD/MT)',
        'Q3 Price (USD/MT)',
        'Price Range Width',
        'Average Price (USD/MT)',
        'Volume (MT)',
        'Destinations'
    ]]

    # Sort by fruit, then volume descending
    master = master.sort_values(['Fruit', 'Volume (MT)'], ascending=[True, False])

    # Save
    output_file = '../output/MASTER_europe_exporter_fruit_format_prices.csv'
    master.to_csv(output_file, index=False)

    print(f"\nMaster file created: {output_file}")
    print(f"\nTotal combinations: {len(master):,}")
    print(f"Fruits: {master['Fruit'].nunique()}")
    print(f"Exporters: {master['Exporter'].nunique()}")
    print(f"Formats: {master['Format'].nunique()}")

    print("\n" + "="*120)
    print("SAMPLE DATA - Mango Chunks (showing Q1/Median/Q3 instead of Min/Max)")
    print("="*120)

    sample = master[(master['Fruit'] == 'mango') & (master['Format'] == 'chunks')].head(15)
    print(sample.to_string(index=False))

    print("\n" + "="*120)
    print("INTERPRETATION GUIDE")
    print("="*120)
    print("• Median Price: The typical/middle price - use this as your baseline")
    print("• Q1 Price (25th percentile): Lower bound - 25% of shipments are below this")
    print("• Q3 Price (75th percentile): Upper bound - 75% of shipments are below this")
    print("• Price Range Width: Q3-Q1 = price variability (smaller = more consistent)")
    print("• 50% of all shipments fall between Q1 and Q3 (the interquartile range)")
    print("\nFor pricing strategy:")
    print("  - Competitive price: Below Q1")
    print("  - Market price: Between Q1 and Median")
    print("  - Premium price: Between Median and Q3")
    print("  - Very high price: Above Q3")

    print("\n" + "="*120)
    print("Summary by Fruit")
    print("="*120)
    summary = master.groupby('Fruit').agg({
        'Exporter': 'nunique',
        'Format': 'nunique',
        'Shipments': 'sum',
        'Volume (MT)': 'sum',
        'Median Price (USD/MT)': 'median'
    }).round(2)
    summary.columns = ['Exporters', 'Formats', 'Total Shipments', 'Total Volume MT', 'Overall Median Price']
    summary = summary.sort_values('Total Volume MT', ascending=False)
    print(summary.to_string())

if __name__ == '__main__':
    main()
