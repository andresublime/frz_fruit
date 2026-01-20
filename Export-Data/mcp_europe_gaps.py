"""
Europe Market Gap Identification Tools.
Identify underserved product-country combinations with opportunity potential.
"""
from typing import Dict, Any, Optional
from mcp_helpers import (
    get_db_connection,
    parse_relative_date
)
import fastmcp

mcp = fastmcp.FastMCP("Frozen Fruit Exports - Europe Gaps")


def _identify_market_gaps_impl(
    target_country: Optional[str] = None,
    product_category: Optional[str] = None,
    source_country: Optional[str] = None,
    min_market_size_mt: float = 100.0,
    max_suppliers: int = 5,
    start_date: str = "ytd"
) -> Dict[str, Any]:
    """Implementation of market gap identification."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Parse date
    parsed_start = parse_relative_date(start_date)
    if not parsed_start:
        parsed_start = parse_relative_date("ytd")

    date_filter = parsed_start.strftime('%Y-%m-%d')

    # Build query
    where_clauses = ["net_weight_mt > 0", "Date >= ?"]
    params = [date_filter]

    if target_country:
        where_clauses.append("destination_country_en LIKE ?")
        params.append(f"%{target_country}%")

    if product_category:
        where_clauses.append("fruit_name LIKE ?")
        params.append(f"%{product_category}%")

    if source_country:
        where_clauses.append("source_country = ?")
        params.append(source_country.lower())

    where_sql = " AND ".join(where_clauses)

    # Find product-country combinations with market metrics
    # IMPORTANT: Always include source_country in grouping to keep Peru/Ecuador separate
    query = f"""
        SELECT
            source_country,
            fruit_name,
            format_type,
            certification,
            destination_country_en,
            region,
            COUNT(DISTINCT Exporter) as supplier_count,
            COUNT(*) as shipment_count,
            SUM(net_weight_mt) as total_volume_mt,
            AVG(usd_per_mt_fob) as avg_price,
            MIN(usd_per_mt_fob) as min_price,
            MAX(usd_per_mt_fob) as max_price
        FROM exports
        WHERE {where_sql}
        GROUP BY source_country, fruit_name, format_type, certification, destination_country_en, region
        HAVING total_volume_mt >= ? AND supplier_count <= ?
        ORDER BY total_volume_mt DESC
        LIMIT 50
    """

    params.extend([min_market_size_mt, max_suppliers])
    cursor.execute(query, params)
    gaps = cursor.fetchall()

    # Calculate opportunity scores for each gap
    opportunities = []

    for gap in gaps:
        src_country = gap[0]
        fruit = gap[1]
        format_type = gap[2]
        certification = gap[3]
        country = gap[4]
        region = gap[5]
        supplier_count = gap[6]
        shipment_count = gap[7]
        volume_mt = gap[8]
        avg_price = gap[9]
        min_price = gap[10]
        max_price = gap[11]

        # Calculate scores
        # 1. Low competition score (0-40): Fewer suppliers = higher score
        if supplier_count == 1:
            competition_score = 40
        elif supplier_count == 2:
            competition_score = 30
        elif supplier_count == 3:
            competition_score = 20
        else:
            competition_score = 10

        # 2. Market size score (0-30): Larger market = higher score
        if volume_mt > 1000:
            size_score = 30
        elif volume_mt > 500:
            size_score = 20
        elif volume_mt > 200:
            size_score = 10
        else:
            size_score = 5

        # 3. Price premium score (0-30): Higher prices = higher score
        if avg_price > 3000:
            price_score = 30
        elif avg_price > 2500:
            price_score = 20
        elif avg_price > 2000:
            price_score = 10
        else:
            price_score = 5

        opportunity_score = competition_score + size_score + price_score

        # Priority level
        if opportunity_score >= 70:
            priority = "high"
        elif opportunity_score >= 50:
            priority = "medium"
        else:
            priority = "low"

        opportunities.append({
            "source_country": src_country,
            "product": {
                "fruit": fruit,
                "format": format_type,
                "certification": certification
            },
            "market": {
                "country": country,
                "region": region
            },
            "opportunity_score": opportunity_score,
            "priority": priority,
            "metrics": {
                "supplier_count": supplier_count,
                "market_size_mt": round(volume_mt, 2),
                "avg_price_usd_per_mt_fob": round(avg_price, 2),
                "price_range": {
                    "min": round(min_price, 2),
                    "max": round(max_price, 2),
                    "spread_pct": round((max_price - min_price) / min_price * 100, 1) if min_price > 0 else 0
                },
                "shipment_frequency": shipment_count
            },
            "score_breakdown": {
                "low_competition": competition_score,
                "market_size": size_score,
                "price_premium": price_score
            }
        })

    # Sort by opportunity score
    opportunities.sort(key=lambda x: x['opportunity_score'], reverse=True)

    conn.close()

    return {
        "analysis_period": start_date,
        "filters": {
            "target_country": target_country or "all",
            "product_category": product_category or "all",
            "source_country": source_country or "all",
            "min_market_size_mt": min_market_size_mt,
            "max_suppliers": max_suppliers
        },
        "opportunities_found": len(opportunities),
        "top_opportunities": opportunities[:20],  # Top 20
        "summary": {
            "high_priority_count": sum(1 for o in opportunities if o['priority'] == 'high'),
            "medium_priority_count": sum(1 for o in opportunities if o['priority'] == 'medium'),
            "low_priority_count": sum(1 for o in opportunities if o['priority'] == 'low'),
            "by_source_country": {
                "peru": sum(1 for o in opportunities if o['source_country'] == 'peru'),
                "ecuador": sum(1 for o in opportunities if o['source_country'] == 'ecuador')
            }
        }
    }


@mcp.tool()
def identify_market_gaps(
    target_country: Optional[str] = None,
    product_category: Optional[str] = None,
    source_country: Optional[str] = None,
    min_market_size_mt: float = 100.0,
    max_suppliers: int = 5,
    start_date: str = "ytd"
) -> Dict[str, Any]:
    """
    Identify underserved product-country combinations with opportunity potential.

    Finds markets with:
    - High demand (volume) but few suppliers
    - Premium pricing opportunities
    - Low competition intensity
    - Seasonal supply gaps

    Results are always separated by source country (Peru vs Ecuador).

    Args:
        target_country: Optional specific country to analyze (English name)
        product_category: Optional fruit type filter
        source_country: Filter by source country ('peru' or 'ecuador')
        min_market_size_mt: Minimum market size to consider (default 100 MT)
        max_suppliers: Max suppliers to qualify as "underserved" (default 5)
        start_date: Analysis period (default 'ytd')

    Returns:
        List of market gap opportunities with priority scores, separated by source country
    """
    return _identify_market_gaps_impl(
        target_country, product_category, source_country,
        min_market_size_mt, max_suppliers, start_date
    )


# Export implementation for use by main module
identify_market_gaps_impl = _identify_market_gaps_impl


if __name__ == "__main__":
    mcp.run()
