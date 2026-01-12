# Peru Frozen Fruit Exports - MCP Server (Coherent Architecture)

FastMCP server for querying Peru frozen fruit export data through Claude Desktop using the unified analytics system.

## Architecture Overview

This MCP server uses the **coherent architecture** for consistent, high-quality analytics:

- **Exporter Normalization** (`core/exporter_mapping.py`): 152 variations → 48 canonical names
- **Data Quality Filters** (`core/filters.py`): Clean data only (75.4% retention)
- **Quartile Pricing Engine** (`analysis/pricing.py`): Q1/Median/Q3 pricing (no outlier distortion)
- **Database Utilities** (`core/database.py`): Unified database access

### Data Quality

**Filters Applied:**
- ✅ No air freight (sea only)
- ✅ No samples or zero-value shipments
- ✅ Minimum 0.1 MT (100 kg) shipments
- ✅ IQR outlier removal per fruit
- ✅ Valid pricing data only

**Results:**
- **Clean records:** 8,361 of 11,098 YTD (75.4% retention)
- **Data period:** YTD October 2024 - October 2025
- **Exporters:** 48 canonical names (from 152 variations)
- **Example:** Viru consolidated: 2,640 shipments from 2 variations

### Pricing Method

**Quartiles (Q1/Median/Q3)** instead of min/avg/max:
- **Q1 (25th percentile):** Lower-priced segment, value positioning
- **Median (50th):** Middle market pricing, most common
- **Q3 (75th percentile):** Premium segment, higher quality
- **Why quartiles?** Eliminates outlier distortion vs absolute min/max

## Setup

### 1. Database Already Created
✅ SQLite database with clean, filtered export records
✅ Indexed on key fields (exporter, destination, fruit, format, date)
✅ Optimized views: `v_clean_exports` (YTD Oct 2024 - Oct 2025)
✅ Europe vs Rest of World region mapping (20 European + 37 RoW countries)

### 2. Add to Claude Desktop

Copy the configuration from `claude_desktop_config.json` into your Claude Desktop config file:

**Location:**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

**Configuration:**
```json
{
  "mcpServers": {
    "peru-exports": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/andresublime/Documents/Claude files/Peru-Frozen-Fruit-Analysis/Export-Data",
        "run",
        "mcp_tools/server.py"
      ]
    }
  }
}
```

**Important:** Use `mcp_tools/server.py` (coherent version), not `mcp_server.py` (deprecated).

### 3. Restart Claude Desktop

After adding the configuration, restart Claude Desktop to load the MCP server.

## Available Tools (12 tools)

### Summary Tools (4 tools)

#### 1. `get_fruit_pricing_summary`
Get quartile pricing summary for all fruits.

**Parameters:**
- `region`: Optional - "Europe" or "RoW" (default: worldwide)
- `limit`: Max results (default: 20)

**Returns:** Q1/Median/Q3 prices (USD/MT FOB), YTD volume (MT) for each fruit

**Example:**
> "Show me fruit pricing for the European market"

**CLI Equivalent:** `python cli/main.py summary fruit --region Europe`

---

#### 2. `get_exporter_pricing_summary`
Get quartile pricing summary for all exporters (with canonical name normalization).

**Parameters:**
- `region`: Optional - "Europe" or "RoW" (default: worldwide)
- `limit`: Max results (default: 20)

**Returns:** Q1/Median/Q3 prices, fruit count, YTD volume for each exporter

**Example:**
> "Who are the top exporters?"

**CLI Equivalent:** `python cli/main.py summary exporter`

---

#### 3. `get_importer_pricing_summary` ⭐ NEW
Get quartile pricing summary for all importers (with canonical mapping).

**Parameters:**
- `region`: Optional - "Europe" or "RoW" (default: worldwide)
- `limit`: Max results (default: 20)

**Returns:** Q1/Median/Q3 prices, YTD volume for each importer

**Example:**
> "Show me the largest importers in Europe"

**CLI Equivalent:** `python cli/main.py summary importer --region Europe`

---

#### 4. `get_format_pricing_summary`
Get quartile pricing summary for all product formats.

**Parameters:**
- `region`: Optional - "Europe" or "RoW" (default: worldwide)

**Returns:** Q1/Median/Q3 prices, YTD volume for each format type

**Example:**
> "What are the pricing ranges for different formats?"

**CLI Equivalent:** `python cli/main.py summary format`

---

### Drill-Down Tools (6 tools)

#### 5. `drill_fruit_by_exporter`
See which exporters ship a specific fruit and their pricing.

**Parameters:**
- `fruit_name`: Fruit name (e.g., "mango", "avocado") - required
- `region`: Optional - "Europe" or "RoW"
- `limit`: Max exporters (default: 20)

**Returns:** List of exporters with Q1/Median/Q3 pricing for this fruit

**Example:**
> "Who ships mangoes to Europe?"

**CLI Equivalent:** `python cli/main.py drill mango --by exporter --region Europe`

---

#### 6. `drill_exporter_by_fruit`
See an exporter's complete fruit portfolio (with automatic name normalization).

**Parameters:**
- `exporter_name`: Exporter name (fuzzy matching supported) - required
- `region`: Optional - "Europe" or "RoW"

**Returns:** List of fruits with pricing, portfolio diversity score

**Example:**
> "What does Viru export?"

**CLI Equivalent:** `python cli/main.py drill Viru --by fruit --filter-dimension exporter`

---

#### 7. `drill_importer_by_fruit` ⭐ NEW
See an importer's fruit purchase profile.

**Parameters:**
- `importer_name`: Importer name - required
- `region`: Optional - "Europe" or "RoW"

**Returns:** List of fruits with pricing, purchase profile analysis

**Example:**
> "What fruits does Salud Foodgroup Europe import?"

**CLI Equivalent:** `python cli/main.py drill "Salud Foodgroup Europe" --by fruit --filter-dimension importer`

---

#### 8. `drill_fruit_by_format`
See which formats are available for a specific fruit.

**Parameters:**
- `fruit_name`: Fruit name - required
- `region`: Optional - "Europe" or "RoW"

**Returns:** List of formats with pricing for this fruit

**Example:**
> "What mango formats are available?"

**CLI Equivalent:** `python cli/main.py drill mango --by format`

---

#### 9. `drill_importer_by_format` ⭐ NEW
See an importer's format preferences.

**Parameters:**
- `importer_name`: Importer name - required
- `region`: Optional - "Europe" or "RoW"

**Returns:** List of formats with pricing for this importer

**Example:**
> "What formats does Ardo purchase?"

**CLI Equivalent:** Not available in CLI yet

---

### Export Tools (1 tool)

#### 10. `export_pricing_to_csv` ⭐ NEW
Export pricing summary to CSV file (matches CLI export command).

**Parameters:**
- `dimension`: "fruit", "exporter", "importer", or "format" - required
- `output_path`: File path for CSV - required
- `region`: Optional - "Europe" or "RoW"

**Returns:** Success message with rows exported

**Example:**
> "Export European fruit pricing to fruits_europe.csv"

**CLI Equivalent:** `python cli/main.py export fruit fruits_europe.csv --region Europe`

---

### Discovery Tools (2 tools)

#### 11. `search_exporters`
Search for exporters by name (partial matching, returns canonical names).

**Parameters:**
- `query`: Partial name to search (optional - if None, returns all)
- `limit`: Max results (default: 50)

**Returns:** List of canonical exporter names with normalization examples

**Example:**
> "Find exporters with 'Viru' in the name"

---

#### 12. `get_available_values`
Discover all available data (fruits, exporters, formats, stats).

**Parameters:** None

**Returns:**
- List of all fruits
- List of all canonical exporters (first 50)
- List of all formats
- Database statistics (total records, date range, entity counts)

**Example:**
> "What data is available in the system?"

---

### Utility Tools (1 tool + 2 cache tools)

#### 13. `get_system_info`
Get system architecture, data quality filters, and LLM usage guide.

**Parameters:** None

**Returns:**
- Architecture overview
- Data quality filters applied
- Capabilities (dimensions, drill-downs, regions)
- LLM usage guide (query patterns and tool selection)
- Key improvements (normalization examples)

**Example:**
> "Tell me about the data quality filters"

---

#### 14. `get_cache_stats` (if cache enabled)
Get cache statistics (hits, misses, size).

#### 15. `clear_cache` (if cache enabled)
Clear all cached data.

---

## MCP Prompts - Multi-Tool Workflows (6 prompts)

The server includes comprehensive workflow guides for complex analysis:

1. **`market_entry_analysis`** - Complete market entry workflow
2. **`exporter_competitive_profile`** - Exporter competitive analysis
3. **`product_pricing_strategy`** - Multi-dimensional pricing strategy
4. **`supplier_discovery`** - Supplier discovery and evaluation
5. **`format_optimization`** - Product format optimization
6. **`regional_market_intelligence`** - Regional comparison workflow

**Usage:** These prompts guide LLMs through multi-step analyses combining multiple tools.

---

## Example Queries

### "What's the fruit pricing landscape in Europe?"
```
Use: get_fruit_pricing_summary(region='Europe', limit=20)
```

**Returns:** Top 20 fruits with Q1/Median/Q3 pricing and YTD volume for Europe

---

### "Who are the top mango exporters and what are their prices?"
```
Step 1: drill_fruit_by_exporter(fruit_name='mango', limit=10)
Step 2: drill_exporter_by_fruit(exporter_name='Viru') # Check top exporter's portfolio
```

**Returns:**
- All mango exporters with pricing
- Top exporter's complete fruit portfolio with diversity score

---

### "What does Salud Foodgroup Europe import?"
```
Use: drill_importer_by_fruit(importer_name='Salud Foodgroup Europe')
```

**Returns:** Complete fruit purchase profile with diversification analysis

---

### "Compare Europe vs Rest of World pricing for strawberries"
```
Step 1: get_fruit_pricing_summary(region='Europe')
Step 2: get_fruit_pricing_summary(region='RoW')
# Compare strawberry pricing between regions
```

**Returns:** Regional pricing comparison to identify arbitrage opportunities

---

### "Export all European exporter data to CSV"
```
Use: export_pricing_to_csv(dimension='exporter', output_path='eu_exporters.csv', region='Europe')
```

**Returns:** CSV file with all European exporters and their quartile pricing

---

## Key Differences from Original MCP Server

| Feature | Original Server | Coherent Server ✅ |
|---------|-----------------|-------------------|
| **File** | `mcp_server.py` | `mcp_tools/server.py` |
| **Tools** | 11 tools | 12 tools |
| **Architecture** | Direct SQL queries | Uses `analysis/pricing.py` |
| **Pricing** | Min/Avg/Max | Q1/Median/Q3 (quartiles) |
| **Exporter Names** | Raw (152 variations) | Normalized (48 canonical) |
| **Data Quality** | None (14,279 records) | Filtered (8,361 clean records) |
| **Retention** | 100% (unfiltered) | 75.4% (quality filters) |
| **Importer Dimension** | ❌ Not available | ✅ Full support |
| **CSV Export** | Partial | ✅ Full support |
| **Date Scope** | All historical | YTD Oct 2024 - Oct 2025 |
| **MCP Prompts** | ❌ None | ✅ 6 comprehensive workflows |
| **CLI Alignment** | ❌ Different approach | ✅ 95% aligned |

---

## Data Dimensions

The coherent system supports 4 dimensions:

1. **Fruit**: Mango, Pineapple, Avocado, Strawberry, etc.
2. **Exporter**: Peruvian export companies (48 canonical names)
3. **Importer**: International importing companies (with canonical mapping) ⭐
4. **Format**: Product formats (IQF, Chunk, Puree, Dices, etc.)

## Regional Filters

- **Worldwide (default)**: All 57 destination countries
- **Europe**: 20 countries (EU + UK, Norway, Switzerland, etc.)
- **Rest of World (RoW)**: 37 countries (Asia, Middle East, Americas, etc.)

---

## File Structure

```
Export-Data/
├── exports.db                      # SQLite database
├── mcp_tools/
│   └── server.py                   # ✅ Coherent MCP server (USE THIS)
├── archive/
│   ├── mcp_server.py              # ❌ Original server (deprecated)
│   ├── mcp_server_v2.py           # ❌ Modular server (deprecated)
│   └── README.md                   # Deprecation notice
├── core/
│   ├── exporter_mapping.py         # Exporter name normalization
│   ├── filters.py                  # Data quality filters
│   └── database.py                 # Database utilities
├── analysis/
│   └── pricing.py                  # Quartile pricing engine
├── cli/
│   └── main.py                     # CLI interface (95% aligned)
├── claude_desktop_config.json      # MCP configuration
└── MCP_README.md                   # This file
```

---

## Troubleshooting

### MCP server not showing in Claude Desktop
1. Check config file location is correct
2. Verify you're using `mcp_tools/server.py` (not `mcp_server.py`)
3. Verify JSON syntax is valid
4. Restart Claude Desktop
5. Check Claude Desktop logs

### "No data found for exporter" error
- Exporter names are normalized automatically
- Try using `search_exporters()` first to find the canonical name
- Example: "VIRU SA" → "Viru" (automatic normalization)

### "Invalid dimension" error
Valid dimensions: `fruit`, `exporter`, `importer`, `format`

### Want to see raw, unfiltered data?
The coherent server uses clean, filtered data by design. If you need unfiltered data:
- Use the original `mcp_server.py` (see archive/README.md)
- Note: Results will differ due to different methodology

---

## Performance

- Summary queries: <200ms
- Drill-down queries: <300ms
- CSV exports: <500ms
- Cache-enabled queries: <50ms (if cache available)

All queries use indexed views (`v_clean_exports`) for fast performance.

---

## Best Practices for LLMs

1. **Start with summary tools** before drilling down
2. **Default is worldwide**: All queries include both Europe and RoW unless region filter specified
3. **Regional filtering is optional**: Use `region='Europe'` or `region='RoW'` for regional analysis
4. **Use get_available_values** if unsure about valid parameters
5. **Cross-reference**: fruit → exporter, then exporter → fruit for validation
6. **Interpret Q1/Median/Q3** as pricing segments, not just statistics
7. **Remember**: ALL exporter names are normalized (use canonical names)
8. **Use MCP Prompts** for comprehensive multi-tool workflows

---

## CLI Integration

The MCP server is **95% aligned** with the CLI:

**Aligned:**
- ✅ Same pricing engine (`analysis/pricing.py`)
- ✅ Same data quality filters
- ✅ Same quartile pricing (Q1/Median/Q3)
- ✅ Same exporter normalization
- ✅ Same regional filtering

**MCP-Specific:**
- MCP Prompts (6 comprehensive workflows)
- LLM usage guide
- Discovery tools (search_exporters, get_available_values)
- System info tool

**CLI-Specific:**
- Command-line interface with argparse
- Direct file output control

---

## Version

**Coherent Architecture v1.0**

Updated: 2025-11-16

Built with FastMCP, SQLite, and pandas.
