#!/usr/bin/env python3
"""Generate individual Sankey diagrams for each fruit from Peru to Europe"""
import sys
from pathlib import Path

# Add parent directory to path to import sankey module
sys.path.insert(0, str(Path(__file__).parent.parent))

from sankey import read_export_data, create_supply_chain_sankey

def main():
    """Generate Peru to Europe sankey diagrams per fruit"""
    DB_PATH = "../data/exports.db"
    OUTPUT_DIR = Path(__file__).parent / "peru" / "europe"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("="*60)
    print("Generating Peru → Europe Sankey Diagrams PER FRUIT")
    print("="*60)

    # Read Peru exports to Europe
    print(f"\nReading data from {DB_PATH}...")
    df = read_export_data(
        DB_PATH,
        product_filter=None,
        region_filter='Europe'
    )

    # Filter to Peru only
    if 'source_country' not in df.columns:
        print("ERROR: source_country column not found in database!")
        sys.exit(1)

    df_peru = df[df['source_country'] == 'peru'].copy()
    print(f"Peru exports to Europe: {len(df_peru)} records")
    print(f"Total MT: {df_peru['MT'].sum():.0f}")

    # Get top fruits (> 1000 MT)
    fruit_totals = df_peru.groupby('Fruit')['MT'].sum().sort_values(ascending=False)
    top_fruits = fruit_totals[fruit_totals > 1000].index.tolist()

    print(f"\nGenerating diagrams for {len(top_fruits)} fruits (> 1000 MT):")
    for fruit in top_fruits:
        print(f"  • {fruit}: {fruit_totals[fruit]:.0f} MT")

    # Process each fruit
    for fruit_name in top_fruits:
        print(f"\n{'='*60}")
        print(f"Processing: {fruit_name}")
        print('='*60)

        # Filter to this fruit
        df_fruit = df_peru[df_peru['Fruit'] == fruit_name].copy()

        print(f"  Records: {len(df_fruit)}")
        print(f"  Total MT: {df_fruit['MT'].sum():.0f}")
        print(f"  Exporters: {df_fruit['Exporter_Name'].nunique()}")
        print(f"  Importers: {df_fruit['Importer_Name'].nunique()}")

        # Generate sankey with min_value filtering + moderate aggregation
        total_mt = df_fruit['MT'].sum()
        min_threshold = total_mt * 0.02  # Only show flows >= 2% of total

        output = create_supply_chain_sankey(
            df_fruit,
            value_col='MT',
            min_value=min_threshold,
            aggregate_others=True,
            others_percentage=0.30,
            font_size=18
        )

        # Update to show values
        output = output.replace('showValues: false', 'showValues: true')

        # Write mermaid file
        fruit_key = fruit_name.lower().replace(' ', '_').replace('_', '-')
        mmd_file = OUTPUT_DIR / f"sankey-peru-europe-{fruit_key}.mmd"
        mmd_file.write_text(output)

        flow_count = output.count('\n') - 12
        print(f"  ✓ Mermaid: {mmd_file.name} ({flow_count} flows)")

        # Generate PNG
        png_file = OUTPUT_DIR / f"sankey-peru-europe-{fruit_key}.png"
        print(f"  Generating PNG: {png_file.name}...")

        import subprocess
        try:
            result = subprocess.run(
                ['mmdc', '-i', str(mmd_file), '-o', str(png_file),
                 '-w', '1920', '-H', '1080', '-b', 'transparent', '-s', '2'],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                size_mb = png_file.stat().st_size / (1024 * 1024)
                print(f"  ✓ PNG: {png_file.name} ({size_mb:.1f}MB)")
            else:
                print(f"  ⚠ Failed: {result.stderr}")
        except FileNotFoundError:
            print(f"  ⚠ mmdc not found")
        except Exception as e:
            print(f"  ⚠ Error: {e}")

    print("\n" + "="*60)
    print(f"✓ Generated {len(top_fruits)} Peru → Europe per-fruit diagrams!")
    print("="*60)

if __name__ == '__main__':
    main()
