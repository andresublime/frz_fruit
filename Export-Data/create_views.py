"""
Create database views for clean data and summaries.
"""

from core.database import create_view, execute_query, DEFAULT_DB_PATH


def create_clean_exports_view():
    """
    Create v_clean_exports view with filtered, YTD data.

    Filters:
    - analysis_valid = 1 (passed data quality checks)
    - Date between Oct 2024 and Oct 2025 (YTD period)
    """
    query = """
        SELECT *
        FROM exports
        WHERE analysis_valid = 1
          AND Date >= '2024-10-01'
          AND Date <= '2025-10-31'
    """

    create_view('v_clean_exports', query)

    # Verify
    df = execute_query("SELECT COUNT(*) as count FROM v_clean_exports")
    count = df.iloc[0]['count']
    print(f"✓ Created v_clean_exports view with {count:,} records")

    return count


def main():
    print("Creating database views...")
    print("=" * 60)

    # Create clean exports view
    count = create_clean_exports_view()

    # Show sample
    df = execute_query("""
        SELECT canonical_exporter, fruit_name, format_type, net_weight_mt, usd_per_mt_fob
        FROM v_clean_exports
        LIMIT 5
    """)

    print("\nSample of clean exports:")
    print(df.to_string(index=False))

    print("\n✓ Views created successfully!")


if __name__ == '__main__':
    main()
