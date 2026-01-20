"""
Frozen Fruit Export Analysis - Command Line Interface
Supports: Peru, Ecuador

Unified interface for all pricing analytics and reporting.
IMPORTANT: Peru and Ecuador data are always kept separate and never combined.

Usage:
    python cli/main.py summary fruit
    python cli/main.py summary exporter --source-country peru
    python cli/main.py summary importer --region Europe
    python cli/main.py drill mango --by exporter
    python cli/main.py drill Viru --by fruit --source-country ecuador
    python cli/main.py drill "Salud Foodgroup Europe" --filter-dimension importer --by fruit
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
from analysis.pricing import (
    calculate_pricing_summary,
    calculate_pricing_drill_down,
    export_to_csv,
)


def display_table(df, title=None):
    """Display DataFrame as formatted table."""
    if title:
        print(f"\n{title}")
        print("=" * 80)

    print(df.to_string(index=False))
    print()


def cmd_summary(args):
    """Generate pricing summary by dimension."""
    dimension = args.dimension

    if dimension not in ['fruit', 'exporter', 'importer']:
        print(f"Error: Invalid dimension '{dimension}'. Must be: fruit, exporter, or importer")
        return 1

    print(f"\nCalculating {dimension} pricing summary...")
    df = calculate_pricing_summary(
        dimension=dimension,
        region=args.region,
        source_country=args.source_country
    )

    if len(df) == 0:
        print("No data found for the specified criteria.")
        return 0

    # Display
    title = f"{dimension.title()} Pricing Summary (YTD Oct 2024 - Oct 2025)"
    if args.source_country:
        title += f" - {args.source_country.title()}"
    if args.region:
        title += f" - {args.region}"

    display_table(df.head(args.limit), title)

    # Export if requested
    if args.output:
        export_to_csv(df, args.output, include_records=True)

    print(f"Total: {len(df)} rows")
    return 0


def cmd_drill(args):
    """Drill down pricing for a specific entity."""
    filter_value = args.filter_value
    by = args.by

    if by not in ['fruit', 'exporter', 'importer', 'format']:
        print(f"Error: Invalid --by dimension '{by}'. Must be: fruit, exporter, importer, or format")
        return 1

    # Determine filter dimension
    filter_dimension = args.filter_dimension

    if filter_dimension not in ['fruit', 'exporter', 'importer']:
        print(f"Error: Invalid filter dimension '{filter_dimension}'. Must be: fruit, exporter, or importer")
        print("Note: 'format' cannot be used as a filter (formats are fruit-specific)")
        return 1

    print(f"\nCalculating {filter_dimension}={filter_value} by {by}...")
    df = calculate_pricing_drill_down(
        filter_dimension=filter_dimension,
        filter_value=filter_value,
        by=by,
        region=args.region,
        source_country=args.source_country
    )

    if len(df) == 0:
        print(f"No data found for {filter_dimension}='{filter_value}'")
        return 0

    # Display
    title = f"{filter_value.title()} Pricing by {by.title()}"
    if args.source_country:
        title += f" - {args.source_country.title()}"
    if args.region:
        title += f" - {args.region}"

    display_table(df.head(args.limit), title)

    # Export if requested
    if args.output:
        export_to_csv(df, args.output, include_records=True)

    print(f"Total: {len(df)} rows")
    return 0


def cmd_export(args):
    """Export full pricing summary to CSV."""
    dimension = args.dimension

    if dimension not in ['fruit', 'exporter', 'importer']:
        print(f"Error: Invalid dimension '{dimension}'. Must be: fruit, exporter, or importer")
        return 1

    print(f"\nGenerating {dimension} pricing summary...")
    df = calculate_pricing_summary(
        dimension=dimension,
        region=args.region,
        source_country=args.source_country
    )

    export_to_csv(df, args.output, include_records=False)
    print(f"✓ Exported {len(df)} records to {args.output}")
    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Frozen Fruit Export Analysis CLI (Peru & Ecuador)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Summary command
    summary_parser = subparsers.add_parser('summary', help='Generate pricing summary')
    summary_parser.add_argument('dimension', choices=['fruit', 'exporter', 'importer'],
                                help='Dimension to summarize (format not valid as standalone)')
    summary_parser.add_argument('--source-country', dest='source_country', choices=['peru', 'ecuador'],
                                help='Filter by source country (default: show both separately)')
    summary_parser.add_argument('--region', choices=['Europe', 'RoW'],
                                help='Region filter (default: worldwide)')
    summary_parser.add_argument('--output', help='Output CSV file path')
    summary_parser.add_argument('--limit', type=int, default=20,
                                help='Number of results to display (default: 20)')

    # Drill command
    drill_parser = subparsers.add_parser('drill', help='Drill down pricing')
    drill_parser.add_argument('filter_value', help='Value to filter (e.g., mango, Viru, "Salud Foodgroup Europe")')
    drill_parser.add_argument('--by', required=True, choices=['fruit', 'exporter', 'importer', 'format'],
                             help='Dimension to drill down by (format only valid when filtering by fruit)')
    drill_parser.add_argument('--filter-dimension', dest='filter_dimension',
                             choices=['fruit', 'exporter', 'importer'], default='fruit',
                             help='Filter dimension (default: fruit, format not allowed)')
    drill_parser.add_argument('--source-country', dest='source_country', choices=['peru', 'ecuador'],
                             help='Filter by source country (default: show both separately)')
    drill_parser.add_argument('--region', choices=['Europe', 'RoW'],
                             help='Region filter (default: worldwide)')
    drill_parser.add_argument('--output', help='Output CSV file path')
    drill_parser.add_argument('--limit', type=int, default=20,
                             help='Number of results to display (default: 20)')

    # Export command
    export_parser = subparsers.add_parser('export', help='Export pricing to CSV')
    export_parser.add_argument('dimension', choices=['fruit', 'exporter', 'importer'],
                              help='Dimension to export (format not valid as standalone)')
    export_parser.add_argument('output', help='Output CSV file path')
    export_parser.add_argument('--source-country', dest='source_country', choices=['peru', 'ecuador'],
                              help='Filter by source country (default: show both separately)')
    export_parser.add_argument('--region', choices=['Europe', 'RoW'],
                              help='Region filter (default: worldwide)')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Route to command handler
    if args.command == 'summary':
        return cmd_summary(args)
    elif args.command == 'drill':
        return cmd_drill(args)
    elif args.command == 'export':
        return cmd_export(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
