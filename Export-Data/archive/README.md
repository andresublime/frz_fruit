# Archived MCP Servers

This directory contains deprecated MCP server implementations that have been replaced by the coherent architecture.

## Why These Were Archived

These MCP servers were replaced on **2025-11-16** to align with the CLI's coherent architecture and ensure consistent analytics across all interfaces.

## Archived Files

### 1. `mcp_server.py` - Original MCP Server
**Status:** ❌ Deprecated

**Why Archived:**
- Uses direct SQL queries instead of unified analytics engine
- No data quality filters (100% unfiltered data)
- Uses min/avg/max pricing instead of quartiles
- No exporter name normalization
- Inconsistent with CLI implementation
- Missing importer dimension

**Key Differences from Coherent:**
- 14,279 records (unfiltered) vs 8,361 (filtered)
- 152 exporter variations vs 48 canonical names
- All historical data vs YTD Oct 2024 - Oct 2025

**Use Case:**
If you need unfiltered raw data or historical analysis beyond YTD, this server may still be useful. However, results will differ significantly from the coherent system.

---

### 2. `mcp_server_v2.py` - Modular MCP Server
**Status:** ❌ Deprecated

**Why Archived:**
- Hybrid approach with modular helpers but still uses direct SQL
- No quartile pricing methodology
- No integration with coherent architecture
- Reduced tool count (6 core tools)
- Includes caching layer (but not integrated with coherent analytics)

**Key Features (if still needed):**
- Modular helper structure (mcp_helpers.py, mcp_cache.py)
- 1-hour cache TTL for dashboard queries
- Simplified tool set

**Use Case:**
Educational reference for modular MCP server architecture, but not recommended for production use.

---

## Recommended Alternative

**Use:** `/mcp_tools/server.py` (Coherent Architecture)

**Why:**
- ✅ 100% aligned with CLI analytics
- ✅ Uses unified pricing engine (`analysis/pricing.py`)
- ✅ Data quality filters (75.4% retention)
- ✅ Quartile pricing (Q1/Median/Q3)
- ✅ Exporter name normalization (48 canonical names)
- ✅ Full importer dimension support
- ✅ CSV export functionality
- ✅ YTD scope (Oct 2024 - Oct 2025)
- ✅ MCP Prompts for multi-tool workflows

---

## Migration Guide

If you were using the original MCP servers, here's how to migrate:

### Tool Mapping

| Original Server | Coherent Server |
|----------------|-----------------|
| `query_by_exporter()` | `drill_exporter_by_fruit()` |
| `query_by_destination()` | Use `region` parameter in any tool |
| `query_by_product()` | `drill_fruit_by_exporter()` + `drill_fruit_by_format()` |
| `search_exporters()` | `search_exporters()` (same, but returns canonical names) |
| `analyze_seasonality()` | Not available (use time-series analysis in CLI) |
| `get_price_analysis()` | `get_fruit_pricing_summary()` or `get_format_pricing_summary()` |
| `summarize_by_region()` | Use `region='Europe'` or `region='RoW'` in any summary tool |
| `compare_products()` | Use multiple `drill_fruit_by_format()` calls |
| `compare_exporters()` | Use multiple `drill_exporter_by_fruit()` calls |
| `compare_periods()` | Not available (coherent scope is YTD only) |
| `get_available_values()` | `get_available_values()` (same concept, different data) |

### Parameter Mapping

| Original Parameter | Coherent Parameter |
|-------------------|-------------------|
| `destination_region` | `region` |
| `destination_country` | Not available (use region filter) |
| `certification` | Not available in MCP (available in raw data) |
| `format_type` | Use `drill_fruit_by_format()` or `drill_importer_by_format()` |

### Expected Data Differences

When migrating, expect these changes:

1. **Volume differences:** Coherent uses filtered data (75.4% retention)
2. **Price differences:** Quartiles vs min/avg/max can show different ranges
3. **Exporter names:** Normalized (e.g., "VIRU SA" → "Viru")
4. **Date scope:** YTD Oct 2024 - Oct 2025 (not all historical)
5. **Missing tools:** Seasonality and period comparison (use CLI for time-series)

---

## Restoration

If you need to restore these servers temporarily:

1. Copy the desired file back to the parent directory
2. Update your Claude Desktop config to point to it
3. Restart Claude Desktop

**Warning:** Using archived servers will produce results inconsistent with CLI and current analytics standards.

---

## Support

For questions about the coherent architecture or migration:
- See `/MCP_README.md` for coherent server documentation
- See `/cli/.CLAUDE` for CLI documentation
- Check `/core/` for coherent module implementations

---

**Archived:** 2025-11-16
**Replaced By:** `/mcp_tools/server.py` (Coherent Architecture v1.0)
