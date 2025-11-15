"""
Database Utilities for Peru Frozen Fruit Export Analysis

Provides centralized database connection and query utilities.
All analysis modules should use these functions for consistency.
"""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import Optional, List, Tuple
from datetime import datetime, timedelta
from contextlib import contextmanager


# Default database path
DEFAULT_DB_PATH = Path(__file__).parent.parent / 'exports.db'


@contextmanager
def get_connection(db_path: Optional[Path] = None):
    """
    Context manager for database connections.

    Usage:
        with get_connection() as conn:
            df = pd.read_sql("SELECT * FROM exports", conn)

    Args:
        db_path: Path to SQLite database (default: exports.db in project root)

    Yields:
        sqlite3.Connection object
    """
    if db_path is None:
        db_path = DEFAULT_DB_PATH

    conn = sqlite3.connect(str(db_path))
    try:
        yield conn
    finally:
        conn.close()


def execute_query(
    query: str,
    params: Optional[Tuple] = None,
    db_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Execute a SQL query and return results as DataFrame.

    Args:
        query: SQL query string
        params: Optional query parameters (for parameterized queries)
        db_path: Optional database path

    Returns:
        DataFrame with query results
    """
    with get_connection(db_path) as conn:
        if params:
            return pd.read_sql_query(query, conn, params=params)
        else:
            return pd.read_sql_query(query, conn)


def execute_statement(
    statement: str,
    params: Optional[Tuple] = None,
    db_path: Optional[Path] = None
) -> None:
    """
    Execute a SQL statement (INSERT, UPDATE, DELETE, CREATE, etc.).

    Args:
        statement: SQL statement string
        params: Optional statement parameters
        db_path: Optional database path
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        if params:
            cursor.execute(statement, params)
        else:
            cursor.execute(statement)
        conn.commit()


def load_all_exports(db_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load all export records from database.

    Args:
        db_path: Optional database path

    Returns:
        DataFrame with all exports
    """
    query = "SELECT * FROM exports"
    return execute_query(query, db_path=db_path)


def get_ytd_date_range() -> Tuple[str, str]:
    """
    Get YTD date range (Oct 2024 - Oct 2025).

    Returns:
        Tuple of (start_date, end_date) as ISO format strings
    """
    # User specified YTD = Oct 2024 to Oct 2025
    start_date = '2024-10-01'
    end_date = '2025-10-31'

    return start_date, end_date


def load_ytd_exports(db_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load export records for YTD period (Oct 2024 - Oct 2025).

    Args:
        db_path: Optional database path

    Returns:
        DataFrame with YTD exports only
    """
    start_date, end_date = get_ytd_date_range()

    query = """
        SELECT *
        FROM exports
        WHERE Date >= ? AND Date <= ?
    """

    return execute_query(query, params=(start_date, end_date), db_path=db_path)


def load_clean_exports(
    ytd_only: bool = True,
    db_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Load clean, filtered export records ready for analysis.

    Applies data quality filters:
    - No air freight
    - No samples
    - No small shipments
    - No price outliers
    - YTD date range (optional)

    Args:
        ytd_only: Whether to filter to YTD period (Oct 2024 - Oct 2025)
        db_path: Optional database path

    Returns:
        DataFrame with clean export records
    """
    # Load from v_clean_exports view if it exists, otherwise filter manually
    try:
        if ytd_only:
            query = "SELECT * FROM v_clean_exports"
        else:
            query = "SELECT * FROM exports WHERE analysis_valid = 1"

        return execute_query(query, db_path=db_path)

    except pd.io.sql.DatabaseError:
        # View doesn't exist yet - load and filter manually
        from core.filters import filter_valid_shipments

        if ytd_only:
            df = load_ytd_exports(db_path)
        else:
            df = load_all_exports(db_path)

        return filter_valid_shipments(df)


def get_unique_values(
    column: str,
    table: str = 'exports',
    db_path: Optional[Path] = None
) -> List[str]:
    """
    Get list of unique values for a column.

    Args:
        column: Column name
        table: Table name (default: exports)
        db_path: Optional database path

    Returns:
        List of unique values
    """
    query = f"SELECT DISTINCT {column} FROM {table} WHERE {column} IS NOT NULL ORDER BY {column}"
    df = execute_query(query, db_path=db_path)
    return df[column].tolist()


def get_fruit_types(db_path: Optional[Path] = None) -> List[str]:
    """Get list of all fruit types in database."""
    return get_unique_values('fruit_name', db_path=db_path)


def get_exporters(db_path: Optional[Path] = None) -> List[str]:
    """Get list of all exporters in database."""
    return get_unique_values('Exporter', db_path=db_path)


def get_format_types(db_path: Optional[Path] = None) -> List[str]:
    """Get list of all format types in database."""
    return get_unique_values('format_type', db_path=db_path)


def get_destinations(db_path: Optional[Path] = None) -> List[str]:
    """Get list of all destination countries in database."""
    return get_unique_values('destination_country_en', db_path=db_path)


def get_table_stats(table: str = 'exports', db_path: Optional[Path] = None) -> dict:
    """
    Get basic statistics about a table.

    Args:
        table: Table name
        db_path: Optional database path

    Returns:
        Dictionary with:
        - total_records
        - date_range (min, max)
        - total_exporters
        - total_fruits
        - total_destinations
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()

        # Total records
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        total_records = cursor.fetchone()[0]

        # Date range
        cursor.execute(f"SELECT MIN(Date), MAX(Date) FROM {table}")
        date_range = cursor.fetchone()

        # Unique counts
        cursor.execute(f"SELECT COUNT(DISTINCT Exporter) FROM {table}")
        total_exporters = cursor.fetchone()[0]

        cursor.execute(f"SELECT COUNT(DISTINCT fruit_name) FROM {table}")
        total_fruits = cursor.fetchone()[0]

        cursor.execute(f"SELECT COUNT(DISTINCT destination_country_en) FROM {table}")
        total_destinations = cursor.fetchone()[0]

    return {
        'total_records': total_records,
        'date_range': date_range,
        'total_exporters': total_exporters,
        'total_fruits': total_fruits,
        'total_destinations': total_destinations,
    }


def create_view(view_name: str, query: str, db_path: Optional[Path] = None) -> None:
    """
    Create or replace a database view.

    Args:
        view_name: Name of the view to create
        query: SELECT query defining the view
        db_path: Optional database path
    """
    drop_statement = f"DROP VIEW IF EXISTS {view_name}"
    create_statement = f"CREATE VIEW {view_name} AS {query}"

    execute_statement(drop_statement, db_path=db_path)
    execute_statement(create_statement, db_path=db_path)


def add_column_if_not_exists(
    table: str,
    column: str,
    column_type: str,
    default_value: Optional[str] = None,
    db_path: Optional[Path] = None
) -> bool:
    """
    Add a column to a table if it doesn't already exist.

    Args:
        table: Table name
        column: Column name to add
        column_type: SQL column type (e.g., "TEXT", "INTEGER", "REAL")
        default_value: Optional default value
        db_path: Optional database path

    Returns:
        True if column was added, False if it already existed
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()

        # Check if column exists
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]

        if column in columns:
            return False

        # Add column
        default_clause = f" DEFAULT {default_value}" if default_value else ""
        alter_statement = f"ALTER TABLE {table} ADD COLUMN {column} {column_type}{default_clause}"
        cursor.execute(alter_statement)
        conn.commit()

        return True


def create_index_if_not_exists(
    index_name: str,
    table: str,
    columns: List[str],
    db_path: Optional[Path] = None
) -> bool:
    """
    Create an index if it doesn't already exist.

    Args:
        index_name: Name of the index
        table: Table name
        columns: List of column names to index
        db_path: Optional database path

    Returns:
        True if index was created, False if it already existed
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()

        # Check if index exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name=?",
            (index_name,)
        )

        if cursor.fetchone():
            return False

        # Create index
        columns_str = ', '.join(columns)
        create_statement = f"CREATE INDEX {index_name} ON {table} ({columns_str})"
        cursor.execute(create_statement)
        conn.commit()

        return True


# Testing
if __name__ == '__main__':
    print("Database Utilities Test")
    print("=" * 60)

    # Test connection
    with get_connection() as conn:
        print(f"✓ Connected to database: {DEFAULT_DB_PATH}")

    # Get stats
    stats = get_table_stats()
    print("\nDatabase Statistics:")
    print("=" * 60)
    print(f"Total records: {stats['total_records']:,}")
    print(f"Date range: {stats['date_range'][0]} to {stats['date_range'][1]}")
    print(f"Exporters: {stats['total_exporters']:,}")
    print(f"Fruit types: {stats['total_fruits']:,}")
    print(f"Destinations: {stats['total_destinations']:,}")

    # Test YTD date range
    start, end = get_ytd_date_range()
    print(f"\nYTD period: {start} to {end}")

    # Load sample data
    print("\nLoading YTD exports...")
    df = load_ytd_exports()
    print(f"✓ Loaded {len(df):,} YTD records")

    # Show fruit types
    fruits = get_fruit_types()
    print(f"\nFruit types ({len(fruits)}):")
    print(", ".join(fruits[:10]) + ("..." if len(fruits) > 10 else ""))

    print("\n✓ All tests passed!")
