"""
Parser to extract structured product information from commercial descriptions.
"""
import re
from typing import Optional
from models import FruitProduct, ProductFormat, ProductClassification


class DescriptionParser:
    """Parse commercial descriptions into structured product data."""

    # Fruit detection patterns (Spanish → English)
    # Order matters: Check specific patterns before generic ones
    FRUIT_PATTERNS = {
        'mango': r'\bmango[s]?(?:\b|(?=[A-Z]))',  # Match word boundary or before uppercase (MANGOCILINDROS)
        'pineapple': r'\b(pineapple|piña|pina|ananas)\b',
        'strawberry': r'\b(strawberry|fresa[s]?)\b',
        'blueberry': r'\b(blueberry|arandano[s]?|arándano[s]?)\b',
        'papaya': r'\bpapaya[s]?\b',
        'avocado': r'\b(avocado[s]?|aguacate[s]?|palta[s]?)\b',
        'pomegranate': r'\b(pomegranate|granada[s]?)\b',
        'lucuma': r'\b(lucuma|lúcuma)\b',  # Important Peruvian fruit
        'passion_fruit': r'\b(passion fruit|maracuya|maracuyá)\b',
        'golden_berry': r'\b(golden berry|aguaymanto|physalis)\b',
        'camu_camu': r'\b(camu camu|camu-camu)\b',
        'soursop': r'\b(soursop|guanabana|guanábana)\b',
        'cherimoya': r'\b(cherimoya|chirimoya)\b',
        'pitaya': r'\b(pitaya|pitahaya|dragon fruit)\b',
        'acai': r'\b(acai|açai|acaí)\b',
        'banana': r'\b(banana[s]?|platano[s]?|plátano[s]?|banano)\b',
        'raspberry': r'\b(raspberry|frambuesa[s]?)\b',
        'cherry': r'\b(cherry|cherries|cereza[s]?)\b',
        'peach': r'\b(peach|peaches|durazno[s]?|melocoton|melocotón)\b',
        'grape': r'\b(grape[s]?|uva[s]?)\b',
        'orange': r'\b(orange[s]?|naranja[s]?)\b',
        'mix': r'\b(mix|mixtura|mezcla|berry mix|tropical mix)\b',
    }

    # Variety patterns
    VARIETY_PATTERNS = [
        r'(?:variedad|variety|var)[:\s]+([a-z]+)',
        r'\b(kent|edward|haden|keitt|tommy atkins|ataulfo)\b',
        r'\b(golden|md2|cayenne)\b',  # pineapple varieties
    ]

    # Format patterns (Spanish → English)
    FORMAT_PATTERNS = {
        'chunks': r'\b(chunk[s]?|trozo[s]?|pedazo[s]?|bits and pieces)\b',
        'cubes': r'\b(cube[s]?|cubo[s]?|cubos|dado[s]?|diced|picado[s]?|arilo[s]?)\b',  # diced = cubes, arilos = arils
        'slices': r'\b(slice[s]?|sliced|rebanada[s]?|rodaja[s]?)\b',
        'halves': r'\b(halves|mitades)\b',
        'puree': r'\b(puree|pure|puré)\b',
        'pulp': r'\b(pulp|pulpa)\b',
        'whole': r'\b(whole|entero[s]?|entera[s]?)\b',
        'strips': r'\b(strip[s]?|tira[s]?)\b',
        'broken_pieces': r'\bb\s*&\s*p\b',  # broken & pieces
        'concentrate': r'\b(concentrate|concentrado)\b',
        'juice': r'\b(juice|jugo)\b',
    }

    # Size patterns
    SIZE_PATTERNS = [
        r'(\d+)\s*[xX×]\s*(\d+)\s*(?:mm)?',  # 20x20mm, 20X20, etc.
        r'(\d+)\s*mm\s*[xX×]\s*(\d+)\s*mm',
    ]

    # Classification patterns
    ORGANIC_PATTERNS = r'\b(organic|organico|org)\b'
    CONVENTIONAL_PATTERNS = r'\b(conventional|convencional)\b'
    IQF_PATTERNS = r'\biqf\b'
    ASEPTIC_PATTERNS = r'\b(aseptic|aseptico|aséptico)\b'  # Aseptic processing (not frozen)

    @classmethod
    def parse(cls, description: str) -> FruitProduct:
        """
        Parse a commercial description into structured product data.

        Args:
            description: Commercial description text

        Returns:
            FruitProduct with extracted information
        """
        if not description:
            return FruitProduct(fruit_name="unknown")

        # Normalize text
        desc_lower = description.lower()

        # Clean up repeated text (common in this dataset)
        # Take only the first occurrence
        words = desc_lower.split()
        seen_phrases = set()
        cleaned_words = []
        window_size = 5

        for i in range(len(words)):
            phrase = ' '.join(words[i:min(i+window_size, len(words))])
            if phrase not in seen_phrases:
                cleaned_words.append(words[i])
                seen_phrases.add(phrase)

        desc_clean = ' '.join(cleaned_words)

        # Extract fruit name
        fruit_name = cls._extract_fruit(desc_clean)

        # Extract variety
        variety = cls._extract_variety(desc_clean)

        # Extract format
        product_format = cls._extract_format(desc_clean)

        # Extract classification
        classification = cls._extract_classification(desc_clean)

        return FruitProduct(
            fruit_name=fruit_name,
            variety=variety,
            product_format=product_format,
            classification=classification
        )

    @classmethod
    def _extract_fruit(cls, text: str) -> str:
        """Extract fruit name from text."""
        for fruit, pattern in cls.FRUIT_PATTERNS.items():
            if re.search(pattern, text, re.IGNORECASE):
                return fruit
        return "unknown"

    @classmethod
    def _extract_variety(cls, text: str) -> Optional[str]:
        """Extract fruit variety from text."""
        for pattern in cls.VARIETY_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                variety = match.group(1).strip()
                return variety.title()
        return None

    @classmethod
    def _extract_format(cls, text: str) -> ProductFormat:
        """Extract product format information from text."""
        format_type = None
        size_mm = None

        # Detect IQF first, as it might appear with other formats
        is_iqf = bool(re.search(cls.IQF_PATTERNS, text, re.IGNORECASE))

        # If IQF is mentioned without other format, use it as format
        if is_iqf:
            format_type = "iqf"

        # Check for specific formats
        for fmt, pattern in cls.FORMAT_PATTERNS.items():
            if re.search(pattern, text, re.IGNORECASE):
                format_type = fmt
                break

        # Extract size
        for pattern in cls.SIZE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                size_mm = f"{match.group(1)}x{match.group(2)}"
                break

        # If format still not found but size is present, assume chunks
        if not format_type and size_mm:
            format_type = "chunks"

        return ProductFormat(
            format_type=format_type or "unknown",
            size_mm=size_mm
        )

    @classmethod
    def _extract_classification(cls, text: str) -> ProductClassification:
        """Extract product classification from text."""
        is_organic = bool(re.search(cls.ORGANIC_PATTERNS, text, re.IGNORECASE))
        is_conventional = bool(re.search(cls.CONVENTIONAL_PATTERNS, text, re.IGNORECASE))
        is_iqf = bool(re.search(cls.IQF_PATTERNS, text, re.IGNORECASE))
        is_aseptic = bool(re.search(cls.ASEPTIC_PATTERNS, text, re.IGNORECASE))

        # If neither organic nor conventional is specified, mark as unknown
        certification = "unknown"
        if is_organic:
            certification = "organic"
        elif is_conventional:
            certification = "conventional"

        return ProductClassification(
            is_organic=is_organic,
            is_conventional=is_conventional,
            is_iqf=is_iqf,
            is_aseptic=is_aseptic,
            certification=certification
        )


def parse_description(description: str) -> FruitProduct:
    """
    Convenience function to parse a commercial description.

    Args:
        description: Commercial description text

    Returns:
        FruitProduct with extracted information
    """
    return DescriptionParser.parse(description)
