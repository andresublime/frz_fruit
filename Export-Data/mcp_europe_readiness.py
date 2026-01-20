"""
Europe Market Readiness Assessment Tools.
Assess exporter's readiness for European market entry and expansion.
"""
from typing import Dict, Any, Optional
from mcp_helpers import (
    get_db_connection,
    fuzzy_match_exporter,
    calculate_hhi,
    parse_relative_date
)
import fastmcp

mcp = fastmcp.FastMCP("Frozen Fruit Exports - Europe Readiness")


def _analyze_europe_readiness_impl(
    exporter_name: str,
    source_country: Optional[str] = None,
    start_date: str = "ytd"
) -> Dict[str, Any]:
    """
    Implementation of Europe readiness assessment.
    """
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

    # 1. Overall export profile
    cursor.execute("""
        SELECT
            COUNT(*) as total_shipments,
            SUM(net_weight_mt) as total_volume,
            SUM([U$ FOB Tot]) as total_fob,
            AVG(usd_per_mt_fob) as avg_price
        FROM exports
        WHERE Exporter = ? AND net_weight_mt > 0 AND Date >= ?
    """, (exporter, date_filter))
    overall = cursor.fetchone()

    # 2. Europe-specific metrics
    cursor.execute("""
        SELECT
            COUNT(*) as europe_shipments,
            SUM(net_weight_mt) as europe_volume,
            SUM([U$ FOB Tot]) as europe_fob,
            AVG(usd_per_mt_fob) as europe_avg_price,
            COUNT(DISTINCT destination_country_en) as europe_countries
        FROM exports
        WHERE Exporter = ? AND region = 'Europe' AND net_weight_mt > 0 AND Date >= ?
    """, (exporter, date_filter))
    europe = cursor.fetchone()

    # 3. Organic certification analysis
    cursor.execute("""
        SELECT
            SUM(CASE WHEN certification = 'organic' THEN net_weight_mt ELSE 0 END) as organic_mt,
            SUM(CASE WHEN certification = 'organic' AND region = 'Europe' THEN net_weight_mt ELSE 0 END) as europe_organic_mt,
            SUM(net_weight_mt) as total_mt
        FROM exports
        WHERE Exporter = ? AND net_weight_mt > 0 AND Date >= ?
    """, (exporter, date_filter))
    organic = cursor.fetchone()

    # 4. Product diversification in Europe
    cursor.execute("""
        SELECT
            fruit_name,
            format_type,
            SUM(net_weight_mt) as volume_mt,
            AVG(usd_per_mt_fob) as avg_price
        FROM exports
        WHERE Exporter = ? AND region = 'Europe' AND net_weight_mt > 0 AND Date >= ?
        GROUP BY fruit_name, format_type
        ORDER BY volume_mt DESC
    """, (exporter, date_filter))
    europe_products = cursor.fetchall()

    # 5. European countries served
    cursor.execute("""
        SELECT
            destination_country_en,
            SUM(net_weight_mt) as volume_mt,
            AVG(usd_per_mt_fob) as avg_price,
            COUNT(*) as shipment_count
        FROM exports
        WHERE Exporter = ? AND region = 'Europe' AND net_weight_mt > 0 AND Date >= ?
        GROUP BY destination_country_en
        ORDER BY volume_mt DESC
    """, (exporter, date_filter))
    europe_countries = cursor.fetchall()

    # 6. Market average prices in Europe for comparison
    cursor.execute("""
        SELECT AVG(usd_per_mt_fob) as market_avg_price_europe
        FROM exports
        WHERE region = 'Europe' AND net_weight_mt > 0 AND Date >= ?
    """, (date_filter,))
    market_europe_price = cursor.fetchone()[0]

    conn.close()

    # Calculate metrics
    total_volume = overall[1] or 0
    europe_volume = europe[1] or 0
    europe_exposure_pct = (europe_volume / total_volume * 100) if total_volume > 0 else 0

    organic_mt = organic[0] or 0
    total_mt = organic[2] or 0
    organic_certification_pct = (organic_mt / total_mt * 100) if total_mt > 0 else 0

    europe_organic_mt = organic[1] or 0
    europe_organic_pct = (europe_organic_mt / europe_volume * 100) if europe_volume > 0 else 0

    europe_countries_count = europe[4] or 0
    europe_products_count = len(europe_products)

    # Price positioning
    exporter_europe_price = europe[3] or 0
    price_premium_vs_market = ((exporter_europe_price / market_europe_price - 1) * 100) if market_europe_price > 0 else 0

    # Calculate HHI for product concentration in Europe
    if europe_products:
        product_volumes = [p[2] for p in europe_products]
        product_shares = [v / sum(product_volumes) for v in product_volumes]
        product_concentration_hhi = calculate_hhi(product_shares)
    else:
        product_concentration_hhi = 0

    # Calculate HHI for geographic concentration in Europe
    if europe_countries:
        country_volumes = [c[1] for c in europe_countries]
        country_shares = [v / sum(country_volumes) for v in country_volumes]
        geographic_concentration_hhi = calculate_hhi(country_shares)
    else:
        geographic_concentration_hhi = 0

    # Readiness scoring (0-100)
    # 1. Europe exposure (0-25 points): >20% = 25, 10-20% = 15, 5-10% = 10, <5% = 5
    if europe_exposure_pct > 20:
        exposure_score = 25
    elif europe_exposure_pct > 10:
        exposure_score = 15
    elif europe_exposure_pct > 5:
        exposure_score = 10
    else:
        exposure_score = 5

    # 2. Organic certification (0-25 points): >50% = 25, 30-50% = 20, 10-30% = 10, <10% = 5
    if organic_certification_pct > 50:
        organic_score = 25
    elif organic_certification_pct > 30:
        organic_score = 20
    elif organic_certification_pct > 10:
        organic_score = 10
    else:
        organic_score = 5

    # 3. Geographic diversification (0-25 points): >5 countries = 25, 3-5 = 15, 1-2 = 5
    if europe_countries_count > 5:
        geo_score = 25
    elif europe_countries_count >= 3:
        geo_score = 15
    else:
        geo_score = 5

    # 4. Product diversification (0-25 points): Low HHI = diversified = higher score
    if product_concentration_hhi < 2500:
        product_score = 25
    elif product_concentration_hhi < 5000:
        product_score = 15
    else:
        product_score = 5

    readiness_score = exposure_score + organic_score + geo_score + product_score

    # Interpretation
    if readiness_score >= 75:
        readiness_level = "high"
        recommendation = "Strong Europe readiness. Well-positioned for expansion."
    elif readiness_score >= 50:
        readiness_level = "medium"
        recommendation = "Moderate Europe readiness. Opportunities for improvement in diversification or organic certification."
    else:
        readiness_level = "low"
        recommendation = "Limited Europe readiness. Consider building organic portfolio and expanding country coverage."

    return {
        "exporter": exporter,
        "analysis_period": start_date,
        "readiness_score": readiness_score,
        "readiness_level": readiness_level,
        "recommendation": recommendation,
        "score_breakdown": {
            "europe_exposure": {"score": exposure_score, "max": 25},
            "organic_certification": {"score": organic_score, "max": 25},
            "geographic_diversification": {"score": geo_score, "max": 25},
            "product_diversification": {"score": product_score, "max": 25}
        },
        "europe_metrics": {
            "exposure_pct": round(europe_exposure_pct, 1),
            "volume_mt": round(europe_volume, 2),
            "fob_value_usd": round(europe[2], 2) if europe[2] else 0,
            "shipment_count": europe[0],
            "countries_served": europe_countries_count,
            "avg_price_usd_per_mt": round(exporter_europe_price, 2)
        },
        "organic_analysis": {
            "overall_organic_pct": round(organic_certification_pct, 1),
            "europe_organic_pct": round(europe_organic_pct, 1),
            "organic_volume_mt": round(organic_mt, 2),
            "europe_organic_volume_mt": round(europe_organic_mt, 2)
        },
        "price_positioning": {
            "exporter_avg_price_europe": round(exporter_europe_price, 2),
            "market_avg_price_europe": round(market_europe_price, 2),
            "price_premium_pct": round(price_premium_vs_market, 2),
            "tier": "premium" if price_premium_vs_market > 10 else "economy" if price_premium_vs_market < -10 else "mid-market"
        },
        "diversification": {
            "product_concentration_hhi": round(product_concentration_hhi, 2),
            "product_diversity": "high" if product_concentration_hhi < 2500 else "medium" if product_concentration_hhi < 5000 else "low",
            "geographic_concentration_hhi": round(geographic_concentration_hhi, 2),
            "geographic_diversity": "high" if geographic_concentration_hhi < 2500 else "medium" if geographic_concentration_hhi < 5000 else "low",
            "unique_products": europe_products_count
        },
        "europe_portfolio": {
            "products": [
                {"fruit": p[0], "format": p[1], "volume_mt": round(p[2], 2), "avg_price": round(p[3], 2)}
                for p in europe_products[:10]
            ],
            "countries": [
                {"country": c[0], "volume_mt": round(c[1], 2), "avg_price": round(c[2], 2), "shipments": c[3]}
                for c in europe_countries
            ]
        }
    }


@mcp.tool()
def analyze_europe_readiness(
    exporter_name: str,
    source_country: Optional[str] = None,
    start_date: str = "ytd"
) -> Dict[str, Any]:
    """
    Assess exporter's readiness for European market entry and expansion.

    Analyzes:
    - Current Europe market exposure
    - Organic certification percentage (Europe demands)
    - Product-country diversification
    - Price positioning vs European competitors
    - Compliance readiness indicators

    Args:
        exporter_name: Company name (fuzzy match supported)
        source_country: Filter by source country ('peru' or 'ecuador')
        start_date: Analysis period (default 'ytd')

    Returns:
        Comprehensive Europe readiness assessment with scores
    """
    return _analyze_europe_readiness_impl(exporter_name, source_country, start_date)


# Export implementation for use by main module
analyze_europe_readiness_impl = _analyze_europe_readiness_impl


if __name__ == "__main__":
    mcp.run()
