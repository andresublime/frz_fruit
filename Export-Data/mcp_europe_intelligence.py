"""
Europe Market Intelligence Tools for Peru Frozen Fruit Export MCP Server.
Specialized tools for European market entry analysis and gap identification.
"""
from typing import Dict, Any, Optional, List
from mcp_helpers import (
    get_db_connection,
    fuzzy_match_exporter,
    calculate_hhi,
    parse_relative_date
)
import fastmcp

mcp = fastmcp.FastMCP("Peru Frozen Fruit Exports - Europe Intelligence")


@mcp.tool()
def analyze_europe_readiness(
    exporter_name: str,
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
        start_date: Analysis period (default 'ytd')

    Returns:
        Comprehensive Europe readiness assessment with scores
    """
    # Find matching exporter
    matching_exporters = fuzzy_match_exporter(exporter_name)
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
def identify_market_gaps(
    target_country: Optional[str] = None,
    product_category: Optional[str] = None,
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

    Args:
        target_country: Optional specific country to analyze (English name)
        product_category: Optional fruit type filter
        min_market_size_mt: Minimum market size to consider (default 100 MT)
        max_suppliers: Max suppliers to qualify as "underserved" (default 5)
        start_date: Analysis period (default 'ytd')

    Returns:
        List of market gap opportunities with priority scores
    """
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

    where_sql = " AND ".join(where_clauses)

    # Find product-country combinations with market metrics
    query = f"""
        SELECT
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
        GROUP BY fruit_name, format_type, certification, destination_country_en, region
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
        fruit = gap[0]
        format_type = gap[1]
        certification = gap[2]
        country = gap[3]
        region = gap[4]
        supplier_count = gap[5]
        shipment_count = gap[6]
        volume_mt = gap[7]
        avg_price = gap[8]
        min_price = gap[9]
        max_price = gap[10]

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
                "avg_price_usd_per_mt": round(avg_price, 2),
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
            "min_market_size_mt": min_market_size_mt,
            "max_suppliers": max_suppliers
        },
        "opportunities_found": len(opportunities),
        "top_opportunities": opportunities[:20],  # Top 20
        "summary": {
            "high_priority_count": sum(1 for o in opportunities if o['priority'] == 'high'),
            "medium_priority_count": sum(1 for o in opportunities if o['priority'] == 'medium'),
            "low_priority_count": sum(1 for o in opportunities if o['priority'] == 'low')
        }
    }


@mcp.tool()
def benchmark_europe_competitors(
    exporter_name: str,
    fruit: Optional[str] = None,
    certification: Optional[str] = None,
    start_date: str = "ytd"
) -> Dict[str, Any]:
    """
    Benchmark exporter against competitors in European markets.

    Analyzes:
    - Market share in Europe
    - Pricing strategy vs competitors
    - Product overlap and differentiation
    - Geographic coverage comparison
    - Certification mix

    Args:
        exporter_name: Company to benchmark (fuzzy match)
        fruit: Optional fruit filter
        certification: Optional certification filter ('organic', 'conventional')
        start_date: Analysis period (default 'ytd')

    Returns:
        Competitive benchmark analysis for Europe
    """
    # Find matching exporter
    matching_exporters = fuzzy_match_exporter(exporter_name)
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

    # 1. Get target exporter's Europe metrics
    cursor.execute(f"""
        SELECT
            SUM(net_weight_mt) as volume_mt,
            AVG(usd_per_mt_fob) as avg_price,
            COUNT(*) as shipments,
            COUNT(DISTINCT destination_country_en) as countries,
            COUNT(DISTINCT fruit_name) as fruits
        FROM exports
        WHERE Exporter = ? AND {where_sql}
    """, [exporter] + params)
    target = cursor.fetchone()

    # 2. Get market total for share calculation
    cursor.execute(f"""
        SELECT SUM(net_weight_mt) as market_total
        FROM exports
        WHERE {where_sql}
    """, params)
    market_total = cursor.fetchone()[0] or 0

    # 3. Get top 10 competitors in Europe
    cursor.execute(f"""
        SELECT
            Exporter,
            SUM(net_weight_mt) as volume_mt,
            AVG(usd_per_mt_fob) as avg_price,
            COUNT(*) as shipments,
            COUNT(DISTINCT destination_country_en) as countries
        FROM exports
        WHERE {where_sql}
        GROUP BY Exporter
        ORDER BY volume_mt DESC
        LIMIT 10
    """, params)
    competitors = cursor.fetchall()

    # 4. Find target's rank
    cursor.execute(f"""
        SELECT Exporter, SUM(net_weight_mt) as volume_mt
        FROM exports
        WHERE {where_sql}
        GROUP BY Exporter
        ORDER BY volume_mt DESC
    """, params)
    all_exporters = cursor.fetchall()

    target_rank = next((i + 1 for i, e in enumerate(all_exporters) if e[0] == exporter), None)

    conn.close()

    # Calculate metrics
    target_volume = target[0] or 0
    market_share_pct = (target_volume / market_total * 100) if market_total > 0 else 0

    # Format competitors
    competitor_list = []
    for i, comp in enumerate(competitors, 1):
        comp_name = comp[0]
        comp_volume = comp[1]
        comp_share = (comp_volume / market_total * 100) if market_total > 0 else 0

        competitor_list.append({
            "rank": i,
            "exporter": comp_name,
            "is_target": comp_name == exporter,
            "volume_mt": round(comp_volume, 2),
            "market_share_pct": round(comp_share, 2),
            "avg_price_usd_per_mt": round(comp[2], 2) if comp[2] else 0,
            "shipments": comp[3],
            "countries_served": comp[4]
        })

    return {
        "target_exporter": exporter,
        "analysis_period": start_date,
        "market_scope": "Europe",
        "filters": {
            "fruit": fruit or "all",
            "certification": certification or "all"
        },
        "target_metrics": {
            "rank": target_rank,
            "market_share_pct": round(market_share_pct, 2),
            "volume_mt": round(target_volume, 2),
            "avg_price_usd_per_mt": round(target[1], 2) if target[1] else 0,
            "shipments": target[2],
            "countries_served": target[3],
            "unique_fruits": target[4]
        },
        "market_context": {
            "total_market_size_mt": round(market_total, 2),
            "total_exporters": len(all_exporters)
        },
        "top_10_competitors": competitor_list,
        "competitive_position": {
            "rank_category": "leader" if target_rank and target_rank <= 3 else "challenger" if target_rank and target_rank <= 10 else "follower",
            "share_category": "dominant" if market_share_pct > 20 else "strong" if market_share_pct > 10 else "moderate" if market_share_pct > 5 else "niche"
        }
    }


@mcp.tool()
def analyze_europe_by_fruit(
    fruit: str,
    start_date: str = "ytd",
    min_market_size_mt: float = 10.0,
    include_product_breakdown: bool = True,
    include_price_analysis: bool = True,
    include_supplier_analysis: bool = True
) -> Dict[str, Any]:
    """
    Comprehensive European country-by-country analysis for a specific fruit.

    Analyzes each European country showing:
    - Market size (volume and value)
    - Market share of Europe total
    - Average pricing and price ranges
    - Supplier concentration (HHI)
    - Product mix (formats, sizes, certifications)
    - Organic vs conventional split
    - Top exporters per country
    - Market attractiveness scoring

    Perfect for answering: "Show me what each European country looks like for mangoes"

    Args:
        fruit: Fruit type to analyze (e.g., 'mango', 'blueberry', 'avocado')
        start_date: Analysis period (default 'ytd')
        min_market_size_mt: Minimum market size to include (default 10 MT)
        include_product_breakdown: Show format/size/certification breakdown
        include_price_analysis: Include price statistics and ranges
        include_supplier_analysis: Show supplier concentration and top exporters

    Returns:
        Detailed analysis of each European country for the specified fruit
        Sorted by market attractiveness score
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Parse date
    parsed_start = parse_relative_date(start_date)
    if not parsed_start:
        parsed_start = parse_relative_date("ytd")

    date_filter = parsed_start.strftime('%Y-%m-%d')

    # Get all European countries for this fruit
    cursor.execute("""
        SELECT
            destination_country_en,
            COUNT(*) as shipment_count,
            SUM(net_weight_mt) as total_volume_mt,
            SUM([U$ FOB Tot]) as total_fob_usd,
            AVG(usd_per_mt_fob) as avg_price,
            MIN(usd_per_mt_fob) as min_price,
            MAX(usd_per_mt_fob) as max_price,
            COUNT(DISTINCT Exporter) as supplier_count
        FROM exports
        WHERE region = 'Europe'
          AND fruit_name LIKE ?
          AND net_weight_mt > 0
          AND usd_per_mt_fob > 0
          AND Date >= ?
        GROUP BY destination_country_en
        HAVING total_volume_mt >= ?
        ORDER BY total_volume_mt DESC
    """, (f"%{fruit}%", date_filter, min_market_size_mt))

    countries_data = cursor.fetchall()

    if not countries_data:
        conn.close()
        return {
            "error": f"No European market data found for '{fruit}' in period {start_date}",
            "suggestion": "Try a different fruit or broader date range"
        }

    # Calculate total Europe market for percentages
    total_europe_volume = sum(c[2] for c in countries_data)
    total_europe_value = sum(c[3] for c in countries_data)

    # Analyze each country
    country_analyses = []

    for country_data in countries_data:
        country = country_data[0]
        shipment_count = country_data[1]
        volume_mt = country_data[2]
        fob_usd = country_data[3]
        avg_price = country_data[4]
        min_price = country_data[5]
        max_price = country_data[6]
        supplier_count = country_data[7]

        # Market share
        market_share_volume_pct = (volume_mt / total_europe_volume * 100) if total_europe_volume > 0 else 0
        market_share_value_pct = (fob_usd / total_europe_value * 100) if total_europe_value > 0 else 0

        country_analysis = {
            "country": country,
            "market_metrics": {
                "volume_mt": round(volume_mt, 2),
                "fob_value_usd": round(fob_usd, 2),
                "shipment_count": shipment_count,
                "market_share_volume_pct": round(market_share_volume_pct, 2),
                "market_share_value_pct": round(market_share_value_pct, 2),
                "avg_shipment_size_mt": round(volume_mt / shipment_count, 2) if shipment_count > 0 else 0
            }
        }

        # Price analysis
        if include_price_analysis:
            price_range_pct = ((max_price - min_price) / min_price * 100) if min_price > 0 else 0

            country_analysis["price_analysis"] = {
                "avg_price_usd_per_mt": round(avg_price, 2),
                "min_price": round(min_price, 2),
                "max_price": round(max_price, 2),
                "price_range_usd": round(max_price - min_price, 2),
                "price_volatility_pct": round(price_range_pct, 2),
                "price_tier": "premium" if avg_price > 2500 else "economy" if avg_price < 2000 else "mid-market"
            }

        # Product breakdown
        if include_product_breakdown:
            cursor.execute("""
                SELECT
                    format_type,
                    size_mm,
                    certification,
                    SUM(net_weight_mt) as volume_mt,
                    AVG(usd_per_mt_fob) as avg_price,
                    COUNT(*) as shipments
                FROM exports
                WHERE region = 'Europe'
                  AND destination_country_en = ?
                  AND fruit_name LIKE ?
                  AND net_weight_mt > 0
                  AND Date >= ?
                GROUP BY format_type, size_mm, certification
                ORDER BY volume_mt DESC
                LIMIT 5
            """, (country, f"%{fruit}%", date_filter))

            products = []
            for row in cursor.fetchall():
                products.append({
                    "format": row[0],
                    "size": row[1],
                    "certification": row[2],
                    "volume_mt": round(row[3], 2),
                    "avg_price": round(row[4], 2),
                    "shipments": row[5]
                })

            # Organic vs Conventional split
            cursor.execute("""
                SELECT
                    certification,
                    SUM(net_weight_mt) as volume_mt,
                    AVG(usd_per_mt_fob) as avg_price
                FROM exports
                WHERE region = 'Europe'
                  AND destination_country_en = ?
                  AND fruit_name LIKE ?
                  AND net_weight_mt > 0
                  AND Date >= ?
                GROUP BY certification
            """, (country, f"%{fruit}%", date_filter))

            cert_split = {}
            for row in cursor.fetchall():
                cert_type = row[0]
                cert_volume = row[1]
                cert_price = row[2]
                cert_pct = (cert_volume / volume_mt * 100) if volume_mt > 0 else 0

                cert_split[cert_type] = {
                    "volume_mt": round(cert_volume, 2),
                    "percentage": round(cert_pct, 2),
                    "avg_price": round(cert_price, 2)
                }

            country_analysis["product_breakdown"] = {
                "top_products": products,
                "certification_split": cert_split,
                "organic_percentage": round(cert_split.get('organic', {}).get('percentage', 0), 2)
            }

        # Supplier analysis
        if include_supplier_analysis:
            # Get supplier shares for HHI calculation
            cursor.execute("""
                SELECT
                    Exporter,
                    SUM(net_weight_mt) as volume_mt,
                    AVG(usd_per_mt_fob) as avg_price,
                    COUNT(*) as shipments
                FROM exports
                WHERE region = 'Europe'
                  AND destination_country_en = ?
                  AND fruit_name LIKE ?
                  AND net_weight_mt > 0
                  AND Date >= ?
                GROUP BY Exporter
                ORDER BY volume_mt DESC
            """, (country, f"%{fruit}%", date_filter))

            suppliers = cursor.fetchall()

            # Calculate HHI
            supplier_volumes = [s[1] for s in suppliers]
            if supplier_volumes:
                supplier_shares = [v / sum(supplier_volumes) for v in supplier_volumes]
                supplier_hhi = calculate_hhi(supplier_shares)
            else:
                supplier_hhi = 0

            # Top 5 suppliers
            top_suppliers = []
            for i, sup in enumerate(suppliers[:5], 1):
                sup_share = (sup[1] / volume_mt * 100) if volume_mt > 0 else 0
                top_suppliers.append({
                    "rank": i,
                    "exporter": sup[0],
                    "volume_mt": round(sup[1], 2),
                    "market_share_pct": round(sup_share, 2),
                    "avg_price": round(sup[2], 2),
                    "shipments": sup[3]
                })

            country_analysis["supplier_analysis"] = {
                "supplier_count": supplier_count,
                "concentration_hhi": round(supplier_hhi, 2),
                "concentration_level": "highly concentrated" if supplier_hhi > 2500 else "moderately concentrated" if supplier_hhi > 1500 else "competitive",
                "top_suppliers": top_suppliers
            }

        # Market attractiveness scoring
        # Factors: Size (0-30), Price (0-25), Competition (0-25), Organic demand (0-20)

        # Size score
        if volume_mt > 500:
            size_score = 30
        elif volume_mt > 200:
            size_score = 25
        elif volume_mt > 100:
            size_score = 20
        elif volume_mt > 50:
            size_score = 15
        else:
            size_score = 10

        # Price score (higher = better)
        if avg_price > 3000:
            price_score = 25
        elif avg_price > 2500:
            price_score = 20
        elif avg_price > 2000:
            price_score = 15
        else:
            price_score = 10

        # Competition score (lower concentration = higher score)
        if include_supplier_analysis:
            if supplier_hhi < 1500:
                competition_score = 25
            elif supplier_hhi < 2500:
                competition_score = 15
            else:
                competition_score = 5
        else:
            competition_score = 15  # Default middle

        # Organic demand score
        if include_product_breakdown:
            organic_pct = cert_split.get('organic', {}).get('percentage', 0)
            if organic_pct > 50:
                organic_score = 20
            elif organic_pct > 30:
                organic_score = 15
            elif organic_pct > 10:
                organic_score = 10
            else:
                organic_score = 5
        else:
            organic_score = 10  # Default middle

        attractiveness_score = size_score + price_score + competition_score + organic_score

        # Determine priority
        if attractiveness_score >= 75:
            priority = "high"
            recommendation = "Attractive market: Large size, good pricing, and favorable competition."
        elif attractiveness_score >= 60:
            priority = "medium"
            recommendation = "Moderate opportunity: Consider entry with differentiation strategy."
        else:
            priority = "low"
            recommendation = "Limited attractiveness: Small market or intense competition."

        country_analysis["market_attractiveness"] = {
            "score": attractiveness_score,
            "priority": priority,
            "recommendation": recommendation,
            "score_breakdown": {
                "market_size": size_score,
                "price_premium": price_score,
                "competition": competition_score,
                "organic_demand": organic_score
            }
        }

        country_analyses.append(country_analysis)

    # Sort by attractiveness score
    country_analyses.sort(key=lambda x: x['market_attractiveness']['score'], reverse=True)

    # Summary statistics
    summary = {
        "fruit": fruit,
        "analysis_period": start_date,
        "total_europe_volume_mt": round(total_europe_volume, 2),
        "total_europe_value_usd": round(total_europe_value, 2),
        "avg_europe_price_usd_per_mt": round(total_europe_value / total_europe_volume, 2) if total_europe_volume > 0 else 0,
        "countries_analyzed": len(country_analyses),
        "priority_breakdown": {
            "high_priority": sum(1 for c in country_analyses if c['market_attractiveness']['priority'] == 'high'),
            "medium_priority": sum(1 for c in country_analyses if c['market_attractiveness']['priority'] == 'medium'),
            "low_priority": sum(1 for c in country_analyses if c['market_attractiveness']['priority'] == 'low')
        },
        "top_3_markets": [
            {
                "country": c['country'],
                "volume_mt": c['market_metrics']['volume_mt'],
                "market_share_pct": c['market_metrics']['market_share_volume_pct'],
                "attractiveness_score": c['market_attractiveness']['score']
            }
            for c in country_analyses[:3]
        ]
    }

    conn.close()

    return {
        "summary": summary,
        "country_analyses": country_analyses
    }


# European country geographic neighbors mapping
EUROPEAN_NEIGHBORS = {
    # Baltic States (expanded to include major EU trading partners)
    'Lithuania': ['Poland', 'Latvia', 'Estonia', 'Germany', 'Netherlands'],
    'Latvia': ['Lithuania', 'Estonia', 'Poland', 'Germany', 'Finland'],
    'Estonia': ['Latvia', 'Lithuania', 'Finland', 'Sweden', 'Germany'],
    
    # Western Europe
    'Netherlands': ['Belgium', 'Germany', 'France'],
    'Belgium': ['Netherlands', 'France', 'Germany', 'Luxembourg'],
    'Luxembourg': ['Belgium', 'Germany', 'France'],
    
    # Central Europe
    'Germany': ['Poland', 'Netherlands', 'Belgium', 'France', 'Austria', 'Czech Republic'],
    'Poland': ['Germany', 'Czech Republic', 'Lithuania', 'Latvia'],
    'Czech Republic': ['Germany', 'Poland', 'Austria', 'Slovakia'],
    'Slovakia': ['Czech Republic', 'Poland', 'Austria', 'Hungary'],
    'Austria': ['Germany', 'Czech Republic', 'Slovakia', 'Hungary', 'Italy', 'Switzerland'],
    'Switzerland': ['Germany', 'France', 'Italy', 'Austria'],
    
    # Southern Europe
    'Italy': ['France', 'Austria', 'Switzerland', 'Slovenia'],
    'France': ['Belgium', 'Luxembourg', 'Germany', 'Switzerland', 'Italy', 'Spain'],
    'Spain': ['France', 'Portugal'],
    'Portugal': ['Spain'],
    'Greece': ['Bulgaria', 'Romania'],
    'Slovenia': ['Italy', 'Austria', 'Croatia', 'Hungary'],
    'Croatia': ['Slovenia', 'Hungary', 'Austria'],
    
    # Northern Europe
    'Sweden': ['Norway', 'Finland', 'Denmark'],
    'Norway': ['Sweden', 'Finland', 'Denmark'],
    'Finland': ['Sweden', 'Norway', 'Estonia'],
    'Denmark': ['Germany', 'Sweden', 'Norway'],
    
    # Eastern Europe
    'Hungary': ['Austria', 'Slovakia', 'Romania', 'Croatia', 'Slovenia'],
    'Romania': ['Hungary', 'Bulgaria', 'Greece'],
    'Bulgaria': ['Romania', 'Greece'],
    
    # British Isles
    'United Kingdom': ['Ireland', 'France', 'Netherlands', 'Belgium'],
    'Ireland': ['United Kingdom'],
}


@mcp.tool()
def analyze_country_multi_product(
    target_country: str,
    products: List[Dict[str, str]],
    start_date: str = "ytd",
    use_neighbor_reference: bool = True,
    min_reference_market_size_mt: float = 20.0
) -> Dict[str, Any]:
    """
    Analyze a European country for multiple products simultaneously.
    If the target country has no imports for a product, reference similar neighboring countries.

    Perfect for queries like:
    "How does the market in Lithuania look for: Mango chunks, Pineapple chunks, Blueberries, etc."

    Args:
        target_country: Country to analyze (e.g., 'Lithuania', 'Poland')
        products: List of products to analyze, each with:
                  - fruit: Fruit name (required)
                  - format: Optional format (chunks, cubes, halves, pulp, etc.)
                  - size: Optional size (20x20, 25x25, 10x10, etc.)
                  - certification: Optional ('organic', 'conventional')
        start_date: Analysis period (default 'ytd')
        use_neighbor_reference: If True, reference neighboring countries when no data
        min_reference_market_size_mt: Minimum size for neighbor to be considered relevant

    Returns:
        Analysis for each product showing:
        - Target country data (if available)
        - Neighbor reference markets (if no target data)
        - Market recommendations

    Example:
        products = [
            {"fruit": "mango", "format": "chunks"},
            {"fruit": "pineapple", "format": "chunks"},
            {"fruit": "passion_fruit", "format": "cubes", "size": "20x20"},
            {"fruit": "strawberry", "format": "halves"},
            {"fruit": "blueberry"},
            {"fruit": "papaya", "format": "pulp"},
            {"fruit": "papaya", "format": "cubes"},
            {"fruit": "avocado", "format": "cubes"}
        ]
    """
    from translations import translate_country_to_english, translate_country_to_spanish

    conn = get_db_connection()
    cursor = conn.cursor()

    # Parse date
    parsed_start = parse_relative_date(start_date)
    if not parsed_start:
        parsed_start = parse_relative_date("ytd")
    date_filter = parsed_start.strftime('%Y-%m-%d')

    # Normalize target country name (for display)
    target_country_normalized = translate_country_to_english(target_country)

    # Get Spanish name for database query
    target_country_spanish = translate_country_to_spanish(target_country_normalized)

    # Get neighbors
    neighbors = EUROPEAN_NEIGHBORS.get(target_country_normalized, [])

    # Analyze each product
    product_analyses = []

    for product in products:
        fruit = product.get('fruit')
        format_type = product.get('format')
        size = product.get('size')
        certification = product.get('certification')

        if not fruit:
            continue

        # Build product description for display
        product_desc_parts = [fruit]
        if format_type:
            product_desc_parts.append(format_type)
        if size:
            product_desc_parts.append(size)
        if certification:
            product_desc_parts.append(certification)
        product_description = " ".join(product_desc_parts)

        # Build WHERE clause for product
        product_where = ["fruit_name LIKE ?"]
        product_params = [f"%{fruit}%"]

        if format_type:
            product_where.append("format_type LIKE ?")
            product_params.append(f"%{format_type}%")

        if size:
            product_where.append("size_mm LIKE ?")
            product_params.append(f"%{size}%")

        if certification:
            product_where.append("certification = ?")
            product_params.append(certification)

        product_where_sql = " AND ".join(product_where)

        # Query target country from regional_exports
        cursor.execute(f"""
            SELECT
                shipment_count,
                total_mt,
                total_fob_usd,
                avg_usd_per_mt
            FROM regional_exports
            WHERE country = ?
              AND {product_where_sql}
              AND total_mt > 0
        """, [target_country_spanish] + product_params)

        target_data = cursor.fetchone()
        target_volume = target_data[1] if target_data else 0

        product_analysis = {
            "product": product_description,
            "product_specs": product,
            "target_country": target_country_normalized
        }

        # If target country has data
        if target_volume > 0:
            product_analysis["target_market"] = {
                "status": "active",
                "volume_mt": round(target_volume, 2),
                "fob_value_usd": round(target_data[2], 2) if target_data[2] else 0,
                "shipment_count": target_data[0],
                "avg_price_usd_per_mt": round(target_data[3], 2) if target_data[3] else 0,
                "recommendation": f"Active market with {target_data[0]} shipments. "
                                f"Avg price: ${round(target_data[3], 2) if target_data[3] else 0}/MT."
            }

        # If no target country data, reference neighbors
        elif use_neighbor_reference and neighbors:
            # Query all neighbors
            neighbor_markets = []

            for neighbor in neighbors:
                # Translate neighbor name to Spanish for database query
                neighbor_spanish = translate_country_to_spanish(neighbor)

                cursor.execute(f"""
                    SELECT
                        country,
                        shipment_count,
                        total_mt,
                        total_fob_usd,
                        avg_usd_per_mt
                    FROM regional_exports
                    WHERE country = ?
                      AND {product_where_sql}
                      AND total_mt >= ?
                """, [neighbor_spanish] + product_params + [min_reference_market_size_mt])

                neighbor_data = cursor.fetchone()
                if neighbor_data and neighbor_data[2]:  # Check total_mt exists
                    # Get ALL exporters for this neighbor-product combination
                    cursor.execute(f"""
                        SELECT
                            Exporter,
                            SUM(net_weight_mt) as volume,
                            AVG(usd_per_mt_fob) as avg_price,
                            COUNT(*) as shipments
                        FROM exports
                        WHERE "Destination Country" = ?
                          AND {product_where_sql}
                          AND net_weight_mt > 0
                          AND usd_per_mt_fob > 0
                        GROUP BY Exporter
                        ORDER BY volume DESC
                    """, [neighbor_spanish] + product_params)

                    top_exporters = []
                    for exp_row in cursor.fetchall():
                        top_exporters.append({
                            "exporter": exp_row[0],
                            "volume_mt": round(exp_row[1], 2),
                            "avg_price": round(exp_row[2], 2),
                            "shipments": exp_row[3]
                        })

                    # Get ALL importers (clients) for this neighbor-product combination
                    cursor.execute(f"""
                        SELECT
                            Importer,
                            SUM(net_weight_mt) as volume,
                            AVG(usd_per_mt_fob) as avg_price,
                            COUNT(*) as shipments
                        FROM exports
                        WHERE "Destination Country" = ?
                          AND {product_where_sql}
                          AND net_weight_mt > 0
                          AND usd_per_mt_fob > 0
                        GROUP BY Importer
                        ORDER BY volume DESC
                    """, [neighbor_spanish] + product_params)

                    top_importers = []
                    for imp_row in cursor.fetchall():
                        top_importers.append({
                            "importer": imp_row[0],
                            "volume_mt": round(imp_row[1], 2),
                            "avg_price": round(imp_row[2], 2),
                            "shipments": imp_row[3]
                        })

                    # Get product specifications from this market (top 20)
                    cursor.execute(f"""
                        SELECT
                            fruit_name,
                            format_type,
                            size_mm,
                            certification,
                            SUM(net_weight_mt) as volume
                        FROM exports
                        WHERE "Destination Country" = ?
                          AND {product_where_sql}
                          AND net_weight_mt > 0
                          AND usd_per_mt_fob > 0
                        GROUP BY fruit_name, format_type, size_mm, certification
                        ORDER BY volume DESC
                        LIMIT 20
                    """, [neighbor_spanish] + product_params)

                    product_specs = []
                    for spec_row in cursor.fetchall():
                        fruit_val = spec_row[0]
                        format_val = spec_row[1]
                        size_val = spec_row[2]
                        cert_val = spec_row[3]
                        volume_val = spec_row[4]

                        # Calculate realistic price range (excluding samples < 1 MT)
                        price_where = ["\"Destination Country\" = ?", "net_weight_mt >= 1.0", "usd_per_mt_fob > 0"]
                        price_params = [neighbor_spanish]

                        # Add product filters
                        for param in product_params:
                            price_where.append(product_where_sql.split(" AND ")[len(price_params) - 1])
                            price_params.append(param)

                        if fruit_val:
                            price_where.append("fruit_name = ?")
                            price_params.append(fruit_val)
                        if format_val:
                            price_where.append("format_type = ?")
                            price_params.append(format_val)
                        if size_val:
                            price_where.append("size_mm = ?")
                            price_params.append(size_val)
                        if cert_val:
                            price_where.append("certification = ?")
                            price_params.append(cert_val)

                        cursor.execute(f"""
                            SELECT
                                AVG(usd_per_mt_fob) as avg_price,
                                MIN(usd_per_mt_fob) as min_price,
                                MAX(usd_per_mt_fob) as max_price
                            FROM exports
                            WHERE {product_where_sql}
                              AND "Destination Country" = ?
                              AND net_weight_mt >= 1.0
                              AND usd_per_mt_fob > 0
                              AND fruit_name = COALESCE(?, fruit_name)
                              AND format_type = COALESCE(?, format_type)
                              AND size_mm = COALESCE(?, size_mm)
                              AND certification = COALESCE(?, certification)
                        """, product_params + [neighbor_spanish, fruit_val, format_val, size_val, cert_val])

                        price_row = cursor.fetchone()

                        spec = {}
                        if fruit_val: spec["fruit"] = fruit_val
                        if format_val: spec["format"] = format_val
                        if size_val: spec["size"] = size_val
                        if cert_val: spec["certification"] = cert_val
                        spec["volume_mt"] = round(volume_val, 2)
                        spec["avg_price_usd_per_mt"] = round(price_row[0], 2) if price_row and price_row[0] else 0
                        spec["price_range"] = {
                            "min": round(price_row[1], 2) if price_row and price_row[1] else 0,
                            "max": round(price_row[2], 2) if price_row and price_row[2] else 0
                        }
                        product_specs.append(spec)

                    neighbor_markets.append({
                        "country": neighbor,  # Use English name for display
                        "volume_mt": round(neighbor_data[2], 2),
                        "fob_value_usd": round(neighbor_data[3], 2) if neighbor_data[3] else 0,
                        "shipment_count": neighbor_data[1],
                        "avg_price_usd_per_mt": round(neighbor_data[4], 2) if neighbor_data[4] else 0,
                        "top_exporters": top_exporters,
                        "top_importers": top_importers,
                        "product_specifications": product_specs
                    })

            # Sort by volume
            neighbor_markets.sort(key=lambda x: x['volume_mt'], reverse=True)

            if neighbor_markets:
                product_analysis["target_market"] = {
                    "status": "no_imports",
                    "message": f"No {product_description} imports found in {target_country_normalized}",
                    "recommendation": f"Consider market entry. Similar neighboring countries show active demand."
                }

                product_analysis["reference_markets"] = {
                    "search_type": "immediate_neighbors",
                    "neighbors_analyzed": len(neighbors),
                    "active_neighbors": len(neighbor_markets),
                    "closest_markets": neighbor_markets[:3],  # Top 3 by volume
                    "market_potential_estimate": {
                        "conservative_mt": round(neighbor_markets[0]['volume_mt'] * 0.3, 2) if neighbor_markets else 0,
                        "moderate_mt": round(neighbor_markets[0]['volume_mt'] * 0.5, 2) if neighbor_markets else 0,
                        "optimistic_mt": round(neighbor_markets[0]['volume_mt'] * 0.7, 2) if neighbor_markets else 0,
                        "basis": f"Based on {neighbor_markets[0]['country']}" if neighbor_markets else None
                    },
                    "insights": [
                        f"{market['country']}: {market['volume_mt']} MT @ ${market['avg_price_usd_per_mt']}/MT ({market['shipment_count']} shipments)"
                        for market in neighbor_markets[:3]
                    ]
                }
            else:
                # No data in immediate neighbors - try broader European region
                cursor.execute(f"""
                    SELECT
                        country,
                        shipment_count,
                        total_mt,
                        total_fob_usd,
                        avg_usd_per_mt
                    FROM regional_exports
                    WHERE region = 'Europe'
                      AND {product_where_sql}
                      AND total_mt >= ?
                    ORDER BY total_mt DESC
                    LIMIT 5
                """, product_params + [min_reference_market_size_mt])

                regional_markets = []
                for row in cursor.fetchall():
                    country_spanish = row[0]
                    country_english = translate_country_to_english(country_spanish)

                    # Get top exporters for this regional market
                    cursor.execute(f"""
                        SELECT
                            Exporter,
                            SUM(net_weight_mt) as volume,
                            AVG(usd_per_mt_fob) as avg_price,
                            COUNT(*) as shipments
                        FROM exports
                        WHERE "Destination Country" = ?
                          AND {product_where_sql}
                          AND net_weight_mt > 0
                          AND usd_per_mt_fob > 0
                        GROUP BY Exporter
                        ORDER BY volume DESC
                        LIMIT 5
                    """, [country_spanish] + product_params)

                    top_exporters = []
                    for exp_row in cursor.fetchall():
                        top_exporters.append({
                            "exporter": exp_row[0],
                            "volume_mt": round(exp_row[1], 2),
                            "avg_price": round(exp_row[2], 2),
                            "shipments": exp_row[3]
                        })

                    # Get top importers for this regional market
                    cursor.execute(f"""
                        SELECT
                            Importer,
                            SUM(net_weight_mt) as volume,
                            AVG(usd_per_mt_fob) as avg_price,
                            COUNT(*) as shipments
                        FROM exports
                        WHERE "Destination Country" = ?
                          AND {product_where_sql}
                          AND net_weight_mt > 0
                          AND usd_per_mt_fob > 0
                        GROUP BY Importer
                        ORDER BY volume DESC
                        LIMIT 5
                    """, [country_spanish] + product_params)

                    top_importers = []
                    for imp_row in cursor.fetchall():
                        top_importers.append({
                            "importer": imp_row[0],
                            "volume_mt": round(imp_row[1], 2),
                            "avg_price": round(imp_row[2], 2),
                            "shipments": imp_row[3]
                        })

                    # Get product specifications
                    cursor.execute(f"""
                        SELECT
                            fruit_name,
                            format_type,
                            size_mm,
                            certification,
                            SUM(net_weight_mt) as volume
                        FROM exports
                        WHERE "Destination Country" = ?
                          AND {product_where_sql}
                          AND net_weight_mt > 0
                          AND usd_per_mt_fob > 0
                        GROUP BY fruit_name, format_type, size_mm, certification
                        ORDER BY volume DESC
                        LIMIT 5
                    """, [country_spanish] + product_params)

                    product_specs = []
                    for spec_row in cursor.fetchall():
                        fruit_val = spec_row[0]
                        format_val = spec_row[1]
                        size_val = spec_row[2]
                        cert_val = spec_row[3]
                        volume_val = spec_row[4]

                        # Calculate realistic price range (excluding samples < 1 MT)
                        cursor.execute(f"""
                            SELECT
                                AVG(usd_per_mt_fob) as avg_price,
                                MIN(usd_per_mt_fob) as min_price,
                                MAX(usd_per_mt_fob) as max_price
                            FROM exports
                            WHERE {product_where_sql}
                              AND "Destination Country" = ?
                              AND net_weight_mt >= 1.0
                              AND usd_per_mt_fob > 0
                              AND fruit_name = COALESCE(?, fruit_name)
                              AND format_type = COALESCE(?, format_type)
                              AND size_mm = COALESCE(?, size_mm)
                              AND certification = COALESCE(?, certification)
                        """, product_params + [country_spanish, fruit_val, format_val, size_val, cert_val])

                        price_row = cursor.fetchone()

                        spec = {}
                        if fruit_val: spec["fruit"] = fruit_val
                        if format_val: spec["format"] = format_val
                        if size_val: spec["size"] = size_val
                        if cert_val: spec["certification"] = cert_val
                        spec["volume_mt"] = round(volume_val, 2)
                        spec["avg_price_usd_per_mt"] = round(price_row[0], 2) if price_row and price_row[0] else 0
                        spec["price_range"] = {
                            "min": round(price_row[1], 2) if price_row and price_row[1] else 0,
                            "max": round(price_row[2], 2) if price_row and price_row[2] else 0
                        }
                        product_specs.append(spec)

                    regional_markets.append({
                        "country": country_english,
                        "volume_mt": round(row[2], 2),
                        "fob_value_usd": round(row[3], 2) if row[3] else 0,
                        "shipment_count": row[1],
                        "avg_price_usd_per_mt": round(row[4], 2) if row[4] else 0,
                        "top_exporters": top_exporters,
                        "top_importers": top_importers,
                        "product_specifications": product_specs
                    })

                if regional_markets:
                    product_analysis["target_market"] = {
                        "status": "no_imports",
                        "message": f"No {product_description} imports in {target_country_normalized} or immediate neighbors",
                        "recommendation": f"Market entry opportunity - broader European market shows demand. Consider logistics from major hubs."
                    }

                    product_analysis["reference_markets"] = {
                        "search_type": "broader_european_region",
                        "neighbors_analyzed": len(neighbors),
                        "active_neighbors": 0,
                        "regional_markets": regional_markets,
                        "market_potential_estimate": {
                            "conservative_mt": round(regional_markets[0]['volume_mt'] * 0.1, 2),  # Lower % for distant markets
                            "moderate_mt": round(regional_markets[0]['volume_mt'] * 0.2, 2),
                            "optimistic_mt": round(regional_markets[0]['volume_mt'] * 0.3, 2),
                            "basis": f"Based on European leader {regional_markets[0]['country']}"
                        },
                        "insights": [
                            f"{market['country']}: {market['volume_mt']} MT @ ${market['avg_price_usd_per_mt']}/MT ({market['shipment_count']} shipments)"
                            for market in regional_markets
                        ]
                    }
                else:
                    product_analysis["target_market"] = {
                        "status": "no_imports",
                        "message": f"No {product_description} imports found in Europe",
                        "recommendation": "Limited European demand. Consider other regions or focus on proven products."
                    }

        else:
            # No data and no neighbor reference
            product_analysis["target_market"] = {
                "status": "no_imports",
                "message": f"No {product_description} imports found in {target_country_normalized}",
                "recommendation": "Enable neighbor reference to see similar markets in the region."
            }

        product_analyses.append(product_analysis)

    conn.close()

    # Summary
    active_products = sum(1 for p in product_analyses if p.get('target_market', {}).get('status') == 'active')
    no_import_products = sum(1 for p in product_analyses if p.get('target_market', {}).get('status') == 'no_imports')
    reference_available = sum(1 for p in product_analyses if 'reference_markets' in p)

    return {
        "target_country": target_country_normalized,
        "analysis_period": start_date,
        "products_analyzed": len(product_analyses),
        "summary": {
            "active_markets": active_products,
            "no_imports": no_import_products,
            "neighbor_references_provided": reference_available
        },
        "neighbors_available": neighbors if use_neighbor_reference else [],
        "product_analyses": product_analyses,
        "overall_recommendation": _generate_overall_recommendation(
            target_country_normalized, 
            active_products, 
            no_import_products, 
            reference_available
        )
    }


def _generate_overall_recommendation(country: str, active: int, no_imports: int, references: int) -> str:
    """Generate overall market recommendation."""
    total = active + no_imports
    
    if total == 0:
        return "No products analyzed."
    
    active_pct = (active / total * 100) if total > 0 else 0
    
    if active_pct > 70:
        return f"{country} is an active market for most products analyzed ({active}/{total}). Strong market presence. Consider expansion or optimization."
    elif active_pct > 40:
        return f"{country} shows moderate activity ({active}/{total} products). Mixed market - focus on active products, evaluate reference markets for expansion."
    elif references > 0:
        return f"{country} has limited current imports ({active}/{total}), but neighboring countries show demand. Good opportunity for market entry based on regional trends."
    else:
        return f"{country} shows minimal activity for these products. Consider alternative markets or products with existing demand."


if __name__ == "__main__":
    mcp.run()
