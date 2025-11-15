"""
Quartile Pricing Analytics Engine

Provides unified pricing analysis with Q1/Median/Q3 calculations.
Supports multiple aggregation dimensions and drill-downs.

Output format: Low$ (Q1) | Mid$ (Median) | Hi$ (Q3) | YTD MT

Examples:
    # Fruit-level summary
    df = calculate_pricing_summary(dimension='fruit')

    # Exporter-level summary
    df = calculate_pricing_summary(dimension='exporter')

    # Drill down: Mango by exporter
    df = calculate_pricing_drill_down('fruit', 'mango', by='exporter')

    # Drill down: Viru by fruit
    df = calculate_pricing_drill_down('exporter', 'Viru', by='fruit')
"""

import pandas as pd
import numpy as np
from typing import Optional, Literal, Dict, List
from core.database import execute_query


DimensionType = Literal['fruit', 'exporter', 'format']


def calculate_pricing_summary(
    dimension: DimensionType = 'fruit',
    region: Optional[str] = None,
    use_clean_view: bool = True
) -> pd.DataFrame:
    """
    Calculate quartile pricing summary for a dimension.

    Args:
        dimension: Dimension to aggregate by ('fruit', 'exporter', or 'format')
        region: Optional region filter ('Europe', 'RoW', or None for worldwide)
        use_clean_view: Use v_clean_exports view (YTD, filtered data)

    Returns:
        DataFrame with columns:
        - [dimension]: Fruit/Exporter/Format name
        - Low$: Q1 price (25th percentile, USD/MT FOB)
        - Mid$: Median price (50th percentile)
        - Hi$: Q3 price (75th percentile)
        - YTD MT: Total metric tons
        - (Additional columns based on dimension)
    """
    # Map dimension to column name
    dimension_col_map = {
        'fruit': 'fruit_name',
        'exporter': 'canonical_exporter',
        'format': 'format_type',
    }

    dimension_col = dimension_col_map[dimension]
    source_table = 'v_clean_exports' if use_clean_view else 'exports'

    # Build region filter
    region_filter = ""
    if region == 'Europe':
        region_filter = "AND region = 'Europe'"
    elif region == 'RoW':
        region_filter = "AND region != 'Europe'"

    # Load data
    query = f"""
        SELECT
            {dimension_col} as dimension_value,
            fruit_name,
            usd_per_mt_fob,
            net_weight_mt
        FROM {source_table}
        WHERE {dimension_col} IS NOT NULL
          AND usd_per_mt_fob IS NOT NULL
          AND net_weight_mt > 0
          {region_filter}
    """

    df = execute_query(query)

    # Calculate quartiles using pandas - simpler approach
    result = df.groupby('dimension_value').agg(
        low_price=pd.NamedAgg(column='usd_per_mt_fob', aggfunc=lambda x: x.quantile(0.25)),
        mid_price=pd.NamedAgg(column='usd_per_mt_fob', aggfunc=lambda x: x.quantile(0.50)),
        hi_price=pd.NamedAgg(column='usd_per_mt_fob', aggfunc=lambda x: x.quantile(0.75)),
        total_mt=pd.NamedAgg(column='net_weight_mt', aggfunc='sum'),
        records=pd.NamedAgg(column='usd_per_mt_fob', aggfunc='count'),
    ).reset_index()

    # Rename columns
    result = result.rename(columns={
        'dimension_value': dimension.title(),
        'low_price': 'Low$',
        'mid_price': 'Mid$',
        'hi_price': 'Hi$',
        'total_mt': 'YTD MT',
        'records': 'Records',
    })

    # For exporter dimension, add fruit count
    if dimension == 'exporter':
        fruit_counts = df.groupby('dimension_value')['fruit_name'].nunique().reset_index()
        fruit_counts.columns = [dimension.title(), 'Fruits']
        result = result.merge(fruit_counts, on=dimension.title())

    # Round values
    result['Low$'] = result['Low$'].round(0).astype(int)
    result['Mid$'] = result['Mid$'].round(0).astype(int)
    result['Hi$'] = result['Hi$'].round(0).astype(int)
    result['YTD MT'] = result['YTD MT'].round(0).astype(int)

    # Reorder columns
    if dimension == 'exporter':
        result = result[[dimension.title(), 'Fruits', 'Low$', 'Mid$', 'Hi$', 'YTD MT', 'Records']]
    else:
        result = result[[dimension.title(), 'Low$', 'Mid$', 'Hi$', 'YTD MT', 'Records']]

    # Sort by YTD MT descending
    result = result.sort_values('YTD MT', ascending=False).reset_index(drop=True)

    return result


def calculate_pricing_drill_down(
    filter_dimension: DimensionType,
    filter_value: str,
    by: DimensionType,
    region: Optional[str] = None,
    use_clean_view: bool = True
) -> pd.DataFrame:
    """
    Calculate pricing for a specific entity, broken down by another dimension.

    Examples:
        # Mango prices by exporter
        calculate_pricing_drill_down('fruit', 'mango', by='exporter')

        # Viru prices by fruit
        calculate_pricing_drill_down('exporter', 'Viru', by='fruit')

        # Chunks format by exporter
        calculate_pricing_drill_down('format', 'chunks', by='exporter')

    Args:
        filter_dimension: Dimension to filter on ('fruit', 'exporter', 'format')
        filter_value: Value to filter for
        by: Dimension to aggregate by
        region: Optional region filter
        use_clean_view: Use v_clean_exports view

    Returns:
        DataFrame with pricing breakdown
    """
    # Map dimensions to column names
    dimension_col_map = {
        'fruit': 'fruit_name',
        'exporter': 'canonical_exporter',
        'format': 'format_type',
    }

    filter_col = dimension_col_map[filter_dimension]
    by_col = dimension_col_map[by]
    source_table = 'v_clean_exports' if use_clean_view else 'exports'

    # Build region filter
    region_filter = ""
    if region == 'Europe':
        region_filter = "AND region = 'Europe'"
    elif region == 'RoW':
        region_filter = "AND region != 'Europe'"

    # Load data
    query = f"""
        SELECT
            {filter_col} as filter_value,
            {by_col} as by_value,
            usd_per_mt_fob,
            net_weight_mt
        FROM {source_table}
        WHERE {filter_col} = ?
          AND {by_col} IS NOT NULL
          AND usd_per_mt_fob IS NOT NULL
          AND net_weight_mt > 0
          {region_filter}
    """

    df = execute_query(query, params=(filter_value,))

    if len(df) == 0:
        # Return empty DataFrame with correct columns
        return pd.DataFrame(columns=[
            filter_dimension.title(), by.title(), 'Low$', 'Mid$', 'Hi$', 'YTD MT', 'Records'
        ])

    # Calculate quartiles using pandas - simpler approach
    result = df.groupby('by_value').agg(
        low_price=pd.NamedAgg(column='usd_per_mt_fob', aggfunc=lambda x: x.quantile(0.25)),
        mid_price=pd.NamedAgg(column='usd_per_mt_fob', aggfunc=lambda x: x.quantile(0.50)),
        hi_price=pd.NamedAgg(column='usd_per_mt_fob', aggfunc=lambda x: x.quantile(0.75)),
        total_mt=pd.NamedAgg(column='net_weight_mt', aggfunc='sum'),
        records=pd.NamedAgg(column='usd_per_mt_fob', aggfunc='count'),
    ).reset_index()

    # Rename columns
    result = result.rename(columns={
        'by_value': by.title(),
        'low_price': 'Low$',
        'mid_price': 'Mid$',
        'hi_price': 'Hi$',
        'total_mt': 'YTD MT',
        'records': 'Records',
    })

    # Add filter column
    result.insert(0, filter_dimension.title(), filter_value)

    # Round values
    result['Low$'] = result['Low$'].round(0).astype(int)
    result['Mid$'] = result['Mid$'].round(0).astype(int)
    result['Hi$'] = result['Hi$'].round(0).astype(int)
    result['YTD MT'] = result['YTD MT'].round(0).astype(int)

    # Reorder columns
    result = result[[filter_dimension.title(), by.title(), 'Low$', 'Mid$', 'Hi$', 'YTD MT', 'Records']]

    # Sort by YTD MT descending
    result = result.sort_values('YTD MT', ascending=False).reset_index(drop=True)

    return result


def export_to_csv(
    df: pd.DataFrame,
    output_path: str,
    include_records: bool = False
) -> None:
    """
    Export pricing DataFrame to CSV.

    Args:
        df: DataFrame to export
        output_path: Path to output CSV file
        include_records: Whether to include Records column
    """
    if not include_records and 'Records' in df.columns:
        df = df.drop(columns=['Records'])

    df.to_csv(output_path, index=False)
    print(f"✓ Exported to {output_path}")


# Testing
if __name__ == '__main__':
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))

    print("Quartile Pricing Analytics Test")
    print("=" * 80)

    # Test 1: Fruit-level summary (should match user's example image)
    print("\n1. Fruit-Level Pricing Summary (YTD, Worldwide)")
    print("=" * 80)
    df_fruit = calculate_pricing_summary(dimension='fruit')
    print(df_fruit.head(15).to_string(index=False))

    # Test 2: Exporter-level summary (NEW - shows fruit count + pricing)
    print("\n2. Exporter-Level Pricing Summary (YTD, Worldwide)")
    print("=" * 80)
    df_exporter = calculate_pricing_summary(dimension='exporter')
    print(df_exporter.head(10).to_string(index=False))

    # Test 3: Format-level summary
    print("\n3. Format-Level Pricing Summary (YTD, Worldwide)")
    print("=" * 80)
    df_format = calculate_pricing_summary(dimension='format')
    print(df_format.to_string(index=False))

    # Test 4: Drill-down - Mango by exporter
    print("\n4. Drill-Down: Mango Pricing by Exporter")
    print("=" * 80)
    df_mango_exp = calculate_pricing_drill_down('fruit', 'mango', by='exporter')
    print(df_mango_exp.head(10).to_string(index=False))

    # Test 5: Drill-down - Viru by fruit
    print("\n5. Drill-Down: Viru Pricing by Fruit")
    print("=" * 80)
    df_viru_fruit = calculate_pricing_drill_down('exporter', 'Viru', by='fruit')
    print(df_viru_fruit.to_string(index=False))

    print("\n✓ All tests completed successfully!")
