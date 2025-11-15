"""
Exporter Name Normalization Module

Handles canonicalization of company names to resolve spelling variations,
legal suffixes, and accent differences.

Critical fixes:
- VIRÚ GROUP PERÚ S.A. + VIRU S.A. → "Viru" (2,640 shipments combined)
- MEBOL GF S.A.C. + MEBOL SAC → "Mebol" (698 shipments combined)
"""

import re
import unicodedata
from typing import Dict, Optional


# Manual canonical mappings for known companies
# Format: {original_name: canonical_name}
CANONICAL_MAPPINGS: Dict[str, str] = {
    # VIRU variations (2,640 shipments total)
    'VIRÚ GROUP PERÚ S.A.': 'Viru',
    'VIRU S.A.': 'Viru',
    'VIRU GROUP PERU S.A.': 'Viru',
    'VIRU': 'Viru',

    # MEBOL variations (698 shipments total)
    'MEBOL GF S.A.C.': 'Mebol',
    'MEBOL SAC': 'Mebol',
    'MEBOL S.A.C.': 'Mebol',
    'MEBOL': 'Mebol',

    # Other major exporters (canonical short names)
    'SUNSHINE EXPORT S.A.C': 'Sunshine Export',
    'AGROINDUSTRIAS AIB S.A': 'AIB',
    'CAMPOSOL S.A.': 'Camposol',
    'AGRICOLA Y GANADERA CHAVIN DE HUANTAR SA': 'Chavin de Huantar',
    'AGROINDUSTRIA FRUTOS DE ORO S.A.C.': 'Frutos de Oro',
    'DOMINUS S.A.C': 'Dominus',
    'FRUTÍCOLA OLMUÉ PERÚ S.A.C.': 'Frutícola Olmué',
    'FRUTÍCOLA OLMUE PERU S.A.C.': 'Frutícola Olmué',
    'EXPORTACIONES MIRSA EMPRESA INDIVIDUAL D': 'Exportaciones Mirsa',
    'FRUTOS TROPICALES PERU EXPORT SOCIEDAD A': 'Frutos Tropicales Peru',
    'AMARA FOODS S.A.C.': 'Amara Foods',
    'AGRICOLA LOS MEDANOS S.A.': 'Agricola Los Medanos',
    'DEL ANDE ALIMENTOS S.A.C.': 'Del Ande Alimentos',
    'ARA FOODS INDUSTRY S.A.C.': 'Ara Foods',
    'UNION DE NEGOCIOS CORPORATIVOS SOCIEDAD ANONIMA CERRADA': 'Union de Negocios Corporativos',
    'QUICORNAC S.A.C.': 'Quicornac',
    'PROCESADORA PERU SOCIEDAD ANONIMA CERRADA': 'Procesadora Peru',
    'DANPER TRUJILLO S.A.C.': 'Danper',
    'FRUTOS TONGORRAPE SOCIEDAD ANONIMA': 'Frutos Tongorrape',
    'AGROEMPAQUES S.A.': 'Agroempaques',
    'FUSION FOODS S.A.C.': 'Fusion Foods',
    'WESTFALIA FRUIT PERÚ S.A.C.': 'Westfalia Fruit',
    'WESTFALIA FRUIT PERU S.A.C.': 'Westfalia Fruit',
    'ELITE FOOD PERU S.A.C.': 'Elite Food Peru',
    'AGRO FROST S.A.C.': 'Agro Frost',
    'PULPAS Y PROCESADOS DEL AGRO SOCIEDAD ANONIMA-PULPAGRO': 'Pulpagro',
    'AGROMAR INDUSTRIAL S.A.': 'Agromar Industrial',
    'AGROVISION PERU S.A.C.': 'Agrovision Peru',
    'GRUPO TAVARI S.A.C.': 'Grupo Tavari',
    'FRUTICAL S.A.C.': 'Frutical',
    'IMPORTADORA Y EXPORTADORA DOÑA ISABEL E.': 'Doña Isabel',
    'PROCESADORA LARAN SAC': 'Procesadora Laran',
    'LAMAS IMPORT EXPORT S.A.C.': 'Lamas Import Export',
    'COMPLEJO AGROINDUSTRIAL BETA S.A.': 'Beta',
    'MIRANDA - LANGA AGRO EXPORT S.A.C - MIRANDA - LANGA S.A.C': 'Miranda-Langa',
    'MIRANDA - LANGA AGRO EXPORT S.A.C': 'Miranda-Langa',
    'P & M FRUITS S.A.C.': 'P&M Fruits',
    'THE GREEN FARMER S.A.C.': 'The Green Farmer',
    'ANDEAN SUPERFOOD SOCIEDAD COMERCIAL DE RESPONSABILIDAD LIMITADA': 'Andean Superfood',
    'SANTA SOFIA DEL SUR S.A.C.': 'Santa Sofia del Sur',
    'MAPA LOGISTICA INTERNACIONAL SAC': 'Mapa Logistica',
    "NITHO'S COMPANY S.A.C.": "Nitho's Company",
    'AGROFRUTOS TRADING S.A.': 'Agrofrutos Trading',
    'MONDO IMPRENDITORE S.A.C.': 'Mondo Imprenditore',
    'HONEST FOODS S.A.C.': 'Honest Foods',
    'KARLINI INTERNATIONAL FOODS S.A.C.': 'Karlini Foods',
    'BELMONT FOODS PERU S.A.C.': 'Belmont Foods',
    'CFRUITS PERU E.I.R.L.': 'CFruits Peru',
    'COTRINA EXPORTS EMPRESA INDIVIDUAL DE RESPONSABILIDAD LIMITADA - COTRINA EXPORTS E.I.R.L.': 'Cotrina Exports',
}


# Legal suffixes to strip for fuzzy matching
LEGAL_SUFFIXES = [
    'S.A.C.',
    'S.A.C',
    'SAC',
    'S.A.',
    'SA',
    'S.R.L.',
    'SRL',
    'E.I.R.L.',
    'E.I.R.L',
    'EIRL',
    'SOCIEDAD ANONIMA CERRADA',
    'SOCIEDAD ANONIMA',
    'SOCIEDAD COMERCIAL DE RESPONSABILIDAD LIMITADA',
    'EMPRESA INDIVIDUAL DE RESPONSABILIDAD LIMITADA',
    'EMPRESA INDIVIDUAL D',
]


def remove_accents(text: str) -> str:
    """Remove accents from text (e.g., Ú → U)."""
    nfd = unicodedata.normalize('NFD', text)
    return ''.join(char for char in nfd if unicodedata.category(char) != 'Mn')


def strip_legal_suffix(name: str) -> str:
    """Remove common legal suffixes from company names."""
    name_upper = name.upper().strip()

    for suffix in LEGAL_SUFFIXES:
        # Try to match suffix at the end, with optional trailing punctuation
        pattern = r'\s*' + re.escape(suffix) + r'\.?\s*$'
        name_upper = re.sub(pattern, '', name_upper, flags=re.IGNORECASE)

    return name_upper.strip()


def normalize_whitespace(text: str) -> str:
    """Normalize multiple spaces, tabs, etc. to single space."""
    return ' '.join(text.split())


def get_canonical_name(exporter_name: str) -> str:
    """
    Get the canonical (standardized) name for an exporter.

    Process:
    1. Check exact match in CANONICAL_MAPPINGS
    2. Check accent-insensitive match
    3. Check match after stripping legal suffixes
    4. Return original name if no match found

    Args:
        exporter_name: Original exporter name from database

    Returns:
        Canonical name (short, clean version)

    Examples:
        >>> get_canonical_name('VIRÚ GROUP PERÚ S.A.')
        'Viru'
        >>> get_canonical_name('MEBOL SAC')
        'Mebol'
        >>> get_canonical_name('VIRU')
        'Viru'
    """
    if not exporter_name:
        return exporter_name

    # Clean input
    name = normalize_whitespace(exporter_name.strip())

    # 1. Exact match (fastest)
    if name in CANONICAL_MAPPINGS:
        return CANONICAL_MAPPINGS[name]

    # 2. Accent-insensitive match
    name_no_accent = remove_accents(name)
    for original, canonical in CANONICAL_MAPPINGS.items():
        if remove_accents(original) == name_no_accent:
            return canonical

    # 3. Match after stripping legal suffixes
    name_stripped = strip_legal_suffix(name)
    for original, canonical in CANONICAL_MAPPINGS.items():
        if strip_legal_suffix(original) == name_stripped:
            return canonical

    # 4. No match - return cleaned original (strip suffixes for consistency)
    # This creates a "best effort" canonical name for unmapped exporters
    return strip_legal_suffix(name).title()


def add_canonical_mapping(original_name: str, canonical_name: str) -> None:
    """
    Add a new canonical mapping at runtime.

    Useful for handling new exporter names discovered during analysis.

    Args:
        original_name: The name as it appears in the database
        canonical_name: The standardized short name to use
    """
    CANONICAL_MAPPINGS[original_name] = canonical_name


def get_all_mappings() -> Dict[str, str]:
    """
    Get all canonical mappings.

    Returns:
        Dictionary of {original_name: canonical_name}
    """
    return CANONICAL_MAPPINGS.copy()


def get_mapping_stats() -> Dict[str, int]:
    """
    Get statistics about the canonical mappings.

    Returns:
        Dictionary with:
        - total_mappings: Number of explicit mappings defined
        - canonical_names: Number of unique canonical names
    """
    return {
        'total_mappings': len(CANONICAL_MAPPINGS),
        'canonical_names': len(set(CANONICAL_MAPPINGS.values())),
    }


# Testing
if __name__ == '__main__':
    # Test known variations
    test_cases = [
        ('VIRÚ GROUP PERÚ S.A.', 'Viru'),
        ('VIRU S.A.', 'Viru'),
        ('MEBOL GF S.A.C.', 'Mebol'),
        ('MEBOL SAC', 'Mebol'),
        ('SUNSHINE EXPORT S.A.C', 'Sunshine Export'),
        ('CAMPOSOL S.A.', 'Camposol'),
    ]

    print("Testing exporter name normalization:")
    print("=" * 60)
    for original, expected in test_cases:
        result = get_canonical_name(original)
        status = "✓" if result == expected else "✗"
        print(f"{status} {original:40} → {result}")

    print("\nMapping statistics:")
    print("=" * 60)
    stats = get_mapping_stats()
    print(f"Total mappings: {stats['total_mappings']}")
    print(f"Unique canonical names: {stats['canonical_names']}")
