"""
Peru Frozen Fruit Exports - MCP Server (Coherent Architecture)

Uses the unified analytics system with:
- Exporter normalization (core/exporter_mapping.py)
- Data quality filters (core/filters.py)
- Quartile pricing engine (analysis/pricing.py)
- Database utilities (core/database.py)

CRITICAL INSTRUCTIONS FOR LLM:
- ONLY use data explicitly returned by these tools
- DO NOT infer, extrapolate, or create hypothetical data
- DO NOT make recommendations beyond what the data directly shows
- If data is missing, state "Data not available" - do NOT fill gaps
- Stick to descriptive statistics and direct observations from query results
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import fastmcp
from typing import Optional, List, Dict, Any
import pandas as pd

# Import coherent modules
from core.database import (
    get_connection,
    execute_query,
    get_fruit_types,
    get_exporters,
    get_format_types,
    get_table_stats,
)
from core.exporter_mapping import get_canonical_name, get_all_mappings
from analysis.pricing import (
    calculate_pricing_summary,
    calculate_pricing_drill_down,
)

# Import cache if available
try:
    from mcp_tools.cache import get_cache
    cache = get_cache()
    CACHE_ENABLED = True
except ImportError:
    CACHE_ENABLED = False
    cache = None

# Initialize MCP server
mcp = fastmcp.FastMCP("Peru Frozen Fruit Exports - Coherent")


# ============================================================================
# MCP PROMPTS - Multi-Tool Workflows for Complex Analysis
# ============================================================================
# These prompts guide LLMs through comprehensive analysis workflows that
# combine multiple tools for deep insights.

@mcp.prompt()
def market_entry_analysis() -> str:
    """
    Complete market entry analysis workflow.

    Use this workflow when analyzing opportunities for entering a market with
    a specific fruit product. This combines discovery, pricing, supplier, and
    format analysis.
    """
    return """# Market Entry Analysis Workflow

This workflow helps analyze opportunities for entering a market with a specific fruit product.

## Step 1: Discover Available Data
**Tool:** `get_available_values()`
- Identify all available fruits, exporters, and formats
- Get database statistics and coverage

## Step 2: Get Fruit Pricing Overview
**Tool:** `get_fruit_pricing_summary(region='Europe', limit=20)`
- Understand pricing landscape across all fruits
- Identify high-value vs commodity fruits
- Look at Q1, Median, Q3 pricing to understand price ranges

## Step 3: Analyze Specific Fruit Suppliers
**Tool:** `drill_fruit_by_exporter(fruit_name='mango', region='Europe')`
- Identify who is shipping this fruit
- Compare their pricing positions (Q1/Median/Q3)
- Look at volume levels to assess market concentration

## Step 4: Evaluate Supplier Portfolios
**Tool:** `drill_exporter_by_fruit(exporter_name='Viru', region='Europe')`
- For top suppliers, check their fruit portfolio
- Assess their specialization vs diversification
- Identify potential partners or competitors

## Step 5: Understand Format Options
**Tool:** `drill_fruit_by_format(fruit_name='mango', region='Europe')`
- See which formats are available (chunks, puree, etc.)
- Understand pricing by format
- Identify format opportunities

## Step 6: Compare Regional Pricing
**Repeat tools from Steps 2-5 with `region='RoW'`**
- Compare Europe vs Rest of World pricing
- Identify regional arbitrage opportunities

## Key Insights to Extract:
- Price positioning opportunity (enter at Q1, Median, or Q3?)
- Supplier landscape (concentrated vs fragmented?)
- Format preferences (what sells best?)
- Regional differences (where's the opportunity?)

## Data Quality Note:
All data uses clean, filtered records:
- No air freight (sea only)
- No samples or zero-value shipments
- Minimum 0.1 MT shipments
- IQR outlier removal per fruit
- 75.4% data retention rate (8,361 of 11,098 YTD records)
"""


@mcp.prompt()
def exporter_competitive_profile() -> str:
    """
    Comprehensive exporter competitive analysis workflow.

    Use this when analyzing a specific exporter's competitive position,
    portfolio strategy, and market positioning.
    """
    return """# Exporter Competitive Profile Workflow

Analyze an exporter's competitive position and strategic portfolio.

## Step 1: Find the Exporter
**Tool:** `search_exporters(query='viru')`
- Search for exporter by partial name
- Get canonical normalized name
- See name variation examples

## Step 2: Analyze Exporter Portfolio
**Tool:** `drill_exporter_by_fruit(exporter_name='Viru', region='Europe')`
- Get complete fruit portfolio
- See pricing by fruit (Q1/Median/Q3)
- Assess portfolio diversity score (High/Medium/Low)
- Identify top fruit by volume

## Step 3: Compare Against Market
**Tool:** `get_exporter_pricing_summary(region='Europe', limit=20)`
- See where this exporter ranks by volume
- Compare pricing position vs peers
- Understand competitive landscape

## Step 4: Analyze Top Fruit Competition
**Tool:** `drill_fruit_by_exporter(fruit_name='mango', region='Europe')`
(Use exporter's top fruit from Step 2)
- See who else ships this fruit
- Compare pricing strategies
- Assess market share for this fruit

## Optional Step 5: Regional Comparison
**Repeat Steps 2-4 with `region='RoW'`**
- Compare Europe vs Rest of World strategy
- Identify regional specialization

## Key Insights to Extract:
- Portfolio strategy (specialist vs generalist?)
- Pricing position (premium vs value?)
- Market rank (leader vs challenger?)
- Fruit specialization (which fruits drive volume?)
- Geographic focus (Europe vs RoW?)

## Exporter Name Normalization:
- Names are automatically normalized (e.g., VIRU → Viru)
- Variations consolidated (e.g., 2 variations → 1 canonical)
- Example: Viru = 2,640 shipments from 2 name variations
"""


@mcp.prompt()
def product_pricing_strategy() -> str:
    """
    Multi-dimensional pricing strategy analysis workflow.

    Use this when developing pricing strategy for a fruit product,
    considering format, supplier, and regional variations.
    """
    return """# Product Pricing Strategy Workflow

Develop comprehensive pricing strategy for a fruit product.

## Step 1: Get Fruit Market Pricing
**Tool:** `get_fruit_pricing_summary(region='Europe', limit=20)`
- Understand overall fruit pricing landscape
- Identify where target fruit ranks
- Note Q1/Median/Q3 spreads

## Step 2: Analyze Format Pricing
**Tool:** `drill_fruit_by_format(fruit_name='mango', region='Europe')`
- See pricing by format (chunks, puree, etc.)
- Identify premium vs commodity formats
- Understand volume by format

## Step 3: Analyze Supplier Pricing
**Tool:** `drill_fruit_by_exporter(fruit_name='mango', region='Europe')`
- See pricing distribution across suppliers
- Identify price leaders and followers
- Understand competitive pricing ranges

## Step 4: Cross-Reference Format Pricing
**Tool:** `get_format_pricing_summary(region='Europe')`
- Get overall format pricing benchmarks
- Compare target fruit formats vs market averages
- Identify format premiums/discounts

## Optional Step 5: Regional Pricing Comparison
**Repeat Steps 1-4 with `region='RoW'`**
- Compare Europe vs Rest of World pricing
- Identify regional pricing opportunities
- Understand geographic arbitrage potential

## Key Insights to Extract:
- Optimal pricing position (Q1/Median/Q3?)
- Format premiums (which format commands highest price?)
- Supplier benchmarks (what are competitors charging?)
- Regional differences (where's the pricing power?)
- Price-volume relationships (premium vs volume play?)

## Pricing Method - Quartiles:
- **Q1 (25th percentile):** Lower-priced segment
- **Median (50th percentile):** Market middle
- **Q3 (75th percentile):** Premium segment
- **Why quartiles?** Eliminates outlier distortion vs min/max
- **Application:** Calculated per fruit with IQR filtering
"""


@mcp.prompt()
def supplier_discovery() -> str:
    """
    Supplier discovery and evaluation workflow.

    Use this when searching for potential suppliers of a specific fruit,
    evaluating their capabilities and reliability.
    """
    return """# Supplier Discovery & Evaluation Workflow

Find and evaluate potential suppliers for a specific fruit.

## Step 1: Search for Relevant Exporters
**Tool:** `search_exporters(query='partial_name')`
OR
**Tool:** `get_available_values()`
- Get list of all exporters in database
- Search by partial name if you have leads
- Note: Names are normalized (VIRU → Viru)

## Step 2: Identify Suppliers by Fruit
**Tool:** `drill_fruit_by_exporter(fruit_name='mango', region='Europe')`
- Get all exporters shipping this fruit
- See volume levels (YTD MT)
- Compare pricing positions (Q1/Median/Q3)
- Assess supplier concentration

## Step 3: Evaluate Top Supplier Portfolios
**Tool:** `drill_exporter_by_fruit(exporter_name='Viru', region='Europe')`
(Repeat for top 3-5 suppliers from Step 2)
- Check portfolio diversity
- See if supplier is specialist or generalist
- Assess their volume capacity
- Compare pricing across their portfolio

## Step 4 (Optional): Reverse Check
**Tool:** `drill_fruit_by_exporter(fruit_name='avocado', region='Europe')`
(Use a different fruit to cross-validate)
- Check if same suppliers appear
- Assess their multi-fruit capabilities
- Validate consistency

## Key Evaluation Criteria:
- **Volume capacity:** YTD MT shipped
- **Pricing position:** Q1/Median/Q3 relative to market
- **Specialization:** Portfolio diversity score
- **Geographic reach:** Europe vs RoW presence
- **Consistency:** Show up across multiple fruits?

## Supplier Categories:
- **Specialists:** Low diversity (1-2 fruits), high volume
- **Diversified:** Medium diversity (3-4 fruits), balanced
- **Generalists:** High diversity (5+ fruits), broad portfolio

## Data Quality Assurance:
- All suppliers use normalized names (57 variations → 48 canonical)
- Example: Viru consolidates 2 name variations, 2,640 shipments
- Clean data only (no air freight, samples, outliers)
"""


@mcp.prompt()
def format_optimization() -> str:
    """
    Product format optimization analysis workflow.

    Use this when deciding which product format to use or analyzing
    format profitability and market preferences.
    """
    return """# Format Optimization Analysis Workflow

Optimize product format selection for maximum profitability.

## Step 1: Get Format Market Overview
**Tool:** `get_format_pricing_summary(region='Europe')`
- See all available formats
- Understand pricing ranges by format
- Identify volume levels by format
- Note Q1/Median/Q3 for each format

## Step 2: Analyze Target Fruit Formats
**Tool:** `drill_fruit_by_format(fruit_name='mango', region='Europe')`
- See which formats are used for this fruit
- Compare pricing across formats
- Assess volume distribution

## Step 3: Compare Against Overall Market
**Tool:** `get_fruit_pricing_summary(region='Europe', limit=20)`
- Get pricing for the target fruit overall
- Compare to format-specific pricing from Step 2
- Identify format premiums/discounts

## Step 4 (Optional): Cross-Check with Suppliers
**Tool:** `drill_fruit_by_exporter(fruit_name='mango', region='Europe')`
- See which suppliers offer which formats
- Assess supplier concentration by format
- Identify format availability

## Optional Step 5: Regional Comparison
**Repeat Steps 1-2 with `region='RoW'`**
- Compare Europe vs Rest of World format preferences
- Identify regional format opportunities

## Key Insights to Extract:
- **Format premiums:** Which formats command highest prices?
- **Volume preferences:** Which formats have highest demand?
- **Competition:** Which formats are crowded vs underserved?
- **Regional differences:** Format preferences by region?
- **Supplier availability:** Can you source desired format?

## Common Format Types:
- Chunks (IQF)
- Cubes
- Dices
- Slices
- Puree
- Halves
- Whole fruit (IQF)

## Format Pricing Insights:
- Value-added formats (dices, specific cuts) often command premiums
- Bulk formats (puree) often lower $/MT but higher volume
- IQF (Individual Quick Frozen) formats vary by specificity
"""


@mcp.prompt()
def regional_market_intelligence() -> str:
    """
    Regional market comparison and intelligence workflow.

    Use this when comparing markets across regions (Europe vs Rest of World)
    to identify geographic opportunities and regional strategies.
    """
    return """# Regional Market Intelligence Workflow

Compare markets across regions to identify geographic opportunities.

## Step 1: Europe Market Analysis
**Tool:** `get_fruit_pricing_summary(region='Europe', limit=20)`
- Get Europe fruit pricing landscape
- Note top fruits by volume
- Identify pricing ranges (Q1/Median/Q3)

## Step 2: Rest of World Market Analysis
**Tool:** `get_fruit_pricing_summary(region='RoW', limit=20)`
- Get Rest of World pricing landscape
- Compare fruit mix vs Europe
- Identify pricing differences

## Step 3: Deep Dive on Target Fruit - Europe
**Tool:** `drill_fruit_by_exporter(fruit_name='mango', region='Europe')`
- Analyze Europe suppliers for target fruit
- Note volume concentration
- Assess pricing competition

## Step 4: Deep Dive on Target Fruit - RoW
**Tool:** `drill_fruit_by_exporter(fruit_name='mango', region='RoW')`
- Analyze RoW suppliers for same fruit
- Compare to Europe patterns
- Identify geographic arbitrage opportunities

## Optional Step 5: Exporter Regional Strategy
**Tool:** `drill_exporter_by_fruit(exporter_name='Viru', region='Europe')`
**Tool:** `drill_exporter_by_fruit(exporter_name='Viru', region='RoW')`
- Compare exporter's portfolio across regions
- Identify regional specialization
- Assess geographic diversification

## Key Insights to Extract:
- **Pricing arbitrage:** Where are prices higher for same fruit?
- **Market maturity:** Europe vs RoW demand patterns
- **Supplier concentration:** More competitive in which region?
- **Product mix:** Different fruit preferences by region?
- **Exporter strategies:** Regional specialists vs global players?

## Regional Definitions:
- **Europe:** 20 countries (EU + UK, Norway, Switzerland, etc.)
- **Rest of World (RoW):** 37 countries (Asia, Middle East, Americas, etc.)
- **Total coverage:** 57 destination countries

## Interpretation Guide:
- **Higher Europe pricing:** Often indicates quality/certification premiums
- **Higher RoW pricing:** May indicate emerging market demand
- **Price convergence:** Commodity fruit with global market
- **Price divergence:** Regional preferences or quality differences
"""


# ============================================================================
# PRICING ANALYTICS TOOLS (using coherent pricing engine)
# ============================================================================

@mcp.tool()
def get_fruit_pricing_summary(
    region: Optional[str] = None,
    limit: int = 20
) -> Dict[str, Any]:
    """
    Get quartile pricing summary for all fruits.

    Returns Q1/Median/Q3 prices (USD/MT FOB) and YTD volume (MT) for each fruit.
    Uses clean, filtered data (no air freight, samples, or outliers).

    Args:
        region: Filter by region ('Europe' or 'RoW'). Default: worldwide.
        limit: Maximum number of fruits to return. Default: 20.

    Returns:
        Dictionary with:
        - fruits: List of fruit pricing summaries
        - total_fruits: Total number of fruits
        - data_period: Date range
        - filters_applied: List of quality filters

    Example Usage:
        # Get top 20 fruits worldwide
        get_fruit_pricing_summary(limit=20)

        # Get European market pricing
        get_fruit_pricing_summary(region='Europe', limit=15)

        # Get Rest of World pricing
        get_fruit_pricing_summary(region='RoW', limit=10)

    Output Interpretation:
        - Q1 (25th percentile): Lower-priced segment, value positioning
        - Median (50th): Middle market pricing, most common
        - Q3 (75th percentile): Premium segment, higher quality
        - YTD MT: Total volume shipped year-to-date (market size indicator)

    Common Workflows:
        1. Market Entry: Start here to understand fruit landscape → drill_fruit_by_exporter
        2. Pricing Strategy: Compare fruits → drill_fruit_by_format for detail
        3. Regional Comparison: Call with region='Europe', then region='RoW'

    Related Tools:
        - drill_fruit_by_exporter: Drill down to see who ships specific fruits
        - drill_fruit_by_format: See format options for specific fruits
        - get_exporter_pricing_summary: Compare with exporter landscape
    """
    df = calculate_pricing_summary(dimension='fruit', region=region)

    fruits = df.head(limit).to_dict('records')

    return {
        "fruits": fruits,
        "total_fruits": len(df),
        "data_period": "YTD Oct 2024 - Oct 2025",
        "filters_applied": [
            "No air freight",
            "No samples or zero-value shipments",
            "Minimum 0.1 MT (100 kg)",
            "IQR outlier removal per fruit",
            "Valid pricing data only"
        ],
        "pricing_method": "Quartiles (Q1/Median/Q3) to avoid outlier distortion"
    }


@mcp.tool()
def get_exporter_pricing_summary(
    region: Optional[str] = None,
    limit: int = 20
) -> Dict[str, Any]:
    """
    Get quartile pricing summary for all exporters.

    Returns Q1/Median/Q3 prices, fruit count, and YTD volume for each exporter.
    Exporter names are normalized (e.g., VIRU variations consolidated).

    Args:
        region: Filter by region ('Europe' or 'RoW'). Default: worldwide.
        limit: Maximum number of exporters to return. Default: 20.

    Returns:
        Dictionary with:
        - exporters: List of exporter pricing summaries (with fruit count)
        - total_exporters: Total number of unique exporters
        - top_exporter: Largest exporter by volume
        - normalization_note: Info about name consolidation

    Example Usage:
        # Get top 20 exporters worldwide
        get_exporter_pricing_summary(limit=20)

        # Identify top European suppliers
        get_exporter_pricing_summary(region='Europe', limit=10)

        # Compare top exporters to Rest of World
        get_exporter_pricing_summary(region='RoW', limit=10)

    Output Interpretation:
        - Fruit Count: Number of different fruits this exporter ships (diversity)
        - YTD MT: Total volume → market power indicator
        - Q1/Median/Q3: Pricing strategy (value vs premium)
        - Low fruit count + high volume = Specialist
        - High fruit count = Diversified/Generalist

    Common Workflows:
        1. Competitive Intelligence: Identify leaders → drill_exporter_by_fruit for detail
        2. Supplier Discovery: Find exporters → drill_exporter_by_fruit to evaluate
        3. Market Share: Compare volumes, identify concentration

    Related Tools:
        - drill_exporter_by_fruit: Deep dive into specific exporter's portfolio
        - search_exporters: Find specific exporters by name
        - drill_fruit_by_exporter: See competition for specific fruits
    """
    df = calculate_pricing_summary(dimension='exporter', region=region)

    exporters = df.head(limit).to_dict('records')
    top = exporters[0] if exporters else None

    return {
        "exporters": exporters,
        "total_exporters": len(df),
        "top_exporter": top,
        "data_period": "YTD Oct 2024 - Oct 2025",
        "normalization_note": "Exporter names normalized (e.g., Viru: 2,640 shipments from 2 variations)"
    }


@mcp.tool()
def get_format_pricing_summary(
    region: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get quartile pricing summary for all product formats.

    Returns Q1/Median/Q3 prices and YTD volume for each format type.

    Args:
        region: Filter by region ('Europe' or 'RoW'). Default: worldwide.

    Returns:
        Dictionary with:
        - formats: List of format pricing summaries
        - total_formats: Total number of unique formats

    Example Usage:
        # Get all format pricing worldwide
        get_format_pricing_summary()

        # European format preferences
        get_format_pricing_summary(region='Europe')

        # Rest of World format pricing
        get_format_pricing_summary(region='RoW')

    Output Interpretation:
        - Higher Q3/Median ratio: Premium format with quality variation
        - High YTD MT: Popular/commodity format
        - Low YTD MT but high pricing: Niche/specialized format
        - Common formats: chunks, dices, puree, slices, halves

    Common Workflows:
        1. Format Optimization: Compare formats → drill_fruit_by_format for specific fruit
        2. Product Development: Identify premium formats → drill_fruit_by_format
        3. Market Gaps: Find low-volume, high-price formats

    Related Tools:
        - drill_fruit_by_format: See which formats are used for specific fruits
        - drill_fruit_by_exporter: Check supplier format capabilities
        - get_fruit_pricing_summary: Compare format pricing to overall fruit pricing
    """
    df = calculate_pricing_summary(dimension='format', region=region)

    return {
        "formats": df.to_dict('records'),
        "total_formats": len(df),
        "data_period": "YTD Oct 2024 - Oct 2025"
    }


@mcp.tool()
def drill_fruit_by_exporter(
    fruit_name: str,
    region: Optional[str] = None,
    limit: int = 20
) -> Dict[str, Any]:
    """
    Get pricing breakdown for a specific fruit by exporter.

    Shows which exporters ship this fruit and their pricing.

    Args:
        fruit_name: Name of the fruit (e.g., 'mango', 'avocado')
        region: Filter by region ('Europe' or 'RoW'). Default: worldwide.
        limit: Maximum number of exporters to return. Default: 20.

    Returns:
        Dictionary with:
        - fruit: Fruit name
        - exporters: List of exporters with pricing for this fruit
        - total_exporters: Number of exporters shipping this fruit

    Example Usage:
        # Who ships mangoes worldwide?
        drill_fruit_by_exporter(fruit_name='mango')

        # European mango suppliers
        drill_fruit_by_exporter(fruit_name='mango', region='Europe', limit=10)

        # Top 5 avocado exporters to Europe
        drill_fruit_by_exporter(fruit_name='avocado', region='Europe', limit=5)

    Output Interpretation:
        - Many exporters (>10): Competitive/fragmented market
        - Few exporters (<5): Concentrated market, higher barriers
        - Wide Q1-Q3 spread: Quality/brand differentiation
        - Narrow Q1-Q3 spread: Commodity market, price competition
        - Use volume (YTD MT) to identify market leaders

    Common Workflows:
        1. Supplier Discovery: Find suppliers → drill_exporter_by_fruit for portfolio check
        2. Competitive Analysis: Identify competitors → compare pricing positions
        3. Market Entry: Assess competition level and pricing strategies

    Related Tools:
        - drill_exporter_by_fruit: Reverse view - get exporter's full portfolio
        - get_fruit_pricing_summary: Get overall fruit pricing first
        - drill_fruit_by_format: Cross-reference with format analysis
    """
    df = calculate_pricing_drill_down(
        filter_dimension='fruit',
        filter_value=fruit_name,
        by='exporter',
        region=region
    )

    if len(df) == 0:
        return {
            "error": f"No data found for fruit '{fruit_name}'",
            "suggestion": "Check spelling or try: " + ", ".join(get_fruit_types()[:5])
        }

    return {
        "fruit": fruit_name,
        "exporters": df.head(limit).to_dict('records'),
        "total_exporters": len(df),
        "data_period": "YTD Oct 2024 - Oct 2025"
    }


@mcp.tool()
def drill_exporter_by_fruit(
    exporter_name: str,
    region: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get pricing breakdown for a specific exporter by fruit.

    Shows which fruits this exporter ships and their pricing.
    Exporter name will be normalized automatically (e.g., VIRU → Viru).

    Args:
        exporter_name: Name of the exporter (fuzzy matching supported)
        region: Filter by region ('Europe' or 'RoW'). Default: worldwide.

    Returns:
        Dictionary with:
        - exporter: Canonical exporter name
        - fruits: List of fruits with pricing
        - total_fruits: Number of fruit types
        - portfolio_diversity: Analysis of product range

    Example Usage:
        # Analyze Viru's complete portfolio
        drill_exporter_by_fruit(exporter_name='Viru')

        # Check exporter's European portfolio only
        drill_exporter_by_fruit(exporter_name='Camposol', region='Europe')

        # Fuzzy matching works (VIRU → Viru automatically)
        drill_exporter_by_fruit(exporter_name='VIRU')

    Output Interpretation:
        - Portfolio Diversity Score:
          * High (5+ fruits): Diversified generalist
          * Medium (3-4 fruits): Balanced portfolio
          * Low (1-2 fruits): Specialist/focused
        - Top Fruit Share %: Concentration risk indicator
        - Total Volume: Overall capacity/scale
        - Use to assess: Specialization vs diversification strategy

    Common Workflows:
        1. Exporter Profile: Start here → drill_fruit_by_exporter for market context
        2. Partnership Evaluation: Check portfolio → compare to get_exporter_pricing_summary rankings
        3. Competitive Intelligence: Analyze portfolio → identify specialization

    Related Tools:
        - search_exporters: Find exporter name first if unsure
        - drill_fruit_by_exporter: See who else ships their top fruits (competition)
        - get_exporter_pricing_summary: Compare to overall exporter rankings
    """
    # Normalize exporter name
    canonical_name = get_canonical_name(exporter_name)

    df = calculate_pricing_drill_down(
        filter_dimension='exporter',
        filter_value=canonical_name,
        by='fruit',
        region=region
    )

    if len(df) == 0:
        return {
            "error": f"No data found for exporter '{exporter_name}' (normalized to '{canonical_name}')",
            "suggestion": "Try a different name or check available exporters"
        }

    fruits_list = df.to_dict('records')
    total_volume = df['YTD MT'].sum()

    # Portfolio diversity analysis
    portfolio_analysis = {
        "fruit_count": len(df),
        "total_volume_mt": int(total_volume),
        "top_fruit": fruits_list[0]['Fruit'] if fruits_list else None,
        "top_fruit_share_pct": round((fruits_list[0]['YTD MT'] / total_volume * 100), 1) if fruits_list and total_volume > 0 else 0,
        "diversification": "High" if len(df) >= 5 else "Medium" if len(df) >= 3 else "Low"
    }

    return {
        "exporter": canonical_name,
        "original_query": exporter_name,
        "fruits": fruits_list,
        "total_fruits": len(df),
        "portfolio_diversity": portfolio_analysis,
        "data_period": "YTD Oct 2024 - Oct 2025"
    }


@mcp.tool()
def drill_fruit_by_format(
    fruit_name: str,
    region: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get pricing breakdown for a specific fruit by format.

    Shows which formats are used for this fruit and their pricing.

    Args:
        fruit_name: Name of the fruit (e.g., 'mango', 'avocado')
        region: Filter by region ('Europe' or 'RoW'). Default: worldwide.

    Returns:
        Dictionary with:
        - fruit: Fruit name
        - formats: List of formats with pricing
        - total_formats: Number of formats used

    Example Usage:
        # What formats are available for mango?
        drill_fruit_by_format(fruit_name='mango')

        # European strawberry format options
        drill_fruit_by_format(fruit_name='strawberry', region='Europe')

        # Compare avocado formats: Europe vs RoW
        drill_fruit_by_format(fruit_name='avocado', region='Europe')
        drill_fruit_by_format(fruit_name='avocado', region='RoW')

    Output Interpretation:
        - Format premiums: Compare Q3 prices across formats
        - Volume leaders: Highest YTD MT = most popular format
        - Niche formats: Low volume but high pricing
        - Value-added: Dices/specific cuts often command premiums
        - Bulk formats: Puree often lower $/MT but higher volume

    Common Workflows:
        1. Format Selection: See options → get_format_pricing_summary for benchmarks
        2. Product Development: Identify premium formats → drill_fruit_by_exporter for sourcing
        3. Pricing Strategy: Compare format pricing → choose positioning

    Related Tools:
        - get_format_pricing_summary: Get overall format pricing benchmarks
        - drill_fruit_by_exporter: Check which exporters offer desired formats
        - get_fruit_pricing_summary: Compare to overall fruit pricing
    """
    df = calculate_pricing_drill_down(
        filter_dimension='fruit',
        filter_value=fruit_name,
        by='format',
        region=region
    )

    if len(df) == 0:
        return {
            "error": f"No data found for fruit '{fruit_name}'",
            "suggestion": "Check spelling or try: " + ", ".join(get_fruit_types()[:5])
        }

    return {
        "fruit": fruit_name,
        "formats": df.to_dict('records'),
        "total_formats": len(df),
        "data_period": "YTD Oct 2024 - Oct 2025"
    }


# ============================================================================
# SEARCH & DISCOVERY TOOLS
# ============================================================================

@mcp.tool()
def search_exporters(
    query: Optional[str] = None,
    limit: int = 50
) -> Dict[str, Any]:
    """
    Search for exporters by name (supports partial matching).

    Returns canonical (normalized) exporter names.

    Args:
        query: Partial name to search for. If None, returns all exporters.
        limit: Maximum number of results. Default: 50.

    Returns:
        Dictionary with:
        - exporters: List of matching canonical exporter names
        - total_found: Number of matches
        - normalization_examples: Examples of name consolidation

    Example Usage:
        # Search for exporters with "vir" in name
        search_exporters(query='vir')

        # Get all available exporters (first 50)
        search_exporters()

        # Search with higher limit
        search_exporters(query='agro', limit=100)

    Output Interpretation:
        - Canonical names: Normalized versions (VIRU → Viru)
        - Normalization examples: Shows consolidation (2 variations → 1)
        - Use canonical name in other tools for consistency
        - Partial matching is case-insensitive

    Common Workflows:
        1. Discovery: Find exporter → drill_exporter_by_fruit for details
        2. Name Verification: Check correct name before drilling down
        3. Exploration: List all → pick interesting ones for analysis

    Related Tools:
        - drill_exporter_by_fruit: Analyze specific exporter's portfolio
        - get_exporter_pricing_summary: Get top exporters without searching
        - get_available_values: Alternative way to see all exporters
    """
    all_exporters = get_exporters()

    if query:
        query_lower = query.lower()
        matching = [e for e in all_exporters if query_lower in e.lower()]
    else:
        matching = all_exporters

    # Get normalization examples
    mappings = get_all_mappings()
    examples = []
    seen = set()

    for original, canonical in mappings.items():
        if canonical not in seen and len(examples) < 3:
            # Find all variations for this canonical name
            variations = [k for k, v in mappings.items() if v == canonical]
            if len(variations) > 1:
                examples.append({
                    "canonical": canonical,
                    "variations": variations[:3]  # Show max 3 variations
                })
                seen.add(canonical)

    return {
        "exporters": matching[:limit],
        "total_found": len(matching),
        "total_exporters": len(all_exporters),
        "normalization_examples": examples
    }


@mcp.tool()
def get_available_values() -> Dict[str, Any]:
    """
    Get all available filter values (fruits, exporters, formats).

    Useful for discovering what data is available in the system.

    Returns:
        Dictionary with lists of:
        - fruits: All fruit types
        - exporters: All canonical exporter names (normalized)
        - formats: All product format types
        - stats: Database statistics

    Example Usage:
        # Discover what's in the database
        get_available_values()

    Output Interpretation:
        - Fruits: Complete list of available fruit types
        - Exporters: First 50 canonical names (normalized)
        - Formats: All product format types
        - Stats: Total records, date range, entity counts
        - Use this to know valid values for other tools

    Common Workflows:
        1. Initial Discovery: Start here → choose fruit/exporter → drill down
        2. Parameter Validation: Check valid values before querying
        3. Coverage Assessment: Understand data scope and completeness

    Related Tools:
        - search_exporters: More flexible exporter search with partial matching
        - get_fruit_pricing_summary: Start analyzing specific fruits
        - get_system_info: Understand system architecture and capabilities

    Best Practices:
        - Use this tool first when starting exploration
        - Check stats to understand data coverage
        - Use exact fruit/exporter names from this output in other tools
    """
    stats = get_table_stats()

    return {
        "fruits": get_fruit_types(),
        "exporters": get_exporters()[:50],  # Limit to 50 for readability
        "formats": get_format_types(),
        "stats": {
            "total_records": stats['total_records'],
            "date_range": stats['date_range'],
            "total_exporters": stats['total_exporters'],
            "total_fruits": stats['total_fruits'],
            "total_destinations": stats['total_destinations'],
        },
        "note": "Exporter names are normalized (e.g., VIRU variations consolidated into 'Viru')"
    }


# ============================================================================
# UTILITY TOOLS
# ============================================================================

@mcp.tool()
def get_system_info() -> Dict[str, Any]:
    """
    Get information about the analytics system.

    Returns system architecture, data quality filters, and capabilities.

    Returns:
        Dictionary with:
        - version: System version
        - architecture: Description of coherent structure
        - data_quality: Applied filters
        - capabilities: Available analytics
        - llm_usage_guide: How to select tools based on query type

    Example Usage:
        # Understand system capabilities
        get_system_info()

    Output Interpretation:
        - Architecture: Core modules (exporter mapping, filters, database, pricing)
        - Data Quality: Filters applied (75.4% retention, clean data only)
        - Capabilities: Available dimensions, drill-downs, regions
        - Key Improvements: Normalization examples (Viru: 2,640 shipments)

    Common Workflows:
        1. Onboarding: Start here to understand system capabilities
        2. Data Quality Questions: Check filters and retention rates
        3. Architecture Understanding: Learn about coherent design

    Related Tools:
        - get_available_values: See actual data (fruits, exporters, formats)
        - MCP Prompts: See comprehensive workflow guides
    """
    return {
        "version": "Coherent Architecture v1.0",
        "llm_usage_guide": {
            "query_patterns": {
                "market_overview": {
                    "description": "User wants overall market landscape",
                    "recommended_tools": [
                        "get_fruit_pricing_summary (start here)",
                        "get_exporter_pricing_summary (competitive landscape)",
                        "get_format_pricing_summary (product formats)"
                    ],
                    "example_queries": [
                        "What's the market overview?",
                        "Show me the frozen fruit landscape",
                        "What are the top fruits and exporters?"
                    ]
                },
                "supplier_discovery": {
                    "description": "User wants to find suppliers",
                    "recommended_tools": [
                        "drill_fruit_by_exporter (who ships X fruit?)",
                        "drill_exporter_by_fruit (check their portfolio)",
                        "search_exporters (find by name)"
                    ],
                    "example_queries": [
                        "Who ships mangoes?",
                        "Find avocado suppliers",
                        "Which exporters can supply strawberries?"
                    ]
                },
                "exporter_analysis": {
                    "description": "User wants to analyze specific exporter",
                    "recommended_tools": [
                        "search_exporters (find correct name)",
                        "drill_exporter_by_fruit (portfolio analysis)",
                        "get_exporter_pricing_summary (competitive position)"
                    ],
                    "example_queries": [
                        "Tell me about Viru",
                        "Analyze Camposol's portfolio",
                        "How does this exporter compare?"
                    ]
                },
                "pricing_strategy": {
                    "description": "User wants pricing insights",
                    "recommended_tools": [
                        "get_fruit_pricing_summary (market pricing)",
                        "drill_fruit_by_format (format premiums)",
                        "drill_fruit_by_exporter (competitive pricing)"
                    ],
                    "example_queries": [
                        "What's the pricing for mango?",
                        "Which format is most profitable?",
                        "Price positioning for strawberries?"
                    ]
                },
                "format_analysis": {
                    "description": "User wants format/product options",
                    "recommended_tools": [
                        "drill_fruit_by_format (what formats for X?)",
                        "get_format_pricing_summary (overall format pricing)",
                        "drill_fruit_by_exporter (who offers which formats?)"
                    ],
                    "example_queries": [
                        "What mango formats are available?",
                        "Which formats command premium prices?",
                        "Compare chunks vs puree pricing"
                    ]
                },
                "regional_comparison": {
                    "description": "User wants Europe vs RoW comparison",
                    "recommended_tools": [
                        "ALL summary tools with region='Europe' then region='RoW'",
                        "Compare results to identify arbitrage opportunities"
                    ],
                    "example_queries": [
                        "Compare Europe vs Asia pricing",
                        "Regional differences for avocado?",
                        "Where is mango pricing higher?"
                    ]
                },
                "data_discovery": {
                    "description": "User wants to explore available data",
                    "recommended_tools": [
                        "get_available_values (see all data)",
                        "get_system_info (understand capabilities)",
                        "Then drill down based on interest"
                    ],
                    "example_queries": [
                        "What data is available?",
                        "Show me what you have",
                        "What fruits can I analyze?"
                    ]
                }
            },
            "best_practices": [
                "ALWAYS use multiple tools for comprehensive analysis",
                "Start with summary tools (get_fruit_pricing_summary, etc.) before drilling down",
                "Compare regions (Europe vs RoW) for complete picture",
                "Use get_available_values first if unsure about valid parameter values",
                "Cross-reference: fruit → exporter, then exporter → fruit for validation",
                "Check portfolio_diversity score when evaluating exporters",
                "Interpret Q1/Median/Q3 as pricing segments, not just statistics",
                "Remember: ALL exporter names are normalized (use canonical names)"
            ],
            "tool_selection_logic": {
                "step_1_discovery": "Use get_available_values or summary tools",
                "step_2_overview": "Use summary tools (fruit/exporter/format)",
                "step_3_drill_down": "Use drill tools for specific analysis",
                "step_4_cross_reference": "Use reverse drill to validate (fruit→exporter, then exporter→fruit)",
                "step_5_regional": "Repeat key analyses with region filters"
            }
        },
        "architecture": {
            "core_modules": [
                "exporter_mapping: Normalizes company names (57 mappings)",
                "filters: Data quality filters (air, samples, outliers)",
                "database: Unified DB access utilities"
            ],
            "analytics_modules": [
                "pricing: Quartile pricing engine (Q1/Median/Q3)"
            ],
            "interfaces": [
                "CLI: Command-line interface",
                "MCP: Model Context Protocol server (this)"
            ]
        },
        "data_quality_filters": {
            "air_freight": "Excluded (sea freight only)",
            "samples": "Excluded (MUESTRA, SIN VALOR, <10kg)",
            "small_shipments": "Excluded (<0.1 MT / 100kg)",
            "outliers": "IQR method per fruit type",
            "date_range": "YTD Oct 2024 - Oct 2025",
            "retention_rate": "75.4% (8,361 of 11,098 YTD records)"
        },
        "capabilities": {
            "pricing_dimensions": ["fruit", "exporter", "format"],
            "drill_downs": [
                "fruit → exporter",
                "fruit → format",
                "exporter → fruit",
                "exporter → format",
                "format → exporter"
            ],
            "regions": ["Worldwide (default)", "Europe", "Rest of World"],
            "pricing_method": "Quartiles (Q1/Median/Q3) instead of absolute min/max"
        },
        "key_improvements": [
            "Viru consolidated: 2,640 shipments (was split into 2 variations)",
            "Mebol consolidated: 698 shipments (was split into 2 variations)",
            "48 canonical exporters (from 152 originals)",
            "Quartile pricing eliminates outlier distortion",
            "Database-driven (single source of truth)"
        ]
    }


# ============================================================================
# CACHE TOOLS (if available)
# ============================================================================

if CACHE_ENABLED and cache:
    @mcp.tool()
    def get_cache_stats() -> Dict[str, Any]:
        """Get cache statistics (hits, misses, size)."""
        return cache.get_stats()

    @mcp.tool()
    def clear_cache() -> Dict[str, str]:
        """Clear all cached data."""
        cache.clear()
        return {"status": "Cache cleared successfully"}


# ============================================================================
# SERVER STARTUP
# ============================================================================

if __name__ == "__main__":
    mcp.run()
