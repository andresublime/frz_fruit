"""
Interactive GUI wrapper for the Frozen Fruit Export Analysis CLI.
Supports: Peru, Ecuador

IMPORTANT: Peru and Ecuador data are always kept separate and never combined.

Usage:
    python cli/gui.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

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


def get_choice(prompt, choices, allow_empty=False):
    """Get user choice from a list of options."""
    print(f"\n{prompt}")
    for i, choice in enumerate(choices, 1):
        print(f"  {i}. {choice}")
    if allow_empty:
        print(f"  {len(choices) + 1}. None (skip)")

    while True:
        try:
            choice = input("\nEnter number: ").strip()
            if not choice and allow_empty:
                return None
            idx = int(choice) - 1
            if allow_empty and idx == len(choices):
                return None
            if 0 <= idx < len(choices):
                return choices[idx]
            print(f"Please enter a number between 1 and {len(choices) + (1 if allow_empty else 0)}")
        except (ValueError, KeyboardInterrupt):
            print("Invalid input. Please enter a number.")


def get_input(prompt, allow_empty=False):
    """Get text input from user."""
    while True:
        value = input(f"\n{prompt}: ").strip()
        if value or allow_empty:
            return value if value else None
        print("This field is required.")


def get_number(prompt, default=None):
    """Get numeric input from user."""
    while True:
        value = input(f"\n{prompt} (default: {default}): ").strip()
        if not value and default is not None:
            return default
        try:
            return int(value)
        except ValueError:
            print("Please enter a valid number.")


def run_summary():
    """Run pricing summary command interactively."""
    print("\n" + "=" * 80)
    print("PRICING SUMMARY")
    print("=" * 80)

    # Get dimension
    dimension = get_choice(
        "Select dimension to summarize:",
        ['fruit', 'exporter', 'importer']
    )

    # Get source country
    source_country = get_choice(
        "Filter by source country? (Peru and Ecuador are always shown separately)",
        ['Peru', 'Ecuador', 'Both (show separately)'],
        allow_empty=False
    )
    if source_country == 'Both (show separately)':
        source_country = None
    else:
        source_country = source_country.lower()

    # Get region
    region = get_choice(
        "Filter by region?",
        ['Europe', 'RoW', 'Worldwide'],
        allow_empty=False
    )
    if region == 'Worldwide':
        region = None

    # Get limit
    limit = get_number("Number of results to display", default=20)

    # Get output
    output = get_input("Export to CSV? (enter file path or leave empty to skip)", allow_empty=True)

    # Execute
    print(f"\nCalculating {dimension} pricing summary...")
    df = calculate_pricing_summary(
        dimension=dimension,
        region=region,
        source_country=source_country
    )

    if len(df) == 0:
        print("No data found for the specified criteria.")
        return

    # Display
    title = f"{dimension.title()} Pricing Summary (YTD Oct 2024 - Oct 2025)"
    if source_country:
        title += f" - {source_country.title()}"
    if region:
        title += f" - {region}"

    display_table(df.head(limit), title)

    # Export if requested
    if output:
        export_to_csv(df, output, include_records=True)
        print(f"\n✓ Exported to {output}")

    print(f"Total: {len(df)} rows")


def run_drill():
    """Run pricing drill-down command interactively."""
    print("\n" + "=" * 80)
    print("PRICING DRILL-DOWN")
    print("=" * 80)

    # Get filter dimension
    filter_dimension = get_choice(
        "What are you filtering by?",
        ['fruit', 'exporter', 'importer']
    )

    # Get filter value
    filter_value = get_input(f"Enter {filter_dimension} name (e.g., 'mango', 'Viru')")

    # Get breakdown dimension
    by = get_choice(
        "Break down results by:",
        ['fruit', 'exporter', 'importer', 'format']
    )

    # Get source country
    source_country = get_choice(
        "Filter by source country? (Peru and Ecuador are always shown separately)",
        ['Peru', 'Ecuador', 'Both (show separately)'],
        allow_empty=False
    )
    if source_country == 'Both (show separately)':
        source_country = None
    else:
        source_country = source_country.lower()

    # Get region
    region = get_choice(
        "Filter by region?",
        ['Europe', 'RoW', 'Worldwide'],
        allow_empty=False
    )
    if region == 'Worldwide':
        region = None

    # Get limit
    limit = get_number("Number of results to display", default=20)

    # Get output
    output = get_input("Export to CSV? (enter file path or leave empty to skip)", allow_empty=True)

    # Execute
    print(f"\nCalculating {filter_dimension}={filter_value} by {by}...")
    df = calculate_pricing_drill_down(
        filter_dimension=filter_dimension,
        filter_value=filter_value,
        by=by,
        region=region,
        source_country=source_country
    )

    if len(df) == 0:
        print(f"No data found for {filter_dimension}='{filter_value}'")
        return

    # Display
    title = f"{filter_value.title()} Pricing by {by.title()}"
    if source_country:
        title += f" - {source_country.title()}"
    if region:
        title += f" - {region}"

    display_table(df.head(limit), title)

    # Export if requested
    if output:
        export_to_csv(df, output, include_records=True)
        print(f"\n✓ Exported to {output}")

    print(f"Total: {len(df)} rows")


def run_export():
    """Run CSV export command interactively."""
    print("\n" + "=" * 80)
    print("EXPORT TO CSV")
    print("=" * 80)

    # Get dimension
    dimension = get_choice(
        "Select dimension to export:",
        ['fruit', 'exporter', 'importer']
    )

    # Get source country
    source_country = get_choice(
        "Filter by source country? (Peru and Ecuador are always shown separately)",
        ['Peru', 'Ecuador', 'Both (show separately)'],
        allow_empty=False
    )
    if source_country == 'Both (show separately)':
        source_country = None
    else:
        source_country = source_country.lower()

    # Get region
    region = get_choice(
        "Filter by region?",
        ['Europe', 'RoW', 'Worldwide'],
        allow_empty=False
    )
    if region == 'Worldwide':
        region = None

    # Get output
    output = get_input("Output CSV file path")

    # Execute
    print(f"\nGenerating {dimension} pricing summary...")
    df = calculate_pricing_summary(
        dimension=dimension,
        region=region,
        source_country=source_country
    )

    export_to_csv(df, output, include_records=False)
    print(f"✓ Exported {len(df)} records to {output}")


def main():
    """Main interactive loop."""
    print("\n" + "=" * 80)
    print("FROZEN FRUIT EXPORT ANALYSIS (PERU & ECUADOR)")
    print("Interactive Shell")
    print("=" * 80)

    while True:
        command = get_choice(
            "\nWhat would you like to do?",
            ['Summary - View pricing by dimension',
             'Drill-down - Analyze specific entity',
             'Export - Save full data to CSV',
             'Exit']
        )

        try:
            if 'Summary' in command:
                run_summary()
            elif 'Drill-down' in command:
                run_drill()
            elif 'Export' in command:
                run_export()
            elif 'Exit' in command:
                print("\nGoodbye!")
                break

            # Ask if user wants to continue
            continue_choice = input("\nPress Enter to continue, or 'q' to quit: ").strip().lower()
            if continue_choice == 'q':
                print("\nGoodbye!")
                break

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")
            print("Please try again.")


if __name__ == "__main__":
    main()
