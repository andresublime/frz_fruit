#!/usr/bin/env python3
"""Generate Sankey diagrams for Ecuador exports to Germany"""
import sys
from pathlib import Path

# Add parent directory to path to import sankey module
sys.path.insert(0, str(Path(__file__).parent.parent))

from sankey import read_export_data, create_supply_chain_sankey

def main():
    """Generate Ecuador to Germany sankey diagram"""
    DB_PATH = "../data/exports.db"
    OUTPUT_DIR = Path(__file__).parent / "ecuador" / "germany"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("="*60)
    print("Generating Ecuador → Germany Sankey Diagram")
    print("="*60)

    # Read all export data
    print(f"\nReading data from {DB_PATH}...")
    df = read_export_data(
        DB_PATH,
        product_filter=None,
        region_filter=None
    )

    # Filter to Ecuador and Germany only
    if 'source_country' not in df.columns:
        print("ERROR: source_country column not found in database!")
        sys.exit(1)

    df_ecuador = df[df['source_country'] == 'ecuador'].copy()
    df_ecuador_germany = df_ecuador[df_ecuador['Country'] == 'Germany'].copy()

    print(f"Ecuador exports to Germany: {len(df_ecuador_germany)} records")
    print(f"Total MT: {df_ecuador_germany['MT'].sum():.0f}")

    if len(df_ecuador_germany) == 0:
        print("No Ecuador exports to Germany found!")
        sys.exit(1)

    # Show fruit breakdown
    print("\nFruit breakdown:")
    fruit_totals = df_ecuador_germany.groupby('Fruit')['MT'].sum().sort_values(ascending=False)
    for fruit, mt in fruit_totals.items():
        print(f"  {fruit}: {mt:.0f} MT")

    # Generate sankey for all fruits
    print("\nGenerating Exporter → Fruit → Importer → Country sankey...")
    output = create_supply_chain_sankey(
        df_ecuador_germany,
        value_col='MT',
        aggregate_others=True,
        others_percentage=0.20,
        font_size=18
    )

    # Update to show values
    output = output.replace('showValues: false', 'showValues: true')

    # Write mermaid file
    mmd_file = OUTPUT_DIR / "sankey-ecuador-germany-all-fruits.mmd"
    mmd_file.write_text(output)
    print(f"\n✓ Mermaid file: {mmd_file}")

    # Generate PNG using mmdc
    png_file = OUTPUT_DIR / "sankey-ecuador-germany-all-fruits.png"
    print(f"Generating PNG: {png_file}...")

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
            print(f"✓ PNG: {png_file} ({size_mb:.1f}MB)")
        else:
            print(f"⚠ Failed to generate PNG: {result.stderr}")
    except FileNotFoundError:
        print(f"⚠ mmdc not found. Install with: npm install -g @mermaid-js/mermaid-cli")
    except Exception as e:
        print(f"⚠ Error generating PNG: {e}")

    print("\n" + "="*60)
    print("✓ Ecuador → Germany Sankey complete!")
    print("="*60)

if __name__ == '__main__':
    main()
