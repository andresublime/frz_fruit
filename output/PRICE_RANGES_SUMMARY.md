# Peru Frozen Fruit Exports to Europe - Price Range Analysis

## Summary Statistics
- **Total Export Records:** 5,433
- **Clean Records (outliers removed):** 5,401 (99.4%)
- **Outliers Identified:** 32 (0.6%)
- **Fruit Types:** 18
- **Exporters:** 85
- **Format Types:** 13
- **Date Range:** January 2024 to October 2025

## Recommended Price Ranges by Fruit (Outliers Excluded)

Prices are FOB (Free on Board) in USD per Metric Ton.

| Fruit | Export Records | Outliers | Min USD/MT | Max USD/MT | Median USD/MT | Main Formats |
|-------|----------------|----------|------------|------------|---------------|--------------|
| **Avocado** | 2,585 | 7 | $1,771 | $4,039 | $2,860 | Unknown, Pulp, Cubes, Chunks, Slices |
| **Mango** | 1,620 | 13 | $899 | $2,636 | $1,749 | Unknown, Chunks, Puree, Cubes, Pulp |
| **Blueberry** | 774 | 6 | $1,447 | $3,056 | $2,230 | Unknown, Chunks, Whole, IQF |
| **Lucuma** | 156 | 1 | $2 | $6,100 | $2,500 | Unknown, Pulp, Halves |
| **Passion Fruit** | 98 | 1 | $833 | $4,300 | $2,500 | Pulp, Unknown, Juice |
| **Pineapple** | 53 | 2 | $5 | $4,280 | $893 | Unknown, Chunks, Pulp, Juice |
| **Banana** | 30 | 1 | $30 | $4,072 | $1,050 | Slices, Unknown, Pulp, Whole |
| **Acai** | 29 | 1 | $2 | $1,394 | $354 | Pulp, Unknown, Chunks |
| **Strawberry** | 23 | 0 | $26 | $7,325 | $1,050 | Unknown, Pulp, Whole |
| **Grape** | 18 | 0 | $2 | $3,379 | $1,464 | Unknown |
| **Soursop** | 14 | 0 | $557 | $3,715 | $1,613 | Pulp, Unknown, Chunks |
| **Mix** | 10 | 0 | $150 | $4,950 | $2,680 | IQF, Unknown |
| **Golden Berry** | 8 | 0 | $30 | $9,519 | $1,808 | Unknown, IQF, Whole |
| **Camu Camu** | 8 | 0 | $43,211 | $58,525 | $49,945 | Unknown, Pulp |
| **Papaya** | 7 | 0 | $667 | $2,248 | $1,805 | Chunks, Cubes, Pulp |
| **Cherimoya** | 2 | 0 | $5,639 | $6,056 | $5,847 | Pulp |
| **Pitaya** | 1 | 0 | $1,957 | $1,957 | $1,957 | Unknown |
| **Pomegranate** | 1 | 0 | $3,800 | $3,800 | $3,800 | Unknown |

## Key Insights

### High-Volume Fruits
1. **Avocado**: Dominant export with 2,585 records, consistent pricing around $2,860/MT
2. **Mango**: Second largest with 1,620 records, lower price point at $1,749/MT
3. **Blueberry**: Third with 774 records, premium pricing at $2,230/MT

### Premium Products
- **Camu Camu**: Highest price range ($43k-$59k/MT) - superfood with limited supply
- **Strawberry**: Wide price variance ($26-$7,325/MT) indicating quality/format differences
- **Golden Berry**: High variability ($30-$9,519/MT) suggesting niche market

### Format Diversity
- **Avocado**: Most format variety (10 types) - Unknown, Pulp, Cubes, Chunks, Slices, Halves, IQF, Puree, Broken pieces, Juice
- **Mango**: High format variety (10 types) - Unknown, Chunks, Puree, Cubes, Pulp, IQF, Concentrate, Halves, Broken pieces, Strips
- **Blueberry**: Limited formats (4 types) - mainly Unknown and IQF

### Outlier Detection Methodology
- **IQR Method**: Identifies values outside 1.5x the interquartile range
- **Z-Score Method**: Identifies values more than 3 standard deviations from mean
- **Combined Approach**: Only flags as outlier if BOTH methods agree (conservative approach)
- This dual-method approach ensures only extreme outliers are excluded

## Data Quality Notes

1. **"Unknown" Format**: Large portion of exports lack specific format classification
2. **Price Variability**:
   - Some fruits (Camu Camu, Strawberry, Golden Berry) show extreme price ranges
   - This may reflect quality tiers, organic certification, or processing differences
3. **Low Volume Items**: Pitaya, Pomegranate, Cherimoya have <5 records - use ranges cautiously

## Files Generated

1. **europe_fruit_exports_full.csv** - Complete dataset with outlier flags
2. **europe_fruit_exports_clean.csv** - Dataset with outliers removed (recommended for pricing)
3. **europe_price_statistics.json** - Detailed statistics for each fruit
4. **europe_format_summary.csv** - Analysis by fruit and format type
5. **europe_exporter_summary.csv** - Analysis by fruit and exporter

## Usage Recommendations

For pricing strategy:
- Use **Median** prices as baseline (more robust than mean)
- Use **Recommended Min/Max** ranges for negotiation boundaries
- Consider format-specific pricing from the format_summary file
- Review top exporters in exporter_summary for competitive benchmarking

---

*Data Source: Veritrade Peru Export Database*
*Analysis Period: January 2024 - October 2025*
*Generated: 2025-11-13*
