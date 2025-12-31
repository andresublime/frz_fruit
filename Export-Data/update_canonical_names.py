#!/usr/bin/env python3
"""
Update Database with VT-Normalize Canonical Names

Updates the canonical_exporter and canonical_importer columns in the exports
table with the new vt-normalize clustered canonical names.

This replaces the old manual mapping names with the new automated clustering results.
"""

import sqlite3
from pathlib import Path
import json

from vt_normalize.config import Colors


def load_canonical_mappings(json_path: str) -> dict[str, str]:
    """Load canonical mappings from clustered JSON file."""
    with open(json_path, 'r') as f:
        clustered_data = json.load(f)

    # Build alias -> canonical lookup dictionary
    mapping = {}
    for item in clustered_data:
        canonical = item['canonical_name']

        # Map the canonical name to itself
        mapping[canonical] = canonical

        # Map all aliases to canonical
        for alias in item.get('aliases', []):
            mapping[alias] = canonical

    return mapping


def update_canonical_names(db_path: str, column_name: str, mapping: dict[str, str], entity_type: str):
    """Update canonical names in the database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all unique original names from the database
    cursor.execute(f'SELECT DISTINCT "{column_name}" FROM exports WHERE "{column_name}" IS NOT NULL')
    original_names = [row[0] for row in cursor.fetchall()]

    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}")
    print(f"{'UPDATING ' + entity_type.upper() + ' CANONICAL NAMES':^80}")
    print(f"{'='*80}{Colors.RESET}")
    print(f"{Colors.BRIGHT_CYAN}Total unique {entity_type}s:{Colors.RESET} {Colors.BRIGHT_WHITE}{len(original_names):,}{Colors.RESET}")

    # Update each name
    updated_count = 0
    unmapped_count = 0
    unmapped_names = []

    total = len(original_names)
    for idx, original_name in enumerate(original_names, 1):
        # Look up canonical name
        canonical_name = mapping.get(original_name)

        if canonical_name:
            # Update all records with this original name
            canonical_col = f"canonical_{entity_type}"
            cursor.execute(
                f'UPDATE exports SET "{canonical_col}" = ? WHERE "{column_name}" = ?',
                (canonical_name, original_name)
            )
            updated_count += 1
        else:
            unmapped_count += 1
            unmapped_names.append(original_name)

        # Progress indicator
        if idx % 50 == 0 or idx == total:
            print(f"  Progress: {idx}/{total} {entity_type}s processed...", end='\r')

    print()  # New line after progress
    conn.commit()

    # Get update statistics
    cursor.execute(f'SELECT COUNT(*) FROM exports WHERE canonical_{entity_type} IS NOT NULL')
    total_records_updated = cursor.fetchone()[0]

    print(f"\n{Colors.BRIGHT_GREEN}✓{Colors.RESET} {Colors.CYAN}Updated:{Colors.RESET} {Colors.BRIGHT_WHITE}{updated_count:,}{Colors.RESET} unique {entity_type}s")
    print(f"{Colors.BRIGHT_GREEN}✓{Colors.RESET} {Colors.CYAN}Records updated:{Colors.RESET} {Colors.BRIGHT_WHITE}{total_records_updated:,}{Colors.RESET}")

    if unmapped_count > 0:
        print(f"\n{Colors.BRIGHT_YELLOW}⚠{Colors.RESET}  {Colors.YELLOW}Unmapped {entity_type}s:{Colors.RESET} {Colors.BRIGHT_RED}{unmapped_count}{Colors.RESET}")
        print(f"{Colors.DIM}These names were not in the clustering output (likely filtered as invalid):{Colors.RESET}")
        for name in unmapped_names[:10]:
            print(f"  {Colors.DIM}•{Colors.RESET} {name}")
        if len(unmapped_names) > 10:
            print(f"  {Colors.DIM}... and {len(unmapped_names) - 10} more{Colors.RESET}")

    conn.close()
    return updated_count, unmapped_count


def verify_updates(db_path: str):
    """Verify the updates by showing sample canonical names."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print(f"\n{Colors.BOLD}{Colors.MAGENTA}{'='*80}")
    print(f"{'VERIFICATION - SAMPLE CANONICAL NAMES':^80}")
    print(f"{'='*80}{Colors.RESET}")

    # Show top exporters
    cursor.execute('''
        SELECT canonical_exporter, COUNT(*) as count
        FROM exports
        WHERE canonical_exporter IS NOT NULL
        GROUP BY canonical_exporter
        ORDER BY count DESC
        LIMIT 10
    ''')

    print(f"\n{Colors.BRIGHT_CYAN}Top 10 Exporters (by record count):{Colors.RESET}")
    for i, (name, count) in enumerate(cursor.fetchall(), 1):
        print(f"  {Colors.BRIGHT_YELLOW}{i:2d}.{Colors.RESET} {Colors.BRIGHT_WHITE}{name:30}{Colors.RESET} {Colors.GREEN}{count:,}{Colors.RESET} records")

    # Show top importers
    cursor.execute('''
        SELECT canonical_importer, COUNT(*) as count
        FROM exports
        WHERE canonical_importer IS NOT NULL
        GROUP BY canonical_importer
        ORDER BY count DESC
        LIMIT 10
    ''')

    print(f"\n{Colors.BRIGHT_CYAN}Top 10 Importers (by record count):{Colors.RESET}")
    for i, (name, count) in enumerate(cursor.fetchall(), 1):
        print(f"  {Colors.BRIGHT_YELLOW}{i:2d}.{Colors.RESET} {Colors.BRIGHT_WHITE}{name:30}{Colors.RESET} {Colors.GREEN}{count:,}{Colors.RESET} records")

    conn.close()


def main():
    """Main update pipeline."""
    db_path = 'exports.db'

    print(f"\n{Colors.BOLD}{Colors.MAGENTA}{'='*80}")
    print(f"{'VT-NORMALIZE DATABASE UPDATE':^80}")
    print(f"{'='*80}{Colors.RESET}")
    print(f"\n{Colors.CYAN}This script updates the database with new canonical company names")
    print(f"from the vt-normalize clustering system.{Colors.RESET}\n")

    # Load mappings
    print(f"{Colors.BRIGHT_CYAN}Loading canonical mappings...{Colors.RESET}")
    exporter_mapping = load_canonical_mappings('data/clustered_exporters.json')
    importer_mapping = load_canonical_mappings('data/clustered_importers.json')
    print(f"{Colors.GREEN}✓{Colors.RESET} Loaded {len(exporter_mapping):,} exporter mappings")
    print(f"{Colors.GREEN}✓{Colors.RESET} Loaded {len(importer_mapping):,} importer mappings")

    # Update exporters
    exp_updated, exp_unmapped = update_canonical_names(
        db_path, 'Exporter', exporter_mapping, 'exporter'
    )

    # Update importers
    imp_updated, imp_unmapped = update_canonical_names(
        db_path, 'Importer', importer_mapping, 'importer'
    )

    # Verify
    verify_updates(db_path)

    # Final summary
    print(f"\n{Colors.BOLD}{Colors.GREEN}{'='*80}")
    print(f"{'UPDATE COMPLETE':^80}")
    print(f"{'='*80}{Colors.RESET}")
    print(f"{Colors.BRIGHT_CYAN}Exporters updated:{Colors.RESET} {Colors.BRIGHT_GREEN}{exp_updated:,}{Colors.RESET}")
    print(f"{Colors.BRIGHT_CYAN}Importers updated:{Colors.RESET} {Colors.BRIGHT_GREEN}{imp_updated:,}{Colors.RESET}")
    print(f"\n{Colors.DIM}The database now uses vt-normalize canonical names!{Colors.RESET}\n")


if __name__ == '__main__':
    main()
