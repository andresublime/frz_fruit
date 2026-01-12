#!/usr/bin/env python3
"""Generate individual Sankey diagrams for each fruit to Germany"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from sankey import read_export_data, format_mermaid_sankey
import pandas as pd

def mermaid_to_png_playwright(mermaid_code, output_file, title="Sankey Diagram"):
    """Convert mermaid code to PNG using Playwright"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print(f"  ⚠ Playwright not available for {output_file}")
        return False

    # Create a simple HTML page with mermaid
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            background: white;
        }}
        #diagram {{
            display: inline-block;
        }}
    </style>
</head>
<body>
    <div id="diagram"></div>
    <script>
        mermaid.initialize({{
            startOnLoad: false,
            theme: 'base',
            themeVariables: {{
                fontSize: '18px'
            }},
            sankey: {{
                showValues: true,
                width: 1400,
                height: 700
            }}
        }});

        mermaid.render('mermaid-svg', `{mermaid_code}`)
            .then(result => {{
                document.getElementById('diagram').innerHTML = result.svg;

                // Force increase all text elements font size
                const allText = document.querySelectorAll('svg text');
                allText.forEach(text => {{
                    const currentSize = window.getComputedStyle(text).fontSize;
                    const newSize = parseFloat(currentSize) * 1.5;
                    text.style.fontSize = newSize + 'px';
                    text.style.fontWeight = '500';
                }});
            }});
    </script>
</body>
</html>"""

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={'width': 1920, 'height': 1080}, device_scale_factor=2)
            page.set_content(html_content)
            page.wait_for_selector("#diagram svg", timeout=10000)

            # Take a screenshot of the diagram element with higher quality
            diagram = page.query_selector("#diagram")
            diagram.screenshot(path=output_file, type='png', scale='device')

            browser.close()
            return True
    except Exception as e:
        print(f"    Error: {e}")
        return False

# List of fruits
fruits = [
    ("Mango", "mango"),
    ("Avocado", "avocado"),
    ("Blueberry", "blueberry"),
    ("Strawberry", "strawberry"),
    ("Grape", "grape"),
    ("Passion Fruit", "passion_fruit"),
    ("Pineapple", "pineapple"),
    ("Banana", "banana"),
    ("Papaya", "papaya"),
    ("Lucuma", "lucuma"),
    ("Golden Berry", "golden_berry"),
    ("Pomegranate", "pomegranate"),
    ("Soursop", "soursop"),
]

# Read all export data
print("Reading export data...")
df = read_export_data("exports.db", product_filter=None, region_filter=None)

# Filter to Germany only
print(f"Total records: {len(df)}")
df_germany = df[df['Country'] == 'Germany'].copy()
print(f"Records to Germany: {len(df_germany)}")

if len(df_germany) == 0:
    print("No exports to Germany found!")
    sys.exit(1)

print("\n" + "="*60)
print("Generating individual Germany Sankey diagrams per fruit")
print("="*60)

# Process each fruit
for fruit_name, fruit_key in fruits:
    print(f"\n🍎 Processing {fruit_name}...")

    # Filter to this specific fruit
    df_fruit = df_germany[df_germany['Fruit'] == fruit_name].copy()

    if len(df_fruit) == 0:
        print(f"  ⚠ No exports to Germany for {fruit_name}, skipping")
        continue

    print(f"  Records: {len(df_fruit)}")
    print(f"  Total MT: {df_fruit['MT'].sum():.0f}")

    # Create flows: Exporter → Importer → Country
    all_flows = []

    # 1. Exporter → Importer flows
    exporter_importer = df_fruit.groupby(['Exporter_Name', 'Importer_Name'])['MT'].sum().reset_index()
    flows1 = list(exporter_importer.itertuples(index=False, name=None))
    all_flows.extend(flows1)

    # 2. Importer → Germany (destination)
    importer_country = df_fruit.groupby(['Importer_Name', 'Country'])['MT'].sum().reset_index()
    flows2 = list(importer_country.itertuples(index=False, name=None))
    all_flows.extend(flows2)

    # Sort by value
    all_flows = sorted(all_flows, key=lambda x: x[2], reverse=True)

    print(f"  Flows: {len(all_flows)}")
    print(f"  Exporters: {df_fruit['Exporter_Name'].nunique()}")
    print(f"  Importers: {df_fruit['Importer_Name'].nunique()}")

    # Generate mermaid
    output = format_mermaid_sankey(
        all_flows,
        title=f"{fruit_name} to Germany: Exporter → Importer → Country (MT)",
        decimal_places=0
    )

    # Update to show values
    output = output.replace('showValues: false', 'showValues: true')

    # Write mermaid file
    mmd_file = f"sankey-germany-{fruit_key}.mmd"
    Path(mmd_file).write_text(output)
    print(f"  ✓ Mermaid: {mmd_file}")

    # Generate PNG
    png_file = f"sankey-germany-{fruit_key}.png"
    print(f"  Generating PNG: {png_file}...")
    if mermaid_to_png_playwright(output, png_file, f"{fruit_name} to Germany"):
        size_kb = Path(png_file).stat().st_size / 1024
        print(f"  ✓ PNG: {png_file} ({size_kb:.0f} KB)")
    else:
        print(f"  ✗ PNG generation failed for {png_file}")

print("\n" + "="*60)
print("✓ All Germany Sankey diagrams generated!")
print("="*60)
