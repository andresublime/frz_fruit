import sqlite3
import pandas as pd
from datetime import datetime

# Connect to database
conn = sqlite3.connect('/home/andresublime/apps/frz_fruit/Export-Data/data/exports.db')

# Query the data
query = """
SELECT
    source_country,
    fruit_name,
    Date,
    net_weight_mt,
    is_aseptic,
    is_iqf
FROM exports
WHERE fruit_name IS NOT NULL
  AND net_weight_mt IS NOT NULL
"""

df = pd.read_sql_query(query, conn)
conn.close()

# Determine format type
def get_format(row):
    if row['is_aseptic'] == 1:
        return 'aseptic'
    elif row['is_iqf'] == 1:
        return 'frozen'
    else:
        return 'frozen'  # Default to frozen if neither flag is set

df['format'] = df.apply(get_format, axis=1)

# Convert Date to datetime and extract month name
df['Date'] = pd.to_datetime(df['Date'])
df['Month'] = df['Date'].dt.strftime('%B')  # Full month name

# Group by source_country, format, fruit_name, and Month, summing the MT
monthly_data = df.groupby(['source_country', 'format', 'fruit_name', 'Month'])['net_weight_mt'].sum().reset_index()

# Pivot to get months as columns
pivot_df = monthly_data.pivot_table(
    index=['source_country', 'fruit_name', 'format'],
    columns='Month',
    values='net_weight_mt',
    fill_value=0
)

# Reorder columns by calendar month order
month_order = ['January', 'February', 'March', 'April', 'May', 'June',
               'July', 'August', 'September', 'October', 'November', 'December']

# Only keep months that exist in the data
existing_months = [month for month in month_order if month in pivot_df.columns]
pivot_df = pivot_df[existing_months]

# Filter out rows where total across all months is less than 48 MT
pivot_df['Total'] = pivot_df.sum(axis=1)
pivot_df = pivot_df[pivot_df['Total'] >= 48]
# pivot_df = pivot_df.drop('Total', axis=1)

# Round all values to 0 decimal places
pivot_df = pivot_df.round(0).astype(int)

# Save to CSV
pivot_df.to_csv('monthly_exports.csv')

print(f"Created monthly_exports.csv with {len(pivot_df)} rows")
print(f"\nMonths included: {', '.join(existing_months)}")
print(f"\nPreview:")
print(pivot_df)

