# Europe Fruit Analyzer - User Guide

## Overview

The **`analyze_europe_by_fruit`** tool provides comprehensive country-by-country analysis of European markets for a specific fruit. Perfect for answering: *"What does each European country look like for mangoes?"*

---

## What It Analyzes

For **each European country**, you get:

### 1. **Market Metrics**
- Total volume (MT)
- Total FOB value (USD)
- Shipment count
- Market share % of total Europe
- Average shipment size

### 2. **Price Analysis**
- Average price (USD/MT)
- Price range (min/max)
- Price volatility %
- Price tier (premium/mid-market/economy)

### 3. **Product Breakdown**
- Top 5 product configurations (format, size, certification)
- Organic vs Conventional split
- Organic percentage of market
- Product-specific pricing

### 4. **Supplier Analysis**
- Total supplier count
- Market concentration (HHI)
- Concentration level (competitive/moderate/highly concentrated)
- Top 5 suppliers with market shares

### 5. **Market Attractiveness Score (0-100)**
Automatically scores each country based on:
- **Market Size (0-30 pts):** Larger = better
- **Price Premium (0-25 pts):** Higher prices = better
- **Competition (0-25 pts):** Lower concentration = better
- **Organic Demand (0-20 pts):** Higher organic % = better

**Priority Levels:**
- **High (75-100):** Attractive markets to prioritize
- **Medium (60-74):** Moderate opportunities
- **Low (<60):** Limited attractiveness

---

## How to Use

### Basic Query
```
"Analyze European countries for mango exports"
```

### With Date Range
```
"Show me blueberry markets in Europe for Q1 2024"
```

### Focused Analysis
```
"What does each European country look like for organic strawberries?"
```

---

## Example Output

### Query: *"Analyze European countries for mango"*

```json
{
  "summary": {
    "fruit": "mango",
    "analysis_period": "ytd",
    "total_europe_volume_mt": 12543.50,
    "total_europe_value_usd": 31358750.00,
    "avg_europe_price_usd_per_mt": 2500.00,
    "countries_analyzed": 15,
    "priority_breakdown": {
      "high_priority": 5,
      "medium_priority": 7,
      "low_priority": 3
    },
    "top_3_markets": [
      {
        "country": "Netherlands",
        "volume_mt": 3250.00,
        "market_share_pct": 25.9,
        "attractiveness_score": 85
      },
      {
        "country": "Germany",
        "volume_mt": 2800.00,
        "market_share_pct": 22.3,
        "attractiveness_score": 80
      },
      {
        "country": "Belgium",
        "volume_mt": 1950.00,
        "market_share_pct": 15.5,
        "attractiveness_score": 75
      }
    ]
  },
  "country_analyses": [
    {
      "country": "Netherlands",
      "market_metrics": {
        "volume_mt": 3250.00,
        "fob_value_usd": 8125000.00,
        "shipment_count": 245,
        "market_share_volume_pct": 25.9,
        "market_share_value_pct": 25.9,
        "avg_shipment_size_mt": 13.27
      },
      "price_analysis": {
        "avg_price_usd_per_mt": 2500.00,
        "min_price": 1800.00,
        "max_price": 3200.00,
        "price_range_usd": 1400.00,
        "price_volatility_pct": 77.8,
        "price_tier": "mid-market"
      },
      "product_breakdown": {
        "top_products": [
          {
            "format": "chunks",
            "size": "20x20",
            "certification": "organic",
            "volume_mt": 850.00,
            "avg_price": 2800.00,
            "shipments": 65
          },
          {
            "format": "chunks",
            "size": "25x25",
            "certification": "conventional",
            "volume_mt": 620.00,
            "avg_price": 2200.00,
            "shipments": 48
          }
        ],
        "certification_split": {
          "organic": {
            "volume_mt": 1300.00,
            "percentage": 40.0,
            "avg_price": 2850.00
          },
          "conventional": {
            "volume_mt": 1450.00,
            "percentage": 44.6,
            "avg_price": 2250.00
          },
          "unknown": {
            "volume_mt": 500.00,
            "percentage": 15.4,
            "avg_price": 2400.00
          }
        },
        "organic_percentage": 40.0
      },
      "supplier_analysis": {
        "supplier_count": 12,
        "concentration_hhi": 1250.50,
        "concentration_level": "competitive",
        "top_suppliers": [
          {
            "rank": 1,
            "exporter": "CAMPOSOL S.A.",
            "volume_mt": 650.00,
            "market_share_pct": 20.0,
            "avg_price": 2650.00,
            "shipments": 48
          },
          {
            "rank": 2,
            "exporter": "DANPER",
            "volume_mt": 480.00,
            "market_share_pct": 14.8,
            "avg_price": 2550.00,
            "shipments": 35
          }
        ]
      },
      "market_attractiveness": {
        "score": 85,
        "priority": "high",
        "recommendation": "Attractive market: Large size, good pricing, and favorable competition.",
        "score_breakdown": {
          "market_size": 30,
          "price_premium": 20,
          "competition": 25,
          "organic_demand": 10
        }
      }
    },
    // ... more countries
  ]
}
```

---

## Interpreting Results

### Market Share %
- **>20%**: Dominant market in Europe
- **10-20%**: Major market
- **5-10%**: Significant market
- **<5%**: Niche market

### Price Tiers
- **Premium**: >$2,500/MT - High-value market
- **Mid-market**: $2,000-$2,500/MT - Standard market
- **Economy**: <$2,000/MT - Price-sensitive market

### Concentration Levels (HHI)
- **Competitive** (HHI < 1,500): Many suppliers, easy entry
- **Moderately Concentrated** (1,500-2,500): Some consolidation
- **Highly Concentrated** (>2,500): Few dominant suppliers

### Attractiveness Scores
- **85-100**: Top-tier markets - prioritize immediately
- **75-84**: Strong markets - excellent opportunities
- **60-74**: Good markets - consider with strategy
- **<60**: Limited markets - entry barriers or small size

---

## Use Cases

### 1. Market Entry Strategy
**Question:** *"Which European countries should we target for organic blueberries?"*

**Use the tool:**
```
analyze_europe_by_fruit(
    fruit='blueberry',
    start_date='ytd'
)
```

**Look for:**
- High attractiveness scores (>75)
- High organic percentage (>30%)
- Competitive supplier landscape (HHI < 1,500)
- Growing market share

**Decision:** Enter top 3 scored markets first

---

### 2. Competitive Analysis
**Question:** *"Where do we have the strongest position in Europe for mangoes?"*

**Use the tool:**
```
analyze_europe_by_fruit(
    fruit='mango',
    include_supplier_analysis=True
)
```

**Look for:**
- Countries where your company is in top 5 suppliers
- Your market share % in each country
- Concentration levels where you're competitive

**Decision:** Double down on markets where you're #1-#3

---

### 3. Pricing Strategy
**Question:** *"Which European countries pay premium prices for organic strawberries?"*

**Use the tool:**
```
analyze_europe_by_fruit(
    fruit='strawberry',
    include_price_analysis=True,
    include_product_breakdown=True
)
```

**Look for:**
- Price tier = "premium"
- High organic percentage
- Organic avg_price vs conventional avg_price gap

**Decision:** Focus organic production for premium markets

---

### 4. Product Mix Optimization
**Question:** *"What product formats are popular in each European country for pineapple?"*

**Use the tool:**
```
analyze_europe_by_fruit(
    fruit='pineapple',
    include_product_breakdown=True
)
```

**Look at:**
- `top_products` list per country
- Format (chunks, slices, puree, etc.)
- Size preferences
- Certification preferences

**Decision:** Tailor product mix per target country

---

### 5. Opportunity Scanning
**Question:** *"Show me all underserved European markets for avocado"*

**Use the tool:**
```
analyze_europe_by_fruit(
    fruit='avocado',
    min_market_size_mt=50.0
)
```

**Filter results by:**
- High attractiveness score (>75)
- Low supplier count (<5)
- Competitive concentration (HHI < 1,500)

**Decision:** Enter markets with high scores + low competition

---

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `fruit` | str | **Required** | Fruit type (e.g., 'mango', 'blueberry') |
| `start_date` | str | `'ytd'` | 'ytd', 'q1_2024', 'last_90_days', etc. |
| `min_market_size_mt` | float | `10.0` | Minimum market size to include |
| `include_product_breakdown` | bool | `True` | Show format/size/certification details |
| `include_price_analysis` | bool | `True` | Show price statistics |
| `include_supplier_analysis` | bool | `True` | Show supplier concentration and top suppliers |

---

## Tips for Best Results

### 1. **Choose the Right Date Range**
- **YTD**: Current year trends
- **Last 90 days**: Recent activity
- **Q1_2024**: Specific quarter comparison
- **Last 365 days**: Full annual picture

### 2. **Filter by Market Size**
- **Large markets:** `min_market_size_mt=100`
- **All markets:** `min_market_size_mt=10`
- **Major markets only:** `min_market_size_mt=500`

### 3. **Focus Your Analysis**
- **Quick overview:** Set all `include_*` to `False`, look at summary
- **Deep dive:** Keep all `include_*` as `True`
- **Pricing focus:** Only `include_price_analysis=True`

### 4. **Interpret Scores Holistically**
Don't just look at attractiveness score alone:
- **Large + Competitive = Great for volume play**
- **Small + Premium + Low competition = Niche opportunity**
- **Large + Concentrated = Need strong partnerships**

---

## Common Questions

### Q: Why is a country not showing up?
**A:** Market size is below `min_market_size_mt` threshold. Lower it to see smaller markets.

### Q: What does "unknown" certification mean?
**A:** The commercial description didn't specify organic or conventional. Common in older data.

### Q: How is HHI calculated?
**A:** Σ(market_share_i)² for all suppliers. Higher = more concentrated.

### Q: Can I compare multiple fruits?
**A:** Run the tool multiple times and compare results manually, or ask Claude to compare outputs.

### Q: What if I want Rest of World instead of Europe?
**A:** This tool is Europe-specific. Use `query_by_destination` for non-European countries.

---

## Integration with Other Tools

### Combined with Market Gaps
```
Step 1: analyze_europe_by_fruit(fruit='mango')
        → Find countries with high scores

Step 2: identify_market_gaps(target_country='Germany', product_category='mango')
        → Find specific product opportunities
```

### Combined with Exporter Readiness
```
Step 1: analyze_europe_by_fruit(fruit='blueberry')
        → Identify top 3 European markets

Step 2: analyze_europe_readiness(exporter_name='CAMPOSOL')
        → Check if exporter can serve those markets
```

### Combined with Competitor Benchmarking
```
Step 1: analyze_europe_by_fruit(fruit='strawberry')
        → See supplier landscape per country

Step 2: benchmark_europe_competitors(exporter_name='SUNSHINE', fruit='strawberry')
        → Understand your competitive position
```

---

## Performance

- **Query time:** ~500-1000ms (depends on data volume)
- **Cacheable:** No (dynamic analysis)
- **Memory:** Low (streams results)

---

## Example Insights

### Insight 1: Premium Organic Markets
```
Netherlands: 40% organic @ $2,850/MT avg
Germany: 35% organic @ $2,900/MT avg
→ Focus organic production for these markets
```

### Insight 2: Competitive Entry Points
```
Poland: 5 suppliers, HHI 850 (competitive), Score 78 (high)
→ Easy market entry with good opportunity
```

### Insight 3: Price Optimization
```
Belgium: Avg $2,400/MT, Range $1,800-$3,200
→ 77% price volatility = opportunity for premium positioning
```

### Insight 4: Product Mix Strategy
```
UK: Top product = Chunks 20x20 organic (850 MT)
France: Top product = Slices 25x25 conventional (620 MT)
→ Different products for different countries
```

---

## Troubleshooting

### "No European market data found"
- Check fruit spelling (use `get_available_values(field='fruits')`)
- Try broader date range
- Lower `min_market_size_mt`

### Too many countries (overwhelming)
- Increase `min_market_size_mt` to 100 or 200
- Focus on top 5 by filtering results

### Missing supplier analysis
- Set `include_supplier_analysis=True`
- Check if data has supplier information

---

## Summary

**`analyze_europe_by_fruit`** is your go-to tool for:
- ✅ Understanding European country landscapes per fruit
- ✅ Identifying high-potential markets
- ✅ Optimizing pricing strategies
- ✅ Analyzing competitive dynamics
- ✅ Tailoring product mix per country

**Perfect for:** Market entry, competitive intelligence, pricing strategy, and opportunity identification.

---

**Version:** 1.0
**Added:** November 2024
**Module:** `mcp_europe_intelligence.py`
**Related Tools:** `identify_market_gaps`, `analyze_europe_readiness`, `benchmark_europe_competitors`
