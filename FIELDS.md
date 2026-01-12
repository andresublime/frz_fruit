# FIELDS.md
# Peru Frozen Fruit Export Analysis - Complete Field Reference

**Purpose**: Comprehensive documentation of every field from input through all transformation stages
**Generated**: 2026-01-07
**Pipeline**: Raw CSV (33 cols) → Enriched CSV (46 cols) → SQLite Database (49 cols) → Analytics

---

## TABLE OF CONTENTS

1. [Overview](#overview)
2. [Original Fields (33 columns)](#original-fields-33-columns)
3. [Enriched Fields (13 added)](#enriched-fields-13-added)
4. [Database-Only Fields (3 added)](#database-only-fields-3-added)
5. [Analytics Fields (Derived)](#analytics-fields-derived)
6. [Field Transformation Map](#field-transformation-map)

---

## OVERVIEW

### Pipeline Summary

```
Stage 1: Raw CSV (Veritrade Export)
├─ 33 original columns
├─ Source: Veritrade customs export declarations
└─ Format: peru_frozen_fruit_exports.csv.gz

Stage 2: NLP Enrichment (parser.py + enrich_data.py)
├─ +8 structured product fields (fruit_name, variety, format_type, size_mm, etc.)
├─ +2 computed metrics (net_weight_mt, usd_per_mt_fob)
└─ Output: peru_frozen_fruit_exports_enriched.csv.gz (46 columns)

Stage 3: Database Loading (create_database.py)
├─ +2 translation fields (destination_country_en, region)
├─ +2 canonical name fields (canonical_exporter, canonical_importer)
├─ +1 quality flag (analysis_valid)
└─ Output: exports.db (49 columns)

Stage 4: Analytics (pricing.py, filters.py)
├─ Quality filtering (75.4% retention)
├─ Quartile calculations (Q1, Median, Q3)
└─ Output: Pricing summaries and drill-downs
```

### Key Metrics
- **Records**: 14,279 export shipments (Jan 2024 - Oct 2025)
- **Data Quality**: 75.4% retention after filtering (10,762 valid records)
- **Company Normalization**: 152→146 exporters, 1,423→579 importers
- **Fruits Tracked**: 24 types (mango, avocado, blueberry, pineapple, etc.)
- **Destinations**: 57 countries

---

## ORIGINAL FIELDS (33 columns)

These fields come directly from Veritrade export data without modification.

### 1. HTS Code
**Column Name**: `HTS Code`
**Type**: TEXT (String)
**Purpose**: Harmonized Tariff System classification code for export products
**Sample Values**:
- `0811909000` (Frozen fruits, nesoi)
- `0811100000` (Frozen strawberries)

**Stages**:
- **Raw CSV**: Present, unchanged
- **Enriched CSV**: Present, unchanged
- **Database**: Present, unchanged
- **Analytics**: Not used (product classification done via NLP)

**Modifications**: None

---

### 2. HTS Code Description
**Column Name**: `HTS Code Description`
**Type**: TEXT (String)
**Purpose**: Human-readable description of HTS code
**Sample Values**:
- `FROZEN FRUITS`
- `FROZEN STRAWBERRIES`

**Stages**:
- **Raw CSV**: Present, unchanged
- **Enriched CSV**: Present, unchanged
- **Database**: Present, unchanged
- **Analytics**: Not used

**Modifications**: None

---

### 3. Customs
**Column Name**: `Customs`
**Type**: TEXT (String)
**Purpose**: Peruvian customs office handling the export
**Sample Values**:
- `MARITIMA DEL CALLAO`
- `AEROPUERTO DEL CALLAO`
- `PAITA`

**Stages**:
- **Raw CSV**: Present, unchanged
- **Enriched CSV**: Present, unchanged
- **Database**: Present, unchanged
- **Analytics**: Not used directly

**Modifications**: None

---

### 4. DUA / DAM
**Column Name**: `DUA / DAM`
**Type**: TEXT (String)
**Purpose**: Customs document number (Declaración Única de Aduanas / Declaración Aduanera de Mercancías)
**Sample Values**:
- `125-2024-10-12345`
- `126-2025-03-67890`

**Stages**:
- **Raw CSV**: Present, unchanged
- **Enriched CSV**: Present, unchanged
- **Database**: Present, unchanged
- **Analytics**: Not used (serves as unique shipment ID)

**Modifications**: None

---

### 5. Date
**Column Name**: `Date`
**Type**: DATETIME
**Purpose**: Export shipment date
**Sample Values**:
- `2024-01-08`
- `2025-10-30`

**Stages**:
- **Raw CSV**: Present as string (ISO format)
- **Enriched CSV**: Converted to datetime object
- **Database**: Stored as TEXT in ISO format, indexed for time-series queries
- **Analytics**:
  - Used for YTD filtering (Oct 2024 - Oct 2025)
  - Used in monthly_exports view for seasonality
  - Filter: `Date >= '2024-10-01' AND Date <= '2025-10-31'` in v_clean_exports

**Modifications**:
- **enrich_data.py**: String → datetime parsing
- **create_database.py**: datetime → ISO string for SQLite
- **Index**: `idx_date` created for performance

**Date Range**: 2024-01-08 to 2025-10-30 (661 days)

---

### 6. Tax ID
**Column Name**: `Tax ID`
**Type**: INTEGER
**Purpose**: Peruvian tax identification number (RUC) of exporter
**Sample Values**:
- `20123456789`
- `20987654321`

**Stages**:
- **Raw CSV**: Present, unchanged
- **Enriched CSV**: Present, unchanged
- **Database**: Present, unchanged
- **Analytics**: Not used (company identity tracked via Exporter name)

**Modifications**: None

---

### 7. Exporter
**Column Name**: `Exporter`
**Type**: TEXT (String)
**Purpose**: Name of exporting company (raw, unnormalized)
**Sample Values**:
- `VIRÚ GROUP PERÚ S.A.`
- `CAMPOSOL S.A.`
- `SUNSHINE EXPORT S.A.C`
- `MEBOL GF S.A.C.`

**Stages**:
- **Raw CSV**: Present, original format with legal suffixes
- **Enriched CSV**: Present, unchanged (original preserved)
- **Database**:
  - Original preserved
  - **NEW FIELD CREATED**: `canonical_exporter` (normalized version)
  - Indexed: `idx_exporter`, `idx_canonical_exporter`
- **Analytics**:
  - Canonical version used for aggregation
  - Original used for display/drill-down

**Modifications**:
- **create_database.py** (lines 62-64):
  ```python
  df['canonical_exporter'] = df['Exporter'].apply(
      lambda x: get_canonical_name(x) if pd.notna(x) else None
  )
  ```

**Normalization Process** (see canonical_exporter):
1. Fix UTF-8 corruption: `NATURE?S` → `NATURE'S`
2. Remove accents: `VIRÚ` → `VIRU`
3. Strip legal suffixes: `S.A.`, `S.A.C.`, `LLC`, etc.
4. Remove stop words: `GRUPO`, `SOCIEDAD`, `AGRICOLA`
5. Fuzzy matching (85-95% similarity)

**Results**: 152 unique raw names → 146 canonical names (3.9% reduction)

---

### 8. Importer
**Column Name**: `Importer`
**Type**: TEXT (String, Optional)
**Purpose**: Name of importing company (raw, unnormalized)
**Sample Values**:
- `SALUD FOODGROUP EUROPE B.V.`
- `NATURE'S TOUCH FROZEN FOODS`
- `DOLE FRUIT COMPANY`
- `SYSCO CORPORATION`

**Stages**:
- **Raw CSV**: Present, original format
- **Enriched CSV**: Present, unchanged
- **Database**:
  - Original preserved
  - **NEW FIELD CREATED**: `canonical_importer` (normalized version)
  - Indexed: `idx_canonical_importer`
- **Analytics**: Canonical version used for aggregation

**Modifications**:
- **create_database.py** (lines 65-67):
  ```python
  df['canonical_importer'] = df['Importer'].apply(
      lambda x: get_canonical_importer(x) if pd.notna(x) else None
  )
  ```

**Normalization Process**: Same as Exporter (see canonical_importer)

**Results**: 1,423 unique raw names → 579 canonical names (59.3% reduction)

**Note**: May be NULL for some records (confidential or unknown)

---

### 9. Gross kg
**Column Name**: `Gross kg`
**Type**: REAL (Float, Optional)
**Purpose**: Gross weight in kilograms (including packaging)
**Sample Values**:
- `18,500.0`
- `22,340.5`
- `15,200.0`

**Stages**:
- **Raw CSV**: Present
- **Enriched CSV**: Present, unchanged
- **Database**: Present, unchanged
- **Analytics**: Not used (net weight preferred)

**Modifications**: None

**Relationship**: Gross kg > Net kg (includes packaging weight)

---

### 10. Net kg
**Column Name**: `Net kg`
**Type**: REAL (Float, Optional)
**Purpose**: Net weight in kilograms (product only, excluding packaging)
**Sample Values**:
- `18,000.0`
- `21,600.0`
- `14,850.5`

**Stages**:
- **Raw CSV**: Present
- **Enriched CSV**:
  - Present, unchanged
  - **TRIGGERS COMPUTATION**: Used to calculate `net_weight_mt`
- **Database**: Present, unchanged
- **Analytics**:
  - Used indirectly via `net_weight_mt`
  - Quality filter: Records with Net kg = 0 or NULL flagged as invalid

**Modifications**:
- **enrich_data.py** (lines 177-180):
  ```python
  net_kg = row.get('Net kg', 0) or 0
  net_mt = round(net_kg / 1000, 3) if net_kg else 0
  enriched_row['net_weight_mt'] = net_mt
  ```

**Conversion**: Net kg ÷ 1000 = net_weight_mt

**Quality Checks**:
- **filters.py** (line 116): Sample detection if < 10 kg
- **filters.py** (line 143): Invalid if NULL or 0

---

### 11. Qty 1
**Column Name**: `Qty 1`
**Type**: REAL (Float, Optional)
**Purpose**: Primary quantity in Unit 1 measurement
**Sample Values**:
- `900.0` (when Unit 1 = "CAJAS" = boxes)
- `1,800.0` (when Unit 1 = "KG")

**Stages**:
- **Raw CSV**: Present
- **Enriched CSV**: Present, unchanged
- **Database**: Present, unchanged
- **Analytics**: Not used (analysis based on net_weight_mt)

**Modifications**: None

**Relationship**: Qty 1 measured in Unit 1

---

### 12. Unit 1
**Column Name**: `Unit 1`
**Type**: TEXT (String, Optional)
**Purpose**: Unit of measurement for Qty 1
**Sample Values**:
- `CAJAS` (boxes)
- `KG` (kilograms)
- `UNIDADES` (units)

**Stages**:
- **Raw CSV**: Present
- **Enriched CSV**: Present, unchanged
- **Database**: Present, unchanged
- **Analytics**: Not used

**Modifications**: None

---

### 13. Qty 2
**Column Name**: `Qty 2`
**Type**: REAL (Float, Optional)
**Purpose**: Secondary quantity in Unit 2 measurement
**Sample Values**:
- `18,000.0` (when Unit 2 = "KG")
- `900.0` (when Unit 2 = "BOLSAS" = bags)

**Stages**:
- **Raw CSV**: Present
- **Enriched CSV**: Present, unchanged
- **Database**: Present, unchanged
- **Analytics**: Not used

**Modifications**: None

**Relationship**: Qty 2 measured in Unit 2

---

### 14. Unit 2
**Column Name**: `Unit 2`
**Type**: TEXT (String, Optional)
**Purpose**: Unit of measurement for Qty 2
**Sample Values**:
- `KG` (kilograms)
- `BOLSAS` (bags)
- `UNIDADES` (units)

**Stages**:
- **Raw CSV**: Present
- **Enriched CSV**: Present, unchanged
- **Database**: Present, unchanged
- **Analytics**: Not used

**Modifications**: None

---

### 15. U$ FOB Tot
**Column Name**: `U$ FOB Tot`
**Type**: REAL (Float, Optional)
**Purpose**: Total FOB (Free On Board) value in US Dollars
**Sample Values**:
- `47,250.00`
- `52,800.00`
- `35,640.00`

**Stages**:
- **Raw CSV**: Present
- **Enriched CSV**:
  - Present, unchanged
  - **TRIGGERS COMPUTATION**: Used to calculate `usd_per_mt_fob`
- **Database**: Present, unchanged
- **Analytics**:
  - Used to calculate pricing metrics
  - Used in quartile calculations
  - Aggregated in views (SUM for total FOB)

**Modifications**:
- **enrich_data.py** (lines 178-181):
  ```python
  fob_total = row.get('U$ FOB Tot', 0) or 0
  usd_per_mt = round(fob_total / net_mt, 2) if net_mt > 0 else 0
  enriched_row['usd_per_mt_fob'] = usd_per_mt
  ```

**Conversion**: U$ FOB Tot ÷ net_weight_mt = usd_per_mt_fob

**Quality Checks**:
- **filters.py** (line 121): Sample detection if < $10
- **enrich_data.py** (lines 42-50): Warning if missing (>5% threshold)

---

### 16. U$ FOB Unit 1
**Column Name**: `U$ FOB Unit 1`
**Type**: REAL (Float, Optional)
**Purpose**: FOB price per Unit 1
**Sample Values**:
- `52.50` (USD per box)
- `2.92` (USD per kg)

**Stages**:
- **Raw CSV**: Present
- **Enriched CSV**: Present, unchanged
- **Database**: Present, unchanged
- **Analytics**: Not used (usd_per_mt_fob preferred)

**Modifications**: None

**Calculation**: U$ FOB Tot ÷ Qty 1

---

### 17. U$ FOB Unit 2
**Column Name**: `U$ FOB Unit 2`
**Type**: REAL (Float, Optional)
**Purpose**: FOB price per Unit 2
**Sample Values**:
- `2.92` (USD per kg)
- `58.40` (USD per bag)

**Stages**:
- **Raw CSV**: Present
- **Enriched CSV**: Present, unchanged
- **Database**: Present, unchanged
- **Analytics**: Not used

**Modifications**: None

**Calculation**: U$ FOB Tot ÷ Qty 2

---

### 18. Destination Country
**Column Name**: `Destination Country`
**Type**: TEXT (String, Optional)
**Purpose**: Destination country name in SPANISH
**Sample Values**:
- `ALEMANIA` (Germany)
- `PAÍSES BAJOS` (Netherlands)
- `ESTADOS UNIDOS` (United States)
- `REINO UNIDO` (United Kingdom)

**Stages**:
- **Raw CSV**: Present, Spanish names
- **Enriched CSV**: Present, unchanged
- **Database**:
  - Original Spanish name preserved
  - **NEW FIELD CREATED**: `destination_country_en` (English translation)
  - **NEW FIELD CREATED**: `region` (Europe vs Rest of World)
  - Indexed: `idx_destination`
- **Analytics**: English version used for user-facing reports

**Modifications**:
- **create_database.py** (lines 46-48):
  ```python
  df['destination_country_en'] = df['Destination Country'].apply(
      lambda x: translate_country_to_english(str(x)) if pd.notna(x) else x
  )
  ```

**Translation Dictionary** (translations.py, 80+ mappings):
- `'ALEMANIA'` → `'Germany'`
- `'PAÍSES BAJOS'` → `'Netherlands'`
- `'REINO UNIDO'` → `'United Kingdom'`
- `'ESTADOS UNIDOS'` → `'United States'`

**Usage**: See destination_country_en for full details

---

### 19. Destination Port
**Column Name**: `Destination Port`
**Type**: TEXT (String, Optional)
**Purpose**: Port of arrival in destination country
**Sample Values**:
- `ROTTERDAM`
- `HAMBURG`
- `LONG BEACH`
- `ANTWERP`

**Stages**:
- **Raw CSV**: Present
- **Enriched CSV**: Present, unchanged
- **Database**: Present, unchanged
- **Analytics**: Not used

**Modifications**: None

---

### 20. Last Port
**Column Name**: `Last Port`
**Type**: TEXT (String, Optional)
**Purpose**: Last port before destination (transshipment point)
**Sample Values**:
- `CALLAO` (Peru)
- `PANAMA`
- `CARTAGENA`

**Stages**:
- **Raw CSV**: Present
- **Enriched CSV**: Present, unchanged
- **Database**: Present, unchanged
- **Analytics**: Not used

**Modifications**: None

---

### 21. Via
**Column Name**: `Via`
**Type**: TEXT (String, Optional)
**Purpose**: Shipping method (maritime, air, land)
**Sample Values**:
- `MARÍTIMO` (sea freight)
- `AÉREO` (air freight)
- `TERRESTRE` (land)

**Stages**:
- **Raw CSV**: Present
- **Enriched CSV**: Present, unchanged
- **Database**: Present, unchanged
- **Analytics**:
  - **CRITICAL FILTER**: Used to exclude air freight shipments
  - Air shipments have inflated pricing, excluded from analysis

**Modifications**: None

**Quality Filter** (filters.py, lines 68-88):
```python
def is_air_shipment(row: pd.Series) -> bool:
    via = row.get('Via', '')
    if pd.isna(via):
        return False
    via_upper = str(via).upper()
    return any(method in via_upper for method in ['AÉREO', 'AEREO', 'AIR'])
```

**Impact**: Air shipments flagged as invalid (analysis_valid = 0)

---

### 22. Port Agent
**Column Name**: `Port Agent`
**Type**: TEXT (String, Optional)
**Purpose**: Port handling agent company
**Sample Values**:
- `TRABAJOS MARITIMOS S.A.`
- `NEPTUNIA S.A.`

**Stages**:
- **Raw CSV**: Present
- **Enriched CSV**: Present, unchanged
- **Database**: Present, unchanged
- **Analytics**: Not used

**Modifications**: None

---

### 23. Customs Agent
**Column Name**: `Customs Agent`
**Type**: TEXT (String, Optional)
**Purpose**: Customs broker handling documentation
**Sample Values**:
- `NEPTUNIA S.A.`
- `AGUNSA AGENCIA EN ADUANA S.A.`

**Stages**:
- **Raw CSV**: Present
- **Enriched CSV**: Present, unchanged
- **Database**: Present, unchanged
- **Analytics**: Not used

**Modifications**: None

---

### 24. Shipping Line
**Column Name**: `Shipping Line`
**Type**: TEXT (String, Optional)
**Purpose**: Shipping company/carrier
**Sample Values**:
- `MAERSK LINE`
- `MSC`
- `HAPAG-LLOYD`
- `CMA CGM`

**Stages**:
- **Raw CSV**: Present
- **Enriched CSV**: Present, unchanged
- **Database**: Present, unchanged
- **Analytics**: Not used

**Modifications**: None

---

### 25. Forwarding Agent (Origin)
**Column Name**: `Forwarding Agent(Origin)`
**Type**: TEXT (String, Optional)
**Purpose**: Freight forwarder in Peru (origin)
**Sample Values**:
- `KUEHNE + NAGEL`
- `DHL GLOBAL FORWARDING`

**Stages**:
- **Raw CSV**: Present
- **Enriched CSV**: Present, unchanged
- **Database**: Present, unchanged
- **Analytics**: Not used

**Modifications**: None

---

### 26. Forwarding Agent (Destination)
**Column Name**: `Forwarding Agent(Destination)`
**Type**: TEXT (String, Optional)
**Purpose**: Freight forwarder in destination country
**Sample Values**:
- `KUEHNE + NAGEL`
- `SCHENKER`

**Stages**:
- **Raw CSV**: Present
- **Enriched CSV**: Present, unchanged
- **Database**: Present, unchanged
- **Analytics**: Not used

**Modifications**: None

---

### 27. Channel
**Column Name**: `Channel`
**Type**: TEXT (String, Optional)
**Purpose**: Customs inspection channel (red, yellow, green)
**Sample Values**:
- `VERDE` (green - no inspection)
- `NARANJA` (orange - document review)
- `ROJO` (red - physical inspection)

**Stages**:
- **Raw CSV**: Present
- **Enriched CSV**: Present, unchanged
- **Database**: Present, unchanged
- **Analytics**: Not used

**Modifications**: None

---

### 28. Commercial Description
**Column Name**: `Commercial Description`
**Type**: TEXT (String)
**Purpose**: Free-text product description (Spanish/English mix)
**Sample Values**:
- `MANGO CONGELADO ORGANICO CHUNKS 20X20MM IQF VARIEDAD: EDWARD`
- `FROZEN PINEAPPLE GOLDEN CHUNKS 20X20 IQF`
- `BLUEBERRY FROZEN WHOLE CONVENTIONAL IQF`
- `AVOCADO PULP FROZEN ORGANIC`

**Stages**:
- **Raw CSV**: Present, raw text
- **Enriched CSV**:
  - Present, unchanged (original preserved)
  - **TRIGGERS NLP PARSING**: Entire enrichment process
  - Parsed to extract 8 structured fields
- **Database**: Present, unchanged (original preserved)
- **Analytics**:
  - **CRITICAL FILTER**: Used to detect sample shipments
  - Keywords: MUESTRA, SIN VALOR, SAMPLE, TEST

**Modifications**: None to original field, but triggers creation of:
1. `fruit_name` - Extracted via regex (24 fruit patterns)
2. `variety` - Extracted via regex (Kent, Edward, Haden, etc.)
3. `format_type` - Extracted via regex (chunks, cubes, slices, etc.)
4. `size_mm` - Extracted via regex (20x20, 10x10, etc.)
5. `is_organic` - Boolean flag
6. `is_conventional` - Boolean flag
7. `is_iqf` - Boolean flag
8. `certification` - Derived from flags

**NLP Parsing** (parser.py, lines 74-122):

**Step 1: Normalize Text**
```python
desc_lower = description.lower()
# "MANGO CONGELADO..." → "mango congelado..."
```

**Step 2: Extract Fruit** (24 patterns)
```python
FRUIT_PATTERNS = {
    'mango': r'\bmango[s]?(?:\b|(?=[A-Z]))',
    'pineapple': r'\b(pineapple|piña|pina|ananas)\b',
    'blueberry': r'\b(blueberry|arandano[s]?|arándano[s]?)\b',
    'avocado': r'\b(avocado[s]?|aguacate[s]?|palta[s]?)\b',
    ...
}
# Match: "mango" → fruit_name = "mango"
```

**Step 3: Extract Variety**
```python
VARIETY_PATTERNS = [
    r'(?:variedad|variety|var)[:\s]+([a-z]+)',  # "VARIEDAD: EDWARD"
    r'\b(kent|edward|haden|keitt|tommy atkins|ataulfo)\b',
]
# Match: "VARIEDAD: EDWARD" → variety = "Edward"
```

**Step 4: Extract Format** (11 patterns)
```python
FORMAT_PATTERNS = {
    'chunks': r'\b(chunk[s]?|trozo[s]?|pedazo[s]?)\b',
    'cubes': r'\b(cube[s]?|cubo[s]?|dado[s]?|diced)\b',
    'slices': r'\b(slice[s]?|sliced|rebanada[s]?)\b',
    'puree': r'\b(puree|pure|puré)\b',
    ...
}
# Match: "CHUNKS" → format_type = "chunks"
```

**Step 5: Extract Size**
```python
SIZE_PATTERNS = [
    r'(\d+)\s*[xX×]\s*(\d+)\s*(?:mm)?',  # 20x20mm, 20X20
]
# Match: "20X20MM" → size_mm = "20x20"
```

**Step 6: Extract Classification**
```python
ORGANIC_PATTERNS = r'\b(organic|organico|org)\b'
IQF_PATTERNS = r'\biqf\b'
# Match: "ORGANICO" → is_organic = True
# Match: "IQF" → is_iqf = True
# Derive: certification = "organic"
```

**Parsing Success Rates**:
- Fruit identification: 99.7%
- Format identification: 91.3%
- Certification identification: 32.4%

**Quality Filter** (filters.py, lines 107-112):
```python
SAMPLE_KEYWORDS = [
    'MUESTRA', 'SIN VALOR COMERCIAL', 'ENVIO DE MUESTRAS',
    'SAMPLE', 'NO COMMERCIAL VALUE', 'TEST SHIPMENT', 'TRIAL'
]
# If ANY keyword found → is_sample_shipment() returns True
```

---

### 29-33. Description1, Description2, Description3, Description4, Description5
**Column Names**: `Description1`, `Description2`, `Description3`, `Description4`, `Description5`
**Type**: TEXT (String, Optional)
**Purpose**: Additional product description fields (mostly unused in this dataset)
**Sample Values**: Usually NULL or empty

**Stages**:
- **Raw CSV**: Present
- **Enriched CSV**: Present, unchanged
- **Database**: Present, unchanged
- **Analytics**: Not used

**Modifications**: None

**Note**: These fields are part of the Veritrade standard format but rarely populated.

---

## ENRICHED FIELDS (13 added)

These fields are created during the enrichment process (enrich_data.py + parser.py).

### 34. fruit_name
**Column Name**: `fruit_name`
**Type**: TEXT (Literal - 24 options)
**Purpose**: Standardized fruit type extracted from Commercial Description
**Possible Values**:
- `"mango"`, `"pineapple"`, `"strawberry"`, `"blueberry"`, `"papaya"`, `"avocado"`
- `"pomegranate"`, `"lucuma"`, `"passion_fruit"`, `"golden_berry"`, `"camu_camu"`
- `"soursop"`, `"cherimoya"`, `"pitaya"`, `"acai"`, `"banana"`, `"raspberry"`
- `"cherry"`, `"peach"`, `"grape"`, `"orange"`, `"mix"`, `"other"`, `"unknown"`

**Sample Values**:
- `mango` (from "MANGO CONGELADO...")
- `pineapple` (from "FROZEN PINEAPPLE...")
- `blueberry` (from "BLUEBERRY FROZEN...")
- `unknown` (if no fruit pattern matched)

**Stages**:
- **Raw CSV**: Does not exist
- **Enriched CSV**:
  - **CREATED**: Extracted from Commercial Description via NLP
  - Source: parser.py lines 125-130
- **Database**:
  - Present
  - Indexed: `idx_fruit` for query performance
- **Analytics**:
  - **PRIMARY AGGREGATION DIMENSION**
  - Used in quartile calculations
  - Used in quality filtering (fruit-specific price floors)
  - Used in IQR outlier detection (per-fruit bounds)

**Creation** (parser.py, lines 125-130):
```python
@classmethod
def _extract_fruit(cls, text: str) -> str:
    for fruit, pattern in cls.FRUIT_PATTERNS.items():
        if re.search(pattern, text, re.IGNORECASE):
            return fruit
    return "unknown"
```

**Extraction Patterns** (24 fruits):
```python
FRUIT_PATTERNS = {
    'mango': r'\bmango[s]?(?:\b|(?=[A-Z]))',
    'pineapple': r'\b(pineapple|piña|pina|ananas)\b',
    'blueberry': r'\b(blueberry|arandano[s]?|arándano[s]?)\b',
    'avocado': r'\b(avocado[s]?|aguacate[s]?|palta[s]?)\b',
    # ... 20 more patterns
}
```

**Success Rate**: 99.7% (0.3% remain as "unknown")

**Used In**:
- **filters.py**: Fruit-specific price floors (FRUIT_PRICE_FLOORS dict)
- **filters.py**: IQR outlier bounds calculated per fruit
- **pricing.py**: Primary aggregation dimension
- **create_database.py**: View aggregations (exporter_products, destination_products)

---

### 35. variety
**Column Name**: `variety`
**Type**: TEXT (String, Optional)
**Purpose**: Specific fruit variety/cultivar (e.g., Kent mango, MD2 pineapple)
**Sample Values**:
- `Kent` (mango)
- `Edward` (mango)
- `Haden` (mango)
- `Keitt` (mango)
- `Golden` (pineapple)
- `MD2` (pineapple)
- NULL (when not specified)

**Stages**:
- **Raw CSV**: Does not exist
- **Enriched CSV**:
  - **CREATED**: Extracted from Commercial Description via NLP
  - Source: parser.py lines 133-140
- **Database**: Present
- **Analytics**: Not used (too granular for current analysis)

**Creation** (parser.py, lines 133-140):
```python
@classmethod
def _extract_variety(cls, text: str) -> Optional[str]:
    for pattern in cls.VARIETY_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            variety = match.group(1).strip()
            return variety.title()  # Capitalize
    return None
```

**Extraction Patterns**:
```python
VARIETY_PATTERNS = [
    r'(?:variedad|variety|var)[:\s]+([a-z]+)',  # "VARIEDAD: EDWARD"
    r'\b(kent|edward|haden|keitt|tommy atkins|ataulfo)\b',  # Mango varieties
    r'\b(golden|md2|cayenne)\b',  # Pineapple varieties
]
```

**Identification Rate**: ~40% (most records don't specify variety)

**Future Use**: Could be used for variety-level pricing analysis

---

### 36. format_type
**Column Name**: `format_type`
**Type**: TEXT (Literal - 13 options)
**Purpose**: Product format/cut type extracted from Commercial Description
**Possible Values**:
- `"chunks"`, `"cubes"`, `"slices"`, `"halves"`, `"puree"`, `"pulp"`, `"whole"`
- `"strips"`, `"iqf"`, `"broken_pieces"`, `"concentrate"`, `"juice"`, `"unknown"`

**Sample Values**:
- `chunks` (from "CHUNKS 20X20")
- `cubes` (from "CUBOS" or "DICED")
- `puree` (from "PUREE" or "PURÉ")
- `whole` (from "WHOLE" or "ENTERO")
- `unknown` (if no format pattern matched)

**Stages**:
- **Raw CSV**: Does not exist
- **Enriched CSV**:
  - **CREATED**: Extracted from Commercial Description via NLP
  - Source: parser.py lines 143-175
- **Database**:
  - Present
  - Indexed: `idx_format` for query performance
- **Analytics**:
  - Used as drill-down dimension (when filtering by fruit)
  - NOT valid as standalone dimension (formats are fruit-specific)

**Creation** (parser.py, lines 143-175):
```python
@classmethod
def _extract_format(cls, text: str) -> ProductFormat:
    format_type = None

    # Check for specific formats
    for fmt, pattern in cls.FORMAT_PATTERNS.items():
        if re.search(pattern, text, re.IGNORECASE):
            format_type = fmt
            break

    # If format not found but size is present, assume chunks
    if not format_type and size_mm:
        format_type = "chunks"

    return ProductFormat(format_type=format_type or "unknown", ...)
```

**Extraction Patterns** (11 formats):
```python
FORMAT_PATTERNS = {
    'chunks': r'\b(chunk[s]?|trozo[s]?|pedazo[s]?|bits and pieces)\b',
    'cubes': r'\b(cube[s]?|cubo[s]?|dado[s]?|diced|picado[s]?)\b',
    'slices': r'\b(slice[s]?|sliced|rebanada[s]?|rodaja[s]?)\b',
    'halves': r'\b(halves|mitades)\b',
    'puree': r'\b(puree|pure|puré)\b',
    'pulp': r'\b(pulp|pulpa)\b',
    'whole': r'\b(whole|entero[s]?|entera[s]?)\b',
    'strips': r'\b(strip[s]?|tira[s]?)\b',
    'broken_pieces': r'\bb\s*&\s*p\b',  # "B&P" = broken & pieces
    'concentrate': r'\b(concentrate|concentrado)\b',
    'juice': r'\b(juice|jugo)\b',
}
```

**Success Rate**: 91.3% (8.7% remain as "unknown")

**Used In**:
- **pricing.py**: Drill-down dimension (e.g., "mango by format")
- **create_database.py**: View aggregations

**Important**: Format is NOT a standalone aggregation dimension because:
- "20x20 chunks" means different things for mango vs passion fruit
- Same format name ≠ same product across fruits
- Valid usage: Filter by fruit FIRST, then aggregate by format

---

### 37. size_mm
**Column Name**: `size_mm`
**Type**: TEXT (String, Optional)
**Purpose**: Standardized product size in millimeters
**Sample Values**:
- `20x20` (standardized from "20X20MM", "20x20mm", "20 x 20")
- `10x10` (standardized from "10X10", "10x10MM")
- `15x15`
- `25x25`
- NULL (when size not specified)

**Stages**:
- **Raw CSV**: Does not exist
- **Enriched CSV**:
  - **CREATED**: Extracted and standardized from Commercial Description
  - Source: parser.py lines 162-166
- **Database**:
  - Present
  - Indexed: `idx_size` for query performance
- **Analytics**: Used as aggregation dimension

**Creation** (parser.py, lines 162-166):
```python
# Extract size
for pattern in cls.SIZE_PATTERNS:
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        size_mm = f"{match.group(1)}x{match.group(2)}"
        break
```

**Extraction Patterns**:
```python
SIZE_PATTERNS = [
    r'(\d+)\s*[xX×]\s*(\d+)\s*(?:mm)?',  # 20x20mm, 20X20, 20 x 20
    r'(\d+)\s*mm\s*[xX×]\s*(\d+)\s*mm',  # 20mm x 20mm
]
```

**Standardization** (models.py, lines 21-30):
```python
@field_validator('size_mm', mode='before')
@classmethod
def standardize_size(cls, v):
    if v and isinstance(v, str):
        match = re.search(r'(\d+)\s*[xX]\s*(\d+)', v)
        if match:
            return f"{match.group(1)}x{match.group(2)}"
    return v
```

**Transformations**:
- `"20X20MM"` → `"20x20"`
- `"20 x 20"` → `"20x20"`
- `"20X20"` → `"20x20"`
- `"10 X 10 MM"` → `"10x10"`

**Identification Rate**: ~60% (many records don't specify size)

**Used In**:
- **create_database.py**: View aggregations (exporter_products, destination_products)
- **pricing.py**: Optional drill-down dimension

---

### 38. is_organic
**Column Name**: `is_organic`
**Type**: INTEGER (Boolean: 0 or 1)
**Purpose**: Flag indicating organic certification
**Sample Values**:
- `1` (True - organic)
- `0` (False - not organic or unknown)

**Stages**:
- **Raw CSV**: Does not exist
- **Enriched CSV**:
  - **CREATED**: Extracted from Commercial Description via keyword matching
  - Source: parser.py line 180
- **Database**: Present (stored as INTEGER for SQLite compatibility)
- **Analytics**: Used via `certification` field

**Creation** (parser.py, line 180):
```python
is_organic = bool(re.search(cls.ORGANIC_PATTERNS, text, re.IGNORECASE))
```

**Detection Pattern**:
```python
ORGANIC_PATTERNS = r'\b(organic|organico|org)\b'
```

**Matches**:
- `"MANGO ORGANICO"` → `is_organic = 1`
- `"ORGANIC BLUEBERRY"` → `is_organic = 1`
- `"ORG PINEAPPLE"` → `is_organic = 1`

**Detection Rate**: ~32% identified as organic

**Relationship**: Triggers `certification = "organic"` in certification field

---

### 39. is_conventional
**Column Name**: `is_conventional`
**Type**: INTEGER (Boolean: 0 or 1)
**Purpose**: Flag indicating conventional (non-organic) certification
**Sample Values**:
- `1` (True - conventional)
- `0` (False - not conventional or unknown)

**Stages**:
- **Raw CSV**: Does not exist
- **Enriched CSV**:
  - **CREATED**: Extracted from Commercial Description via keyword matching
  - Source: parser.py line 181
- **Database**: Present
- **Analytics**: Used via `certification` field

**Creation** (parser.py, line 181):
```python
is_conventional = bool(re.search(cls.CONVENTIONAL_PATTERNS, text, re.IGNORECASE))
```

**Detection Pattern**:
```python
CONVENTIONAL_PATTERNS = r'\b(conventional|convencional)\b'
```

**Detection Rate**: Very low (usually not explicitly stated)

**Relationship**: Triggers `certification = "conventional"` in certification field

---

### 40. is_iqf
**Column Name**: `is_iqf`
**Type**: INTEGER (Boolean: 0 or 1)
**Purpose**: Flag indicating IQF (Individually Quick Frozen) processing
**Sample Values**:
- `1` (True - IQF)
- `0` (False - not IQF or unknown)

**Stages**:
- **Raw CSV**: Does not exist
- **Enriched CSV**:
  - **CREATED**: Extracted from Commercial Description via keyword matching
  - Source: parser.py line 182
- **Database**: Present
- **Analytics**: Not used directly

**Creation** (parser.py, line 182):
```python
is_iqf = bool(re.search(cls.IQF_PATTERNS, text, re.IGNORECASE))
```

**Detection Pattern**:
```python
IQF_PATTERNS = r'\biqf\b'
```

**Matches**:
- `"MANGO IQF"` → `is_iqf = 1`
- `"FROZEN IQF BLUEBERRY"` → `is_iqf = 1`

**Detection Rate**: ~50% (very common in frozen fruit exports)

**Note**: IQF is a processing method, not a certification. Can be combined with organic or conventional.

---

### 41. is_aseptic
**Column Name**: `is_aseptic`
**Type**: INTEGER (Boolean: 0 or 1)
**Purpose**: Flag indicating aseptic processing (NOT frozen, shelf-stable)
**Sample Values**:
- `1` (True - aseptic)
- `0` (False - frozen or unknown)

**Stages**:
- **Raw CSV**: Does not exist
- **Enriched CSV**:
  - **CREATED**: Extracted from Commercial Description via keyword matching
  - Source: parser.py line 183
- **Database**: Present
- **Analytics**: Not used directly

**Creation** (parser.py, line 183):
```python
is_aseptic = bool(re.search(cls.ASEPTIC_PATTERNS, text, re.IGNORECASE))
```

**Detection Pattern**:
```python
ASEPTIC_PATTERNS = r'\b(aseptic|aseptico|aséptico)\b'
```

**Detection Rate**: Very low (~1%, most products are frozen not aseptic)

**Note**: Aseptic products should be analyzed separately from frozen products.

---

### 42. certification
**Column Name**: `certification`
**Type**: TEXT (Literal: "organic", "conventional", "unknown")
**Purpose**: Derived certification type from is_organic and is_conventional flags
**Sample Values**:
- `organic` (if is_organic = 1)
- `conventional` (if is_conventional = 1)
- `unknown` (if neither flag set)

**Stages**:
- **Raw CSV**: Does not exist
- **Enriched CSV**:
  - **CREATED**: Auto-derived from is_organic and is_conventional flags
  - Source: models.py lines 48-56
- **Database**:
  - Present
  - Indexed: `idx_certification` for query performance
- **Analytics**: Used as aggregation dimension

**Creation** (models.py, lines 48-56):
```python
@field_validator('certification', mode='after')
@classmethod
def determine_certification(cls, v, info):
    if info.data.get('is_organic'):
        return "organic"
    elif info.data.get('is_conventional'):
        return "conventional"
    return v or "unknown"
```

**Derivation Logic**:
```
IF is_organic = 1    → certification = "organic"
ELIF is_conventional = 1 → certification = "conventional"
ELSE                 → certification = "unknown"
```

**Distribution**:
- `organic`: ~32%
- `conventional`: ~1%
- `unknown`: ~67%

**Used In**:
- **create_database.py**: View aggregations (exporter_products, destination_products)
- **pricing.py**: Optional aggregation dimension

**Note**: "unknown" doesn't mean non-organic, just that certification wasn't stated in description.

---

### 43. net_weight_mt
**Column Name**: `net_weight_mt`
**Type**: REAL (Float)
**Purpose**: Net weight converted to metric tons for standardized analysis
**Sample Values**:
- `18.0` (from Net kg = 18,000)
- `21.6` (from Net kg = 21,600)
- `14.851` (from Net kg = 14,850.5)
- `0` (if Net kg is NULL or 0)

**Stages**:
- **Raw CSV**: Does not exist
- **Enriched CSV**:
  - **CREATED**: Calculated from Net kg
  - Source: enrich_data.py lines 177-180, models.py lines 143-146
- **Database**: Present
- **Analytics**:
  - **PRIMARY VOLUME METRIC**
  - Used for all volume aggregations
  - Used in quality filtering (< 0.1 MT flagged as invalid)

**Calculation** (enrich_data.py, lines 177-180):
```python
net_kg = row.get('Net kg', 0) or 0
net_mt = round(net_kg / 1000, 3) if net_kg else 0
enriched_row['net_weight_mt'] = net_mt
```

**Formula**: `net_weight_mt = Net kg ÷ 1000`

**Precision**: Rounded to 3 decimal places (1 kg precision)

**Quality Checks**:
- **filters.py** (line 143): Invalid if NULL or 0
- **filters.py** (line 146): Invalid if < 0.1 MT (100 kg minimum)
- **filters.py** (line 116): Sample if < 0.01 MT (10 kg)

**Used In**:
- **pricing.py**: Total MT calculations (YTD MT column)
- **create_database.py**: All view aggregations (SUM(net_weight_mt))
- **filters.py**: Shipment size validation

**Total Dataset**: 14,279 records, ~35,000 MT total

---

### 44. usd_per_mt_fob
**Column Name**: `usd_per_mt_fob`
**Type**: REAL (Float)
**Purpose**: Price per metric ton (USD FOB) for standardized pricing analysis
**Sample Values**:
- `2,625.00` (from $47,250 / 18 MT)
- `2,444.44` (from $52,800 / 21.6 MT)
- `2,400.00` (from $35,640 / 14.851 MT)
- `0` (if net_weight_mt = 0 or U$ FOB Tot = 0)

**Stages**:
- **Raw CSV**: Does not exist
- **Enriched CSV**:
  - **CREATED**: Calculated from U$ FOB Tot and net_weight_mt
  - Source: enrich_data.py lines 178-181, models.py lines 148-150
- **Database**: Present
- **Analytics**:
  - **PRIMARY PRICING METRIC**
  - Used for all pricing calculations
  - Used for quartile analysis (Q1, Median, Q3)
  - Used in quality filtering (price floors, IQR outliers)

**Calculation** (enrich_data.py, lines 178-181):
```python
fob_total = row.get('U$ FOB Tot', 0) or 0
usd_per_mt = round(fob_total / net_mt, 2) if net_mt > 0 else 0
enriched_row['usd_per_mt_fob'] = usd_per_mt
```

**Formula**: `usd_per_mt_fob = U$ FOB Tot ÷ net_weight_mt`

**Precision**: Rounded to 2 decimal places (cent precision)

**Quality Checks**:

**1. Zero/Missing Price** (enrich_data.py, lines 42-50):
```python
missing_prices = len(df[df['usd_per_mt_fob'] == 0])
if missing_prices_pct > 5.0:
    warnings.append(f"⚠️  {missing_prices_pct:.1f}% of records have zero/missing prices")
```

**2. Price Floors** (filters.py, lines 181-202):
```python
FRUIT_PRICE_FLOORS = {
    'mango': 1500,       # $1,500/MT minimum
    'avocado': 2000,     # $2,000/MT minimum
    'blueberry': 1800,   # $1,800/MT minimum
    'pineapple': 800,    # $800/MT minimum
    'default': 500       # $500/MT for unlisted fruits
}
# If price < floor → is_below_price_floor() = True → invalid
```

**3. IQR Outlier Detection** (filters.py, lines 205-243):
```python
# Per-fruit statistical outlier detection
# Q1 = 25th percentile price for fruit
# Q3 = 75th percentile price for fruit
# IQR = Q3 - Q1
# lower_bound = Q1 - 1.5 × IQR
# upper_bound = Q3 + 1.5 × IQR
# If price < lower_bound OR price > upper_bound → outlier → invalid
```

**Used In**:
- **pricing.py**: Quartile calculations (Q1, Median, Q3)
- **pricing.py**: Drill-down pricing analysis
- **filters.py**: Quality filtering (all 3 checks above)
- **create_database.py**: View aggregations (AVG, MIN, MAX)

**Price Range**: $500 to $10,000+ per MT (varies by fruit, format, certification)

**Typical Prices** (Mid$ from pricing.py):
- Mango: ~$2,650/MT
- Avocado: ~$3,400/MT
- Blueberry: ~$4,200/MT
- Pineapple: ~$1,200/MT

---

### 45-46. product (Nested Object - Not in Database)
**Column Name**: `product`
**Type**: FruitProduct (Pydantic nested model)
**Purpose**: Nested structured product information (used in enrichment, flattened for database)

**Note**: This is a nested object in the Pydantic model but is **flattened** into individual columns (fruit_name, variety, format_type, size_mm, etc.) when stored in CSV and database.

**Structure**:
```python
product = FruitProduct(
    fruit_name="mango",
    variety="Edward",
    product_format=ProductFormat(
        format_type="chunks",
        size_mm="20x20"
    ),
    classification=ProductClassification(
        is_organic=True,
        is_conventional=False,
        is_iqf=True,
        is_aseptic=False,
        certification="organic"
    )
)
```

**Storage**: Flattened into columns 34-42 above.

---

## DATABASE-ONLY FIELDS (3 added)

These fields are created when loading data into the SQLite database (create_database.py).

### 47. destination_country_en
**Column Name**: `destination_country_en`
**Type**: TEXT (String, Optional)
**Purpose**: English translation of Destination Country (Spanish → English)
**Sample Values**:
- `Germany` (from `ALEMANIA`)
- `Netherlands` (from `PAÍSES BAJOS`)
- `United States` (from `ESTADOS UNIDOS`)
- `United Kingdom` (from `REINO UNIDO`)

**Stages**:
- **Raw CSV**: Does not exist
- **Enriched CSV**: Does not exist
- **Database**:
  - **CREATED**: Translated from Destination Country during database load
  - Source: create_database.py lines 46-48
- **Analytics**: Used for user-facing reports (English speakers)

**Creation** (create_database.py, lines 46-48):
```python
df['destination_country_en'] = df['Destination Country'].apply(
    lambda x: translate_country_to_english(str(x)) if pd.notna(x) else x
)
```

**Translation Function** (translations.py, lines 97-107):
```python
def translate_country_to_english(spanish_name: str) -> str:
    return COUNTRY_TRANSLATIONS.get(spanish_name.upper(), spanish_name)
```

**Translation Dictionary** (translations.py, 80+ mappings):
```python
COUNTRY_TRANSLATIONS = {
    'ALEMANIA': 'Germany',
    'PAÍSES BAJOS': 'Netherlands',
    'REINO UNIDO': 'United Kingdom',
    'ESTADOS UNIDOS': 'United States',
    'BÉLGICA': 'Belgium',
    'FRANCIA': 'France',
    'ESPAÑA': 'Spain',
    'ITALIA': 'Italy',
    # ... 80+ total mappings
}
```

**Coverage**: All 57 destination countries have translations

**Fallback**: If country not in dictionary, returns original Spanish name unchanged

**Used In**:
- **create_database.py**: Region classification (Europe vs RoW)
- **create_database.py**: region_mapping table
- **Analytics**: User-facing reports and exports

---

### 48. region
**Column Name**: `region`
**Type**: TEXT (Literal: "Europe" or "Rest of World")
**Purpose**: Geographic region classification for market analysis
**Sample Values**:
- `Europe` (31 countries)
- `Rest of World` (26+ countries)

**Stages**:
- **Raw CSV**: Does not exist
- **Enriched CSV**: Does not exist
- **Database**:
  - **CREATED**: Derived from destination_country_en
  - Source: create_database.py lines 51-53
  - Indexed: `idx_region` for query performance
- **Analytics**:
  - **KEY FILTER DIMENSION**
  - Used for regional pricing analysis
  - Used in all analytics views

**Creation** (create_database.py, lines 51-53):
```python
df['region'] = df['destination_country_en'].apply(
    lambda x: 'Europe' if str(x) in EUROPE_COUNTRIES_EN else 'Rest of World'
)
```

**Europe Country List** (create_database.py, lines 18-24):
```python
EUROPE_COUNTRIES_EN = {
    'Germany', 'Austria', 'Belgium', 'Bulgaria', 'Cyprus', 'Croatia',
    'Denmark', 'Slovakia', 'Slovenia', 'Spain', 'Estonia', 'Finland',
    'France', 'Greece', 'Hungary', 'Ireland', 'Iceland', 'Italy',
    'Latvia', 'Lithuania', 'Luxembourg', 'Malta', 'Norway',
    'Netherlands', 'Poland', 'Portugal', 'United Kingdom',
    'Czech Republic', 'Romania', 'Sweden', 'Switzerland'
}
# Total: 31 European countries
```

**Classification Logic**:
```
IF destination_country_en IN EUROPE_COUNTRIES_EN
    → region = "Europe"
ELSE
    → region = "Rest of World"
```

**Distribution**:
- Europe: ~18,000 MT (51%)
- Rest of World: ~17,000 MT (49%)

**Top European Markets**:
- Germany
- Netherlands
- United Kingdom
- Belgium
- France

**Top RoW Markets**:
- United States
- Canada
- Japan
- South Korea
- Australia

**Used In**:
- **pricing.py**: Regional filter parameter (Europe, RoW, or None for worldwide)
- **create_database.py**: regional_exports view
- **CLI**: --region flag for regional pricing queries

---

### 49. canonical_exporter
**Column Name**: `canonical_exporter`
**Type**: TEXT (String, Optional)
**Purpose**: Normalized/standardized exporter name for accurate aggregation
**Sample Values**:
- `VIRU` (from "VIRÚ GROUP PERÚ S.A.", "VIRU S.A.", "VIRU SAC")
- `CAMPOSOL` (from "CAMPOSOL S.A.")
- `MEBOL GF` (from "MEBOL GF S.A.C.", "MEBOL SAC")
- `SUNSHINE` (from "SUNSHINE EXPORT S.A.C")

**Stages**:
- **Raw CSV**: Does not exist
- **Enriched CSV**: Does not exist
- **Database**:
  - **CREATED**: Normalized from Exporter via vt-normalize clustering
  - Source: create_database.py lines 62-64
  - Indexed: `idx_canonical_exporter` for query performance
- **Analytics**:
  - **PRIMARY EXPORTER IDENTIFIER**
  - Used for all exporter-level aggregations
  - Original Exporter name preserved for display

**Creation** (create_database.py, lines 62-64):
```python
df['canonical_exporter'] = df['Exporter'].apply(
    lambda x: get_canonical_name(x) if pd.notna(x) and x != '' else None
)
```

**Normalization Pipeline** (core/exporter_mapping.py + vt_normalize/):

**Step 1: Fix UTF-8 Corruption**
```
"NATURE?S TOUCH" → "NATURE'S TOUCH"
```

**Step 2: Remove Accents** (NFD decomposition)
```
"VIRÚ GROUP PERÚ S.A." → "VIRU GROUP PERU S.A."
```

**Step 3: Strip Legal Suffixes** (50+ patterns)
```python
LEGAL_SUFFIXES = [
    "S.A.", "S.A.C.", "SAC", "S.R.L.", "SRL", "LLC", "Inc", "Inc.",
    "Corp", "Ltd", "NV", "B.V.", "GmbH", "AG", "PLC", ...
]
# "VIRÚ GROUP PERÚ S.A." → "VIRU GROUP PERU"
```

**Step 4: Remove Stop Words** (100+ terms)
```python
STOP_WORDS = [
    "SOCIEDAD", "GRUPO", "AGRICOLA", "EXPORTADORA",
    "COMERCIALIZADORA", "EMPRESA", "INTERNATIONAL", ...
]
# "SOCIEDAD AGRICOLA VIRU S.A." → "VIRU"
```

**Step 5: Remove Addresses**
```
# Remove postal codes, PO boxes, street names
```

**Step 6: Fuzzy Clustering** (85-95% similarity)
```
# Group similar names into canonical form
# Select most frequent variation as canonical name
```

**Example Transformations**:
```
Original                        → Canonical
────────────────────────────────────────────────────
"VIRÚ GROUP PERÚ S.A."         → "VIRU"
"VIRU S.A."                    → "VIRU"
"VIRU SAC"                     → "VIRU"
"MEBOL GF S.A.C."              → "MEBOL GF"
"MEBOL SAC"                    → "MEBOL GF"
"SUNSHINE EXPORT S.A.C"        → "SUNSHINE"
"CAMPOSOL S.A."                → "CAMPOSOL"
"NATURE?S TOUCH FROZEN FOODS"  → "NATURES TOUCH FROZEN FOODS"
```

**Results**:
- **Raw names**: 152 unique exporters
- **Canonical names**: 146 unique exporters
- **Reduction**: 3.9% (6 duplicates merged)

**Clustering Storage** (data/clustered_exporters.json):
```json
{
  "VIRÚ GROUP PERÚ S.A.": "VIRU",
  "VIRU S.A.": "VIRU",
  "VIRU SAC": "VIRU",
  "MEBOL GF S.A.C.": "MEBOL GF",
  "MEBOL SAC": "MEBOL GF",
  ...
}
```

**Used In**:
- **pricing.py**: Exporter dimension aggregations
- **pricing.py**: Drill-down by exporter
- **create_database.py**: exporter_products view
- **CLI**: Exporter-level pricing queries

**Lookup Performance**: Indexed for fast queries

---

### 50. canonical_importer
**Column Name**: `canonical_importer`
**Type**: TEXT (String, Optional)
**Purpose**: Normalized/standardized importer name for accurate aggregation
**Sample Values**:
- `SALUD FOODGROUP EUROPE` (from "SALUD FOODGROUP EUROPE B.V.")
- `NATURES TOUCH FROZEN FOODS` (from "NATURE'S TOUCH FROZEN FOODS")
- `DOLE FRUIT COMPANY` (from various Dole entities)

**Stages**:
- **Raw CSV**: Does not exist
- **Enriched CSV**: Does not exist
- **Database**:
  - **CREATED**: Normalized from Importer via vt-normalize clustering
  - Source: create_database.py lines 65-67
  - Indexed: `idx_canonical_importer` for query performance
- **Analytics**:
  - **PRIMARY IMPORTER IDENTIFIER**
  - Used for all importer-level aggregations
  - Original Importer name preserved for display

**Creation** (create_database.py, lines 65-67):
```python
df['canonical_importer'] = df['Importer'].apply(
    lambda x: get_canonical_importer(x) if pd.notna(x) and x != '' else None
)
```

**Normalization Pipeline**: Same as canonical_exporter (see above)

**Results**:
- **Raw names**: 1,423 unique importers
- **Canonical names**: 579 unique importers
- **Reduction**: 59.3% (844 duplicates merged!)

**Why Higher Reduction?**:
- Importers often have multiple subsidiaries
- Regional variations (e.g., "Dole Europe", "Dole USA", etc.)
- More variations in company suffixes across countries

**Example Transformations**:
```
Original                              → Canonical
──────────────────────────────────────────────────────────
"SALUD FOODGROUP EUROPE B.V."        → "SALUD FOODGROUP EUROPE"
"NATURE'S TOUCH FROZEN FOODS"        → "NATURES TOUCH FROZEN FOODS"
"DOLE FRUIT COMPANY, INC."           → "DOLE FRUIT COMPANY"
"SYSCO CORPORATION"                  → "SYSCO"
```

**Clustering Storage** (data/clustered_importers.json):
```json
{
  "SALUD FOODGROUP EUROPE B.V.": "SALUD FOODGROUP EUROPE",
  "SALUD FOODGROUP EUROPE": "SALUD FOODGROUP EUROPE",
  "NATURE'S TOUCH FROZEN FOODS": "NATURES TOUCH FROZEN FOODS",
  ...
}
```

**Used In**:
- **pricing.py**: Importer dimension aggregations
- **pricing.py**: Drill-down by importer
- **create_database.py**: destination_products view
- **CLI**: Importer-level pricing queries

**Note**: May be NULL for some records (confidential importers)

---

### 51. analysis_valid
**Column Name**: `analysis_valid`
**Type**: INTEGER (Boolean: 0 or 1)
**Purpose**: Quality flag indicating if record passes all filters for pricing analysis
**Sample Values**:
- `1` (True - passes all filters, valid for analysis)
- `0` (False - fails one or more filters, excluded from analysis)

**Stages**:
- **Raw CSV**: Does not exist
- **Enriched CSV**: Does not exist
- **Database**:
  - **CREATED**: Calculated during database load or via separate filtering script
  - Source: filters.py lines 288-365
  - Used in v_clean_exports view
- **Analytics**:
  - **CRITICAL FILTER**
  - Only records with analysis_valid = 1 used in pricing calculations
  - v_clean_exports view: `WHERE analysis_valid = 1`

**Creation** (filters.py, lines 288-365):
```python
def filter_valid_shipments(df: pd.DataFrame) -> pd.DataFrame:
    # Apply 5-stage filter cascade
    # Return filtered df with analysis_valid = 1
    # Excluded records have analysis_valid = 0
```

**Filter Criteria** (5 stages):

**1. Air Freight** (lines 68-88)
```python
def is_air_shipment(row) -> bool:
    via = row.get('Via', '')
    return any(method in via.upper() for method in ['AÉREO', 'AEREO', 'AIR'])
# If True → analysis_valid = 0
```

**2. Sample Shipments** (lines 91-124)
```python
def is_sample_shipment(row) -> bool:
    # Check keywords: MUESTRA, SIN VALOR, SAMPLE, TEST
    # Check weight < 10 kg
    # Check value < $10
    # If any True → analysis_valid = 0
```

**3. Small Shipments** (lines 127-146)
```python
def is_small_shipment(row) -> bool:
    return row.get('net_weight_mt', 0) < 0.1  # 100 kg minimum
# If True → analysis_valid = 0
```

**4. Price Floor** (lines 181-202)
```python
def is_below_price_floor(row) -> bool:
    price = row.get('usd_per_mt_fob', None)
    fruit = row.get('fruit_name', 'default')
    floor = FRUIT_PRICE_FLOORS.get(fruit, 500)  # $500-$2,500 depending on fruit
    return price < floor
# If True → analysis_valid = 0
```

**5. IQR Outlier** (lines 338-361)
```python
# Calculate per-fruit quartiles
# Q1 = 25th percentile, Q3 = 75th percentile
# IQR = Q3 - Q1
# lower_bound = Q1 - 1.5 × IQR
# upper_bound = Q3 + 1.5 × IQR
# If price < lower_bound OR price > upper_bound → analysis_valid = 0
```

**Filter Results**:
```
Total records: 14,279
After air freight removal: 14,100 (-179)
After sample removal: 13,950 (-150)
After small shipment removal: 12,800 (-1,150)
After price floor removal: 11,500 (-1,300)
After IQR outlier removal: 10,762 (-738)
─────────────────────────────────────────
Final: 10,762 valid records (75.4% retention)
Invalid: 3,517 records (24.6%)
```

**Distribution**:
- `analysis_valid = 1`: 10,762 records (75.4%)
- `analysis_valid = 0`: 3,517 records (24.6%)

**Used In**:
- **core/database.py**: v_clean_exports view definition
- **pricing.py**: All pricing calculations use v_clean_exports
- **CLI**: All analytics use filtered data by default

**View Definition** (core/database.py):
```sql
CREATE VIEW v_clean_exports AS
SELECT * FROM exports
WHERE analysis_valid = 1
  AND Date >= '2024-10-01'
  AND Date <= '2025-10-31';
```

**Override**: Can query full exports table directly if needed (use_clean_view=False parameter)

---

## ANALYTICS FIELDS (Derived)

These fields are calculated on-the-fly during analytics operations and do not exist in storage.

### Low$ (Q1 Price)
**Column Name**: `Low$`
**Type**: INTEGER (rounded)
**Purpose**: First quartile (25th percentile) price - "low" tier pricing
**Sample Values**:
- `2,150` (USD/MT for mango)
- `2,800` (USD/MT for avocado)
- `3,200` (USD/MT for blueberry)

**Calculation** (pricing.py, lines 92-98):
```python
low_price = df.groupby('dimension_value').agg(
    low_price=('usd_per_mt_fob', lambda x: x.quantile(0.25))
)
```

**Interpretation**: 25% of shipments priced below this, 75% above

**Use Cases**: Budget tier pricing, minimum competitive price

---

### Mid$ (Median Price)
**Column Name**: `Mid$`
**Type**: INTEGER (rounded)
**Purpose**: Median (50th percentile) price - "typical" market price
**Sample Values**:
- `2,650` (USD/MT for mango)
- `3,400` (USD/MT for avocado)
- `4,200` (USD/MT for blueberry)

**Calculation** (pricing.py, lines 92-98):
```python
mid_price = df.groupby('dimension_value').agg(
    mid_price=('usd_per_mt_fob', lambda x: x.quantile(0.50))
)
```

**Interpretation**: 50% of shipments priced below this, 50% above - most common price

**Use Cases**: Market benchmark, typical transaction price, price negotiations

---

### Hi$ (Q3 Price)
**Column Name**: `Hi$`
**Type**: INTEGER (rounded)
**Purpose**: Third quartile (75th percentile) price - "high" tier pricing
**Sample Values**:
- `3,200` (USD/MT for mango)
- `4,100` (USD/MT for avocado)
- `5,500` (USD/MT for blueberry)

**Calculation** (pricing.py, lines 92-98):
```python
hi_price = df.groupby('dimension_value').agg(
    hi_price=('usd_per_mt_fob', lambda x: x.quantile(0.75))
)
```

**Interpretation**: 75% of shipments priced below this, 25% above - premium tier

**Use Cases**: Premium product pricing, organic certification premium, quality differentiation

---

### YTD MT (Year-to-Date Metric Tons)
**Column Name**: `YTD MT`
**Type**: INTEGER (rounded)
**Purpose**: Total metric tons shipped in YTD period (Oct 2024 - Oct 2025)
**Sample Values**:
- `8,500` (MT for mango)
- `5,200` (MT for avocado)
- `3,800` (MT for blueberry)

**Calculation** (pricing.py, lines 92-98):
```python
total_mt = df.groupby('dimension_value').agg(
    total_mt=('net_weight_mt', 'sum')
)
```

**Use Cases**: Volume analysis, market share, exporter capacity

---

### Records
**Column Name**: `Records`
**Type**: INTEGER
**Purpose**: Number of individual shipment records in aggregation
**Sample Values**:
- `3,245` (shipments for mango)
- `1,876` (shipments for avocado)
- `1,456` (shipments for blueberry)

**Calculation** (pricing.py, lines 92-98):
```python
records = df.groupby('dimension_value').agg(
    records=('usd_per_mt_fob', 'count')
)
```

**Use Cases**: Statistical confidence, data sufficiency validation

---

### Fruits (Exporter-Specific)
**Column Name**: `Fruits`
**Type**: INTEGER
**Purpose**: Number of unique fruit types exported by exporter
**Sample Values**:
- `5` (VIRU exports 5 different fruits)
- `7` (CAMPOSOL exports 7 different fruits)
- `2` (Smaller exporters may focus on 1-2 fruits)

**Calculation** (pricing.py, lines 111-114):
```python
fruit_counts = df.groupby('dimension_value')['fruit_name'].nunique()
```

**Use Cases**: Exporter diversification analysis, specialization vs. portfolio strategy

---

## FIELD TRANSFORMATION MAP

### Transformation Stage 1: Raw → Enriched CSV

| Original Field | Action | New Fields Created |
|---|---|---|
| Commercial Description | **NLP PARSE** | → fruit_name, variety, format_type, size_mm, is_organic, is_conventional, is_iqf, is_aseptic, certification |
| Net kg | **CALCULATE** | → net_weight_mt = Net kg ÷ 1000 |
| U$ FOB Tot + net_weight_mt | **CALCULATE** | → usd_per_mt_fob = U$ FOB Tot ÷ net_weight_mt |
| (All other 30 fields) | **PRESERVE** | (Unchanged) |

**Output**: 33 → 46 columns (+13)

---

### Transformation Stage 2: Enriched CSV → Database

| Enriched Field | Action | New Fields Created |
|---|---|---|
| Destination Country | **TRANSLATE** | → destination_country_en (Spanish → English) |
| destination_country_en | **CLASSIFY** | → region (Europe vs Rest of World) |
| Exporter | **NORMALIZE** | → canonical_exporter (vt-normalize clustering) |
| Importer | **NORMALIZE** | → canonical_importer (vt-normalize clustering) |
| (All fields) | **QUALITY FILTER** | → analysis_valid (0 or 1) |
| (All other 43 fields) | **PRESERVE** | (Unchanged) |

**Output**: 46 → 49 columns (+3)

---

### Transformation Stage 3: Database → Analytics

| Database Field | Action | Analytics Output |
|---|---|---|
| usd_per_mt_fob | **QUARTILE (Q1)** | → Low$ (25th percentile) |
| usd_per_mt_fob | **QUARTILE (Q2)** | → Mid$ (50th percentile, median) |
| usd_per_mt_fob | **QUARTILE (Q3)** | → Hi$ (75th percentile) |
| net_weight_mt | **SUM** | → YTD MT (total volume) |
| (Any dimension) | **COUNT** | → Records (shipment count) |
| fruit_name | **COUNT DISTINCT** | → Fruits (for exporter dimension) |

**Output**: Aggregated pricing summaries and drill-downs

---

## QUALITY FILTER SUMMARY

### Filter Cascade Flow

```
14,279 Total Records
    ↓
[1. Air Freight Filter]
    ↓ (Remove 179 records)
14,100 Records
    ↓
[2. Sample Filter]
    ↓ (Remove 150 records)
13,950 Records
    ↓
[3. Small Shipment Filter (<0.1 MT)]
    ↓ (Remove 1,150 records)
12,800 Records
    ↓
[4. Price Floor Filter]
    ↓ (Remove 1,300 records)
11,500 Records
    ↓
[5. IQR Outlier Filter]
    ↓ (Remove 738 records)
10,762 Valid Records (75.4% retention)
    ↓
[v_clean_exports VIEW]
    ↓ + YTD Date Filter (Oct 2024 - Oct 2025)
    ↓
Analysis-Ready Data
```

### Fields Involved in Filtering

| Field | Filter Stage | Condition | Action if Failed |
|---|---|---|---|
| Via | 1. Air Freight | Contains "AÉREO", "AEREO", or "AIR" | analysis_valid = 0 |
| Commercial Description | 2. Sample | Contains "MUESTRA", "SIN VALOR", "SAMPLE", etc. | analysis_valid = 0 |
| net_weight_mt | 2. Sample | < 0.01 MT (10 kg) | analysis_valid = 0 |
| U$ FOB Tot | 2. Sample | < $10 | analysis_valid = 0 |
| net_weight_mt | 3. Small Shipment | < 0.1 MT (100 kg) | analysis_valid = 0 |
| usd_per_mt_fob | 4. Price Floor | < Fruit-specific floor ($500-$2,500) | analysis_valid = 0 |
| usd_per_mt_fob | 5. IQR Outlier | < Q1-1.5×IQR OR > Q3+1.5×IQR | analysis_valid = 0 |
| Date | v_clean_exports | Outside Oct 2024 - Oct 2025 | Excluded from view |

---

## SAMPLE DATA JOURNEY

### Example Record Transformation

**Stage 1: Raw CSV Input**
```csv
HTS Code: 0811909000
Commercial Description: MANGO CONGELADO ORGANICO CHUNKS 20X20MM IQF VARIEDAD: EDWARD
Net kg: 18000.0
U$ FOB Tot: 47250.00
Destination Country: ALEMANIA
Exporter: VIRÚ GROUP PERÚ S.A.
Via: MARÍTIMO
```

**Stage 2: After NLP Enrichment**
```csv
(All original fields preserved)
+ fruit_name: mango
+ variety: Edward
+ format_type: chunks
+ size_mm: 20x20
+ is_organic: 1
+ is_conventional: 0
+ is_iqf: 1
+ is_aseptic: 0
+ certification: organic
+ net_weight_mt: 18.0
+ usd_per_mt_fob: 2625.00
```

**Stage 3: After Database Load**
```sql
(All enriched fields preserved)
+ destination_country_en: Germany
+ region: Europe
+ canonical_exporter: VIRU
+ canonical_importer: (importer canonical name)
+ analysis_valid: 1  -- Passes all filters
```

**Stage 4: In Analytics**
```
Fruit: mango
  Low$: 2,150  (Q1 of all mango prices)
  Mid$: 2,650  (Median of all mango prices)
  Hi$: 3,200   (Q3 of all mango prices)
  YTD MT: 8,500
  Records: 3,245

This record contributes:
  - 18.0 MT to YTD MT
  - $2,625/MT to quartile calculations
  - 1 to Records count
```

---

## FIELD DEPENDENCIES

### Computation Dependencies

```
Net kg
  └─→ net_weight_mt = Net kg ÷ 1000
       ├─→ usd_per_mt_fob = U$ FOB Tot ÷ net_weight_mt
       │    ├─→ Low$ (Q1 quartile)
       │    ├─→ Mid$ (Median)
       │    ├─→ Hi$ (Q3 quartile)
       │    └─→ Price floor filter
       │         └─→ analysis_valid
       └─→ Small shipment filter
            └─→ analysis_valid

Commercial Description
  └─→ NLP Parse
       ├─→ fruit_name
       │    ├─→ Fruit-specific price floor
       │    ├─→ Per-fruit IQR outlier bounds
       │    └─→ Primary aggregation dimension
       ├─→ variety (optional)
       ├─→ format_type
       ├─→ size_mm (optional)
       ├─→ is_organic
       │    └─→ certification
       ├─→ is_conventional
       │    └─→ certification
       ├─→ is_iqf
       └─→ is_aseptic

Destination Country (Spanish)
  └─→ destination_country_en (English)
       └─→ region (Europe vs Rest of World)
            └─→ Regional pricing filters

Exporter
  └─→ canonical_exporter
       └─→ Exporter aggregation dimension

Importer
  └─→ canonical_importer
       └─→ Importer aggregation dimension

Via + Commercial Description + net_weight_mt + U$ FOB Tot + usd_per_mt_fob
  └─→ Quality filters (5 stages)
       └─→ analysis_valid
            └─→ v_clean_exports VIEW
```

---

## INDEXING STRATEGY

### Database Indexes Created

```sql
CREATE INDEX idx_exporter ON exports(Exporter);
CREATE INDEX idx_canonical_exporter ON exports(canonical_exporter);
CREATE INDEX idx_canonical_importer ON exports(canonical_importer);
CREATE INDEX idx_destination ON exports([Destination Country]);
CREATE INDEX idx_fruit ON exports(fruit_name);
CREATE INDEX idx_format ON exports(format_type);
CREATE INDEX idx_size ON exports(size_mm);
CREATE INDEX idx_certification ON exports(certification);
CREATE INDEX idx_date ON exports(Date);
CREATE INDEX idx_region ON exports(region);
```

**Total**: 10 indexes for query performance

**Query Patterns Optimized**:
- Filter by fruit: `idx_fruit`
- Filter by exporter: `idx_canonical_exporter`
- Filter by region: `idx_region`
- Time-series queries: `idx_date`
- Format drill-downs: `idx_format`
- Certification analysis: `idx_certification`

---

## VALIDATION THRESHOLDS

### Data Quality Checks (enrich_data.py)

| Check | Threshold | Current Status |
|---|---|---|
| Unknown fruits | < 1% | ✓ 0.3% (Pass) |
| Missing prices | < 5% | ✓ 2.8% (Pass) |
| Zero volumes | < 5% | ✓ 1.9% (Pass) |
| High price outliers (>$10k/MT) | 0 records | ⚠️ 42 records (Flagged) |
| Low price outliers (<$500/MT) | 0 records | ⚠️ 156 records (Flagged) |
| Unknown formats | < 10% | ✓ 8.7% (Pass) |
| Unknown certification | < 70% | ✓ 67.6% (Pass) |

---

## END OF DOCUMENT

**Document Version**: 1.0
**Generated**: 2026-01-07
**Total Fields Documented**: 51 (33 original + 13 enriched + 3 database + 2 nested)
**Total Transformations**: 6 major stages
**Database Size**: 21 MB (49 columns × 14,279 records)

**Usage**: Reference guide for understanding field origins, transformations, and usage throughout the Peru frozen fruit export analysis pipeline.

**Related Documents**:
- DATA_STRUCTURE.md - Complete data architecture and pipeline overview
- README.md - Project overview and usage
- models.py - Pydantic schema definitions
- parser.py - NLP extraction patterns
- filters.py - Quality filtering logic
