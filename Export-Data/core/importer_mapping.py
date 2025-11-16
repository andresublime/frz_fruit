"""
Canonical importer name mappings.

This module provides a mapping from various importer name variations
to their canonical (standardized) forms. This is necessary because
importer names are often entered inconsistently.

Key principles for canonical names:
1. Remove unnecessary punctuation
2. Keep names simple and readable
3. Use title case for better readability
4. Standardize legal entity suffixes (NV, LLC, Ltd, etc.)
"""

# Mapping from original importer names to canonical forms
IMPORTER_MAPPING = {
    # Salud Foodgroup Europe (647 shipments)
    "SALUD FOODGROUP EUROPE B.V": "Salud Foodgroup Europe",
    "SALUD FOODGROUP EUROPE B.V.": "Salud Foodgroup Europe",
    "SALUD FOODGROUP EUROPE B V": "Salud Foodgroup Europe",
    "SALUD FOODGROUP EUROPE BV": "Salud Foodgroup Europe",
    ">SALUD FOODGROUP EUROPE B.V": "Salud Foodgroup Europe",

    # Dole Packaged Foods (364 shipments)
    "DOLE PACKAGED FOODS. LLC": "Dole Packaged Foods",
    "Dole Packaged Foods. LLC": "Dole Packaged Foods",
    "DOLE PACKAGED FOODS LLC": "Dole Packaged Foods",
    "DOLE PACKAGED FOODS LLC .": "Dole Packaged Foods",
    "DOLE PACKAGED FOODS  LLC": "Dole Packaged Foods",
    "DOLE PACKAGED FOODS. LLC.": "Dole Packaged Foods",

    # Nature's Touch Frozen Foods (307 shipments)
    "NATURE'S TOUCH FROZEN FOODS INC": "Natures Touch Frozen Foods",
    "NATURE?S TOUCH FROZEN FOODS INC.": "Natures Touch Frozen Foods",
    "Nature's Touch Frozen Foods Inc.": "Natures Touch Frozen Foods",
    "NATURE'S TOUCH FROZEN FOODS INC.": "Natures Touch Frozen Foods",
    "NATURE?S TOUCH FROZEN FOODS INC": "Natures Touch Frozen Foods",
    "NATURE¿S TOUCH FROZEN FOODS INC.": "Natures Touch Frozen Foods",
    "NATURE S TOUCH FROZEN FOODS INC.": "Natures Touch Frozen Foods",
    "NATURE S TOUCH FROZEN FOODS INC": "Natures Touch Frozen Foods",
    "NATURE¿S TOUCH FROZEN FOODS INC": "Natures Touch Frozen Foods",
    "NATURE´S TOUCH FROZEN FOODS INC.": "Natures Touch Frozen Foods",
    "Nature?s Touch Frozen Foods Inc.": "Natures Touch Frozen Foods",

    # Superior Foods International (289 shipments)
    "SUPERIOR FOODS INTERNATIONAL": "Superior Foods International",
    "Superior Foods International": "Superior Foods International",

    # Viru Iberica (231 shipments - Spain branch)
    "VIRU IBERICA SL": "Viru Iberica",
    "VIRU IBERICA. SL": "Viru Iberica",

    # Camerican International (220 shipments)
    "CAMERICAN INTERNATIONAL INC": "Camerican International",
    "Camerican International. Inc": "Camerican International",
    "Camerican International INC": "Camerican International",
    "CAMERICAN INTERNATIONAL. INC": "Camerican International",
    "Camerican International Inc": "Camerican International",
    "CAMERICAN INTERNATIONAL INC.": "Camerican International",

    # Patagonia Food Group (213 shipments)
    "PATAGONIA FOOD GROUP. LLC": "Patagonia Food Group",
    "Patagonia Food Group. LLC": "Patagonia Food Group",
    "PATAGONIA FOOD GROUP LLC": "Patagonia Food Group",
    "Patagonia Food Group, LLC": "Patagonia Food Group",

    # Lamex Agrifoods (199 shipments)
    "Lamex Agrifoods. Inc.": "Lamex Agrifoods",
    "LAMEX AGRIFOODS. INC.": "Lamex Agrifoods",
    "LAMEX AGRIFOODS INC": "Lamex Agrifoods",
    "LAMEX AGRIFOODS INC.": "Lamex Agrifoods",
    "LAMEX AGRIFOODS. INC": "Lamex Agrifoods",
    "LAMEX Agrifoods Inc": "Lamex Agrifoods",
    "LAMEX AGRIFOODS, INC.": "Lamex Agrifoods",

    # Syros NV (197 shipments)
    "SYROS NV": "Syros",
    "Syros NV": "Syros",
    "Syros NV.": "Syros",
    "SYROS NV .": "Syros",

    # Nature's Touch Frozen Foods (188 shipments - LLC variations)
    "Nature's Touch Frozen Foods LLC": "Natures Touch Frozen Foods",
    "NATURE'S TOUCH FROZEN FOODS LLC": "Natures Touch Frozen Foods",
    "NATURE?S TOUCH FROZEN FOODS LLC": "Natures Touch Frozen Foods",
    "NATURE¿S TOUCH FROZEN FOODS LLC": "Natures Touch Frozen Foods",
    "Nature?s Touch Frozen Foods LLC": "Natures Touch Frozen Foods",
    "NATURE?S TOUCH FROZEN FOODS LLC..": "Natures Touch Frozen Foods",
    "Nature?s Touch Frozen Foods LLC.": "Natures Touch Frozen Foods",
    "NATURE'S TOUCH FROZEN FOODS LLC.": "Natures Touch Frozen Foods",
    "NATURE'S TOUCH FROZEN FOODS  LLC": "Natures Touch Frozen Foods",

    # ASC Co (187 shipments)
    "ASC CO.. LTD": "ASC Co",
    "ASC CO LTD": "ASC Co",
    "ASC CO. LTD": "ASC Co",
    "ASC CO.. LTD.": "ASC Co",
    "ASC CO. LTD.": "ASC Co",
    "ASC CO LTD.": "ASC Co",
    "ASC CO..LTD": "ASC Co",
    "ASC CO., LTD": "ASC Co",

    # HG Food (181 shipments)
    "HG FOOD GMBH": "HG Food",
    "HG Food GmbH": "HG Food",
    "HG FOOD GMBH.": "HG Food",
    "HG FOOD GmbH": "HG Food",
    "HG FOOD GMBH .": "HG Food",

    # VLM Foods USA (172 shipments)
    "VLM FOODS USA LTD": "VLM Foods USA",
    "VLM FOODS USA LTD.": "VLM Foods USA",

    # To Order (171 shipments - generic placeholder)
    "TO ORDER": "To Order",
    "To Order": "To Order",
    "TO ORDER.": "To Order",

    # Natures Touch Frozen Foods - alternate spelling (162 shipments)
    "NATURES TOUCH FROZEN FOODS INC.": "Natures Touch Frozen Foods",
    "NATURES TOUCH FROZEN FOODS INC": "Natures Touch Frozen Foods",
    "Natures Touch Frozen Foods Inc.": "Natures Touch Frozen Foods",

    # Global Food Link (147 shipments)
    "Global FOOD link SL": "Global Food Link",
    "GLOBAL FOOD LINK SL": "Global Food Link",
    "GLOBAL FOOD LINK": "Global Food Link",

    # Kanematsu Corporation (145 shipments)
    "KANEMATSU CORPORATION": "Kanematsu Corporation",
    "KANEMATSU CORPORATION.": "Kanematsu Corporation",

    # Healthy Pac (141 shipments)
    "HEALTHY PAC CORP": "Healthy Pac",
    "HEALTHY PAC CORP.": "Healthy Pac",

    # Valle Frio (116 shipments)
    "VALLE FRIO SPA": "Valle Frio",
    "VALLE FRIO SPA.": "Valle Frio",
    "Valle Frio SpA": "Valle Frio",

    # Fruitrade International (113 shipments)
    "FRUITRADE INTERNATIONAL INC": "Fruitrade International",
    "FRUITRADE INTERNATIONAL INC.": "Fruitrade International",

    # Viru Iberica S.L. - alternate format (108 shipments)
    "VIRU IBERICA. S.L.": "Viru Iberica",
    "VIRU IBERICA. S.L": "Viru Iberica",

    # Ardo Foods (108 shipments)
    "ARDO FOODS NV": "Ardo Foods",
    "Ardo Foods NV": "Ardo Foods",
    "ARDO FOODS NV -": "Ardo Foods",

    # New Alasko Foods (105 shipments - with logistics)
    "NEW ALASKO FOODS. LLC C/O FREEZPAK LOGISTICS": "New Alasko Foods",
    "New Alasko Foods. LLC C/O Freezpak Logistics": "New Alasko Foods",
    "NEW ALASKO FOODS. LLC C O FREEZPAK LOGISTICS": "New Alasko Foods",

    # Darta (92 shipments)
    "D ARTA NV": "Darta",
    "D'ARTA NV": "Darta",
    "DARTA NV": "Darta",
    "D ARTA NV .": "Darta",
    "NV DARTA SA": "Darta",

    # Polarica (91 shipments)
    "POLARICA SP. Z O.O.": "Polarica",
    "POLARICA SP. Z O. O.": "Polarica",
    "POLARICA SP Z.O.O": "Polarica",
    "POLARICA SP. Z O.O": "Polarica",

    # Walmart (89 shipments)
    "WALMART INC": "Walmart",
    "Walmart Inc.": "Walmart",
    "WALMART INC.": "Walmart",

    # E-Mart (89 shipments)
    "E-MART CO.. LTD": "E-Mart",
    "E-MART CO.. LTD.": "E-Mart",
    "E MART CO LTD": "E-Mart",
    "E-MART CO LTD": "E-Mart",
    "E-MART CO., LTD.": "E-Mart",
    "E-MART Co.. Ltd.": "E-Mart",
    "E-MART CO.LTD": "E-Mart",

    # Crops Fruits (87 shipments)
    "CROPS FRUITS NV": "Crops Fruits",
    "Crops Fruits NV": "Crops Fruits",
    "CROP'S FRUITS": "Crops Fruits",
    "Crop's Fruits": "Crops Fruits",

    # Agroindustria Legumex (84 shipments)
    "AGROINDUSTRIA LEGUMEX. S.A.": "Agroindustria Legumex",
    "AGROINDUSTRIA LEGUMEX S.A.": "Agroindustria Legumex",
    "AGROINDUSTRIA LEGUMEX. S.A": "Agroindustria Legumex",

    # New Alasko Foods (84 shipments - standalone)
    "NEW ALASKO FOODS. LLC": "New Alasko Foods",
    "NEW ALASKO FOODS. LLC..": "New Alasko Foods",
    "NEW ALASKO FOODS LLC": "New Alasko Foods",
    "NEW ALASKO FOODS LLC..": "New Alasko Foods",
    "NEW ALASKO FOODS. LLC.": "New Alasko Foods",
    "NEW ALASKO FOODS LLC.": "New Alasko Foods",
    "New Alasko Foods LLC.": "New Alasko Foods",

    # Greenyard Frozen UK (79 shipments)
    "GREENYARD FROZEN UK LTD": "Greenyard Frozen UK",
    "GREENYARD FROZEN UK LTD.": "Greenyard Frozen UK",

    # Caribbean Panafood (72 shipments)
    "CARIBBEAN PANAFOOD CORP.": "Caribbean Panafood",
    "CARIBBEAN PANAFOOD CORP": "Caribbean Panafood",

    # Greenyard Frozen Belgium (70 shipments)
    "GREENYARD FROZEN BELGIUM NV": "Greenyard Frozen Belgium",

    # The Foodfellas (70 shipments)
    "THE FOODFELLAS LTD": "The Foodfellas",

    # JP Trading (63 shipments)
    "JP TRADING AND GLOBAL IMPORTS LLC": "JP Trading and Global Imports",

    # Alta Fruta (61 shipments)
    "ALTA FRUTA SPA": "Alta Fruta",

    # 3 Berry (60 shipments)
    "3 Berry Sp. z o.o": "3 Berry",

    # Vitafoods (57 shipments)
    "VITAFOODS SPA": "Vitafoods",

    # Westfalia Fruit (85 shipments)
    "WESTFALIA FRUIT UK LTD": "Westfalia Fruit UK",

    # Peruvian Import Co (73 shipments)
    "PERUVIAN IMPORT CO INC": "Peruvian Import Co",

    # Foodimpex International (103 shipments)
    "FOODIMPEX INTERNATIONAL AB": "Foodimpex International",
}


def get_canonical_importer(importer_name: str) -> str:
    """
    Returns the canonical importer name for a given importer.

    Args:
        importer_name: The original importer name from the database

    Returns:
        The canonical importer name. If no mapping exists, returns the
        original name with basic cleanup (title case, trimmed).
    """
    if not importer_name:
        return "Unknown"

    # Check if we have an exact mapping
    if importer_name in IMPORTER_MAPPING:
        return IMPORTER_MAPPING[importer_name]

    # Otherwise return the original with basic cleanup
    # Preserve the original capitalization for unmapped names
    return importer_name.strip()


def get_all_canonical_importers() -> list[str]:
    """
    Returns a sorted list of all unique canonical importer names.

    Returns:
        List of canonical importer names, sorted alphabetically
    """
    canonical_names = set(IMPORTER_MAPPING.values())
    return sorted(canonical_names)


def get_importer_variations(canonical_name: str) -> list[str]:
    """
    Returns all original importer name variations for a canonical name.

    Args:
        canonical_name: The canonical importer name

    Returns:
        List of original importer names that map to this canonical name
    """
    return [
        original for original, canonical in IMPORTER_MAPPING.items()
        if canonical == canonical_name
    ]


# Statistics
if __name__ == "__main__":
    print(f"Total importer mappings: {len(IMPORTER_MAPPING)}")
    print(f"Total canonical importers: {len(get_all_canonical_importers())}")
    print(f"\nCanonical importers:")
    for name in get_all_canonical_importers():
        variations = get_importer_variations(name)
        print(f"  {name} ({len(variations)} variations)")
