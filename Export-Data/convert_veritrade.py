"""Convert Veritrade XLSX files to CSV.gz format with product categorization.

This script:
1. Reads Veritrade_Frozen.xlsx and Veritrade_Aseptic.xlsx
2. Categorizes products based on filename (frozen vs aseptic)
3. Validates categorization against HTS codes
4. Merges datasets into a single CSV.gz file

Product Categorization Strategy:
- Primary: Filename determines product type
  * Veritrade_Frozen.xlsx → is_iqf=1, is_aseptic=0
  * Veritrade_Aseptic.xlsx → is_aseptic=1, is_iqf=0
- Validation: HTS codes verify correctness
  * Frozen: HTS 8119xxxx (Chapter 08: Fruits & Nuts)
  * Aseptic: HTS 200x/2009x (Chapter 20: Preparations)
"""

import pandas as pd
from pathlib import Path
from config_loader import load_config, get_input_path, get_output_path, get_processing_param


def read_veritrade_xlsx(xlsx_path: str, header_row: int = 5) -> pd.DataFrame:
    """Read Veritrade XLSX file with proper header detection.

    Args:
        xlsx_path: Path to XLSX file
        header_row: Row index where actual column headers start (default: 5)

    Returns:
        DataFrame with validated schema

    Raises:
        ValueError: If schema validation fails
    """
    print(f"Reading {Path(xlsx_path).name}...")
    df = pd.read_excel(xlsx_path, header=header_row)

    # Validate schema
    expected_cols = 33
    if len(df.columns) != expected_cols:
        raise ValueError(
            f"Expected {expected_cols} columns, got {len(df.columns)}. "
            f"Columns: {list(df.columns)}"
        )

    print(f"  Loaded {len(df):,} records")
    return df


def validate_dataframe(df: pd.DataFrame, source: str) -> None:
    """Validate DataFrame schema and data quality.

    Args:
        df: DataFrame to validate
        source: Source name for error messages

    Raises:
        ValueError: If validation fails
    """
    required_cols = ['Date', 'Exporter', 'Net kg', 'U$ FOB Tot', 'Commercial Description', 'HTS Code']

    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"{source}: Missing required column '{col}'")

    print(f"  Schema validation: ✓ PASS")


def categorize_and_validate(df: pd.DataFrame, source: str) -> pd.DataFrame:
    """Categorize products and validate against HTS codes.

    Args:
        df: DataFrame with Veritrade export data
        source: 'frozen' or 'aseptic' (from filename)

    Returns:
        DataFrame with is_iqf and is_aseptic flags set
    """
    print(f"\nCategorizing {source} products...")

    # Make a copy to avoid modifying original
    df = df.copy()

    # Set flags based on filename
    if source == 'frozen':
        df['is_iqf'] = 1
        df['is_aseptic'] = 0
        expected_pattern = '8119'
    else:  # aseptic
        df['is_iqf'] = 0
        df['is_aseptic'] = 1
        expected_pattern = ('200', '2009')

    # Validate against HTS codes
    df['HTS Code'] = df['HTS Code'].astype(str).str.strip()

    mismatches = []
    for idx, row in df.iterrows():
        hts = row['HTS Code']

        # Check if HTS matches expected pattern
        if source == 'frozen':
            if not hts.startswith(expected_pattern):
                mismatches.append(f"Row {idx}: HTS {hts}")
        else:  # aseptic
            if not (hts.startswith('200') or hts.startswith('2009')):
                mismatches.append(f"Row {idx}: HTS {hts}")

    # Report validation results
    if len(mismatches) == 0:
        print(f"  ✓ Validation: ALL {len(df):,} records match expected HTS pattern")
    else:
        print(f"  ⚠️  Validation: {len(mismatches)} records have unexpected HTS codes")
        if len(mismatches) <= 10:
            for mismatch in mismatches:
                print(f"    - {mismatch}")
        else:
            print(f"    - Showing first 10 of {len(mismatches)} mismatches:")
            for mismatch in mismatches[:10]:
                print(f"      {mismatch}")

    # Add source tracking
    df['data_source'] = source

    return df


def merge_datasets(frozen_df: pd.DataFrame, aseptic_df: pd.DataFrame) -> pd.DataFrame:
    """Merge frozen and aseptic datasets after categorization.

    Strategy:
    1. Categorize and validate each dataset
    2. Concatenate vertically
    3. Sort by Date
    4. Reset index

    Args:
        frozen_df: DataFrame with frozen products
        aseptic_df: DataFrame with aseptic products

    Returns:
        Merged DataFrame
    """
    print("\n" + "=" * 60)
    print("Categorizing and Validating Products")
    print("=" * 60)

    # Categorize with validation
    frozen_df = categorize_and_validate(frozen_df, 'frozen')
    aseptic_df = categorize_and_validate(aseptic_df, 'aseptic')

    # Merge
    print("\nMerging datasets...")
    combined_df = pd.concat([frozen_df, aseptic_df], ignore_index=True)

    # Sort by date (newest first)
    combined_df = combined_df.sort_values('Date', ascending=False)
    combined_df = combined_df.reset_index(drop=True)

    print(f"  Frozen: {len(frozen_df):,} records (is_iqf=1)")
    print(f"  Aseptic: {len(aseptic_df):,} records (is_aseptic=1)")
    print(f"  Combined: {len(combined_df):,} records")

    return combined_df


def main():
    """Main execution: XLSX → CSV.gz conversion."""
    print("\n" + "=" * 60)
    print("VERITRADE XLSX TO CSV.GZ CONVERTER")
    print("=" * 60)

    # Load config
    config = load_config()

    # Get file paths
    frozen_xlsx = get_input_path(config, 'frozen_xlsx')
    aseptic_xlsx = get_input_path(config, 'aseptic_xlsx')
    # combined_csv is in inputs section (it's input to enrich_data.py)
    output_csv = get_input_path(config, 'combined_csv')
    header_row = get_processing_param(config, 'xlsx_header_row', 5)

    # Check input files exist
    if not frozen_xlsx.exists():
        raise FileNotFoundError(f"Frozen XLSX file not found: {frozen_xlsx}")
    if not aseptic_xlsx.exists():
        raise FileNotFoundError(f"Aseptic XLSX file not found: {aseptic_xlsx}")

    # Read frozen data
    print("\n" + "=" * 60)
    print("STEP 1: Loading Veritrade_Frozen.xlsx")
    print("=" * 60)
    frozen_df = read_veritrade_xlsx(str(frozen_xlsx), header_row)
    validate_dataframe(frozen_df, "Veritrade_Frozen")

    # Read aseptic data
    print("\n" + "=" * 60)
    print("STEP 2: Loading Veritrade_Aseptic.xlsx")
    print("=" * 60)
    aseptic_df = read_veritrade_xlsx(str(aseptic_xlsx), header_row)
    validate_dataframe(aseptic_df, "Veritrade_Aseptic")

    # Merge datasets
    print("\n" + "=" * 60)
    print("STEP 3: Merging Datasets")
    print("=" * 60)
    combined_df = merge_datasets(frozen_df, aseptic_df)

    # Save to CSV.gz
    print("\n" + "=" * 60)
    print("STEP 4: Saving to CSV.gz")
    print("=" * 60)
    print(f"Output: {output_csv}")

    # Create output directory if needed
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    # Save with gzip compression
    combined_df.to_csv(output_csv, compression='gzip', index=False)

    # Report file size
    file_size_mb = output_csv.stat().st_size / (1024 * 1024)
    print(f"  File size: {file_size_mb:.1f} MB")

    # Summary statistics
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total records: {len(combined_df):,}")
    print(f"  Frozen (is_iqf=1): {(combined_df['is_iqf'] == 1).sum():,}")
    print(f"  Aseptic (is_aseptic=1): {(combined_df['is_aseptic'] == 1).sum():,}")
    print(f"\nColumns: {len(combined_df.columns)}")
    print(f"  Original: 33")
    print(f"  Added: 3 (is_iqf, is_aseptic, data_source)")
    print(f"\n✓ Conversion complete!")


if __name__ == "__main__":
    main()
