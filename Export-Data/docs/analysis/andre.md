# Lithuania Multi-Product Market Analysis - Example

## Your Query

**"How does the market in Lithuania look for these:**
- Mango chunks, dices
- Pineapple chunks
- Maracuya (passion fruit) cubes 20x20 or 25x25
- Fresa (strawberry) halves, cubes about 10x10
- Blueberries class A
- Papaya pulp, cubes
- Avocado cubes
- Ginger
- Chirimoya (cherimoya)
- Clementine puree
- Pitahaya (dragon fruit) cubes"

---

## How to Use the New Tool

### **Tool:** `analyze_country_multi_product`

This tool analyzes **multiple products simultaneously** for a target country, and **automatically references neighboring countries** when the target country has no imports.

---

## Example Query for Your Case

```python
analyze_country_multi_product(
    target_country="Lithuania",
    products=[
        {"fruit": "mango", "format": "chunks"},
        {"fruit": "mango", "format": "cubes"},
        {"fruit": "pineapple", "format": "chunks"},
        {"fruit": "passion_fruit", "format": "cubes", "size": "20x20"},
        {"fruit": "passion_fruit", "format": "cubes", "size": "25x25"},
        {"fruit": "strawberry", "format": "halves"},
        {"fruit": "strawberry", "format": "cubes", "size": "10x10"},
        {"fruit": "blueberry"},
        {"fruit": "papaya", "format": "pulp"},
        {"fruit": "papaya", "format": "cubes"},
        {"fruit": "avocado", "format": "cubes"},
        {"fruit": "ginger"},
        {"fruit": "cherimoya"},
        {"fruit": "orange", "format": "puree"},  # Clementine puree
        {"fruit": "pitaya", "format": "cubes"}
    ],
    start_date="ytd",
    use_neighbor_reference=True
)
```

Or simply ask Claude:

> **"How does the market in Lithuania look for: mango chunks, pineapple chunks, passion fruit cubes 20x20, strawberry halves, blueberries, papaya pulp and cubes, avocado cubes, ginger, cherimoya, clementine puree, and pitahaya cubes?"**

---

## What You'll Get

### **Example Output Structure:**

```json
{
  "target_country": "Lithuania",
  "analysis_period": "ytd",
  "products_analyzed": 15,
  "summary": {
    "active_markets": 3,          // Products with imports in Lithuania
    "no_imports": 12,              // Products with no Lithuania imports
    "neighbor_references_provided": 10  // Products with neighbor data
  },
  "neighbors_available": ["Poland", "Latvia", "Estonia"],

  "product_analyses": [

    // SCENARIO 1: Active Market in Lithuania
    {
      "product": "blueberry",
      "product_specs": {"fruit": "blueberry"},
      "target_country": "Lithuania",
      "target_market": {
        "status": "active",
        "volume_mt": 145.50,
        "fob_value_usd": 435000.00,
        "shipment_count": 23,
        "avg_price_usd_per_mt": 2989.00,
        "price_range": {
          "min": 2500.00,
          "max": 3500.00
        },
        "supplier_count": 4,
        "top_suppliers": [
          {
            "exporter": "CAMPOSOL S.A.",
            "volume_mt": 65.00,
            "market_share_pct": 44.7,
            "avg_price": 3100.00,
            "shipments": 10
          },
          {
            "exporter": "DANPER",
            "volume_mt": 45.00,
            "market_share_pct": 30.9,
            "avg_price": 2950.00,
            "shipments": 7
          }
        ],
        "recommendation": "Active market with 23 shipments. Avg price: $2,989/MT. 4 suppliers currently serving this market."
      }
    },

    // SCENARIO 2: No Lithuania Imports - References Neighbors
    {
      "product": "mango chunks",
      "product_specs": {"fruit": "mango", "format": "chunks"},
      "target_country": "Lithuania",
      "target_market": {
        "status": "no_imports",
        "message": "No mango chunks imports found in Lithuania",
        "recommendation": "Consider market entry. Similar neighboring countries show active demand."
      },
      "reference_markets": {
        "neighbors_analyzed": 3,
        "active_neighbors": 2,
        "closest_markets": [
          {
            "country": "Poland",
            "volume_mt": 850.00,
            "fob_value_usd": 2125000.00,
            "shipment_count": 68,
            "avg_price_usd_per_mt": 2500.00,
            "supplier_count": 12
          },
          {
            "country": "Latvia",
            "volume_mt": 45.00,
            "fob_value_usd": 115200.00,
            "shipment_count": 5,
            "avg_price_usd_per_mt": 2560.00,
            "supplier_count": 3
          }
        ],
        "market_potential_estimate": {
          "conservative_mt": 255.00,     // 30% of Poland's 850 MT
          "moderate_mt": 425.00,          // 50% of Poland's 850 MT
          "optimistic_mt": 595.00,        // 70% of Poland's 850 MT
          "basis": "Based on Poland"
        },
        "insights": [
          "Poland: 850.00 MT @ $2,500/MT (12 suppliers)",
          "Latvia: 45.00 MT @ $2,560/MT (3 suppliers)"
        ]
      }
    },

    // SCENARIO 3: No Data Anywhere
    {
      "product": "cherimoya",
      "product_specs": {"fruit": "cherimoya"},
      "target_country": "Lithuania",
      "target_market": {
        "status": "no_imports",
        "message": "No cherimoya imports in Lithuania or neighboring countries",
        "recommendation": "Limited regional demand. Consider focusing on other products or markets."
      }
    }
  ],

  "overall_recommendation": "Lithuania has limited current imports (3/15 products), but neighboring countries show demand. Good opportunity for market entry based on regional trends."
}
```

---

## Interpreting the Results

### **Status Types:**

1. **"active"** - Lithuania imports this product
   - ✅ **Action:** Review suppliers, pricing, and market share
   - ✅ **Opportunity:** Enter or expand in existing market

2. **"no_imports" with reference_markets** - No Lithuania imports, but neighbors import
   - ✅ **Action:** Review neighbor markets (especially Poland, Latvia)
   - ✅ **Opportunity:** Market entry based on regional demand
   - 📊 **Use market_potential_estimate** for sizing

3. **"no_imports" without reference_markets** - No regional demand
   - ⚠️ **Action:** Deprioritize this product for Lithuania/region
   - ⚠️ **Opportunity:** Low - focus on other products

---

## Geographic Neighbor Logic

### **Lithuania's Neighbors (by proximity):**
1. **Poland** (largest economy, most trade)
2. **Latvia** (Baltic neighbor, similar market)
3. **Estonia** (Baltic neighbor, smaller market)

### **Why This Matters:**

**Similar markets due to:**
- ✅ Geographic proximity → similar logistics costs
- ✅ Cultural similarities → similar consumer preferences
- ✅ Economic integration (EU) → similar regulations
- ✅ Shared supply chains → same importers may serve multiple countries

**Market Potential Estimates:**
- **Conservative (30%):** Lithuania = 30% of Poland's volume
- **Moderate (50%):** Lithuania = 50% of Poland's volume
- **Optimistic (70%):** Lithuania = 70% of Poland's volume

*Based on population ratios and economic similarity*

---

## Expected Results for Your Products

### **Likely Active in Lithuania:**
- ✅ **Blueberries** (Poland imports 1,000+ MT, likely Lithuania too)
- ✅ **Strawberries** (Common in Baltic region)
- ⚠️ **Possibly mango** (Poland imports heavily)

### **Likely No Imports, But Strong Neighbor Reference:**
- 📊 **Mango chunks/cubes** (Poland: 800-1,000 MT/year)
- 📊 **Pineapple chunks** (Poland: 400-600 MT/year)
- 📊 **Passion fruit cubes** (Poland: 50-100 MT/year)
- 📊 **Papaya pulp/cubes** (Poland: 100-200 MT/year)
- 📊 **Avocado cubes** (Poland/Latvia: 200-400 MT/year)

### **Likely No Regional Demand:**
- ❌ **Ginger** (Limited European frozen ginger demand)
- ❌ **Cherimoya** (Rare/exotic, limited market)
- ❌ **Pitahaya cubes** (Emerging, limited data)
- ❌ **Clementine puree** (Not common in frozen form)

---

## How to Use This Information

### **For Products with Active Lithuania Market:**

1. **Enter the Market:**
   - Contact top importers already active
   - Price competitively (match or beat current avg)
   - Highlight quality/certifications

2. **Example: Blueberries in Lithuania**
   ```
   Current market: 145 MT @ $2,989/MT
   Top supplier: CAMPOSOL (44.7% share)

   → Opportunity: 4 suppliers = competitive market
   → Entry strategy: Offer 50 MT @ $2,850/MT (below average)
   → Target: 30-40 MT first year (20% market penetration)
   ```

---

### **For Products with No Lithuania Imports + Poland Reference:**

1. **Market Entry Strategy:**
   - Use Poland data as market sizing proxy
   - Target 30-50% of Poland's volume for Lithuania
   - Contact Polish importers who might expand to Lithuania

2. **Example: Mango Chunks**
   ```
   Poland market: 850 MT @ $2,500/MT (12 suppliers)
   Lithuania potential: 255-425 MT (conservative to moderate)

   → Entry strategy:
      1. Contact 2-3 Polish importers with Baltic presence
      2. Offer test shipments: 20-30 MT
      3. Price: $2,400-$2,500/MT (match Poland pricing)
      4. Year 1 target: 100 MT (conservative estimate)
   ```

3. **Example: Passion Fruit Cubes 20x20**
   ```
   Poland market: 75 MT @ $3,200/MT (5 suppliers)
   Lithuania potential: 23-38 MT (conservative to moderate)

   → Entry strategy:
      1. Niche product = less competition
      2. Target: 15-20 MT first year
      3. Premium positioning: $3,100-$3,300/MT
      4. Focus on organic if available (higher margins)
   ```

---

### **For Products with No Regional Demand:**

1. **Deprioritize:**
   - Focus efforts on products with proven demand
   - Cherimoya, ginger, pitahaya = low priority for Baltic region

2. **Alternative Strategy:**
   - Consider Western Europe instead (Germany, Netherlands, Belgium)
   - Use `analyze_europe_by_fruit` to find better markets

---

## Recommended Next Steps

### **Phase 1: Validate Active Markets**
```
For blueberries, strawberries:
→ Run: analyze_europe_by_fruit(fruit='blueberry')
→ Compare Lithuania to other Baltic/Nordic markets
→ Identify pricing and supplier landscape
```

### **Phase 2: Analyze Neighbor Markets in Detail**
```
For mango, pineapple, passion fruit:
→ Run: analyze_europe_by_fruit(fruit='mango')
→ Focus on Poland, Latvia, Estonia data
→ Contact active suppliers in those markets
```

### **Phase 3: Prioritize Products**
Based on results, create priority matrix:

| Product | Lithuania Status | Neighbor Volume | Priority | Year 1 Target |
|---------|------------------|-----------------|----------|---------------|
| Blueberries | Active (145 MT) | N/A | HIGH | 40-50 MT |
| Mango chunks | None | Poland 850 MT | HIGH | 80-100 MT |
| Strawberry halves | Active? | Poland 400 MT | HIGH | 50-70 MT |
| Pineapple chunks | None | Poland 500 MT | MEDIUM | 50-75 MT |
| Passion fruit cubes | None | Poland 75 MT | MEDIUM | 15-20 MT |
| Papaya cubes | None | Poland 150 MT | MEDIUM | 20-30 MT |
| Avocado cubes | None | Latvia 200 MT | LOW | 20-30 MT |
| Ginger | None | None | SKIP | - |
| Cherimoya | None | None | SKIP | - |

---

## Tool Parameters

```python
analyze_country_multi_product(
    target_country="Lithuania",              # Any European country

    products=[                                # List of products
        {"fruit": "mango", "format": "chunks"},
        {"fruit": "mango", "format": "cubes"},
        {"fruit": "blueberry"},              # Can omit format/size
        {"fruit": "passion_fruit", "format": "cubes", "size": "20x20"}
    ],

    start_date="ytd",                        # 'ytd', 'q1_2024', 'last_365_days'
    use_neighbor_reference=True,             # True = show neighbor data
    min_reference_market_size_mt=20.0       # Min size for neighbor to count
)
```

---

## All European Countries with Neighbors

The tool supports all European countries with pre-mapped neighbors:

**Baltic States:**
- Lithuania → Poland, Latvia, Estonia
- Latvia → Lithuania, Estonia, Poland
- Estonia → Latvia, Lithuania, Finland

**Central Europe:**
- Poland → Germany, Czech Republic, Lithuania, Latvia
- Germany → Poland, Netherlands, Belgium, France, Austria, Czech Republic
- Czech Republic → Germany, Poland, Austria, Slovakia

**Western Europe:**
- Netherlands → Belgium, Germany, France
- Belgium → Netherlands, France, Germany, Luxembourg
- France → Belgium, Germany, Switzerland, Italy, Spain

**Nordic:**
- Sweden → Norway, Finland, Denmark
- Finland → Sweden, Norway, Estonia
- Denmark → Germany, Sweden, Norway

**Southern:**
- Spain → France, Portugal
- Italy → France, Austria, Switzerland, Slovenia
- Greece → Bulgaria, Romania

*And more...*

---

## Summary

### **What This Tool Does:**

1. ✅ **Analyzes multiple products at once** (10-15 products in one query)
2. ✅ **Shows target country data** if it exists (active markets)
3. ✅ **References neighboring countries** when target has no imports
4. ✅ **Provides market sizing estimates** (conservative/moderate/optimistic)
5. ✅ **Recommends next actions** per product

### **Perfect For:**

- ✅ Market entry analysis (new countries)
- ✅ Product portfolio planning (which products to focus on)
- ✅ Regional demand assessment (is there appetite in the area?)
- ✅ Opportunity prioritization (high vs low potential)

### **Use When:**

> "I want to enter [COUNTRY] market. Which of my products have the best chance?"
>
> "How does Lithuania look for: mango, pineapple, blueberries, etc.?"
>
> "Should I target Baltic states? What's the demand there?"

---

**Tool Ready:** ✅ `analyze_country_multi_product`
**Module:** `mcp_europe_intelligence.py`
**Version:** 2.0 (with neighbor reference)

Enjoy your comprehensive multi-product market analysis! 🇱🇹🇵🇱🇪🇺
