#!/usr/bin/env python3
"""
Clean up European importer names by creating canonical mappings.
"""

import sqlite3
import re
from collections import defaultdict


def normalize_name(name):
    """Normalize a company name for comparison."""
    if not name:
        return ""

    # Convert to uppercase and strip
    original = name.upper().strip()
    name = original

    # Remove all punctuation and special characters first
    name = re.sub(r'[\'\"\.,:;()\-/]+', '', name)

    # Normalize spacing
    name = re.sub(r'\s+', ' ', name)

    # If name is too long (>30 chars), it likely contains an address
    # Try to truncate after legal entity type
    if len(name) > 30:
        # Try to find legal entity type and cut there
        match = re.search(r'\b(NV|BV|SA|SL|GMBH|LTD|LLC|INC|CORP|AB|SAS|SP Z OO|SP ZOO)\b', name)
        if match:
            # Keep up to and including the legal entity type
            name = name[:match.end()].strip()

    # Remove legal entity types FIRST
    legal_types = [
        r'\s+N V\s*$',
        r'\s+B V\s*$',
        r'\s+S A\s*$',
        r'\s+S L\s*$',
        r'\s+GMBH\s*$',
        r'\s+LTD\s*$',
        r'\s+LIMITED\s*$',
        r'\s+LLC\s*$',
        r'\s+INC\s*$',
        r'\s+CORP\s*$',
        r'\s+AB\s*$',
        r'\s+SAS\s*$',
        r'\s+SP Z OO\s*$',
        r'\s+SP ZOO\s*$',
        r'\s+NV\s*$',
        r'\s+BV\s*$',
    ]

    for legal_type in legal_types:
        name = re.sub(legal_type, '', name)

    # Normalize spacing
    name = re.sub(r'\s+', ' ', name).strip()

    # NOW remove country/region suffixes from company names
    # These are subsidiaries that should consolidate to the parent company
    country_suffixes = [
        r'\s+UK\s*$',
        r'\s+POLAND\s*$',
        r'\s+BELGIUM\s*$',
        r'\s+BELIUM\s*$',  # Common typo
        r'\s+FRANCE\s*$',
        r'\s+GERMANY\s*$',
        r'\s+SPAIN\s*$',
        r'\s+NETHERLANDS\s*$',
        r'\s+EUROPE\s*$',
        r'\s+IBERICA\s*$',  # Spanish for Iberian/Spain
        r'\s+ITALIA\s*$',
        r'\s+SVERIGE\s*$',  # Swedish for Sweden
        r'\s+DANMARK\s*$',  # Danish for Denmark
    ]

    for suffix in country_suffixes:
        name = re.sub(suffix, '', name)

    # Specific fixes for known variations
    name = name.replace('CROP S FRUITS', 'CROPS FRUITS')
    name = name.replace('D ARTA', 'DARTA')

    # Normalize spacing one more time
    name = re.sub(r'\s+', ' ', name)

    return name.strip()


def create_canonical_name(base_name):
    """Create a clean canonical name from the base name - kept in uppercase."""
    # Keep uppercase
    name = base_name.upper().strip()

    # Remove trailing/leading spaces
    name = ' '.join(name.split())

    return name.strip()


def get_european_importers():
    """Get all European importer name variations."""
    conn = sqlite3.connect('exports.db')
    cursor = conn.cursor()

    query = """
    SELECT
        Importer,
        canonical_importer,
        COUNT(*) as shipment_count
    FROM exports
    WHERE analysis_valid = 1
        AND region = 'Europe'
        AND Importer IS NOT NULL
        AND Importer != ''
    GROUP BY Importer
    ORDER BY shipment_count DESC
    """

    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()

    return results


def group_similar_names(importers):
    """Group similar importer names together."""
    groups = defaultdict(list)

    for original, canonical, count in importers:
        normalized = normalize_name(original)
        groups[normalized].append((original, canonical, count))

    return groups


def generate_mappings():
    """Generate canonical mappings for European importers."""
    print("Analyzing European importer names...")

    importers = get_european_importers()
    groups = group_similar_names(importers)

    mappings = {}

    for normalized, variations in groups.items():
        if not normalized:
            continue

        # Sort by shipment count to find the most common variation
        variations.sort(key=lambda x: x[2], reverse=True)

        # ALWAYS create a fresh canonical name from the normalized name
        # This ensures all names are properly cleaned and consolidated
        canonical = create_canonical_name(normalized)

        # Map all variations to the canonical name
        for original, _, _ in variations:
            # Always update the mapping, even if it already has a canonical name
            mappings[original] = canonical

    return mappings, groups


def update_database(mappings):
    """Update the canonical_importer field in the database."""
    conn = sqlite3.connect('exports.db')
    cursor = conn.cursor()

    updated = 0
    for original, canonical in mappings.items():
        cursor.execute("""
            UPDATE exports
            SET canonical_importer = ?
            WHERE Importer = ?
                AND region = 'Europe'
                AND analysis_valid = 1
        """, (canonical, original))
        updated += cursor.rowcount

    conn.commit()
    conn.close()

    return updated


def main():
    mappings, groups = generate_mappings()

    print(f"\nFound {len(groups)} unique company groups")
    print(f"Generated {len(mappings)} mappings")

    # Show some examples
    print("\n=== Examples of name consolidation ===")
    examples = 0
    for normalized, variations in sorted(groups.items(), key=lambda x: sum(v[2] for v in x[1]), reverse=True):
        if len(variations) > 1 and examples < 10:
            total_shipments = sum(v[2] for v in variations)
            canonical = mappings.get(variations[0][0], variations[0][1])
            print(f"\n{canonical} ({total_shipments} total shipments):")
            for orig, canon, count in variations[:5]:
                print(f"  - {orig} ({count})")
            examples += 1

    # Update the database
    print(f"\n\nUpdating {len(mappings)} importer name mappings in the database...")
    updated = update_database(mappings)
    print(f"\n✓ Updated {updated} records with canonical importer names")
    print("\nRun 'uv run sankey.py' to regenerate the Sankey diagram with cleaned names.")


if __name__ == '__main__':
    main()
