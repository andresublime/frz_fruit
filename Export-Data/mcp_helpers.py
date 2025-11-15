"""
Helper functions for Peru Frozen Fruit Export MCP Server.
Shared utilities used across all MCP tools.
"""
import sqlite3
from pathlib import Path
from typing import Optional, List
from datetime import datetime, timedelta
from difflib import SequenceMatcher

# Database path
DB_PATH = Path(__file__).parent / "exports.db"


def get_db_connection():
    """Get database connection."""
    return sqlite3.connect(DB_PATH)


def parse_relative_date(date_str: str) -> Optional[datetime]:
    """
    Parse relative date strings like 'last_30_days', 'ytd', 'q1_2024', etc.

    Args:
        date_str: Relative date string or ISO date

    Returns:
        datetime object or None
    """
    today = datetime.now()
    date_str_lower = date_str.lower()

    # Absolute date
    if '-' in date_str and len(date_str) >= 10:
        try:
            return datetime.fromisoformat(date_str[:10])
        except:
            pass

    # Relative dates
    if date_str_lower == 'today':
        return today
    elif date_str_lower == 'yesterday':
        return today - timedelta(days=1)
    elif date_str_lower.startswith('last_') and date_str_lower.endswith('_days'):
        days = int(date_str_lower.replace('last_', '').replace('_days', ''))
        return today - timedelta(days=days)
    elif date_str_lower == 'mtd':  # Month to date
        return today.replace(day=1)
    elif date_str_lower == 'qtd':  # Quarter to date
        quarter_start_month = ((today.month - 1) // 3) * 3 + 1
        return today.replace(month=quarter_start_month, day=1)
    elif date_str_lower == 'ytd':  # Year to date
        return today.replace(month=1, day=1)
    elif date_str_lower.startswith('q') and '_' in date_str_lower:  # q1_2024
        parts = date_str_lower.split('_')
        quarter = int(parts[0][1])
        year = int(parts[1])
        month = (quarter - 1) * 3 + 1
        return datetime(year, month, 1)

    return None


def calculate_hhi(shares: List[float]) -> float:
    """
    Calculate Herfindahl-Hirschman Index (market concentration).

    Args:
        shares: List of market shares as decimals (e.g., [0.25, 0.15, 0.10, ...])

    Returns:
        HHI value (0-10000, higher = more concentrated)
    """
    return sum([(share * 100) ** 2 for share in shares])


def calculate_growth_rate(old_value: float, new_value: float) -> Optional[float]:
    """
    Calculate percentage growth rate.

    Args:
        old_value: Previous period value
        new_value: Current period value

    Returns:
        Growth rate as percentage or None if old_value is 0
    """
    if old_value == 0:
        return None
    return ((new_value - old_value) / old_value) * 100


def fuzzy_match_exporter(search_term: str, threshold: float = 0.6) -> List[str]:
    """
    Find exporter names using fuzzy matching.

    Args:
        search_term: Name to search for
        threshold: Similarity threshold (0.0 to 1.0)

    Returns:
        List of matching exporter names
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT Exporter FROM exports")
    all_exporters = [row[0] for row in cursor.fetchall()]
    conn.close()

    search_lower = search_term.lower()
    matches = []

    for exporter in all_exporters:
        exporter_lower = exporter.lower()

        # Exact match
        if search_lower == exporter_lower:
            return [exporter]

        # Substring match
        if search_lower in exporter_lower:
            matches.append((exporter, 1.0))
            continue

        # Fuzzy match using SequenceMatcher
        similarity = SequenceMatcher(None, search_lower, exporter_lower).ratio()
        if similarity >= threshold:
            matches.append((exporter, similarity))

    # Sort by similarity score descending
    matches.sort(key=lambda x: x[1], reverse=True)

    return [name for name, score in matches[:10]]  # Return top 10 matches
