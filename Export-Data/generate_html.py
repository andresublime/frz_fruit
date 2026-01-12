#!/usr/bin/env python3
"""Generate HTML with all sankey diagrams"""
from pathlib import Path
import subprocess
import sys

def mermaid_to_png_playwright(mermaid_code, output_file):
    """Convert mermaid code to PNG using Playwright"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  ⚠ Playwright not installed. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "playwright"], check=True)
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
        from playwright.sync_api import sync_playwright

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
                    const newSize = parseFloat(currentSize) * 2.5;
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

fruits = [
    ("Mango", "mango", "🥭", 1176),
    ("Avocado", "avocado", "🥑", 2120),
    ("Blueberry", "blueberry", "🫐", 627),
    ("Strawberry", "strawberry", "🍓", 1),
    ("Grape", "grape", "🍇", 9),
    ("Passion Fruit", "passion_fruit", "💜", 47),
    ("Pineapple", "pineapple", "🍍", 17),
    ("Banana", "banana", "🍌", 10),
    ("Papaya", "papaya", "🟠", 5),
    ("Lucuma", "lucuma", "🟡", 36),
    ("Golden Berry", "golden_berry", "🟨", 2),
    ("Pomegranate", "pomegranate", "🔴", 1),
    ("Soursop", "soursop", "🟢", 6),
]

html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Export Flow Analysis - All Fruits</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #f5f5f5;
            padding: 2rem;
        }

        .header {
            text-align: center;
            margin-bottom: 3rem;
            background: white;
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .header h1 {
            font-size: 2.5rem;
            color: #333;
            margin-bottom: 0.5rem;
        }

        .header p {
            color: #666;
            font-size: 1.1rem;
        }

        .fruit-section {
            background: white;
            margin-bottom: 3rem;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow: hidden;
            page-break-inside: avoid;
        }

        .fruit-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1.5rem 2rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .fruit-title {
            display: flex;
            align-items: center;
            gap: 1rem;
            font-size: 2rem;
            font-weight: 700;
        }

        .fruit-icon {
            font-size: 2.5rem;
        }

        .fruit-stats {
            display: flex;
            gap: 2rem;
            font-size: 0.9rem;
            opacity: 0.95;
        }

        .stat-item {
            text-align: center;
        }

        .stat-value {
            display: block;
            font-size: 1.4rem;
            font-weight: 700;
        }

        .stat-label {
            display: block;
            font-size: 0.8rem;
            opacity: 0.9;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .diagram-container {
            padding: 2rem;
            min-height: 500px;
            display: flex;
            justify-content: center;
            align-items: center;
        }

        .diagram-container img {
            max-width: 100%;
            height: auto;
            border-radius: 8px;
        }

        .footer {
            text-align: center;
            color: #666;
            font-size: 0.9rem;
            margin-top: 2rem;
        }

        @media print {
            body {
                background: white;
            }
            .fruit-section {
                page-break-inside: avoid;
                margin-bottom: 2rem;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🍎 Export Flow Analysis - All Fruits</h1>
        <p>Exporter → Importer → Country (Europe Region) • Canonical Company Names via vt-normalize</p>
    </div>

"""

# Add each fruit section
for name, file_name, icon, records in fruits:
    mmd_file = Path(f"sankey-{file_name}.mmd")
    if not mmd_file.exists():
        continue

    # Read the .mmd file
    content = mmd_file.read_text()

    # Generate PNG using Playwright
    png_file = f"sankey-{file_name}.png"
    print(f"Generating {png_file} using Playwright...")
    try:
        if mermaid_to_png_playwright(content, png_file):
            print(f"  ✓ Generated {png_file}")
            png_success = True
        else:
            print(f"  ✗ Failed, using mermaid code fallback")
            png_success = False
    except Exception as e:
        print(f"  ✗ Error: {e}, using mermaid code fallback")
        png_success = False

    # Count flows (rough estimate)
    flow_count = content.count('\n') - 7  # Subtract header lines

    # Use PNG if available, otherwise use mermaid code
    if png_success:
        diagram_html = f'<img src="{png_file}" alt="{name} Export Flow Sankey Diagram">'
    else:
        diagram_html = f'<pre class="mermaid">\n{content}\n            </pre>'

    html += f"""
    <div class="fruit-section">
        <div class="fruit-header">
            <div class="fruit-title">
                <span class="fruit-icon">{icon}</span>
                <span>{name}</span>
            </div>
            <div class="fruit-stats">
                <div class="stat-item">
                    <span class="stat-value">{records}</span>
                    <span class="stat-label">Records</span>
                </div>
                <div class="stat-item">
                    <span class="stat-value">{flow_count}</span>
                    <span class="stat-label">Flows</span>
                </div>
                <div class="stat-item">
                    <span class="stat-value">MT</span>
                    <span class="stat-label">Metric</span>
                </div>
            </div>
        </div>
        <div class="diagram-container">
            {diagram_html}
        </div>
    </div>
"""

html += """
    <div class="footer">
        Generated with canonical company names using vt-normalize clustering • Data from exports.db
    </div>

    <script>
        window.addEventListener('load', () => {
            console.log('All sankey diagrams loaded as PNG images');
        });
    </script>
</body>
</html>
"""

# Write HTML file
Path("sankey-all-fruits.html").write_text(html)
print("✓ HTML file generated: sankey-all-fruits.html")
print("  Open this file in your browser to view and screenshot all diagrams")
