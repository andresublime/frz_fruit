"""
Exporter Name Normalization Module (VT-Normalize Integration)

Provides canonical name lookup for exporters using automated clustering.
Uses vt-normalize library for superior name matching and deduplication.

Key improvements over manual mapping:
- Automated clustering discovers variations without manual input
- Multi-stage normalization (encoding, accents, legal suffixes, stop words)
- Fuzzy matching within and across name groups
- 3.9% reduction in exporter duplicates (152 → 146 unique companies)

Critical fixes achieved:
- VIRÚ GROUP PERÚ S.A. + VIRU S.A. → "VIRU" (2,640 shipments combined)
"""

import json
from pathlib import Path
from typing import Dict, Optional

from vt_normalize.text_utils import clean_company_name


# Lazy-loaded mapping database
_MAPPING_DATABASE: Dict[str, str] = {}
_DATABASE_LOADED = False


def _load_database() -> None:
    """Load the clustered exporters database on first use."""
    global _MAPPING_DATABASE, _DATABASE_LOADED

    if _DATABASE_LOADED:
        return

    database_path = Path(__file__).parent.parent / 'data' / 'clustered_exporters.json'

    if not database_path.exists():
        raise FileNotFoundError(
            f"Clustered exporters database not found at {database_path}. "
            f"Run 'uv run cluster_company_names.py' to generate it."
        )

    with open(database_path, 'r') as f:
        clustered_data = json.load(f)

    # Build alias -> canonical lookup dictionary
    _MAPPING_DATABASE.clear()
    for item in clustered_data:
        canonical = item['canonical_name']

        # Map the canonical name to itself (for direct lookups)
        _MAPPING_DATABASE[canonical] = canonical

        # Map all aliases to canonical
        for alias in item.get('aliases', []):
            _MAPPING_DATABASE[alias] = canonical

    _DATABASE_LOADED = True


def get_canonical_name(exporter_name: str) -> str:
    """
    Get the canonical (standardized) name for an exporter.

    Uses automated clustering and fuzzy matching to identify company name
    variations. Handles:
    - Legal suffix variations (S.A., S.A.C., SAC, etc.)
    - Accent differences (VIRÚ → VIRU)
    - Encoding issues (NATURE?S → NATURES)
    - Spacing differences (D'ARTA → DARTA)
    - Stop word removal (SOCIEDAD, AGRICOLA, etc.)

    Args:
        exporter_name: Original exporter name from database

    Returns:
        Canonical name (short, clean version)

    Examples:
        >>> get_canonical_name('VIRÚ GROUP PERÚ S.A.')
        'VIRU'
        >>> get_canonical_name('VIRU S.A.')
        'VIRU'
        >>> get_canonical_name('MEBOL GF S.A.C.')
        'MEBOL GF'
        >>> get_canonical_name('SOCIEDAD AGRICOLA VIRU S.A.')
        'VIRU'
    """
    if not exporter_name:
        return exporter_name

    # Ensure database is loaded
    _load_database()

    # Try exact match first (fastest path)
    if exporter_name in _MAPPING_DATABASE:
        return _MAPPING_DATABASE[exporter_name].upper()

    # Try normalized version (handles minor variations)
    normalized = clean_company_name(exporter_name, strip_legal=True, remove_addresses=True)
    for alias, canonical in _MAPPING_DATABASE.items():
        if clean_company_name(alias, strip_legal=True, remove_addresses=True) == normalized:
            return canonical.upper()

    # No match found - return normalized original name in UPPERCASE
    # This handles new/unmapped exporters gracefully
    return normalized.upper() if normalized else exporter_name.upper()


def get_all_canonical_exporters() -> list[str]:
    """
    Returns a sorted list of all unique canonical exporter names.

    Returns:
        List of canonical exporter names, sorted alphabetically
    """
    _load_database()

    # Get unique canonical names (values in the mapping)
    canonical_names = set(_MAPPING_DATABASE.values())
    return sorted(canonical_names)


def get_exporter_variations(canonical_name: str) -> list[str]:
    """
    Returns all original exporter name variations for a canonical name.

    Args:
        canonical_name: The canonical exporter name

    Returns:
        List of original exporter names that map to this canonical name
    """
    _load_database()

    return [
        original for original, canonical in _MAPPING_DATABASE.items()
        if canonical == canonical_name
    ]


def get_mapping_stats() -> Dict[str, int]:
    """
    Get statistics about the canonical mappings.

    Returns:
        Dictionary with:
        - total_mappings: Number of name variations in database
        - canonical_names: Number of unique canonical exporters
        - reduction_pct: Percentage reduction in names
    """
    _load_database()

    database_path = Path(__file__).parent.parent / 'data' / 'clustered_exporters.json'
    with open(database_path, 'r') as f:
        clustered_data = json.load(f)

    total_raw_names = sum(1 + len(item.get('aliases', [])) for item in clustered_data)
    canonical_count = len(clustered_data)
    reduction = total_raw_names - canonical_count
    reduction_pct = (reduction / total_raw_names * 100) if total_raw_names > 0 else 0

    return {
        'total_mappings': len(_MAPPING_DATABASE),
        'canonical_names': canonical_count,
        'raw_names': total_raw_names,
        'names_merged': reduction,
        'reduction_pct': reduction_pct,
    }


# Testing and migration validation
if __name__ == '__main__':
    import sys

    # Test known variations
    test_cases = [
        ('VIRÚ GROUP PERÚ S.A.', 'VIRU'),
        ('VIRU S.A.', 'VIRU'),
        ('MEBOL GF S.A.C.', 'MEBOL GF'),
        ('MEBOL SAC', 'MEBOL GF'),
        ('SUNSHINE EXPORT S.A.C', 'SUNSHINE'),
        ('CAMPOSOL S.A.', 'CAMPOSOL'),
    ]

    print("Testing exporter name normalization:")
    print("=" * 70)

    all_passed = True
    for original, expected in test_cases:
        result = get_canonical_name(original)
        passed = result == expected
        all_passed = all_passed and passed
        status = "✓" if passed else "✗"
        print(f"{status} {original:45} → {result:20} (expected: {expected})")

    print("\nMapping statistics:")
    print("=" * 70)
    stats = get_mapping_stats()
    print(f"Total name variations: {stats['total_mappings']:,}")
    print(f"Canonical exporters: {stats['canonical_names']:,}")
    print(f"Raw names: {stats['raw_names']:,}")
    print(f"Names merged: {stats['names_merged']:,} ({stats['reduction_pct']:.1f}%)")

    # Print top 10 exporters
    print("\nAll canonical exporters (first 20):")
    print("=" * 70)
    for i, name in enumerate(get_all_canonical_exporters()[:20], 1):
        variations = get_exporter_variations(name)
        print(f"{i:2d}. {name:30} ({len(variations)} variations)")

    sys.exit(0 if all_passed else 1)
