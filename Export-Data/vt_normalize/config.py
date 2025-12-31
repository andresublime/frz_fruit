import re


# ==============================================================================
# TERMINAL COLORS
# ==============================================================================

class Colors:
    """ANSI color codes for terminal output"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

    # Foreground colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'

    # Bright foreground colors
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'

    # Background colors
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'


# ==============================================================================
# NAME CLEANING CONSTANTS
# ==============================================================================

# Generic business prefixes that are NOT part of the unique brand identity
STOP_WORDS = {
    'SOCIEDAD', 'SOC', 'SOC.',
    'CORPORACION', 'CORP', 'CORP.',
    'GRUPO', 'GROUP',
    'AGRICOLA', 'AGRO', 'AGROINDUSTRIAL',
    'EXPORTADORA', 'EXPORT',
    'CONSORCIO',
    'IMPORTADORA', 'IMPORT',
    'COMERCIAL', 'COMERCIALIZADORA',
    'COMPANIA', 'CIA', 'CIA.',
    'EMPRESA',
    'NEGOCIOS',
    'INVERSIONES',
    'THE',
    'ASOCIACION',

    # Countries and locations (not part of brand identity)
    'MEXICO', 'MEXICAN', 'MEXICANA',
    'USA', 'US', 'UNITED', 'STATES',
    'UK', 'UNITED', 'KINGDOM',
    'CHILE', 'CHILEAN', 'CHILENA',
    'PERU', 'PERUVIAN', 'PERUANA',
    'ARGENTINA', 'ARGENTINIAN', 'ARGENTINA',
    'BRAZIL', 'BRAZILIAN', 'BRASILEIRA',
    'COLOMBIA', 'COLOMBIAN', 'COLOMBIANA',
    'ECUADOR', 'ECUADORIAN', 'ECUATORIANA',
    'SPAIN', 'SPANISH', 'ESPANA', 'ESPANOLA',
    'POLAND', 'POLISH', 'POLSKA',
    'GERMANY', 'GERMAN', 'DEUTSCHLAND',
    'FRANCE', 'FRENCH', 'FRANCAISE',
    'ITALY', 'ITALIAN', 'ITALIANA',
    'NETHERLANDS', 'DUTCH', 'NEDERLAND',
    'BELGIUM', 'BELGIAN', 'BELGIQUE',
    'KOREA', 'KOREAN',
    'CHINA', 'CHINESE',
    'JAPAN', 'JAPANESE',
    'INDIA', 'INDIAN',
    'AUSTRALIA', 'AUSTRALIAN',
    'SWITZERLAND', 'SWISS', 'CH',  # CH is Swiss country code
    'AUSTRIA', 'AUSTRIAN',
    'CZECH', 'CZECHIA',
    'SLOVAKIA', 'SLOVAK',

    # Generic descriptors that appear after brand name
    'DE', 'CV', 'SDE', 'RL',  # Mexican/Spanish legal terms
    'FLOOR', 'BUILDING', 'STREET', 'AVENUE', 'ROAD',
    'NORTH', 'SOUTH', 'EAST', 'WEST',

    # Additional location/legal identifiers
    'AS',  # Norwegian legal entity (Aksjeselskap)
    'CO', 'COMPANY',

    # Legal/operational terms
    'DBA',  # Doing Business As
    'JOINTLY', 'SEVERALLY', 'WITH',
    'SITE', 'FACILITY', 'BRANCH', 'OFFICE',
    'PRIVATE', 'PUBLIC',
    'INTERNATIONAL', 'INTL',  # Generic scope descriptors

    # Spanish/Portuguese conjunctions
    'Y', 'O', 'E',  # AND, OR variants

    # Address components
    'CARE', 'OF',  # C/O pattern

    # City/facility names that appear after brand name
    'GOURIN',  # City in France (ARDO facility)
    'ASHFORD',  # City in UK
    'ARDOOIE',  # City in Belgium
    'CHARING',  # City in UK
    'KENT',  # County in UK
    'BASEL',  # City in Switzerland
    'SWITZERLAN',  # Truncated "Switzerland"
}

# Invalid company names that should be filtered out
INVALID_NAMES = {
    'UNKNOWN',
    'VARIOUS',
    'TBD',
    'TBA',
    'PENDING',
    'NA',
    'N/A',
    'NONE',
}

# Legal entity suffixes to strip during cleaning
# Note: Pattern-based cleanup in clean_company_name() handles most spacing variations
# This list focuses on compound forms and distinct suffixes
LEGAL_SUFFIXES = [
    # Latin America / Spain - Compound forms (must come before simple forms)
    'S.A. DE C.V.', 'SA DE CV',  # Mexican
    'S DE R.L. DE C.V.', 'S DE RL DE CV',
    'SOCIEDAD ANONIMA CERRADA',
    'SOCIEDAD ANONIMA',

    # Latin America / Spain - Simple forms
    'S.A.C.', 'SAC',
    'S.A.', 'SA',
    'E.I.R.L.', 'EIRL',
    'S.R.L.', 'SRL',
    'LTDA', 'LIMITADA',
    'S.C.R.L.', 'SCRL',

    # International / English
    'LIMITED', 'LTD.',  'LTD',
    'INCORPORATED', 'INC.', 'INC',
    'CORPORATION', 'CORP.', 'CORP',
    'L.L.C.', 'LLC',
    'PLC.',  'PLC',

    # Europe - Compound forms (must come before simple forms)
    'GMBH & CO. KG', 'GMBH & CO KG',  # German
    'SPOLKA Z OGRANICZONA ODPOWIEDZIALNOSCIA',  # Polish (full)

    # Europe - Simple forms
    'GMBH', 'AG', 'KG',  # German
    'B.V.', 'BV',  # Dutch
    'N.V.', 'NV',  # Dutch
    'S.P.A.', 'SPA',  # Italian
    'S.L.U.', 'SLU',  # Spanish
    'S.L.', 'SL',  # Spanish
    'AB', 'OY',  # Swedish/Finnish
    'A/S',  # Nordic (note: "AS" removed as it conflicts with "AS" in company names)

    # French
    'S.A.R.L.', 'SARL',
    'SASU', 'SAS',

    # Polish - Most common forms (pattern-based cleanup handles variations)
    'SP. Z O.O.', 'SPZOO',

    # Czech/Slovak
    'S.R.O.', 'SRO',

    # Balkans (Serbia, Croatia, Bosnia)
    'D.O.O.', 'DOO',  # Društvo s Ograničenom Odgovornošću
]

# Compile regex for efficiency (sort by length desc to catch longest suffixes first)
SUFFIX_PATTERN = re.compile(
    r'\b(' + '|'.join(re.escape(s) for s in sorted(LEGAL_SUFFIXES, key=len, reverse=True)) + r')\b\.?',
    re.IGNORECASE
)


# ==============================================================================
# CLUSTERING THRESHOLDS
# ==============================================================================

# Fuzzy matching thresholds for clustering
FUZZY_THRESHOLD_WITHIN_GROUP = 80  # Within same core group
FUZZY_THRESHOLD_CROSS_GROUP = 90   # Across different core groups
FUZZY_THRESHOLD_SPACING = 95       # Spacing-normalized comparison
