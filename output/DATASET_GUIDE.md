# Peru Frozen Fruit Exports to Europe - Complete Dataset Guide

## 📁 Files Overview

### Main Detailed Datasets

#### 1. **europe_detailed_pricing_by_exporter_format.csv** ⭐ PRIMARY FILE
**360 unique combinations of Exporter × Format × Fruit**

This is your main file with granular pricing for each exporter's specific format offerings.

**Columns:**
- `fruit_name` - Type of fruit
- `Exporter` - Company name
- `format_type` - Product format (chunks, pulp, cubes, etc.)
- `Shipments` - Number of export records
- `Avg Price USD/MT` - Average price per metric ton
- `Median Price USD/MT` - Median price (more robust for outliers)
- `Std Dev` - Standard deviation (price variability)
- `Min Price USD/MT` - Minimum observed price
- `Max Price USD/MT` - Maximum observed price
- `Total Volume MT` - Total volume in metric tons
- `Destination Countries` - Where products were shipped
- `Organic` - Whether organic products were shipped (Yes/No)
- `IQF` - Whether IQF products were shipped (Yes/No)
- `Certifications` - Any certifications mentioned

**Example rows:**
```
fruit_name,Exporter,format_type,Shipments,Avg Price,Median Price,Min,Max,Volume MT
mango,VIRU S.A.,chunks,67,1850.00,1830.00,1300.00,2500.00,1234.5
mango,VIRU S.A.,puree,12,1050.00,830.73,666.09,1586.00,345.2
avocado,AGROEMPAQUES S.A.,chunks,78,2866.21,2750.00,2550.00,4520.88,1651.34
```

**Use this file when:**
- Comparing specific exporters for a particular format
- Analyzing which exporter offers the best price for a specific product
- Understanding price ranges by exporter and format

---

#### 2. **europe_pricing_pivot_exporter_format.csv**
**Pivot table format for quick comparisons**

Rows = Exporter + Format combination
Columns = Each fruit (median prices)

**Use this file when:**
- Quickly scanning which exporters offer which fruits
- Comparing prices across different fruits for the same exporter
- Identifying gaps in product offerings

**Example:**
```
Exporter                          | format  | mango  | avocado | blueberry |
VIRU S.A.                        | chunks  | 1830   | 2680    | -         |
AGROINDUSTRIA FRUTOS DE ORO      | chunks  | 1581   | 2581    | -         |
```

---

### Summary Files

#### 3. **europe_pricing_by_exporter.csv**
Summary of each exporter's pricing **aggregated across all formats**

**Columns:**
- `fruit_name`, `Exporter`
- `Shipments` - Total shipment records
- `Avg Price USD/MT`, `Median Price USD/MT`
- `Min Price USD/MT`, `Max Price USD/MT`
- `Total Volume MT`
- `Formats Offered` - List of all formats this exporter offers

**Use this file when:**
- Evaluating overall exporter competitiveness
- Identifying top exporters by volume
- Understanding an exporter's format diversity

---

#### 4. **europe_pricing_by_format.csv**
Summary of each format's pricing **aggregated across all exporters**

**Columns:**
- `fruit_name`, `format_type`
- `Shipments`, `Avg Price USD/MT`, `Median Price USD/MT`
- `Min Price USD/MT`, `Max Price USD/MT`
- `Total Volume MT`
- `Number of Exporters` - How many companies offer this format

**Use this file when:**
- Understanding market pricing for a specific format
- Identifying which formats are most competitive
- Finding format-specific price benchmarks

---

### Individual Fruit Files

#### 5. **by_fruit/** folder
**18 individual CSV files, one per fruit**

Each file contains the exporter × format pricing matrix for that specific fruit.

**Files:**
- `mango_exporter_format_pricing.csv` (88 combinations)
- `avocado_exporter_format_pricing.csv` (111 combinations)
- `blueberry_exporter_format_pricing.csv` (36 combinations)
- ... and 15 more

**Use these files when:**
- Deep-diving into a single fruit
- Comparing all exporters for one fruit type
- Building fruit-specific pricing strategies

---

## 📊 Data Statistics

### Coverage
- **Total Export Records:** 5,433
- **Clean Records (outliers removed):** 5,375 (98.9%)
- **Outliers Removed:** 58 (1.1%)
- **Fruit Types:** 18
- **Exporters:** 84
- **Format Types:** 13
- **Unique Exporter×Format×Fruit Combinations:** 360

### Top Fruits by Export Volume
1. **Avocado**: 38,641 MT (2,585 records)
2. **Mango**: 32,148 MT (1,620 records)
3. **Blueberry**: 16,754 MT (774 records)

### Format Types Available
- unknown (unspecified format)
- chunks
- pulp
- cubes
- IQF (Individually Quick Frozen)
- slices
- halves
- puree
- whole
- broken_pieces
- juice
- concentrate
- strips

---

## 🎯 How to Use This Data

### Scenario 1: Finding the best price for mango chunks
**Use:** `mango_exporter_format_pricing.csv` or filter `europe_detailed_pricing_by_exporter_format.csv`

Look for:
- Sort by "Median Price USD/MT" (ascending)
- Check "Shipments" to ensure reliability (higher = more consistent)
- Review "Total Volume MT" for capacity

### Scenario 2: Comparing multiple fruits from one exporter
**Use:** `europe_pricing_pivot_exporter_format.csv`

Find the exporter row and scan across fruit columns to see their pricing.

### Scenario 3: Understanding market rates for a format
**Use:** `europe_pricing_by_format.csv`

Filter by fruit and format to see:
- Median market price
- Min-Max range
- Number of suppliers

### Scenario 4: Evaluating an exporter's competitiveness
**Use:** `europe_pricing_by_exporter.csv`

Compare:
- Their median prices vs. market median (from format file)
- Volume shipped (reliability indicator)
- Format diversity (flexibility)

### Scenario 5: Setting price ranges for negotiations
**Use:** `europe_detailed_pricing_by_exporter_format.csv`

For each fruit + format combination:
- **Floor price**: Use Q1 (25th percentile) from clean data
- **Target price**: Use Median
- **Ceiling price**: Use Q3 (75th percentile)

---

## 🔍 Data Quality Notes

### Outlier Detection
- **Method**: Dual-method conservative approach
  - IQR: 1.5× interquartile range
  - Z-score: 3 standard deviations
  - Combined: Flagged only if BOTH methods agree
- **Detection Level**: By fruit + format combination
- **Result**: Only extreme outliers removed (1.1%)

### "Unknown" Format
- Large portion of exports lack specific format classification
- Often represents mixed or proprietary formats
- Prices typically similar to most common format for that fruit

### Price Variability
Some combinations show wide ranges due to:
- Quality tiers (premium vs. standard)
- Organic vs. conventional
- Processing method differences (IQF, aseptic, etc.)
- Seasonal variations
- Small sample sizes

### Recommended Price Metric
**Always use MEDIAN prices** instead of average (mean) because:
- More robust to remaining outliers
- Better represents typical market price
- Less affected by extreme values

---

## 📈 Quick Reference: Median Prices by Fruit

| Fruit | Median Price Range (USD/MT) | Most Common Formats |
|-------|---------------------------|-------------------|
| Camu Camu | $49,945 | Unknown, Pulp |
| Cherimoya | $5,847 | Pulp |
| Pomegranate | $3,800 | Cubes |
| Avocado | $2,860 | Unknown, Pulp, Cubes, Chunks |
| Blueberry | $2,230 | Unknown, Chunks, IQF |
| Passion Fruit | $2,500 | Pulp, Unknown |
| Lucuma | $2,500 | Unknown, Pulp |
| Pitaya | $1,957 | Unknown |
| Golden Berry | $1,808 | Unknown, IQF |
| Mango | $1,749 | Unknown, Chunks, Puree |
| Grape | $1,464 | Unknown |
| Soursop | $1,613 | Pulp, Unknown |
| Banana | $1,050 | Slices, Unknown |
| Strawberry | $1,050 | Unknown, Pulp |
| Pineapple | $893 | Chunks, Unknown |
| Acai | $354 | Pulp, Unknown |

---

## 🛠️ Tools Provided

### Query Tool: `query_europe_data.py`
Interactive command-line tool to query the database.

```bash
# View all fruits summary
python3 query_europe_data.py

# View specific fruit details
python3 query_europe_data.py mango
python3 query_europe_data.py avocado
```

Shows:
- Overall statistics
- Top 10 exporters
- Breakdown by format
- Top destination countries

---

## 📅 Data Period

**Date Range:** January 2024 - October 2025

**Source:** Veritrade Peru Export Database

**Last Updated:** November 13, 2025

---

## 💡 Tips for Analysis

1. **Always cross-reference** median prices with shipment counts
2. **Higher shipment counts** = more reliable price data
3. **Check destination countries** - prices may vary by region
4. **Consider certifications** - organic typically commands premium
5. **IQF products** usually priced higher than standard frozen
6. **Volume matters** - larger volumes may indicate better capacity/reliability

---

## ❓ Questions This Data Answers

✅ What is the market rate for mango chunks to Europe?
✅ Which exporter offers the best price for avocado pulp?
✅ How many suppliers offer organic blueberries?
✅ What formats does VIRU S.A. export?
✅ What's the price difference between chunks and cubes?
✅ Which countries receive the most frozen fruit exports?
✅ What's a reasonable price range for passion fruit pulp?
✅ How diverse is each exporter's product portfolio?

---

**For questions or issues with the data, please review the source files or contact the data analyst.**
