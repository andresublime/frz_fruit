# Peru Frozen Fruit Export Data - Enriched Dataset

## Overview

This project converts and enriches Peru frozen fruit export data from a 2.21 MB Excel file into a structured, LLM-friendly format with comprehensive Pydantic validation.

## Files

### Input
- `Veritrade_JUAN.CABREJOS@REPCOANDINO.COM_PE_E_20251106063034.xlsx` (2.21 MB) - Original export data

### Output
- `peru_frozen_fruit_exports_enriched.csv.gz` (1.0 MB) - Enriched dataset with structured product fields
- `export_summary.json` (69 KB) - Summary statistics in JSON format
- `peru_frozen_fruit_exports.csv.gz` (914 KB) - Original data converted to CSV (no enrichment)

### Code
- `models.py` - Pydantic models for data validation and structure
- `parser.py` - Parser to extract structured information from commercial descriptions
- `enrich_data.py` - Script to enrich the dataset

## Data Structure

### Original Fields (33 columns)
All original export data fields are retained, including:
- HTS Code, Customs, Date, Exporter, Importer
- Weight (Gross kg, Net kg)
- Pricing (U$ FOB Tot, U$ FOB Unit 1, U$ FOB Unit 2)
- Destination (Country, Port)
- Logistics (Shipping Line, Agents)
- Commercial Description

### New Enriched Fields (10 columns)
Extracted from commercial descriptions using Pydantic validation:

1. **fruit_name** - Type of fruit (mango, avocado, pineapple, etc.)
2. **variety** - Fruit variety (Kent, Edward, Haden, etc.)
3. **format_type** - Product format (chunks, slices, puree, pulp, iqf, etc.)
4. **size_mm** - Size specification (e.g., "20x20", "25x25", "10x10")
5. **is_organic** - Boolean flag for organic certification
6. **is_conventional** - Boolean flag for conventional (non-organic)
7. **is_iqf** - Boolean flag for Individually Quick Frozen
8. **certification** - Certification type (organic/conventional/unknown)
9. **net_weight_mt** - Net weight in metric tons (calculated from Net kg)
10. **usd_per_mt_fob** - Price in USD per metric ton FOB (calculated)

## Key Metrics Summary

### Dataset Statistics
- **Total Records**: 14,279 export records
- **Date Range**: January 2024 - October 2025
- **Total Volume**: 218,281.75 MT
- **Total FOB Value**: $507,801,244.27 USD
- **Average Price**: $2,326.36 USD/MT
- **Unique Exporters**: 152
- **Unique Destinations**: 57 countries

### Top Fruits by Volume
1. **Mango**: 113,896.25 MT (52%)
2. **Avocado**: 49,844.90 MT (23%)
3. **Passion Fruit**: 2,854.50 MT (1%)
4. **Pineapple**: 2,329.75 MT (1%)
5. **Strawberry**: 866.46 MT (<1%)

### Top Product Configurations (Fruit → Format → Size)

| Rank | Fruit | Format | Size | Cert | MT | USD/MT | Records |
|------|-------|--------|------|------|-----|--------|---------|
| 1 | Mango | Chunks | 20x20 | Unknown | 6,296.74 | $2,019.92 | 323 |
| 2 | Mango | Chunks | 25x25 | Unknown | 1,999.43 | $1,889.03 | 100 |
| 3 | Avocado | Chunks | 15x15 | Unknown | 1,788.27 | $2,976.83 | 131 |
| 4 | Mango | Chunks | 1x10 | Unknown | 1,549.42 | $1,825.59 | 68 |
| 5 | Mango | Chunks | 1x30 | Unknown | 1,541.43 | $1,857.38 | 73 |

### Top Destinations
1. **United States**: 60,925.66 MT
2. **Belgium**: 21,220.82 MT
3. **Netherlands**: 20,693.62 MT
4. **Chile**: 15,815.85 MT
5. **Canada**: 15,451.12 MT

## Usage

### Installation

```bash
uv init
uv add pandas openpyxl pyarrow pydantic
```

### Enrich Data

```bash
uv run python enrich_data.py
```

### Use Pydantic Models

```python
from models import ExportRecord, FruitProduct, ProductSummary
from parser import parse_description
import pandas as pd

# Load enriched data
df = pd.read_csv('peru_frozen_fruit_exports_enriched.csv.gz')

# Parse a commercial description
product = parse_description("MANGO ORGANICO CHUNKS 20X20MM CONGELADO IQF")
print(f"Fruit: {product.fruit_name}")
print(f"Format: {product.product_format.format_type}")
print(f"Size: {product.product_format.size_mm}")
print(f"Organic: {product.classification.is_organic}")
print(f"IQF: {product.classification.is_iqf}")
```

### Query Examples

```python
import pandas as pd

df = pd.read_csv('peru_frozen_fruit_exports_enriched.csv.gz')

# Get organic mango exports
organic_mango = df[(df['fruit_name'] == 'mango') & (df['is_organic'] == True)]

# Get exports by format and size
chunks_20x20 = df[(df['format_type'] == 'chunks') & (df['size_mm'] == '20x20')]

# Calculate average price by fruit and certification
avg_prices = df.groupby(['fruit_name', 'certification'])['usd_per_mt_fob'].mean()

# Top exporters by volume
top_exporters = df.groupby('Exporter')['net_weight_mt'].sum().nlargest(10)
```

## Data Hierarchy

The data follows this hierarchical structure for analysis:

```
Fruit
├── Format (chunks, slices, puree, etc.)
│   ├── Size (20x20mm, 25x25mm, etc.)
│   │   ├── Certification (organic, conventional, unknown)
│   │   │   ├── Total MT
│   │   │   ├── Average USD/MT FOB
│   │   │   └── Record Count
```

## Benefits for LLM Analysis

1. **Size Reduction**: 2.21 MB → 1.0 MB (55% reduction)
2. **Structured Format**: CSV instead of Excel (easier parsing)
3. **Clean Fields**: Extracted structured data from unstructured descriptions
4. **Computed Metrics**: Pre-calculated USD/MT and MT values
5. **Type Safety**: Pydantic validation ensures data consistency
6. **Hierarchical**: Easy to query by Fruit → Format → Size
7. **Summary Available**: 69 KB JSON summary for quick insights
