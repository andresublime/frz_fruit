# Peru Frozen Fruit Exports MCP - User Guide

## Table of Contents
1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Tool Categories](#tool-categories)
4. [Complete Tool Reference](#complete-tool-reference)
5. [Common Use Cases](#common-use-cases)
6. [Date Filtering Guide](#date-filtering-guide)
7. [Tips & Best Practices](#tips--best-practices)

---

## Overview

This MCP (Model Context Protocol) server provides **19 specialized tools** for analyzing Peru's frozen fruit export data. The dataset includes 14,279 export records from January 2024 to October 2025, covering:

- **152 unique exporters**
- **57 destination countries**
- **20 fruit types** (mango, avocado, blueberry, pomegranate, lucuma, etc.)
- **218,281 MT total volume**
- **$507.8M total FOB value**

### What You Can Do

- Query exports by exporter, destination, product, or date range
- Analyze time-series trends and growth rates
- Calculate market share and competitive positioning
- Compare organic vs conventional prices
- Export data for external analysis
- Generate executive dashboard KPIs
- Track seasonality patterns
- Benchmark prices and identify outliers

---

## Getting Started

### Prerequisites

1. **Claude Desktop** installed with MCP support
2. **MCP server configured** in `claude_desktop_config.json`:

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

3. **Restart Claude Desktop** after configuration

### Your First Query

Try asking Claude:

> "Show me the top 10 mango exporters by volume"

Claude will automatically use the `get_top_n` tool to answer your question.

---

## Tool Categories

### 🔍 **Querying Tools** (4 tools)
Query and filter export records by various criteria.

- `query_by_exporter` - Find exports by company name
- `query_by_destination` - Find exports to specific countries
- `query_by_product` - Find exports by fruit/format/size
- `query_with_date_range` ⭐ **NEW** - Advanced filtering with date ranges

### 📊 **Analysis Tools** (4 tools)
Analyze trends, patterns, and statistics.

- `analyze_seasonality` - Monthly trends and peak seasons
- `get_price_analysis` - Price statistics by product/destination
- `get_time_series_analysis` ⭐ **NEW** - Trends with growth rates
- `analyze_price_dynamics` ⭐ **NEW** - Comprehensive price analysis

### 🏆 **Market Intelligence** (4 tools)
Understand market dynamics and competitive positioning.

- `get_market_share` ⭐ **NEW** - Market share with HHI concentration
- `analyze_exporter_portfolio` ⭐ **NEW** - Portfolio & diversification analysis
- `get_top_n` ⭐ **NEW** - Flexible rankings with percentages
- `search_exporters` - Fuzzy search for exporter names

### 🌍 **Regional Tools** (2 tools)
Compare regions and countries.

- `summarize_by_region` - Europe vs Rest of World breakdown
- `compare_periods` - Compare two time periods

### 📈 **Comparison Tools** (2 tools)
Side-by-side comparisons.

- `compare_products` - Compare multiple products
- `compare_exporters` - Compare exporter performance

### 💾 **Data Access** (2 tools)
Export and access underlying data.

- `export_data` ⭐ **NEW** - Export to JSON/CSV format
- `get_available_values` - List unique values (fruits, exporters, etc.)

### 📋 **Dashboard** (1 tool)
Executive summaries and KPIs.

- `get_dashboard_metrics` ⭐ **NEW** - KPI dashboard with comparisons

---

## Complete Tool Reference

### 1. `query_with_date_range` ⭐ NEW

**Purpose**: Query exports with flexible date ranges and advanced filtering.

**Key Features**:
- Relative date support ('last_30_days', 'ytd', 'q1_2024')
- Price range filtering (min/max USD/MT)
- Volume filtering (minimum MT)
- Multiple sort options
- Summary statistics included

**Example Questions**:
- "Show all organic mango exports in Q1 2024 priced above $2500/MT"
- "Find blueberry shipments from last 90 days sorted by volume"
- "Get mango chunks exports to Europe YTD"

**Parameters**:
```
start_date: 'last_30_days', 'ytd', 'q1_2024', '2024-01-01', etc.
end_date: Same as start_date
exporter: Exporter name (fuzzy match supported)
fruit: Fruit type (mango, blueberry, etc.)
destination: Country name (English or Spanish)
certification: 'organic', 'conventional', or 'unknown'
min_price: Minimum USD/MT
max_price: Maximum USD/MT
min_volume_mt: Minimum volume in metric tons
sort_by: 'date', 'price', or 'volume'
limit: Max results (default 100)
```

**Sample Response**:
```json
{
  "filters": {
    "start_date": "q1_2024",
    "fruit": "mango",
    "min_price": 2500
  },
  "summary": {
    "total_records": 45,
    "total_volume_mt": 1250.50,
    "total_fob_usd": 3125000.00,
    "avg_price_usd_per_mt": 2500.00
  },
  "records": [...]
}
```

---

### 2. `export_data` ⭐ NEW

**Purpose**: Export filtered data in JSON or CSV-ready format for external analysis.

**Key Features**:
- JSON or CSV output format
- Includes summary statistics
- Capped at 5000 records for safety
- Reuses `query_with_date_range` filtering

**Example Questions**:
- "Export last month's blueberry data to CSV"
- "Give me all Q1 2024 mango exports in JSON format"
- "Export organic strawberry shipments from this year"

**Parameters**:
```
format_type: 'json' or 'csv'
start_date: Date filter
end_date: Date filter
exporter: Exporter filter
fruit: Fruit filter
destination: Destination filter
limit: Max records (default 1000, max 5000)
```

**Use Cases**:
- Import into Excel/Google Sheets for pivot tables
- Load into PowerBI or Tableau for visualization
- Perform custom analysis in R or Python
- Archive historical data

---

### 3. `get_dashboard_metrics` ⭐ NEW

**Purpose**: Get executive KPI dashboard with period-over-period comparisons.

**Key Features**:
- High-level KPIs: volume, value, price, shipment count
- Top 5 products and destinations
- Automatic period comparison (MoM, YoY)
- Growth rate calculations
- Relative date support

**Example Questions**:
- "Show me this month's dashboard metrics"
- "Get YTD performance dashboard for mango exports"
- "Compare this quarter to last quarter"
- "What are the key metrics for last 30 days?"

**Parameters**:
```
fruit: Optional fruit filter
exporter: Optional exporter filter
destination: Optional destination filter
date_range: 'last_30_days', 'mtd', 'qtd', 'ytd', 'last_90_days'
compare_to_previous: Include previous period comparison (default true)
```

**Sample Response**:
```json
{
  "period": "ytd",
  "kpis": {
    "shipment_count": 245,
    "total_volume_mt": 5432.10,
    "total_fob_usd": 12500000.00,
    "avg_price_usd_per_mt": 2300.50,
    "unique_exporters": 45,
    "unique_destinations": 18
  },
  "top_products": [
    {"fruit": "mango", "format": "chunks", "volume_mt": 2500.00}
  ],
  "comparison": {
    "growth": {
      "volume_pct": 15.5,
      "fob_value_pct": 18.2,
      "avg_price_pct": 2.3
    }
  }
}
```

---

### 4. `get_top_n` ⭐ NEW

**Purpose**: Get top-N rankings by exporters, fruits, or destinations.

**Key Features**:
- Flexible dimensions (exporters, fruits, destinations)
- Multiple metrics (volume, value, shipment count)
- Percentage and cumulative share calculation
- Date range filtering
- Configurable N (top 10, 20, 50, etc.)

**Example Questions**:
- "Who are the top 20 exporters by volume?"
- "Show top 10 fruits by FOB value"
- "Which countries receive the most organic blueberries?"
- "Top 15 mango exporters in Q1 2024"

**Parameters**:
```
dimension: 'exporters', 'fruits', or 'destinations'
metric: 'volume', 'value', or 'shipment_count'
n: Number of results (default 10)
fruit: Optional fruit filter
destination: Optional destination filter
start_date: Optional start date
end_date: Optional end date
```

**Sample Response**:
```json
{
  "dimension": "exporters",
  "metric": "volume",
  "results": [
    {
      "rank": 1,
      "name": "CAMPOSOL S.A.",
      "value": 5432.10,
      "percentage": 15.5,
      "cumulative_percentage": 15.5,
      "shipment_count": 245
    }
  ]
}
```

---

### 5. `get_time_series_analysis` ⭐ NEW

**Purpose**: Analyze time-series trends with growth rates and moving averages.

**Key Features**:
- Multiple metrics: volume, price, shipment count, FOB value
- Granularity options: daily, weekly, monthly
- MoM and YoY growth calculations
- 3-period and 6-period moving averages
- Trend direction detection
- Supports all standard filters

**Example Questions**:
- "Show mango volume trends for the last 12 months"
- "Track organic blueberry price changes monthly this year"
- "What's the weekly export volume trend for last quarter?"
- "Analyze CAMPOSOL's monthly shipment trends"

**Parameters**:
```
metric: 'volume', 'price', 'shipment_count', or 'fob_value'
fruit: Optional fruit filter
exporter: Optional exporter filter
destination: Optional destination filter
start_date: Start date (default 'last_365_days')
granularity: 'daily', 'weekly', or 'monthly'
include_trends: Calculate trends (default true)
```

**Sample Response**:
```json
{
  "metric": "volume",
  "granularity": "monthly",
  "data_points": 12,
  "time_series": [
    {"period": "2024-01", "value": 1250.50},
    {"period": "2024-02", "value": 1350.75}
  ],
  "trends": {
    "mom_growth_pct": 8.0,
    "yoy_growth_pct": 15.5,
    "moving_avg_3period": 1300.00,
    "moving_avg_6period": 1275.50,
    "trend_direction": "increasing"
  }
}
```

---

### 6. `get_market_share` ⭐ NEW

**Purpose**: Calculate market share with HHI concentration index.

**Key Features**:
- Market share percentages by exporter, fruit, or destination
- HHI (Herfindahl-Hirschman Index) calculation
- Concentration interpretation (unconcentrated/moderate/highly concentrated)
- Top-3 and Top-5 cumulative share
- By volume or value
- Date range filtering

**Example Questions**:
- "What's CAMPOSOL's market share in mango exports?"
- "How concentrated is the organic blueberry market?"
- "Show market share for top 10 fruits"
- "Is the Germany market dominated by a few exporters?"

**Parameters**:
```
dimension: 'exporter', 'fruit', or 'destination'
metric: 'volume' or 'value'
fruit: Optional fruit filter
destination: Optional destination filter
start_date: Optional start date
end_date: Optional end date
top_n: Number of top players (default 10)
```

**Sample Response**:
```json
{
  "dimension": "exporter",
  "metric": "volume",
  "market_concentration": {
    "hhi": 850.5,
    "interpretation": "unconcentrated",
    "top_3_share_pct": 35.2,
    "top_5_share_pct": 52.8
  },
  "top_players": [
    {
      "rank": 1,
      "name": "CAMPOSOL S.A.",
      "value": 5432.10,
      "percentage": 15.5,
      "cumulative_percentage": 15.5
    }
  ]
}
```

**HHI Interpretation**:
- **< 1500**: Unconcentrated (competitive market)
- **1500-2500**: Moderately concentrated (some market power)
- **> 2500**: Highly concentrated (oligopoly/monopoly)

---

### 7. `analyze_exporter_portfolio` ⭐ NEW

**Purpose**: Analyze exporter's product portfolio and market positioning.

**Key Features**:
- Product mix analysis (fruits, formats, certifications)
- Geographic distribution (countries served)
- Product diversification score (HHI-based)
- Geographic diversification score
- Market share percentage
- Price positioning (premium/mid-market/economy)
- Fuzzy name matching

**Example Questions**:
- "Analyze CAMPOSOL's product portfolio and market position"
- "How diversified is DANPER's geographic reach?"
- "Show me SUNSHINE EXPORT's product mix and pricing strategy"
- "What's AGROINDUSTRIAS AIB's competitive positioning?"

**Parameters**:
```
exporter_name: Company name (fuzzy match supported)
include_diversification: Calculate diversification scores (default true)
include_market_position: Include competitive positioning (default true)
```

**Sample Response**:
```json
{
  "exporter": "CAMPOSOL S.A.",
  "product_portfolio": {
    "unique_products": 15,
    "products": [
      {
        "fruit": "mango",
        "format": "chunks",
        "certification": "organic",
        "volume_mt": 1250.50,
        "avg_price": 2500.00,
        "shipment_count": 45
      }
    ]
  },
  "geographic_reach": {
    "countries_served": 12,
    "destinations": [
      {"country": "United States", "volume_mt": 2500.00, "shipment_count": 120}
    ]
  },
  "diversification": {
    "product_concentration_hhi": 2250.5,
    "product_diversity": "medium",
    "geographic_concentration_hhi": 3500.0,
    "geographic_diversity": "low"
  },
  "market_position": {
    "overall_market_share_pct": 5.5,
    "avg_price_positioning": 8.5,
    "price_tier": "premium"
  }
}
```

**Diversification Levels**:
- **High diversity** (HHI < 2500): Well-diversified across products/countries
- **Medium diversity** (HHI 2500-5000): Moderate concentration
- **Low diversity** (HHI > 5000): Highly concentrated in few products/countries

---

### 8. `analyze_price_dynamics` ⭐ NEW

**Purpose**: Comprehensive price analysis with organic premium and regional comparisons.

**Key Features**:
- Price statistics: min, max, avg, median, std dev
- Weighted average price (volume-weighted)
- Coefficient of variation (price volatility)
- Organic vs conventional premium calculation
- Europe vs Rest of World price gap analysis
- Organic market share percentage
- Sample size for statistical confidence

**Example Questions**:
- "What's the organic premium for mango chunks?"
- "Analyze blueberry price volatility this year"
- "Do Europe prices differ from Rest of World for strawberries?"
- "Show me comprehensive price stats for avocado halves"

**Parameters**:
```
fruit: Fruit type (required)
format_type: Optional format filter
size: Optional size filter
include_organic_premium: Compare organic vs conventional (default true)
include_regional_gaps: Compare Europe vs RoW (default true)
start_date: Analysis period (default 'last_365_days')
```

**Sample Response**:
```json
{
  "fruit": "mango",
  "format": "chunks",
  "size": "20x20",
  "period": "last_365_days",
  "sample_size": 1250,
  "price_statistics": {
    "avg_price_usd_per_mt": 2300.50,
    "weighted_avg_price": 2285.75,
    "min_price": 1800.00,
    "max_price": 2900.00,
    "price_range": 1100.00,
    "std_deviation": 250.50,
    "coefficient_of_variation_pct": 10.9
  },
  "organic_analysis": {
    "organic_avg_price": 2500.00,
    "conventional_avg_price": 2200.00,
    "organic_premium_pct": 13.6,
    "organic_volume_mt": 500.00,
    "conventional_volume_mt": 1800.00,
    "organic_market_share_pct": 21.7
  },
  "regional_analysis": {
    "europe_avg_price": 2450.00,
    "rest_of_world_avg_price": 2250.00,
    "europe_premium_pct": 8.9,
    "europe_volume_mt": 800.00,
    "rest_of_world_volume_mt": 1500.00
  }
}
```

**Price Volatility Guide** (Coefficient of Variation):
- **< 10%**: Low volatility (stable prices)
- **10-20%**: Moderate volatility
- **> 20%**: High volatility (unstable/seasonal prices)

---

### 9-11. Original Query Tools

**`query_by_exporter`**
- Find exports by company name with fuzzy matching
- Filter by destination region, country, or fruit
- Returns export records with product specs and prices

**`query_by_destination`**
- Query exports to specific country (English or Spanish supported)
- Filter by fruit and certification
- Automatic country name translation

**`query_by_product`**
- Query by fruit, format, size, or certification
- Filter by destination
- Find specific product configurations

---

### 12-14. Original Analysis Tools

**`analyze_seasonality`**
- Monthly export patterns and trends
- Peak and low seasons identification
- Optional year filter
- Volume and shipment count by month

**`get_price_analysis`**
- Price statistics by product and destination
- Min, average, max prices
- Total volume and value
- Weighted average calculations

**`summarize_by_region`**
- Europe vs Rest of World breakdown
- Regional totals and averages
- Country-level details optional
- Supports fruit filtering

---

### 15-17. Original Comparison Tools

**`compare_products`**
- Side-by-side product comparison
- Volume, price, and shipment metrics
- Up to 5 products at once
- Certification and format filtering

**`compare_exporters`**
- Performance comparison between exporters
- Total volume, average price, destinations
- Product mix analysis
- Fuzzy name matching

**`compare_periods`**
- Compare two time periods
- Absolute and percentage changes
- Volume and price trends
- Supports fruit and exporter filters

---

### 18-19. Utility Tools

**`search_exporters`**
- Fuzzy search for exporter names
- Handles typos and partial matches
- Returns top 10 matches with export counts
- Quick exporter name verification

**`get_available_values`**
- List all unique values for a field
- Fields: fruits, formats, sizes, exporters, destinations, certifications
- Sorted by total volume
- Useful for discovering available options

---

## Common Use Cases

### 1. Market Research

**"I want to understand the mango market"**

```
Step 1: Get market overview
→ Ask: "Show me dashboard metrics for mango exports YTD"

Step 2: Identify key players
→ Ask: "Who are the top 15 mango exporters by volume?"

Step 3: Analyze market concentration
→ Ask: "What's the market share distribution for mango exporters?"

Step 4: Understand pricing
→ Ask: "Analyze mango price dynamics including organic premium"

Step 5: Track trends
→ Ask: "Show mango export volume trends monthly for last year"
```

---

### 2. Competitive Intelligence

**"I want to benchmark against competitors"**

```
Step 1: Analyze your portfolio
→ Ask: "Analyze [YOUR COMPANY]'s product portfolio and market position"

Step 2: Compare to competitors
→ Ask: "Compare exporters: [YOUR COMPANY], [COMPETITOR 1], [COMPETITOR 2]"

Step 3: Check market share
→ Ask: "What's [YOUR COMPANY]'s market share in organic mangoes to Europe?"

Step 4: Benchmark pricing
→ Ask: "Show price analysis for mango chunks - where do I stand?"
```

---

### 3. Pricing Strategy

**"Should I price my organic blueberries higher?"**

```
Step 1: Check organic premium
→ Ask: "What's the organic premium for blueberries?"

Step 2: Analyze regional differences
→ Ask: "Analyze blueberry price dynamics including regional gaps"

Step 3: Check market prices
→ Ask: "Get price analysis for organic blueberries to Europe"

Step 4: Track price trends
→ Ask: "Show organic blueberry price trends monthly for last year"
```

---

### 4. Market Entry Analysis

**"Should I enter the Germany market with organic strawberries?"**

```
Step 1: Check market size
→ Ask: "Show all strawberry exports to Germany YTD"

Step 2: Identify competition
→ Ask: "Who are the top exporters of strawberries to Germany?"

Step 3: Check price levels
→ Ask: "What are strawberry prices in Germany vs other markets?"

Step 4: Analyze trends
→ Ask: "Show strawberry export trends to Germany for last 12 months"
```

---

### 5. Quarterly Business Review

**"Generate Q1 2024 performance report"**

```
Step 1: Get KPI dashboard
→ Ask: "Show dashboard metrics for Q1 2024 compared to previous quarter"

Step 2: Export detailed data
→ Ask: "Export all Q1 2024 data to CSV"

Step 3: Identify top products
→ Ask: "What were the top 10 products in Q1 2024 by volume?"

Step 4: Check destinations
→ Ask: "Show top destinations in Q1 2024 with market share"

Step 5: Analyze growth
→ Ask: "Show time-series analysis of volume for Q1 2024 weekly"
```

---

### 6. Product Launch Planning

**"Planning to launch organic mango cubes 15x15mm"**

```
Step 1: Check existing market
→ Ask: "Find all mango cubes 15x15mm exports"

Step 2: Analyze pricing
→ Ask: "Analyze price dynamics for mango cubes 15x15mm"

Step 3: Check organic premium
→ Ask: "What's the organic premium for mango cubes?"

Step 4: Identify target markets
→ Ask: "Show top destinations for organic mango cubes"

Step 5: Benchmark competitors
→ Ask: "Who exports organic mango cubes and at what prices?"
```

---

## Date Filtering Guide

The MCP supports flexible date filtering across most tools. Here's your complete guide:

### Relative Dates (Recommended)

| Date String | Meaning | Example Period |
|------------|---------|----------------|
| `today` | Today only | 2024-11-08 |
| `yesterday` | Yesterday only | 2024-11-07 |
| `last_7_days` | Last 7 days | 2024-11-01 to 2024-11-08 |
| `last_30_days` | Last 30 days | 2024-10-09 to 2024-11-08 |
| `last_90_days` | Last 90 days | 2024-08-10 to 2024-11-08 |
| `last_365_days` | Last year | 2023-11-08 to 2024-11-08 |
| `mtd` | Month to date | 2024-11-01 to 2024-11-08 |
| `qtd` | Quarter to date | 2024-10-01 to 2024-11-08 |
| `ytd` | Year to date | 2024-01-01 to 2024-11-08 |

### Quarter Dates

| Date String | Meaning | Period |
|------------|---------|--------|
| `q1_2024` | Q1 2024 | Jan 1 - Mar 31, 2024 |
| `q2_2024` | Q2 2024 | Apr 1 - Jun 30, 2024 |
| `q3_2024` | Q3 2024 | Jul 1 - Sep 30, 2024 |
| `q4_2024` | Q4 2024 | Oct 1 - Dec 31, 2024 |

### Absolute Dates

Use ISO format: `YYYY-MM-DD`

Examples:
- `2024-01-01` - January 1, 2024
- `2024-06-30` - June 30, 2024
- `2025-10-30` - October 30, 2025

### Date Range Examples

```
"Show exports from last quarter"
→ start_date="qtd"

"Get all Q1 2024 shipments"
→ start_date="q1_2024", end_date="2024-03-31"

"Last 6 months of data"
→ start_date="last_180_days"

"Year to date performance"
→ start_date="ytd"

"Specific date range"
→ start_date="2024-01-01", end_date="2024-06-30"
```

---

## Tips & Best Practices

### 🎯 Getting Accurate Results

1. **Use specific fruit names**: "mango" instead of "mangoes" or "mangos"
2. **Check available values first**: Use `get_available_values` to see exact fruit names, formats, etc.
3. **Fuzzy matching works**: Exporter names don't need to be exact (e.g., "camposol" finds "CAMPOSOL S.A.")
4. **Language flexible**: Destination countries work in English or Spanish ("Germany" or "ALEMANIA")

### 📊 Data Quality Tips

1. **Check sample sizes**: Look at `sample_size` in results to assess statistical confidence
2. **Filter out noise**: Use `min_volume_mt` to exclude small shipments
3. **Use weighted averages**: For price analysis, weighted averages are more accurate than simple averages
4. **Watch for seasonality**: Fruit exports are highly seasonal - compare same periods year-over-year

### ⚡ Performance Tips

1. **Use date ranges**: Narrow queries with date filters for faster results
2. **Limit results**: Use the `limit` parameter for large queries
3. **Export for deep analysis**: Use `export_data` for large datasets instead of querying repeatedly
4. **Cache common queries**: Dashboard metrics and market share calculations can be saved

### 🧮 Analysis Best Practices

1. **Market Share**: HHI < 1500 = competitive, HHI > 2500 = concentrated
2. **Price Volatility**: CV < 10% = stable, CV > 20% = volatile
3. **Growth Rates**: Compare YoY (year-over-year) for true growth, MoM shows seasonality
4. **Organic Premium**: Typical range is 10-30% for most fruits
5. **Regional Gaps**: Europe typically pays 5-15% premium over Rest of World

### 🎨 Visualization Tips

When exporting data for visualization:

1. **Time-series**: Use `get_time_series_analysis` → export to line charts
2. **Market share**: Use `get_market_share` → export to pie charts
3. **Rankings**: Use `get_top_n` → export to bar charts
4. **Comparisons**: Use comparison tools → export to grouped bar charts
5. **Distributions**: Use `analyze_price_dynamics` → export to histograms

### ❓ Troubleshooting

**"No results found"**
- Check fruit spelling (use `get_available_values` field='fruits')
- Try broader date range
- Check if filters are too restrictive

**"Exporter not found"**
- Use `search_exporters` to find correct name
- Fuzzy matching is automatic but try partial names

**"Price analysis shows no organic data"**
- Not all products have organic certification
- Try different fruit or remove certification filter

**"Time-series has few data points"**
- Product might be seasonal
- Try broader date range
- Check if product/filter combination is too specific

---

## Data Dictionary

### Fruit Types (20 available)
- **Primary**: mango, avocado, blueberry
- **Berries**: strawberry, raspberry, blackberry, golden_berry
- **Tropical**: pineapple, papaya, passion_fruit, banana
- **Peruvian Specialties**: lucuma, cherimoya, camu_camu, soursop
- **Other**: pomegranate, grape, cherry, peach, orange, pitaya, acai

### Format Types (13 available)
- **Cut Formats**: chunks, cubes, slices, halves, strips
- **Processed**: puree, pulp, concentrate, juice
- **Whole**: whole, iqf (individually quick frozen)
- **Other**: broken_pieces, unknown

### Common Sizes
- **Chunks**: 20x20, 25x25, 15x15, 10x10 (mm)
- **Strawberries**: 6x48, 8x48, 12x48 (mm)
- **Package codes**: 1x10, 1x30 (kg configurations)

### Certification Types
- `organic` - Certified organic
- `conventional` - Non-organic
- `unknown` - Not specified

### Regions
- `Europe` - 16 European countries
- `Rest of World` - 41 countries globally

### Top Destinations
1. United States (60,925 MT)
2. Belgium (21,220 MT)
3. Netherlands (20,693 MT)
4. Chile (15,815 MT)
5. Canada (15,451 MT)

---

## Support & Resources

### Need Help?

1. **Check available values**: `get_available_values` to see all fruits, formats, etc.
2. **Search exporters**: `search_exporters` to find company names
3. **Try simpler queries**: Start broad, then add filters
4. **Check date ranges**: Ensure dates are within dataset range (Jan 2024 - Oct 2025)

### Dataset Coverage

- **Date Range**: January 1, 2024 - October 30, 2025 (22 months)
- **Total Records**: 14,279 export shipments
- **Total Volume**: 218,281.75 MT
- **Total Value**: $507.8M FOB
- **Data Quality**: 99.7% fruit identification rate

### Updates

This MCP is based on the enriched dataset with:
- ✅ Spanish → English translation
- ✅ Structured product parsing
- ✅ Calculated metrics (USD/MT, net MT)
- ✅ Regional classification
- ✅ Organic/conventional labeling

---

## Quick Reference Card

### Most Useful Tools

| Task | Tool | Example |
|------|------|---------|
| Quick overview | `get_dashboard_metrics` | "Show YTD dashboard" |
| Rankings | `get_top_n` | "Top 10 exporters" |
| Market share | `get_market_share` | "Mango market share" |
| Price analysis | `analyze_price_dynamics` | "Mango price analysis" |
| Trends | `get_time_series_analysis` | "Monthly volume trends" |
| Export data | `export_data` | "Export Q1 data to CSV" |
| Portfolio analysis | `analyze_exporter_portfolio` | "Analyze CAMPOSOL" |
| Date filtering | `query_with_date_range` | "Last 30 days, mango" |

### Date Shortcuts

- `ytd` - Year to date
- `qtd` - Quarter to date
- `mtd` - Month to date
- `last_30_days` - Last month
- `last_90_days` - Last quarter
- `q1_2024` - Q1 2024

### Key Metrics

- **Volume**: Metric tons (MT)
- **Value**: FOB USD (Free On Board)
- **Price**: USD per MT
- **HHI**: Market concentration (0-10,000)
- **CV**: Coefficient of variation (price volatility %)

---

**Version**: 1.0
**Last Updated**: November 2024
**Tools**: 19 total (11 original + 8 new)
**Dataset**: Peru Frozen Fruit Exports 2024-2025
