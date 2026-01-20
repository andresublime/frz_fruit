"""
Europe Competitive Benchmarking Tools.
Benchmark exporters against competitors in European markets.
Always separates data by source country (Peru vs Ecuador).
"""
from typing import Dict, Any, Optional
from mcp_helpers import (
    get_db_connection,
    fuzzy_match_exporter,
    parse_relative_date
)
import fastmcp

mcp = fastmcp.FastMCP("Frozen Fruit Exports - Europe Benchmark")


def _benchmark_europe_competitors_impl(
    exporter_name: str,
    source_country: Optional[str] = None,
    fruit: Optional[str] = None,
    certification: Optional[str] = None,
    start_date: str = "ytd"
) -> Dict[str, Any]:
    """Implementation of competitive benchmarking."""
    # Find matching exporter
    matching_exporters = fuzzy_match_exporter(exporter_name, source_country=source_country)
    if not matching_exporters:
        return {"error": f"No exporters found matching '{exporter_name}'"}

    exporter = matching_exporters[0]

    conn = get_db_connection()
    cursor = conn.cursor()

    # Parse date
    parsed_start = parse_relative_date(start_date)
    if not parsed_start:
        parsed_start = parse_relative_date("ytd")

    date_filter = parsed_start.strftime('%Y-%m-%d')

    # Build filters
    where_clauses = ["region = 'Europe'", "net_weight_mt > 0", "Date >= ?"]
    params = [date_filter]

    if fruit:
        where_clauses.append("fruit_name LIKE ?")
        params.append(f"%{fruit}%")

    if certification:
        where_clauses.append("certification = ?")
        params.append(certification)

    where_sql = " AND ".join(where_clauses)

    # Get target exporter's source country
    cursor.execute("""
        SELECT DISTINCT source_country FROM exports WHERE Exporter = ?
    """, [exporter])
    exporter_countries = [row[0] for row in cursor.fetchall()]

    # 1. Get target exporter's Europe metrics BY SOURCE COUNTRY
    cursor.execute(f"""
        SELECT
            source_country,
            SUM(net_weight_mt) as volume_mt,
            AVG(usd_per_mt_fob) as avg_price,
            COUNT(*) as shipments,
            COUNT(DISTINCT destination_country_en) as countries,
            COUNT(DISTINCT fruit_name) as fruits
        FROM exports
        WHERE Exporter = ? AND {where_sql}
        GROUP BY source_country
    """, [exporter] + params)
    target_by_country = {row[0]: {
        "volume_mt": row[1],
        "avg_price_usd_per_mt_fob": row[2],
        "shipments": row[3],
        "countries_served": row[4],
        "unique_fruits": row[5]
    } for row in cursor.fetchall()}

    # 2. Get market total for share calculation BY SOURCE COUNTRY
    cursor.execute(f"""
        SELECT source_country, SUM(net_weight_mt) as market_total
        FROM exports
        WHERE {where_sql}
        GROUP BY source_country
    """, params)
    market_totals = {row[0]: row[1] for row in cursor.fetchall()}

    # 3. Get top 10 competitors in Europe BY SOURCE COUNTRY
    cursor.execute(f"""
        SELECT
            source_country,
            Exporter,
            SUM(net_weight_mt) as volume_mt,
            AVG(usd_per_mt_fob) as avg_price,
            COUNT(*) as shipments,
            COUNT(DISTINCT destination_country_en) as countries
        FROM exports
        WHERE {where_sql}
        GROUP BY source_country, Exporter
        ORDER BY source_country, volume_mt DESC
    """, params)

    competitors_by_country = {}
    for row in cursor.fetchall():
        src_country = row[0]
        if src_country not in competitors_by_country:
            competitors_by_country[src_country] = []
        if len(competitors_by_country[src_country]) < 10:
            competitors_by_country[src_country].append({
                "exporter": row[1],
                "volume_mt": row[2],
                "avg_price_usd_per_mt_fob": row[3],
                "shipments": row[4],
                "countries": row[5]
            })

    conn.close()

    # Format results by source country
    results_by_country = {}
    for src_country in set(list(market_totals.keys()) + list(target_by_country.keys())):
        market_total = market_totals.get(src_country, 0)
        target_metrics = target_by_country.get(src_country, {})
        target_volume = target_metrics.get("volume_mt", 0)
        market_share_pct = (target_volume / market_total * 100) if market_total > 0 else 0

        # Find target's rank in this country
        competitors = competitors_by_country.get(src_country, [])
        target_rank = next((i + 1 for i, c in enumerate(competitors) if c["exporter"] == exporter), None)

        # Format competitors with rank and share
        competitor_list = []
        for i, comp in enumerate(competitors, 1):
            comp_volume = comp["volume_mt"]
            comp_share = (comp_volume / market_total * 100) if market_total > 0 else 0
            competitor_list.append({
                "rank": i,
                "exporter": comp["exporter"],
                "is_target": comp["exporter"] == exporter,
                "volume_mt": round(comp_volume, 2),
                "market_share_pct": round(comp_share, 2),
                "avg_price_usd_per_mt_fob": round(comp["avg_price_usd_per_mt_fob"], 2) if comp["avg_price_usd_per_mt_fob"] else 0,
                "shipments": comp["shipments"],
                "countries_served": comp["countries"]
            })

        results_by_country[src_country] = {
            "target_metrics": {
                "rank": target_rank,
                "market_share_pct": round(market_share_pct, 2),
                "volume_mt": round(target_volume, 2) if target_volume else 0,
                "avg_price_usd_per_mt_fob": round(target_metrics.get("avg_price_usd_per_mt_fob", 0), 2) if target_metrics.get("avg_price_usd_per_mt_fob") else 0,
                "shipments": target_metrics.get("shipments", 0),
                "countries_served": target_metrics.get("countries_served", 0),
                "unique_fruits": target_metrics.get("unique_fruits", 0)
            },
            "market_context": {
                "total_market_size_mt": round(market_total, 2),
                "total_exporters": len(competitors)
            },
            "top_10_competitors": competitor_list,
            "competitive_position": {
                "rank_category": "leader" if target_rank and target_rank <= 3 else "challenger" if target_rank and target_rank <= 10 else "follower",
                "share_category": "dominant" if market_share_pct > 20 else "strong" if market_share_pct > 10 else "moderate" if market_share_pct > 5 else "niche"
            }
        }

    return {
        "target_exporter": exporter,
        "exporter_source_countries": exporter_countries,
        "analysis_period": start_date,
        "market_scope": "Europe",
        "filters": {
            "fruit": fruit or "all",
            "certification": certification or "all"
        },
        "results_by_source_country": results_by_country
    }


@mcp.tool()
def benchmark_europe_competitors(
    exporter_name: str,
    source_country: Optional[str] = None,
    fruit: Optional[str] = None,
    certification: Optional[str] = None,
    start_date: str = "ytd"
) -> Dict[str, Any]:
    """
    Benchmark exporter against competitors in European markets.

    Analyzes:
    - Market share in Europe
    - Pricing strategy vs competitors (USD/MT FOB)
    - Product overlap and differentiation
    - Geographic coverage comparison
    - Certification mix

    IMPORTANT: Results are always separated by source country (Peru vs Ecuador).
    Prices from Peru and Ecuador are shown separately to enable differential analysis.

    Args:
        exporter_name: Company to benchmark (fuzzy match)
        source_country: Filter by source country ('peru' or 'ecuador')
        fruit: Optional fruit filter
        certification: Optional certification filter ('organic', 'conventional')
        start_date: Analysis period (default 'ytd')

    Returns:
        Competitive benchmark analysis for Europe, separated by source country
    """
    return _benchmark_europe_competitors_impl(
        exporter_name, source_country, fruit, certification, start_date
    )


# Export implementation for use by main module
benchmark_europe_competitors_impl = _benchmark_europe_competitors_impl


if __name__ == "__main__":
    mcp.run()
