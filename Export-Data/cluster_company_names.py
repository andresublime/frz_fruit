#!/usr/bin/env python3
"""
Cluster company names (exporters and importers) from the database using vt-normalize.

This script extracts all unique company names from the exports database,
clusters them to identify variations, and saves the canonical mappings.

Output:
- data/clustered_exporters.json - Exporter canonical name mappings
- data/clustered_importers.json - Importer canonical name mappings
"""

import json
import sqlite3
from pathlib import Path
from collections import Counter

from vt_normalize import CompanyNormalizer
from vt_normalize.models import CompanyName
from vt_normalize.clustering import cluster_company_names
from vt_normalize.text_utils import clean_company_name
from vt_normalize.config import INVALID_NAMES, Colors


def extract_company_names_from_db(
    db_path: str,
    column_name: str,
    entity_type: str
) -> tuple[list[str], dict[str, int]]:
    """
    Extract company names and their counts from the database.

    Args:
        db_path: Path to SQLite database
        column_name: Column name to extract ('Exporter' or 'Importer')
        entity_type: Type of entity for display ('exporter' or 'importer')

    Returns:
        Tuple of (unique_names, name_counts)
    """
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}")
    print(f"{'EXTRACTING ' + entity_type.upper() + 'S FROM DATABASE':^80}")
    print(f"{'='*80}{Colors.RESET}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all company names with counts
    query = f"""
        SELECT "{column_name}", COUNT(*) as count
        FROM exports
        WHERE "{column_name}" IS NOT NULL
        AND "{column_name}" != ''
        GROUP BY "{column_name}"
        ORDER BY count DESC
    """

    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()

    # Filter out invalid names
    filtered_results = []
    for name, count in results:
        cleaned = clean_company_name(name, strip_legal=True, remove_addresses=True)
        if cleaned not in INVALID_NAMES and cleaned.strip():
            filtered_results.append((name, count))

    # Build lists
    unique_names = [name for name, _ in filtered_results]
    name_counts = {name: count for name, count in filtered_results}

    total_records = sum(name_counts.values())
    filtered_out = len(results) - len(filtered_results)

    print(f"{Colors.BRIGHT_CYAN}Raw unique {entity_type}s:{Colors.RESET} {Colors.BRIGHT_WHITE}{len(results):,}{Colors.RESET}")
    if filtered_out > 0:
        print(f"{Colors.BRIGHT_YELLOW}Invalid names filtered:{Colors.RESET} {Colors.BRIGHT_RED}{filtered_out}{Colors.RESET}")
    print(f"{Colors.BRIGHT_CYAN}Valid unique {entity_type}s:{Colors.RESET} {Colors.BRIGHT_WHITE}{len(unique_names):,}{Colors.RESET}")
    print(f"{Colors.BRIGHT_CYAN}Total records:{Colors.RESET} {Colors.BRIGHT_WHITE}{total_records:,}{Colors.RESET}")

    return unique_names, name_counts


def print_clustering_stats(
    clustered: list[CompanyName],
    name_counts: dict[str, int],
    total_raw: int,
    entity_type: str
):
    """Print comprehensive clustering statistics."""
    total_clustered = len(clustered)
    reduction_count = total_raw - total_clustered
    reduction_pct = (reduction_count / total_raw * 100) if total_raw > 0 else 0

    # Quality metrics
    single_name_clusters = sum(1 for item in clustered if len(item.aliases) == 0)
    multi_name_clusters = total_clustered - single_name_clusters
    total_records = sum(item.count for item in clustered)
    avg_records_per_cluster = total_records / total_clustered if total_clustered > 0 else 0

    print(f"\n{Colors.BOLD}{Colors.MAGENTA}{'='*80}")
    print(f"{'CLUSTERING RESULTS SUMMARY':^80}")
    print(f"{'='*80}{Colors.RESET}")
    print(f"{Colors.BRIGHT_CYAN}Raw unique {entity_type}s:{Colors.RESET}        {Colors.BRIGHT_WHITE}{total_raw:,}{Colors.RESET}")
    print(f"{Colors.BRIGHT_CYAN}Clustered unique {entity_type}s:{Colors.RESET}  {Colors.BRIGHT_WHITE}{total_clustered:,}{Colors.RESET}")
    print(f"{Colors.BRIGHT_CYAN}Names merged:{Colors.RESET}                   {Colors.BRIGHT_GREEN}{reduction_count:,}{Colors.RESET} {Colors.DIM}({reduction_pct:.1f}%){Colors.RESET}")
    print(f"{Colors.BRIGHT_CYAN}Total records:{Colors.RESET}         {Colors.BRIGHT_WHITE}{total_records:,}{Colors.RESET}")
    print(f"{Colors.BRIGHT_CYAN}Average records per {entity_type}:{Colors.RESET} {Colors.BRIGHT_WHITE}{avg_records_per_cluster:.1f}{Colors.RESET}")
    print(f"\n{Colors.YELLOW}Clustering breakdown:{Colors.RESET}")
    print(f"  {Colors.BRIGHT_BLUE}Single-name clusters:{Colors.RESET}  {single_name_clusters:,} {Colors.DIM}({single_name_clusters/total_clustered*100:.1f}%){Colors.RESET}")
    print(f"  {Colors.BRIGHT_BLUE}Multi-name clusters:{Colors.RESET}   {multi_name_clusters:,} {Colors.DIM}({multi_name_clusters/total_clustered*100:.1f}%){Colors.RESET}")

    # Top 10 by count
    print(f"\n{Colors.BOLD}{Colors.YELLOW}{'='*80}")
    print(f"{'TOP 10 ' + entity_type.upper() + 'S BY RECORD COUNT':^80}")
    print(f"{'='*80}{Colors.RESET}")
    sorted_by_count = sorted(clustered, key=lambda x: x.count, reverse=True)[:10]
    for i, item in enumerate(sorted_by_count, 1):
        print(f"\n{Colors.BOLD}{Colors.BRIGHT_YELLOW}{i:2d}.{Colors.RESET} {Colors.BRIGHT_WHITE}{item.canonical_name}{Colors.RESET}")
        print(f"    {Colors.CYAN}Records:{Colors.RESET} {Colors.BRIGHT_GREEN}{item.count:,}{Colors.RESET}")
        if item.aliases:
            print(f"    {Colors.CYAN}Aliases:{Colors.RESET} {Colors.BRIGHT_MAGENTA}{len(item.aliases)}{Colors.RESET} {Colors.DIM}variations{Colors.RESET}")
            for alias in item.aliases[:3]:
                print(f"      {Colors.DIM}•{Colors.RESET} {Colors.WHITE}{alias}{Colors.RESET}")
            if len(item.aliases) > 3:
                print(f"      {Colors.DIM}... and {len(item.aliases) - 3} more{Colors.RESET}")


def main():
    """Main clustering pipeline."""
    db_path = 'exports.db'

    # Create data directory if it doesn't exist
    data_dir = Path('data')
    data_dir.mkdir(exist_ok=True)

    # Process exporters
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}")
    print(f"{'CLUSTERING EXPORTERS':^80}")
    print(f"{'='*80}{Colors.RESET}\n")

    exporter_names, exporter_counts = extract_company_names_from_db(
        db_path, 'Exporter', 'exporter'
    )

    print(f"\n{Colors.BOLD}{Colors.CYAN}Running clustering algorithm...{Colors.RESET}")
    clustered_exporters = cluster_company_names(exporter_names, exporter_counts)

    print_clustering_stats(
        clustered_exporters, exporter_counts, len(exporter_names), 'exporter'
    )

    # Save exporters - UPPERCASE canonical names
    exporter_output = data_dir / 'clustered_exporters.json'
    exporter_data = []
    for item in clustered_exporters:
        data = item.model_dump()
        data['canonical_name'] = data['canonical_name'].upper()
        exporter_data.append(data)
    with open(exporter_output, 'w') as f:
        json.dump(exporter_data, f, indent=2)

    print(f"\n{Colors.BRIGHT_GREEN}✓{Colors.RESET} Saved to: {Colors.BRIGHT_WHITE}{exporter_output}{Colors.RESET}")

    # Process importers
    print(f"\n\n{Colors.BOLD}{Colors.CYAN}{'='*80}")
    print(f"{'CLUSTERING IMPORTERS':^80}")
    print(f"{'='*80}{Colors.RESET}\n")

    importer_names, importer_counts = extract_company_names_from_db(
        db_path, 'Importer', 'importer'
    )

    print(f"\n{Colors.BOLD}{Colors.CYAN}Running clustering algorithm...{Colors.RESET}")
    clustered_importers = cluster_company_names(importer_names, importer_counts)

    print_clustering_stats(
        clustered_importers, importer_counts, len(importer_names), 'importer'
    )

    # Save importers - UPPERCASE canonical names
    importer_output = data_dir / 'clustered_importers.json'
    importer_data = []
    for item in clustered_importers:
        data = item.model_dump()
        data['canonical_name'] = data['canonical_name'].upper()
        importer_data.append(data)
    with open(importer_output, 'w') as f:
        json.dump(importer_data, f, indent=2)

    print(f"\n{Colors.BRIGHT_GREEN}✓{Colors.RESET} Saved to: {Colors.BRIGHT_WHITE}{importer_output}{Colors.RESET}")

    # Final summary
    print(f"\n{Colors.BOLD}{Colors.MAGENTA}{'='*80}")
    print(f"{'CLUSTERING COMPLETE':^80}")
    print(f"{'='*80}{Colors.RESET}")
    print(f"{Colors.BRIGHT_CYAN}Exporters:{Colors.RESET} {Colors.BRIGHT_WHITE}{len(exporter_names):,}{Colors.RESET} → {Colors.BRIGHT_GREEN}{len(clustered_exporters):,}{Colors.RESET}")
    print(f"{Colors.BRIGHT_CYAN}Importers:{Colors.RESET} {Colors.BRIGHT_WHITE}{len(importer_names):,}{Colors.RESET} → {Colors.BRIGHT_GREEN}{len(clustered_importers):,}{Colors.RESET}")
    print()


if __name__ == '__main__':
    main()
