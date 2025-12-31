#!/usr/bin/env python3
"""Fix canonical names in database to be uppercase"""
import sqlite3

conn = sqlite3.connect("exports.db")
cursor = conn.cursor()

print("Fixing canonical names to UPPERCASE in database...")

# Update canonical_exporter to uppercase
cursor.execute("""
UPDATE exports
SET canonical_exporter = UPPER(canonical_exporter)
WHERE canonical_exporter IS NOT NULL
""")
exporter_rows = cursor.rowcount
print(f"  Updated {exporter_rows} canonical_exporter rows")

# Update canonical_importer to uppercase
cursor.execute("""
UPDATE exports
SET canonical_importer = UPPER(canonical_importer)
WHERE canonical_importer IS NOT NULL
""")
importer_rows = cursor.rowcount
print(f"  Updated {importer_rows} canonical_importer rows")

# Commit changes
conn.commit()

# Verify - check for any remaining non-uppercase
cursor.execute("""
SELECT COUNT(*)
FROM exports
WHERE (canonical_exporter IS NOT NULL AND canonical_exporter != UPPER(canonical_exporter))
   OR (canonical_importer IS NOT NULL AND canonical_importer != UPPER(canonical_importer))
""")
remaining = cursor.fetchone()[0]

conn.close()

if remaining == 0:
    print(f"\n✓ All canonical names are now UPPERCASE")
else:
    print(f"\n⚠ Warning: {remaining} rows still have non-uppercase canonical names")

print("\nSample canonical names after fix:")
conn = sqlite3.connect("exports.db")
cursor = conn.cursor()
cursor.execute("""
SELECT DISTINCT canonical_importer
FROM exports
WHERE canonical_importer LIKE '%HG%'
""")
print("  HG-related:")
for row in cursor.fetchall():
    print(f"    {row[0]}")

conn.close()
