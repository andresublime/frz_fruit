"""Convert Veritrade XLSX files to CSV.gz format with multi-country support.

This script:
1. Reads country-specific Veritrade XLSX files (Peru and Ecuador)
2. Normalizes column names to a unified schema
3. Adds source_country field for tracking
4. Merges datasets into a single CSV.gz file

Supports:
- Peru: 33 columns
- Ecuador: 51 columns

Product Categorization Strategy:
- HTS codes determine product type:
  * 8119xxxx → is_iqf=1, is_aseptic=0 (Frozen)
  * 200x/2008/2009 → is_aseptic=1, is_iqf=0 (Aseptic)
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from config_loader import load_config, get_input_path, get_processing_param


# Column mapping: Peru -> Canonical names
PERU_COLUMN_MAP = {
    'Qty 1': 'Qty',
    'Unit 1': 'Unit',
    'Tax ID': 'Tax_ID',
    'Destination Port': 'Destination_Port',
    'U$ FOB Unit 1': 'U$ FOB Unit',
}

# Column mapping: Ecuador -> Canonical names
ECUADOR_COLUMN_MAP = {
    'Tax Id': 'Tax_ID',
    'Unloading Port': 'Destination_Port',
}

# Core columns that must be present in both datasets (using canonical names after mapping)
REQUIRED_COLUMNS = [
    'Date', 'Exporter', 'Net kg', 'U$ FOB Tot',
    'Commercial Description', 'HTS Code'
]


def detect_country_from_columns(df: pd.DataFrame) -> str:
    """Detect source country based on column patterns.

    Args:
        df: DataFrame with Veritrade data

    Returns:
        'peru' or 'ecuador'

    Raises:
        ValueError: If country cannot be determined
    """
    columns = set(df.columns)

    # Peru-specific columns
    if 'Qty 1' in columns and 'Tax ID' in columns:
        return 'peru'
    # Ecuador-specific columns
    elif 'Tax Id' in columns and 'Unloading Port' in columns:
        return 'ecuador'
    else:
        raise ValueError(
            f"Unable to detect country from columns. "
            f"Sample columns: {list(columns)[:10]}..."
        )


def normalize_columns(df: pd.DataFrame, source_country: str) -> pd.DataFrame:
    """Normalize column names to canonical schema.

    Args:
        df: DataFrame with country-specific column names
        source_country: 'peru' or 'ecuador'

    Returns:
        DataFrame with normalized column names
    """
    df = df.copy()

    if source_country == 'peru':
        df = df.rename(columns=PERU_COLUMN_MAP)
    elif source_country == 'ecuador':
        df = df.rename(columns=ECUADOR_COLUMN_MAP)

    return df


def read_veritrade_xlsx(
    xlsx_path: str,
    header_row: int = 5,
    expected_columns: Optional[int] = None
) -> Tuple[pd.DataFrame, str]:
    """Read Veritrade XLSX file and detect country.

    Args:
        xlsx_path: Path to XLSX file
        header_row: Row index where actual column headers start (default: 5)
        expected_columns: Expected number of columns (optional validation)

    Returns:
        Tuple of (DataFrame, detected_country)

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If country cannot be detected
    """
    path = Path(xlsx_path)
    print(f"Reading {path.name}...")

    df = pd.read_excel(xlsx_path, header=header_row)

    # Detect country from columns
    source_country = detect_country_from_columns(df)
    print(f"  Detected country: {source_country.upper()}")
    print(f"  Columns: {len(df.columns)}")

    # Optional validation
    if expected_columns and len(df.columns) != expected_columns:
        print(f"  WARNING: Expected {expected_columns} columns, got {len(df.columns)}")

    print(f"  Loaded {len(df):,} records")
    return df, source_country


def validate_dataframe(df: pd.DataFrame, source: str) -> None:
    """Validate DataFrame has required columns.

    Args:
        df: DataFrame to validate (with normalized column names)
        source: Source name for error messages

    Raises:
        ValueError: If validation fails
    """
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]

    if missing:
        raise ValueError(f"{source}: Missing required columns: {missing}")

    print(f"  Schema validation: PASS")


def process_country_data(df: pd.DataFrame, source_country: str) -> pd.DataFrame:
    """Process and normalize country-specific data.

    Args:
        df: DataFrame with Veritrade data
        source_country: 'peru' or 'ecuador'

    Returns:
        Normalized DataFrame with source_country field
    """
    print(f"\nProcessing {source_country.upper()} data...")

    # Normalize column names
    df = normalize_columns(df, source_country)

    # Add source_country field
    df['source_country'] = source_country

    # Validate required columns
    validate_dataframe(df, source_country.upper())

    print(f"  Records: {len(df):,}")

    return df


def get_common_columns(dfs: List[pd.DataFrame]) -> List[str]:
    """Get columns common to all DataFrames.

    Args:
        dfs: List of DataFrames

    Returns:
        List of common column names
    """
    if not dfs:
        return []

    common = set(dfs[0].columns)
    for df in dfs[1:]:
        common &= set(df.columns)

    return list(common)


def merge_country_datasets(*dfs: pd.DataFrame) -> pd.DataFrame:
    """Merge multiple country datasets with common columns.

    Args:
        *dfs: Variable number of DataFrames to merge

    Returns:
        Combined DataFrame with common columns only
    """
    print("\n" + "=" * 60)
    print("Merging Country Datasets")
    print("=" * 60)

    if not dfs:
        raise ValueError("No DataFrames provided to merge")

    # Get common columns
    common_columns = get_common_columns(list(dfs))

    # Ensure source_country is included
    if 'source_country' not in common_columns:
        common_columns.append('source_country')

    print(f"Common columns: {len(common_columns)}")

    # Select only common columns and concatenate
    normalized_dfs = []
    for df in dfs:
        # Only keep columns that exist in this df
        cols_to_keep = [c for c in common_columns if c in df.columns]
        normalized_dfs.append(df[cols_to_keep])

    combined = pd.concat(normalized_dfs, ignore_index=True)

    # Sort by date (newest first)
    if 'Date' in combined.columns:
        combined = combined.sort_values('Date', ascending=False)
        combined = combined.reset_index(drop=True)

    # Summary by country
    for country in combined['source_country'].unique():
        count = len(combined[combined['source_country'] == country])
        print(f"  {country.upper()}: {count:,} records")

    print(f"  Combined: {len(combined):,} records")

    return combined


def categorize_by_hts(df: pd.DataFrame) -> pd.DataFrame:
    """Categorize products by HTS code (frozen vs aseptic).

    Args:
        df: DataFrame with HTS Code column

    Returns:
        DataFrame with is_iqf and is_aseptic flags
    """
    print("\n" + "=" * 60)
    print("Categorizing Products by HTS Code")
    print("=" * 60)

    df = df.copy()

    # Ensure HTS Code is string
    df['HTS Code'] = df['HTS Code'].astype(str).str.strip()

    # Frozen: HTS 8119xxxx (Chapter 08: Fruits & Nuts)
    df['is_iqf'] = df['HTS Code'].str.startswith('8119').astype(int)

    # Aseptic: HTS 200x, 2008, 2009 (Chapter 20: Preparations)
    df['is_aseptic'] = (
        df['HTS Code'].str.startswith('200') |
        df['HTS Code'].str.startswith('2008') |
        df['HTS Code'].str.startswith('2009')
    ).astype(int)

    # Add data_source tracking
    df['data_source'] = 'veritrade_combined'

    # Summary
    frozen_count = df['is_iqf'].sum()
    aseptic_count = df['is_aseptic'].sum()
    print(f"  Frozen (is_iqf=1): {frozen_count:,}")
    print(f"  Aseptic (is_aseptic=1): {aseptic_count:,}")

    return df


def main():
    """Main execution: Multi-country XLSX to CSV.gz conversion."""
    print("\n" + "=" * 60)
    print("VERITRADE MULTI-COUNTRY XLSX TO CSV.GZ CONVERTER")
    print("=" * 60)

    # Load config
    config = load_config()
    header_row = get_processing_param(config, 'xlsx_header_row', 5)

    # Define input files
    base_path = Path(__file__).parent.parent
    peru_file = base_path / "Veritrade_New_Peru.xlsx"
    ecuador_file = base_path / "Veritrade_New_Ecuador.xlsx"

    # Output path
    output_csv = get_input_path(config, 'combined_csv')

    datasets = []

    # Read Peru data
    if peru_file.exists():
        print("\n" + "=" * 60)
        print("STEP 1: Loading Peru Data")
        print("=" * 60)
        peru_df, _ = read_veritrade_xlsx(str(peru_file), header_row, expected_columns=33)
        peru_df = process_country_data(peru_df, 'peru')
        datasets.append(peru_df)
    else:
        print(f"\nWARNING: Peru file not found: {peru_file}")

    # Read Ecuador data
    if ecuador_file.exists():
        print("\n" + "=" * 60)
        print("STEP 2: Loading Ecuador Data")
        print("=" * 60)
        ecuador_df, _ = read_veritrade_xlsx(str(ecuador_file), header_row, expected_columns=51)
        ecuador_df = process_country_data(ecuador_df, 'ecuador')
        datasets.append(ecuador_df)
    else:
        print(f"\nWARNING: Ecuador file not found: {ecuador_file}")

    if not datasets:
        raise FileNotFoundError("No data files found!")

    # Merge datasets
    combined_df = merge_country_datasets(*datasets)

    # Categorize by HTS code
    combined_df = categorize_by_hts(combined_df)

    # Save to CSV.gz
    print("\n" + "=" * 60)
    print("STEP 3: Saving to CSV.gz")
    print("=" * 60)

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    combined_df.to_csv(output_csv, compression='gzip', index=False)

    file_size_mb = output_csv.stat().st_size / (1024 * 1024)
    print(f"Output: {output_csv}")
    print(f"File size: {file_size_mb:.1f} MB")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total records: {len(combined_df):,}")
    for country in combined_df['source_country'].unique():
        count = len(combined_df[combined_df['source_country'] == country])
        print(f"  {country.upper()}: {count:,}")
    print(f"\nColumns: {len(combined_df.columns)}")
    print(f"\nConversion complete!")


if __name__ == "__main__":
    main()
