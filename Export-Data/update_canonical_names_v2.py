#!/usr/bin/env python3
"""
Update Database with VT-Normalize Canonical Names (V2)

Uses the actual normalization functions instead of exact lookups.
This handles all the text normalization logic automatically.
"""

import sqlite3
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.exporter_mapping import get_canonical_name
from core.importer_mapping import get_canonical_importer
from vt_normalize.config import Colors


def update_canonical_exporters(db_path: str):
    """Update canonical_exporter column using normalization functions."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}")
    print(f"{'UPDATING EXPORTER CANONICAL NAMES':^80}")
    print(f"{'='*80}{Colors.RESET}")

    # Get all unique exporters
    cursor.execute('SELECT DISTINCT Exporter FROM exports WHERE Exporter IS NOT NULL AND Exporter != ""')
    exporters = [row[0] for row in cursor.fetchall()]

    print(f"{Colors.BRIGHT_CYAN}Total unique exporters:{Colors.RESET} {Colors.BRIGHT_WHITE}{len(exporters):,}{Colors.RESET}")
    print(f"{Colors.CYAN}Processing...{Colors.RESET}")

    # Update each exporter
    for idx, exporter in enumerate(exporters, 1):
        canonical = get_canonical_name(exporter)
        cursor.execute(
            'UPDATE exports SET canonical_exporter = ? WHERE Exporter = ?',
            (canonical, exporter)
        )

        if idx % 50 == 0 or idx == len(exporters):
            print(f"  Progress: {idx}/{len(exporters)} exporters processed...", end='\r')

    print()  # New line after progress
    conn.commit()

    # Get statistics
    cursor.execute('SELECT COUNT(DISTINCT canonical_exporter) FROM exports WHERE canonical_exporter IS NOT NULL')
    unique_canonical = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM exports WHERE canonical_exporter IS NOT NULL')
    records_updated = cursor.fetchone()[0]

    print(f"\n{Colors.BRIGHT_GREEN}✓{Colors.RESET} {Colors.CYAN}Canonical exporters:{Colors.RESET} {Colors.BRIGHT_WHITE}{unique_canonical:,}{Colors.RESET}")
    print(f"{Colors.BRIGHT_GREEN}✓{Colors.RESET} {Colors.CYAN}Records updated:{Colors.RESET} {Colors.BRIGHT_WHITE}{records_updated:,}{Colors.RESET}")

    conn.close()
    return len(exporters), unique_canonical


def update_canonical_importers(db_path: str):
    """Update canonical_importer column using normalization functions."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}")
    print(f"{'UPDATING IMPORTER CANONICAL NAMES':^80}")
    print(f"{'='*80}{Colors.RESET}")

    # Get all unique importers
    cursor.execute('SELECT DISTINCT Importer FROM exports WHERE Importer IS NOT NULL AND Importer != ""')
    importers = [row[0] for row in cursor.fetchall()]

    print(f"{Colors.BRIGHT_CYAN}Total unique importers:{Colors.RESET} {Colors.BRIGHT_WHITE}{len(importers):,}{Colors.RESET}")
    print(f"{Colors.CYAN}Processing...{Colors.RESET}")

    # Update each importer
    for idx, importer in enumerate(importers, 1):
        canonical = get_canonical_importer(importer)
        cursor.execute(
            'UPDATE exports SET canonical_importer = ? WHERE Importer = ?',
            (canonical, importer)
        )

        if idx % 50 == 0 or idx == len(importers):
            print(f"  Progress: {idx}/{len(importers)} importers processed...", end='\r')

    print()  # New line after progress
    conn.commit()

    # Get statistics
    cursor.execute('SELECT COUNT(DISTINCT canonical_importer) FROM exports WHERE canonical_importer IS NOT NULL')
    unique_canonical = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM exports WHERE canonical_importer IS NOT NULL')
    records_updated = cursor.fetchone()[0]

    print(f"\n{Colors.BRIGHT_GREEN}✓{Colors.RESET} {Colors.CYAN}Canonical importers:{Colors.RESET} {Colors.BRIGHT_WHITE}{unique_canonical:,}{Colors.RESET}")
    print(f"{Colors.BRIGHT_GREEN}✓{Colors.RESET} {Colors.CYAN}Records updated:{Colors.RESET} {Colors.BRIGHT_WHITE}{records_updated:,}{Colors.RESET}")

    conn.close()
    return len(importers), unique_canonical


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
        print(f"  {Colors.BRIGHT_YELLOW}{i:2d}.{Colors.RESET} {Colors.BRIGHT_WHITE}{name:35}{Colors.RESET} {Colors.GREEN}{count:,}{Colors.RESET} records")

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
        print(f"  {Colors.BRIGHT_YELLOW}{i:2d}.{Colors.RESET} {Colors.BRIGHT_WHITE}{name:35}{Colors.RESET} {Colors.GREEN}{count:,}{Colors.RESET} records")

    conn.close()


def main():
    """Main update pipeline."""
    db_path = 'exports.db'

    print(f"\n{Colors.BOLD}{Colors.MAGENTA}{'='*80}")
    print(f"{'VT-NORMALIZE DATABASE UPDATE (V2)':^80}")
    print(f"{'='*80}{Colors.RESET}")
    print(f"\n{Colors.CYAN}Using normalization functions for complete coverage{Colors.RESET}\n")

    # Update exporters
    exp_raw, exp_canonical = update_canonical_exporters(db_path)

    # Update importers
    imp_raw, imp_canonical = update_canonical_importers(db_path)

    # Verify
    verify_updates(db_path)

    # Calculate reductions
    exp_reduction = ((exp_raw - exp_canonical) / exp_raw * 100) if exp_raw > 0 else 0
    imp_reduction = ((imp_raw - imp_canonical) / imp_raw * 100) if imp_raw > 0 else 0

    # Final summary
    print(f"\n{Colors.BOLD}{Colors.GREEN}{'='*80}")
    print(f"{'UPDATE COMPLETE':^80}")
    print(f"{'='*80}{Colors.RESET}")
    print(f"\n{Colors.BRIGHT_CYAN}Exporters:{Colors.RESET}")
    print(f"  Raw names: {exp_raw:,}")
    print(f"  Canonical: {exp_canonical:,}")
    print(f"  Reduction: {exp_raw - exp_canonical:,} ({exp_reduction:.1f}%)")
    print(f"\n{Colors.BRIGHT_CYAN}Importers:{Colors.RESET}")
    print(f"  Raw names: {imp_raw:,}")
    print(f"  Canonical: {imp_canonical:,}")
    print(f"  Reduction: {imp_raw - imp_canonical:,} ({imp_reduction:.1f}%)")
    print(f"\n{Colors.DIM}The database now uses vt-normalize canonical names!{Colors.RESET}\n")


if __name__ == '__main__':
    main()
