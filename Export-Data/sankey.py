#!/usr/bin/env python3
"""
Generate Sankey diagram data in Mermaid format from export data.
Flow: Exporter → Fruit → Country → Importer
Default: Mango exports to Europe only
"""

import pandas as pd
import sqlite3
from pathlib import Path
from typing import List, Tuple, Optional


def read_export_data(
    file_path: str = "exports.db",
    product_filter: Optional[str] = None,
    region_filter: Optional[str] = None
) -> pd.DataFrame:
    """Read export data from database, CSV, or Excel file."""
    path = Path(file_path)

    if path.suffix == '.db':
        conn = sqlite3.connect(file_path)
        # Read from database, selecting relevant columns
        query = """
        SELECT
            Exporter,
            canonical_exporter,
            Importer,
            canonical_importer,
            [Destination Country],
            destination_country_en,
            fruit_name,
            variety,
            format_type,
            region,
            [U$ FOB Tot] as FOB_Value,
            net_weight_mt,
            Date
        FROM exports
        WHERE analysis_valid = 1
        """
        df = pd.read_sql_query(query, conn)
        conn.close()

        # Create standardized columns
        df['Exporter_Name'] = df['canonical_exporter'].fillna(df['Exporter']).fillna('Unknown Exporter')
        df['Importer_Name'] = df['canonical_importer'].fillna(df['Importer']).fillna('Unknown Importer')
        df['Fruit'] = df['fruit_name'].str.title().fillna('Unknown Fruit')
        df['Country'] = df['destination_country_en'].fillna(df['Destination Country']).fillna('Unknown Country')
        df['MT'] = df['net_weight_mt'].fillna(0)

        # Filter by product if specified
        if product_filter:
            df = df[df['Fruit'].str.lower() == product_filter.lower()]

        # Filter by region if specified
        if region_filter:
            df = df[df['region'].str.lower() == region_filter.lower()]

        return df
    elif path.suffix == '.csv':
        return pd.read_csv(file_path)
    elif path.suffix in ['.xlsx', '.xls']:
        return pd.read_excel(file_path)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")


def aggregate_small_players(
    df: pd.DataFrame,
    group_col: str,
    value_col: str,
    others_percentage: float = 0.20,
    others_label: str = "Others"
) -> pd.DataFrame:
    """
    Aggregate small players into 'Others' category.

    Args:
        df: DataFrame with flow data
        group_col: Column to aggregate (e.g., 'Exporter_Name')
        value_col: Value column (e.g., 'MT')
        others_percentage: Target percentage for 'Others' category (default 0.20 = 20%)
        others_label: Label for aggregated category (default: 'Others')

    Returns:
        DataFrame with small players aggregated to specified label
    """
    # Calculate total volume per player
    player_totals = df.groupby(group_col)[value_col].sum().sort_values(ascending=False)
    total_volume = player_totals.sum()

    # Calculate cumulative percentage
    cumulative_pct = player_totals.cumsum() / total_volume

    # Find the threshold: players that together represent the top (1 - others_percentage)
    # Keep players until we hit (1 - others_percentage) of total volume
    keep_threshold = 1 - others_percentage
    players_to_keep = cumulative_pct[cumulative_pct <= keep_threshold].index.tolist()

    # If we have very few players, keep at least the top ones
    if len(players_to_keep) < 3:
        players_to_keep = player_totals.head(max(3, int(len(player_totals) * 0.8))).index.tolist()

    # Create a copy of the dataframe
    df_agg = df.copy()

    # Replace small players with specified label
    df_agg.loc[~df_agg[group_col].isin(players_to_keep), group_col] = others_label

    return df_agg


def format_mermaid_sankey(
    flows: List[Tuple[str, str, float]],
    show_values: bool = False,
    title: Optional[str] = None,
    decimal_places: int = 0
) -> str:
    """
    Format flows as Mermaid sankey diagram.

    Args:
        flows: List of (source, target, value) tuples
        show_values: Whether to show values in the diagram
        title: Optional title for the diagram
        decimal_places: Number of decimal places for values

    Returns:
        Mermaid formatted string
    """
    lines = []

    # Add header
    lines.append("---")
    lines.append("config:")
    lines.append("  sankey:")
    lines.append(f"    showValues: {str(show_values).lower()}")
    lines.append("---")
    lines.append("sankey-beta")
    lines.append("")

    # Add title if provided
    if title:
        lines.append(f"%% {title}")
        lines.append("")

    # Add flows
    for source, target, value in flows:
        # Clean node names (remove special characters that break Mermaid)
        def clean_name(name):
            name = str(name)
            # Replace accented characters
            replacements = {
                'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
                'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
                'ñ': 'n', 'Ñ': 'N', 'ü': 'u', 'Ü': 'U',
                ',': ' -', '"': "'", '/': '-', '(': '', ')': '',
                '&': 'and'
            }
            for old, new in replacements.items():
                name = name.replace(old, new)
            return name.strip()

        source_clean = clean_name(source)
        target_clean = clean_name(target)

        # Format value with specified decimal places
        if decimal_places == 0:
            lines.append(f"{source_clean},{target_clean},{int(round(value))}")
        else:
            lines.append(f"{source_clean},{target_clean},{value:.{decimal_places}f}")

    return "\n".join(lines)


def create_supply_chain_sankey(
    df: pd.DataFrame,
    value_col: str = 'MT',
    min_value: Optional[float] = None,
    top_n: Optional[int] = None,
    aggregate_others: bool = True,
    others_percentage: float = 0.20
) -> str:
    """
    Create sankey diagram. If only one fruit, creates Exporter → Importer → Country.
    If multiple fruits, creates Exporter → Fruit → Importer → Country.
    """
    # Aggregate small players if requested with distinct labels to avoid circular references
    if aggregate_others:
        df = aggregate_small_players(df, 'Exporter_Name', value_col, others_percentage, 'Other Exporters')
        df = aggregate_small_players(df, 'Importer_Name', value_col, others_percentage, 'Other Importers')
        df = aggregate_small_players(df, 'Country', value_col, others_percentage, 'Other Countries')

    all_flows = []

    # Check if we have only one fruit type
    unique_fruits = df['Fruit'].nunique()

    if unique_fruits == 1:
        # Skip fruit level when only one product - creates Exporter → Importer → Country
        # 1. Exporter → Importer flows
        exporter_importer = df.groupby(['Exporter_Name', 'Importer_Name'])[value_col].sum().reset_index()
        flows1 = list(exporter_importer.itertuples(index=False, name=None))
        all_flows.extend(flows1)

        # 2. Importer → Country flows
        importer_country = df.groupby(['Importer_Name', 'Country'])[value_col].sum().reset_index()
        flows2 = list(importer_country.itertuples(index=False, name=None))
        all_flows.extend(flows2)

        flow_title = f"{df['Fruit'].iloc[0]}: Exporter → Importer → Country (MT)"
    else:
        # Include fruit level when multiple products
        # 1. Exporter → Fruit flows
        exporter_fruit = df.groupby(['Exporter_Name', 'Fruit'])[value_col].sum().reset_index()
        flows1 = list(exporter_fruit.itertuples(index=False, name=None))
        all_flows.extend(flows1)

        # 2. Fruit → Importer flows
        fruit_importer = df.groupby(['Fruit', 'Importer_Name'])[value_col].sum().reset_index()
        flows2 = list(fruit_importer.itertuples(index=False, name=None))
        all_flows.extend(flows2)

        # 3. Importer → Country flows
        importer_country = df.groupby(['Importer_Name', 'Country'])[value_col].sum().reset_index()
        flows3 = list(importer_country.itertuples(index=False, name=None))
        all_flows.extend(flows3)

        flow_title = "Exporter → Fruit → Importer → Country (MT)"

    # Apply filters if specified
    if min_value is not None:
        all_flows = [(s, t, v) for s, t, v in all_flows if v >= min_value]

    # Sort by value
    all_flows = sorted(all_flows, key=lambda x: x[2], reverse=True)

    # Apply top_n if specified
    if top_n is not None:
        all_flows = all_flows[:top_n]

    # Use 0 decimal places for MT
    decimal_places = 0 if value_col == 'MT' else 3

    return format_mermaid_sankey(
        all_flows,
        title=flow_title,
        decimal_places=decimal_places
    )


def main():
    """Main function to demonstrate usage."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Generate Mermaid Sankey diagram: Exporter → Fruit → Importer → Country (Default: Mango to Europe)'
    )
    parser.add_argument('input_file', nargs='?', default='exports.db',
                        help='Input database, CSV or Excel file (default: exports.db)')
    parser.add_argument('-o', '--output', default='sankey-data.mmd',
                        help='Output file (default: sankey-data.mmd)')
    parser.add_argument('-p', '--product', default='Mango',
                        help='Filter by product/fruit (default: Mango, use "all" for all products)')
    parser.add_argument('-r', '--region', default='Europe',
                        help='Filter by region (default: Europe, use "all" for all regions)')
    parser.add_argument('-v', '--value-col', default='MT',
                        help='Column to use for flow values (default: MT)')
    parser.add_argument('--min-value', type=float, help='Minimum value threshold')
    parser.add_argument('--top-n', type=int,
                        help='Only show top N flows')
    parser.add_argument('--no-aggregate', action='store_true',
                        help='Disable aggregation of small players into Others')
    parser.add_argument('--others-pct', type=float, default=0.20,
                        help='Target percentage for Others category (default: 0.20 = 20%%)')
    parser.add_argument('--show-values', action='store_true',
                        help='Show values in diagram')
    parser.add_argument('--no-png', action='store_true',
                        help='Skip PNG generation (only generate .mmd file)')
    parser.add_argument('--stdout', action='store_true',
                        help='Print to stdout instead of file')

    args = parser.parse_args()

    # Handle "all" filters
    product_filter = None if args.product.lower() == 'all' else args.product
    region_filter = None if args.region.lower() == 'all' else args.region

    # Read data
    print(f"Reading data from {args.input_file}...")
    df = read_export_data(args.input_file, product_filter=product_filter, region_filter=region_filter)

    filter_desc = []
    if product_filter:
        filter_desc.append(f"{product_filter}")
    if region_filter:
        filter_desc.append(f"to {region_filter}")

    print(f"Loaded {len(df)} records" + (f" ({' '.join(filter_desc)})" if filter_desc else ""))

    # Generate sankey
    print(f"Generating Exporter → Fruit → Importer → Country sankey...")
    output = create_supply_chain_sankey(
        df,
        value_col=args.value_col,
        min_value=args.min_value,
        top_n=args.top_n,
        aggregate_others=not args.no_aggregate,
        others_percentage=args.others_pct
    )

    # Update show_values if needed
    if args.show_values:
        output = output.replace('showValues: false', 'showValues: true')

    # Write output
    if args.stdout:
        print(output)
    else:
        with open(args.output, 'w') as f:
            f.write(output)
        print(f"✓ Sankey diagram written to {args.output}")
        if product_filter:
            print(f"  Product: {product_filter}")
        if region_filter:
            print(f"  Region: {region_filter}")
        print(f"  Flow count: {output.count(chr(10)) - 7}")  # Rough count of flows
        print(f"  Value column: {args.value_col}")
        if not args.no_aggregate:
            print(f"  Others aggregation: ~{args.others_pct*100:.0f}%")

        # Generate PNG by default
        if not args.no_png:
            import subprocess
            import os

            png_output = args.output.replace('.mmd', '.png')
            print(f"\nGenerating PNG...")
            try:
                result = subprocess.run(
                    ['mmdc', '-i', args.output, '-o', png_output,
                     '-w', '1920', '-H', '1080', '-b', 'transparent', '-s', '2'],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                if result.returncode == 0:
                    # Get file size
                    size_mb = os.path.getsize(png_output) / (1024 * 1024)
                    print(f"✓ PNG image written to {png_output} ({size_mb:.1f}MB)")
                else:
                    print(f"⚠ Failed to generate PNG: {result.stderr}")
            except FileNotFoundError:
                print(f"⚠ mmdc (mermaid-cli) not found. Install with: npm install -g @mermaid-js/mermaid-cli")
            except subprocess.TimeoutExpired:
                print(f"⚠ PNG generation timed out")
            except Exception as e:
                print(f"⚠ Error generating PNG: {e}")


if __name__ == '__main__':
    main()
