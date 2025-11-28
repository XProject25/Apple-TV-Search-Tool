#!/usr/bin/env python3
"""
Apple TV Search Tool
CLI tool to search Apple TV for Movies and TV Shows (unofficial).

Original idea/structure: @sp4rk.y
Improved & maintained by X Project
"""

import sys
import argparse
import json
from typing import List, Dict, Optional
import requests


__version__ = "1.1.0"
__author__ = "X Project"


class ATVSearch:
    """
    Apple TV Search without authentication.

    You can search by:
      - storefront ID (e.g., "143441")
      - region code (e.g., "US", "GB", "DE")
    """

    STOREFRONTS_URL = "https://uts-api.itunes.apple.com/uts/v3/storefronts"
    SEARCH_URL = "https://uts-api.itunes.apple.com/uts/v3/search"

    def __init__(
        self,
        storefront_id: Optional[str] = None,
        region: Optional[str] = None,
        locale: str = "en-US",
        timeout: int = 10,
        include_people: bool = False,
    ):
        """
        Initialize ATV Search.

        Args:
            storefront_id: Storefront ID (e.g., "143441" for US)
            region: 2-letter country code (e.g., "US", "GB", "CA")
            locale: Locale string (e.g., "en-US", "de-DE")
            timeout: HTTP timeout in seconds
            include_people: Whether to include people/person results
        """
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0 Safari/537.36"
                ),
                "Accept": "application/json",
            }
        )

        self.timeout = timeout
        self.locale = locale
        self.include_people = include_people

        # If region is provided but no storefront_id, try to resolve it
        if region and not storefront_id:
            storefront_id = self.get_storefront_for_region(region)
            if not storefront_id:
                print(
                    f"[!] Warning: Could not find storefront for region '{region}', falling back to US (143441)",
                    file=sys.stderr,
                )
                storefront_id = "143441"

        # Default storefront: US
        if not storefront_id:
            storefront_id = "143441"

        self.storefront_id = storefront_id

        # Base params extracted from web requests (may change over time)
        self.base_params = {
            "locale": self.locale,
            "pfm": "web",
            "sf": self.storefront_id,
            "utscf": "OjAAAAAAAAA~",
            "utsk": "6e3013c6d6fae3c2::::::baf1a0dbeffe95a4",
            "v": "90",
            "caller": "js",
            "suppressAuthentication": "true",
        }

    def get_storefront_for_region(self, region: str) -> Optional[str]:
        """
        Resolve storefront ID for a given 2-letter region code.

        Args:
            region: 2-letter country code (e.g., "US", "GB")

        Returns:
            Storefront ID as string, or None if not found.
        """
        params = {
            "utscf": "OjAAAAAAAAA~",
            "utsk": "6e3013c6d6fae3c2::::::baf1a0dbeffe95a4",
            "caller": "web",
            "sf": "143441",
            "v": "56",
            "pfm": "web",
            "locale": self.locale,
        }

        try:
            resp = self.session.get(
                self.STOREFRONTS_URL, params=params, timeout=self.timeout
            )
            resp.raise_for_status()
            data = resp.json()
            region_data = data.get("data", {}).get(region.upper())
            if region_data:
                return str(region_data.get("storefrontId"))
        except Exception as e:
            print(f"[!] Error fetching storefronts: {e}", file=sys.stderr)

        return None

    @staticmethod
    def _score_result(title: str, query: str, position: int) -> int:
        """
        Compute a relevance score for a result.

        Higher is better.
        """
        title_lower = title.lower()
        query_lower = query.lower()
        score = 0

        # Exact / prefix / contains priority
        if title_lower == query_lower:
            score += 1000
        elif title_lower.startswith(query_lower):
            score += 500
        elif f" {query_lower}" in f" {title_lower}":
            score += 300
        elif query_lower in title_lower:
            score += 200

        # Word-based scoring
        query_words = query_lower.split()
        title_words = title_lower.split()
        for qword in query_words:
            if qword in title_words:
                score += 50

        # Earlier in the list = higher score
        score += max(0, 100 - position)

        return score

    def search(
        self,
        query: str,
        max_results: Optional[int] = None,
        filter_type: Optional[str] = None,
    ) -> List[Dict]:
        """
        Search for content on Apple TV.

        Args:
            query: Search query string
            max_results: Optional maximum number of results to return
            filter_type: Optional filter ("movie", "show") to narrow results

        Returns:
            List of results with fields: score, id, title, type, url
        """
        params = {**self.base_params, "searchTerm": query}

        try:
            resp = self.session.get(self.SEARCH_URL, params=params, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            print(f"[!] Error: Failed to search - {e}", file=sys.stderr)
            return []

        shelves = data.get("data", {}).get("canvas", {}).get("shelves", [])
        if not shelves:
            return []

        results: List[Dict] = []
        seen_ids = set()

        for shelf in shelves:
            shelf_id = shelf.get("id", "")

            # Skip people shelves unless explicitly requested
            if not self.include_people and (
                "PN" in shelf_id or "people" in shelf_id.lower()
            ):
                continue

            items = shelf.get("items", [])

            for position, item in enumerate(items):
                content_id = item.get("id")
                if not content_id or content_id in seen_ids:
                    continue

                seen_ids.add(content_id)

                title = item.get("title", "Unknown")
                content_type = item.get("type", "Unknown")
                localized_type = item.get("localizedType", content_type)
                url = item.get("url", "")

                # Only keep items with valid URL structure
                if not url or (
                    "/show/" not in url
                    and "/movie/" not in url
                    and "/person/" not in url
                ):
                    continue

                # Optional filter: movies or shows
                if filter_type:
                    ft = filter_type.lower()
                    is_movie = "/movie/" in url
                    is_show = "/show/" in url
                    if ft == "movie" and not is_movie:
                        continue
                    if ft in ("show", "series") and not is_show:
                        continue

                score = self._score_result(title, query, position)

                results.append(
                    {
                        "score": score,
                        "id": content_id,
                        "title": title,
                        "type": localized_type,
                        "raw_type": content_type,
                        "url": url,
                    }
                )

        # Sort by score desc, then by title asc
        results.sort(key=lambda x: (-x["score"], x["title"]))

        if max_results is not None and max_results > 0:
            results = results[:max_results]

        return results


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Search Apple TV for Movies and TV Shows (unofficial).\n"
            "Developed by X Project."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python atv_search.py "Foundation"
  python atv_search.py "Ted Lasso" -sf CA
  python atv_search.py "Severance" -sf 143444 --max-results 5
  python atv_search.py "See" -sf DE --type show --json

Common regions:
  US (143441), GB (143444), CA (143455), AU (143460)
  FR (143442), DE (143443), JP (143462), IN (143467)

Developed by X Project
        """,
    )

    parser.add_argument("query", nargs="+", help="Search query string")
    parser.add_argument(
        "-sf",
        "--storefront",
        help=(
            "Storefront ID (e.g., 143441) or 2-letter region code "
            "(e.g., US, GB, CA, DE)"
        ),
        default=None,
    )
    parser.add_argument(
        "-l",
        "--locale",
        help="Locale (e.g., en-US, de-DE, fr-FR). Default: en-US",
        default="en-US",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        help="Maximum number of results to show (default: all)",
        default=None,
    )
    parser.add_argument(
        "--type",
        dest="filter_type",
        choices=["movie", "show", "series"],
        help="Filter only movies or shows",
        default=None,
    )
    parser.add_argument(
        "--include-people",
        action="store_true",
        help="Include people/person results in output",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON only (no pretty text)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="HTTP timeout in seconds (default: 10)",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="store_true",
        help="Show version and exit",
    )

    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    """Main CLI entry point."""
    args = parse_args(argv)

    if args.version:
        print(f"Apple TV Search Tool v{__version__} — Developed by X Project")
        return 0

    query = " ".join(args.query)

    storefront_id: Optional[str] = None
    region: Optional[str] = None

    if args.storefront:
        if args.storefront.isdigit():
            storefront_id = args.storefront
        else:
            region = args.storefront.upper()

    searcher = ATVSearch(
        storefront_id=storefront_id,
        region=region,
        locale=args.locale,
        timeout=args.timeout,
        include_people=args.include_people,
    )

    # Human-friendly info header (suppressed if JSON mode)
    if not args.json:
        print(f"Storefront ID: {searcher.storefront_id}")
        if region:
            print(f"Region:       {region}")
        print(f"Locale:       {args.locale}")
        print(f"Query:        {query}")
        if args.filter_type:
            print(f"Filter type:  {args.filter_type}")
        print("Developed by X Project\n")

    results = searcher.search(
        query=query,
        max_results=args.max_results,
        filter_type=args.filter_type,
    )

    if not results:
        if args.json:
            print("[]")
        else:
            print("No results found.")
        return 0

    if args.json:
        # Strip score if you don't want it; I leave it because it's useful
        print(json.dumps(results, indent=2, ensure_ascii=False))
        return 0

    print(f"Found {len(results)} result(s):\n")

    for i, result in enumerate(results, 1):
        print(f"{i}. {result['title']}")
        print(f"   Type:   {result['type']} ({result['raw_type']})")
        print(f"   ID:     {result['id']}")
        print(f"   Score:  {result['score']}")
        print(f"   URL:    {result['url']}")
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
