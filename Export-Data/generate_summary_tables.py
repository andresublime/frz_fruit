"""Generate summary tables for frozen vs aseptic analysis.

This script creates two tables:
1. Fruit breakdown: net MT frozen vs aseptic per fruit
2. Top exporters: top 50 frozen exporters and top 50 aseptic exporters by volume
"""

import pandas as pd
from pathlib import Path


def generate_fruit_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """Generate fruit breakdown table with frozen vs aseptic volumes.

    Args:
        df: DataFrame with enriched export data

    Returns:
        DataFrame with columns: fruit, net_mt_frozen, net_mt_aseptic
    """
    # Filter for valid data
    df_valid = df[
        (df['fruit_name'].notna()) &
        (df['net_weight_mt'].notna()) &
        (df['net_weight_mt'] > 0)
    ].copy()

    # Calculate frozen volumes (is_iqf = 1)
    frozen = df_valid[df_valid['is_iqf'] == 1].groupby('fruit_name')['net_weight_mt'].sum()

    # Calculate aseptic volumes (is_aseptic = 1)
    aseptic = df_valid[df_valid['is_aseptic'] == 1].groupby('fruit_name')['net_weight_mt'].sum()

    # Combine into single table
    result = pd.DataFrame({
        'fruit': frozen.index.union(aseptic.index),
    })

    result['net_mt_frozen'] = result['fruit'].map(frozen).fillna(0)
    result['net_mt_aseptic'] = result['fruit'].map(aseptic).fillna(0)
    result['total_mt'] = result['net_mt_frozen'] + result['net_mt_aseptic']

    # Sort by total volume
    result = result.sort_values('total_mt', ascending=False)

    # Round to 2 decimal places
    result['net_mt_frozen'] = result['net_mt_frozen'].round(2)
    result['net_mt_aseptic'] = result['net_mt_aseptic'].round(2)
    result['total_mt'] = result['total_mt'].round(2)

    return result[['fruit', 'net_mt_frozen', 'net_mt_aseptic', 'total_mt']].reset_index(drop=True)


def generate_top_exporters(df: pd.DataFrame, top_n: int = 50) -> tuple:
    """Generate top exporters tables for frozen and aseptic separately.

    Args:
        df: DataFrame with enriched export data
        top_n: Number of top exporters to return

    Returns:
        Tuple of (frozen_exporters_df, aseptic_exporters_df)
    """
    # Filter for valid data
    df_valid = df[
        (df['Exporter'].notna()) &
        (df['net_weight_mt'].notna()) &
        (df['net_weight_mt'] > 0)
    ].copy()

    # Top frozen exporters (is_iqf = 1)
    frozen_df = df_valid[df_valid['is_iqf'] == 1]
    frozen_exporters = frozen_df.groupby('Exporter').agg(
        total_mt=('net_weight_mt', 'sum'),
        shipments=('net_weight_mt', 'count')
    ).reset_index()
    frozen_exporters = frozen_exporters.sort_values('total_mt', ascending=False).head(top_n)
    frozen_exporters['total_mt'] = frozen_exporters['total_mt'].round(2)
    frozen_exporters['rank'] = range(1, len(frozen_exporters) + 1)
    frozen_exporters = frozen_exporters[['rank', 'Exporter', 'total_mt', 'shipments']]
    frozen_exporters.columns = ['rank', 'exporter', 'frozen_mt', 'shipments']

    # Top aseptic exporters (is_aseptic = 1)
    aseptic_df = df_valid[df_valid['is_aseptic'] == 1]
    aseptic_exporters = aseptic_df.groupby('Exporter').agg(
        total_mt=('net_weight_mt', 'sum'),
        shipments=('net_weight_mt', 'count')
    ).reset_index()
    aseptic_exporters = aseptic_exporters.sort_values('total_mt', ascending=False).head(top_n)
    aseptic_exporters['total_mt'] = aseptic_exporters['total_mt'].round(2)
    aseptic_exporters['rank'] = range(1, len(aseptic_exporters) + 1)
    aseptic_exporters = aseptic_exporters[['rank', 'Exporter', 'total_mt', 'shipments']]
    aseptic_exporters.columns = ['rank', 'exporter', 'aseptic_mt', 'shipments']

    return frozen_exporters, aseptic_exporters


def main():
    """Generate summary tables and save to CSV files."""
    print("=" * 80)
    print("FROZEN VS ASEPTIC SUMMARY TABLES")
    print("=" * 80)

    # Load deduplicated enriched data
    input_file = Path("data/veritrade_combined_enriched_dedup.csv.gz")

    print(f"\nLoading data from {input_file}...")
    df = pd.read_csv(input_file, compression='gzip')
    print(f"  Loaded {len(df):,} records (deduplicated)")

    # Generate Table 1: Fruit breakdown
    print("\n" + "=" * 80)
    print("TABLE 1: Fruit Breakdown (Frozen vs Aseptic)")
    print("=" * 80)

    fruit_table = generate_fruit_breakdown(df)

    print("\n" + fruit_table.to_string(index=False))

    # Save to CSV
    fruit_output = Path("data/fruit_frozen_vs_aseptic.csv")
    fruit_table.to_csv(fruit_output, index=False)
    print(f"\n✓ Saved to: {fruit_output}")

    # Generate Table 2: Top exporters
    print("\n" + "=" * 80)
    print("TABLE 2: Top 50 Exporters by Volume")
    print("=" * 80)

    frozen_exporters, aseptic_exporters = generate_top_exporters(df, top_n=50)

    print("\n" + "-" * 80)
    print("TOP 50 FROZEN EXPORTERS")
    print("-" * 80)
    print(frozen_exporters.head(20).to_string(index=False))
    if len(frozen_exporters) > 20:
        print(f"... (showing top 20 of {len(frozen_exporters)})")

    print("\n" + "-" * 80)
    print("TOP 50 ASEPTIC EXPORTERS")
    print("-" * 80)
    print(aseptic_exporters.head(20).to_string(index=False))
    if len(aseptic_exporters) > 20:
        print(f"... (showing top 20 of {len(aseptic_exporters)})")

    # Save to CSV
    frozen_output = Path("data/top_frozen_exporters.csv")
    aseptic_output = Path("data/top_aseptic_exporters.csv")

    frozen_exporters.to_csv(frozen_output, index=False)
    aseptic_exporters.to_csv(aseptic_output, index=False)

    print(f"\n✓ Frozen exporters saved to: {frozen_output}")
    print(f"✓ Aseptic exporters saved to: {aseptic_output}")

    # Summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)

    total_frozen = fruit_table['net_mt_frozen'].sum()
    total_aseptic = fruit_table['net_mt_aseptic'].sum()

    print(f"\nTotal Frozen MT: {total_frozen:,.2f}")
    print(f"Total Aseptic MT: {total_aseptic:,.2f}")
    print(f"Grand Total MT: {total_frozen + total_aseptic:,.2f}")

    print(f"\nFrozen Percentage: {total_frozen / (total_frozen + total_aseptic) * 100:.1f}%")
    print(f"Aseptic Percentage: {total_aseptic / (total_frozen + total_aseptic) * 100:.1f}%")

    print(f"\nUnique Frozen Exporters: {len(frozen_exporters)}")
    print(f"Unique Aseptic Exporters: {len(aseptic_exporters)}")

    print("\n" + "=" * 80)
    print("✓ Summary tables generated successfully!")
    print("=" * 80)


if __name__ == "__main__":
    main()
