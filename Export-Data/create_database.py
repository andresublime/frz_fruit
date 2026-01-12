"""
Create SQLite database from enriched Peru frozen fruit export data.
"""
import pandas as pd
import sqlite3
from pathlib import Path
from translations import translate_country_to_english, COUNTRY_TRANSLATIONS

# Import vt-normalize canonical name functions
try:
    from core.exporter_mapping import get_canonical_name
    from core.importer_mapping import get_canonical_importer
    VT_NORMALIZE_AVAILABLE = True
except ImportError:
    VT_NORMALIZE_AVAILABLE = False

# Europe country list (English names)
EUROPE_COUNTRIES_EN = {
    'Germany', 'Austria', 'Belgium', 'Bulgaria', 'Cyprus', 'Croatia',
    'Denmark', 'Slovakia', 'Slovenia', 'Spain', 'Estonia', 'Finland',
    'France', 'Greece', 'Hungary', 'Ireland', 'Iceland', 'Italy', 'Latvia',
    'Lithuania', 'Luxembourg', 'Malta', 'Norway', 'Netherlands', 'Poland',
    'Portugal', 'United Kingdom', 'Czech Republic', 'Romania', 'Sweden', 'Switzerland'
}

# Europe country list (Spanish names) - for backward compatibility
EUROPE_COUNTRIES_ES = {
    'ALEMANIA', 'AUSTRIA', 'BÉLGICA', 'BULGARIA', 'CHIPRE', 'CROACIA',
    'DINAMARCA', 'ESLOVAQUIA', 'ESLOVENIA', 'ESPAÑA', 'ESTONIA', 'FINLANDIA',
    'FRANCIA', 'GRECIA', 'HUNGRÍA', 'IRLANDA', 'ISLANDIA', 'ITALIA', 'LETONIA',
    'LITUANIA', 'LUXEMBURGO', 'MALTA', 'NORUEGA', 'PAÍSES BAJOS', 'POLONIA',
    'PORTUGAL', 'REINO UNIDO', 'REPÚBLICA CHECA', 'RUMANIA', 'SUECIA', 'SUIZA'
}


def create_database(csv_file: str, db_file: str = "exports.db"):
    """Create SQLite database from enriched CSV file."""

    print(f"Loading data from {csv_file}...")
    df = pd.read_csv(csv_file, compression='gzip' if csv_file.endswith('.gz') else None)

    print(f"Loaded {len(df)} records")

    # Add English country names and region
    print("Translating country names to English...")
    df['destination_country_en'] = df['Destination Country'].apply(
        lambda x: translate_country_to_english(str(x)) if pd.notna(x) else x
    )

    print("Adding region classification...")
    df['region'] = df['destination_country_en'].apply(
        lambda x: 'Europe' if str(x) in EUROPE_COUNTRIES_EN else 'Rest of World'
    )

    # Connect to database
    print(f"Creating database: {db_file}")
    conn = sqlite3.connect(db_file)

    # Add canonical company names using vt-normalize
    if VT_NORMALIZE_AVAILABLE:
        print("Adding canonical company names (vt-normalize)...")
        df['canonical_exporter'] = df['Exporter'].apply(
            lambda x: get_canonical_name(x) if pd.notna(x) and x != '' else None
        )
        df['canonical_importer'] = df['Importer'].apply(
            lambda x: get_canonical_importer(x) if pd.notna(x) and x != '' else None
        )

        # Get reduction statistics
        raw_exporters = df['Exporter'].nunique()
        canonical_exporters = df['canonical_exporter'].nunique()
        raw_importers = df['Importer'].nunique()
        canonical_importers = df['canonical_importer'].nunique()

        print(f"  Exporters: {raw_exporters:,} → {canonical_exporters:,} canonical names")
        print(f"  Importers: {raw_importers:,} → {canonical_importers:,} canonical names")
    else:
        print("Warning: vt-normalize not available, canonical columns will be empty")
        df['canonical_exporter'] = None
        df['canonical_importer'] = None

    # Load data into main table
    print("Loading data into exports table...")
    df.to_sql('exports', conn, if_exists='replace', index=False)

    # Create indexes
    print("Creating indexes...")
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_exporter ON exports(Exporter)",
        "CREATE INDEX IF NOT EXISTS idx_canonical_exporter ON exports(canonical_exporter)",
        "CREATE INDEX IF NOT EXISTS idx_canonical_importer ON exports(canonical_importer)",
        "CREATE INDEX IF NOT EXISTS idx_destination ON exports([Destination Country])",
        "CREATE INDEX IF NOT EXISTS idx_fruit ON exports(fruit_name)",
        "CREATE INDEX IF NOT EXISTS idx_format ON exports(format_type)",
        "CREATE INDEX IF NOT EXISTS idx_size ON exports(size_mm)",
        "CREATE INDEX IF NOT EXISTS idx_certification ON exports(certification)",
        "CREATE INDEX IF NOT EXISTS idx_date ON exports(Date)",
        "CREATE INDEX IF NOT EXISTS idx_region ON exports(region)",
    ]

    for idx_sql in indexes:
        conn.execute(idx_sql)

    # Create region mapping table
    print("Creating region mapping table...")
    conn.execute("DROP TABLE IF EXISTS region_mapping")
    conn.execute("""
        CREATE TABLE region_mapping (
            country TEXT PRIMARY KEY,
            region TEXT NOT NULL
        )
    """)

    # Insert region mappings (using English country names)
    unique_countries_en = df['destination_country_en'].unique()
    region_data = [
        (country, 'Europe' if str(country) in EUROPE_COUNTRIES_EN else 'Rest of World')
        for country in unique_countries_en if pd.notna(country)
    ]
    conn.executemany("INSERT INTO region_mapping VALUES (?, ?)", region_data)

    # Create optimized views
    print("Creating database views...")

    # Exporter products view
    conn.execute("DROP VIEW IF EXISTS exporter_products")
    conn.execute("""
        CREATE VIEW exporter_products AS
        SELECT
            Exporter as exporter,
            fruit_name,
            format_type,
            size_mm,
            certification,
            region,
            COUNT(*) as shipment_count,
            SUM(net_weight_mt) as total_mt,
            AVG(usd_per_mt_fob) as avg_usd_per_mt,
            MIN(usd_per_mt_fob) as min_usd_per_mt,
            MAX(usd_per_mt_fob) as max_usd_per_mt,
            SUM([U$ FOB Tot]) as total_fob_usd
        FROM exports
        WHERE net_weight_mt > 0 AND usd_per_mt_fob > 0
        GROUP BY Exporter, fruit_name, format_type, size_mm, certification, region
    """)

    # Destination products view
    conn.execute("DROP VIEW IF EXISTS destination_products")
    conn.execute("""
        CREATE VIEW destination_products AS
        SELECT
            [Destination Country] as country,
            region,
            fruit_name,
            format_type,
            size_mm,
            certification,
            COUNT(*) as shipment_count,
            SUM(net_weight_mt) as total_mt,
            AVG(usd_per_mt_fob) as avg_usd_per_mt,
            MIN(usd_per_mt_fob) as min_usd_per_mt,
            MAX(usd_per_mt_fob) as max_usd_per_mt,
            SUM([U$ FOB Tot]) as total_fob_usd
        FROM exports
        WHERE net_weight_mt > 0 AND usd_per_mt_fob > 0
        GROUP BY [Destination Country], region, fruit_name, format_type, size_mm, certification
    """)

    # Monthly exports view for seasonality
    conn.execute("DROP VIEW IF EXISTS monthly_exports")
    conn.execute("""
        CREATE VIEW monthly_exports AS
        SELECT
            fruit_name,
            strftime('%Y', Date) as year,
            strftime('%m', Date) as month,
            CAST(strftime('%m', Date) AS INTEGER) as month_num,
            COUNT(*) as shipment_count,
            SUM(net_weight_mt) as total_mt,
            AVG(usd_per_mt_fob) as avg_usd_per_mt
        FROM exports
        WHERE net_weight_mt > 0
        GROUP BY fruit_name, year, month
        ORDER BY fruit_name, year, month
    """)

    # Regional exports view
    conn.execute("DROP VIEW IF EXISTS regional_exports")
    conn.execute("""
        CREATE VIEW regional_exports AS
        SELECT
            region,
            [Destination Country] as country,
            fruit_name,
            format_type,
            size_mm,
            certification,
            COUNT(*) as shipment_count,
            SUM(net_weight_mt) as total_mt,
            AVG(usd_per_mt_fob) as avg_usd_per_mt,
            SUM([U$ FOB Tot]) as total_fob_usd
        FROM exports
        WHERE net_weight_mt > 0 AND usd_per_mt_fob > 0
        GROUP BY region, [Destination Country], fruit_name, format_type, size_mm, certification
    """)

    conn.commit()

    # Print statistics
    print("\n" + "="*80)
    print("DATABASE CREATED SUCCESSFULLY")
    print("="*80)

    cursor = conn.cursor()

    # Table counts
    cursor.execute("SELECT COUNT(*) FROM exports")
    total_records = cursor.fetchone()[0]
    print(f"Total export records: {total_records:,}")

    cursor.execute("SELECT COUNT(DISTINCT Exporter) FROM exports")
    total_exporters = cursor.fetchone()[0]
    print(f"Unique exporters: {total_exporters:,}")

    cursor.execute("SELECT COUNT(DISTINCT [Destination Country]) FROM exports")
    total_destinations = cursor.fetchone()[0]
    print(f"Unique destinations: {total_destinations:,}")

    cursor.execute("SELECT COUNT(*) FROM region_mapping WHERE region = 'Europe'")
    europe_count = cursor.fetchone()[0]
    print(f"European countries: {europe_count}")

    cursor.execute("""
        SELECT region, COUNT(*) as countries, SUM(total_mt) as mt
        FROM (
            SELECT region, [Destination Country], SUM(net_weight_mt) as total_mt
            FROM exports
            GROUP BY region, [Destination Country]
        )
        GROUP BY region
    """)

    print("\nExports by Region:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} countries, {row[2]:,.2f} MT")

    # Database size
    db_path = Path(db_file)
    db_size_mb = db_path.stat().st_size / (1024 * 1024)
    print(f"\nDatabase file size: {db_size_mb:.2f} MB")
    print(f"Database location: {db_path.absolute()}")

    conn.close()
    print("\n" + "="*80)


if __name__ == "__main__":
    from config_loader import load_config, get_input_path, get_output_path

    # Load configuration
    config = load_config()

    # Get paths from config
    enriched_csv = str(get_input_path(config, 'enriched_csv'))
    database_path = str(get_output_path(config, 'database'))

    create_database(enriched_csv, database_path)
