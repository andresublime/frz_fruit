# Peru Frozen Fruit Export Analysis

Analysis of Peru's frozen fruit export data with pricing insights and market intelligence.

## Data Coverage

- **Date Range**: November 2024 - October 2025 (last 12 months)
- **Total Export Volume**: 148,247 MT
- **Products**: 19 frozen fruit varieties
- **Exporters**: 200+ companies

## Key Outputs

### 1. Worldwide Pricing Summary (`output/pricing_summary_worldwide.csv`)
Quartile-based pricing (Q1, Median, Q3) for all frozen fruit products with data quality filters applied:
- Excludes samples and test shipments
- Filters out unrealistic pricing
- Minimum shipment size: 100kg

**Top Products by Volume:**
1. Mango: 86,218 MT
2. Avocado: 34,783 MT
3. Blueberry: 19,262 MT

### 2. Top 20 Exporters (`output/top_20_exporters.csv`)
Leading exporters by total volume (Oct 2024 - Oct 2025)

**Top 5:**
1. VIRU S.A.: 16,938 MT
2. SUNSHINE EXPORT S.A.C: 14,797 MT
3. CAMPOSOL S.A.: 13,113 MT
4. AGROINDUSTRIAS AIB S.A: 12,484 MT
5. AGRICOLA Y GANADERA CHAVIN DE HUANTAR SA: 12,322 MT

## Data Quality

Applied filters:
- ✅ Excluded 482 sample shipments
- ✅ Excluded 644 shipments < 100kg
- ✅ Excluded 551 unrealistically priced shipments
- ✅ Date-filtered to last 12 months only

## Files

```
├── Export-Data/           # Raw export data and database
│   └── exports.db        # SQLite database with cleaned data
├── output/               # Analysis outputs
│   ├── pricing_summary_worldwide.csv
│   └── top_20_exporters.csv
└── README.md
```

## Usage

Generate fresh analysis:
```bash
cd output
uv run create_clean_pricing_summary.py
uv run create_top_exporters.py
```

## Data Sources

- Peru customs export data
- Processed and standardized for analysis
- Includes fruit classification, pricing, and destination information
