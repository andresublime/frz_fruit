# SESSION CONTEXT DUMP
# Peru Frozen Fruit Export Analysis - Data Lineage Analysis Session

**Session Date**: 2026-01-06
**Task**: Analyze project data lineage and create DATA_STRUCTURE.md
**Status**: ✅ COMPLETED

---

## SESSION SUMMARY

### What We Accomplished

1. ✅ **Explored entire project structure** using 3 parallel Explore agents
   - Agent 1: Project structure and data entry points
   - Agent 2: Data models and schemas
   - Agent 3: Data transformation and processing logic

2. ✅ **Designed implementation plan** using Plan agent
   - Created structured approach for DATA_STRUCTURE.md
   - Defined 8 sections with detailed content requirements

3. ✅ **Read all critical files** (15 files total):
   - models.py (Pydantic schemas)
   - parser.py (NLP extraction)
   - create_database.py (Database creation)
   - core/filters.py (Quality filtering)
   - core/exporter_mapping.py (Name normalization)
   - translations.py (Country translation)
   - analysis/pricing.py (Quartile analytics)
   - sankey.py (Visualization)
   - enrich_data.py (Main enrichment pipeline)
   - And more...

4. ✅ **Created comprehensive DATA_STRUCTURE.md**
   - 8 sections as planned
   - ~1,400 lines
   - Complete data lineage documentation
   - Optimized for AI architectural review

---

## PROJECT OVERVIEW

### Project Name
**Peru Frozen Fruit Export Analysis**

### Project Purpose
Comprehensive data analysis platform for Peru's frozen fruit export industry providing:
- Pricing analytics with quartile-based calculations (Q1/Median/Q3)
- Market intelligence and competitive analysis
- Export pattern visualization
- Company name normalization and clustering
- CLI and MCP interfaces for data access

### Key Statistics
- **Records**: 14,279 export shipments (Jan 2024 - Oct 2025)
- **Exporters**: 152 raw → 146 canonical (3.9% reduction via vt-normalize)
- **Importers**: 1,423 raw → 579 canonical (59.3% reduction)
- **Fruits**: 20+ types (mango, avocado, blueberry, pineapple, etc.)
- **Destinations**: 57 countries
- **Volume**: 218,282 MT
- **Value**: $507.8M FOB
- **Data Quality**: 75.4% retention after filtering

### Data Source
- **Provider**: Veritrade (commercial customs data platform)
- **Source File**: `Veritrade_JUAN_CABREJOS_REPCOANDINO_COM_PE_E_20251106063034.xlsx`
- **Downloaded**: 2025-11-06
- **Update Method**: Manual download from Veritrade portal
- **Format**: Peru customs export declarations

---

## CRITICAL INSIGHTS

### 1. Data Pipeline Architecture

**6-Stage Transformation Pipeline**:

```
Stage 1: NLP Enrichment (enrich_data.py)
  Raw CSV (33 cols) → Enriched CSV (46 cols)
  • DescriptionParser.parse() extracts structured data from text
  • 99.7% fruit identification success rate
  ↓
Stage 2: Translation (create_database.py lines 44-53)
  + Country translation (Spanish → English, 80+ mappings)
  + Region classification (Europe vs Rest of World)
  ↓
Stage 3: Canonical Names (create_database.py lines 59-80)
  + vt-normalize clustering
  + 152 → 146 exporters, 1,423 → 579 importers
  ↓
Stage 4: Database Loading (create_database.py lines 82-103)
  + SQLite with 10 indexes + 5 views
  + exports.db (21 MB, 49 columns)
  ↓
Stage 5: Quality Filtering (core/filters.py lines 288-365)
  + 5-stage filter cascade
  + 75.4% retention (10,762 valid from 14,279 total)
  ↓
Stage 6: Analytics (analysis/pricing.py lines 33-131)
  + Quartile pricing (Q1/Median/Q3)
  + Group by fruit/exporter/importer
```

### 2. Schema Evolution

```
33 Original Columns (Veritrade CSV)
  + 8 NLP Enrichment (fruit_name, variety, format_type, size_mm, etc.)
  + 2 Computed Metrics (net_weight_mt, usd_per_mt_fob)
  + 2 Translation (destination_country_en, region)
  + 2 Canonical Names (canonical_exporter, canonical_importer)
  + 1 Quality Flag (analysis_valid)
  + 1 Aseptic Flag (is_aseptic)
────────────────────────────────────
= 49 Database Columns
```

### 3. Key Transformations

**NLP Parser** (parser.py lines 74-122):
- 24 fruit patterns (Spanish + English regex)
- 11 format patterns (chunks, cubes, slices, puree, etc.)
- Size extraction (20x20mm → "20x20")
- Certification detection (organic, conventional, IQF)

**Quality Filters** (core/filters.py):
1. Air freight removal (sea freight only)
2. Sample removal (MUESTRA, < 10kg, < $10)
3. Small shipment removal (< 0.1 MT / 100kg)
4. Price floor enforcement ($500-$2,500/MT per fruit)
5. IQR outlier removal (1.5× multiplier, per-fruit)

**Company Clustering** (vt-normalize):
- Encoding fixes (NATURE?S → NATURE'S)
- Accent removal (VIRÚ → VIRU)
- Legal suffix stripping (S.A., LLC, GmbH, etc.)
- Stop word removal (SOCIEDAD, GRUPO, AGRICOLA)
- Fuzzy matching (80-95% thresholds)
- Result: "VIRÚ GROUP PERÚ S.A." + "VIRU S.A." → "VIRU"

**Pricing Quartiles** (analysis/pricing.py):
- Q1 (25th percentile) = Low$ (budget tier)
- Median (50th percentile) = Mid$ (typical price)
- Q3 (75th percentile) = Hi$ (premium tier)
- Robust to outliers, better than mean/average

### 4. Database Structure

**Main Table**: `exports` (49 columns, 14,279 records)

**Indexes** (10 total):
- idx_exporter, idx_canonical_exporter, idx_canonical_importer
- idx_destination, idx_fruit, idx_format, idx_size, idx_certification
- idx_date, idx_region

**Views** (5 total):
- `v_clean_exports` - Filtered valid records (analysis_valid=1, YTD)
- `exporter_products` - Aggregated by exporter × fruit × format
- `destination_products` - Aggregated by country × fruit × format
- `monthly_exports` - Time series for seasonality
- `regional_exports` - Europe vs Rest of World

**Secondary Table**: `region_mapping` (31 European countries)

### 5. Data Quality

**Validation Results** (enrich_data.py):
- ✅ Fruit identification: 99.7% success
- ✅ Price data: 97.2% complete
- ✅ Volume data: 98.1% complete
- ⚠️ High outliers: 42 records > $10,000/MT
- ⚠️ Low outliers: 156 records < $500/MT
- ✅ Format identification: 91.3% success
- ⚠️ Certification: 32.4% identified (67.6% unknown - acceptable)

**Filter Statistics**:
- Total: 14,279 records
- Air freight removed: ~179
- Samples removed: ~150
- Small shipments removed: ~1,150
- Below price floor removed: ~1,300
- IQR outliers removed: ~738
- **Final valid**: 10,762 (75.4% retention)

---

## CRITICAL FILES MAP

### Core Data Files

```
/home/andresublime/apps/frz_fruit/Export-Data/

📁 Data Files:
├── peru_frozen_fruit_exports.csv.gz              [915 KB, 14,279 records, 33 cols]
├── peru_frozen_fruit_exports_enriched.csv.gz     [1.1 MB, 14,279 records, 46 cols]
├── exports.db                                    [21 MB, SQLite, 49 cols]
├── data/clustered_exporters.json                 [Exporter mappings: 152→146]
└── data/clustered_importers.json                 [Importer mappings: 1,423→579]
```

### Python Modules

```
📁 Schema & Models:
├── models.py                          [Pydantic schemas - ExportRecord, FruitProduct, etc.]
├── parser.py                          [NLP text extraction - DescriptionParser]
└── translations.py                    [Country translation - Spanish→English]

📁 Core Infrastructure:
├── core/database.py                   [SQLite connection & queries]
├── core/filters.py                    [Quality filtering - 5-stage cascade]
├── core/exporter_mapping.py           [Exporter name normalization]
├── core/importer_mapping.py           [Importer name normalization]
└── core/mappings.py                   [Region & country mappings]

📁 VT-Normalize (Name Clustering):
├── vt_normalize/clustering.py         [Fuzzy matching & grouping]
├── vt_normalize/text_utils.py         [Text cleaning & normalization]
├── vt_normalize/config.py             [Stop words & legal suffixes]
└── vt_normalize/models.py             [Company name data structures]

📁 Processing Scripts:
├── enrich_data.py                     [Main enrichment pipeline]
├── create_database.py                 [Database creation & transformation]
├── cluster_company_names.py           [Company name clustering script]
└── update_database_schema.py          [Schema migration utilities]

📁 Analytics:
├── analysis/pricing.py                [Quartile pricing engine]
└── sankey.py                          [Sankey diagram data generator]

📁 Interfaces:
├── cli/main.py                        [CLI for pricing queries]
├── cli/gui.py                         [GUI interface (new)]
└── mcp_tools/server.py                [MCP server - 19 AI-accessible tools]
```

### Documentation Files

```
📁 Documentation:
├── README.md                          [Project overview]
├── USER_GUIDE.md                      [MCP tools guide]
├── QUICKSTART_V2.md                   [Quick start guide]
├── VT_NORMALIZE_INTEGRATION.md        [Clustering details]
├── MODULAR_ARCHITECTURE.md            [Architecture docs]
├── IMPLEMENTATION_SUMMARY.md          [Implementation notes]
├── DATA_STRUCTURE.md                  [THIS SESSION'S OUTPUT - Data lineage]
└── SESSION_CONTEXT.md                 [THIS FILE - Context dump]
```

---

## KEY CODE SNIPPETS

### 1. NLP Parser (parser.py:74-122)

```python
@classmethod
def parse(cls, description: str) -> FruitProduct:
    """Parse commercial description into structured product data."""
    desc_lower = description.lower()

    # Extract fruit (24 types via regex)
    fruit_name = cls._extract_fruit(desc_lower)

    # Extract variety (Kent, Edward, MD2, etc.)
    variety = cls._extract_variety(desc_lower)

    # Extract format (chunks, cubes, puree, etc.)
    product_format = cls._extract_format(desc_lower)

    # Extract classification (organic, IQF, etc.)
    classification = cls._extract_classification(desc_lower)

    return FruitProduct(
        fruit_name=fruit_name,
        variety=variety,
        product_format=product_format,
        classification=classification
    )
```

**Example**:
```
Input:  "MANGO CONGELADO ORGANICO CHUNKS 20X20MM IQF VARIEDAD: EDWARD"
Output: FruitProduct(
          fruit_name='mango',
          variety='Edward',
          product_format=ProductFormat(format_type='chunks', size_mm='20x20'),
          classification=ProductClassification(is_organic=True, is_iqf=True)
        )
```

### 2. Quality Filter Cascade (core/filters.py:288-365)

```python
def filter_valid_shipments(df: pd.DataFrame) -> pd.DataFrame:
    """5-stage quality filter cascade."""
    initial_count = len(df)

    # 1. Remove air freight
    df = df[~df.apply(is_air_shipment, axis=1)]

    # 2. Remove samples
    df = df[~df.apply(is_sample_shipment, axis=1)]

    # 3. Remove small shipments (< 0.1 MT)
    df = df[~df.apply(is_small_shipment, axis=1)]

    # 4. Remove below price floor
    df = df[~df.apply(is_below_price_floor, axis=1)]

    # 5. Remove IQR outliers (per fruit)
    bounds = calculate_iqr_bounds(df, 'usd_per_mt_fob', 'fruit_name')
    df = df.merge(bounds[['fruit_name', 'q1', 'q3']], on='fruit_name')
    df = df[~df.apply(lambda row: is_price_outlier_iqr(row, row['q1'], row['q3']), axis=1)]

    print(f"Final: {len(df)} / {initial_count} ({len(df)/initial_count*100:.1f}%)")
    return df
```

### 3. Canonical Name Mapping (core/exporter_mapping.py:62-108)

```python
def get_canonical_name(exporter_name: str) -> str:
    """Get canonical (standardized) name for an exporter."""
    _load_database()  # Lazy-load clustered_exporters.json

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

**Example**:
```
get_canonical_name('VIRÚ GROUP PERÚ S.A.') → 'VIRU'
get_canonical_name('VIRU S.A.') → 'VIRU'
get_canonical_name('MEBOL GF S.A.C.') → 'MEBOL GF'
```

### 4. Quartile Pricing (analysis/pricing.py:92-98)

```python
# Calculate quartiles using pandas
result = df.groupby('dimension_value').agg(
    low_price=('usd_per_mt_fob', lambda x: x.quantile(0.25)),   # Q1
    mid_price=('usd_per_mt_fob', lambda x: x.quantile(0.50)),   # Median
    hi_price=('usd_per_mt_fob', lambda x: x.quantile(0.75)),    # Q3
    total_mt=('net_weight_mt', 'sum'),
    records=('usd_per_mt_fob', 'count')
).reset_index()
```

**Output**:
```
Fruit         Low$    Mid$    Hi$     YTD MT   Records
─────────────────────────────────────────────────────
mango         2,150   2,650   3,200   8,500    3,245
avocado       2,800   3,400   4,100   5,200    1,876
```

---

## EXPLORATION AGENT FINDINGS

### Agent 1: Project Structure & Data Entry

**Key Findings**:
- **No API Integration**: Data imported manually as Excel/CSV files from Veritrade
- **Update Frequency**: Manual downloads from Veritrade portal
- **Data Flow**: Veritrade Portal → CSV → enrich_data.py → SQLite → Analytics

**Entry Points**:
1. **CLI**: `python cli/main.py summary fruit [--region Europe]`
2. **MCP Server**: 19 tools for AI-powered queries (Claude Desktop integration)
3. **Data Processing**: `python enrich_data.py`, `python create_database.py`
4. **Visualization**: Sankey diagram generators for flow analysis

**Configuration**:
- Database path: Hard-coded in `core/database.py`
- YTD date range: Oct 2024 - Oct 2025 (hard-coded)
- Quality thresholds: Defined in `core/filters.py`
- Region definitions: Hard-coded in `create_database.py`

### Agent 2: Data Models & Schemas

**Pydantic Models** (models.py):
- `ExportRecord`: Main container (33 original + 13 enriched fields)
- `FruitProduct`: Structured product info (fruit, variety, format, classification)
- `ProductFormat`: Format/size data (chunks, cubes, slices, 20x20, etc.)
- `ProductClassification`: Certification flags (organic, conventional, IQF, aseptic)

**Database Schema** (exports.db):
- Main table: exports (49 columns, 14,279 records)
- Views: v_clean_exports, exporter_products, destination_products, monthly_exports, regional_exports
- Indexes: 10 indexes for query performance
- Secondary: region_mapping table (31 European countries)

**Data Clustering**:
- Exporters: `data/clustered_exporters.json` (152→146)
- Importers: `data/clustered_importers.json` (1,423→579)
- Format: JSON with canonical_name, aliases, count

### Agent 3: Data Transformation & Processing

**Enrichment Pipeline** (enrich_data.py):
- NLP parsing: DescriptionParser.parse() on commercial descriptions
- Metric calculation: net_weight_mt, usd_per_mt_fob
- Validation: 8 quality checks with warnings

**Quality Filtering** (core/filters.py):
- 5-stage cascade: air freight, samples, small shipments, price floors, IQR outliers
- Result: 75.4% retention (10,762 valid from 14,279)

**Company Normalization** (vt_normalize/):
- Text cleaning: encoding fixes, accent removal, legal suffix stripping
- Fuzzy clustering: 80-95% similarity thresholds
- Multi-stage: within-group → cross-group → spacing-normalized

**Analytics Transformation** (analysis/pricing.py):
- Quartile aggregation: Q1/Median/Q3 by dimension
- Drill-down: Filter by entity, aggregate by another dimension
- Regional filtering: Europe, RoW, or worldwide

**Visualization Transform** (sankey.py):
- Flow aggregation: Exporter → Fruit → Importer → Country
- Small player grouping: Bottom 20% → "Others"
- Mermaid output: .mmd → .png (via mmdc CLI)

---

## IMPORTANT PATTERNS & CONVENTIONS

### 1. Column Naming
- **Original Veritrade**: Title case with spaces: "Destination Country", "U$ FOB Tot"
- **Enriched fields**: Snake case: `fruit_name`, `format_type`, `net_weight_mt`
- **Canonical names**: Lowercase with underscore: `canonical_exporter`, `canonical_importer`
- **Database aliases**: SQLite column names use brackets: `[Destination Country]`, `[U$ FOB Tot]`

### 2. Region Classification
```python
EUROPE_COUNTRIES_EN = {
    'Germany', 'Austria', 'Belgium', 'France', 'Netherlands',
    'Spain', 'Italy', 'United Kingdom', 'Poland', 'Switzerland',
    # ... (31 countries total)
}

region = 'Europe' if country in EUROPE_COUNTRIES_EN else 'Rest of World'
```

### 3. YTD Date Range
```python
def get_ytd_date_range():
    return '2024-10-01', '2025-10-31'  # Oct 2024 - Oct 2025
```

### 4. Price Floors by Fruit
```python
FRUIT_PRICE_FLOORS = {
    'mango': 1500,      # $1,500/MT
    'avocado': 2000,    # $2,000/MT
    'blueberry': 1800,  # $1,800/MT
    'pineapple': 800,   # $800/MT
    'default': 500      # $500/MT
}
```

### 5. IQR Outlier Detection
```python
# Per-fruit statistical bounds
q1 = 25th percentile
q3 = 75th percentile
iqr = q3 - q1
valid_range = [q1 - 1.5×iqr, q3 + 1.5×iqr]
```

### 6. Company Name Cleaning
```python
# Normalization steps:
1. Fix encoding (NATURE?S → NATURE'S)
2. Remove accents (VIRÚ → VIRU)
3. Strip legal suffixes (S.A., LLC, GmbH)
4. Remove stop words (SOCIEDAD, GRUPO, AGRICOLA)
5. Remove addresses (PO Box, street names)
6. Normalize whitespace
```

---

## QUESTIONS & CLARIFICATIONS NEEDED

### Resolved
✅ **Q**: What's the source of the export data?
   **A**: Veritrade (commercial customs data platform), manual downloads

✅ **Q**: How is data quality ensured?
   **A**: 5-stage filter cascade (75.4% retention)

✅ **Q**: How are company names normalized?
   **A**: vt-normalize library with fuzzy clustering (59.3% reduction for importers)

✅ **Q**: What pricing methodology is used?
   **A**: Quartile-based (Q1/Median/Q3) to avoid outlier distortion

✅ **Q**: What's the difference between fruit formats?
   **A**: chunks, cubes, slices, halves, puree, pulp, whole, strips (11 types)

### Open Questions
None at this time - comprehensive exploration completed

---

## NEXT STEPS / POTENTIAL FOLLOW-UPS

### If Continuing This Work:

1. **Data Quality Improvements**:
   - Improve format detection (currently 91.3%, could reach 95%+)
   - Enhance certification extraction (currently 32.4%, target 50%+)
   - Add more variety detection patterns (especially for blueberries, pineapples)

2. **Analytics Enhancements**:
   - Add time-series analysis (seasonality, trends)
   - Implement exporter portfolio diversity metrics
   - Create importer competition analysis
   - Add FOB vs CIF pricing comparison (if CIF data available)

3. **Visualization Improvements**:
   - Interactive Sankey diagrams (D3.js instead of Mermaid)
   - Price trend charts (Plotly/Matplotlib)
   - Market share evolution over time
   - Geographic heat maps

4. **Data Pipeline Optimizations**:
   - Automate Veritrade downloads (if API available)
   - Add incremental updates (append new data instead of full reload)
   - Implement change detection (track price movements, new exporters)
   - Add data versioning (track historical changes)

5. **API/Interface Enhancements**:
   - RESTful API (FastAPI) for web applications
   - GraphQL endpoint for flexible queries
   - Excel export templates for business users
   - PowerBI/Tableau connectors

6. **Testing & Validation**:
   - Unit tests for parser.py (test all 24 fruit patterns)
   - Integration tests for filter pipeline
   - Data validation regression tests
   - Performance benchmarks (query optimization)

---

## DELIVERABLES FROM THIS SESSION

### Created Files

1. **`/home/andresublime/apps/frz_fruit/DATA_STRUCTURE.md`** ✅
   - Comprehensive data lineage documentation
   - 8 sections, ~1,400 lines
   - Optimized for AI architectural review
   - Complete with code snippets and line numbers

2. **`/home/andresublime/apps/frz_fruit/SESSION_CONTEXT.md`** ✅ (this file)
   - Complete context dump for session continuity
   - All exploration findings
   - Critical file map
   - Key insights and patterns

3. **`/home/andresublime/.claude/plans/vast-sprouting-graham.md`** ✅
   - Implementation plan for DATA_STRUCTURE.md
   - Detailed section breakdown
   - Success criteria

### Knowledge Captured

- ✅ Complete understanding of 6-stage data pipeline
- ✅ Schema evolution from 33 → 49 columns
- ✅ NLP parser logic (24 fruits, 11 formats)
- ✅ Quality filtering methodology (5-stage cascade)
- ✅ Company name clustering approach (vt-normalize)
- ✅ Quartile pricing methodology
- ✅ Database structure (tables, views, indexes)
- ✅ File organization and module responsibilities

---

## HOW TO RESUME THIS WORK

### Quick Start

1. **Review this file**: `SESSION_CONTEXT.md` - Get oriented on what was accomplished

2. **Review deliverable**: `DATA_STRUCTURE.md` - See the final output

3. **Access plan**: `/home/andresublime/.claude/plans/vast-sprouting-graham.md` - Original implementation plan

### Reference Materials

**For Data Pipeline Questions**:
- See "Data Pipeline Architecture" section above
- Read `DATA_STRUCTURE.md` Section 3: "Data Life Cycle"

**For Schema Questions**:
- See "Critical Files Map" section above
- Read `models.py` for Pydantic schemas
- Check `create_database.py` lines 82-205 for database schema

**For Quality Filtering Questions**:
- See "Key Code Snippets" section above
- Read `core/filters.py` lines 288-365
- Check "Data Quality" section for statistics

**For Analytics Questions**:
- Read `analysis/pricing.py` lines 33-245
- See "Quartile Pricing" code snippet above

### Key Commands

```bash
# Navigate to project
cd /home/andresublime/apps/frz_fruit/Export-Data

# Run enrichment pipeline
python enrich_data.py

# Create database
python create_database.py

# Cluster company names
python cluster_company_names.py

# CLI queries
python cli/main.py summary fruit --region Europe
python cli/main.py drill mango --by exporter --filter-dimension fruit

# Start MCP server
python start_mcp_server.py
```

---

## TECHNICAL NOTES

### Environment
- **Working Directory**: `/home/andresublime/apps/frz_fruit`
- **Python Package Manager**: `uv`
- **Database**: SQLite 3.x
- **Dependencies**: pandas, pydantic, fuzzywuzzy, fastmcp, openpyxl

### Git Status (Start of Session)
```
Current branch: Coherence
Main branch: Coherence

Modified files:
- Export-Data/analysis/pricing.py
- Export-Data/cli/main.py
- Export-Data/generate_germany_sankey.py
- Export-Data/sankey.py
- Multiple .mmd and .png files

Untracked files:
- Export-Data/cli/gui.py (new)
- Various .mmd and .png test files
```

### Recent Commits
```
6f09667 Convert Sankey diagrams to high-resolution PNG images
8accf4a Update database with vt-normalize canonical names
0846c65 Integrate vt-normalize for automated company name clustering
4bcecad Add European market analysis and visualization tools
2d29306 Backup
```

---

## CONVERSATION HIGHLIGHTS

### User Request
> "Analyze this entire project with a focus on 'Data Lineage.' Identify every file that interacts with data—including database models, API integrations, data schemas, utility functions for data cleaning, and state management. Create a single Markdown file named DATA_STRUCTURE.md..."

### Approach Taken
1. **Phase 1**: Launched 3 parallel Explore agents for comprehensive codebase exploration
2. **Phase 2**: Designed implementation plan with Plan agent
3. **Phase 3**: Read all 15 critical files for accurate line numbers and code snippets
4. **Phase 4**: Created comprehensive DATA_STRUCTURE.md (8 sections, ~1,400 lines)
5. **Phase 5**: Created this SESSION_CONTEXT.md for session continuity

### Key Decisions
- ✅ Used parallel exploration for efficiency (3 agents simultaneously)
- ✅ Read actual files instead of relying on exploration summaries
- ✅ Included exact line numbers for all code references
- ✅ Added real code snippets with examples
- ✅ Focused on data lineage (not general project documentation)
- ✅ Optimized for AI consumption (clear hierarchy, scannable structure)

---

## END OF CONTEXT DUMP

**Total Exploration Time**: ~3 agent invocations + 15 file reads
**Total Files Analyzed**: 15 critical files
**Total Lines of Documentation Created**: ~2,500 lines (DATA_STRUCTURE.md + SESSION_CONTEXT.md)
**Session Status**: ✅ COMPLETE

**To Resume**: Read this file top-to-bottom, then review `DATA_STRUCTURE.md`

**Last Updated**: 2026-01-06

---

## APPENDIX: FILE QUICK REFERENCE

**Data Files**:
- Raw: `peru_frozen_fruit_exports.csv.gz` (33 cols)
- Enriched: `peru_frozen_fruit_exports_enriched.csv.gz` (46 cols)
- Database: `exports.db` (49 cols)
- Clustered: `data/clustered_exporters.json`, `data/clustered_importers.json`

**Schema**:
- `models.py` - Pydantic models
- `parser.py` - NLP extraction

**Pipeline**:
- `enrich_data.py` - Main enrichment
- `create_database.py` - Database creation
- `cluster_company_names.py` - Name clustering

**Core**:
- `core/database.py` - Connections
- `core/filters.py` - Quality filters
- `core/exporter_mapping.py` - Exporter names
- `core/importer_mapping.py` - Importer names

**Analytics**:
- `analysis/pricing.py` - Quartiles
- `sankey.py` - Visualizations

**Interfaces**:
- `cli/main.py` - CLI
- `mcp_tools/server.py` - MCP

**Documentation**:
- `DATA_STRUCTURE.md` - Data lineage (THIS SESSION'S OUTPUT)
- `SESSION_CONTEXT.md` - Context dump (THIS FILE)
