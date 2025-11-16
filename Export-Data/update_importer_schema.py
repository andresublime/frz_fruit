"""
Update database schema to add canonical_importer column.

This script:
1. Adds a canonical_importer column to the exports table
2. Populates it using the importer mapping
3. Creates an index for better query performance
"""

import sqlite3
from core.importer_mapping import get_canonical_importer


def update_schema():
    """Add canonical_importer column and populate it."""
    conn = sqlite3.connect('exports.db')
    cursor = conn.cursor()

    # Check if column already exists
    cursor.execute("PRAGMA table_info(exports)")
    columns = [row[1] for row in cursor.fetchall()]

    if 'canonical_importer' not in columns:
        print("Adding canonical_importer column...")
        cursor.execute("""
            ALTER TABLE exports
            ADD COLUMN canonical_importer TEXT
        """)
        print("✓ Column added")
    else:
        print("canonical_importer column already exists")

    # Populate canonical_importer for all rows
    print("\nPopulating canonical_importer values...")
    cursor.execute("SELECT DISTINCT importer FROM exports")
    importers = [row[0] for row in cursor.fetchall()]

    update_count = 0
    for importer in importers:
        canonical = get_canonical_importer(importer)
        cursor.execute("""
            UPDATE exports
            SET canonical_importer = ?
            WHERE importer = ? OR importer IS NULL AND ? IS NULL
        """, (canonical, importer, importer))
        update_count += cursor.rowcount

    print(f"✓ Updated {update_count} rows")

    # Create index for better performance
    print("\nCreating index on canonical_importer...")
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_canonical_importer
        ON exports(canonical_importer)
    """)
    print("✓ Index created")

    # Show statistics
    print("\n" + "=" * 80)
    print("Statistics:")
    print("=" * 80)

    cursor.execute("""
        SELECT
            COUNT(DISTINCT importer) as original_count,
            COUNT(DISTINCT canonical_importer) as canonical_count
        FROM exports
    """)
    original, canonical = cursor.fetchone()

    print(f"Original importer names: {original:,}")
    print(f"Canonical importer names: {canonical:,}")
    print(f"Reduction: {original - canonical:,} ({(1 - canonical/original)*100:.1f}%)")

    # Show top importers by canonical name
    print("\n" + "=" * 80)
    print("Top 20 importers by shipment count (canonical names):")
    print("=" * 80)

    cursor.execute("""
        SELECT
            canonical_importer,
            COUNT(*) as shipment_count,
            COUNT(DISTINCT importer) as name_variations
        FROM exports
        GROUP BY canonical_importer
        ORDER BY shipment_count DESC
        LIMIT 20
    """)

    for i, (name, count, variations) in enumerate(cursor.fetchall(), 1):
        print(f"{i:2d}. {count:4d} shipments  {name:40s} ({variations} variations)")

    conn.commit()
    conn.close()

    print("\n✓ Database schema updated successfully!")


if __name__ == '__main__':
    update_schema()
