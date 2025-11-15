"""
Translation mappings for Spanish → English conversions.
"""

# Spanish country names → English
COUNTRY_TRANSLATIONS = {
    # Spanish → English
    'ESTADOS UNIDOS': 'United States',
    'REINO UNIDO': 'United Kingdom',
    'PAÍSES BAJOS': 'Netherlands',
    'ALEMANIA': 'Germany',
    'BÉLGICA': 'Belgium',
    'FRANCIA': 'France',
    'ESPAÑA': 'Spain',
    'ITALIA': 'Italy',
    'PORTUGAL': 'Portugal',
    'SUIZA': 'Switzerland',
    'AUSTRIA': 'Austria',
    'DINAMARCA': 'Denmark',
    'SUECIA': 'Sweden',
    'NORUEGA': 'Norway',
    'FINLANDIA': 'Finland',
    'POLONIA': 'Poland',
    'LETONIA': 'Latvia',
    'LITUANIA': 'Lithuania',
    'ESTONIA': 'Estonia',
    'REPÚBLICA CHECA': 'Czech Republic',
    'HUNGRÍA': 'Hungary',
    'RUMANIA': 'Romania',
    'BULGARIA': 'Bulgaria',
    'GRECIA': 'Greece',
    'IRLANDA': 'Ireland',
    'LUXEMBURGO': 'Luxembourg',
    'ESLOVAQUIA': 'Slovakia',
    'ESLOVENIA': 'Slovenia',
    'CROACIA': 'Croatia',
    'JAPÓN': 'Japan',
    'CHINA': 'China',
    'COREA DEL SUR': 'South Korea',
    'COREA DEL NORTE': 'North Korea',
    'TAIWÁN': 'Taiwan',
    'TAILANDIA': 'Thailand',
    'VIETNAM': 'Vietnam',
    'SINGAPUR': 'Singapore',
    'MALASIA': 'Malaysia',
    'INDONESIA': 'Indonesia',
    'FILIPINAS': 'Philippines',
    'INDIA': 'India',
    'AUSTRALIA': 'Australia',
    'NUEVA ZELANDA': 'New Zealand',
    'CANADÁ': 'Canada',
    'MÉXICO': 'Mexico',
    'BRASIL': 'Brazil',
    'ARGENTINA': 'Argentina',
    'CHILE': 'Chile',
    'PERÚ': 'Peru',
    'COLOMBIA': 'Colombia',
    'VENEZUELA': 'Venezuela',
    'ECUADOR': 'Ecuador',
    'BOLIVIA': 'Bolivia',
    'PARAGUAY': 'Paraguay',
    'URUGUAY': 'Uruguay',
    'COSTA RICA': 'Costa Rica',
    'PANAMÁ': 'Panama',
    'GUATEMALA': 'Guatemala',
    'HONDURAS': 'Honduras',
    'EL SALVADOR': 'El Salvador',
    'NICARAGUA': 'Nicaragua',
    'REPÚBLICA DOMINICANA': 'Dominican Republic',
    'PUERTO RICO': 'Puerto Rico',
    'CUBA': 'Cuba',
    'JAMAICA': 'Jamaica',
    'HAITÍ': 'Haiti',
    'ISRAEL': 'Israel',
    'EMIRATOS ÁRABES UNIDOS': 'United Arab Emirates',
    'ARABIA SAUDITA': 'Saudi Arabia',
    'EGIPTO': 'Egypt',
    'SUDÁFRICA': 'South Africa',
    'KENIA': 'Kenya',
    'MARRUECOS': 'Morocco',
    'RUSIA': 'Russia',
    'UCRANIA': 'Ukraine',
}

# Create reverse mapping (English → Spanish)
COUNTRY_TRANSLATIONS_REVERSE = {v: k for k, v in COUNTRY_TRANSLATIONS.items()}

# Add common English variations
COUNTRY_TRANSLATIONS_REVERSE.update({
    'USA': 'ESTADOS UNIDOS',
    'US': 'ESTADOS UNIDOS',
    'UK': 'REINO UNIDO',
    'UAE': 'EMIRATOS ÁRABES UNIDOS',
})


def translate_country_to_english(spanish_name: str) -> str:
    """
    Translate Spanish country name to English.

    Args:
        spanish_name: Country name in Spanish

    Returns:
        English country name, or original if no translation found
    """
    return COUNTRY_TRANSLATIONS.get(spanish_name.upper(), spanish_name)


def translate_country_to_spanish(english_name: str) -> str:
    """
    Translate English country name to Spanish.

    Args:
        english_name: Country name in English

    Returns:
        Spanish country name, or original if no translation found
    """
    # Try exact match first (with original case)
    if english_name in COUNTRY_TRANSLATIONS_REVERSE:
        return COUNTRY_TRANSLATIONS_REVERSE[english_name]
    # Try uppercase version
    if english_name.upper() in COUNTRY_TRANSLATIONS_REVERSE:
        return COUNTRY_TRANSLATIONS_REVERSE[english_name.upper()]
    # Try title case
    if english_name.title() in COUNTRY_TRANSLATIONS_REVERSE:
        return COUNTRY_TRANSLATIONS_REVERSE[english_name.title()]
    # Not found, return uppercase
    return english_name.upper()


def normalize_country_name(name: str) -> str:
    """
    Normalize a country name to Spanish (for database queries).
    Tries English first, then returns as-is if not found.

    Args:
        name: Country name in any language

    Returns:
        Normalized Spanish country name for database lookup
    """
    # Try reverse lookup first (English → Spanish)
    spanish = translate_country_to_spanish(name)
    if spanish != name.upper():
        return spanish

    # Already Spanish or unknown, return uppercase
    return name.upper()
