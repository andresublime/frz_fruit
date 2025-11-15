"""
Database Schema Migration Script

Adds new columns to support coherence features:
1. canonical_exporter - Normalized exporter names (fixes VIRU/Mebol variations)
2. analysis_valid - Boolean flag for data quality filtering

Usage:
    python update_database_schema.py
"""

import sqlite3
import pandas as pd
from pathlib import Path
from core.database import (
    get_connection,
    add_column_if_not_exists,
    create_index_if_not_exists,
    DEFAULT_DB_PATH
)
from core.exporter_mapping import get_canonical_name
from core.filters import is_valid_for_analysis, calculate_iqr_bounds


def add_schema_columns(db_path: Path = DEFAULT_DB_PATH):
    """Add new columns to exports table."""
    print("Adding new columns to exports table...")
    print("=" * 60)

    # Add canonical_exporter column
    added = add_column_if_not_exists(
        table='exports',
        column='canonical_exporter',
        column_type='TEXT',
        db_path=db_path
    )
    if added:
        print("✓ Added column: canonical_exporter")
    else:
        print("  Column already exists: canonical_exporter")

    # Add analysis_valid column (0 = invalid, 1 = valid)
    added = add_column_if_not_exists(
        table='exports',
        column='analysis_valid',
        column_type='INTEGER',
        default_value='0',
        db_path=db_path
    )
    if added:
        print("✓ Added column: analysis_valid")
    else:
        print("  Column already exists: analysis_valid")


def populate_canonical_exporters(db_path: Path = DEFAULT_DB_PATH):
    """Populate canonical_exporter column using exporter mapping."""
    print("\nPopulating canonical_exporter column...")
    print("=" * 60)

    with get_connection(db_path) as conn:
        # Get all unique exporters
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT Exporter FROM exports WHERE Exporter IS NOT NULL")
        exporters = [row[0] for row in cursor.fetchall()]

        print(f"Found {len(exporters)} unique exporters")

        # Create mapping
        exporter_map = {}
        for exporter in exporters:
            canonical = get_canonical_name(exporter)
            exporter_map[exporter] = canonical

        # Show some examples
        print("\nSample mappings:")
        for i, (original, canonical) in enumerate(list(exporter_map.items())[:5]):
            print(f"  {original:50} → {canonical}")

        # Update database
        print("\nUpdating database...")
        for original, canonical in exporter_map.items():
            cursor.execute(
                "UPDATE exports SET canonical_exporter = ? WHERE Exporter = ?",
                (canonical, original)
            )

        conn.commit()

        # Verify
        cursor.execute("SELECT COUNT(*) FROM exports WHERE canonical_exporter IS NOT NULL")
        count = cursor.fetchone()[0]
        print(f"✓ Updated {count:,} records")

        # Show top exporters before/after
        print("\nTop exporters BEFORE normalization:")
        cursor.execute("""
            SELECT Exporter, COUNT(*) as count
            FROM exports
            GROUP BY Exporter
            ORDER BY count DESC
            LIMIT 5
        """)
        for row in cursor.fetchall():
            print(f"  {row[0]:50} {row[1]:6,}")

        print("\nTop exporters AFTER normalization:")
        cursor.execute("""
            SELECT canonical_exporter, COUNT(*) as count
            FROM exports
            GROUP BY canonical_exporter
            ORDER BY count DESC
            LIMIT 5
        """)
        for row in cursor.fetchall():
            print(f"  {row[0]:50} {row[1]:6,}")


def populate_analysis_valid(db_path: Path = DEFAULT_DB_PATH):
    """Populate analysis_valid column using data quality filters."""
    print("\nPopulating analysis_valid column...")
    print("=" * 60)

    # Load all data
    with get_connection(db_path) as conn:
        print("Loading all export records...")
        df = pd.read_sql_query("SELECT * FROM exports", conn)
        print(f"✓ Loaded {len(df):,} records")

        # Calculate IQR bounds per fruit (for outlier detection)
        print("\nCalculating IQR bounds per fruit...")
        iqr_bounds = calculate_iqr_bounds(
            df[df['usd_per_mt_fob'].notna()],
            price_col='usd_per_mt_fob',
            group_by='fruit_name'
        )
        print(f"✓ Calculated bounds for {len(iqr_bounds)} fruit types")

        # Apply validation to each record
        print("\nApplying data quality filters...")
        df['analysis_valid'] = df.apply(
            lambda row: 1 if is_valid_for_analysis(row, iqr_bounds) else 0,
            axis=1
        )

        # Show statistics
        total = len(df)
        valid = df['analysis_valid'].sum()
        invalid = total - valid
        print(f"\nResults:")
        print(f"  Valid records:   {valid:8,} ({valid/total*100:5.1f}%)")
        print(f"  Invalid records: {invalid:8,} ({invalid/total*100:5.1f}%)")

        # Update database
        print("\nUpdating database...")
        cursor = conn.cursor()

        # Use executemany for efficiency
        updates = [(int(row['analysis_valid']), row['DUA / DAM']) for _, row in df.iterrows()]
        cursor.executemany(
            "UPDATE exports SET analysis_valid = ? WHERE \"DUA / DAM\" = ?",
            updates
        )

        conn.commit()
        print(f"✓ Updated {len(updates):,} records")


def create_indexes(db_path: Path = DEFAULT_DB_PATH):
    """Create indexes for new columns."""
    print("\nCreating indexes...")
    print("=" * 60)

    created = create_index_if_not_exists(
        index_name='idx_canonical_exporter',
        table='exports',
        columns=['canonical_exporter'],
        db_path=db_path
    )
    if created:
        print("✓ Created index: idx_canonical_exporter")
    else:
        print("  Index already exists: idx_canonical_exporter")

    created = create_index_if_not_exists(
        index_name='idx_analysis_valid',
        table='exports',
        columns=['analysis_valid'],
        db_path=db_path
    )
    if created:
        print("✓ Created index: idx_analysis_valid")
    else:
        print("  Index already exists: idx_analysis_valid")

    # Composite index for common queries
    created = create_index_if_not_exists(
        index_name='idx_valid_date',
        table='exports',
        columns=['analysis_valid', 'Date'],
        db_path=db_path
    )
    if created:
        print("✓ Created index: idx_valid_date")
    else:
        print("  Index already exists: idx_valid_date")


def main():
    """Run all migration steps."""
    print("\n" + "=" * 60)
    print("DATABASE SCHEMA MIGRATION")
    print("=" * 60)

    # Step 1: Add columns
    add_schema_columns()

    # Step 2: Populate canonical exporters
    populate_canonical_exporters()

    # Step 3: Populate analysis_valid flags
    populate_analysis_valid()

    # Step 4: Create indexes
    create_indexes()

    print("\n" + "=" * 60)
    print("✓ MIGRATION COMPLETE!")
    print("=" * 60)

    # Final verification
    with get_connection() as conn:
        cursor = conn.cursor()

        # Check VIRU consolidation
        cursor.execute("""
            SELECT canonical_exporter, COUNT(*) as count
            FROM exports
            WHERE canonical_exporter = 'Viru'
            GROUP BY canonical_exporter
        """)
        result = cursor.fetchone()
        if result:
            print(f"\nVerification: Viru now has {result[1]:,} shipments (should be 2,640)")

        # Check valid records
        cursor.execute("SELECT COUNT(*) FROM exports WHERE analysis_valid = 1")
        valid_count = cursor.fetchone()[0]
        print(f"Valid records for analysis: {valid_count:,}")


if __name__ == '__main__':
    main()
