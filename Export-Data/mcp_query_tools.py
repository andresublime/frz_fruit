"""
Query tools for Frozen Fruit Export MCP Server.
Basic querying and filtering functionality.
Supports: Peru, Ecuador
"""
from typing import Optional, Dict, Any, List
from mcp_helpers import (
    get_db_connection,
    fuzzy_match_exporter,
    parse_relative_date
)
from translations import normalize_country_name
import fastmcp

mcp = fastmcp.FastMCP("Frozen Fruit Exports - Query Tools")


@mcp.tool()
def query_by_exporter(
    exporter_name: str,
    source_country: Optional[str] = None,
    destination_region: Optional[str] = None,
    destination_country: Optional[str] = None,
    fruit: Optional[str] = None,
    limit: int = 100
) -> Dict[str, Any]:
    """
    Query exports by company name with fuzzy matching.

    Args:
        exporter_name: Company name (supports partial/fuzzy matching)
        source_country: Filter by source country ('peru' or 'ecuador')
        destination_region: Filter by 'Europe' or 'Rest of World'
        destination_country: Specific destination country
        fruit: Filter by fruit type
        limit: Maximum results to return (default 100)

    Returns:
        Export records with specs and prices
    """
    # Find matching exporters
    matching_exporters = fuzzy_match_exporter(exporter_name, source_country=source_country)

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
            source_country,
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

    if source_country:
        query += " AND source_country = ?"
        params.append(source_country.lower())

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
            "source_country": row[0],
            "exporter": row[1],
            "fruit": row[2],
            "variety": row[3],
            "format": row[4],
            "size": row[5],
            "certification": row[6],
            "destination": row[7],
            "region": row[8],
            "date": row[9],
            "mt": round(row[10], 2),
            "usd_per_mt": round(row[11], 2),
            "total_fob_usd": round(row[12], 2)
        })
        total_mt += row[10]
        total_fob += row[12]

    conn.close()

    return {
        "query": f"Exports by {exporter_name}",
        "matched_exporters": matching_exporters,
        "filters_applied": {
            "source_country": source_country,
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
    source_country: Optional[str] = None,
    fruit: Optional[str] = None,
    certification: Optional[str] = None,
    limit: int = 100
) -> Dict[str, Any]:
    """
    Query exports to a specific destination country.

    Supports both English and Spanish country names (e.g., "Poland" or "POLONIA").

    Args:
        country: Destination country name in English (e.g., "Poland", "Germany", "United States")
        source_country: Filter by source country ('peru' or 'ecuador')
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
            source_country,
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

    if source_country:
        query += " AND source_country = ?"
        params.append(source_country.lower())

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
            "source_country": row[0],
            "fruit": row[1],
            "format": row[2],
            "size": row[3],
            "certification": row[4],
            "exporter": row[5],
            "date": row[6],
            "mt": round(row[7], 2),
            "usd_per_mt": round(row[8], 2),
            "total_fob_usd": round(row[9], 2),
            "destination": row[10]  # English country name
        })
        total_mt += row[7]
        total_fob += row[9]

    conn.close()

    return {
        "query": f"Exports to {country}",
        "filters_applied": {
            "source_country": source_country,
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
    source_country: Optional[str] = None,
    format_type: Optional[str] = None,
    size: Optional[str] = None,
    certification: Optional[str] = None,
    limit: int = 100
) -> Dict[str, Any]:
    """
    Query exports by product specifications.

    Args:
        fruit: Fruit name (required)
        source_country: Filter by source country ('peru' or 'ecuador')
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
            source_country,
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

    if source_country:
        query += " AND source_country = ?"
        params.append(source_country.lower())

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
            "source_country": row[0],
            "exporter": row[1],
            "destination": row[2],
            "region": row[3],
            "fruit": row[4],
            "variety": row[5],
            "format": row[6],
            "size": row[7],
            "certification": row[8],
            "date": row[9],
            "mt": round(row[10], 2),
            "usd_per_mt": round(row[11], 2),
            "total_fob_usd": round(row[12], 2)
        })
        total_mt += row[10]
        total_fob += row[12]

    conn.close()

    return {
        "query": f"Exports of {fruit}",
        "filters_applied": {
            "source_country": source_country,
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
def query_with_date_range(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    source_country: Optional[str] = None,
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
        source_country: Filter by source country ('peru' or 'ecuador')
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

    # Source country
    if source_country:
        where_clauses.append("source_country = ?")
        params.append(source_country.lower())

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
            source_country,
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
            "source_country": row[0],
            "date": row[1],
            "exporter": row[2],
            "destination": row[3],
            "fruit": row[4],
            "format": row[5],
            "size": row[6],
            "certification": row[7],
            "volume_mt": round(row[8], 2),
            "usd_per_mt": round(row[9], 2) if row[9] else None,
            "total_fob_usd": round(row[10], 2) if row[10] else None
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
            "source_country": source_country,
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
def get_available_values(
    field: str,
    source_country: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get unique values for a specific field.

    Args:
        field: Field name - 'fruits', 'formats', 'sizes', 'exporters', 'destinations', 'certifications', 'source_countries'
        source_country: Filter by source country ('peru' or 'ecuador')

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
        'certifications': ('certification', 'Certification'),
        'source_countries': ('source_country', 'Source Country')
    }

    if field not in field_mapping:
        return {
            "error": f"Invalid field '{field}'",
            "valid_fields": list(field_mapping.keys())
        }

    db_field, display_name = field_mapping[field]

    where_clauses = [
        f"{db_field} IS NOT NULL",
        f"{db_field} != ''",
        "net_weight_mt > 0"
    ]
    params = []

    if source_country:
        where_clauses.append("source_country = ?")
        params.append(source_country.lower())

    where_sql = " AND ".join(where_clauses)

    cursor.execute(f"""
        SELECT
            {db_field} as value,
            COUNT(*) as count,
            SUM(net_weight_mt) as total_mt
        FROM exports
        WHERE {where_sql}
        GROUP BY {db_field}
        ORDER BY total_mt DESC
    """, params)

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
        "source_country_filter": source_country,
        "unique_count": len(results),
        "values": results
    }


@mcp.tool()
def compare_countries(
    fruit: Optional[str] = None,
    format_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Compare export statistics between Peru and Ecuador.

    Args:
        fruit: Filter by fruit type (optional)
        format_type: Filter by format (optional)
        start_date: Start date (ISO format or relative)
        end_date: End date (ISO format or relative)

    Returns:
        Side-by-side comparison of Peru vs Ecuador exports
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    where_clauses = ["net_weight_mt > 0"]
    params = []

    if fruit:
        where_clauses.append("fruit_name LIKE ?")
        params.append(f"%{fruit}%")

    if format_type:
        where_clauses.append("format_type LIKE ?")
        params.append(f"%{format_type}%")

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

    where_sql = " AND ".join(where_clauses)

    cursor.execute(f"""
        SELECT
            source_country,
            COUNT(*) as shipment_count,
            SUM(net_weight_mt) as total_mt,
            SUM([U$ FOB Tot]) as total_fob,
            AVG(usd_per_mt_fob) as avg_price,
            COUNT(DISTINCT Exporter) as unique_exporters,
            COUNT(DISTINCT [Destination Country]) as unique_destinations
        FROM exports
        WHERE {where_sql}
        GROUP BY source_country
    """, params)

    results = {}
    for row in cursor.fetchall():
        country = row[0] if row[0] else 'unknown'
        results[country] = {
            "shipment_count": row[1],
            "total_mt": round(row[2], 2) if row[2] else 0,
            "total_fob_usd": round(row[3], 2) if row[3] else 0,
            "avg_price_usd_per_mt": round(row[4], 2) if row[4] else 0,
            "unique_exporters": row[5],
            "unique_destinations": row[6]
        }

    conn.close()

    return {
        "filters": {
            "fruit": fruit,
            "format_type": format_type,
            "start_date": start_date,
            "end_date": end_date
        },
        "comparison": results
    }
