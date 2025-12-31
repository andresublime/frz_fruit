import json
import os
from collections import Counter

import pandas as pd

from vt_normalize.models import CompanyName
from vt_normalize.clustering import cluster_company_names
from vt_normalize.text_utils import clean_company_name, get_canonical_brand_name
from vt_normalize.config import Colors, INVALID_NAMES


class CompanyNormalizer:
    """
    Company name normalization and clustering system.

    Provides both batch processing (load Excel -> cluster -> save results)
    and individual name lookup (raw name -> canonical name).
    """

    def __init__(self, language: str = 'es'):
        """
        Initialize the CompanyNormalizer.

        Args:
            language: Language code for stop words (currently only 'es' Spanish supported)
        """
        self.language = language
        self._database: dict[str, str] = {}  # Maps alias -> canonical_name

    def process_excel_file(
        self,
        excel_path: str,
        column_name: str,
        output_path: str,
        sheet_name: str = 'Veritrade',
        skiprows: int = 5,
        use_cache: bool = True,
        verbose: bool = True
    ) -> list[CompanyName]:
        """
        Batch processing pipeline: Load Excel -> Extract -> Clean -> Cluster -> Save.

        Args:
            excel_path: Path to Excel file
            column_name: Column name to extract ('Importer' or 'Exporter')
            output_path: Path to save clustered JSON results
            sheet_name: Excel sheet name (default: 'Veritrade')
            skiprows: Number of rows to skip (default: 5)
            use_cache: Use pickle cache if available (default: True)
            verbose: Print statistics and progress (default: True)

        Returns:
            List of CompanyName objects with canonical names and aliases
        """
        if verbose:
            print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}")
            print(f"{'PROCESSING ' + column_name.upper() + 'S':^80}")
            print(f"{'='*80}{Colors.RESET}")

        # Load data
        pickle_path = excel_path.replace('.xlsx', '.pkl')
        if use_cache and os.path.exists(pickle_path):
            table = pd.read_pickle(pickle_path)
            if verbose:
                print(f"{Colors.GREEN}✓{Colors.RESET} Loaded table from cache: {pickle_path}")
        else:
            table = pd.read_excel(excel_path, sheet_name=sheet_name, skiprows=skiprows)
            if use_cache:
                table.to_pickle(pickle_path)
            if verbose:
                print(f"{Colors.GREEN}✓{Colors.RESET} Loaded table from Excel: {excel_path}")

        # Extract names
        names_list, name_counts = self._extract_company_names(
            table, column_name, output_path, verbose
        )

        if verbose:
            print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}")
            print(f"{'CLUSTERING ' + column_name.upper() + 'S':^80}")
            print(f"{'='*80}{Colors.RESET}")

        # Cluster
        clustered = cluster_company_names(names_list, name_counts)

        # Save results
        if verbose:
            self._print_statistics(clustered, name_counts, len(names_list), column_name)

        with open(output_path, "w") as f:
            json.dump([item.model_dump() for item in clustered], f, indent=2)

        if verbose:
            total_shipments = sum(item.count for item in clustered)
            print(f"\n{Colors.BOLD}{Colors.MAGENTA}{'='*80}")
            print(f"{'SAVING RESULTS':^80}")
            print(f"{'='*80}{Colors.RESET}")
            print(f"{Colors.BRIGHT_GREEN}✓{Colors.RESET} {Colors.CYAN}Saved to:{Colors.RESET} {Colors.BRIGHT_WHITE}{output_path}{Colors.RESET}")
            print(f"  {Colors.DIM}Format:{Colors.RESET} {Colors.WHITE}JSON (sorted alphabetically by canonical_name){Colors.RESET}")
            print(f"  {Colors.DIM}Size:{Colors.RESET} {Colors.BRIGHT_YELLOW}{len(clustered):,}{Colors.RESET} {Colors.WHITE}{column_name.lower()}s{Colors.RESET}")
            print(f"  {Colors.DIM}Total records represented:{Colors.RESET} {Colors.BRIGHT_YELLOW}{total_shipments:,}{Colors.RESET}\n")

        return clustered

    def _extract_company_names(
        self,
        table: pd.DataFrame,
        column_name: str,
        output_path: str,
        verbose: bool = True
    ) -> tuple[list[str], dict[str, int]]:
        """Extract company names and their occurrence counts from the table."""
        # Get value counts for all companies in the column
        company_counts = table[column_name].value_counts()

        # Get unique companies (already sorted by frequency via value_counts)
        unique_companies = [x for x in company_counts.index.tolist() if pd.notna(x)]

        # Create a dictionary mapping name -> count
        name_counts = {name: int(count) for name, count in company_counts.items() if pd.notna(name)}

        # Filter out invalid company names
        filtered_companies = []
        filtered_counts = {}

        for name in unique_companies:
            cleaned = clean_company_name(name, strip_legal=True, remove_addresses=True)
            # Skip if the cleaned name is in the invalid list
            if cleaned not in INVALID_NAMES and cleaned.strip():
                filtered_companies.append(name)
                filtered_counts[name] = name_counts[name]

        if verbose:
            filtered_out_count = len(unique_companies) - len(filtered_companies)
            print(f"{Colors.BRIGHT_CYAN}Unique {column_name.lower()}s found:{Colors.RESET} {Colors.BRIGHT_WHITE}{len(unique_companies):,}{Colors.RESET}")
            if filtered_out_count > 0:
                print(f"{Colors.BRIGHT_YELLOW}Invalid names filtered:{Colors.RESET} {Colors.BRIGHT_RED}{filtered_out_count}{Colors.RESET}")
                print(f"{Colors.BRIGHT_CYAN}Valid {column_name.lower()}s:{Colors.RESET} {Colors.BRIGHT_WHITE}{len(filtered_companies):,}{Colors.RESET}")
            print(f"{Colors.BRIGHT_CYAN}Total records:{Colors.RESET} {Colors.BRIGHT_WHITE}{sum(filtered_counts.values()):,}{Colors.RESET}")

        # Save raw names with counts for debugging
        raw_output = output_path.replace('clustered_', 'raw_')
        with open(raw_output, "w") as f:
            output_list = [{"name": name, "count": filtered_counts[name]} for name in sorted(filtered_companies)]
            json.dump(output_list, f, indent=2)
        if verbose:
            print(f"{Colors.DIM}Raw names saved to {raw_output}{Colors.RESET}")

        return filtered_companies, filtered_counts

    def _print_statistics(
        self,
        clustered: list[CompanyName],
        name_counts: dict[str, int],
        total_raw: int,
        entity_type: str
    ):
        """Print comprehensive clustering statistics."""
        total_clustered = len(clustered)
        reduction_count = total_raw - total_clustered
        reduction_pct = (reduction_count / total_raw * 100) if total_raw > 0 else 0

        # Analyze clustering quality
        single_name_clusters = sum(1 for item in clustered if len(item.aliases) == 0)
        multi_name_clusters = total_clustered - single_name_clusters
        total_records = sum(item.count for item in clustered)
        avg_records_per_cluster = total_records / total_clustered if total_clustered > 0 else 0

        # Find largest clusters (by number of aliases)
        largest_clusters = sorted(clustered, key=lambda x: len(x.aliases), reverse=True)[:5]

        # Print comprehensive results
        print(f"\n{Colors.BOLD}{Colors.MAGENTA}{'='*80}")
        print(f"{'CLUSTERING RESULTS SUMMARY':^80}")
        print(f"{'='*80}{Colors.RESET}")
        print(f"{Colors.BRIGHT_CYAN}Raw unique {entity_type.lower()} names:{Colors.RESET}        {Colors.BRIGHT_WHITE}{total_raw:,}{Colors.RESET}")
        print(f"{Colors.BRIGHT_CYAN}Clustered unique {entity_type.lower()}s:{Colors.RESET}       {Colors.BRIGHT_WHITE}{total_clustered:,}{Colors.RESET}")
        print(f"{Colors.BRIGHT_CYAN}Names merged:{Colors.RESET}                     {Colors.BRIGHT_GREEN}{reduction_count:,}{Colors.RESET} {Colors.DIM}({reduction_pct:.1f}%){Colors.RESET}")
        print(f"{Colors.BRIGHT_CYAN}Total records:{Colors.RESET}           {Colors.BRIGHT_WHITE}{total_records:,}{Colors.RESET}")
        print(f"{Colors.BRIGHT_CYAN}Average records per {entity_type.lower()}:{Colors.RESET}   {Colors.BRIGHT_WHITE}{avg_records_per_cluster:.1f}{Colors.RESET}")
        print(f"\n{Colors.YELLOW}Clustering breakdown:{Colors.RESET}")
        print(f"  {Colors.BRIGHT_BLUE}Single-name clusters:{Colors.RESET}           {single_name_clusters:,} {Colors.DIM}({single_name_clusters/total_clustered*100:.1f}%){Colors.RESET}")
        print(f"  {Colors.BRIGHT_BLUE}Multi-name clusters:{Colors.RESET}            {multi_name_clusters:,} {Colors.DIM}({multi_name_clusters/total_clustered*100:.1f}%){Colors.RESET}")

        # Show distribution of cluster sizes
        cluster_sizes = Counter(len(item.aliases) for item in clustered)
        max_size = max(cluster_sizes.keys())
        max_count = max(cluster_sizes.values())

        print(f"\n  {Colors.DIM}Cluster size distribution (variations per cluster):{Colors.RESET}")

        # Braille characters for high-resolution bar chart
        braille_chars = ['⡀', '⡄', '⡆', '⡇', '⣇', '⣧', '⣷', '⣿']

        for size in sorted(cluster_sizes.keys(), reverse=True):
            count = cluster_sizes[size]
            total_names = size + 1  # aliases + canonical = total names in cluster

            # Scale to max 40 chars width
            max_width = 40
            scaled_value = (count / max_count) * max_width

            # Build the bar with Braille characters
            if scaled_value < 1.0:
                partial_index = max(0, int(scaled_value * (len(braille_chars) - 1)))
                bar = braille_chars[partial_index]
            else:
                full_blocks = int(scaled_value)
                remainder = scaled_value - full_blocks
                partial_index = int(remainder * (len(braille_chars) - 1))

                bar = braille_chars[-1] * full_blocks
                if partial_index > 0 and full_blocks < max_width:
                    bar += braille_chars[partial_index]

            print(f"    {Colors.BRIGHT_MAGENTA}{total_names:2d} name{'s' if total_names > 1 else ' '}:{Colors.RESET} {Colors.GREEN}{bar}{Colors.RESET} {Colors.BRIGHT_WHITE}{count:3d}{Colors.RESET} {Colors.DIM}clusters{Colors.RESET}")

        # Show top companies by count
        print(f"\n{Colors.BOLD}{Colors.YELLOW}{'='*80}")
        print(f"{'TOP 10 ' + entity_type.upper() + 'S BY RECORD COUNT':^80}")
        print(f"{'='*80}{Colors.RESET}")
        sorted_by_count = sorted(clustered, key=lambda x: x.count, reverse=True)[:10]
        for i, item in enumerate(sorted_by_count, 1):
            print(f"\n{Colors.BOLD}{Colors.BRIGHT_YELLOW}{i:2d}.{Colors.RESET} {Colors.BRIGHT_WHITE}{item.canonical_name}{Colors.RESET}")
            print(f"    {Colors.CYAN}Records:{Colors.RESET} {Colors.BRIGHT_GREEN}{item.count:,}{Colors.RESET}")
            if item.aliases:
                print(f"    {Colors.CYAN}Aliases:{Colors.RESET} {Colors.BRIGHT_MAGENTA}{len(item.aliases)}{Colors.RESET} {Colors.DIM}variations{Colors.RESET}")
                for alias in item.aliases[:3]:
                    print(f"      {Colors.DIM}•{Colors.RESET} {Colors.WHITE}{alias}{Colors.RESET}")
                if len(item.aliases) > 3:
                    print(f"      {Colors.DIM}... and {len(item.aliases) - 3} more{Colors.RESET}")

    def load_database(self, json_path: str) -> None:
        """
        Load clustering output for fast canonical name lookups.

        Args:
            json_path: Path to clustered JSON file
        """
        with open(json_path, 'r') as f:
            data = json.load(f)

        # Build alias -> canonical lookup dictionary
        self._database.clear()
        for item in data:
            canonical = item['canonical_name']
            # Map all aliases to canonical
            for alias in item.get('aliases', []):
                self._database[alias] = canonical

        print(f"{Colors.GREEN}✓{Colors.RESET} Loaded {len(self._database)} name mappings from {json_path}")

    def get_canonical_name(self, raw_name: str) -> str | None:
        """
        Get canonical name for a raw company name.

        Looks up the raw name in the loaded database and returns the canonical form.

        Args:
            raw_name: Raw company name string

        Returns:
            Canonical company name, or None if not found in database
        """
        if not self._database:
            raise RuntimeError("Database not loaded. Call load_database() first.")

        # Try exact match first
        if raw_name in self._database:
            return self._database[raw_name]

        # Try normalized version
        normalized = clean_company_name(raw_name)
        for alias, canonical in self._database.items():
            if clean_company_name(alias) == normalized:
                return canonical

        return None
