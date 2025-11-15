"""
Data Quality Filters for Peru Frozen Fruit Export Analysis

Implements business rules for filtering out invalid/unreliable data:
1. Air freight shipments (sea freight only for accurate pricing)
2. Sample shipments (MUESTRA, SIN VALOR COMERCIAL, etc.)
3. Small shipments (< 0.1 MT - not representative)
4. Price outliers (IQR method per fruit type)

Usage:
    from core.filters import filter_valid_shipments, is_valid_for_analysis

    # Filter DataFrame
    clean_df = filter_valid_shipments(df)

    # Check individual record
    is_valid = is_valid_for_analysis(row)
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
import re


# Minimum shipment weight threshold (metric tons)
MIN_SHIPMENT_MT = 0.1  # 100 kg

# Sample/test shipment keywords (Spanish and English)
SAMPLE_KEYWORDS = [
    'MUESTRA',
    'SIN VALOR COMERCIAL',
    'ENVIO DE MUESTRAS',
    'SAMPLE',
    'NO COMMERCIAL VALUE',
    'TEST SHIPMENT',
    'TRIAL',
]

# Air freight shipping methods (Via field)
AIR_SHIPPING_METHODS = [
    'AÉREO',
    'AEREO',
    'AIR',
]

# Fruit-specific price thresholds (USD/MT) - for outlier detection
# These are minimum reasonable prices; anything below is likely data error
FRUIT_PRICE_FLOORS: Dict[str, float] = {
    'mango': 1500,
    'avocado': 2000,
    'blueberry': 1800,
    'strawberry': 1500,
    'raspberry': 2000,
    'passion_fruit': 1800,
    'pineapple': 800,
    'papaya': 800,
    'lucuma': 2000,
    'golden_berry': 1500,
    'cherimoya': 2500,
    'pomegranate': 1500,
    'grape': 1000,
    'banana': 500,
    'default': 500,  # General minimum for unlisted fruits
}


def is_air_shipment(row: pd.Series) -> bool:
    """
    Check if shipment was sent by air freight.

    Air shipments typically have:
    - Via field containing "AÉREO" or "AEREO"
    - Sometimes very small weights relative to value

    Args:
        row: DataFrame row with 'Via' field

    Returns:
        True if shipment is via air, False otherwise
    """
    via = row.get('Via', '')

    if pd.isna(via):
        return False

    via_upper = str(via).upper()
    return any(method in via_upper for method in AIR_SHIPPING_METHODS)


def is_sample_shipment(row: pd.Series) -> bool:
    """
    Check if shipment is a sample/test shipment.

    Sample indicators:
    - Keywords in Commercial Description: MUESTRA, SIN VALOR, etc.
    - Very small weight (< 0.01 MT = 10 kg)
    - Zero or near-zero value

    Args:
        row: DataFrame row with 'Commercial Description', net_weight_mt, U$ FOB Tot

    Returns:
        True if shipment is a sample, False otherwise
    """
    # Check commercial description for sample keywords
    comm_desc = row.get('Commercial Description', '')

    if pd.notna(comm_desc):
        comm_desc_upper = str(comm_desc).upper()
        if any(keyword in comm_desc_upper for keyword in SAMPLE_KEYWORDS):
            return True

    # Check for unrealistically small weight
    net_weight_mt = row.get('net_weight_mt', 0)
    if pd.notna(net_weight_mt) and net_weight_mt < 0.01:  # < 10 kg
        return True

    # Check for zero or near-zero value (but not null)
    fob_total = row.get('U$ FOB Tot', 0)
    if pd.notna(fob_total) and 0 < fob_total < 10:  # Less than $10
        return True

    return False


def is_small_shipment(row: pd.Series, min_mt: float = MIN_SHIPMENT_MT) -> bool:
    """
    Check if shipment is below minimum size threshold.

    Small shipments are not representative for pricing analysis.
    Default threshold: 0.1 MT (100 kg)

    Args:
        row: DataFrame row with 'net_weight_mt' field
        min_mt: Minimum metric tons threshold

    Returns:
        True if shipment is below threshold, False otherwise
    """
    net_weight_mt = row.get('net_weight_mt', 0)

    if pd.isna(net_weight_mt) or net_weight_mt is None:
        return True  # Missing weight = invalid

    return net_weight_mt < min_mt


def is_price_outlier_iqr(
    row: pd.Series,
    q1: float,
    q3: float,
    multiplier: float = 1.5
) -> bool:
    """
    Check if price is an outlier using IQR method.

    Outlier definition: price < Q1 - 1.5×IQR or price > Q3 + 1.5×IQR

    Args:
        row: DataFrame row with 'usd_per_mt_fob' field
        q1: First quartile (25th percentile) price
        q3: Third quartile (75th percentile) price
        multiplier: IQR multiplier (default 1.5 for standard outliers)

    Returns:
        True if price is an outlier, False otherwise
    """
    price = row.get('usd_per_mt_fob', None)

    if pd.isna(price) or price is None or price <= 0:
        return True  # Invalid price = outlier

    iqr = q3 - q1
    lower_bound = q1 - multiplier * iqr
    upper_bound = q3 + multiplier * iqr

    return price < lower_bound or price > upper_bound


def is_below_price_floor(row: pd.Series) -> bool:
    """
    Check if price is below the fruit-specific minimum threshold.

    Prices below these floors are likely data errors or non-standard shipments.

    Args:
        row: DataFrame row with 'usd_per_mt_fob' and 'fruit_name' fields

    Returns:
        True if price is below floor, False otherwise
    """
    price = row.get('usd_per_mt_fob', None)
    fruit = row.get('fruit_name', 'default')

    if pd.isna(price) or price is None or price <= 0:
        return True  # Invalid price

    # Get fruit-specific floor or use default
    floor = FRUIT_PRICE_FLOORS.get(fruit, FRUIT_PRICE_FLOORS['default'])

    return price < floor


def calculate_iqr_bounds(
    df: pd.DataFrame,
    price_col: str = 'usd_per_mt_fob',
    group_by: Optional[str] = 'fruit_name',
    multiplier: float = 1.5
) -> pd.DataFrame:
    """
    Calculate IQR-based outlier bounds for each group.

    Args:
        df: DataFrame with price data
        price_col: Name of price column
        group_by: Column to group by (e.g., 'fruit_name'). None = overall.
        multiplier: IQR multiplier

    Returns:
        DataFrame with columns: [group_by, q1, q3, lower_bound, upper_bound]
    """
    if group_by:
        grouped = df.groupby(group_by)[price_col]
    else:
        grouped = df[price_col]

    q1 = grouped.quantile(0.25)
    q3 = grouped.quantile(0.75)
    iqr = q3 - q1

    bounds = pd.DataFrame({
        'q1': q1,
        'q3': q3,
        'iqr': iqr,
        'lower_bound': q1 - multiplier * iqr,
        'upper_bound': q3 + multiplier * iqr,
    })

    if group_by:
        bounds = bounds.reset_index()

    return bounds


def is_valid_for_analysis(row: pd.Series, iqr_bounds: Optional[pd.DataFrame] = None) -> bool:
    """
    Check if a shipment record is valid for pricing analysis.

    Applies all filter criteria:
    1. Not air freight
    2. Not a sample
    3. Not too small (>= 0.1 MT)
    4. Price above fruit-specific floor
    5. Not a statistical outlier (if IQR bounds provided)

    Args:
        row: DataFrame row to check
        iqr_bounds: Optional DataFrame with IQR bounds per fruit (from calculate_iqr_bounds)

    Returns:
        True if record is valid, False otherwise
    """
    # Check each filter criterion
    if is_air_shipment(row):
        return False

    if is_sample_shipment(row):
        return False

    if is_small_shipment(row):
        return False

    if is_below_price_floor(row):
        return False

    # Check IQR outliers if bounds provided
    if iqr_bounds is not None:
        fruit = row.get('fruit_name', None)
        if fruit and fruit in iqr_bounds['fruit_name'].values:
            bounds = iqr_bounds[iqr_bounds['fruit_name'] == fruit].iloc[0]
            if is_price_outlier_iqr(row, bounds['q1'], bounds['q3']):
                return False

    return True


def filter_valid_shipments(
    df: pd.DataFrame,
    apply_iqr_outliers: bool = True,
    iqr_multiplier: float = 1.5,
    min_shipment_mt: float = MIN_SHIPMENT_MT
) -> pd.DataFrame:
    """
    Filter DataFrame to keep only valid shipments for analysis.

    Removes:
    - Air freight
    - Samples
    - Small shipments (< min_shipment_mt)
    - Prices below fruit-specific floors
    - Statistical outliers (IQR method, optional)

    Args:
        df: Input DataFrame with export data
        apply_iqr_outliers: Whether to remove IQR outliers (default True)
        iqr_multiplier: IQR multiplier for outlier detection (default 1.5)
        min_shipment_mt: Minimum shipment size in MT (default 0.1)

    Returns:
        Filtered DataFrame
    """
    # Start with all records
    filtered = df.copy()
    initial_count = len(filtered)

    # Remove air freight
    air_mask = ~filtered.apply(is_air_shipment, axis=1)
    filtered = filtered[air_mask]
    print(f"After removing air freight: {len(filtered):,} records ({initial_count - len(filtered):,} removed)")

    # Remove samples
    sample_mask = ~filtered.apply(is_sample_shipment, axis=1)
    filtered = filtered[sample_mask]
    print(f"After removing samples: {len(filtered):,} records ({initial_count - len(filtered):,} removed)")

    # Remove small shipments
    size_mask = ~filtered.apply(lambda row: is_small_shipment(row, min_shipment_mt), axis=1)
    filtered = filtered[size_mask]
    print(f"After removing small shipments (<{min_shipment_mt} MT): {len(filtered):,} records ({initial_count - len(filtered):,} removed)")

    # Remove prices below floor
    floor_mask = ~filtered.apply(is_below_price_floor, axis=1)
    filtered = filtered[floor_mask]
    print(f"After removing prices below floor: {len(filtered):,} records ({initial_count - len(filtered):,} removed)")

    # Remove IQR outliers if requested
    if apply_iqr_outliers:
        # Calculate bounds per fruit
        bounds = calculate_iqr_bounds(
            filtered,
            price_col='usd_per_mt_fob',
            group_by='fruit_name',
            multiplier=iqr_multiplier
        )

        # Merge bounds and filter
        filtered = filtered.merge(
            bounds[['fruit_name', 'q1', 'q3']],
            on='fruit_name',
            how='left'
        )

        outlier_mask = ~filtered.apply(
            lambda row: is_price_outlier_iqr(row, row['q1'], row['q3'], iqr_multiplier),
            axis=1
        )

        # Remove temporary columns
        filtered = filtered[outlier_mask].drop(columns=['q1', 'q3'])
        print(f"After removing IQR outliers: {len(filtered):,} records ({initial_count - len(filtered):,} removed)")

    print(f"\nFinal: {len(filtered):,} / {initial_count:,} records retained ({len(filtered)/initial_count*100:.1f}%)")

    return filtered


def get_filter_stats(df: pd.DataFrame) -> Dict[str, int]:
    """
    Get statistics on how many records would be filtered by each criterion.

    Useful for understanding data quality issues.

    Args:
        df: Input DataFrame

    Returns:
        Dictionary with counts:
        - total_records
        - air_shipments
        - samples
        - small_shipments
        - below_price_floor
        - (Note: IQR outliers calculated separately after initial filtering)
    """
    return {
        'total_records': len(df),
        'air_shipments': df.apply(is_air_shipment, axis=1).sum(),
        'samples': df.apply(is_sample_shipment, axis=1).sum(),
        'small_shipments': df.apply(is_small_shipment, axis=1).sum(),
        'below_price_floor': df.apply(is_below_price_floor, axis=1).sum(),
    }


# Testing
if __name__ == '__main__':
    import sqlite3

    # Load sample data
    conn = sqlite3.connect('exports.db')
    df = pd.read_sql_query("SELECT * FROM exports LIMIT 1000", conn)
    conn.close()

    print("Data Quality Filter Statistics")
    print("=" * 60)

    stats = get_filter_stats(df)
    for criterion, count in stats.items():
        pct = count / stats['total_records'] * 100
        print(f"{criterion:25} {count:6,} ({pct:5.1f}%)")

    print("\nApplying filters...")
    print("=" * 60)
    filtered = filter_valid_shipments(df, apply_iqr_outliers=True)

    print("\nSample of filtered data:")
    print(filtered[['Exporter', 'fruit_name', 'format_type', 'net_weight_mt', 'usd_per_mt_fob']].head())
