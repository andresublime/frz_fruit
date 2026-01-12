#!/usr/bin/env python3
"""Generate exhaustive Sankey diagram for all fruits to Germany"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from sankey import read_export_data, format_mermaid_sankey
import pandas as pd

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

# Show breakdown by fruit
print("\nBreakdown by fruit:")
fruit_totals = df_germany.groupby('Fruit')['MT'].sum().sort_values(ascending=False)
for fruit, mt in fruit_totals.items():
    print(f"  {fruit}: {mt:.0f} MT")

# Create flows: Exporter → Fruit → Importer → Country
# No aggregation - show everything!
all_flows = []

# 1. Exporter → Fruit flows
exporter_fruit = df_germany.groupby(['Exporter_Name', 'Fruit'])['MT'].sum().reset_index()
flows1 = list(exporter_fruit.itertuples(index=False, name=None))
all_flows.extend(flows1)

# 2. Fruit → Importer flows
fruit_importer = df_germany.groupby(['Fruit', 'Importer_Name'])['MT'].sum().reset_index()
flows2 = list(fruit_importer.itertuples(index=False, name=None))
all_flows.extend(flows2)

# 3. Importer → Germany (destination)
importer_country = df_germany.groupby(['Importer_Name', 'Country'])['MT'].sum().reset_index()
flows3 = list(importer_country.itertuples(index=False, name=None))
all_flows.extend(flows3)

# Sort by value
all_flows = sorted(all_flows, key=lambda x: x[2], reverse=True)

print(f"\nTotal flows: {len(all_flows)}")
print(f"Unique exporters: {df_germany['Exporter_Name'].nunique()}")
print(f"Unique fruits: {df_germany['Fruit'].nunique()}")
print(f"Unique importers: {df_germany['Importer_Name'].nunique()}")

# Generate mermaid
output = format_mermaid_sankey(
    all_flows,
    title=f"All Fruits to Germany: Exporter → Fruit → Importer → Country (MT)",
    decimal_places=0
)

# Update to show values
output = output.replace('showValues: false', 'showValues: true')

# Write mermaid file
mmd_file = "sankey-germany-all-fruits.mmd"
Path(mmd_file).write_text(output)
print(f"\n✓ Mermaid file written to {mmd_file}")

# Generate PNG using Playwright
print("\nGenerating PNG using Playwright...")
try:
    from playwright.sync_api import sync_playwright

    # Create HTML with mermaid
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
</head>
<body style="margin: 0; padding: 20px; background: white;">
    <div id="diagram"></div>
    <script>
        mermaid.initialize({{
            startOnLoad: false,
            theme: 'base',
            themeVariables: {{
                fontSize: '20px',
                fontFamily: 'Arial, sans-serif'
            }},
            sankey: {{
                showValues: true,
                width: 2400,
                height: 1600
            }}
        }});

        mermaid.render('mermaid-svg', `{output}`)
            .then(result => {{
                document.getElementById('diagram').innerHTML = result.svg;

                // Set consistent font size for all text elements
                const allText = document.querySelectorAll('svg text');
                allText.forEach(text => {{
                    text.style.fontSize = '20px';
                    text.style.fontWeight = '500';
                }});
            }});
    </script>
</body>
</html>"""

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': 2600, 'height': 1800})
        page.set_content(html_content)
        page.wait_for_selector("#diagram svg", timeout=30000)

        # Wait a bit more for rendering to complete
        page.wait_for_timeout(2000)

        # Take screenshot
        png_file = "sankey-germany-all-fruits.png"
        page.screenshot(path=png_file, full_page=True)

        browser.close()

        # Get file size
        size_mb = Path(png_file).stat().st_size / (1024 * 1024)
        print(f"✓ PNG written to {png_file} ({size_mb:.2f} MB)")

except Exception as e:
    print(f"✗ Failed to generate PNG: {e}")
    print("  Mermaid file is available, you can convert it manually")
