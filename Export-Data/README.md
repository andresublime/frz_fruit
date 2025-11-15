# Peru Frozen Fruit Export Analysis - Coherent System

## Overview

This project provides comprehensive analysis of Peru frozen fruit export data with a **unified, coherent architecture** that eliminates duplication and provides clean, reliable pricing analytics.

### Key Improvements (Coherence Branch)

✓ **Exporter Normalization** - Viru consolidated (2,640 shipments from 2 variations)
✓ **Data Quality Filters** - Air freight, samples, outliers, small shipments removed (75.4% valid data)
✓ **Quartile Pricing** - Q1/Median/Q3 instead of absolute min/max (avoids outliers)
✓ **Unified Analytics** - Single pricing engine with drill-down capabilities
✓ **Command-Line Interface** - Easy access to all analytics
✓ **Database-Driven** - Single source of truth (no redundant CSVs)

---

## Quick Start

### Generate Pricing Summaries

```bash
# Fruit-level pricing (worldwide, YTD Oct 2024 - Oct 2025)
python cli/main.py summary fruit

# Exporter-level pricing (shows fruit count + quartiles)
python cli/main.py summary exporter --limit 10

# Format-level pricing
python cli/main.py summary format
```

### Drill Down Analysis

```bash
# Mango pricing by exporter
python cli/main.py drill mango --by exporter --filter-dimension fruit

# Viru pricing by fruit
python cli/main.py drill Viru --by fruit --filter-dimension exporter

# Chunks format by exporter
python cli/main.py drill chunks --by exporter --filter-dimension format
```

### Export to CSV

```bash
# Export full fruit summary
python cli/main.py export fruit fruit_pricing.csv

# Export exporter summary (Europe only)
python cli/main.py export exporter exporters_europe.csv --region Europe
```

---

## Project Structure

```
Export-Data/
├── core/                           # Core data processing modules
│   ├── models.py                   # Pydantic data validation
│   ├── parser.py                   # NLP description parser (24 fruits, 13 formats)
│   ├── translations.py             # Country name translations
│   ├── exporter_mapping.py         # Company name normalization (57 mappings)
│   ├── filters.py                  # Data quality filters
│   └── database.py                 # Database utilities & connections
│
├── analysis/                       # Analytics modules
│   └── pricing.py                  # Quartile pricing engine (Q1/Median/Q3)
│
├── cli/                            # Command-line interface
│   └── main.py                     # Unified CLI for all analytics
│
├── data/
│   └── exports.db                  # SQLite database (18MB, 14,279 records)
│       ├── exports table           # Main table with canonical_exporter
│       ├── v_clean_exports view    # Filtered YTD data (8,361 records)
│       └── indexes                 # Performance optimizations
│
└── *.csv.gz                        # Source data (compressed)
```

---

## Data Quality & Filters

### Filters Applied (v_clean_exports view)

The system automatically filters out unreliable data:

1. **Air Freight** - Excluded (sea freight only for accurate pricing)
2. **Samples** - Excluded (MUESTRA, SIN VALOR, < 10kg shipments)
3. **Small Shipments** - Excluded (< 0.1 MT / 100 kg)
4. **Price Outliers** - IQR method per fruit (Q1 - 1.5×IQR to Q3 + 1.5×IQR)
5. **Date Range** - YTD period only (Oct 2024 - Oct 2025)

**Result:** 75.4% of records are valid (8,361 out of 11,098 YTD records)

### Exporter Name Normalization

**Problem Solved:**
- VIRÚ GROUP PERÚ S.A. (1,391) + VIRU S.A. (1,249) → **Viru (2,640)**
- MEBOL GF S.A.C. (354) + MEBOL SAC (344) → **Mebol (698)**

**Approach:**
- Canonical name mappings for top 50 exporters
- Accent-insensitive matching (VIRÚ → VIRU)
- Legal suffix stripping (S.A., S.A.C., SAC, etc.)

---

## Pricing Analytics

### Output Format

All pricing outputs use **quartile-based pricing** (not absolute min/max):

- **Low$** = Q1 (25th percentile) - realistic lower bound
- **Mid$** = Median (50th percentile) - typical price
- **Hi$** = Q3 (75th percentile) - realistic upper bound
- **YTD MT** = Total volume in metric tons (Oct 2024 - Oct 2025)

### Available Dimensions

1. **Fruit** - Aggregate by fruit type (mango, avocado, etc.)
2. **Exporter** - Aggregate by company (includes fruit count)
3. **Format** - Aggregate by product format (chunks, puree, etc.)

### Drill-Down Capabilities

- **Fruit → Exporter** - Which companies export this fruit?
- **Fruit → Format** - Which formats are used for this fruit?
- **Exporter → Fruit** - What fruits does this company export?
- **Exporter → Format** - What formats does this company use?
- **Format → Exporter** - Which companies use this format?

---

## Dataset Statistics

### Overall (Full Database)
- **Total Records**: 14,279 export records
- **Date Range**: January 2024 - October 2025
- **Total Volume**: 218,282 MT
- **Total FOB Value**: $507.8 million USD
- **Unique Exporters**: 152 (48 canonical after normalization)
- **Unique Destinations**: 57 countries
- **Fruit Types**: 20

### YTD Clean Data (v_clean_exports view)
- **Valid Records**: 8,361 (75.4% of YTD data)
- **YTD Volume**: ~153,000 MT
- **Top 3 Fruits**: Mango (87,919 MT), Avocado (36,594 MT), Blueberry (19,903 MT)
- **Top 3 Exporters**: Viru (25,459 MT), Sunshine Export (13,981 MT), Camposol (12,848 MT)

---

## Data Hierarchy

The data follows this hierarchical structure for analysis:

```
Fruit (20 types)
├── Format (13 types: chunks, slices, puree, pulp, etc.)
│   ├── Size (20x20mm, 25x25mm, etc.)
│   │   ├── Exporter (152 companies → 48 canonical)
│   │   │   ├── Destination (57 countries)
│   │   │   │   ├── Certification (organic, conventional, unknown)
│   │   │   │   │   ├── Pricing (Q1, Median, Q3 USD/MT FOB)
│   │   │   │   │   └── Volume (YTD MT)
```

---

## Python API Usage

### Pricing Analytics

```python
from analysis.pricing import (
    calculate_pricing_summary,
    calculate_pricing_drill_down,
    export_to_csv,
)

# Generate fruit-level summary
df_fruit = calculate_pricing_summary(dimension='fruit')
print(df_fruit.head())
# Output: Fruit | Low$ | Mid$ | Hi$ | YTD MT | Records

# Generate exporter-level summary (includes fruit count)
df_exporter = calculate_pricing_summary(dimension='exporter')
print(df_exporter.head())
# Output: Exporter | Fruits | Low$ | Mid$ | Hi$ | YTD MT | Records

# Drill down: Mango by exporter
df_mango = calculate_pricing_drill_down('fruit', 'mango', by='exporter')
print(df_mango.head())

# Drill down: Viru by fruit
df_viru = calculate_pricing_drill_down('exporter', 'Viru', by='fruit')
print(df_viru)

# Export to CSV
export_to_csv(df_fruit, 'fruit_pricing.csv')
```

### Database Access

```python
from core.database import (
    load_clean_exports,
    get_fruit_types,
    get_exporters,
    get_table_stats,
)

# Load clean YTD data (filtered, Oct 2024 - Oct 2025)
df = load_clean_exports(ytd_only=True)

# Get statistics
stats = get_table_stats()
print(f"Total records: {stats['total_records']:,}")
print(f"Date range: {stats['date_range']}")

# Get unique values
fruits = get_fruit_types()
exporters = get_exporters()  # Returns canonical names
```

### Exporter Normalization

```python
from core.exporter_mapping import get_canonical_name

# Normalize exporter names
print(get_canonical_name('VIRÚ GROUP PERÚ S.A.'))  # → 'Viru'
print(get_canonical_name('VIRU S.A.'))  # → 'Viru'
print(get_canonical_name('MEBOL GF S.A.C.'))  # → 'Mebol'
```

### Data Quality Filters

```python
from core.filters import filter_valid_shipments, get_filter_stats

import pandas as pd

# Load raw data
df = pd.read_csv('peru_frozen_fruit_exports_enriched.csv.gz')

# Get filter statistics
stats = get_filter_stats(df)
print(f"Air shipments: {stats['air_shipments']}")
print(f"Samples: {stats['samples']}")

# Apply all filters
clean_df = filter_valid_shipments(df, apply_iqr_outliers=True)
```

---

## Original Data Structure

### Original Fields (33 columns)
All original export data fields are retained, including:
- HTS Code, Customs, Date, Exporter, Importer
- Weight (Gross kg, Net kg)
- Pricing (U$ FOB Tot, U$ FOB Unit 1, U$ FOB Unit 2)
- Destination (Country, Port)
- Logistics (Shipping Line, Agents)
- Commercial Description

### Enriched Fields (13 columns)
Extracted from commercial descriptions using Pydantic validation + NLP:

1. **fruit_name** - Type of fruit (mango, avocado, pineapple, etc.)
2. **variety** - Fruit variety (Kent, Edward, Haden, etc.)
3. **format_type** - Product format (chunks, slices, puree, pulp, iqf, etc.)
4. **size_mm** - Size specification (e.g., "20x20", "25x25", "10x10")
5. **is_organic** - Boolean flag for organic certification
6. **is_conventional** - Boolean flag for conventional (non-organic)
7. **is_iqf** - Boolean flag for Individually Quick Frozen
8. **is_aseptic** - Boolean flag for aseptic processing
9. **certification** - Certification type (organic/conventional/unknown)
10. **net_weight_mt** - Net weight in metric tons (calculated from Net kg)
11. **usd_per_mt_fob** - Price in USD per metric ton FOB (calculated)
12. **destination_country_en** - English country name
13. **region** - Region (Europe / Rest of World)

### Database-Added Fields (2 columns)
14. **canonical_exporter** - Normalized exporter name (fixes VIRU, Mebol variations)
15. **analysis_valid** - Boolean flag for data quality (1 = passed all filters)

---

## Benefits

1. **Accurate Pricing** - Quartile-based pricing eliminates outlier distortion
2. **Clean Data** - Automated quality filters ensure reliability
3. **Consistent Names** - Exporter normalization fixes duplicate companies
4. **Easy to Use** - Simple CLI interface, no code required
5. **Flexible** - Python API for custom analysis
6. **Fast** - Database queries with caching (10-1000x faster than CSV)
7. **Maintainable** - Modular architecture, single source of truth
8. **Complete** - All dimensions covered (fruit, exporter, format, region)

---

## Development

### Update Database Schema

```bash
# Add canonical_exporter and analysis_valid columns
python update_database_schema.py
```

### Create Database Views

```bash
# Create v_clean_exports view
python create_views.py
```

### Run Tests

```bash
# Test pricing analytics
python analysis/pricing.py

# Test exporter mapping
python core/exporter_mapping.py

# Test data filters
python core/filters.py

# Test database utilities
python core/database.py
```

---

## Future Enhancements

- [ ] MCP Server V2 integration with new pricing tools
- [ ] Automated monthly reports
- [ ] Web dashboard for interactive exploration
- [ ] Price prediction models
- [ ] Market gap analysis automation
- [ ] Export opportunity scoring

---

## License

Proprietary - Peru Frozen Fruit Export Analysis System
