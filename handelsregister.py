#!/usr/bin/env python3
"""
bundesAPI/handelsregister is the command-line interface for the shared register of companies portal for the German federal states.
You can query, download, automate and much more, without using a web browser.
"""

from __future__ import annotations

# Standard library imports
import argparse
import hashlib
import json as json_module
import logging
import pathlib
import re
import sys
import tempfile
import time
import urllib.error
import urllib.parse
from dataclasses import dataclass, field
from typing import Optional

# Third-party imports
import mechanize
from bs4 import BeautifulSoup
from bs4.element import Tag

# Configure module logger
logger = logging.getLogger(__name__)

# Cache configuration
DEFAULT_CACHE_TTL_SECONDS: int = 3600  # 1 hour default TTL


# Custom Exceptions
class HandelsregisterError(Exception):
    """Base exception for all Handelsregister errors."""
    pass


class NetworkError(HandelsregisterError):
    """Raised when a network request fails."""
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error


class ParseError(HandelsregisterError):
    """Raised when HTML parsing fails."""
    def __init__(self, message: str, html_snippet: Optional[str] = None):
        super().__init__(message)
        self.html_snippet = html_snippet


class FormError(HandelsregisterError):
    """Raised when form interaction fails."""
    pass


class CacheError(HandelsregisterError):
    """Raised when cache operations fail."""
    pass


# Dictionaries to map arguments to values
schlagwortOptionen: dict[str, int] = {
    "all": 1,
    "min": 2,
    "exact": 3
}


@dataclass
class CacheEntry:
    """Represents a cached search result with metadata."""
    query: str
    options: str
    timestamp: float
    html: str
    
    def is_expired(self, ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS) -> bool:
        """Check if the cache entry has expired.
        
        Args:
            ttl_seconds: Time-to-live in seconds.
            
        Returns:
            True if the entry is expired, False otherwise.
        """
        return (time.time() - self.timestamp) > ttl_seconds
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'query': self.query,
            'options': self.options,
            'timestamp': self.timestamp,
            'html': self.html
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CacheEntry':
        """Create a CacheEntry from a dictionary."""
        return cls(
            query=data['query'],
            options=data['options'],
            timestamp=data['timestamp'],
            html=data['html']
        )


@dataclass
class HistoryEntry:
    """Represents a historical name/location entry for a company."""
    name: str
    location: str


@dataclass
class Company:
    """Represents a company record from the Handelsregister."""
    court: str
    name: str
    state: str
    status: str
    status_normalized: str
    documents: str
    register_num: Optional[str] = None
    history: list[HistoryEntry] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for backward compatibility."""
        return {
            'court': self.court,
            'register_num': self.register_num,
            'name': self.name,
            'state': self.state,
            'status': self.status,
            'statusCurrent': self.status_normalized,
            'documents': self.documents,
            'history': [(h.name, h.location) for h in self.history]
        }

class HandelsRegister:
    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.browser: mechanize.Browser = mechanize.Browser()

        self.browser.set_debug_http(args.debug)
        self.browser.set_debug_responses(args.debug)
        # self.browser.set_debug_redirects(True)

        self.browser.set_handle_robots(False)
        self.browser.set_handle_equiv(True)
        self.browser.set_handle_gzip(True)
        self.browser.set_handle_refresh(False)
        self.browser.set_handle_redirect(True)
        self.browser.set_handle_referer(True)

        self.browser.addheaders = [
            (
                "User-Agent",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.5 Safari/605.1.15",
            ),
            (   "Accept-Language", "en-GB,en;q=0.9"   ),
            (   "Accept-Encoding", "gzip, deflate, br"    ),
            (
                "Accept",
                "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            ),
            (   "Connection", "keep-alive"    ),
        ]
        
        self.cachedir: pathlib.Path = pathlib.Path(tempfile.gettempdir()) / "handelsregister_cache"
        self.cachedir.mkdir(parents=True, exist_ok=True)

    def open_startpage(self) -> None:
        """Open the Handelsregister start page.
        
        Raises:
            NetworkError: If the connection fails or times out.
        """
        try:
            self.browser.open("https://www.handelsregister.de", timeout=10)
        except urllib.error.URLError as e:
            raise NetworkError(
                f"Failed to connect to handelsregister.de: {e.reason}",
                original_error=e
            ) from e
        except mechanize.BrowserStateError as e:
            raise NetworkError(
                f"Browser state error: {e}",
                original_error=e
            ) from e

    def _get_cache_key(self, query: str, options: str) -> str:
        """Generate a safe cache key by hashing the query parameters.
        
        Args:
            query: The search query string.
            options: The search options.
            
        Returns:
            A SHA-256 hash of the query parameters.
        """
        key_data = f"{query}|{options}"
        return hashlib.sha256(key_data.encode('utf-8')).hexdigest()
    
    def _get_cache_path(self, query: str, options: str) -> pathlib.Path:
        """Get the cache file path for a query.
        
        Args:
            query: The search query string.
            options: The search options.
            
        Returns:
            Path to the cache file.
        """
        cache_key = self._get_cache_key(query, options)
        return self.cachedir / f"{cache_key}.json"
    
    def _load_from_cache(self, query: str, options: str) -> Optional[CacheEntry]:
        """Load a cache entry if it exists and is not expired.
        
        Args:
            query: The search query string.
            options: The search options.
            
        Returns:
            CacheEntry if valid cache exists, None otherwise.
        """
        cache_path = self._get_cache_path(query, options)
        
        if not cache_path.exists():
            return None
            
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json_module.load(f)
                entry = CacheEntry.from_dict(data)
                
                if entry.is_expired():
                    # Delete expired cache file
                    try:
                        cache_path.unlink()
                    except OSError:
                        pass
                    return None
                    
                return entry
        except (OSError, json_module.JSONDecodeError, KeyError) as e:
            # Invalid cache file - delete it
            logger.warning("Invalid cache file, removing: %s", e)
            try:
                cache_path.unlink()
            except OSError:
                pass
            return None
    
    def _save_to_cache(self, query: str, options: str, html: str) -> None:
        """Save HTML content to cache.
        
        Args:
            query: The search query string.
            options: The search options.
            html: The HTML content to cache.
        """
        cache_path = self._get_cache_path(query, options)
        entry = CacheEntry(
            query=query,
            options=options,
            timestamp=time.time(),
            html=html
        )
        
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json_module.dump(entry.to_dict(), f)
        except OSError as e:
            logger.warning("Failed to write cache file: %s", e)

    def search_company(self) -> list[dict]:
        """Search for companies matching the provided keywords.
        
        Returns:
            A list of dictionaries containing company information.
            
        Raises:
            NetworkError: If network requests fail.
            FormError: If form selection or submission fails.
            CacheError: If cache read/write operations fail.
            ParseError: If HTML parsing fails.
        """
        query = self.args.schlagwoerter
        options = self.args.schlagwortOptionen
        
        # Try to load from cache
        if not self.args.force:
            cache_entry = self._load_from_cache(query, options)
            if cache_entry is not None:
                logger.info("Returning cached content for query: %s", query)
                return get_companies_in_searchresults(cache_entry.html)
        
        # Fetch fresh data
        # TODO implement token bucket to abide by rate limit
        # Use an atomic counter: https://gist.github.com/benhoyt/8c8a8d62debe8e5aa5340373f9c509c7
        try:
            self.browser.select_form(name="naviForm")
        except mechanize.FormNotFoundError as e:
            raise FormError(f"Navigation form not found. The website structure may have changed: {e}") from e
        
        self.browser.form.new_control('hidden', 'naviForm:erweiterteSucheLink', {'value': 'naviForm:erweiterteSucheLink'})
        self.browser.form.new_control('hidden', 'target', {'value': 'erweiterteSucheLink'})
        
        try:
            self.browser.submit()
        except urllib.error.URLError as e:
            raise NetworkError(f"Failed to submit navigation form: {e.reason}", original_error=e) from e

        logger.debug("Page title after navigation: %s", self.browser.title())

        try:
            self.browser.select_form(name="form")
        except mechanize.FormNotFoundError as e:
            raise FormError(f"Search form not found. The website structure may have changed: {e}") from e

        self.browser["form:schlagwoerter"] = query
        so_id = schlagwortOptionen.get(options)

        self.browser["form:schlagwortOptionen"] = [str(so_id)]

        try:
            response_result = self.browser.submit()
        except urllib.error.URLError as e:
            raise NetworkError(f"Failed to submit search form: {e.reason}", original_error=e) from e

        logger.debug("Page title after search: %s", self.browser.title())

        html = response_result.read().decode("utf-8")
        
        # Save to cache
        self._save_to_cache(query, options, html)

        # TODO catch the situation if there's more than one company?
        # TODO get all documents attached to the exact company
        # TODO parse useful information out of the PDFs
        
        return get_companies_in_searchresults(html)


# Mapping of states to register type suffixes
SUFFIX_MAP: dict[str, dict[str, str]] = {
    'Berlin': {'HRB': ' B'},
    'Bremen': {'HRA': ' HB', 'HRB': ' HB', 'GnR': ' HB', 'VR': ' HB', 'PR': ' HB'}
}


def parse_result(result: Tag) -> dict:
    """Parse a single search result row into a company dictionary.
    
    Args:
        result: A BeautifulSoup Tag representing a table row.
        
    Returns:
        A dictionary containing company information.
        
    Raises:
        ParseError: If the result row has unexpected structure.
    """
    cells: list[str] = [cell.text.strip() for cell in result.find_all('td')]
    
    if len(cells) < 6:
        raise ParseError(
            f"Expected at least 6 cells in result row, got {len(cells)}",
            html_snippet=str(result)[:500]
        )
    
    court = cells[1]
    
    # Extract register number: HRB, HRA, VR, GnR followed by numbers (e.g. HRB 12345, VR 6789)
    # Also capture suffix letter if present (e.g. HRB 12345 B), but avoid matching start of words (e.g. " Formerly")
    reg_match = re.search(r'(HRA|HRB|GnR|VR|PR)\s*\d+(\s+[A-Z])?(?!\w)', court)
    register_num: Optional[str] = reg_match.group(0) if reg_match else None

    state = cells[3]
    status = cells[4].strip()
    
    # Ensure consistent register number suffixes (e.g. ' B' for Berlin HRB, ' HB' for Bremen)
    if register_num:
        reg_type = register_num.split()[0]
        suffix = SUFFIX_MAP.get(state, {}).get(reg_type)
        if suffix and not register_num.endswith(suffix):
            register_num += suffix
    
    # Parse history entries
    history: list[tuple[str, str]] = []
    hist_start = 8
    for i in range(hist_start, len(cells), 3):
        if i + 1 >= len(cells):
            break
        if "Branches" in cells[i] or "Niederlassungen" in cells[i]:
            break
        history.append((cells[i], cells[i + 1]))
    
    return {
        'court': court,
        'register_num': register_num,
        'name': cells[2],
        'state': state,
        'status': status,
        'statusCurrent': status.upper().replace(' ', '_'),
        'documents': cells[5],
        'history': history
    }


def pr_company_info(c: dict) -> None:
    """Print company information to stdout.
    
    Args:
        c: A dictionary containing company information.
    """
    for tag in ('name', 'court', 'register_num', 'district', 'state', 'statusCurrent'):
        print(f"{tag}: {c.get(tag, '-')}")
    print('history:')
    for name, loc in c.get('history', []):
        print(name, loc)


def get_companies_in_searchresults(html: str) -> list[dict]:
    """Extract company records from search results HTML.
    
    Args:
        html: The HTML content of the search results page.
        
    Returns:
        A list of dictionaries, each containing company information.
    """
    soup = BeautifulSoup(html, 'html.parser')
    grid = soup.find('table', role='grid')
    
    results: list[dict] = []
    if grid is None:
        return results
        
    for result in grid.find_all('tr'):
        data_ri = result.get('data-ri')
        if data_ri is not None:
            d = parse_result(result)
            results.append(d)
    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='A handelsregister CLI')
    parser.add_argument(
                          "-d",
                          "--debug",
                          help="Enable debug mode and activate logging",
                          action="store_true"
                        )
    parser.add_argument(
                          "-f",
                          "--force",
                          help="Force a fresh pull and skip the cache",
                          action="store_true"
                        )
    parser.add_argument(
                          "-s",
                          "--schlagwoerter",
                          help="Search for the provided keywords",
                          required=True,
                          default="Gasag AG" # TODO replace default with a generic search term
                        )
    parser.add_argument(
                          "-so",
                          "--schlagwortOptionen",
                          help="Keyword options: all=contain all keywords; min=contain at least one keyword; exact=contain the exact company name.",
                          choices=["all", "min", "exact"],
                          default="all"
                        )
    parser.add_argument(
                          "-j",
                          "--json",
                          help="Return response as JSON",
                          action="store_true"
                        )
    args = parser.parse_args()

    # Configure logging based on debug flag
    if args.debug:
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            stream=sys.stdout
        )
        # Also enable mechanize debug logging
        mechanize_logger = logging.getLogger("mechanize")
        mechanize_logger.setLevel(logging.DEBUG)
    else:
        logging.basicConfig(
            level=logging.WARNING,
            format='%(levelname)s: %(message)s'
        )

    return args

def main() -> int:
    """Main entry point for the CLI.
    
    Returns:
        Exit code (0 for success, non-zero for errors).
    """
    import json
    args = parse_args()
    
    try:
        h = HandelsRegister(args)
        h.open_startpage()
        companies = h.search_company()
        
        if companies is not None:
            if args.json:
                print(json.dumps(companies))
            else:
                for c in companies:
                    pr_company_info(c)
        return 0
        
    except NetworkError as e:
        print(f"Network error: {e}", file=sys.stderr)
        if args.debug and e.original_error:
            print(f"Original error: {e.original_error}", file=sys.stderr)
        return 1
        
    except FormError as e:
        print(f"Form error: {e}", file=sys.stderr)
        return 2
        
    except ParseError as e:
        print(f"Parse error: {e}", file=sys.stderr)
        if args.debug and e.html_snippet:
            print(f"HTML snippet: {e.html_snippet}", file=sys.stderr)
        return 3
        
    except CacheError as e:
        print(f"Cache error: {e}", file=sys.stderr)
        return 4
        
    except HandelsregisterError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
