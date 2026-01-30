import sqlite3
import pandas as pd

# Connect to database
conn = sqlite3.connect('/home/andresublime/apps/frz_fruit/Export-Data/data/exports.db')

# Query for ginger exporters from Peru
query = """
SELECT
    Exporter,
    COUNT(*) as shipment_count,
    ROUND(SUM(net_weight_mt), 2) as total_mt,
    ROUND(SUM(usd_fob_total), 2) as total_fob_usd,
    ROUND(AVG(usd_per_mt_fob), 2) as avg_usd_per_mt,
    MIN(Date) as first_shipment,
    MAX(Date) as last_shipment,
    COUNT(DISTINCT "Destination Country") as num_destinations
FROM exports
WHERE fruit_name = 'ginger'
  AND source_country = 'peru'
GROUP BY Exporter
ORDER BY total_mt DESC
"""

df = pd.read_sql_query(query, conn)
conn.close()

# Display the results
print(f"\n{'=' * 120}")
print(f"GINGER EXPORTERS FROM PERU")
print(f"{'=' * 120}")
print(f"\nTotal exporters found: {len(df)}")
print(f"Total volume: {df['total_mt'].sum():.2f} MT")
print(f"Total FOB value: ${df['total_fob_usd'].sum():,.2f}")
print(f"\n")

# Format the dataframe for better display
df_display = df.copy()
df_display['total_fob_usd'] = df_display['total_fob_usd'].apply(lambda x: f"${x:,.2f}")
df_display['avg_usd_per_mt'] = df_display['avg_usd_per_mt'].apply(lambda x: f"${x:,.2f}")

# Set pandas display options for better table formatting
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 120)
pd.set_option('display.max_colwidth', 40)

print(df_display.to_string(index=False))
print(f"\n{'=' * 120}\n")

# Export to CSV
output_file = 'ginger_exporters_peru.csv'
df.to_csv(output_file, index=False)
print(f"Data exported to: {output_file}")
