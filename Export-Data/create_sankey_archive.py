#!/usr/bin/env python3
"""Create timestamped archive of sankey files"""
from datetime import datetime
from pathlib import Path
import zipfile

# Get timestamp
timestamp = datetime.now().strftime("%y-%m-%d_%H-%M-%S")
zip_name = f"{timestamp}_sankey.zip"

# Files to include
patterns = [
    "sankey-*.mmd",
    "sankey-*.html",
    "sankey-*.svg",
    "sankey.py",
    "generate_html.py",
]

files_to_zip = []
for pattern in patterns:
    files_to_zip.extend(Path(".").glob(pattern))

# Exclude sankey-data.mmd (old file)
files_to_zip = [f for f in files_to_zip if f.name != "sankey-data.mmd"]

# Create zip file
with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for file in sorted(files_to_zip):
        zipf.write(file, file.name)
        print(f"  Added: {file.name}")

# Get file size
size_mb = Path(zip_name).stat().st_size / (1024 * 1024)
print(f"\n✓ Created: {zip_name} ({size_mb:.2f} MB)")
print(f"  Total files: {len(files_to_zip)}")
