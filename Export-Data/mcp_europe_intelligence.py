"""
Europe Market Intelligence Tools for Frozen Fruit Export MCP Server.
Specialized tools for European market entry analysis and gap identification.
Supports: Peru, Ecuador

IMPORTANT: All results are separated by source country (Peru vs Ecuador).
Prices are always shown as USD/MT FOB with source country, destination country, and fruit context.

This module re-exports tools from specialized sub-modules:
- mcp_europe_readiness: Exporter readiness assessment
- mcp_europe_gaps: Market gap identification
- mcp_europe_benchmark: Competitive benchmarking
- mcp_europe_analysis: Country and multi-product analysis

Each sub-module can also be run independently as an MCP server.
"""
import fastmcp
from typing import Dict, Any, Optional, List

# Create main server
mcp = fastmcp.FastMCP("Frozen Fruit Exports - Europe Intelligence")

# Import implementations from sub-modules
from mcp_europe_readiness import analyze_europe_readiness_impl
from mcp_europe_gaps import identify_market_gaps_impl
from mcp_europe_benchmark import benchmark_europe_competitors_impl
from mcp_europe_analysis import (
    analyze_europe_by_fruit_impl,
    analyze_country_multi_product_impl,
    EUROPEAN_NEIGHBORS
)


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
    - Price positioning vs European competitors (USD/MT FOB)
    - Compliance readiness indicators

    Args:
        exporter_name: Company name (fuzzy match supported)
        source_country: Filter by source country ('peru' or 'ecuador')
        start_date: Analysis period (default 'ytd')

    Returns:
        Comprehensive Europe readiness assessment with scores
    """
    return analyze_europe_readiness_impl(exporter_name, source_country, start_date)


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
    - Premium pricing opportunities (USD/MT FOB)
    - Low competition intensity
    - Seasonal supply gaps

    IMPORTANT: Results are always separated by source country (Peru vs Ecuador).

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
    return identify_market_gaps_impl(
        target_country, product_category, source_country,
        min_market_size_mt, max_suppliers, start_date
    )


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
    return benchmark_europe_competitors_impl(
        exporter_name, source_country, fruit, certification, start_date
    )


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

    Perfect for answering: "Show me what each European country looks like for mangoes"

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
    return analyze_europe_by_fruit_impl(
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
        Analysis for each product showing data separated by source country (Peru/Ecuador)

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
    return analyze_country_multi_product_impl(
        target_country, products, start_date,
        use_neighbor_reference, min_reference_market_size_mt
    )


if __name__ == "__main__":
    mcp.run()
