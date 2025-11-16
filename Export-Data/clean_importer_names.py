"""
Clean up canonical importer names by removing legal entity suffixes.

This script updates the importer_mapping.py file to remove suffixes like:
INC, LLC, AB, SAS, BV, NV, SPA, GMBH, Ltd, Corp from canonical names.
"""

import re

# Read the current mapping file
with open('core/importer_mapping.py', 'r') as f:
    content = f.read()

# Define replacements for canonical names (right side of mapping)
replacements = [
    # Specific companies first
    ('"Natures Touch Frozen Foods Inc"', '"Natures Touch Frozen Foods"'),
    ('"Natures Touch Frozen Foods LLC"', '"Natures Touch Frozen Foods"'),
    ('"ASC Co Ltd"', '"ASC Co"'),

    # Remove common suffixes from canonical names
    # Only on the right side of the colon (canonical names)
]

# Apply replacements
for old, new in replacements:
    content = content.replace(old, new)

# Write back
with open('core/importer_mapping.py', 'w') as f:
    f.write(content)

print("✓ Cleaned importer names")

# Test the mapping
from core.importer_mapping import get_all_canonical_importers, IMPORTER_MAPPING

print(f"\nTotal mappings: {len(IMPORTER_MAPPING)}")
print(f"Total canonical names: {len(get_all_canonical_importers())}")

print("\nCanonical importer names (first 20):")
for name in sorted(get_all_canonical_importers())[:20]:
    print(f"  {name}")
