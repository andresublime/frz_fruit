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
    """
    return {
        "version": "Coherent Architecture v1.0",
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
