"""
Peru Frozen Fruit Exports - MCP Server V2
Modular architecture with caching and enhanced analytics.

This is the main entry point that combines all modules.

CRITICAL INSTRUCTIONS FOR LLM:
- ONLY use data explicitly returned by these tools
- DO NOT infer, extrapolate, or create hypothetical data
- DO NOT make recommendations beyond what the data directly shows
- DO NOT generate business plans, strategies, or projections
- If data is missing, state "Data not available" - do NOT fill gaps
- Stick to descriptive statistics and direct observations from query results
"""
import fastmcp
from typing import Optional, List, Dict, Any

# Import helper functions
from mcp_helpers import (
    get_db_connection,
    parse_relative_date,
    calculate_hhi,
    calculate_growth_rate,
    fuzzy_match_exporter
)

# Import cache
from mcp_cache import get_cache

# Import translations
from translations import normalize_country_name

# Initialize MCP server
mcp = fastmcp.FastMCP("Peru Frozen Fruit Exports V2")

# Get cache instance
cache = get_cache()


# ============================================================================
# QUERY TOOLS (imported logic from mcp_query_tools.py)
# ============================================================================

@mcp.tool()
def query_by_exporter(
    exporter_name: str,
    destination_region: Optional[str] = None,
    destination_country: Optional[str] = None,
    fruit: Optional[str] = None,
    limit: int = 100
) -> Dict[str, Any]:
    """Query exports by company name with fuzzy matching."""
    matching_exporters = fuzzy_match_exporter(exporter_name)

    if not matching_exporters:
        return {
            "error": f"No exporters found matching '{exporter_name}'",
            "suggestion": "Try a different spelling or partial name"
        }

    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT Exporter, fruit_name, variety, format_type, size_mm, certification,
               [Destination Country], region, Date, net_weight_mt, usd_per_mt_fob, [U$ FOB Tot]
        FROM exports
        WHERE Exporter IN ({}) AND net_weight_mt > 0 AND usd_per_mt_fob > 0
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
            "exporter": row[0], "fruit": row[1], "variety": row[2], "format": row[3],
            "size": row[4], "certification": row[5], "destination": row[6], "region": row[7],
            "date": row[8], "mt": round(row[9], 2), "usd_per_mt": round(row[10], 2),
            "total_fob_usd": round(row[11], 2)
        })
        total_mt += row[9]
        total_fob += row[11]

    conn.close()

    return {
        "query": f"Exports by {exporter_name}",
        "matched_exporters": matching_exporters,
        "filters_applied": {"destination_region": destination_region, "destination_country": destination_country, "fruit": fruit},
        "result_count": len(results),
        "total_mt": round(total_mt, 2),
        "total_fob_usd": round(total_fob, 2),
        "avg_usd_per_mt": round(total_fob / total_mt, 2) if total_mt > 0 else 0,
        "results": results
    }


@mcp.tool()
def query_by_destination(country: str, fruit: Optional[str] = None, certification: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
    """Query exports to a specific destination country."""
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT fruit_name, format_type, size_mm, certification, Exporter, Date,
               net_weight_mt, usd_per_mt_fob, [U$ FOB Tot], destination_country_en
        FROM exports
        WHERE destination_country_en LIKE ? AND net_weight_mt > 0 AND usd_per_mt_fob > 0
    """
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
            "fruit": row[0], "format": row[1], "size": row[2], "certification": row[3],
            "exporter": row[4], "date": row[5], "mt": round(row[6], 2),
            "usd_per_mt": round(row[7], 2), "total_fob_usd": round(row[8], 2), "destination": row[9]
        })
        total_mt += row[6]
        total_fob += row[8]

    conn.close()

    return {
        "query": f"Exports to {country}",
        "filters_applied": {"fruit": fruit, "certification": certification},
        "result_count": len(results),
        "total_mt": round(total_mt, 2),
        "total_fob_usd": round(total_fob, 2),
        "avg_usd_per_mt": round(total_fob / total_mt, 2) if total_mt > 0 else 0,
        "results": results
    }


@mcp.tool()
def query_by_product(fruit: str, format_type: Optional[str] = None, size: Optional[str] = None, certification: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
    """Query exports by product specifications."""
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT Exporter, [Destination Country], region, fruit_name, variety, format_type, size_mm, certification,
               Date, net_weight_mt, usd_per_mt_fob, [U$ FOB Tot]
        FROM exports
        WHERE fruit_name LIKE ? AND net_weight_mt > 0 AND usd_per_mt_fob > 0
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
            "exporter": row[0], "destination": row[1], "region": row[2], "fruit": row[3],
            "variety": row[4], "format": row[5], "size": row[6], "certification": row[7],
            "date": row[8], "mt": round(row[9], 2), "usd_per_mt": round(row[10], 2),
            "total_fob_usd": round(row[11], 2)
        })
        total_mt += row[9]
        total_fob += row[11]

    conn.close()

    return {
        "query": f"Exports of {fruit}",
        "filters_applied": {"format_type": format_type, "size": size, "certification": certification},
        "result_count": len(results),
        "total_mt": round(total_mt, 2),
        "total_fob_usd": round(total_fob, 2),
        "avg_usd_per_mt": round(total_fob / total_mt, 2) if total_mt > 0 else 0,
        "results": results
    }


@mcp.tool()
def search_exporters(search_term: str, limit: int = 20) -> Dict[str, Any]:
    """Fuzzy search for exporter names."""
    matching_exporters = fuzzy_match_exporter(search_term, threshold=0.4)

    if not matching_exporters:
        return {"query": search_term, "matches": [], "message": "No matching exporters found"}

    conn = get_db_connection()
    cursor = conn.cursor()

    placeholders = ','.join('?' * len(matching_exporters))
    cursor.execute(f"""
        SELECT Exporter, COUNT(*) as shipment_count, SUM(net_weight_mt) as total_mt, SUM([U$ FOB Tot]) as total_fob
        FROM exports
        WHERE Exporter IN ({placeholders})
        GROUP BY Exporter
        ORDER BY total_mt DESC
        LIMIT {limit}
    """, matching_exporters)

    results = []
    for row in cursor.fetchall():
        results.append({"exporter": row[0], "shipment_count": row[1], "total_mt": round(row[2], 2), "total_fob_usd": round(row[3], 2)})

    conn.close()

    return {"query": search_term, "match_count": len(results), "matches": results}


@mcp.tool()
def get_available_values(field: str) -> Dict[str, Any]:
    """Get unique values for a specific field."""
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
        return {"error": f"Invalid field '{field}'", "valid_fields": list(field_mapping.keys())}

    db_field, display_name = field_mapping[field]

    cursor.execute(f"""
        SELECT {db_field} as value, COUNT(*) as count, SUM(net_weight_mt) as total_mt
        FROM exports
        WHERE {db_field} IS NOT NULL AND {db_field} != '' AND net_weight_mt > 0
        GROUP BY {db_field}
        ORDER BY total_mt DESC
    """)

    results = []
    for row in cursor.fetchall():
        results.append({display_name.lower(): row[0], "shipment_count": row[1], "total_mt": round(row[2], 2)})

    conn.close()

    return {"field": field, "unique_count": len(results), "values": results}


# ============================================================================
# DASHBOARD WITH CACHING
# ============================================================================

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
    **CACHED for 1 hour for performance.**

    Args:
        fruit: Filter by fruit type
        exporter: Filter by exporter name
        destination: Filter by destination country
        date_range: 'last_30_days', 'mtd', 'qtd', 'ytd', 'last_90_days'
        compare_to_previous: Include comparison to previous period

    Returns:
        KPI summary with volume, value, prices, and trends
    """
    # Generate cache key
    cache_key = cache._generate_key(
        'dashboard',
        fruit=fruit,
        exporter=exporter,
        destination=destination,
        date_range=date_range,
        compare_to_previous=compare_to_previous
    )

    # Try cache first (TTL: 1 hour)
    cached_result = cache.get(cache_key, ttl_seconds=3600)
    if cached_result is not None:
        cached_result['_from_cache'] = True
        return cached_result

    # Cache miss - compute metrics
    from datetime import datetime, timedelta

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
        SELECT COUNT(*) as shipment_count, SUM(net_weight_mt) as total_mt, SUM([U$ FOB Tot]) as total_fob,
               AVG(usd_per_mt_fob) as avg_price, COUNT(DISTINCT Exporter) as unique_exporters,
               COUNT(DISTINCT destination_country_en) as unique_destinations
        FROM exports
        WHERE {where_sql}
    """

    cursor.execute(query, params)
    current = cursor.fetchone()

    # Top 5 products
    top_products_query = f"""
        SELECT fruit_name, format_type, SUM(net_weight_mt) as total_mt
        FROM exports
        WHERE {where_sql}
        GROUP BY fruit_name, format_type
        ORDER BY total_mt DESC
        LIMIT 5
    """

    cursor.execute(top_products_query, params)
    top_products = [{"fruit": row[0], "format": row[1], "volume_mt": round(row[2], 2)} for row in cursor.fetchall()]

    # Top 5 destinations
    top_destinations_query = f"""
        SELECT destination_country_en, SUM(net_weight_mt) as total_mt
        FROM exports
        WHERE {where_sql}
        GROUP BY destination_country_en
        ORDER BY total_mt DESC
        LIMIT 5
    """

    cursor.execute(top_destinations_query, params)
    top_destinations = [{"country": row[0], "volume_mt": round(row[1], 2)} for row in cursor.fetchall()]

    result = {
        "period": date_range,
        "filters": {"fruit": fruit, "exporter": exporter, "destination": destination},
        "kpis": {
            "shipment_count": current[0],
            "total_volume_mt": round(current[1], 2) if current[1] else 0,
            "total_fob_usd": round(current[2], 2) if current[2] else 0,
            "avg_price_usd_per_mt": round(current[3], 2) if current[3] else 0,
            "unique_exporters": current[4],
            "unique_destinations": current[5]
        },
        "top_products": top_products,
        "top_destinations": top_destinations,
        "_from_cache": False
    }

    # Previous period comparison
    if compare_to_previous:
        period_days = (datetime.now() - start_date).days
        prev_start = start_date - timedelta(days=period_days)
        prev_end = start_date - timedelta(days=1)

        prev_where = where_clauses.copy()
        prev_where[prev_where.index("Date >= ?")] = "Date >= ? AND Date <= ?"
        prev_params = [prev_start.strftime('%Y-%m-%d'), prev_end.strftime('%Y-%m-%d')] + params[1:]

        prev_query = f"""
            SELECT COUNT(*) as shipment_count, SUM(net_weight_mt) as total_mt,
                   SUM([U$ FOB Tot]) as total_fob, AVG(usd_per_mt_fob) as avg_price
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

    # Cache the result
    cache.set(cache_key, result)

    return result


# ============================================================================
# CACHE MANAGEMENT TOOL
# ============================================================================

@mcp.tool()
def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache statistics and performance metrics.

    Returns:
        Cache hit rate, size, and other statistics
    """
    return cache.stats()


@mcp.tool()
def clear_cache(pattern: Optional[str] = None) -> Dict[str, Any]:
    """
    Clear cache entries.

    Args:
        pattern: Optional pattern to match (e.g., 'dashboard:*')
                 If None, clears entire cache

    Returns:
        Number of entries cleared
    """
    count = cache.invalidate(pattern)
    return {
        "cleared_entries": count,
        "pattern": pattern or "all",
        "message": f"Cleared {count} cache entries"
    }


if __name__ == "__main__":
    mcp.run()
