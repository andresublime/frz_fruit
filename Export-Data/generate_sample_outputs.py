"""
Generate sample pricing outputs to validate the new coherent system.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from analysis.pricing import calculate_pricing_summary, calculate_pricing_drill_down, export_to_csv


def main():
    print("Generating Sample Pricing Outputs")
    print("=" * 80)

    output_dir = Path(__file__).parent / 'sample_outputs'
    output_dir.mkdir(exist_ok=True)

    # 1. Fruit-level summary (worldwide)
    print("\n1. Generating fruit summary (worldwide)...")
    df_fruit = calculate_pricing_summary(dimension='fruit')
    export_to_csv(df_fruit, output_dir / 'fruit_pricing_summary.csv')
    print(df_fruit.head(10).to_string(index=False))

    # 2. Exporter-level summary (worldwide)
    print("\n2. Generating exporter summary (worldwide)...")
    df_exporter = calculate_pricing_summary(dimension='exporter')
    export_to_csv(df_exporter, output_dir / 'exporter_pricing_summary.csv')
    print(df_exporter.head(10).to_string(index=False))

    # 3. Format-level summary (worldwide)
    print("\n3. Generating format summary (worldwide)...")
    df_format = calculate_pricing_summary(dimension='format')
    export_to_csv(df_format, output_dir / 'format_pricing_summary.csv')

    # 4. Mango by exporter drill-down
    print("\n4. Generating mango by exporter drill-down...")
    df_mango = calculate_pricing_drill_down('fruit', 'mango', by='exporter')
    export_to_csv(df_mango, output_dir / 'mango_by_exporter.csv')

    # 5. Avocado by exporter drill-down
    print("\n5. Generating avocado by exporter drill-down...")
    df_avocado = calculate_pricing_drill_down('fruit', 'avocado', by='exporter')
    export_to_csv(df_avocado, output_dir / 'avocado_by_exporter.csv')

    # 6. Viru by fruit drill-down
    print("\n6. Generating Viru by fruit drill-down...")
    df_viru = calculate_pricing_drill_down('exporter', 'Viru', by='fruit')
    export_to_csv(df_viru, output_dir / 'viru_by_fruit.csv')

    # 7. Top exporters by fruit drill-down
    print("\n7. Generating top 3 exporters drill-downs...")
    for exporter in ['Viru', 'Sunshine Export', 'Camposol']:
        df = calculate_pricing_drill_down('exporter', exporter, by='fruit')
        safe_name = exporter.lower().replace(' ', '_')
        export_to_csv(df, output_dir / f'{safe_name}_by_fruit.csv')

    print("\n" + "=" * 80)
    print(f"✓ All outputs generated in: {output_dir}")
    print("=" * 80)

    # Summary
    print("\nGenerated Files:")
    for f in sorted(output_dir.glob('*.csv')):
        print(f"  - {f.name}")


if __name__ == '__main__':
    main()
