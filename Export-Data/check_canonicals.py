#!/usr/bin/env python3
"""Check canonical names in database"""
import sqlite3
import pandas as pd

conn = sqlite3.connect("exports.db")

# Check canonical importers for Germany
query = """
SELECT DISTINCT canonical_importer, Importer
FROM exports
WHERE destination_country_en = 'Germany'
  AND canonical_importer IS NOT NULL
ORDER BY canonical_importer
LIMIT 30
"""

df = pd.read_sql_query(query, conn)
print("Canonical Importer Names (Germany):")
print(df.to_string(index=False))

print("\n" + "="*60 + "\n")

# Check canonical exporters for Germany
query2 = """
SELECT DISTINCT canonical_exporter, Exporter
FROM exports
WHERE destination_country_en = 'Germany'
  AND canonical_exporter IS NOT NULL
ORDER BY canonical_exporter
LIMIT 30
"""

df2 = pd.read_sql_query(query2, conn)
print("Canonical Exporter Names (Germany):")
print(df2.to_string(index=False))

conn.close()
