"""
Europe Country and Multi-Product Analysis Tools.
Comprehensive country analysis and multi-product market assessment.
IMPORTANT: All results are separated by source country (Peru vs Ecuador).
"""
from typing import Dict, Any, Optional, List
from mcp_helpers import (
    get_db_connection,
    calculate_hhi,
    parse_relative_date
)
import fastmcp

mcp = fastmcp.FastMCP("Frozen Fruit Exports - Europe Analysis")


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


def _analyze_europe_by_fruit_impl(
    fruit: str,
    source_country: Optional[str] = None,
    start_date: str = "ytd",
    min_market_size_mt: float = 10.0,
    include_product_breakdown: bool = True,
    include_price_analysis: bool = True,
    include_supplier_analysis: bool = True
) -> Dict[str, Any]:
    """Implementation of European country-by-country analysis."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Parse date
    parsed_start = parse_relative_date(start_date)
    if not parsed_start:
        parsed_start = parse_relative_date("ytd")

    date_filter = parsed_start.strftime('%Y-%m-%d')

    # Build WHERE clause
    where_clauses = [
        "region = 'Europe'",
        "fruit_name LIKE ?",
        "net_weight_mt > 0",
        "usd_per_mt_fob > 0",
        "Date >= ?"
    ]
    query_params = [f"%{fruit}%", date_filter]

    if source_country:
        where_clauses.append("source_country = ?")
        query_params.append(source_country.lower())

    where_sql = " AND ".join(where_clauses)

    # Get all European countries for this fruit BY SOURCE COUNTRY
    cursor.execute(f"""
        SELECT
            source_country,
            destination_country_en,
            COUNT(*) as shipment_count,
            SUM(net_weight_mt) as total_volume_mt,
            SUM([U$ FOB Tot]) as total_fob_usd,
            AVG(usd_per_mt_fob) as avg_price,
            MIN(usd_per_mt_fob) as min_price,
            MAX(usd_per_mt_fob) as max_price,
            COUNT(DISTINCT Exporter) as supplier_count
        FROM exports
        WHERE {where_sql}
        GROUP BY source_country, destination_country_en
        HAVING total_volume_mt >= ?
        ORDER BY source_country, total_volume_mt DESC
    """, query_params + [min_market_size_mt])

    countries_data = cursor.fetchall()

    if not countries_data:
        conn.close()
        return {
            "error": f"No European market data found for '{fruit}' in period {start_date}",
            "suggestion": "Try a different fruit or broader date range"
        }

    # Group by source country
    data_by_source = {}
    for row in countries_data:
        src = row[0]
        if src not in data_by_source:
            data_by_source[src] = []
        data_by_source[src].append(row)

    # Analyze each source country separately
    results_by_source_country = {}

    for src_country, countries_list in data_by_source.items():
        # Calculate totals for this source country
        total_volume = sum(c[3] for c in countries_list)
        total_value = sum(c[4] for c in countries_list)

        country_analyses = []

        for country_data in countries_list:
            dest_country = country_data[1]
            shipment_count = country_data[2]
            volume_mt = country_data[3]
            fob_usd = country_data[4]
            avg_price = country_data[5]
            min_price = country_data[6]
            max_price = country_data[7]
            supplier_count = country_data[8]

            # Market share within this source country
            market_share_volume_pct = (volume_mt / total_volume * 100) if total_volume > 0 else 0
            market_share_value_pct = (fob_usd / total_value * 100) if total_value > 0 else 0

            country_analysis = {
                "destination_country": dest_country,
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
                    "avg_price_usd_per_mt_fob": round(avg_price, 2),
                    "min_price_usd_per_mt_fob": round(min_price, 2),
                    "max_price_usd_per_mt_fob": round(max_price, 2),
                    "price_range_usd": round(max_price - min_price, 2),
                    "price_volatility_pct": round(price_range_pct, 2),
                    "price_tier": "premium" if avg_price > 2500 else "economy" if avg_price < 2000 else "mid-market"
                }

            # Product breakdown
            cert_split = {}
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
                      AND source_country = ?
                      AND destination_country_en = ?
                      AND fruit_name LIKE ?
                      AND net_weight_mt > 0
                      AND Date >= ?
                    GROUP BY format_type, size_mm, certification
                    ORDER BY volume_mt DESC
                    LIMIT 5
                """, (src_country, dest_country, f"%{fruit}%", date_filter))

                products = []
                for row in cursor.fetchall():
                    products.append({
                        "format": row[0],
                        "size": row[1],
                        "certification": row[2],
                        "volume_mt": round(row[3], 2),
                        "avg_price_usd_per_mt_fob": round(row[4], 2),
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
                      AND source_country = ?
                      AND destination_country_en = ?
                      AND fruit_name LIKE ?
                      AND net_weight_mt > 0
                      AND Date >= ?
                    GROUP BY certification
                """, (src_country, dest_country, f"%{fruit}%", date_filter))

                for row in cursor.fetchall():
                    cert_type = row[0]
                    cert_volume = row[1]
                    cert_price = row[2]
                    cert_pct = (cert_volume / volume_mt * 100) if volume_mt > 0 else 0

                    cert_split[cert_type] = {
                        "volume_mt": round(cert_volume, 2),
                        "percentage": round(cert_pct, 2),
                        "avg_price_usd_per_mt_fob": round(cert_price, 2)
                    }

                country_analysis["product_breakdown"] = {
                    "top_products": products,
                    "certification_split": cert_split,
                    "organic_percentage": round(cert_split.get('organic', {}).get('percentage', 0), 2)
                }

            # Supplier analysis
            supplier_hhi = 0
            if include_supplier_analysis:
                cursor.execute("""
                    SELECT
                        Exporter,
                        SUM(net_weight_mt) as volume_mt,
                        AVG(usd_per_mt_fob) as avg_price,
                        COUNT(*) as shipments
                    FROM exports
                    WHERE region = 'Europe'
                      AND source_country = ?
                      AND destination_country_en = ?
                      AND fruit_name LIKE ?
                      AND net_weight_mt > 0
                      AND Date >= ?
                    GROUP BY Exporter
                    ORDER BY volume_mt DESC
                """, (src_country, dest_country, f"%{fruit}%", date_filter))

                suppliers = cursor.fetchall()

                # Calculate HHI
                supplier_volumes = [s[1] for s in suppliers]
                if supplier_volumes:
                    supplier_shares = [v / sum(supplier_volumes) for v in supplier_volumes]
                    supplier_hhi = calculate_hhi(supplier_shares)

                # Top 5 suppliers
                top_suppliers = []
                for i, sup in enumerate(suppliers[:5], 1):
                    sup_share = (sup[1] / volume_mt * 100) if volume_mt > 0 else 0
                    top_suppliers.append({
                        "rank": i,
                        "exporter": sup[0],
                        "volume_mt": round(sup[1], 2),
                        "market_share_pct": round(sup_share, 2),
                        "avg_price_usd_per_mt_fob": round(sup[2], 2),
                        "shipments": sup[3]
                    })

                country_analysis["supplier_analysis"] = {
                    "supplier_count": supplier_count,
                    "concentration_hhi": round(supplier_hhi, 2),
                    "concentration_level": "highly concentrated" if supplier_hhi > 2500 else "moderately concentrated" if supplier_hhi > 1500 else "competitive",
                    "top_suppliers": top_suppliers
                }

            # Market attractiveness scoring
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

            # Price score
            if avg_price > 3000:
                price_score = 25
            elif avg_price > 2500:
                price_score = 20
            elif avg_price > 2000:
                price_score = 15
            else:
                price_score = 10

            # Competition score
            if include_supplier_analysis:
                if supplier_hhi < 1500:
                    competition_score = 25
                elif supplier_hhi < 2500:
                    competition_score = 15
                else:
                    competition_score = 5
            else:
                competition_score = 15

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
                organic_score = 10

            attractiveness_score = size_score + price_score + competition_score + organic_score

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

        results_by_source_country[src_country] = {
            "summary": {
                "total_europe_volume_mt": round(total_volume, 2),
                "total_europe_value_usd": round(total_value, 2),
                "avg_europe_price_usd_per_mt_fob": round(total_value / total_volume, 2) if total_volume > 0 else 0,
                "countries_analyzed": len(country_analyses),
                "priority_breakdown": {
                    "high_priority": sum(1 for c in country_analyses if c['market_attractiveness']['priority'] == 'high'),
                    "medium_priority": sum(1 for c in country_analyses if c['market_attractiveness']['priority'] == 'medium'),
                    "low_priority": sum(1 for c in country_analyses if c['market_attractiveness']['priority'] == 'low')
                },
                "top_3_markets": [
                    {
                        "country": c['destination_country'],
                        "volume_mt": c['market_metrics']['volume_mt'],
                        "market_share_pct": c['market_metrics']['market_share_volume_pct'],
                        "attractiveness_score": c['market_attractiveness']['score']
                    }
                    for c in country_analyses[:3]
                ]
            },
            "country_analyses": country_analyses
        }

    conn.close()

    return {
        "fruit": fruit,
        "analysis_period": start_date,
        "results_by_source_country": results_by_source_country
    }


def _analyze_country_multi_product_impl(
    target_country: str,
    products: List[Dict[str, str]],
    start_date: str = "ytd",
    use_neighbor_reference: bool = True,
    min_reference_market_size_mt: float = 20.0
) -> Dict[str, Any]:
    """Implementation of multi-product country analysis."""
    from translations import translate_country_to_english, translate_country_to_spanish

    conn = get_db_connection()
    cursor = conn.cursor()

    # Parse date
    parsed_start = parse_relative_date(start_date)
    if not parsed_start:
        parsed_start = parse_relative_date("ytd")
    date_filter = parsed_start.strftime('%Y-%m-%d')

    # Normalize target country name
    target_country_normalized = translate_country_to_english(target_country)
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

        # Build product description
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

        # Query target country BY SOURCE COUNTRY
        cursor.execute(f"""
            SELECT
                source_country,
                COUNT(*) as shipment_count,
                SUM(net_weight_mt) as total_mt,
                SUM([U$ FOB Tot]) as total_fob_usd,
                AVG(usd_per_mt_fob) as avg_usd_per_mt
            FROM exports
            WHERE "Destination Country" = ?
              AND {product_where_sql}
              AND net_weight_mt > 0
            GROUP BY source_country
        """, [target_country_spanish] + product_params)

        target_data_by_country = {row[0]: {
            "shipment_count": row[1],
            "volume_mt": row[2],
            "fob_value_usd": row[3],
            "avg_price_usd_per_mt_fob": row[4]
        } for row in cursor.fetchall()}

        product_analysis = {
            "product": product_description,
            "product_specs": product,
            "target_country": target_country_normalized
        }

        # If target country has data
        if target_data_by_country:
            product_analysis["target_market_by_source_country"] = {}
            for src_country, data in target_data_by_country.items():
                product_analysis["target_market_by_source_country"][src_country] = {
                    "status": "active",
                    "volume_mt": round(data["volume_mt"], 2),
                    "fob_value_usd": round(data["fob_value_usd"], 2) if data["fob_value_usd"] else 0,
                    "shipment_count": data["shipment_count"],
                    "avg_price_usd_per_mt_fob": round(data["avg_price_usd_per_mt_fob"], 2) if data["avg_price_usd_per_mt_fob"] else 0,
                }

        # If no target country data, reference neighbors
        elif use_neighbor_reference and neighbors:
            neighbor_markets = _analyze_neighbor_markets_by_source(
                cursor, neighbors, product_where_sql, product_params,
                min_reference_market_size_mt
            )

            if neighbor_markets:
                product_analysis["target_market_by_source_country"] = {
                    "status": "no_imports",
                    "message": f"No {product_description} imports found in {target_country_normalized}"
                }
                product_analysis["reference_markets"] = neighbor_markets
            else:
                product_analysis["target_market_by_source_country"] = {
                    "status": "no_imports",
                    "message": f"No {product_description} imports found in Europe"
                }
        else:
            product_analysis["target_market_by_source_country"] = {
                "status": "no_imports",
                "message": f"No {product_description} imports found in {target_country_normalized}"
            }

        product_analyses.append(product_analysis)

    conn.close()

    # Summary
    active_products = sum(1 for p in product_analyses
                         if isinstance(p.get('target_market_by_source_country'), dict)
                         and any(v.get('status') == 'active' for v in p.get('target_market_by_source_country', {}).values()
                                if isinstance(v, dict)))
    no_import_products = len(product_analyses) - active_products
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


def _analyze_neighbor_markets_by_source(cursor, neighbors, product_where_sql, product_params, min_size_mt):
    """Analyze neighboring country markets for a product, BY SOURCE COUNTRY."""
    from translations import translate_country_to_spanish

    neighbor_markets_by_source = {}

    for neighbor in neighbors:
        neighbor_spanish = translate_country_to_spanish(neighbor)

        cursor.execute(f"""
            SELECT
                source_country,
                COUNT(*) as shipment_count,
                SUM(net_weight_mt) as total_mt,
                SUM([U$ FOB Tot]) as total_fob_usd,
                AVG(usd_per_mt_fob) as avg_usd_per_mt
            FROM exports
            WHERE "Destination Country" = ?
              AND {product_where_sql}
              AND net_weight_mt >= ?
            GROUP BY source_country
        """, [neighbor_spanish] + product_params + [min_size_mt])

        for row in cursor.fetchall():
            src_country = row[0]
            if src_country not in neighbor_markets_by_source:
                neighbor_markets_by_source[src_country] = []

            neighbor_markets_by_source[src_country].append({
                "country": neighbor,
                "volume_mt": round(row[2], 2),
                "fob_value_usd": round(row[3], 2) if row[3] else 0,
                "shipment_count": row[1],
                "avg_price_usd_per_mt_fob": round(row[4], 2) if row[4] else 0
            })

    # Sort each source country's markets by volume
    for src_country in neighbor_markets_by_source:
        neighbor_markets_by_source[src_country].sort(key=lambda x: x['volume_mt'], reverse=True)

    if neighbor_markets_by_source:
        return {
            "search_type": "immediate_neighbors",
            "by_source_country": neighbor_markets_by_source
        }
    return None


def _generate_overall_recommendation(country: str, active: int, no_imports: int, references: int) -> str:
    """Generate overall market recommendation."""
    total = active + no_imports

    if total == 0:
        return "No products analyzed."

    active_pct = (active / total * 100) if total > 0 else 0

    if active_pct > 70:
        return f"{country} is an active market for most products analyzed ({active}/{total}). Strong market presence."
    elif active_pct > 40:
        return f"{country} shows moderate activity ({active}/{total} products). Mixed market."
    elif references > 0:
        return f"{country} has limited current imports ({active}/{total}), but neighboring countries show demand."
    else:
        return f"{country} shows minimal activity for these products."


@mcp.tool()
def analyze_europe_by_fruit(
    fruit: str,
    source_country: Optional[str] = None,
    start_date: str = "ytd",
    min_market_size_mt: float = 10.0,
    include_product_breakdown: bool = True,
    include_price_analysis: bool = True,
    include_supplier_analysis: bool = True
) -> Dict[str, Any]:
    """
    Comprehensive European country-by-country analysis for a specific fruit.

    IMPORTANT: Results are always separated by source country (Peru vs Ecuador).
    Prices are always shown as USD/MT FOB with source country context.

    Analyzes each European country showing:
    - Market size (volume and value)
    - Market share of Europe total
    - Average pricing and price ranges (USD/MT FOB)
    - Supplier concentration (HHI)
    - Product mix (formats, sizes, certifications)
    - Organic vs conventional split
    - Top exporters per country
    - Market attractiveness scoring

    Args:
        fruit: Fruit type to analyze (e.g., 'mango', 'blueberry', 'avocado')
        source_country: Filter by source country ('peru' or 'ecuador')
        start_date: Analysis period (default 'ytd')
        min_market_size_mt: Minimum market size to include (default 10 MT)
        include_product_breakdown: Show format/size/certification breakdown
        include_price_analysis: Include price statistics and ranges
        include_supplier_analysis: Show supplier concentration and top exporters

    Returns:
        Detailed analysis separated by source country, with each country's data
        showing destination countries sorted by market attractiveness
    """
    return _analyze_europe_by_fruit_impl(
        fruit, source_country, start_date, min_market_size_mt,
        include_product_breakdown, include_price_analysis, include_supplier_analysis
    )


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

    IMPORTANT: Results are always separated by source country (Peru vs Ecuador).
    Prices are always shown as USD/MT FOB with source country and destination country context.

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
        Analysis for each product showing data separated by source country (Peru/Ecuador)
    """
    return _analyze_country_multi_product_impl(
        target_country, products, start_date,
        use_neighbor_reference, min_reference_market_size_mt
    )


# Export implementations for use by main module
analyze_europe_by_fruit_impl = _analyze_europe_by_fruit_impl
analyze_country_multi_product_impl = _analyze_country_multi_product_impl


if __name__ == "__main__":
    mcp.run()
