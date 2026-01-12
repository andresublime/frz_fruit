"""
Enrich the Peru frozen fruit export dataset with structured product information.
"""
import pandas as pd
import json
from typing import List, Dict, Any
from models import ExportRecord, ProductSummary, ExportDataSummary
from parser import DescriptionParser
from collections import defaultdict
from datetime import datetime


def validate_enriched_data(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate enriched data quality and flag potential issues.

    Args:
        df: Enriched DataFrame

    Returns:
        Dictionary with validation results and warnings
    """
    print("\n" + "="*80)
    print("DATA QUALITY VALIDATION")
    print("="*80)

    issues = {}
    warnings = []

    # 1. Unknown fruits
    unknown_fruits = len(df[df['fruit_name'] == 'unknown'])
    unknown_fruits_pct = (unknown_fruits / len(df) * 100) if len(df) > 0 else 0
    issues['unknown_fruits'] = unknown_fruits
    issues['unknown_fruits_pct'] = round(unknown_fruits_pct, 2)

    if unknown_fruits_pct > 1.0:
        warnings.append(f"⚠️  {unknown_fruits_pct:.1f}% of records have unknown fruit type")
    else:
        print(f"✓ Fruit identification: {100 - unknown_fruits_pct:.1f}% success rate")

    # 2. Missing or zero prices
    missing_prices = len(df[df['usd_per_mt_fob'] == 0])
    missing_prices_pct = (missing_prices / len(df) * 100) if len(df) > 0 else 0
    issues['missing_prices'] = missing_prices
    issues['missing_prices_pct'] = round(missing_prices_pct, 2)

    if missing_prices_pct > 5.0:
        warnings.append(f"⚠️  {missing_prices_pct:.1f}% of records have zero/missing prices")
    else:
        print(f"✓ Price data: {100 - missing_prices_pct:.1f}% complete")

    # 3. Zero volumes
    zero_volumes = len(df[df['net_weight_mt'] == 0])
    zero_volumes_pct = (zero_volumes / len(df) * 100) if len(df) > 0 else 0
    issues['zero_volumes'] = zero_volumes
    issues['zero_volumes_pct'] = round(zero_volumes_pct, 2)

    if zero_volumes_pct > 5.0:
        warnings.append(f"⚠️  {zero_volumes_pct:.1f}% of records have zero volume")
    else:
        print(f"✓ Volume data: {100 - zero_volumes_pct:.1f}% complete")

    # 4. Outlier prices (suspiciously high)
    outlier_high = len(df[df['usd_per_mt_fob'] > 10000])
    outlier_high_pct = (outlier_high / len(df) * 100) if len(df) > 0 else 0
    issues['outlier_prices_high'] = outlier_high
    issues['outlier_prices_high_pct'] = round(outlier_high_pct, 2)

    if outlier_high > 0:
        warnings.append(f"⚠️  {outlier_high} records have prices > $10,000/MT (potential data errors)")
    else:
        print(f"✓ Price outliers (high): None detected")

    # 5. Outlier prices (suspiciously low)
    valid_prices = df[df['usd_per_mt_fob'] > 0]
    outlier_low = len(valid_prices[valid_prices['usd_per_mt_fob'] < 500])
    outlier_low_pct = (outlier_low / len(df) * 100) if len(df) > 0 else 0
    issues['outlier_prices_low'] = outlier_low
    issues['outlier_prices_low_pct'] = round(outlier_low_pct, 2)

    if outlier_low > 0:
        warnings.append(f"⚠️  {outlier_low} records have prices < $500/MT (potential data errors)")
    else:
        print(f"✓ Price outliers (low): None detected")

    # 6. Unknown formats
    unknown_formats = len(df[df['format_type'] == 'unknown'])
    unknown_formats_pct = (unknown_formats / len(df) * 100) if len(df) > 0 else 0
    issues['unknown_formats'] = unknown_formats
    issues['unknown_formats_pct'] = round(unknown_formats_pct, 2)

    if unknown_formats_pct > 10.0:
        warnings.append(f"⚠️  {unknown_formats_pct:.1f}% of records have unknown format type")
    else:
        print(f"✓ Format identification: {100 - unknown_formats_pct:.1f}% success rate")

    # 7. Certification distribution
    cert_dist = df['certification'].value_counts()
    issues['certification_distribution'] = cert_dist.to_dict()

    unknown_cert_pct = (cert_dist.get('unknown', 0) / len(df) * 100) if len(df) > 0 else 0
    if unknown_cert_pct > 70.0:
        warnings.append(f"⚠️  {unknown_cert_pct:.1f}% of records have unknown certification")
    else:
        print(f"✓ Certification data: {100 - unknown_cert_pct:.1f}% identified")

    # 8. Date range validation
    df_temp = df.copy()
    df_temp['Date'] = pd.to_datetime(df_temp['Date'])
    date_min = df_temp['Date'].min()
    date_max = df_temp['Date'].max()
    issues['date_range'] = {
        'min': str(date_min.date()),
        'max': str(date_max.date()),
        'span_days': (date_max - date_min).days
    }

    print(f"✓ Date range: {date_min.date()} to {date_max.date()} ({(date_max - date_min).days} days)")

    # Summary
    issues['total_records'] = len(df)
    issues['validation_passed'] = len(warnings) == 0

    print("\n" + "-"*80)
    if warnings:
        print("VALIDATION WARNINGS:")
        for warning in warnings:
            print(f"  {warning}")
    else:
        print("✓ All validation checks passed!")

    print("="*80 + "\n")

    return issues


def enrich_dataset(input_file: str, output_file: str = None) -> pd.DataFrame:
    """
    Enrich the dataset by parsing commercial descriptions into structured data.

    Args:
        input_file: Path to input CSV file (can be gzipped)
        output_file: Optional path to save enriched dataset

    Returns:
        Enriched DataFrame
    """
    print(f"Loading data from {input_file}...")
    df = pd.read_csv(input_file, compression='gzip' if input_file.endswith('.gz') else None)

    print(f"Loaded {len(df)} records")
    print("Parsing commercial descriptions...")

    # Parse descriptions and add structured fields
    enriched_rows = []

    for idx, row in df.iterrows():
        if idx % 1000 == 0:
            print(f"  Processed {idx}/{len(df)} records...")

        # Parse the commercial description
        product = DescriptionParser.parse(row['Commercial Description'])

        # Add structured fields to the row
        enriched_row = row.to_dict()
        enriched_row['fruit_name'] = product.fruit_name
        enriched_row['variety'] = product.variety
        enriched_row['format_type'] = product.product_format.format_type
        enriched_row['size_mm'] = product.product_format.size_mm
        enriched_row['is_organic'] = product.classification.is_organic
        enriched_row['is_conventional'] = product.classification.is_conventional

        # IMPORTANT: Preserve is_iqf and is_aseptic from input if they exist
        # (these were set by filename-based categorization in convert_veritrade.py)
        # Only use NLP-parsed values if not already set
        if 'is_iqf' not in enriched_row or pd.isna(enriched_row.get('is_iqf')):
            enriched_row['is_iqf'] = product.classification.is_iqf
        if 'is_aseptic' not in enriched_row or pd.isna(enriched_row.get('is_aseptic')):
            enriched_row['is_aseptic'] = product.classification.is_aseptic

        enriched_row['certification'] = product.classification.certification

        # Calculate metrics
        net_kg = row.get('Net kg', 0) or 0
        fob_total = row.get('U$ FOB Tot', 0) or 0

        net_mt = round(net_kg / 1000, 3) if net_kg else 0
        usd_per_mt = round(fob_total / net_mt, 2) if net_mt > 0 else 0

        enriched_row['net_weight_mt'] = net_mt
        enriched_row['usd_per_mt_fob'] = usd_per_mt

        enriched_rows.append(enriched_row)

    print(f"  Processed {len(df)}/{len(df)} records... Done!")

    # Create enriched dataframe
    enriched_df = pd.DataFrame(enriched_rows)

    # Save if output file specified
    if output_file:
        print(f"\nSaving enriched dataset to {output_file}...")
        if output_file.endswith('.gz'):
            enriched_df.to_csv(output_file, index=False, compression='gzip')
        elif output_file.endswith('.parquet'):
            enriched_df.to_parquet(output_file, index=False)
        else:
            enriched_df.to_csv(output_file, index=False)
        print(f"Saved!")

    return enriched_df


def generate_summary(df: pd.DataFrame) -> ExportDataSummary:
    """
    Generate summary statistics from enriched dataset.

    Args:
        df: Enriched DataFrame

    Returns:
        ExportDataSummary object
    """
    print("\nGenerating summary statistics...")

    # Convert date column if it's a string
    df['Date'] = pd.to_datetime(df['Date'])

    # Basic stats
    total_records = len(df)
    date_range_start = df['Date'].min()
    date_range_end = df['Date'].max()
    total_mt = df['net_weight_mt'].sum()
    total_fob_usd = df['U$ FOB Tot'].sum()
    avg_usd_per_mt = total_fob_usd / total_mt if total_mt > 0 else 0

    # Group by fruit
    by_fruit = df.groupby('fruit_name')['net_weight_mt'].sum().to_dict()

    # Group by format
    by_format = df.groupby('format_type')['net_weight_mt'].sum().to_dict()

    # Group by size
    by_size = df.groupby('size_mm')['net_weight_mt'].sum().to_dict()

    # Unique counts
    unique_exporters = df['Exporter'].nunique()
    unique_destinations = df['Destination Country'].nunique()

    # Top destinations by MT
    top_destinations = df.groupby('Destination Country')['net_weight_mt'].sum().nlargest(10).to_dict()

    # Product summaries: Fruit → Format → Size
    product_summaries = []
    grouped = df.groupby(['fruit_name', 'format_type', 'size_mm', 'certification'])

    for (fruit, format_type, size_mm, cert), group in grouped:
        summary = ProductSummary(
            fruit_name=fruit,
            format_type=format_type,
            size_mm=size_mm,
            certification=cert,
            total_mt=round(group['net_weight_mt'].sum(), 3),
            avg_usd_per_mt=round(group['usd_per_mt_fob'].mean(), 2),
            record_count=len(group),
            total_fob_usd=round(group['U$ FOB Tot'].sum(), 2)
        )
        product_summaries.append(summary)

    # Sort by total MT descending
    product_summaries.sort(key=lambda x: x.total_mt, reverse=True)

    return ExportDataSummary(
        total_records=total_records,
        date_range_start=date_range_start,
        date_range_end=date_range_end,
        total_mt=round(total_mt, 3),
        total_fob_usd=round(total_fob_usd, 2),
        avg_usd_per_mt=round(avg_usd_per_mt, 2),
        by_fruit=by_fruit,
        by_format=by_format,
        by_size=by_size,
        product_summaries=product_summaries,
        unique_exporters=unique_exporters,
        unique_destination_countries=unique_destinations,
        top_destinations=top_destinations
    )


def main():
    """Main execution function."""
    from config_loader import load_config, get_input_path, get_output_path

    # Load configuration
    config = load_config()

    # Get paths from config
    input_file = str(get_input_path(config, 'combined_csv'))
    # enriched_csv is in inputs section (it's input to create_database.py)
    output_csv_gz = str(get_input_path(config, 'enriched_csv'))
    output_csv = output_csv_gz.replace('.gz', '')  # Temporary uncompressed file
    summary_json = str(get_output_path(config, 'export_summary'))
    validation_json = str(get_output_path(config, 'data_validation'))

    # Enrich the dataset
    enriched_df = enrich_dataset(input_file, output_csv_gz)

    print(f"\nEnriched dataset shape: {enriched_df.shape}")
    print(f"\nNew columns added:")
    new_cols = ['fruit_name', 'variety', 'format_type', 'size_mm', 'is_organic',
                'is_conventional', 'is_iqf', 'certification', 'net_weight_mt', 'usd_per_mt_fob']
    for col in new_cols:
        print(f"  - {col}")

    # Validate data quality
    validation_results = validate_enriched_data(enriched_df)

    # Save validation results
    print(f"Saving validation results to {validation_json}...")
    with open(validation_json, 'w') as f:
        json.dump(validation_results, f, indent=2, default=str)

    # Generate summary
    summary = generate_summary(enriched_df)

    # Save summary as JSON
    print(f"\nSaving summary to {summary_json}...")
    with open(summary_json, 'w') as f:
        json.dump(summary.model_dump(mode='json'), f, indent=2, default=str)

    # Print summary
    print("\n" + "="*80)
    print("EXPORT DATA SUMMARY")
    print("="*80)
    print(f"Total Records: {summary.total_records:,}")
    print(f"Date Range: {summary.date_range_start.date()} to {summary.date_range_end.date()}")
    print(f"Total Volume: {summary.total_mt:,.2f} MT")
    print(f"Total FOB Value: ${summary.total_fob_usd:,.2f} USD")
    print(f"Average Price: ${summary.avg_usd_per_mt:,.2f} USD/MT")
    print(f"Unique Exporters: {summary.unique_exporters}")
    print(f"Unique Destinations: {summary.unique_destination_countries}")

    print("\n" + "-"*80)
    print("TOP 10 PRODUCTS (by MT)")
    print("-"*80)
    print(f"{'Fruit':<15} {'Format':<15} {'Size':<10} {'Cert':<15} {'MT':>12} {'USD/MT':>12} {'Records':>8}")
    print("-"*80)

    for i, prod in enumerate(summary.product_summaries[:10], 1):
        size_display = prod.size_mm or "N/A"
        print(f"{prod.fruit_name:<15} {prod.format_type:<15} {size_display:<10} "
              f"{prod.certification:<15} {prod.total_mt:>12,.2f} {prod.avg_usd_per_mt:>12,.2f} "
              f"{prod.record_count:>8,}")

    print("\n" + "-"*80)
    print("BY FRUIT")
    print("-"*80)
    for fruit, mt in sorted(summary.by_fruit.items(), key=lambda x: x[1], reverse=True):
        print(f"{fruit:<20} {mt:>12,.2f} MT")

    print("\n" + "-"*80)
    print("TOP DESTINATIONS")
    print("-"*80)
    for country, mt in list(summary.top_destinations.items())[:10]:
        print(f"{country:<30} {mt:>12,.2f} MT")

    print("\n" + "="*80)
    print(f"Enriched data saved to: {output_csv_gz}")
    print(f"Summary saved to: {summary_json}")
    print("="*80)


if __name__ == "__main__":
    main()
