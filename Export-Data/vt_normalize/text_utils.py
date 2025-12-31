import re
import unicodedata

from vt_normalize.config import STOP_WORDS, SUFFIX_PATTERN


# ==============================================================================
# TEXT NORMALIZATION FUNCTIONS
# ==============================================================================

def remove_accents(text: str) -> str:
    """Removes diacritics (accents) from text."""
    if not isinstance(text, str):
        return str(text)
    nfd = unicodedata.normalize('NFD', text)
    return ''.join(char for char in nfd if unicodedata.category(char) != 'Mn')


def fix_encoding_issues(text: str) -> str:
    """
    Fix common encoding corruption patterns in company names.
    - Replace ? with apostrophe when between letters (NATURE?S -> NATURE'S)
    - Handle common mojibake patterns (DA??ARTA, Ã?)
    """
    if not isinstance(text, str):
        return str(text)

    # Replace ? with apostrophe when between word characters
    text = re.sub(r'(\w)\?(\w)', r"\1'\2", text)

    # Replace ?? with empty string (double corruption)
    text = re.sub(r'\?\?', '', text)

    # Handle Ã? patterns (common UTF-8 corruption)
    text = re.sub(r'Ã\?', '', text)

    return text


def clean_company_name(name: str, strip_legal: bool = True, remove_addresses: bool = True) -> str:
    """
    Standard normalization for company names.
    1. Fixes encoding issues (? -> apostrophe, etc.)
    2. Converts to uppercase
    3. Removes accents
    4. Normalizes punctuation (.. -> space, etc.)
    5. Removes apostrophes (joins words like D'ARTA -> DARTA)
    6. Strips legal suffixes like S.A., LLC, B.V., etc.
    7. Removes other punctuation
    8. Optionally removes address fragments
    9. Merges single-letter prefixes with next word (D ARTA -> DARTA)
    10. Normalizes whitespace
    """
    if not name:
        return ""

    # 1. Fix encoding corruption FIRST
    clean = fix_encoding_issues(name)

    # 2. Basic normalization
    clean = remove_accents(clean).upper().strip()

    # 3. Normalize punctuation
    # Multiple dots to single space
    clean = re.sub(r'\.{2,}', ' ', clean)
    # Normalize slashes with spaces around them (A / S -> A S, but keep A/S)
    clean = re.sub(r'\s+/\s+', ' ', clean)

    # 5. Replace apostrophes with nothing (to join words like D'ARTA -> DARTA)
    # This must happen before removing other punctuation to avoid creating spaces
    clean = re.sub(r"['\u2019]", '', clean)  # Both straight and curly apostrophes

    # 6. Strip legal suffixes using pattern-based approach
    if strip_legal:
        # First, apply explicit suffix list for common forms
        clean = SUFFIX_PATTERN.sub('', clean)

        # Pattern-based cleanup for legal forms that appear at the end
        # These patterns are more robust than listing every variation

        # Polish: SP + Z + O variations (sp. z o.o., sp.z.o.o, sp z o o, etc.)
        # Matches: SP (optional space/dot) Z (optional space/dot) O (optional space/dot) O (optional dot)
        # This handles: SP Z O O, SP. Z O.O, SP.Z.O.O, SP. Z.O.O, etc.
        clean = re.sub(r'\bSP\s*\.?\s*Z\s*\.?\s*O\s*\.?\s*O?\.?\s*$', '', clean, flags=re.IGNORECASE)
        clean = re.sub(r'\bSP\s*\.?\s*Z\s*\.?\s*O\s*\.?\s*O?\.?\b', '', clean, flags=re.IGNORECASE)

        # Czech/Slovak: S.R.O variations (s.r.o., sro, s r o, s.r.o, etc.)
        clean = re.sub(r'\bS\s*\.?\s*R\s*\.?\s*O\.?\s*\.?$', '', clean, flags=re.IGNORECASE)

        # Indian/Commonwealth: PVT/PTY variations (anywhere in string)
        clean = re.sub(r'\bP[TV]Y\s*\.?\s*LTD?\.?\b', '', clean, flags=re.IGNORECASE)  # PTY LTD, PVY LTD
        clean = re.sub(r'\bPVT\s*\.?\s*LTD?\.?\b', '', clean, flags=re.IGNORECASE)  # PVT LTD, PVT
        clean = re.sub(r'\bP[TV]Y\s*\.?\b', '', clean, flags=re.IGNORECASE)  # Standalone PTY, PVY
        clean = re.sub(r'\bPVT\s*\.?\b', '', clean, flags=re.IGNORECASE)  # Standalone PVT
        clean = re.sub(r'\bPRIVATE\s+LIMITED\b', '', clean, flags=re.IGNORECASE)

        # Generic single/double letter suffixes at end that weren't caught
        # Match things like "OSP", "AS", "AB" when they're clearly legal forms
        clean = re.sub(r'\b(OSP|OOO)\s*\.?$', '', clean, flags=re.IGNORECASE)

    # 7. Remove other special chars (keep alphanumeric and spaces)
    clean = re.sub(r'[^\w\s]', ' ', clean)

    # 7.5. Clean up legal suffixes that may have been split by punctuation removal
    # After removing dots, "B.V." becomes "B V", "N.V." becomes "N V", "D.O.O" becomes "D O O", etc.
    clean = re.sub(r'\b([BNSAOLD])\s+([VARLPO])\b', r'\1\2', clean)  # B V -> BV, N V -> NV, S A -> SA, D O -> DO, etc.

    # Now remove the rejoined forms if they're legal suffixes
    if strip_legal:
        clean = re.sub(r'\b(BV|NV|SA|SL|AB|OY|AG|KG|SPA|DOO|DO)\b', '', clean, flags=re.IGNORECASE)
        # Clean up any remaining single O/A/L at end (from split legal forms like D.O.O, S.P.A, etc.)
        clean = re.sub(r'\s+[OAL]\s*$', '', clean)

    # 8. Remove address-like fragments using pattern-based approach
    if remove_addresses:
        # Remove common address indicators
        clean = re.sub(r'\b(C|CO)\s+O\b', '', clean, flags=re.IGNORECASE)  # C/O, CO

        # Remove street suffixes (matches anything ending in STRASSE, STRAAT, etc.)
        clean = re.sub(r'\b\w+(STRASSE|STRAAT|STREET|STR)\b', '', clean, flags=re.IGNORECASE)

        # Remove postal codes and similar number patterns
        clean = re.sub(r'\b\d{4,6}\b', '', clean)  # 4-6 digit postal codes
        clean = re.sub(r'\b[A-Z]{1,2}\s*\d{2,6}\b', '', clean)  # UK/Swiss style (CH 4052, B 8850, etc.)

        # Remove office/unit designations
        clean = re.sub(r'\b(SUITE|STE|UNIT|UL|FLOOR|FL)\s+\w+\b', '', clean, flags=re.IGNORECASE)
        clean = re.sub(r'\b\d+\s*(ST|ND|RD|TH)\s+FL(OOR)?\b', '', clean, flags=re.IGNORECASE)

        # Remove PO Box patterns
        clean = re.sub(r'\bP\s*O\s*(BOX|BO)\s*\d*\b', '', clean, flags=re.IGNORECASE)

        # Remove tax/registration IDs (RUT, EORI, etc.)
        clean = re.sub(r'\b(RUT|EORI|VAT|TAX|ID)\s*\d+\b', '', clean, flags=re.IGNORECASE)

        # Remove street number + direction (123 N, 456 WEST, etc.)
        clean = re.sub(r'\b\d+\s*[NSEW](ORTH|OUTH|AST|EST)?\b', '', clean, flags=re.IGNORECASE)

        # Remove standalone numbers at end (often truncated addresses)
        clean = re.sub(r'\s+\d+\s*$', '', clean)

        # Remove trailing truncated words (likely cut-off addresses like "SWITZERLAN")
        # This catches cases where text was truncated mid-word
        clean = re.sub(r'\s+[A-Z]{3,}$', lambda m: '' if m.group().strip() in STOP_WORDS else m.group(), clean)

    # 9. Merge single-letter prefixes with the next word (D ARTA -> DARTA)
    # BUT don't merge conjunctions like Y, O, E - keep them as separate words
    words = clean.split()
    merged_words = []
    i = 0
    while i < len(words):
        word = words[i]
        # If this is a single letter and not the last word
        if len(word) == 1 and i + 1 < len(words):
            # Don't merge Spanish/Portuguese conjunctions - keep them separate
            # "ALIMENTOS Y FRUTOS" stays as "ALIMENTOS Y FRUTOS", not "ALIMENTOS YFRUTOS"
            if word in {'Y', 'O', 'E'}:  # Only conjunctions, not all STOP_WORDS
                merged_words.append(word)
                i += 1
            else:
                # Merge with next word (e.g., "D" + "ARTA" -> "DARTA")
                merged_words.append(word + words[i + 1])
                i += 2  # Skip the next word since we merged it
        else:
            merged_words.append(word)
            i += 1

    return ' '.join(merged_words)


def get_canonical_brand_name(name: str) -> str:
    """
    Extract the canonical brand name by removing TRAILING stop words (countries, legal terms, etc.)
    but keeping brand identity words like FRUIT, FOOD, FROZEN, etc.
    Leading stop words are preserved as they're part of the brand (e.g., "PERUVIAN IMPORT").

    This is used for the final canonical name display, not for clustering.

    Example:
    'AGRANA FRUIT MEXICO S.A. DE C.V.' -> 'AGRANA FRUIT'
    'ARDO GOURIN S.A.S.' -> 'ARDO'
    'WESTFALIA FRUIT UK LTD' -> 'WESTFALIA FRUIT'
    'ALIMENTOS Y FRUTOS S.A.' -> 'ALIMENTOS Y FRUTOS'
    'IMPORTADORA Y COMERCIALIZADORA SABOR PERUANO' -> 'SABOR PERUANO'
    'DARTA FROZEN FOODS BELGIUM' -> 'DARTA FROZEN FOODS'
    'PERUVIAN IMPORT CO INC' -> 'PERUVIAN IMPORT'  # Keeps leading PERUVIAN
    'SUNSHINE EXPORT PERU' -> 'SUNSHINE' # Removes trailing PERU
    """
    cleaned = clean_company_name(name, strip_legal=True)
    words = cleaned.split()

    # Create stop words set excluding conjunctions (Y, O, E are part of brand names)
    stop_words_no_conjunctions = STOP_WORDS - {'Y', 'O', 'E'}

    # Remove trailing stop words (working backwards from the end)
    # Keep leading stop words as they're part of the brand identity
    while words and words[-1] in stop_words_no_conjunctions:
        words.pop()

    # Remove trailing single-letter words (except conjunctions)
    while words and len(words[-1]) == 1 and words[-1] not in {'Y', 'O', 'E'}:
        words.pop()

    # Remove leading generic descriptors (IMPORTADORA, EXPORTADORA, COMERCIAL, etc.)
    # These are always generic, never part of brand
    leading_generics = {'IMPORTADORA', 'EXPORTADORA', 'COMERCIAL', 'COMERCIALIZADORA', 'SOCIEDAD', 'EMPRESA', 'AGRICOLA', 'AGRO', 'GRUPO', 'GROUP'}
    while words and words[0] in leading_generics:
        words.pop(0)

    # Remove leading/trailing conjunctions (Y, O, E should only be between words)
    while words and words[0] in {'Y', 'O', 'E'}:
        words.pop(0)
    while words and words[-1] in {'Y', 'O', 'E'}:
        words.pop()

    return ' '.join(words) if words else ""


def normalize_spacing_for_comparison(name: str) -> str:
    """
    Remove all spaces for fuzzy comparison only.
    Helps match brand names with spacing variations like FOOD FELLAS vs FOODFELLAS.

    This is only used for comparison, not for display.
    """
    return name.replace(' ', '')


def get_core_name(name: str) -> str:
    """
    Extracts the 'distinctive' part of the name (the core brand identifier).
    Removes leading generic descriptors and trailing stop words.
    Preserves leading country/brand identifiers (e.g., PERUVIAN).
    Returns first 1-2 significant words to focus on the core brand name.

    Example:
    'SOCIEDAD AGRICOLA VIRU S.A.' -> 'VIRU'
    'AGRANA FRUIT MEXICO S.A. DE C.V.' -> 'AGRANA FRUIT'
    'ARDO GOURIN S.A.S.' -> 'ARDO'
    'WESTFALIA FRUIT UK LTD' -> 'WESTFALIA FRUIT'
    "D'ARTA" -> 'DARTA'
    'PERUVIAN IMPORT CO INC' -> 'PERUVIAN IMPORT'
    'SUNSHINE EXPORT PERU' -> 'SUNSHINE EXPORT'
    """
    cleaned = clean_company_name(name, strip_legal=True)
    words = cleaned.split()

    # Remove leading generic descriptors (always generic)
    leading_generics = {'IMPORTADORA', 'EXPORTADORA', 'COMERCIAL', 'COMERCIALIZADORA', 'SOCIEDAD', 'EMPRESA', 'AGRICOLA', 'AGRO', 'GRUPO', 'GROUP'}
    while words and words[0] in leading_generics:
        words.pop(0)

    # Remove trailing stop words
    while words and words[-1] in STOP_WORDS:
        words.pop()

    # Return first 1-2 significant words (length > 1)
    # This gives enough context for brand identity while keeping similar brands grouped
    significant_words = [w for w in words if len(w) > 1]

    if significant_words:
        return ' '.join(significant_words[:2])

    # Fallback: return first word if available
    return words[0] if words else ""
