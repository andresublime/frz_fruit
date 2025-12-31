from fuzzywuzzy import fuzz

from vt_normalize.models import CompanyName
from vt_normalize.text_utils import (
    clean_company_name,
    get_canonical_brand_name,
    get_core_name,
    normalize_spacing_for_comparison
)
from vt_normalize.config import (
    FUZZY_THRESHOLD_WITHIN_GROUP,
    FUZZY_THRESHOLD_CROSS_GROUP,
    FUZZY_THRESHOLD_SPACING
)


def select_canonical_name(variations: list[tuple[str, int]]) -> str:
    """
    Select the best canonical name from variations.
    Prioritizes the most frequent variant, but prefers more complete names.
    Returns the canonical brand name with stop words removed.
    """
    if not variations:
        return "UNKNOWN"

    # Sort by count (descending), then by length (descending)
    sorted_vars = sorted(variations, key=lambda x: (x[1], len(x[0])), reverse=True)
    best_name = sorted_vars[0][0]

    # Return canonical brand name (removes countries, legal terms, keeps brand words)
    return get_canonical_brand_name(best_name)


def cluster_company_names(
    company_names: list[str],
    name_counts: dict[str, int]
) -> list[CompanyName]:
    """
    Cluster company names using core name extraction and fuzzy matching.

    Strategy:
    1. Group names by their core/distinctive word (e.g., 'VIRU', 'SUNSHINE')
    2. Within each core group, use fuzzy matching to find similar variations
    3. Select the most frequent variation as the canonical name
    4. Track all aliases and total shipment counts

    Args:
        company_names: List of company names to cluster
        name_counts: Dictionary mapping company name to occurrence count

    Returns:
        List of CompanyName objects with canonical names and aliases
    """

    # Step 1: Group by core name
    core_groups: dict[str, list[str]] = {}

    for name in company_names:
        core = get_core_name(name)
        if core:
            if core not in core_groups:
                core_groups[core] = []
            core_groups[core].append(name)

    print(f"Grouped into {len(core_groups)} core name groups")

    # Step 2: Within each core group, do fine-grained clustering
    clustered_companies: list[CompanyName] = []

    for core, names_in_group in core_groups.items():
        if len(names_in_group) == 1:
            # Only one variation - simple case
            name = names_in_group[0]
            canonical = get_canonical_brand_name(name)

            clustered_companies.append(CompanyName(
                canonical_name=canonical,
                aliases=[],
                count=name_counts.get(name, 0)
            ))
            continue

        # Multiple variations - cluster them
        processed = set()
        sub_clusters: dict[str, list[str]] = {}

        # Sort by frequency (most common first) to prioritize frequent names as roots
        names_sorted = sorted(names_in_group, key=lambda x: name_counts.get(x, 0), reverse=True)

        for name in names_sorted:
            if name in processed:
                continue

            # Clean the name for comparison
            cleaned_name = clean_company_name(name)

            # This name becomes a cluster root
            sub_clusters[name] = []
            processed.add(name)

            # Find similar names to add as aliases
            for candidate in names_sorted:
                if candidate in processed:
                    continue

                cleaned_candidate = clean_company_name(candidate)

                # Use fuzzy matching on cleaned names
                # Try multiple similarity metrics for better matching
                token_sort_sim = fuzz.token_sort_ratio(cleaned_name, cleaned_candidate)
                token_set_sim = fuzz.token_set_ratio(cleaned_name, cleaned_candidate)

                # Use the higher of the two metrics
                similarity = max(token_sort_sim, token_set_sim)

                # Lower threshold since we're already in the same core group
                # This helps catch variations like "NATURE TOUCH" vs "NATURES TOUCH"
                if similarity >= FUZZY_THRESHOLD_WITHIN_GROUP:
                    sub_clusters[name].append(candidate)
                    processed.add(candidate)

        # Convert sub-clusters to CompanyName objects
        for canonical, aliases in sub_clusters.items():
            # Calculate total count (canonical + all aliases)
            total_count = name_counts.get(canonical, 0)
            total_count += sum(name_counts.get(alias, 0) for alias in aliases)

            # Get all variations with their counts for canonical selection
            all_variations = [(canonical, name_counts.get(canonical, 0))]
            all_variations.extend([(alias, name_counts.get(alias, 0)) for alias in aliases])

            # Select the best canonical name (most frequent, most complete)
            best_canonical = select_canonical_name(all_variations)

            clustered_companies.append(CompanyName(
                canonical_name=best_canonical,
                aliases=aliases,
                count=total_count
            ))

    # Sort by count (most common first)
    clustered_companies.sort(key=lambda x: x.count, reverse=True)

    print(f"Before final merge: {len(clustered_companies)} unique companies")

    # Final merge pass: check for very similar canonical names across different core groups
    # This catches cases like "NATURE TOUCH FROZEN" vs "NATURES TOUCH FROZEN"
    final_merged = []
    processed_indices = set()

    for i, company in enumerate(clustered_companies):
        if i in processed_indices:
            continue

        # Start a new merged group
        merged_group = [company]
        processed_indices.add(i)

        # Look for very similar canonical names
        for j in range(i + 1, len(clustered_companies)):
            if j in processed_indices:
                continue

            other = clustered_companies[j]

            # Calculate similarity between canonical names
            sim = fuzz.token_set_ratio(company.canonical_name, other.canonical_name)

            # Also check similarity without spaces to catch "FOOD FELLAS" vs "FOODFELLAS"
            norm_sim = fuzz.ratio(
                normalize_spacing_for_comparison(company.canonical_name),
                normalize_spacing_for_comparison(other.canonical_name)
            )

            # High threshold for cross-group merging (be conservative but catch obvious variants)
            # 90% catches cases like "HG FOOD" vs "HG FOODS", "DIRAFROST FFI" vs "DIRAFROST FF IN"
            # 95% spacing-normalized catches "FOOD FELLAS" vs "FOODFELLAS"
            if sim >= FUZZY_THRESHOLD_CROSS_GROUP or norm_sim >= FUZZY_THRESHOLD_SPACING:
                merged_group.append(other)
                processed_indices.add(j)

        # Merge the group
        if len(merged_group) == 1:
            final_merged.append(company)
        else:
            # Combine all variations
            all_variations = []
            all_aliases = []
            total_count = 0

            for item in merged_group:
                # Add the canonical name as a variation (using original from aliases if available)
                if item.aliases:
                    all_aliases.extend(item.aliases)
                    # Use the most frequent original name
                    all_variations.append((item.aliases[0], name_counts.get(item.aliases[0], 0)))
                total_count += item.count

            # Select best canonical name from all variations
            if all_variations:
                best_canonical = select_canonical_name(all_variations)
            else:
                best_canonical = merged_group[0].canonical_name

            final_merged.append(CompanyName(
                canonical_name=best_canonical,
                aliases=all_aliases,
                count=total_count
            ))

    # Sort alphabetically by canonical name
    final_merged.sort(key=lambda x: x.canonical_name)

    print(f"After final merge: {len(final_merged)} unique companies")
    return final_merged
