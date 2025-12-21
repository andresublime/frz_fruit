"""
Export Price Quote Generator
Creates an Excel spreadsheet with pricing data for specific frozen fruit products
"""

import pandas as pd
from pathlib import Path
from core.database import get_connection
from datetime import datetime

def get_pricing_by_fruit_format(fruit: str, format_type: str = None):
    """Get pricing data for a specific fruit and format"""
    db_path = Path(__file__).parent / 'exports.db'

    with get_connection(db_path) as conn:
        if format_type:
            query = """
                SELECT
                    fruit_name,
                    format_type,
                    MIN(usd_per_mt_fob) as low_usd_mt,
                    AVG(usd_per_mt_fob) as avg_usd_mt,
                    MAX(usd_per_mt_fob) as high_usd_mt,
                    SUM(net_weight_mt) as total_mt,
                    COUNT(*) as records
                FROM v_clean_exports
                WHERE fruit_name = ? AND format_type = ?
                GROUP BY fruit_name, format_type
            """
            df = pd.read_sql_query(query, conn, params=(fruit, format_type))
        else:
            query = """
                SELECT
                    fruit_name,
                    format_type,
                    MIN(usd_per_mt_fob) as low_usd_mt,
                    AVG(usd_per_mt_fob) as avg_usd_mt,
                    MAX(usd_per_mt_fob) as high_usd_mt,
                    SUM(net_weight_mt) as total_mt,
                    COUNT(*) as records
                FROM v_clean_exports
                WHERE fruit_name = ?
                GROUP BY fruit_name, format_type
            """
            df = pd.read_sql_query(query, conn, params=(fruit,))

    return df

def calculate_quartile_pricing(fruit: str, format_type: str = None):
    """Calculate quartile-based pricing (Q1, Median, Q3)"""
    db_path = Path(__file__).parent / 'exports.db'

    with get_connection(db_path) as conn:
        if format_type:
            query = """
                SELECT usd_per_mt_fob, net_weight_mt
                FROM v_clean_exports
                WHERE fruit_name = ? AND format_type = ?
                ORDER BY usd_per_mt_fob
            """
            df = pd.read_sql_query(query, conn, params=(fruit, format_type))
        else:
            query = """
                SELECT usd_per_mt_fob, net_weight_mt
                FROM v_clean_exports
                WHERE fruit_name = ?
                ORDER BY usd_per_mt_fob
            """
            df = pd.read_sql_query(query, conn, params=(fruit,))

    if len(df) == 0:
        return None

    q1 = df['usd_per_mt_fob'].quantile(0.25)
    median = df['usd_per_mt_fob'].quantile(0.50)
    q3 = df['usd_per_mt_fob'].quantile(0.75)
    total_mt = df['net_weight_mt'].sum()
    records = len(df)

    return {
        'q1': round(q1, 0),
        'median': round(median, 0),
        'q3': round(q3, 0),
        'total_mt': round(total_mt, 0),
        'records': records
    }

def create_price_quote_spreadsheet():
    """Create Excel spreadsheet with price quotes for requested products"""

    # Define requested products
    products = [
        {'name': 'Mango IQF Chunks (10mm)', 'fruit': 'mango', 'format': 'chunks'},
        {'name': 'Frozen Mandarine Puree (0.5 mm)', 'fruit': 'orange', 'format': 'puree'},
        {'name': 'Blueberries Class B - IQF Whole', 'fruit': 'blueberry', 'format': 'whole'},
        {'name': 'Passion Fruit Pulp w/ Seeds', 'fruit': 'passion_fruit', 'format': 'pulp'},
        {'name': 'Blueberries IQF Whole', 'fruit': 'blueberry', 'format': 'iqf'},
        {'name': 'Avocado IQF Cubes', 'fruit': 'avocado', 'format': 'cubes'},
    ]

    # Collect pricing data
    pricing_data = []

    for product in products:
        print(f"Getting pricing for {product['name']}...")

        pricing = calculate_quartile_pricing(product['fruit'], product['format'])

        if pricing:
            pricing_data.append({
                'Product Name': product['name'],
                'Fruit': product['fruit'].replace('_', ' ').title(),
                'Format': product['format'].title(),
                'Low (Q1) USD/MT': f"${pricing['q1']:,.0f}",
                'Median USD/MT': f"${pricing['median']:,.0f}",
                'High (Q3) USD/MT': f"${pricing['q3']:,.0f}",
                'YTD Volume (MT)': f"{pricing['total_mt']:,.0f}",
                'Data Records': pricing['records'],
                'Data Availability': 'Available'
            })
        else:
            pricing_data.append({
                'Product Name': product['name'],
                'Fruit': product['fruit'].replace('_', ' ').title(),
                'Format': product['format'].title(),
                'Low (Q1) USD/MT': 'N/A',
                'Median USD/MT': 'N/A',
                'High (Q3) USD/MT': 'N/A',
                'YTD Volume (MT)': 'N/A',
                'Data Records': 0,
                'Data Availability': 'Not Available'
            })

    # Create DataFrame
    df = pd.DataFrame(pricing_data)

    # Create Excel file with formatting
    output_path = Path(__file__).parent / 'output' / 'frozen_fruit_price_quote.xlsx'
    output_path.parent.mkdir(exist_ok=True)

    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Price Quote', index=False)

        # Get worksheet
        worksheet = writer.sheets['Price Quote']

        # Set column widths
        worksheet.column_dimensions['A'].width = 35
        worksheet.column_dimensions['B'].width = 15
        worksheet.column_dimensions['C'].width = 15
        worksheet.column_dimensions['D'].width = 18
        worksheet.column_dimensions['E'].width = 18
        worksheet.column_dimensions['F'].width = 18
        worksheet.column_dimensions['G'].width = 18
        worksheet.column_dimensions['H'].width = 15
        worksheet.column_dimensions['I'].width = 18

        # Add metadata sheet
        metadata = pd.DataFrame({
            'Field': ['Report Date', 'Data Period', 'Price Basis', 'Price Type', 'Data Source'],
            'Value': [
                datetime.now().strftime('%Y-%m-%d'),
                'YTD Oct 2024 - Oct 2025',
                'FOB (Free On Board)',
                'Quartile Pricing (Q1/Median/Q3)',
                'Peru Frozen Fruit Export Database'
            ]
        })
        metadata.to_excel(writer, sheet_name='Metadata', index=False)

        # Notes sheet
        notes = pd.DataFrame({
            'Notes': [
                'PRICING METHODOLOGY',
                '- Quartile pricing (Q1/Median/Q3) eliminates outliers and provides realistic market ranges',
                '- All prices are FOB (Free On Board) basis in USD per Metric Ton',
                '- Data filtered to exclude: air freight, samples, small shipments, and price outliers',
                '',
                'DATA AVAILABILITY',
                '- Products marked "Not Available" were not found in the Peru export database',
                '- Limited data (<10 records) may not be statistically significant',
                '',
                'PRODUCT NOTES',
                '- Mandarine: Peru primarily exports "orange" products, not specifically mandarine',
                '- Ginger: Not found in Peru frozen fruit export database',
                '- Blueberry formats: "IQF" and "Whole" may have different processing specifications',
            ]
        })
        notes.to_excel(writer, sheet_name='Notes', index=False, header=False)

    print(f"\n✓ Price quote spreadsheet created: {output_path}")
    return output_path

if __name__ == '__main__':
    create_price_quote_spreadsheet()
