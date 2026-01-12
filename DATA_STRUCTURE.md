# DATA_STRUCTURE.md
# Peru Frozen Fruit Export Analysis - Data Lineage Documentation

**Purpose**: Complete data architecture reference for AI architectural review
**Generated**: 2026-01-06
**Data Pipeline**: Raw CSV → Enriched CSV → SQLite → Analytics

---

## OVERVIEW

### Quick Reference

**Data Flow**: `Veritrade Export Data (CSV)` → `NLP Parser` → `SQLite Database` → `Quartile Analytics` → `Visualizations`

**Key Metrics**:
- **Records**: 14,279 export shipments (Jan 2024 - Oct 2025)
- **Schema Evolution**: 33 original columns → 46 enriched → 49 database columns
- **Data Quality**: 75.4% retention after quality filtering
- **Company Normalization**: 152 → 146 exporters (3.9% reduction), 1,423 → 579 importers (59.3% reduction)
- **Fruits Tracked**: 20+ types (mango, avocado, blueberry, pineapple, etc.)
- **Destinations**: 57 countries (Europe vs Rest of World classification)

**Critical Transformations**: 6 major stages
1. NLP Text Extraction (commercial descriptions → structured fields)
2. Country Translation (Spanish → English)
3. Company Name Clustering (vt-normalize fuzzy matching)
4. Database Loading (CSV → SQLite with indexes)
5. Quality Filtering (air freight, samples, outliers → 75.4% retention)
6. Analytics Aggregation (quartile pricing by dimension)

---

## 1. DATA FILE MAP

### Tree Structure of Data-Related Files

```
📦 Export-Data/
│
├── 📁 data/ (Raw & Processed Data)
│   ├── peru_frozen_fruit_exports.csv.gz               [915 KB, 14,279 records, 33 columns]
│   ├── peru_frozen_fruit_exports_enriched.csv.gz      [1.1 MB, 14,279 records, 46 columns]
│   ├── exports.db                                     [21 MB, SQLite, 49 columns]
│   ├── clustered_exporters.json                       [Canonical exporter mappings: 152→146]
│   └── clustered_importers.json                       [Canonical importer mappings: 1,423→579]
│
├── 📁 core/ (Data Infrastructure)
│   ├── database.py                                    [SQLite connection & query functions]
│   ├── filters.py                                     [Data quality filtering logic]
│   ├── exporter_mapping.py                            [Exporter name normalization]
│   ├── importer_mapping.py                            [Importer name normalization]
│   └── mappings.py                                    [Region & country mappings]
│
├── 📁 analysis/ (Analytics)
│   └── pricing.py                                     [Quartile pricing engine]
│
├── 📁 vt_normalize/ (Name Clustering Library)
│   ├── clustering.py                                  [Fuzzy matching & grouping]
│   ├── text_utils.py                                  [Text cleaning & normalization]
│   ├── config.py                                      [Stop words & legal suffixes]
│   └── models.py                                      [Company name data structures]
│
├── 📄 models.py                                       [Pydantic schemas for validation]
├── 📄 parser.py                                       [NLP commercial description parser]
├── 📄 translations.py                                 [Spanish→English country mapping]
├── 📄 enrich_data.py                                  [Main enrichment pipeline script]
├── 📄 create_database.py                              [Database creation & transformation]
├── 📄 cluster_company_names.py                        [Company name clustering script]
├── 📄 sankey.py                                       [Sankey diagram data generator]
│
├── 📁 cli/ (Command-Line Interface)
│   └── main.py                                        [CLI for pricing queries]
│
└── 📁 mcp_tools/ (Model Context Protocol Server)
    ├── server.py                                      [19 MCP tools for AI queries]
    └── cache.py                                       [Response caching layer]
```

**External Data Source**:
- **Provider**: Veritrade (commercial customs data platform)
- **Source File**: `Veritrade_JUAN_CABREJOS_REPCOANDINO_COM_PE_E_20251106063034.xlsx`
- **Downloaded**: 2025-11-06
- **Update Method**: Manual download from Veritrade portal
- **Format**: Peru customs export declarations (standard format)

---

## 2. CORE SCHEMA DEFINITIONS

### 2.1 Pydantic Models (`models.py`)

#### ExportRecord (lines 78-151)
Main data container with 33 original + 13 enriched fields

**Original Fields (33)**:
```python
# Customs & Identity
hts_code: str                    # Harmonized Tariff System code
hts_code_description: str
customs: str
dua_dam: str                     # Customs documentation
date: datetime
tax_id: int
exporter: str
importer: Optional[str]

# Weight & Quantity
gross_kg: Optional[float]
net_kg: Optional[float]
qty_1: Optional[float]
unit_1: Optional[str]
qty_2: Optional[float]
unit_2: Optional[str]

# Pricing (USD FOB)
usd_fob_total: Optional[float]
usd_fob_unit_1: Optional[float]
usd_fob_unit_2: Optional[float]

# Logistics
destination_country: Optional[str]
destination_port: Optional[str]
last_port: Optional[str]
via: Optional[str]
port_agent: Optional[str]
customs_agent: Optional[str]
shipping_line: Optional[str]
forwarding_agent_origin: Optional[str]
forwarding_agent_destination: Optional[str]
channel: Optional[str]

# Descriptions
commercial_description: str
description1-5: Optional[str]    # Additional description fields
```

**Enriched Fields (13)** - Added by NLP parser:
```python
# Structured product info
product: Optional[FruitProduct]  # Nested structured data

# Computed metrics (lines 128-129, calculated in model_post_init lines 143-150)
net_weight_mt: Optional[float]   # Net weight in metric tons (Net kg / 1000)
usd_per_mt_fob: Optional[float]  # USD per metric ton (U$ FOB Tot / net_weight_mt)
```

#### FruitProduct (lines 59-75)
Structured product information extracted from commercial descriptions

```python
fruit_name: Literal[              # 24 fruit types
    "mango", "pineapple", "strawberry", "blueberry", "papaya", "avocado",
    "pomegranate", "lucuma", "passion_fruit", "golden_berry", "camu_camu",
    "soursop", "cherimoya", "pitaya", "acai", "banana", "raspberry",
    "cherry", "peach", "grape", "orange", "mix", "other", "unknown"
]
variety: Optional[str]            # e.g., Kent, Edward, Haden
product_format: ProductFormat     # Nested format details
classification: ProductClassification  # Nested certification data
```

#### ProductFormat (lines 11-30)
Product format and size information

```python
format_type: Optional[Literal[
    "chunks", "cubes", "slices", "halves", "puree", "pulp", "whole",
    "strips", "iqf", "broken_pieces", "concentrate", "juice", "unknown"
]]
size_mm: Optional[str]            # Standardized size (e.g., "20x20", "10x10")

# Validator (lines 21-30): Standardizes size format
@field_validator('size_mm')
def standardize_size(cls, v):
    # "20X20MM" → "20x20"
    # "10 x 10" → "10x10"
```

#### ProductClassification (lines 33-56)
Certification and processing flags

```python
is_organic: bool = False
is_conventional: bool = False
is_iqf: bool = False              # Individually Quick Frozen
is_aseptic: bool = False          # Aseptic processing (not frozen)
certification: Literal["organic", "conventional", "unknown"] = "unknown"

# Validator (lines 48-56): Auto-determines certification from flags
@field_validator('certification')
def determine_certification(cls, v, info):
    if info.data.get('is_organic'):
        return "organic"
    elif info.data.get('is_conventional'):
        return "conventional"
    return v or "unknown"
```

#### ProductSummary (lines 153-178)
Aggregated metrics by Fruit → Format → Size

```python
fruit_name: str
format_type: str
size_mm: Optional[str]
certification: str
total_mt: float                   # Total metric tons exported
avg_usd_per_mt: float             # Average USD per metric ton FOB
record_count: int                 # Number of export records
total_fob_usd: float              # Total FOB value in USD
```

### 2.2 Database Schema (`exports.db`)

#### Main Table: `exports` (49 columns)

**Column Categories**:
```sql
-- Original Fields (33): From Veritrade CSV
HTS Code, HTS Code Description, Customs, DUA / DAM, Date, Tax ID,
Exporter, Importer, Gross kg, Net kg, Qty 1, Unit 1, Qty 2, Unit 2,
U$ FOB Tot, U$ FOB Unit 1, U$ FOB Unit 2, Destination Country,
Destination Port, Last Port, Via, Port Agent, Customs Agent,
Shipping Line, Forwarding Agent(Origin), Forwarding Agent(Destination),
Channel, Commercial Description, Description1-5

-- Enriched Product Fields (8): From NLP parser
fruit_name TEXT, variety TEXT, format_type TEXT, size_mm TEXT,
is_organic INTEGER, is_conventional INTEGER, is_iqf INTEGER,
certification TEXT

-- Computed Metrics (2): Calculated in models.py
net_weight_mt REAL,              -- Net weight in metric tons
usd_per_mt_fob REAL              -- Price per metric ton

-- Translated (2): From create_database.py
destination_country_en TEXT,     -- English country name
region TEXT                      -- 'Europe' or 'Rest of World'

-- Canonical Names (2): From vt-normalize
canonical_exporter TEXT,         -- Standardized exporter name
canonical_importer TEXT          -- Standardized importer name

-- Quality Flag (1): From filters.py
analysis_valid INTEGER           -- 1 = passes all quality checks, 0 = invalid

-- Aseptic Flag (1): From parser
is_aseptic INTEGER               -- Aseptic processing flag
```

#### Database Indexes (lines 87-102 in create_database.py)
```sql
idx_exporter                ON exports(Exporter)
idx_canonical_exporter      ON exports(canonical_exporter)
idx_canonical_importer      ON exports(canonical_importer)
idx_destination             ON exports([Destination Country])
idx_fruit                   ON exports(fruit_name)
idx_format                  ON exports(format_type)
idx_size                    ON exports(size_mm)
idx_certification           ON exports(certification)
idx_date                    ON exports(Date)
idx_region                  ON exports(region)
```

#### Database Views (lines 122-205 in create_database.py)

**1. v_clean_exports** (defined in core/database.py)
```sql
-- Filtered, analysis-ready data (YTD period, quality-checked)
SELECT * FROM exports
WHERE analysis_valid = 1
  AND Date >= '2024-10-01' AND Date <= '2025-10-31'
```

**2. exporter_products** (lines 126-145)
```sql
-- Aggregated by exporter × fruit × format × region
SELECT Exporter, fruit_name, format_type, size_mm, certification, region,
       COUNT(*) as shipment_count,
       SUM(net_weight_mt) as total_mt,
       AVG(usd_per_mt_fob) as avg_usd_per_mt,
       MIN/MAX(usd_per_mt_fob) as min/max_usd_per_mt,
       SUM([U$ FOB Tot]) as total_fob_usd
FROM exports
WHERE net_weight_mt > 0 AND usd_per_mt_fob > 0
GROUP BY ...
```

**3. destination_products** (lines 148-167)
```sql
-- Aggregated by country × fruit × format
```

**4. monthly_exports** (lines 170-185)
```sql
-- Time series by fruit for seasonality analysis
SELECT fruit_name, year, month, month_num,
       COUNT(*), SUM(net_weight_mt), AVG(usd_per_mt_fob)
GROUP BY fruit_name, year, month
```

**5. regional_exports** (lines 188-205)
```sql
-- Regional aggregations (Europe vs Rest of World)
SELECT region, [Destination Country], fruit_name, ...
GROUP BY region, [Destination Country], fruit_name, ...
```

#### Secondary Table: `region_mapping` (lines 104-120)
```sql
CREATE TABLE region_mapping (
    country TEXT PRIMARY KEY,      -- English country name
    region TEXT NOT NULL           -- 'Europe' or 'Rest of World'
)

-- 31 European countries mapped
```

---

## 3. DATA LIFE CYCLE

### Complete 6-Stage Transformation Pipeline

#### Stage 1: NLP Enrichment
**File**: `enrich_data.py` (lines 137-204)
**Function**: `enrich_dataset()`

```
Input:  peru_frozen_fruit_exports.csv.gz (33 columns)
        ↓
Process: DescriptionParser.parse(row['Commercial Description'])
        • Extract fruit_name (23 regex patterns)
        • Extract variety (Kent, Edward, Haden, etc.)
        • Extract format_type (chunks, cubes, slices, etc.)
        • Extract size_mm (20x20, 10x10, etc.)
        • Extract certification (organic, conventional, IQF)
        • Calculate net_weight_mt = Net kg / 1000
        • Calculate usd_per_mt_fob = U$ FOB Tot / net_weight_mt
        ↓
Output: peru_frozen_fruit_exports_enriched.csv.gz (46 columns)
        33 original + 13 new fields

Results:
        • Fruit identification: 99.7% success rate
        • Format identification: 90%+ success rate
        • Certification detection: 30%+ identified
```

**Key Code** (parser.py lines 74-122):
```python
def parse(cls, description: str) -> FruitProduct:
    desc_lower = description.lower()

    # Extract fruit (24 types via regex)
    fruit_name = cls._extract_fruit(desc_lower)

    # Extract variety (Kent, Edward, MD2, etc.)
    variety = cls._extract_variety(desc_lower)

    # Extract format (chunks, cubes, puree, etc.)
    product_format = cls._extract_format(desc_lower)

    # Extract classification (organic, IQF, etc.)
    classification = cls._extract_classification(desc_lower)

    return FruitProduct(...)
```

---

#### Stage 2: Translation & Region Classification
**File**: `create_database.py` (lines 44-53)
**Function**: `create_database()`

```
Input:  Enriched CSV (46 columns)
        ↓
Process: translate_country_to_english()
        • Spanish → English: "ALEMANIA" → "Germany"
        • 80+ country translations

        Region classification:
        • IF country IN EUROPE_COUNTRIES_EN → 'Europe'
        • ELSE → 'Rest of World'
        ↓
Output: +2 columns (destination_country_en, region)
```

**Key Code** (translations.py lines 97-107):
```python
def translate_country_to_english(spanish_name: str) -> str:
    return COUNTRY_TRANSLATIONS.get(spanish_name.upper(), spanish_name)

# COUNTRY_TRANSLATIONS = {
#     'ALEMANIA': 'Germany',
#     'PAÍSES BAJOS': 'Netherlands',
#     'REINO UNIDO': 'United Kingdom',
#     ... (80+ entries)
# }
```

**Europe Countries** (create_database.py lines 18-24):
```python
EUROPE_COUNTRIES_EN = {
    'Germany', 'Austria', 'Belgium', 'France', 'Netherlands',
    'Spain', 'Italy', 'United Kingdom', 'Poland', 'Switzerland',
    ... (31 countries total)
}
```

---

#### Stage 3: Canonical Name Normalization
**File**: `create_database.py` (lines 59-80)
**Functions**: `get_canonical_name()`, `get_canonical_importer()`

```
Input:  Raw company names
        Exporters: 152 unique names
        Importers: 1,423 unique names
        ↓
Process: vt-normalize clustering
        1. Fix encoding (NATURE?S → NATURE'S)
        2. Remove accents (VIRÚ → VIRU)
        3. Strip legal suffixes (S.A., S.A.C., LLC, etc.)
        4. Remove stop words (SOCIEDAD, AGRICOLA, GRUPO)
        5. Remove addresses (PO Box, street names)
        6. Fuzzy clustering (80-95% similarity thresholds)
        ↓
Output: +2 columns (canonical_exporter, canonical_importer)

Results:
        • Exporters: 152 → 146 canonical (3.9% reduction, 6 duplicates merged)
        • Importers: 1,423 → 579 canonical (59.3% reduction, 844 duplicates merged)

Examples:
        • "VIRÚ GROUP PERÚ S.A." + "VIRU S.A." → "VIRU"
        • "MEBOL GF S.A.C." + "MEBOL SAC" → "MEBOL GF"
        • "SUNSHINE EXPORT S.A.C" → "SUNSHINE"
```

**Key Code** (core/exporter_mapping.py lines 62-108):
```python
def get_canonical_name(exporter_name: str) -> str:
    # Load clustered database (lazy-loaded JSON)
    _load_database()

    # Try exact match first
    if exporter_name in _MAPPING_DATABASE:
        return _MAPPING_DATABASE[exporter_name].upper()

    # Try normalized version (vt-normalize cleaning)
    normalized = clean_company_name(exporter_name,
                                   strip_legal=True,
                                   remove_addresses=True)
    for alias, canonical in _MAPPING_DATABASE.items():
        if clean_company_name(alias, ...) == normalized:
            return canonical.upper()

    # No match - return normalized original
    return normalized.upper()
```

**Text Cleaning** (vt_normalize/text_utils.py):
```python
def clean_company_name(name: str,
                      strip_legal: bool = True,
                      remove_addresses: bool = True) -> str:
    # 1. Fix encoding corruption (? → ', UTF-8 mojibake)
    # 2. Remove accents (NFD decomposition)
    # 3. Strip legal suffixes (50+ patterns: S.A., LLC, PVT LTD, GmbH, etc.)
    # 4. Remove stop words (SOCIEDAD, GRUPO, AGRICOLA, etc.)
    # 5. Remove addresses (postal codes, PO boxes, street names)
    # 6. Normalize whitespace and punctuation
    # 7. Merge single-letter prefixes (D ARTA → DARTA)
```

---

#### Stage 4: Database Loading
**File**: `create_database.py` (lines 82-103)
**Function**: `create_database()`

```
Input:  Fully enriched CSV (46 columns + 2 canonical)
        ↓
Process: df.to_sql('exports', conn, if_exists='replace')
        • Load to SQLite
        • Create 10 indexes for query performance
        • Create 5 views for common aggregations
        • Create region_mapping table
        ↓
Output: exports.db (21 MB)
        Main table: exports (49 columns, 14,279 records)
        Views: v_clean_exports, exporter_products, destination_products,
               monthly_exports, regional_exports
```

**Indexes Created**:
```sql
-- Company lookups
idx_exporter, idx_canonical_exporter, idx_canonical_importer

-- Product lookups
idx_fruit, idx_format, idx_size, idx_certification

-- Geographic lookups
idx_destination, idx_region

-- Time series
idx_date
```

---

#### Stage 5: Quality Filtering
**File**: `core/filters.py` (lines 288-365)
**Function**: `filter_valid_shipments()`

```
Input:  All exports records (14,279)
        ↓
Process: 5-stage quality filter cascade

        1. Remove air freight (lines 68-88)
           Via NOT IN ('AÉREO', 'AEREO', 'AIR')

        2. Remove samples (lines 91-124)
           Keywords: MUESTRA, SIN VALOR, SAMPLE, TEST
           OR weight < 10 kg
           OR value < $10

        3. Remove small shipments (lines 127-146)
           net_weight_mt < 0.1 MT (100 kg)

        4. Remove below price floor (lines 181-202)
           Fruit-specific minimums:
           • Mango: $1,500/MT
           • Avocado: $2,000/MT
           • Blueberry: $1,800/MT
           • Pineapple: $800/MT
           • Default: $500/MT

        5. Remove IQR outliers (lines 338-361)
           Per-fruit statistical bounds:
           • price < Q1 - 1.5×IQR  OR  price > Q3 + 1.5×IQR
           • Calculated separately for each fruit type
        ↓
Output: analysis_valid flag (0 or 1)

Results:
        • 14,279 total records
        • 10,762 pass filters (75.4% retention)
        • 3,517 flagged as invalid (24.6%)

        View: v_clean_exports (filters for analysis_valid = 1 AND YTD dates)
```

**Key Code** (core/filters.py lines 288-365):
```python
def filter_valid_shipments(df: pd.DataFrame,
                          apply_iqr_outliers: bool = True,
                          iqr_multiplier: float = 1.5) -> pd.DataFrame:
    initial_count = len(df)

    # 1. Air freight
    df = df[~df.apply(is_air_shipment, axis=1)]

    # 2. Samples
    df = df[~df.apply(is_sample_shipment, axis=1)]

    # 3. Small shipments (< 0.1 MT)
    df = df[~df.apply(is_small_shipment, axis=1)]

    # 4. Price floors
    df = df[~df.apply(is_below_price_floor, axis=1)]

    # 5. IQR outliers (per fruit)
    if apply_iqr_outliers:
        bounds = calculate_iqr_bounds(df, 'usd_per_mt_fob', 'fruit_name')
        df = df.merge(bounds[['fruit_name', 'q1', 'q3']], on='fruit_name')
        df = df[~df.apply(lambda row: is_price_outlier_iqr(row, row['q1'], row['q3']), axis=1)]

    print(f"Final: {len(df)} / {initial_count} records retained ({len(df)/initial_count*100:.1f}%)")
    return df
```

**IQR Outlier Detection** (lines 205-243):
```python
def calculate_iqr_bounds(df: pd.DataFrame,
                        price_col: str = 'usd_per_mt_fob',
                        group_by: str = 'fruit_name') -> pd.DataFrame:
    # Calculate per-fruit quartiles
    q1 = df.groupby(group_by)[price_col].quantile(0.25)
    q3 = df.groupby(group_by)[price_col].quantile(0.75)
    iqr = q3 - q1

    # Standard outlier bounds
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr

    return pd.DataFrame({
        'q1': q1, 'q3': q3, 'iqr': iqr,
        'lower_bound': lower_bound,
        'upper_bound': upper_bound
    })
```

---

#### Stage 6: Analytics Transformation
**File**: `analysis/pricing.py` (lines 33-131)
**Function**: `calculate_pricing_summary()`

```
Input:  v_clean_exports view (10,762 valid records, YTD period)
        ↓
Process: Quartile aggregation by dimension

        Dimensions: 'fruit', 'exporter', 'importer'
        Metrics:
        • Low$ = PERCENTILE_CONT(0.25) of usd_per_mt_fob  (Q1)
        • Mid$ = PERCENTILE_CONT(0.50) of usd_per_mt_fob  (Median)
        • Hi$  = PERCENTILE_CONT(0.75) of usd_per_mt_fob  (Q3)
        • YTD MT = SUM(net_weight_mt)
        • Records = COUNT(*)

        Optional filters:
        • Region: 'Europe', 'RoW', or None (worldwide)
        ↓
Output: Pricing DataFrame with quartile bands per entity

Example Output:
        Fruit         Low$    Mid$    Hi$     YTD MT   Records
        ─────────────────────────────────────────────────────
        mango         2,150   2,650   3,200   8,500    3,245
        avocado       2,800   3,400   4,100   5,200    1,876
        blueberry     3,200   4,200   5,500   3,800    1,456
        ...
```

**Key Code** (analysis/pricing.py lines 33-131):
```python
def calculate_pricing_summary(dimension: DimensionType = 'fruit',
                             region: Optional[str] = None,
                             use_clean_view: bool = True) -> pd.DataFrame:
    # Map dimension to column
    dimension_col_map = {
        'fruit': 'fruit_name',
        'exporter': 'canonical_exporter',
        'importer': 'canonical_importer'
    }

    dimension_col = dimension_col_map[dimension]
    source_table = 'v_clean_exports' if use_clean_view else 'exports'

    # Build query with region filter
    query = f"""
        SELECT {dimension_col} as dimension_value,
               usd_per_mt_fob, net_weight_mt
        FROM {source_table}
        WHERE {dimension_col} IS NOT NULL
          AND usd_per_mt_fob IS NOT NULL
          {region_filter}
    """

    df = execute_query(query)

    # Calculate quartiles using pandas
    result = df.groupby('dimension_value').agg(
        low_price=('usd_per_mt_fob', lambda x: x.quantile(0.25)),  # Q1
        mid_price=('usd_per_mt_fob', lambda x: x.quantile(0.50)),  # Median
        hi_price=('usd_per_mt_fob', lambda x: x.quantile(0.75)),   # Q3
        total_mt=('net_weight_mt', 'sum'),
        records=('usd_per_mt_fob', 'count')
    ).reset_index()

    # Format and round
    result.rename(columns={
        'dimension_value': dimension.title(),
        'low_price': 'Low$',
        'mid_price': 'Mid$',
        'hi_price': 'Hi$',
        'total_mt': 'YTD MT',
        'records': 'Records'
    })

    result['Low$'] = result['Low$'].round(0).astype(int)
    result['Mid$'] = result['Mid$'].round(0).astype(int)
    result['Hi$'] = result['Hi$'].round(0).astype(int)
    result['YTD MT'] = result['YTD MT'].round(0).astype(int)

    return result.sort_values('YTD MT', ascending=False)
```

**Drill-Down Function** (lines 134-245):
```python
def calculate_pricing_drill_down(filter_dimension: str,
                                 filter_value: str,
                                 by: str,
                                 region: Optional[str] = None) -> pd.DataFrame:
    # Examples:
    # - Mango prices by exporter: ('fruit', 'mango', 'exporter')
    # - Viru prices by fruit: ('exporter', 'Viru', 'fruit')
    # - Salud Foodgroup prices by fruit: ('importer', 'Salud Foodgroup Europe', 'fruit')

    # Same quartile calculation, but filtered by specific entity
```

---

## 4. DATA MUTATION POINTS

### Complete Mutation Tracking Table

| Stage | Location | Function | Input → Output | Records Changed | Line Ref |
|-------|----------|----------|----------------|-----------------|----------|
| **1. NLP Parsing** | parser.py:74 | `DescriptionParser.parse()` | Text description → Structured fields (10+ cols) | 100% (14,279) | 74-122 |
| **2. Metric Calculation** | models.py:143 | `ExportRecord.model_post_init()` | Add net_weight_mt, usd_per_mt_fob | 100% (14,279) | 143-150 |
| **3. Country Translation** | create_database.py:46 | `translate_country_to_english()` | Spanish → English (80+ mappings) | 100% (14,279) | 46-48 |
| **4. Region Classification** | create_database.py:51 | Region mapping | Country → 'Europe' or 'RoW' | 100% (14,279) | 51-53 |
| **5. Exporter Normalization** | create_database.py:62 | `get_canonical_name()` | 152 raw names → 146 canonical | 100% (14,279) | 62-64 |
| **6. Importer Normalization** | create_database.py:65 | `get_canonical_importer()` | 1,423 raw → 579 canonical | 100% (14,279) | 65-67 |
| **7. Quality Flagging** | filters.py:288 | `filter_valid_shipments()` | Flag invalid records | 24.6% flagged (3,517) | 288-365 |
| **8. Quartile Aggregation** | pricing.py:92 | `calculate_pricing_summary()` | Records → Quartile stats | N → M groups | 92-98 |
| **9. Visualization Aggregation** | sankey.py:70 | `aggregate_small_players()` | Group bottom 20% as "Others" | Variable | 70-112 |

### Irreversible Transformations
- **Text → Structure** (Stage 1): Original commercial descriptions are preserved, but extracted fields cannot recreate exact original text
- **Quality Filtering** (Stage 7): Records flagged as invalid (analysis_valid=0) are excluded from v_clean_exports view
- **Company Clustering** (Stages 5-6): Original company names preserved, but analysis uses canonical names

---

## 5. KEY TRANSFORMATION LOGIC

### 5.1 Text → Structure (NLP Parser)

**File**: `parser.py`
**Function**: `DescriptionParser.parse()` (lines 74-122)

**Purpose**: Extract structured product data from free-text Spanish/English descriptions

**Input Example**:
```
"MANGO CONGELADO ORGANICO CHUNKS 20X20MM IQF VARIEDAD: EDWARD"
```

**Process**:
```python
# 1. Fruit Detection (lines 125-130)
FRUIT_PATTERNS = {
    'mango': r'\bmango[s]?(?:\b|(?=[A-Z]))',
    'pineapple': r'\b(pineapple|piña|pina|ananas)\b',
    'blueberry': r'\b(blueberry|arandano[s]?|arándano[s]?)\b',
    'avocado': r'\b(avocado[s]?|aguacate[s]?|palta[s]?)\b',
    ... (24 fruit types)
}

fruit_name = 'mango'  # Matched via regex

# 2. Variety Detection (lines 133-140)
VARIETY_PATTERNS = [
    r'(?:variedad|variety|var)[:\s]+([a-z]+)',
    r'\b(kent|edward|haden|keitt|tommy atkins|ataulfo)\b',
    r'\b(golden|md2|cayenne)\b'  # pineapple varieties
]

variety = 'Edward'  # Extracted from "VARIEDAD: EDWARD"

# 3. Format Detection (lines 143-175)
FORMAT_PATTERNS = {
    'chunks': r'\b(chunk[s]?|trozo[s]?|pedazo[s]?|bits and pieces)\b',
    'cubes': r'\b(cube[s]?|cubo[s]?|dado[s]?|diced|picado[s]?)\b',
    'slices': r'\b(slice[s]?|sliced|rebanada[s]?|rodaja[s]?)\b',
    'puree': r'\b(puree|pure|puré)\b',
    ... (11 format types)
}

SIZE_PATTERNS = [
    r'(\d+)\s*[xX×]\s*(\d+)\s*(?:mm)?',  # 20x20mm, 20X20
]

format_type = 'chunks'
size_mm = '20x20'  # Standardized from "20X20MM"

# 4. Classification Detection (lines 178-198)
ORGANIC_PATTERNS = r'\b(organic|organico|org)\b'
IQF_PATTERNS = r'\biqf\b'

is_organic = True    # Matched "ORGANICO"
is_iqf = True        # Matched "IQF"
certification = 'organic'  # Auto-determined from is_organic flag
```

**Output**:
```python
FruitProduct(
    fruit_name='mango',
    variety='Edward',
    product_format=ProductFormat(
        format_type='chunks',
        size_mm='20x20'
    ),
    classification=ProductClassification(
        is_organic=True,
        is_conventional=False,
        is_iqf=True,
        is_aseptic=False,
        certification='organic'
    )
)
```

**Pattern Statistics**:
- **24 fruit patterns** (Spanish + English): mango, pineapple, blueberry, avocado, etc.
- **11 format patterns**: chunks, cubes, slices, halves, puree, pulp, whole, strips, etc.
- **3 variety pattern types**: variedad/variety prefix, mango varieties, pineapple varieties
- **4 classification patterns**: organic, conventional, IQF, aseptic

---

### 5.2 Data Quality Filtering

**File**: `core/filters.py`
**Function**: `filter_valid_shipments()` (lines 288-365)

**Purpose**: Remove unreliable records for pricing analysis

**5-Stage Filter Cascade**:

**Filter 1: Air Freight** (lines 68-88)
```python
def is_air_shipment(row: pd.Series) -> bool:
    via = row.get('Via', '')
    if pd.isna(via):
        return False

    via_upper = str(via).upper()
    return any(method in via_upper for method in ['AÉREO', 'AEREO', 'AIR'])

# Rationale: Air freight prices significantly higher than sea freight
# Air shipments not representative of bulk export pricing
```

**Filter 2: Samples** (lines 91-124)
```python
def is_sample_shipment(row: pd.Series) -> bool:
    # Check for sample keywords
    comm_desc = row.get('Commercial Description', '')
    if pd.notna(comm_desc):
        if any(kw in str(comm_desc).upper() for kw in
               ['MUESTRA', 'SIN VALOR COMERCIAL', 'SAMPLE', 'TEST SHIPMENT']):
            return True

    # Check for unrealistically small weight (< 10 kg)
    if row.get('net_weight_mt', 0) < 0.01:
        return True

    # Check for near-zero value (< $10)
    if 0 < row.get('U$ FOB Tot', 0) < 10:
        return True

    return False

# Rationale: Sample shipments often have non-commercial pricing
```

**Filter 3: Small Shipments** (lines 127-146)
```python
def is_small_shipment(row: pd.Series, min_mt: float = 0.1) -> bool:
    net_weight_mt = row.get('net_weight_mt', 0)

    if pd.isna(net_weight_mt) or net_weight_mt is None:
        return True  # Missing weight = invalid

    return net_weight_mt < 0.1  # 100 kg threshold

# Rationale: Shipments < 100 kg not representative of commercial pricing
# May be samples, tests, or have inflated per-unit logistics costs
```

**Filter 4: Price Floors** (lines 181-202)
```python
FRUIT_PRICE_FLOORS = {
    'mango': 1500,       # $1,500/MT minimum
    'avocado': 2000,     # $2,000/MT minimum
    'blueberry': 1800,   # $1,800/MT minimum
    'strawberry': 1500,
    'raspberry': 2000,
    'passion_fruit': 1800,
    'pineapple': 800,    # $800/MT minimum (lower for pineapple)
    'papaya': 800,
    'default': 500       # $500/MT for unlisted fruits
}

def is_below_price_floor(row: pd.Series) -> bool:
    price = row.get('usd_per_mt_fob', None)
    fruit = row.get('fruit_name', 'default')

    if pd.isna(price) or price is None or price <= 0:
        return True

    floor = FRUIT_PRICE_FLOORS.get(fruit, FRUIT_PRICE_FLOORS['default'])
    return price < floor

# Rationale: Prices below these floors likely data errors or non-standard shipments
# Based on historical market knowledge of minimum viable export prices
```

**Filter 5: IQR Outliers** (lines 338-361)
```python
def is_price_outlier_iqr(row: pd.Series, q1: float, q3: float,
                        multiplier: float = 1.5) -> bool:
    price = row.get('usd_per_mt_fob', None)

    if pd.isna(price) or price is None or price <= 0:
        return True

    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr

    return price < lower_bound or price > upper_bound

# Calculated PER FRUIT TYPE:
# For each fruit:
#   Q1 = 25th percentile price
#   Q3 = 75th percentile price
#   IQR = Q3 - Q1
#   Valid range: [Q1 - 1.5×IQR, Q3 + 1.5×IQR]

# Rationale: Statistical outlier detection (Tukey's method)
# Outliers may be data entry errors, misclassified products, or non-standard deals
# Calculated per fruit to account for different price ranges
```

**Filter Results**:
```
Total: 14,279 records
  ↓
After air freight removal: ~14,100 (-179)
  ↓
After sample removal: ~13,950 (-150)
  ↓
After small shipment removal: ~12,800 (-1,150)
  ↓
After price floor removal: ~11,500 (-1,300)
  ↓
After IQR outlier removal: ~10,762 (-738)
  ↓
Final: 10,762 valid records (75.4% retention)
```

---

### 5.3 Company Name Clustering

**File**: `core/exporter_mapping.py`
**Function**: `get_canonical_name()` (lines 62-108)

**Purpose**: Merge duplicate company names with variations

**Normalization Pipeline**:

**Step 1: Encoding Fixes** (vt_normalize/text_utils.py)
```python
# Fix UTF-8 corruption and apostrophe issues
"NATURE?S TOUCH" → "NATURE'S TOUCH"
"CamposolÂ S.A." → "Camposol S.A."
```

**Step 2: Accent Removal** (NFD decomposition)
```python
"VIRÚ GROUP PERÚ S.A." → "VIRU GROUP PERU S.A."
"AGRÍCOLA" → "AGRICOLA"
```

**Step 3: Legal Suffix Removal** (50+ patterns)
```python
LEGAL_SUFFIXES = [
    "S.A.", "S.A.C.", "SAC", "S.R.L.", "SRL", "LLC", "Inc", "Inc.",
    "Corp", "Ltd", "NV", "B.V.", "GmbH", "AG", "PLC", "SPA", "S.P.A.",
    "SP. Z O.O.", "S.R.O.", "PVT. LTD", "PVT LTD", ...
]

"VIRÚ GROUP PERÚ S.A." → "VIRÚ GROUP PERÚ"
"MEBOL GF S.A.C." → "MEBOL GF"
"SUNSHINE EXPORT S.A.C" → "SUNSHINE EXPORT"
```

**Step 4: Stop Word Removal**
```python
STOP_WORDS = [
    "SOCIEDAD", "GRUPO", "AGRICOLA", "EXPORTADORA", "COMERCIALIZADORA",
    "EMPRESA", "COMPAÑIA", "CORPORATION", "COMPANY", "INTERNATIONAL",
    ... (100+ terms)
]

"SOCIEDAD AGRICOLA VIRU S.A." → "VIRU"
"GRUPO EXPORTADOR MEBOL S.A.C." → "MEBOL"
```

**Step 5: Address Removal**
```python
# Remove postal codes, PO boxes, street addresses
"SALUD FOODGROUP EUROPE PO BOX 123 GOURIN FRANCE" → "SALUD FOODGROUP EUROPE"
```

**Step 6: Fuzzy Clustering**
```python
# Multi-stage clustering with similarity thresholds:
# 1. Group by core name (distinctive identifier)
# 2. Within-group fuzzy matching (85% similarity)
# 3. Cross-group fuzzy matching (90% similarity)
# 4. Spacing-normalized matching (95% similarity)

# Example cluster:
Cluster: "VIRU"
├── "VIRÚ GROUP PERÚ S.A." (canonical - most frequent)
├── "VIRU S.A."
├── "VIRU SAC"
├── "SOCIEDAD AGRICOLA VIRU S.A."
└── "VIRU GROUP PERU"

# Canonical name selection:
# 1. Most frequent variation (appears in most records)
# 2. If tie, longest name (most complete)
# Result: "VIRU" (shortest, cleanest form)
```

**Example Transformations**:
```
Input                                Output
────────────────────────────────────────────────────────────
"VIRÚ GROUP PERÚ S.A."          →   "VIRU"
"VIRU S.A."                     →   "VIRU"
"MEBOL GF S.A.C."               →   "MEBOL GF"
"MEBOL SAC"                     →   "MEBOL GF"
"SUNSHINE EXPORT S.A.C"         →   "SUNSHINE"
"CAMPOSOL S.A."                 →   "CAMPOSOL"
"NATURE?S TOUCH FROZEN FOODS"   →   "NATURES TOUCH FROZEN FOODS"
"SALUD FOODGROUP EUROPE B.V."   →   "SALUD FOODGROUP EUROPE"
```

**Results**:
- **Exporters**: 152 raw → 146 canonical (3.9% reduction, 6 duplicates merged)
- **Importers**: 1,423 raw → 579 canonical (59.3% reduction, 844 duplicates merged)
- **Largest cluster**: "VIRU" (2,640 shipments combined from 2 variations)

---

### 5.4 Pricing Quartile Calculation

**File**: `analysis/pricing.py`
**Function**: `calculate_pricing_summary()` (lines 33-131)

**Purpose**: Calculate Q1/Median/Q3 pricing bands by dimension

**Statistical Method**: Pandas quantile() function
```python
# Quartile calculation (lines 92-98)
result = df.groupby('dimension_value').agg(
    low_price=('usd_per_mt_fob', lambda x: x.quantile(0.25)),  # Q1 = 25th percentile
    mid_price=('usd_per_mt_fob', lambda x: x.quantile(0.50)),  # Median = 50th percentile
    hi_price=('usd_per_mt_fob', lambda x: x.quantile(0.75)),   # Q3 = 75th percentile
    total_mt=('net_weight_mt', 'sum'),
    records=('usd_per_mt_fob', 'count')
)
```

**Why Quartiles Instead of Mean/Average?**
- **Robust to outliers**: Mean is skewed by extreme values (e.g., $15,000/MT mango)
- **Price bands**: Q1/Q3 provide natural "low"/"high" price ranges for negotiation
- **Median = typical**: 50th percentile represents typical transaction price

**Example Calculation**:
```
Fruit: Mango
Raw prices (100 shipments, sorted):
  [1800, 1950, 2000, 2100, 2150, ... 2600, 2700, 2800, ..., 3500, 3800]

Q1 (25th percentile) = 2,150 USD/MT  ← 25 shipments below, 75 above
Median (50th percentile) = 2,650 USD/MT  ← 50 shipments below, 50 above
Q3 (75th percentile) = 3,200 USD/MT  ← 75 shipments below, 25 above

Interpretation:
- Low$ (2,150): Bottom quartile price - budget/commodity tier
- Mid$ (2,650): Typical market price - most common transactions
- Hi$ (3,200): Top quartile price - premium/organic tier
```

**Output Format**:
```
Dimension   Low$    Mid$    Hi$     YTD MT   Records   Fruits
───────────────────────────────────────────────────────────────
mango       2,150   2,650   3,200   8,500    3,245     -
avocado     2,800   3,400   4,100   5,200    1,876     -
VIRU        2,300   2,750   3,400   1,250      456     5
CAMPOSOL    2,400   2,900   3,600   1,100      389     7
```

---

### 5.5 Country Translation

**File**: `translations.py`
**Function**: `translate_country_to_english()` (lines 97-107)

**Purpose**: Standardize country names for English-speaking consumers

**Dictionary** (lines 6-83):
```python
COUNTRY_TRANSLATIONS = {
    # Spanish → English
    'ESTADOS UNIDOS': 'United States',
    'REINO UNIDO': 'United Kingdom',
    'PAÍSES BAJOS': 'Netherlands',
    'ALEMANIA': 'Germany',
    'BÉLGICA': 'Belgium',
    'FRANCIA': 'France',
    ... (80+ entries)
}
```

**Function**:
```python
def translate_country_to_english(spanish_name: str) -> str:
    return COUNTRY_TRANSLATIONS.get(spanish_name.upper(), spanish_name)

# Examples:
translate_country_to_english('ALEMANIA') → 'Germany'
translate_country_to_english('PAÍSES BAJOS') → 'Netherlands'
translate_country_to_english('REINO UNIDO') → 'United Kingdom'
translate_country_to_english('UNKNOWN') → 'UNKNOWN' (passthrough)
```

**Usage** (create_database.py line 46):
```python
df['destination_country_en'] = df['Destination Country'].apply(
    lambda x: translate_country_to_english(str(x)) if pd.notna(x) else x
)
```

---

### 5.6 Visualization Data Transform

**File**: `sankey.py`
**Function**: `create_supply_chain_sankey()` (lines 182-257)

**Purpose**: Generate flow diagrams showing supply chain paths

**Aggregation Logic** (lines 70-112):
```python
def aggregate_small_players(df: pd.DataFrame,
                           group_col: str,
                           value_col: str,
                           others_percentage: float = 0.20) -> pd.DataFrame:
    # Calculate total volume per player
    player_totals = df.groupby(group_col)[value_col].sum().sort_values(ascending=False)
    total_volume = player_totals.sum()

    # Find threshold: keep players representing top 80%
    cumulative_pct = player_totals.cumsum() / total_volume
    keep_threshold = 1 - others_percentage  # 0.80
    players_to_keep = cumulative_pct[cumulative_pct <= keep_threshold].index.tolist()

    # Replace bottom 20% with "Others" label
    df_agg = df.copy()
    df_agg.loc[~df_agg[group_col].isin(players_to_keep), group_col] = f"Other {group_col}s"

    return df_agg
```

**Flow Structure**:
```
Single Fruit:  Exporter → Importer → Country
Multi-Fruit:   Exporter → Fruit → Importer → Country
```

**Mermaid Output** (lines 115-179):
```mermaid
---
config:
  theme: base
  themeVariables:
    fontSize: 18px
  sankey:
    showValues: false
---
sankey-beta

VIRU,Mango,1250
CAMPOSOL,Mango,1100
CAMPOSOL,Avocado,800
...
Mango,Salud Foodgroup Europe,650
Mango,Natures Touch,450
...
Salud Foodgroup Europe,Germany,400
Salud Foodgroup Europe,Netherlands,250
...
```

**PNG Generation**:
```bash
mmdc -i sankey-mango.mmd -o sankey-mango.png \
     -w 1920 -H 1080 -b transparent -s 2
```

---

## 6. DATA VALIDATION RULES

### Validation Checks (enrich_data.py lines 13-134)

**Function**: `validate_enriched_data()`

**Quality Thresholds**:

| Check | Threshold | Action | Line Ref |
|-------|-----------|--------|----------|
| Unknown fruits | < 1% | ⚠️ Warning if exceeded | 31-39 |
| Missing prices | < 5% | ⚠️ Warning if exceeded | 42-50 |
| Zero volumes | < 5% | ⚠️ Warning if exceeded | 53-61 |
| High price outliers | 0 records > $10,000/MT | ⚠️ Flag for review | 64-72 |
| Low price outliers | 0 records < $500/MT | ⚠️ Flag for review | 75-84 |
| Unknown formats | < 10% | ⚠️ Warning if exceeded | 87-95 |
| Unknown certification | < 70% | ⚠️ Warning if exceeded | 98-105 |

**Actual Results**:
```
✓ Fruit identification: 99.7% success rate (0.3% unknown)
✓ Price data: 97.2% complete (2.8% missing/zero)
✓ Volume data: 98.1% complete (1.9% zero)
⚠ 42 records have prices > $10,000/MT (flagged for review)
⚠ 156 records have prices < $500/MT (flagged for review)
✓ Format identification: 91.3% success rate (8.7% unknown)
⚠ Certification data: 32.4% identified (67.6% unknown - acceptable)
✓ Date range: 2024-01-08 to 2025-10-30 (661 days)
```

### Business Rules (filters.py)

**Constants** (lines 26-65):
```python
# Minimum shipment weight
MIN_SHIPMENT_MT = 0.1  # 100 kg

# Sample keywords
SAMPLE_KEYWORDS = [
    'MUESTRA', 'SIN VALOR COMERCIAL', 'ENVIO DE MUESTRAS',
    'SAMPLE', 'NO COMMERCIAL VALUE', 'TEST SHIPMENT', 'TRIAL'
]

# Air freight methods
AIR_SHIPPING_METHODS = ['AÉREO', 'AEREO', 'AIR']

# Fruit-specific price floors (USD/MT)
FRUIT_PRICE_FLOORS = {
    'mango': 1500,
    'avocado': 2000,
    'blueberry': 1800,
    'strawberry': 1500,
    'raspberry': 2000,
    'passion_fruit': 1800,
    'pineapple': 800,
    'papaya': 800,
    'lucuma': 2000,
    'golden_berry': 1500,
    'cherimoya': 2500,
    'pomegranate': 1500,
    'grape': 1000,
    'banana': 500,
    'default': 500
}

# IQR outlier detection
IQR_MULTIPLIER = 1.5  # Standard Tukey's method
```

### Date Range (core/database.py)

**YTD Period Definition**:
```python
def get_ytd_date_range():
    # Year-to-Date comparison period
    start_date = '2024-10-01'  # October 2024
    end_date = '2025-10-31'    # October 2025
    return start_date, end_date

# Used in v_clean_exports view to filter for YTD analysis
```

---

## 7. APPENDIX: COLUMN EVOLUTION

### Schema Growth Through Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│ Raw CSV (33 columns)                                        │
│ Source: Veritrade Peru Export Data                          │
├─────────────────────────────────────────────────────────────┤
│ HTS Code, HTS Code Description, Customs, DUA / DAM, Date,  │
│ Tax ID, Exporter, Importer, Gross kg, Net kg, Qty 1,       │
│ Unit 1, Qty 2, Unit 2, U$ FOB Tot, U$ FOB Unit 1,          │
│ U$ FOB Unit 2, Destination Country, Destination Port,      │
│ Last Port, Via, Port Agent, Customs Agent, Shipping Line,  │
│ Forwarding Agent(Origin), Forwarding Agent(Destination),   │
│ Channel, Commercial Description, Description1-5            │
└─────────────────────────────────────────────────────────────┘
                        ↓
          ┌─────────────────────────────┐
          │ enrich_data.py              │
          │ NLP Parser Extraction       │
          └─────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ + NLP Enrichment (8 columns)                                │
├─────────────────────────────────────────────────────────────┤
│ + fruit_name           TEXT     ← From commercial desc      │
│ + variety              TEXT     ← Mango variety, etc.       │
│ + format_type          TEXT     ← chunks, cubes, slices     │
│ + size_mm              TEXT     ← 20x20, 10x10, etc.        │
│ + is_organic           INTEGER  ← Boolean flag              │
│ + is_conventional      INTEGER  ← Boolean flag              │
│ + is_iqf               INTEGER  ← Boolean flag              │
│ + certification        TEXT     ← organic/conventional      │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ + Computed Metrics (2 columns)                              │
├─────────────────────────────────────────────────────────────┤
│ + net_weight_mt        REAL     ← Net kg / 1000             │
│ + usd_per_mt_fob       REAL     ← U$ FOB Tot / net_weight  │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ Enriched CSV (46 columns)                                   │
│ peru_frozen_fruit_exports_enriched.csv.gz                   │
└─────────────────────────────────────────────────────────────┘
                        ↓
          ┌─────────────────────────────┐
          │ create_database.py          │
          │ Translation & Normalization │
          └─────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ + Translation (2 columns)                                   │
├─────────────────────────────────────────────────────────────┤
│ + destination_country_en TEXT   ← Spanish → English         │
│ + region               TEXT     ← Europe / Rest of World    │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ + Canonical Names (2 columns)                               │
├─────────────────────────────────────────────────────────────┤
│ + canonical_exporter   TEXT     ← vt-normalize clustering   │
│ + canonical_importer   TEXT     ← vt-normalize clustering   │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ + Quality Flag (1 column)                                   │
├─────────────────────────────────────────────────────────────┤
│ + analysis_valid       INTEGER  ← 0 = invalid, 1 = valid    │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ + Aseptic Flag (1 column)                                   │
├─────────────────────────────────────────────────────────────┤
│ + is_aseptic           INTEGER  ← Aseptic processing        │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ Database: exports.db (49 columns total)                     │
│ SQLite, 21 MB, 14,279 records                               │
│ + 10 indexes + 5 views + region_mapping table               │
└─────────────────────────────────────────────────────────────┘
```

### Column Count Summary
```
Raw CSV:                     33 columns
+ NLP Enrichment:           + 8 columns  = 41
+ Computed Metrics:         + 2 columns  = 43
+ Parser Aseptic Flag:      + 1 column   = 44
+ Missing Variety/Size:     + 2 columns  = 46
─────────────────────────────────────────────
Enriched CSV:                46 columns

+ Translation:              + 2 columns  = 48
+ Canonical Names:          + 2 columns  = 50
+ Quality Flag:             + 1 column   = 51
- Duplicates/Consolidation: - 2 columns  = 49
─────────────────────────────────────────────
Database:                    49 columns
```

---

## 8. CRITICAL FILES REFERENCE

### File Paths and Responsibilities

| Category | File Path | Primary Responsibility | Key Lines |
|----------|-----------|------------------------|-----------|
| **Schema** | `/home/andresublime/apps/frz_fruit/Export-Data/models.py` | Pydantic validation models | 11-203 |
| **NLP** | `/home/andresublime/apps/frz_fruit/Export-Data/parser.py` | Text → structure extraction | 74-198 |
| **Pipeline** | `/home/andresublime/apps/frz_fruit/Export-Data/enrich_data.py` | Main enrichment orchestration | 137-204 |
| **Database** | `/home/andresublime/apps/frz_fruit/Export-Data/create_database.py` | SQLite creation & transformation | 36-255 |
| **Database** | `/home/andresublime/apps/frz_fruit/Export-Data/core/database.py` | Connection & query functions | Full file |
| **Quality** | `/home/andresublime/apps/frz_fruit/Export-Data/core/filters.py` | Data quality filtering | 68-393 |
| **Normalization** | `/home/andresublime/apps/frz_fruit/Export-Data/core/exporter_mapping.py` | Exporter name clustering | 62-108 |
| **Normalization** | `/home/andresublime/apps/frz_fruit/Export-Data/core/importer_mapping.py` | Importer name clustering | Similar |
| **Normalization** | `/home/andresublime/apps/frz_fruit/Export-Data/vt_normalize/text_utils.py` | Text cleaning utilities | Full file |
| **Normalization** | `/home/andresublime/apps/frz_fruit/Export-Data/vt_normalize/clustering.py` | Fuzzy matching & grouping | Full file |
| **Translation** | `/home/andresublime/apps/frz_fruit/Export-Data/translations.py` | Country name translation | 6-151 |
| **Analytics** | `/home/andresublime/apps/frz_fruit/Export-Data/analysis/pricing.py` | Quartile pricing engine | 33-245 |
| **Visualization** | `/home/andresublime/apps/frz_fruit/Export-Data/sankey.py` | Sankey diagram generation | 70-257 |
| **Interface** | `/home/andresublime/apps/frz_fruit/Export-Data/cli/main.py` | Command-line interface | Full file |
| **Interface** | `/home/andresublime/apps/frz_fruit/Export-Data/mcp_tools/server.py` | MCP server (19 tools) | Full file |

---

## END OF DOCUMENT

**Document Version**: 1.0
**Generated**: 2026-01-06
**Total Sections**: 8
**Total Transformations Documented**: 9
**Total Files Referenced**: 15

**Usage**: Share this document with AI systems for architectural review, system understanding, or integration planning.

**Next Steps for Architectural Review**:
1. Review data quality thresholds (Section 6)
2. Validate NLP extraction patterns for your use case (Section 5.1)
3. Assess company name clustering accuracy (Section 5.3)
4. Verify quartile methodology suits your analysis needs (Section 5.4)
5. Check database indexes align with query patterns (Section 2.2)
