# Peru Frozen Fruit Exports - MCP Server

FastMCP server for querying Peru frozen fruit export data through Claude Desktop.

## Setup

### 1. Database Created
✅ SQLite database with 14,279 export records
✅ Indexed on key fields (exporter, destination, fruit, format, size, date)
✅ Optimized views for fast queries
✅ Europe vs Rest of World region mapping (20 European countries)

**Database stats:**
- File size: 17.73 MB
- Records: 14,279 exports
- Exporters: 152 unique companies
- Destinations: 57 countries (20 Europe, 37 Rest of World)
- Volume: 218,282 MT | $507.8M USD FOB

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
        "mcp_server.py"
      ]
    }
  }
}
```

### 3. Restart Claude Desktop

After adding the configuration, restart Claude Desktop to load the MCP server.

## Available Tools (11 tools)

### Query Tools

#### 1. `query_by_exporter`
Find exports by company name (fuzzy matching handles typos).

**Parameters:**
- `exporter_name` (required): Company name
- `destination_region`: "Europe" or "Rest of World"
- `destination_country`: Specific country
- `fruit`: Filter by fruit type
- `limit`: Max results (default 100)

**Example:**
> "Show me what Chavin de Huantar exports to Europe"

#### 2. `query_by_destination`
Get exports to a specific country with product breakdown.

**Parameters:**
- `country` (required): Destination country
- `fruit`: Filter by fruit
- `certification`: "organic", "conventional", or "unknown"
- `limit`: Max results (default 100)

**Example:**
> "What is being exported to Poland for what prices?"

#### 3. `query_by_product`
Search by product specifications.

**Parameters:**
- `fruit` (required): Fruit name
- `format_type`: "chunks", "slices", "puree", etc.
- `size`: "20x20", "25x25", etc.
- `certification`: "organic", "conventional", "unknown"
- `limit`: Max results (default 100)

**Example:**
> "Show me organic mango chunks 20x20"

#### 4. `search_exporters`
Fuzzy search for exporter names.

**Parameters:**
- `search_term` (required): Partial name
- `limit`: Max results (default 20)

**Example:**
> "Find exporters with 'Sunshine' in the name"

### Analysis Tools

#### 5. `analyze_seasonality`
Monthly trends with auto-detected peak seasons.

**Parameters:**
- `fruit` (required): Fruit name
- `year`: Specific year (optional)

**Returns:** Peak months, monthly breakdown, insights

**Example:**
> "What is the best season for Pineapple?"

#### 6. `get_price_analysis`
Price ranges (min/avg/max USD/MT) by product.

**Parameters:**
- `fruit`: Filter by fruit
- `format_type`: Filter by format
- `certification`: Filter by certification
- `destination_region`: "Europe" or "Rest of World"

**Example:**
> "What are mango chunk prices to Europe?"

#### 7. `summarize_by_region`
Europe vs Rest of World with country breakdowns.

**Parameters:**
- `fruit`: Filter by fruit
- `show_countries`: Include country details (default true)
- `limit_countries`: Max countries per region (default 10)

**Example:**
> "Compare Europe vs Rest of World for strawberries"

### Comparison Tools

#### 8. `compare_products`
Side-by-side product comparison.

**Parameters:**
- `products` (required): List of products to compare
  - Each product: `{"fruit": "mango", "format": "chunks", "size": "20x20"}`
- `metric`: "volume", "price", or "both"

**Example:**
> "Compare 20x20 vs 25x25 mango chunks"

#### 9. `compare_exporters`
Performance comparison between exporters.

**Parameters:**
- `exporter_names` (required): List of exporter names
- `date_range_months`: Limit to last N months

**Example:**
> "Compare Sunshine Export vs Camposol"

#### 10. `compare_periods`
Year-over-year or custom period comparison.

**Parameters:**
- `period1_start`, `period1_end`: First period dates (YYYY-MM-DD)
- `period2_start`, `period2_end`: Second period dates (YYYY-MM-DD)
- `fruit`: Optional fruit filter

**Example:**
> "Compare 2024 Q1 vs 2024 Q2"

### Helper Tools

#### 11. `get_available_values`
List unique values for fields.

**Parameters:**
- `field` (required): "fruits", "formats", "sizes", "exporters", "destinations", "certifications"

**Example:**
> "What fruit types are available?"

## Example Queries

### "Who are the largest players in Poland?"
```
Use: query_by_destination(country="Poland")
Or: search_exporters + filter by destination
```

**Answer:** Top 3 importers in Poland:
1. **POLARICA SP. Z O.O.** - 1,869 MT @ $2,012/MT
2. **BESTFOODS POLSKA SP. Z O.O.** - 936 MT @ $1,882/MT  
3. **GREENYARD FROZEN POLAND SP. Z O.O.** - 696 MT @ $2,077/MT

### "What products go to Poland?"
Top products to Poland:
- Unknown specs: 3,288 MT @ $2,022/MT
- Mango (unspecified): 1,466 MT @ $1,771/MT
- Mango IQF 20x20 organic: 770 MT @ $1,668/MT
- Mango chunks 1x10: 426 MT @ $2,361/MT

### "What is the best season for pineapple?"
```
Use: analyze_seasonality(fruit="pineapple")
```

Auto-detects peak months with % above/below average.

### "Compare organic vs conventional mango prices"
```
Use: compare_products(
  products=[
    {"fruit": "mango", "certification": "organic"},
    {"fruit": "mango", "certification": "conventional"}
  ]
)
```

## Features

### 🔍 Fuzzy Matching
- Handles typos and partial names
- "Chavin" finds "Chavin de Huantar SA"
- "Sunshine" finds "Sunshine Export S.A.C"

### 🌍 Regional Analysis
- Europe: 20 countries mapped (89,049 MT)
- Rest of World: 37 countries (129,232 MT)
- Automatic country breakdowns

### 📊 Auto-Detection
- Peak seasons automatically identified
- Top 3 months highlighted
- % above/below average calculated

### 📈 Comprehensive Metrics
All queries return:
- Volume (MT)
- Pricing (USD/MT FOB)
- Product specs (fruit, format, size, certification)
- Exporter/importer details
- Dates and trends

## Database Schema

**Main Table:** `exports` (14,279 records, 43 columns)

**Key Columns:**
- Exporter, Importer
- Fruit, Variety, Format, Size, Certification
- Destination Country, Region
- Date
- Net Weight MT, USD per MT FOB
- Total FOB USD

**Views:**
- `exporter_products` - Aggregated by exporter + product
- `destination_products` - Aggregated by destination + product
- `monthly_exports` - Time-series for seasonality
- `regional_exports` - Europe vs Rest of World

## File Structure

```
Export-Data/
├── exports.db (17.73 MB)           # SQLite database
├── mcp_server.py                   # FastMCP server (11 tools)
├── create_database.py              # Database setup script
├── claude_desktop_config.json      # MCP configuration
├── peru_frozen_fruit_exports_enriched.csv.gz  # Source data
└── MCP_README.md                   # This file
```

## Troubleshooting

### MCP server not showing in Claude Desktop
1. Check config file location is correct
2. Verify JSON syntax is valid
3. Restart Claude Desktop
4. Check Claude Desktop logs

### "Database not found" error
Run: `uv run python create_database.py` to recreate database

### Fuzzy matching not finding exporters
Try broader search terms or use `search_exporters` tool first

## Query Performance

- Indexed queries: <100ms
- Aggregations: <500ms
- Full table scans: <2s

All queries limited to 10,000 results maximum for safety.
