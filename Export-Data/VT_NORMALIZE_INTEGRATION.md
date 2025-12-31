# VT-Normalize Integration

## Overview

The Export-Data project now uses **vt-normalize**, a sophisticated company name normalization and clustering library, replacing the previous manual mapping approach. This integration provides automated discovery of company name variations with significantly improved accuracy and coverage.

## Key Improvements

### Before (Manual Mapping)
- **Exporters:** 57 explicit manual mappings
- **Importers:** 200+ exact dictionary lookups (no fuzzy matching)
- **Maintenance:** All variations had to be manually identified and added
- **Coverage:** Limited to manually discovered variations

### After (VT-Normalize Clustering)
- **Exporters:** 146 canonical names (from 152 raw names, 3.9% reduction)
- **Importers:** 579 canonical names (from 1,423 raw names, **59.3% reduction!**)
- **Maintenance:** Automated clustering discovers variations
- **Coverage:** Comprehensive, handles all name variations automatically

## Clustering Results

### Exporters
- **Raw unique names:** 152
- **Clustered canonical names:** 146
- **Names merged:** 6 (3.9% reduction)
- **Total records:** 14,264 shipments

**Top Example:**
- **VIRU:** 2 variations merged (2,640 shipments)
  - VIRU S.A.

### Importers
- **Raw unique names:** 1,423
- **Clustered canonical names:** 579
- **Names merged:** 844 (**59.3% reduction!**)
- **Total records:** 13,616 shipments

**Top Examples:**
- **NATURES TOUCH FROZEN FOODS:** 32 variations merged (753 shipments)
- **SALUD FOODGROUP EUROPE:** 5 variations merged (648 shipments)
- **DOLE PACKAGED FOODS:** 7 variations merged (372 shipments)
- **GLOBAL FOOD LINK:** 10 variations merged (278 shipments)

## Technical Approach

### Multi-Stage Normalization

1. **Encoding fixes**
   - `NATURE?S` → `NATURE'S` (character corruption)
   - UTF-8 mojibake patterns

2. **Accent removal**
   - `VIRÚ` → `VIRU`
   - `Ã?` corruption handling

3. **Apostrophe joining**
   - `D'ARTA` → `DARTA`
   - Handles multiple apostrophe encodings

4. **Legal suffix removal (pattern-based)**
   - S.A., S.A.C., LLC, Inc, NV, GmbH, Ltd, SPA, etc.
   - Handles all spacing variations: `B.V` / `BV` / `B V`
   - Polish: `SP. Z O.O.` (all variations)
   - Czech: `S.R.O.`
   - Indian: `PVT. LTD`

5. **Stop word filtering (100+ terms)**
   - Business prefixes: SOCIEDAD, GRUPO, AGRICOLA, EXPORTADORA
   - Countries: MEXICO, POLAND, USA, SWITZERLAND, etc.
   - Locations: GOURIN, KENT, BASEL

6. **Address removal**
   - C/O patterns
   - Street addresses
   - Postal codes
   - Office/unit designations

### Clustering Algorithm

1. **Core name grouping**
   ```
   "SOCIEDAD AGRICOLA VIRU S.A." → core: "VIRU"
   "VIRU GROUP PERU" → core: "VIRU"
   ```

2. **Fuzzy matching within groups (80% threshold)**
   ```
   "NATURE TOUCH" ≈ "NATURES TOUCH" → merged
   ```

3. **Cross-group merging (90% threshold)**
   ```
   "HG FOOD" ≈ "HG FOODS" → merged
   ```

4. **Spacing-normalized comparison (95% threshold)**
   ```
   "FOOD FELLAS" ≈ "FOODFELLAS" → merged
   ```

## Usage

### Running Clustering

Generate or update canonical name mappings:

```bash
uv run cluster_company_names.py
```

Output:
- `data/clustered_exporters.json` - Exporter canonical mappings
- `data/clustered_importers.json` - Importer canonical mappings

### Using in Code

The clustering is integrated transparently into the existing API:

```python
from core.exporter_mapping import get_canonical_name
from core.importer_mapping import get_canonical_importer

# Exporter name normalization
get_canonical_name('VIRU S.A.')  # → 'VIRU'
get_canonical_name('MEBOL GF S.A.C.')  # → 'MEBOL GF'

# Importer name normalization
get_canonical_importer('SALUD FOODGROUP EUROPE B.V')  # → 'SALUD FOODGROUP EUROPE'
get_canonical_importer("NATURE'S TOUCH FROZEN FOODS INC")  # → 'NATURES TOUCH FROZEN FOODS'
```

### Statistics

```python
from core.exporter_mapping import get_mapping_stats

stats = get_mapping_stats()
print(f"Canonical exporters: {stats['canonical_names']:,}")
print(f"Names merged: {stats['names_merged']:,} ({stats['reduction_pct']:.1f}%)")
```

## Architecture

```
Export-Data/
├── vt_normalize/               # VT-Normalize library
│   ├── models.py               # Pydantic data models
│   ├── config.py               # Stop words, legal suffixes, thresholds
│   ├── text_utils.py           # Text normalization functions
│   ├── clustering.py           # Clustering algorithms
│   └── normalizer.py           # Main CompanyNormalizer class
│
├── core/
│   ├── exporter_mapping.py     # Exporter name lookups (vt-normalize powered)
│   └── importer_mapping.py     # Importer name lookups (vt-normalize powered)
│
├── data/
│   ├── clustered_exporters.json  # 146 canonical exporters
│   └── clustered_importers.json  # 579 canonical importers
│
└── cluster_company_names.py    # Clustering script
```

## Benefits

1. **Automated Discovery**
   - No manual mapping required
   - Automatically finds all variations

2. **Superior Accuracy**
   - Multi-stage normalization handles edge cases
   - Fuzzy matching catches similar names

3. **Massive Deduplication**
   - 59.3% reduction in importer duplicates
   - Eliminates manual maintenance burden

4. **Easy Maintenance**
   - Rerun clustering when new data arrives
   - No code changes needed for new variations

5. **Backward Compatible**
   - Same API as manual mappings
   - Drop-in replacement

## Performance

- **Lazy loading:** Database loaded only on first use
- **O(1) lookups:** Fast exact match first
- **Fallback normalization:** Handles unmapped names gracefully
- **Caching:** In-memory dictionary for speed

## Future Enhancements

- [ ] Periodic automated clustering runs
- [ ] Manual override mechanism for edge cases
- [ ] Similarity scoring for review
- [ ] Machine learning-based clustering
- [ ] Cross-dataset name linking
