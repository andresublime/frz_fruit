#!/usr/bin/env python3
"""
Prepare tables for PowerPoint:
1. Fruit Category / Total Metric Tons (Peru and Ecuador, separate by format_type)
2. Exporter / Total Metric Tons (Peru and Ecuador, separate by format_type)
"""

import pandas as pd
import sqlite3
from pathlib import Path

def get_data():
    """Read data from database."""
    db_path = Path(__file__).parent / "data" / "exports.db"
    conn = sqlite3.connect(db_path)

    # Check available columns
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(exports)")
    columns = [row[1] for row in cursor.fetchall()]
    print("Available columns:", columns)

    # First check what source_country values exist
    check_query = "SELECT DISTINCT source_country FROM exports LIMIT 10"
    countries = pd.read_sql_query(check_query, conn)
    print("\nDistinct source_country values:", countries['source_country'].tolist())

    # Build query
    query = """
    SELECT
        source_country,
        fruit_name,
        canonical_exporter,
        Exporter,
        format_type,
        net_weight_mt,
        [U$ FOB Tot] as fob_value
    FROM exports
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    # Filter for Peru and Ecuador (case-insensitive)
    df = df[df['source_country'].str.lower().isin(['peru', 'ecuador'])]

    # Standardize columns
    df['Exporter_Name'] = df['canonical_exporter'].fillna(df['Exporter']).fillna('Unknown')
    df['Fruit'] = df['fruit_name'].str.title().fillna('Unknown')
    df['MT'] = df['net_weight_mt'].fillna(0)
    df['Format'] = df['format_type'].fillna('Unknown')
    df['FOB_Value'] = df['fob_value'].fillna(0)

    # Calculate FOB per MT
    df['FOB_per_MT'] = df.apply(lambda row: row['FOB_Value'] / row['MT'] if row['MT'] > 0 else 0, axis=1)

    return df

def print_table(title, df, index_name=None):
    """Print formatted markdown table for copy-paste."""
    print(f"\n## {title}\n")

    if index_name:
        df.index.name = index_name

    # Format numbers with thousand separators
    df_formatted = df.copy()
    for col in df_formatted.columns:
        if pd.api.types.is_numeric_dtype(df_formatted[col]):
            df_formatted[col] = df_formatted[col].apply(lambda x: f"{x:,.2f}")

    # Reset index to make it a column for markdown
    df_markdown = df_formatted.reset_index()

    # Print as markdown table
    print(df_markdown.to_markdown(index=False))
    print()

def main():
    df = get_data()

    print(f"\nTotal records: {len(df)}")
    print(f"Countries: {df['source_country'].unique()}")
    print(f"Format types: {df['Format'].unique()}")
    print(f"Fruits: {sorted(df['Fruit'].unique())}")

    # TABLE 1: Fruit by Category (Frozen/Aseptic) / Total MT by Country
    print("\n# TABLE 1: FRUIT BY CATEGORY (TOTAL METRIC TONS)\n")

    for country in ['peru', 'ecuador']:
        country_df = df[df['source_country'] == country]

        # Separate Frozen (IQF) and Aseptic (puree, pulp, juice, concentrate)
        frozen_formats = ['iqf', 'chunks', 'slices', 'cubes', 'halves', 'whole', 'strips', 'broken_pieces']
        aseptic_formats = ['puree', 'pulp', 'juice', 'concentrate']

        # Frozen table
        frozen_df = country_df[country_df['Format'].isin(frozen_formats)]
        if len(frozen_df) > 0:
            # Group by Fruit only (no format breakdown)
            fruit_totals = frozen_df.groupby('Fruit').agg({
                'MT': 'sum',
                'FOB_Value': 'sum'
            }).reset_index()
            fruit_totals['Avg FOB USD/MT'] = fruit_totals['FOB_Value'] / fruit_totals['MT']

            # Filter >= 20 MT and group rest as "Others"
            main_items = fruit_totals[fruit_totals['MT'] >= 20].copy()
            small_items = fruit_totals[fruit_totals['MT'] < 20]

            if len(small_items) > 0:
                others_row = pd.DataFrame({
                    'Fruit': ['Others'],
                    'MT': [small_items['MT'].sum()],
                    'FOB_Value': [small_items['FOB_Value'].sum()],
                    'Avg FOB USD/MT': [small_items['FOB_Value'].sum() / small_items['MT'].sum()]
                })
                fruit_totals = pd.concat([main_items, others_row], ignore_index=True)
            else:
                fruit_totals = main_items

            fruit_totals = fruit_totals.sort_values('MT', ascending=False)

            result_df = fruit_totals.set_index('Fruit')[['MT', 'Avg FOB USD/MT']]
            result_df.columns = ['Total Metric Tons', 'Avg FOB USD/MT']

            print_table(
                f"{country.upper()} - FROZEN",
                result_df,
                index_name='Fruit'
            )

        # Aseptic table
        aseptic_df = country_df[country_df['Format'].isin(aseptic_formats)]
        if len(aseptic_df) > 0:
            # Group by Fruit only (no format breakdown)
            fruit_totals = aseptic_df.groupby('Fruit').agg({
                'MT': 'sum',
                'FOB_Value': 'sum'
            }).reset_index()
            fruit_totals['Avg FOB USD/MT'] = fruit_totals['FOB_Value'] / fruit_totals['MT']

            # Filter >= 20 MT and group rest as "Others"
            main_items = fruit_totals[fruit_totals['MT'] >= 20].copy()
            small_items = fruit_totals[fruit_totals['MT'] < 20]

            if len(small_items) > 0:
                others_row = pd.DataFrame({
                    'Fruit': ['Others'],
                    'MT': [small_items['MT'].sum()],
                    'FOB_Value': [small_items['FOB_Value'].sum()],
                    'Avg FOB USD/MT': [small_items['FOB_Value'].sum() / small_items['MT'].sum()]
                })
                fruit_totals = pd.concat([main_items, others_row], ignore_index=True)
            else:
                fruit_totals = main_items

            fruit_totals = fruit_totals.sort_values('MT', ascending=False)

            result_df = fruit_totals.set_index('Fruit')[['MT', 'Avg FOB USD/MT']]
            result_df.columns = ['Total Metric Tons', 'Avg FOB USD/MT']

            print_table(
                f"{country.upper()} - ASEPTIC",
                result_df,
                index_name='Fruit'
            )

    # TABLE 2: Exporter by Fruit / Total MT by Country
    print("\n# TABLE 2: EXPORTER BY FRUIT (TOTAL METRIC TONS)\n")

    for country in ['peru', 'ecuador']:
        country_df = df[df['source_country'] == country]

        # Get top fruits by volume for each category
        frozen_formats = ['iqf', 'chunks', 'slices', 'cubes', 'halves', 'whole', 'strips', 'broken_pieces']
        aseptic_formats = ['puree', 'pulp', 'juice', 'concentrate']

        # Frozen - show top 3 fruits
        frozen_df = country_df[country_df['Format'].isin(frozen_formats)]
        if len(frozen_df) > 0:
            top_frozen_fruits = frozen_df.groupby('Fruit')['MT'].sum().sort_values(ascending=False).head(3).index.tolist()

            for fruit in top_frozen_fruits:
                fruit_df = frozen_df[frozen_df['Fruit'] == fruit]
                exporter_totals = fruit_df.groupby('Exporter_Name').agg({
                    'MT': 'sum',
                    'FOB_Value': 'sum'
                }).reset_index()
                exporter_totals['Avg FOB USD/MT'] = exporter_totals['FOB_Value'] / exporter_totals['MT']
                exporter_totals = exporter_totals.sort_values('MT', ascending=False).head(20)

                result_df = exporter_totals.set_index('Exporter_Name')[['MT', 'Avg FOB USD/MT']]
                result_df.columns = ['Total Metric Tons', 'Avg FOB USD/MT']

                print_table(
                    f"{country.upper()} - {fruit.upper()} FROZEN (Top 20 Exporters)",
                    result_df,
                    index_name='Exporter'
                )

        # Aseptic - show top 3 fruits
        aseptic_df = country_df[country_df['Format'].isin(aseptic_formats)]
        if len(aseptic_df) > 0:
            top_aseptic_fruits = aseptic_df.groupby('Fruit')['MT'].sum().sort_values(ascending=False).head(3).index.tolist()

            for fruit in top_aseptic_fruits:
                fruit_df = aseptic_df[aseptic_df['Fruit'] == fruit]
                exporter_totals = fruit_df.groupby('Exporter_Name').agg({
                    'MT': 'sum',
                    'FOB_Value': 'sum'
                }).reset_index()
                exporter_totals['Avg FOB USD/MT'] = exporter_totals['FOB_Value'] / exporter_totals['MT']
                exporter_totals = exporter_totals.sort_values('MT', ascending=False).head(20)

                result_df = exporter_totals.set_index('Exporter_Name')[['MT', 'Avg FOB USD/MT']]
                result_df.columns = ['Total Metric Tons', 'Avg FOB USD/MT']

                print_table(
                    f"{country.upper()} - {fruit.upper()} ASEPTIC (Top 20 Exporters)",
                    result_df,
                    index_name='Exporter'
                )

    # Summary statistics
    print("\n## SUMMARY STATISTICS (>= 20 MT)\n")

    # Add category column
    frozen_formats = ['iqf', 'chunks', 'slices', 'cubes', 'halves', 'whole', 'strips', 'broken_pieces']
    aseptic_formats = ['puree', 'pulp', 'juice', 'concentrate']

    df['Category'] = df['Format'].apply(lambda x: 'Frozen' if x in frozen_formats else ('Aseptic' if x in aseptic_formats else 'Unknown'))

    summary = df.groupby(['source_country', 'Fruit', 'Category']).agg({
        'MT': 'sum',
        'FOB_Value': 'sum'
    }).reset_index()
    summary['Avg FOB USD/MT'] = summary['FOB_Value'] / summary['MT']

    # Filter >= 20 MT
    summary_main = summary[summary['MT'] >= 20].copy()
    summary_main = summary_main.sort_values(['source_country', 'MT'], ascending=[True, False])

    summary_display = summary_main[['source_country', 'Fruit', 'Category', 'MT', 'Avg FOB USD/MT']].copy()
    summary_display.columns = ['Country', 'Fruit', 'Category', 'Total MT', 'Avg FOB USD/MT']

    # Format for display
    summary_display['Total MT'] = summary_display['Total MT'].apply(lambda x: f"{x:,.2f}")
    summary_display['Avg FOB USD/MT'] = summary_display['Avg FOB USD/MT'].apply(lambda x: f"{x:,.2f}")

    print(summary_display.to_markdown(index=False))
    print()

    # Show totals of filtered items
    summary_small = summary[summary['MT'] < 20]
    if len(summary_small) > 0:
        print(f"\n**Note:** {len(summary_small)} combinations under 20 MT were filtered out, totaling {summary_small['MT'].sum():,.2f} MT\n")

if __name__ == '__main__':
    main()
