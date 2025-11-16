"""
FastMCP Server for Peru Frozen Fruit Export Data
Provides tools for querying and analyzing export data through Claude Desktop.
Supports both English and Spanish country names with automatic translation.

CRITICAL INSTRUCTIONS FOR LLM:
- ONLY use data explicitly returned by these tools
- DO NOT infer, extrapolate, or create hypothetical data
- DO NOT make recommendations beyond what the data directly shows
- DO NOT generate business plans, strategies, or projections
- If data is missing, state "Data not available" - do NOT fill gaps
- Stick to descriptive statistics and direct observations from query results
"""
import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from difflib import SequenceMatcher
import fastmcp
from translations import normalize_country_name, translate_country_to_english

# Initialize MCP server
mcp = fastmcp.FastMCP("Peru Frozen Fruit Exports")

# Database path
DB_PATH = Path(__file__).parent / "exports.db"


def get_db_connection():
    """Get database connection."""
    return sqlite3.connect(DB_PATH)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

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


# ============================================================================
# EXISTING TOOLS
# ============================================================================


@mcp.tool()
def query_by_exporter(
    exporter_name: str,
    destination_region: Optional[str] = None,
    destination_country: Optional[str] = None,
    fruit: Optional[str] = None,
    limit: int = 100
) -> Dict[str, Any]:
    """
    Query exports by company name with fuzzy matching.

    Args:
        exporter_name: Company name (supports partial/fuzzy matching)
        destination_region: Filter by 'Europe' or 'Rest of World'
        destination_country: Specific destination country
        fruit: Filter by fruit type
        limit: Maximum results to return (default 100)

    Returns:
        Export records with specs and prices
    """
    # Find matching exporters
    matching_exporters = fuzzy_match_exporter(exporter_name)

    if not matching_exporters:
        return {
            "error": f"No exporters found matching '{exporter_name}'",
            "suggestion": "Try a different spelling or partial name"
        }

    conn = get_db_connection()
    cursor = conn.cursor()

    # Build query
    query = """
        SELECT
            Exporter,
            fruit_name,
            variety,
            format_type,
            size_mm,
            certification,
            [Destination Country],
            region,
            Date,
            net_weight_mt,
            usd_per_mt_fob,
            [U$ FOB Tot]
        FROM exports
        WHERE Exporter IN ({})
          AND net_weight_mt > 0
          AND usd_per_mt_fob > 0
    """.format(','.join('?' * len(matching_exporters)))

    params = list(matching_exporters)

    if destination_region:
        query += " AND region = ?"
        params.append(destination_region)

    if destination_country:
        query += " AND [Destination Country] LIKE ?"
        params.append(f"%{destination_country}%")

    if fruit:
        query += " AND fruit_name LIKE ?"
        params.append(f"%{fruit}%")

    query += f" ORDER BY Date DESC LIMIT {limit}"

    cursor.execute(query, params)
    rows = cursor.fetchall()

    results = []
    total_mt = 0
    total_fob = 0

    for row in rows:
        results.append({
            "exporter": row[0],
            "fruit": row[1],
            "variety": row[2],
            "format": row[3],
            "size": row[4],
            "certification": row[5],
            "destination": row[6],
            "region": row[7],
            "date": row[8],
            "mt": round(row[9], 2),
            "usd_per_mt": round(row[10], 2),
            "total_fob_usd": round(row[11], 2)
        })
        total_mt += row[9]
        total_fob += row[11]

    conn.close()

    return {
        "query": f"Exports by {exporter_name}",
        "matched_exporters": matching_exporters,
        "filters_applied": {
            "destination_region": destination_region,
            "destination_country": destination_country,
            "fruit": fruit
        },
        "result_count": len(results),
        "total_mt": round(total_mt, 2),
        "total_fob_usd": round(total_fob, 2),
        "avg_usd_per_mt": round(total_fob / total_mt, 2) if total_mt > 0 else 0,
        "results": results
    }


@mcp.tool()
def query_by_destination(
    country: str,
    fruit: Optional[str] = None,
    certification: Optional[str] = None,
    limit: int = 100
) -> Dict[str, Any]:
    """
    Query exports to a specific destination country.

    Supports both English and Spanish country names (e.g., "Poland" or "POLONIA").

    Args:
        country: Destination country name in English (e.g., "Poland", "Germany", "United States")
        fruit: Filter by fruit type
        certification: Filter by 'organic', 'conventional', or 'unknown'
        limit: Maximum results to return (default 100)

    Returns:
        Product breakdown with volumes and prices
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            fruit_name,
            format_type,
            size_mm,
            certification,
            Exporter,
            Date,
            net_weight_mt,
            usd_per_mt_fob,
            [U$ FOB Tot],
            destination_country_en
        FROM exports
        WHERE destination_country_en LIKE ?
          AND net_weight_mt > 0
          AND usd_per_mt_fob > 0
    """

    # Support both English and Spanish input
    params = [f"%{country}%"]

    if fruit:
        query += " AND fruit_name LIKE ?"
        params.append(f"%{fruit}%")

    if certification:
        query += " AND certification = ?"
        params.append(certification)

    query += f" ORDER BY Date DESC LIMIT {limit}"

    cursor.execute(query, params)
    rows = cursor.fetchall()

    results = []
    total_mt = 0
    total_fob = 0

    for row in rows:
        results.append({
            "fruit": row[0],
            "format": row[1],
            "size": row[2],
            "certification": row[3],
            "exporter": row[4],
            "date": row[5],
            "mt": round(row[6], 2),
            "usd_per_mt": round(row[7], 2),
            "total_fob_usd": round(row[8], 2),
            "destination": row[9]  # English country name
        })
        total_mt += row[6]
        total_fob += row[8]

    conn.close()

    return {
        "query": f"Exports to {country}",
        "filters_applied": {
            "fruit": fruit,
            "certification": certification
        },
        "result_count": len(results),
        "total_mt": round(total_mt, 2),
        "total_fob_usd": round(total_fob, 2),
        "avg_usd_per_mt": round(total_fob / total_mt, 2) if total_mt > 0 else 0,
        "results": results
    }


@mcp.tool()
def query_by_product(
    fruit: str,
    format_type: Optional[str] = None,
    size: Optional[str] = None,
    certification: Optional[str] = None,
    limit: int = 100
) -> Dict[str, Any]:
    """
    Query exports by product specifications.

    Args:
        fruit: Fruit name (required)
        format_type: Format like 'chunks', 'slices', 'puree', etc.
        size: Size specification like '20x20', '25x25'
        certification: 'organic', 'conventional', or 'unknown'
        limit: Maximum results to return (default 100)

    Returns:
        Matching exports with exporter, destination, and pricing
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            Exporter,
            [Destination Country],
            region,
            fruit_name,
            variety,
            format_type,
            size_mm,
            certification,
            Date,
            net_weight_mt,
            usd_per_mt_fob,
            [U$ FOB Tot]
        FROM exports
        WHERE fruit_name LIKE ?
          AND net_weight_mt > 0
          AND usd_per_mt_fob > 0
    """

    params = [f"%{fruit}%"]

    if format_type:
        query += " AND format_type LIKE ?"
        params.append(f"%{format_type}%")

    if size:
        query += " AND size_mm LIKE ?"
        params.append(f"%{size}%")

    if certification:
        query += " AND certification = ?"
        params.append(certification)

    query += f" ORDER BY Date DESC LIMIT {limit}"

    cursor.execute(query, params)
    rows = cursor.fetchall()

    results = []
    total_mt = 0
    total_fob = 0

    for row in rows:
        results.append({
            "exporter": row[0],
            "destination": row[1],
            "region": row[2],
            "fruit": row[3],
            "variety": row[4],
            "format": row[5],
            "size": row[6],
            "certification": row[7],
            "date": row[8],
            "mt": round(row[9], 2),
            "usd_per_mt": round(row[10], 2),
            "total_fob_usd": round(row[11], 2)
        })
        total_mt += row[9]
        total_fob += row[11]

    conn.close()

    return {
        "query": f"Exports of {fruit}",
        "filters_applied": {
            "format_type": format_type,
            "size": size,
            "certification": certification
        },
        "result_count": len(results),
        "total_mt": round(total_mt, 2),
        "total_fob_usd": round(total_fob, 2),
        "avg_usd_per_mt": round(total_fob / total_mt, 2) if total_mt > 0 else 0,
        "results": results
    }


@mcp.tool()
def search_exporters(search_term: str, limit: int = 20) -> Dict[str, Any]:
    """
    Fuzzy search for exporter names.

    Args:
        search_term: Partial or full exporter name
        limit: Maximum results to return

    Returns:
        List of matching exporter names with export counts
    """
    matching_exporters = fuzzy_match_exporter(search_term, threshold=0.4)

    if not matching_exporters:
        return {
            "query": search_term,
            "matches": [],
            "message": "No matching exporters found"
        }

    conn = get_db_connection()
    cursor = conn.cursor()

    placeholders = ','.join('?' * len(matching_exporters))
    cursor.execute(f"""
        SELECT
            Exporter,
            COUNT(*) as shipment_count,
            SUM(net_weight_mt) as total_mt,
            SUM([U$ FOB Tot]) as total_fob
        FROM exports
        WHERE Exporter IN ({placeholders})
        GROUP BY Exporter
        ORDER BY total_mt DESC
        LIMIT {limit}
    """, matching_exporters)

    results = []
    for row in cursor.fetchall():
        results.append({
            "exporter": row[0],
            "shipment_count": row[1],
            "total_mt": round(row[2], 2),
            "total_fob_usd": round(row[3], 2)
        })

    conn.close()

    return {
        "query": search_term,
        "match_count": len(results),
        "matches": results
    }


@mcp.tool()
def analyze_seasonality(
    fruit: str,
    year: Optional[int] = None
) -> Dict[str, Any]:
    """
    Analyze seasonal export patterns for a fruit with auto-detected peak seasons.

    Args:
        fruit: Fruit name to analyze
        year: Specific year to analyze (optional, analyzes all years if not provided)

    Returns:
        Monthly trends with identified peak seasons
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    if year:
        cursor.execute("""
            SELECT
                month,
                month_num,
                SUM(total_mt) as total_mt,
                AVG(avg_usd_per_mt) as avg_usd_per_mt,
                SUM(shipment_count) as shipment_count
            FROM monthly_exports
            WHERE fruit_name LIKE ? AND year = ?
            GROUP BY month, month_num
            ORDER BY month_num
        """, (f"%{fruit}%", str(year)))
    else:
        cursor.execute("""
            SELECT
                month,
                month_num,
                SUM(total_mt) as total_mt,
                AVG(avg_usd_per_mt) as avg_usd_per_mt,
                SUM(shipment_count) as shipment_count
            FROM monthly_exports
            WHERE fruit_name LIKE ?
            GROUP BY month, month_num
            ORDER BY month_num
        """, (f"%{fruit}%",))

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return {
            "query": f"Seasonality analysis for {fruit}",
            "error": "No data found for this fruit"
        }

    monthly_data = []
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    total_volume = sum(row[2] for row in rows)
    avg_monthly_volume = total_volume / len(rows) if rows else 0

    for row in rows:
        month_mt = row[2]
        pct_above_avg = ((month_mt - avg_monthly_volume) / avg_monthly_volume * 100) if avg_monthly_volume > 0 else 0

        monthly_data.append({
            "month": month_names[row[1] - 1],
            "month_num": row[1],
            "total_mt": round(month_mt, 2),
            "avg_usd_per_mt": round(row[3], 2) if row[3] else 0,
            "shipment_count": row[4],
            "pct_above_avg": round(pct_above_avg, 1)
        })

    # Sort by volume to find peaks
    sorted_by_volume = sorted(monthly_data, key=lambda x: x['total_mt'], reverse=True)
    peak_months = sorted_by_volume[:3]
    low_months = sorted(monthly_data, key=lambda x: x['total_mt'])[:3]

    return {
        "query": f"Seasonality analysis for {fruit}",
        "year": year if year else "all years",
        "total_volume_mt": round(total_volume, 2),
        "avg_monthly_mt": round(avg_monthly_volume, 2),
        "peak_seasons": [
            {
                "month": m["month"],
                "mt": m["total_mt"],
                "pct_above_avg": m["pct_above_avg"]
            } for m in peak_months
        ],
        "low_seasons": [
            {
                "month": m["month"],
                "mt": m["total_mt"],
                "pct_below_avg": abs(m["pct_above_avg"])
            } for m in low_months
        ],
        "monthly_breakdown": monthly_data,
        "insight": f"Peak export season is {peak_months[0]['month']} with {peak_months[0]['total_mt']} MT ({peak_months[0]['pct_above_avg']:+.1f}% above average)"
    }


@mcp.tool()
def get_price_analysis(
    fruit: Optional[str] = None,
    format_type: Optional[str] = None,
    certification: Optional[str] = None,
    destination_region: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze price ranges (min/avg/max USD/MT) by product and destination.

    Args:
        fruit: Filter by fruit type
        format_type: Filter by format
        certification: Filter by certification type
        destination_region: Filter by 'Europe' or 'Rest of World'

    Returns:
        Price statistics grouped by product
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            fruit_name,
            format_type,
            size_mm,
            certification,
            region,
            COUNT(*) as sample_count,
            MIN(usd_per_mt_fob) as min_price,
            AVG(usd_per_mt_fob) as avg_price,
            MAX(usd_per_mt_fob) as max_price,
            SUM(net_weight_mt) as total_mt
        FROM exports
        WHERE net_weight_mt > 0 AND usd_per_mt_fob > 0
    """

    params = []

    if fruit:
        query += " AND fruit_name LIKE ?"
        params.append(f"%{fruit}%")

    if format_type:
        query += " AND format_type LIKE ?"
        params.append(f"%{format_type}%")

    if certification:
        query += " AND certification = ?"
        params.append(certification)

    if destination_region:
        query += " AND region = ?"
        params.append(destination_region)

    query += """
        GROUP BY fruit_name, format_type, size_mm, certification, region
        HAVING sample_count >= 3
        ORDER BY total_mt DESC
        LIMIT 50
    """

    cursor.execute(query, params)
    rows = cursor.fetchall()

    results = []
    for row in rows:
        results.append({
            "fruit": row[0],
            "format": row[1],
            "size": row[2],
            "certification": row[3],
            "region": row[4],
            "sample_count": row[5],
            "min_usd_per_mt": round(row[6], 2),
            "avg_usd_per_mt": round(row[7], 2),
            "max_usd_per_mt": round(row[8], 2),
            "price_range": round(row[8] - row[6], 2),
            "total_mt": round(row[9], 2)
        })

    conn.close()

    return {
        "query": "Price analysis",
        "filters_applied": {
            "fruit": fruit,
            "format_type": format_type,
            "certification": certification,
            "destination_region": destination_region
        },
        "result_count": len(results),
        "results": results
    }


@mcp.tool()
def summarize_by_region(
    fruit: Optional[str] = None,
    show_countries: bool = True,
    limit_countries: int = 10
) -> Dict[str, Any]:
    """
    Summarize exports by region (Europe vs Rest of World) with country breakdowns.

    Args:
        fruit: Filter by specific fruit
        show_countries: Include country-level breakdowns
        limit_countries: Max countries to show per region

    Returns:
        Regional summary with country details
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Regional totals
    if fruit:
        cursor.execute("""
            SELECT
                region,
                COUNT(*) as shipment_count,
                SUM(net_weight_mt) as total_mt,
                SUM([U$ FOB Tot]) as total_fob,
                AVG(usd_per_mt_fob) as avg_usd_per_mt
            FROM exports
            WHERE fruit_name LIKE ? AND net_weight_mt > 0
            GROUP BY region
            ORDER BY total_mt DESC
        """, (f"%{fruit}%",))
    else:
        cursor.execute("""
            SELECT
                region,
                COUNT(*) as shipment_count,
                SUM(net_weight_mt) as total_mt,
                SUM([U$ FOB Tot]) as total_fob,
                AVG(usd_per_mt_fob) as avg_usd_per_mt
            FROM exports
            WHERE net_weight_mt > 0
            GROUP BY region
            ORDER BY total_mt DESC
        """)

    regional_summary = []
    for row in cursor.fetchall():
        regional_summary.append({
            "region": row[0],
            "shipment_count": row[1],
            "total_mt": round(row[2], 2),
            "total_fob_usd": round(row[3], 2),
            "avg_usd_per_mt": round(row[4], 2)
        })

    # Country breakdowns if requested
    country_breakdowns = {}
    if show_countries:
        for region_data in regional_summary:
            region = region_data["region"]

            if fruit:
                cursor.execute(f"""
                    SELECT
                        [Destination Country],
                        COUNT(*) as shipment_count,
                        SUM(net_weight_mt) as total_mt,
                        SUM([U$ FOB Tot]) as total_fob,
                        AVG(usd_per_mt_fob) as avg_usd_per_mt
                    FROM exports
                    WHERE region = ? AND fruit_name LIKE ? AND net_weight_mt > 0
                    GROUP BY [Destination Country]
                    ORDER BY total_mt DESC
                    LIMIT {limit_countries}
                """, (region, f"%{fruit}%"))
            else:
                cursor.execute(f"""
                    SELECT
                        [Destination Country],
                        COUNT(*) as shipment_count,
                        SUM(net_weight_mt) as total_mt,
                        SUM([U$ FOB Tot]) as total_fob,
                        AVG(usd_per_mt_fob) as avg_usd_per_mt
                    FROM exports
                    WHERE region = ? AND net_weight_mt > 0
                    GROUP BY [Destination Country]
                    ORDER BY total_mt DESC
                    LIMIT {limit_countries}
                """, (region,))

            countries = []
            for row in cursor.fetchall():
                countries.append({
                    "country": row[0],
                    "shipment_count": row[1],
                    "total_mt": round(row[2], 2),
                    "total_fob_usd": round(row[3], 2),
                    "avg_usd_per_mt": round(row[4], 2)
                })

            country_breakdowns[region] = countries

    conn.close()

    return {
        "query": "Regional summary",
        "fruit_filter": fruit,
        "regional_totals": regional_summary,
        "country_breakdowns": country_breakdowns if show_countries else None
    }


@mcp.tool()
def compare_products(
    products: List[Dict[str, str]],
    metric: str = "both"
) -> Dict[str, Any]:
    """
    Compare multiple products side-by-side.

    Args:
        products: List of products to compare, each with fruit, format?, size?, certification?
        metric: What to compare - 'volume' (MT), 'price' (USD/MT), or 'both'

    Returns:
        Side-by-side comparison of products

    Example:
        products=[
            {"fruit": "mango", "format": "chunks", "size": "20x20"},
            {"fruit": "mango", "format": "chunks", "size": "25x25"}
        ]
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    comparisons = []

    for product in products:
        query = """
            SELECT
                COUNT(*) as shipment_count,
                SUM(net_weight_mt) as total_mt,
                AVG(usd_per_mt_fob) as avg_usd_per_mt,
                MIN(usd_per_mt_fob) as min_usd_per_mt,
                MAX(usd_per_mt_fob) as max_usd_per_mt,
                SUM([U$ FOB Tot]) as total_fob
            FROM exports
            WHERE fruit_name LIKE ?
              AND net_weight_mt > 0
              AND usd_per_mt_fob > 0
        """

        params = [f"%{product['fruit']}%"]

        if product.get('format'):
            query += " AND format_type LIKE ?"
            params.append(f"%{product['format']}%")

        if product.get('size'):
            query += " AND size_mm LIKE ?"
            params.append(f"%{product['size']}%")

        if product.get('certification'):
            query += " AND certification = ?"
            params.append(product['certification'])

        cursor.execute(query, params)
        row = cursor.fetchone()

        comparisons.append({
            "product": product,
            "shipment_count": row[0],
            "total_mt": round(row[1], 2) if row[1] else 0,
            "avg_usd_per_mt": round(row[2], 2) if row[2] else 0,
            "min_usd_per_mt": round(row[3], 2) if row[3] else 0,
            "max_usd_per_mt": round(row[4], 2) if row[4] else 0,
            "total_fob_usd": round(row[5], 2) if row[5] else 0
        })

    conn.close()

    # Sort by metric
    if metric == "volume":
        comparisons.sort(key=lambda x: x['total_mt'], reverse=True)
    elif metric == "price":
        comparisons.sort(key=lambda x: x['avg_usd_per_mt'], reverse=True)

    return {
        "query": "Product comparison",
        "comparison_metric": metric,
        "products_compared": len(comparisons),
        "comparisons": comparisons
    }


@mcp.tool()
def compare_exporters(
    exporter_names: List[str],
    date_range_months: int = None
) -> Dict[str, Any]:
    """
    Compare performance between multiple exporters.

    Args:
        exporter_names: List of exporter names (fuzzy matching supported)
        date_range_months: Limit to last N months (optional)

    Returns:
        Side-by-side comparison of exporters
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    comparisons = []

    for name in exporter_names:
        matching = fuzzy_match_exporter(name)
        if not matching:
            comparisons.append({
                "search_term": name,
                "error": "No matching exporter found"
            })
            continue

        exporter = matching[0]

        query = """
            SELECT
                COUNT(*) as shipment_count,
                SUM(net_weight_mt) as total_mt,
                SUM([U$ FOB Tot]) as total_fob,
                AVG(usd_per_mt_fob) as avg_usd_per_mt,
                COUNT(DISTINCT [Destination Country]) as destination_count,
                COUNT(DISTINCT fruit_name) as fruit_count
            FROM exports
            WHERE Exporter = ?
              AND net_weight_mt > 0
        """

        params = [exporter]

        if date_range_months:
            query += " AND Date >= date('now', '-{} months')".format(date_range_months)

        cursor.execute(query, params)
        row = cursor.fetchone()

        comparisons.append({
            "exporter": exporter,
            "shipment_count": row[0],
            "total_mt": round(row[1], 2) if row[1] else 0,
            "total_fob_usd": round(row[2], 2) if row[2] else 0,
            "avg_usd_per_mt": round(row[3], 2) if row[3] else 0,
            "unique_destinations": row[4],
            "unique_fruits": row[5]
        })

    # Sort by volume
    comparisons = [c for c in comparisons if 'error' not in c]
    comparisons.sort(key=lambda x: x['total_mt'], reverse=True)

    conn.close()

    return {
        "query": "Exporter comparison",
        "date_range_months": date_range_months,
        "exporters_compared": len(comparisons),
        "comparisons": comparisons
    }


@mcp.tool()
def compare_periods(
    period1_start: str,
    period1_end: str,
    period2_start: str,
    period2_end: str,
    fruit: Optional[str] = None
) -> Dict[str, Any]:
    """
    Compare export data between two time periods.

    Args:
        period1_start: Start date for period 1 (YYYY-MM-DD)
        period1_end: End date for period 1 (YYYY-MM-DD)
        period2_start: Start date for period 2 (YYYY-MM-DD)
        period2_end: End date for period 2 (YYYY-MM-DD)
        fruit: Optional fruit filter

    Returns:
        Comparison between two periods
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    def get_period_stats(start, end):
        if fruit:
            cursor.execute("""
                SELECT
                    COUNT(*) as shipment_count,
                    SUM(net_weight_mt) as total_mt,
                    SUM([U$ FOB Tot]) as total_fob,
                    AVG(usd_per_mt_fob) as avg_usd_per_mt
                FROM exports
                WHERE Date >= ? AND Date <= ?
                  AND fruit_name LIKE ?
                  AND net_weight_mt > 0
            """, (start, end, f"%{fruit}%"))
        else:
            cursor.execute("""
                SELECT
                    COUNT(*) as shipment_count,
                    SUM(net_weight_mt) as total_mt,
                    SUM([U$ FOB Tot]) as total_fob,
                    AVG(usd_per_mt_fob) as avg_usd_per_mt
                FROM exports
                WHERE Date >= ? AND Date <= ?
                  AND net_weight_mt > 0
            """, (start, end))

        row = cursor.fetchone()
        return {
            "shipment_count": row[0],
            "total_mt": round(row[1], 2) if row[1] else 0,
            "total_fob_usd": round(row[2], 2) if row[2] else 0,
            "avg_usd_per_mt": round(row[3], 2) if row[3] else 0
        }

    period1 = get_period_stats(period1_start, period1_end)
    period2 = get_period_stats(period2_start, period2_end)

    # Calculate changes
    mt_change = period2['total_mt'] - period1['total_mt']
    mt_change_pct = (mt_change / period1['total_mt'] * 100) if period1['total_mt'] > 0 else 0

    price_change = period2['avg_usd_per_mt'] - period1['avg_usd_per_mt']
    price_change_pct = (price_change / period1['avg_usd_per_mt'] * 100) if period1['avg_usd_per_mt'] > 0 else 0

    conn.close()

    return {
        "query": "Period comparison",
        "fruit_filter": fruit,
        "period1": {
            "dates": f"{period1_start} to {period1_end}",
            "stats": period1
        },
        "period2": {
            "dates": f"{period2_start} to {period2_end}",
            "stats": period2
        },
        "changes": {
            "volume_mt": round(mt_change, 2),
            "volume_pct": round(mt_change_pct, 1),
            "price_usd_per_mt": round(price_change, 2),
            "price_pct": round(price_change_pct, 1)
        }
    }


@mcp.tool()
def get_available_values(
    field: str
) -> Dict[str, Any]:
    """
    Get unique values for a specific field.

    Args:
        field: Field name - 'fruits', 'formats', 'sizes', 'exporters', 'destinations', 'certifications'

    Returns:
        List of unique values with counts
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    field_mapping = {
        'fruits': ('fruit_name', 'Fruit'),
        'formats': ('format_type', 'Format'),
        'sizes': ('size_mm', 'Size'),
        'exporters': ('Exporter', 'Exporter'),
        'destinations': ('[Destination Country]', 'Country'),
        'certifications': ('certification', 'Certification')
    }

    if field not in field_mapping:
        return {
            "error": f"Invalid field '{field}'",
            "valid_fields": list(field_mapping.keys())
        }

    db_field, display_name = field_mapping[field]

    cursor.execute(f"""
        SELECT
            {db_field} as value,
            COUNT(*) as count,
            SUM(net_weight_mt) as total_mt
        FROM exports
        WHERE {db_field} IS NOT NULL
          AND {db_field} != ''
          AND net_weight_mt > 0
        GROUP BY {db_field}
        ORDER BY total_mt DESC
    """)

    results = []
    for row in cursor.fetchall():
        results.append({
            display_name.lower(): row[0],
            "shipment_count": row[1],
            "total_mt": round(row[2], 2)
        })

    conn.close()

    return {
        "field": field,
        "unique_count": len(results),
        "values": results
    }


# ============================================================================
# PHASE 1: CORE INFRASTRUCTURE - NEW TOOLS
# ============================================================================

@mcp.tool()
def query_with_date_range(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    exporter: Optional[str] = None,
    fruit: Optional[str] = None,
    destination: Optional[str] = None,
    certification: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_volume_mt: Optional[float] = None,
    sort_by: str = "date",
    limit: int = 100
) -> Dict[str, Any]:
    """
    Query exports with flexible date ranges and advanced filtering.

    Args:
        start_date: Start date (ISO format or 'last_30_days', 'ytd', 'q1_2024', etc.)
        end_date: End date (ISO format or relative date)
        exporter: Filter by exporter name (fuzzy match supported)
        fruit: Filter by fruit type
        destination: Filter by destination country (English or Spanish)
        certification: Filter by 'organic', 'conventional', or 'unknown'
        min_price: Minimum USD/MT price
        max_price: Maximum USD/MT price
        min_volume_mt: Minimum volume in MT
        sort_by: Sort field: 'date', 'price', 'volume' (default 'date')
        limit: Maximum results (default 100)

    Returns:
        Filtered export records with summary statistics
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Build WHERE clauses
    where_clauses = ["net_weight_mt > 0"]
    params = []

    # Date range
    if start_date:
        parsed_start = parse_relative_date(start_date)
        if parsed_start:
            where_clauses.append("Date >= ?")
            params.append(parsed_start.strftime('%Y-%m-%d'))

    if end_date:
        parsed_end = parse_relative_date(end_date)
        if parsed_end:
            where_clauses.append("Date <= ?")
            params.append(parsed_end.strftime('%Y-%m-%d'))

    # Exporter (fuzzy match)
    if exporter:
        matching_exporters = fuzzy_match_exporter(exporter)
        if matching_exporters:
            placeholders = ','.join(['?'] * len(matching_exporters))
            where_clauses.append(f"Exporter IN ({placeholders})")
            params.extend(matching_exporters)

    # Fruit
    if fruit:
        where_clauses.append("fruit_name LIKE ?")
        params.append(f"%{fruit}%")

    # Destination (support English and Spanish)
    if destination:
        norm_country = normalize_country_name(destination)
        where_clauses.append("([Destination Country] LIKE ? OR destination_country_en LIKE ?)")
        params.extend([f"%{norm_country}%", f"%{destination}%"])

    # Certification
    if certification:
        where_clauses.append("certification = ?")
        params.append(certification.lower())

    # Price range
    if min_price is not None:
        where_clauses.append("usd_per_mt_fob >= ?")
        params.append(min_price)

    if max_price is not None:
        where_clauses.append("usd_per_mt_fob <= ?")
        params.append(max_price)

    # Volume minimum
    if min_volume_mt is not None:
        where_clauses.append("net_weight_mt >= ?")
        params.append(min_volume_mt)

    # Build query
    where_sql = " AND ".join(where_clauses)

    # Determine sort column
    sort_column = {
        'date': 'Date',
        'price': 'usd_per_mt_fob',
        'volume': 'net_weight_mt'
    }.get(sort_by, 'Date')

    query = f"""
        SELECT
            Date,
            Exporter,
            destination_country_en,
            fruit_name,
            format_type,
            size_mm,
            certification,
            net_weight_mt,
            usd_per_mt_fob,
            [U$ FOB Tot]
        FROM exports
        WHERE {where_sql}
        ORDER BY {sort_column} DESC
        LIMIT ?
    """

    params.append(limit)
    cursor.execute(query, params)

    records = []
    for row in cursor.fetchall():
        records.append({
            "date": row[0],
            "exporter": row[1],
            "destination": row[2],
            "fruit": row[3],
            "format": row[4],
            "size": row[5],
            "certification": row[6],
            "volume_mt": round(row[7], 2),
            "usd_per_mt": round(row[8], 2) if row[8] else None,
            "total_fob_usd": round(row[9], 2) if row[9] else None
        })

    # Summary statistics
    summary_query = f"""
        SELECT
            COUNT(*) as count,
            SUM(net_weight_mt) as total_mt,
            SUM([U$ FOB Tot]) as total_fob,
            AVG(usd_per_mt_fob) as avg_price,
            MIN(usd_per_mt_fob) as min_price,
            MAX(usd_per_mt_fob) as max_price
        FROM exports
        WHERE {where_sql}
    """

    cursor.execute(summary_query, params[:-1])  # Exclude limit param
    summary_row = cursor.fetchone()

    conn.close()

    return {
        "filters": {
            "start_date": start_date,
            "end_date": end_date,
            "exporter": exporter,
            "fruit": fruit,
            "destination": destination,
            "certification": certification,
            "price_range": f"{min_price or 'any'} - {max_price or 'any'} USD/MT"
        },
        "summary": {
            "total_records": summary_row[0],
            "total_volume_mt": round(summary_row[1], 2) if summary_row[1] else 0,
            "total_fob_usd": round(summary_row[2], 2) if summary_row[2] else 0,
            "avg_price_usd_per_mt": round(summary_row[3], 2) if summary_row[3] else 0,
            "price_range": {
                "min": round(summary_row[4], 2) if summary_row[4] else 0,
                "max": round(summary_row[5], 2) if summary_row[5] else 0
            }
        },
        "records_returned": len(records),
        "records": records
    }


@mcp.tool()
def export_data(
    format_type: str = "json",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    exporter: Optional[str] = None,
    fruit: Optional[str] = None,
    destination: Optional[str] = None,
    limit: int = 1000
) -> Dict[str, Any]:
    """
    Export filtered data in JSON or CSV-ready format.

    Args:
        format_type: 'json' or 'csv' (returns CSV-ready structure)
        start_date: Start date filter (ISO or relative like 'ytd')
        end_date: End date filter
        exporter: Filter by exporter
        fruit: Filter by fruit type
        destination: Filter by destination country
        limit: Maximum records (default 1000, max 5000)

    Returns:
        Exportable data with summary statistics
    """
    # Reuse query_with_date_range logic
    result = query_with_date_range(
        start_date=start_date,
        end_date=end_date,
        exporter=exporter,
        fruit=fruit,
        destination=destination,
        limit=min(limit, 5000)  # Cap at 5000 records
    )

    if format_type == "csv":
        # Return CSV-friendly structure
        csv_rows = []
        for record in result["records"]:
            csv_rows.append({
                "Date": record["date"],
                "Exporter": record["exporter"],
                "Destination": record["destination"],
                "Fruit": record["fruit"],
                "Format": record["format"],
                "Size": record["size"],
                "Certification": record["certification"],
                "Volume_MT": record["volume_mt"],
                "USD_per_MT": record["usd_per_mt"],
                "Total_FOB_USD": record["total_fob_usd"]
            })

        return {
            "format": "csv",
            "summary": result["summary"],
            "data": csv_rows,
            "note": "Convert 'data' array to CSV using standard CSV library"
        }

    return {
        "format": "json",
        "summary": result["summary"],
        "data": result["records"]
    }


@mcp.tool()
def get_dashboard_metrics(
    fruit: Optional[str] = None,
    exporter: Optional[str] = None,
    destination: Optional[str] = None,
    date_range: str = "ytd",
    compare_to_previous: bool = True
) -> Dict[str, Any]:
    """
    Get high-level KPI dashboard metrics with period comparisons.

    Args:
        fruit: Filter by fruit type
        exporter: Filter by exporter name
        destination: Filter by destination country
        date_range: 'last_30_days', 'mtd', 'qtd', 'ytd', 'last_90_days'
        compare_to_previous: Include comparison to previous period

    Returns:
        KPI summary with volume, value, prices, and trends
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Parse date range
    start_date = parse_relative_date(date_range)
    if not start_date:
        start_date = parse_relative_date("ytd")

    # Build filters
    where_clauses = ["net_weight_mt > 0", "Date >= ?"]
    params = [start_date.strftime('%Y-%m-%d')]

    if fruit:
        where_clauses.append("fruit_name LIKE ?")
        params.append(f"%{fruit}%")

    if exporter:
        matching_exporters = fuzzy_match_exporter(exporter)
        if matching_exporters:
            placeholders = ','.join(['?'] * len(matching_exporters))
            where_clauses.append(f"Exporter IN ({placeholders})")
            params.extend(matching_exporters)

    if destination:
        norm_country = normalize_country_name(destination)
        where_clauses.append("([Destination Country] LIKE ? OR destination_country_en LIKE ?)")
        params.extend([f"%{norm_country}%", f"%{destination}%"])

    where_sql = " AND ".join(where_clauses)

    # Current period metrics
    query = f"""
        SELECT
            COUNT(*) as shipment_count,
            SUM(net_weight_mt) as total_mt,
            SUM([U$ FOB Tot]) as total_fob,
            AVG(usd_per_mt_fob) as avg_price,
            COUNT(DISTINCT Exporter) as unique_exporters,
            COUNT(DISTINCT destination_country_en) as unique_destinations
        FROM exports
        WHERE {where_sql}
    """

    cursor.execute(query, params)
    current = cursor.fetchone()

    # Top 5 products
    top_products_query = f"""
        SELECT
            fruit_name,
            format_type,
            SUM(net_weight_mt) as total_mt
        FROM exports
        WHERE {where_sql}
        GROUP BY fruit_name, format_type
        ORDER BY total_mt DESC
        LIMIT 5
    """

    cursor.execute(top_products_query, params)
    top_products = [
        {"fruit": row[0], "format": row[1], "volume_mt": round(row[2], 2)}
        for row in cursor.fetchall()
    ]

    # Top 5 destinations
    top_destinations_query = f"""
        SELECT
            destination_country_en,
            SUM(net_weight_mt) as total_mt
        FROM exports
        WHERE {where_sql}
        GROUP BY destination_country_en
        ORDER BY total_mt DESC
        LIMIT 5
    """

    cursor.execute(top_destinations_query, params)
    top_destinations = [
        {"country": row[0], "volume_mt": round(row[1], 2)}
        for row in cursor.fetchall()
    ]

    result = {
        "period": date_range,
        "filters": {
            "fruit": fruit,
            "exporter": exporter,
            "destination": destination
        },
        "kpis": {
            "shipment_count": current[0],
            "total_volume_mt": round(current[1], 2) if current[1] else 0,
            "total_fob_usd": round(current[2], 2) if current[2] else 0,
            "avg_price_usd_per_mt": round(current[3], 2) if current[3] else 0,
            "unique_exporters": current[4],
            "unique_destinations": current[5]
        },
        "top_products": top_products,
        "top_destinations": top_destinations
    }

    # Previous period comparison (if requested)
    if compare_to_previous:
        # Calculate previous period dates
        period_days = (datetime.now() - start_date).days
        prev_start = start_date - timedelta(days=period_days)
        prev_end = start_date - timedelta(days=1)

        prev_where = where_clauses.copy()
        prev_where[prev_where.index("Date >= ?")] = "Date >= ? AND Date <= ?"
        prev_params = [prev_start.strftime('%Y-%m-%d'), prev_end.strftime('%Y-%m-%d')] + params[1:]

        prev_query = f"""
            SELECT
                COUNT(*) as shipment_count,
                SUM(net_weight_mt) as total_mt,
                SUM([U$ FOB Tot]) as total_fob,
                AVG(usd_per_mt_fob) as avg_price
            FROM exports
            WHERE {' AND '.join(prev_where)}
        """

        cursor.execute(prev_query, prev_params)
        previous = cursor.fetchone()

        result["comparison"] = {
            "previous_period": {
                "start": prev_start.strftime('%Y-%m-%d'),
                "end": prev_end.strftime('%Y-%m-%d'),
                "shipment_count": previous[0],
                "total_volume_mt": round(previous[1], 2) if previous[1] else 0,
                "total_fob_usd": round(previous[2], 2) if previous[2] else 0,
                "avg_price_usd_per_mt": round(previous[3], 2) if previous[3] else 0
            },
            "growth": {
                "shipment_count_pct": calculate_growth_rate(previous[0], current[0]),
                "volume_pct": calculate_growth_rate(previous[1] or 0, current[1] or 0),
                "fob_value_pct": calculate_growth_rate(previous[2] or 0, current[2] or 0),
                "avg_price_pct": calculate_growth_rate(previous[3] or 0, current[3] or 0)
            }
        }

    conn.close()
    return result


@mcp.tool()
def get_top_n(
    dimension: str,
    metric: str = "volume",
    n: int = 10,
    fruit: Optional[str] = None,
    destination: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get top-N rankings by exporters, fruits, or destinations.

    Args:
        dimension: 'exporters', 'fruits', or 'destinations'
        metric: 'volume' (MT), 'value' (FOB USD), or 'shipment_count'
        n: Number of top results (default 10)
        fruit: Filter by fruit type
        destination: Filter by destination country
        start_date: Start date filter (ISO or relative)
        end_date: End date filter

    Returns:
        Ranked list with percentages and cumulative share
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Build filters
    where_clauses = ["net_weight_mt > 0"]
    params = []

    if start_date:
        parsed = parse_relative_date(start_date)
        if parsed:
            where_clauses.append("Date >= ?")
            params.append(parsed.strftime('%Y-%m-%d'))

    if end_date:
        parsed = parse_relative_date(end_date)
        if parsed:
            where_clauses.append("Date <= ?")
            params.append(parsed.strftime('%Y-%m-%d'))

    if fruit:
        where_clauses.append("fruit_name LIKE ?")
        params.append(f"%{fruit}%")

    if destination:
        norm_country = normalize_country_name(destination)
        where_clauses.append("([Destination Country] LIKE ? OR destination_country_en LIKE ?)")
        params.extend([f"%{norm_country}%", f"%{destination}%"])

    where_sql = " AND ".join(where_clauses)

    # Determine grouping and metric columns
    group_by = {
        'exporters': 'Exporter',
        'fruits': 'fruit_name',
        'destinations': 'destination_country_en'
    }.get(dimension)

    metric_column = {
        'volume': 'SUM(net_weight_mt)',
        'value': 'SUM([U$ FOB Tot])',
        'shipment_count': 'COUNT(*)'
    }.get(metric, 'SUM(net_weight_mt)')

    if not group_by:
        return {"error": f"Invalid dimension: {dimension}. Use 'exporters', 'fruits', or 'destinations'"}

    # Get ranked results
    query = f"""
        SELECT
            {group_by} as name,
            {metric_column} as metric_value,
            COUNT(*) as shipment_count
        FROM exports
        WHERE {where_sql}
        GROUP BY {group_by}
        ORDER BY metric_value DESC
        LIMIT ?
    """

    params.append(n)
    cursor.execute(query, params)
    results = cursor.fetchall()

    # Get total for percentage calculation
    total_query = f"""
        SELECT {metric_column} as total
        FROM exports
        WHERE {where_sql}
    """

    cursor.execute(total_query, params[:-1])
    total = cursor.fetchone()[0] or 1  # Avoid division by zero

    # Format results with percentages
    ranked = []
    cumulative = 0
    for rank, row in enumerate(results, 1):
        value = row[1]
        percentage = (value / total) * 100
        cumulative += percentage

        ranked.append({
            "rank": rank,
            "name": row[0],
            "value": round(value, 2),
            "percentage": round(percentage, 2),
            "cumulative_percentage": round(cumulative, 2),
            "shipment_count": row[2]
        })

    conn.close()

    return {
        "dimension": dimension,
        "metric": metric,
        "top_n": n,
        "filters": {
            "fruit": fruit,
            "destination": destination,
            "date_range": f"{start_date or 'all'} to {end_date or 'all'}"
        },
        "total": round(total, 2),
        "results": ranked
    }


# ============================================================================
# PHASE 2: TIME-SERIES ANALYSIS - NEW TOOLS
# ============================================================================

@mcp.tool()
def get_time_series_analysis(
    metric: str,
    fruit: Optional[str] = None,
    exporter: Optional[str] = None,
    destination: Optional[str] = None,
    start_date: str = "last_365_days",
    granularity: str = "monthly",
    include_trends: bool = True
) -> Dict[str, Any]:
    """
    Analyze time-series trends with growth rates and moving averages.

    Args:
        metric: 'volume', 'price', 'shipment_count', or 'fob_value'
        fruit: Filter by fruit type
        exporter: Filter by exporter name
        destination: Filter by destination country
        start_date: Start date (ISO or relative like 'last_365_days')
        granularity: 'daily', 'weekly', or 'monthly' (default)
        include_trends: Calculate MoM, YoY, moving averages

    Returns:
        Time-series data with trend indicators
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Parse date
    parsed_start = parse_relative_date(start_date)
    if not parsed_start:
        parsed_start = parse_relative_date("last_365_days")

    # Build filters
    where_clauses = ["net_weight_mt > 0", "Date >= ?"]
    params = [parsed_start.strftime('%Y-%m-%d')]

    if fruit:
        where_clauses.append("fruit_name LIKE ?")
        params.append(f"%{fruit}%")

    if exporter:
        matching_exporters = fuzzy_match_exporter(exporter)
        if matching_exporters:
            placeholders = ','.join(['?'] * len(matching_exporters))
            where_clauses.append(f"Exporter IN ({placeholders})")
            params.extend(matching_exporters)

    if destination:
        norm_country = normalize_country_name(destination)
        where_clauses.append("([Destination Country] LIKE ? OR destination_country_en LIKE ?)")
        params.extend([f"%{norm_country}%", f"%{destination}%"])

    where_sql = " AND ".join(where_clauses)

    # Determine metric column and aggregation
    metric_map = {
        'volume': ('SUM(net_weight_mt)', 'volume_mt'),
        'price': ('AVG(usd_per_mt_fob)', 'avg_price_usd_per_mt'),
        'shipment_count': ('COUNT(*)', 'shipment_count'),
        'fob_value': ('SUM([U$ FOB Tot])', 'fob_value_usd')
    }

    if metric not in metric_map:
        return {"error": f"Invalid metric: {metric}. Use 'volume', 'price', 'shipment_count', or 'fob_value'"}

    metric_col, metric_name = metric_map[metric]

    # Determine time grouping
    if granularity == 'daily':
        time_group = "DATE(Date)"
    elif granularity == 'weekly':
        time_group = "strftime('%Y-W%W', Date)"
    else:  # monthly
        time_group = "strftime('%Y-%m', Date)"

    # Get time-series data
    query = f"""
        SELECT
            {time_group} as period,
            {metric_col} as value
        FROM exports
        WHERE {where_sql}
        GROUP BY {time_group}
        ORDER BY period
    """

    cursor.execute(query, params)
    results = cursor.fetchall()

    # Format results
    series = []
    for row in results:
        series.append({
            "period": row[0],
            "value": round(row[1], 2) if row[1] else 0
        })

    # Calculate trends if requested
    trends = {}
    if include_trends and len(series) > 1:
        # Month-over-month growth (last period)
        if len(series) >= 2:
            prev_value = series[-2]["value"]
            curr_value = series[-1]["value"]
            trends["mom_growth_pct"] = calculate_growth_rate(prev_value, curr_value)

        # Year-over-year growth (if enough data)
        periods_per_year = {'daily': 365, 'weekly': 52, 'monthly': 12}.get(granularity, 12)
        if len(series) > periods_per_year:
            yoy_prev = series[-(periods_per_year+1)]["value"]
            yoy_curr = series[-1]["value"]
            trends["yoy_growth_pct"] = calculate_growth_rate(yoy_prev, yoy_curr)

        # 3-period moving average
        if len(series) >= 3:
            recent_three = [s["value"] for s in series[-3:]]
            trends["moving_avg_3period"] = round(sum(recent_three) / 3, 2)

        # 6-period moving average
        if len(series) >= 6:
            recent_six = [s["value"] for s in series[-6:]]
            trends["moving_avg_6period"] = round(sum(recent_six) / 6, 2)

        # Trend direction
        if len(series) >= 6:
            first_half_avg = sum([s["value"] for s in series[:len(series)//2]]) / (len(series)//2)
            second_half_avg = sum([s["value"] for s in series[len(series)//2:]]) / (len(series) - len(series)//2)
            if second_half_avg > first_half_avg * 1.05:
                trends["trend_direction"] = "increasing"
            elif second_half_avg < first_half_avg * 0.95:
                trends["trend_direction"] = "decreasing"
            else:
                trends["trend_direction"] = "stable"

    conn.close()

    return {
        "metric": metric,
        "granularity": granularity,
        "filters": {
            "fruit": fruit,
            "exporter": exporter,
            "destination": destination,
            "start_date": start_date
        },
        "data_points": len(series),
        "time_series": series,
        "trends": trends if include_trends else None
    }


# ============================================================================
# PHASE 3: MARKET INTELLIGENCE - NEW TOOLS
# ============================================================================

@mcp.tool()
def get_market_share(
    dimension: str,
    metric: str = "volume",
    fruit: Optional[str] = None,
    destination: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    top_n: int = 10
) -> Dict[str, Any]:
    """
    Calculate market share with HHI concentration index.

    Args:
        dimension: 'exporter', 'fruit', or 'destination'
        metric: 'volume' (MT) or 'value' (FOB USD)
        fruit: Filter by fruit type
        destination: Filter by destination country
        start_date: Start date (ISO or relative)
        end_date: End date
        top_n: Number of top players to show (default 10)

    Returns:
        Market share analysis with HHI and concentration metrics
    """
    # Reuse get_top_n for rankings
    rankings = get_top_n(
        dimension=dimension + 's',  # exporters, fruits, destinations
        metric=metric,
        n=top_n,
        fruit=fruit,
        destination=destination,
        start_date=start_date,
        end_date=end_date
    )

    if "error" in rankings:
        return rankings

    # Calculate HHI from all entities (not just top_n)
    conn = get_db_connection()
    cursor = conn.cursor()

    # Build filters
    where_clauses = ["net_weight_mt > 0"]
    params = []

    if start_date:
        parsed = parse_relative_date(start_date)
        if parsed:
            where_clauses.append("Date >= ?")
            params.append(parsed.strftime('%Y-%m-%d'))

    if end_date:
        parsed = parse_relative_date(end_date)
        if parsed:
            where_clauses.append("Date <= ?")
            params.append(parsed.strftime('%Y-%m-%d'))

    if fruit:
        where_clauses.append("fruit_name LIKE ?")
        params.append(f"%{fruit}%")

    if destination:
        norm_country = normalize_country_name(destination)
        where_clauses.append("([Destination Country] LIKE ? OR destination_country_en LIKE ?)")
        params.extend([f"%{norm_country}%", f"%{destination}%"])

    where_sql = " AND ".join(where_clauses)

    group_by = {
        'exporter': 'Exporter',
        'fruit': 'fruit_name',
        'destination': 'destination_country_en'
    }.get(dimension)

    metric_col = 'SUM(net_weight_mt)' if metric == 'volume' else 'SUM([U$ FOB Tot])'

    # Get all shares for HHI
    query = f"""
        SELECT {metric_col} as value
        FROM exports
        WHERE {where_sql}
        GROUP BY {group_by}
    """

    cursor.execute(query, params)
    all_values = [row[0] for row in cursor.fetchall()]
    total = sum(all_values)

    if total > 0:
        shares = [v / total for v in all_values]
        hhi = calculate_hhi(shares)
    else:
        hhi = 0

    conn.close()

    # Market concentration interpretation
    if hhi < 1500:
        concentration = "unconcentrated"
    elif hhi < 2500:
        concentration = "moderately concentrated"
    else:
        concentration = "highly concentrated"

    # Top-3 and Top-5 cumulative share
    top_3_share = sum([r["percentage"] for r in rankings["results"][:3]]) if len(rankings["results"]) >= 3 else 0
    top_5_share = sum([r["percentage"] for r in rankings["results"][:5]]) if len(rankings["results"]) >= 5 else 0

    return {
        "dimension": dimension,
        "metric": metric,
        "filters": rankings["filters"],
        "market_concentration": {
            "hhi": round(hhi, 2),
            "interpretation": concentration,
            "top_3_share_pct": round(top_3_share, 2),
            "top_5_share_pct": round(top_5_share, 2)
        },
        "top_players": rankings["results"]
    }


@mcp.tool()
def analyze_exporter_portfolio(
    exporter_name: str,
    include_diversification: bool = True,
    include_market_position: bool = True
) -> Dict[str, Any]:
    """
    Analyze exporter's product portfolio and market positioning.

    Args:
        exporter_name: Exporter company name (fuzzy match supported)
        include_diversification: Calculate geographic/product diversification scores
        include_market_position: Include competitive positioning metrics

    Returns:
        Portfolio analysis with diversification and market position
    """
    # Find matching exporter
    matching_exporters = fuzzy_match_exporter(exporter_name)
    if not matching_exporters:
        return {"error": f"No exporters found matching '{exporter_name}'"}

    exporter = matching_exporters[0]

    conn = get_db_connection()
    cursor = conn.cursor()

    # Product mix
    cursor.execute("""
        SELECT
            fruit_name,
            format_type,
            certification,
            SUM(net_weight_mt) as total_mt,
            AVG(usd_per_mt_fob) as avg_price,
            COUNT(*) as shipment_count
        FROM exports
        WHERE Exporter = ? AND net_weight_mt > 0
        GROUP BY fruit_name, format_type, certification
        ORDER BY total_mt DESC
    """, (exporter,))

    product_mix = []
    for row in cursor.fetchall():
        product_mix.append({
            "fruit": row[0],
            "format": row[1],
            "certification": row[2],
            "volume_mt": round(row[3], 2),
            "avg_price": round(row[4], 2) if row[4] else 0,
            "shipment_count": row[5]
        })

    # Geographic distribution
    cursor.execute("""
        SELECT
            destination_country_en,
            SUM(net_weight_mt) as total_mt,
            COUNT(*) as shipment_count
        FROM exports
        WHERE Exporter = ? AND net_weight_mt > 0
        GROUP BY destination_country_en
        ORDER BY total_mt DESC
    """, (exporter,))

    geo_distribution = []
    for row in cursor.fetchall():
        geo_distribution.append({
            "country": row[0],
            "volume_mt": round(row[1], 2),
            "shipment_count": row[2]
        })

    result = {
        "exporter": exporter,
        "product_portfolio": {
            "unique_products": len(product_mix),
            "products": product_mix[:10]  # Top 10
        },
        "geographic_reach": {
            "countries_served": len(geo_distribution),
            "destinations": geo_distribution[:10]  # Top 10
        }
    }

    # Diversification metrics
    if include_diversification and len(product_mix) > 0:
        # Product diversification (HHI based on volume distribution)
        total_volume = sum([p["volume_mt"] for p in product_mix])
        product_shares = [p["volume_mt"] / total_volume for p in product_mix]
        product_hhi = calculate_hhi(product_shares)

        # Geographic diversification
        total_geo_volume = sum([g["volume_mt"] for g in geo_distribution])
        geo_shares = [g["volume_mt"] / total_geo_volume for g in geo_distribution]
        geo_hhi = calculate_hhi(geo_shares)

        result["diversification"] = {
            "product_concentration_hhi": round(product_hhi, 2),
            "product_diversity": "low" if product_hhi > 5000 else "medium" if product_hhi > 2500 else "high",
            "geographic_concentration_hhi": round(geo_hhi, 2),
            "geographic_diversity": "low" if geo_hhi > 5000 else "medium" if geo_hhi > 2500 else "high"
        }

    # Market positioning
    if include_market_position and len(product_mix) > 0:
        # Get total market volume for comparison
        cursor.execute("""
            SELECT SUM(net_weight_mt) as market_total
            FROM exports
            WHERE net_weight_mt > 0
        """)
        market_total = cursor.fetchone()[0]

        # Exporter's total volume
        cursor.execute("""
            SELECT
                SUM(net_weight_mt) as exporter_total,
                AVG(usd_per_mt_fob) as exporter_avg_price
            FROM exports
            WHERE Exporter = ? AND net_weight_mt > 0
        """, (exporter,))
        exporter_stats = cursor.fetchone()
        exporter_total = exporter_stats[0]
        exporter_avg_price = exporter_stats[1]

        # Market average price
        cursor.execute("""
            SELECT AVG(usd_per_mt_fob) as market_avg_price
            FROM exports
            WHERE net_weight_mt > 0
        """)
        market_avg_price = cursor.fetchone()[0]

        market_share_pct = (exporter_total / market_total * 100) if market_total > 0 else 0

        result["market_position"] = {
            "overall_market_share_pct": round(market_share_pct, 2),
            "avg_price_positioning": round((exporter_avg_price / market_avg_price - 1) * 100, 2) if market_avg_price > 0 else 0,
            "price_tier": "premium" if exporter_avg_price > market_avg_price * 1.1 else "economy" if exporter_avg_price < market_avg_price * 0.9 else "mid-market"
        }

    conn.close()
    return result


# ============================================================================
# PHASE 4: PRICE ANALYTICS - NEW TOOLS
# ============================================================================

@mcp.tool()
def analyze_price_dynamics(
    fruit: str,
    format_type: Optional[str] = None,
    size: Optional[str] = None,
    include_organic_premium: bool = True,
    include_regional_gaps: bool = True,
    start_date: str = "last_365_days"
) -> Dict[str, Any]:
    """
    Comprehensive price analysis with organic premium and regional comparisons.

    Args:
        fruit: Fruit type to analyze
        format_type: Optional format filter (chunks, cubes, etc.)
        size: Optional size filter (20x20, etc.)
        include_organic_premium: Compare organic vs conventional prices
        include_regional_gaps: Compare Europe vs Rest of World prices
        start_date: Analysis period (ISO or relative like 'last_365_days')

    Returns:
        Price statistics, premiums, volatility, and trends
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Parse date
    parsed_start = parse_relative_date(start_date)
    if not parsed_start:
        parsed_start = parse_relative_date("last_365_days")

    # Build base filters
    where_clauses = ["net_weight_mt > 0", "usd_per_mt_fob > 0", "Date >= ?", "fruit_name LIKE ?"]
    params = [parsed_start.strftime('%Y-%m-%d'), f"%{fruit}%"]

    if format_type:
        where_clauses.append("format_type LIKE ?")
        params.append(f"%{format_type}%")

    if size:
        where_clauses.append("size_mm = ?")
        params.append(size)

    where_sql = " AND ".join(where_clauses)

    # Overall price statistics
    query = f"""
        SELECT
            COUNT(*) as sample_size,
            AVG(usd_per_mt_fob) as avg_price,
            MIN(usd_per_mt_fob) as min_price,
            MAX(usd_per_mt_fob) as max_price,
            SUM(usd_per_mt_fob * net_weight_mt) / SUM(net_weight_mt) as weighted_avg_price
        FROM exports
        WHERE {where_sql}
    """

    cursor.execute(query, params)
    stats = cursor.fetchone()

    # Calculate standard deviation manually
    cursor.execute(f"""
        SELECT usd_per_mt_fob, net_weight_mt
        FROM exports
        WHERE {where_sql}
    """, params)

    prices = [(row[0], row[1]) for row in cursor.fetchall()]
    if prices:
        weighted_avg = stats[4]
        variance = sum([(p - weighted_avg) ** 2 * w for p, w in prices]) / sum([w for _, w in prices])
        std_dev = variance ** 0.5
        cv = (std_dev / weighted_avg) * 100 if weighted_avg > 0 else 0
    else:
        std_dev = 0
        cv = 0

    result = {
        "fruit": fruit,
        "format": format_type,
        "size": size,
        "period": start_date,
        "sample_size": stats[0],
        "price_statistics": {
            "avg_price_usd_per_mt": round(stats[1], 2) if stats[1] else 0,
            "weighted_avg_price": round(stats[4], 2) if stats[4] else 0,
            "min_price": round(stats[2], 2) if stats[2] else 0,
            "max_price": round(stats[3], 2) if stats[3] else 0,
            "price_range": round(stats[3] - stats[2], 2) if stats[3] and stats[2] else 0,
            "std_deviation": round(std_dev, 2),
            "coefficient_of_variation_pct": round(cv, 2)
        }
    }

    # Organic vs Conventional premium
    if include_organic_premium:
        # Organic prices
        organic_where = where_clauses + ["certification = 'organic'"]
        cursor.execute(f"""
            SELECT
                COUNT(*) as count,
                AVG(usd_per_mt_fob) as avg_price,
                SUM(net_weight_mt) as total_mt
            FROM exports
            WHERE {' AND '.join(organic_where)}
        """, params)
        organic = cursor.fetchone()

        # Conventional prices
        conv_where = where_clauses + ["certification = 'conventional'"]
        cursor.execute(f"""
            SELECT
                COUNT(*) as count,
                AVG(usd_per_mt_fob) as avg_price,
                SUM(net_weight_mt) as total_mt
            FROM exports
            WHERE {' AND '.join(conv_where)}
        """, params)
        conventional = cursor.fetchone()

        if organic[1] and conventional[1]:
            premium_pct = ((organic[1] / conventional[1]) - 1) * 100
            result["organic_analysis"] = {
                "organic_avg_price": round(organic[1], 2),
                "conventional_avg_price": round(conventional[1], 2),
                "organic_premium_pct": round(premium_pct, 2),
                "organic_volume_mt": round(organic[2], 2) if organic[2] else 0,
                "conventional_volume_mt": round(conventional[2], 2) if conventional[2] else 0,
                "organic_market_share_pct": round((organic[2] / (organic[2] + conventional[2])) * 100, 2) if organic[2] and conventional[2] else 0
            }

    # Regional price gaps
    if include_regional_gaps:
        # Europe prices
        europe_where = where_clauses + ["region = 'Europe'"]
        cursor.execute(f"""
            SELECT
                COUNT(*) as count,
                AVG(usd_per_mt_fob) as avg_price,
                SUM(net_weight_mt) as total_mt
            FROM exports
            WHERE {' AND '.join(europe_where)}
        """, params)
        europe = cursor.fetchone()

        # Rest of World prices
        row_where = where_clauses + ["region = 'Rest of World'"]
        cursor.execute(f"""
            SELECT
                COUNT(*) as count,
                AVG(usd_per_mt_fob) as avg_price,
                SUM(net_weight_mt) as total_mt
            FROM exports
            WHERE {' AND '.join(row_where)}
        """, params)
        rest_of_world = cursor.fetchone()

        if europe[1] and rest_of_world[1]:
            price_gap_pct = ((europe[1] / rest_of_world[1]) - 1) * 100
            result["regional_analysis"] = {
                "europe_avg_price": round(europe[1], 2),
                "rest_of_world_avg_price": round(rest_of_world[1], 2),
                "europe_premium_pct": round(price_gap_pct, 2),
                "europe_volume_mt": round(europe[2], 2) if europe[2] else 0,
                "rest_of_world_volume_mt": round(rest_of_world[2], 2) if rest_of_world[2] else 0
            }

    conn.close()
    return result


if __name__ == "__main__":
    mcp.run()
