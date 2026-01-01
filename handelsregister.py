#!/usr/bin/env python3
"""
bundesAPI/handelsregister is the command-line interface for the shared register of companies portal for the German federal states.
You can query, download, automate and much more, without using a web browser.

Architecture:
    - SearchCache: Handles caching of search results with TTL expiration
    - ResultParser: Parses HTML search results into structured data
    - HandelsRegister: Browser automation for the Handelsregister website
    - CLI: Command-line interface (main, parse_args)
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


# =============================================================================
# Configuration
# =============================================================================

DEFAULT_CACHE_TTL_SECONDS: int = 3600  # 1 hour default TTL
BASE_URL: str = "https://www.handelsregister.de"
REQUEST_TIMEOUT: int = 10

# Mapping of keyword option names to form values
KEYWORD_OPTIONS: dict[str, int] = {
    "all": 1,
    "min": 2,
    "exact": 3
}

# Mapping of states to register type suffixes
SUFFIX_MAP: dict[str, dict[str, str]] = {
    'Berlin': {'HRB': ' B'},
    'Bremen': {'HRA': ' HB', 'HRB': ' HB', 'GnR': ' HB', 'VR': ' HB', 'PR': ' HB'}
}

# German state codes for filtering (bundesland parameters)
STATE_CODES: dict[str, str] = {
    'BW': 'Baden-Württemberg',
    'BY': 'Bayern',
    'BE': 'Berlin',
    'BR': 'Brandenburg',
    'HB': 'Bremen',
    'HH': 'Hamburg',
    'HE': 'Hessen',
    'MV': 'Mecklenburg-Vorpommern',
    'NI': 'Niedersachsen',
    'NW': 'Nordrhein-Westfalen',
    'RP': 'Rheinland-Pfalz',
    'SL': 'Saarland',
    'SN': 'Sachsen',
    'ST': 'Sachsen-Anhalt',
    'SH': 'Schleswig-Holstein',
    'TH': 'Thüringen',
}

# Register types
REGISTER_TYPES: list[str] = ['HRA', 'HRB', 'GnR', 'PR', 'VR']

# Results per page options
RESULTS_PER_PAGE_OPTIONS: list[int] = [10, 25, 50, 100]

# For backward compatibility
schlagwortOptionen = KEYWORD_OPTIONS


# =============================================================================
# Exceptions
# =============================================================================

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


# =============================================================================
# Data Models
# =============================================================================

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
    def from_dict(cls, data: dict) -> CacheEntry:
        """Create a CacheEntry from a dictionary."""
        return cls(
            query=data['query'],
            options=data['options'],
            timestamp=data['timestamp'],
            html=data['html']
        )


@dataclass
class SearchOptions:
    """Encapsulates all search parameters for the Handelsregister.
    
    Attributes:
        keywords: Search keywords (schlagwoerter).
        keyword_option: How to match keywords (all, min, exact).
        states: List of state codes to filter by (e.g., ['BE', 'HH']).
        register_type: Register type filter (HRA, HRB, GnR, PR, VR).
        register_number: Specific register number to search for.
        include_deleted: Include deleted/historical entries.
        similar_sounding: Use phonetic/similarity search.
        results_per_page: Number of results per page (10, 25, 50, 100).
    """
    keywords: str
    keyword_option: str = "all"
    states: Optional[list[str]] = None
    register_type: Optional[str] = None
    register_number: Optional[str] = None
    include_deleted: bool = False
    similar_sounding: bool = False
    results_per_page: int = 100
    
    def cache_key(self) -> str:
        """Generate a unique key for caching based on all options."""
        parts = [
            self.keywords,
            self.keyword_option,
            ",".join(sorted(self.states or [])),
            self.register_type or "",
            self.register_number or "",
            str(self.include_deleted),
            str(self.similar_sounding),
            str(self.results_per_page),
        ]
        return "|".join(parts)


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


# =============================================================================
# Cache Layer
# =============================================================================

class SearchCache:
    """Handles caching of search results with TTL expiration.
    
    Cache files are stored as JSON in a temporary directory with SHA-256
    hashed filenames to prevent path traversal attacks.
    """
    
    def __init__(
        self, 
        cache_dir: Optional[pathlib.Path] = None,
        ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS
    ) -> None:
        """Initialize the cache.
        
        Args:
            cache_dir: Directory to store cache files. Defaults to temp directory.
            ttl_seconds: Time-to-live for cache entries in seconds.
        """
        self.ttl_seconds = ttl_seconds
        self.cache_dir = cache_dir or (
            pathlib.Path(tempfile.gettempdir()) / "handelsregister_cache"
        )
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_key(self, query: str, options: str) -> str:
        """Generate a safe cache key by hashing the query parameters."""
        key_data = f"{query}|{options}"
        return hashlib.sha256(key_data.encode('utf-8')).hexdigest()
    
    def _get_cache_path(self, query: str, options: str) -> pathlib.Path:
        """Get the cache file path for a query."""
        cache_key = self._get_cache_key(query, options)
        return self.cache_dir / f"{cache_key}.json"
    
    def get(self, query: str, options: str) -> Optional[str]:
        """Get cached HTML content if available and not expired.
        
        Args:
            query: The search query string.
            options: The search options.
            
        Returns:
            Cached HTML content, or None if not available.
        """
        cache_path = self._get_cache_path(query, options)
        
        if not cache_path.exists():
            return None
            
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json_module.load(f)
                entry = CacheEntry.from_dict(data)
                
                if entry.is_expired(self.ttl_seconds):
                    self._delete_file(cache_path)
                    return None
                    
                return entry.html
                
        except (OSError, json_module.JSONDecodeError, KeyError) as e:
            logger.warning("Invalid cache file, removing: %s", e)
            self._delete_file(cache_path)
            return None
    
    def set(self, query: str, options: str, html: str) -> None:
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
    
    def _delete_file(self, path: pathlib.Path) -> None:
        """Safely delete a cache file."""
        try:
            path.unlink()
        except OSError:
            pass


# =============================================================================
# Parser Layer
# =============================================================================

class ResultParser:
    """Parses HTML search results into structured company data."""
    
    @staticmethod
    def parse_search_results(html: str) -> list[dict]:
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
            
        for row in grid.find_all('tr'):
            data_ri = row.get('data-ri')
            if data_ri is not None:
                company_data = ResultParser.parse_result_row(row)
                results.append(company_data)
                
        return results
    
    @staticmethod
    def parse_result_row(row: Tag) -> dict:
        """Parse a single search result row into a company dictionary.
        
        Args:
            row: A BeautifulSoup Tag representing a table row.
            
        Returns:
            A dictionary containing company information.
            
        Raises:
            ParseError: If the result row has unexpected structure.
        """
        cells: list[str] = [cell.text.strip() for cell in row.find_all('td')]
        
        if len(cells) < 6:
            raise ParseError(
                f"Expected at least 6 cells in result row, got {len(cells)}",
                html_snippet=str(row)[:500]
            )
        
        court = cells[1]
        state = cells[3]
        status = cells[4].strip()
        
        # Extract register number
        register_num = ResultParser._extract_register_number(court, state)
        
        # Parse history entries
        history = ResultParser._parse_history(cells)
        
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
    
    @staticmethod
    def _extract_register_number(court: str, state: str) -> Optional[str]:
        """Extract and normalize the register number from court string.
        
        Args:
            court: The court field containing the register number.
            state: The state, used to add appropriate suffix.
            
        Returns:
            Normalized register number, or None if not found.
        """
        # Extract register number: HRB, HRA, VR, GnR followed by numbers
        # Also capture suffix letter if present (e.g. HRB 12345 B)
        reg_match = re.search(r'(HRA|HRB|GnR|VR|PR)\s*\d+(\s+[A-Z])?(?!\w)', court)
        
        if not reg_match:
            return None
            
        register_num = reg_match.group(0)
        
        # Add state-specific suffix if needed
        reg_type = register_num.split()[0]
        suffix = SUFFIX_MAP.get(state, {}).get(reg_type)
        if suffix and not register_num.endswith(suffix):
            register_num += suffix
            
        return register_num
    
    @staticmethod
    def _parse_history(cells: list[str]) -> list[tuple[str, str]]:
        """Parse history entries from cell data.
        
        Args:
            cells: List of cell text content.
            
        Returns:
            List of (name, location) tuples.
        """
        history: list[tuple[str, str]] = []
        hist_start = 8
        
        for i in range(hist_start, len(cells), 3):
            if i + 1 >= len(cells):
                break
            if "Branches" in cells[i] or "Niederlassungen" in cells[i]:
                break
            history.append((cells[i], cells[i + 1]))
            
        return history


# Backward-compatible function aliases
def parse_result(result: Tag) -> dict:
    """Parse a single search result row into a company dictionary.
    
    Deprecated: Use ResultParser.parse_result_row() instead.
    """
    return ResultParser.parse_result_row(result)


def get_companies_in_searchresults(html: str) -> list[dict]:
    """Extract company records from search results HTML.
    
    Deprecated: Use ResultParser.parse_search_results() instead.
    """
    return ResultParser.parse_search_results(html)


# =============================================================================
# Browser Layer
# =============================================================================

class HandelsRegister:
    """Browser automation for searching the Handelsregister website.
    
    This class handles all interaction with the Handelsregister website,
    including navigation, form submission, and result retrieval.
    """
    
    def __init__(
        self, 
        args: argparse.Namespace,
        cache: Optional[SearchCache] = None
    ) -> None:
        """Initialize the HandelsRegister client.
        
        Args:
            args: Command-line arguments namespace.
            cache: Optional cache instance. Created automatically if not provided.
        """
        self.args = args
        self.cache = cache or SearchCache()
        self.browser = self._create_browser(debug=args.debug)
    
    def _create_browser(self, debug: bool = False) -> mechanize.Browser:
        """Create and configure a mechanize browser instance.
        
        Args:
            debug: Enable debug output for HTTP requests.
            
        Returns:
            Configured Browser instance.
        """
        browser = mechanize.Browser()
        
        browser.set_debug_http(debug)
        browser.set_debug_responses(debug)
        
        browser.set_handle_robots(False)
        browser.set_handle_equiv(True)
        browser.set_handle_gzip(True)
        browser.set_handle_refresh(False)
        browser.set_handle_redirect(True)
        browser.set_handle_referer(True)
        
        browser.addheaders = [
            ("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.5 Safari/605.1.15"),
            ("Accept-Language", "en-GB,en;q=0.9"),
            ("Accept-Encoding", "gzip, deflate, br"),
            ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
            ("Connection", "keep-alive"),
        ]
        
        return browser
    
    # Backward compatibility: expose cachedir
    @property
    def cachedir(self) -> pathlib.Path:
        """Get the cache directory path."""
        return self.cache.cache_dir
    
    def open_startpage(self) -> None:
        """Open the Handelsregister start page.
        
        Raises:
            NetworkError: If the connection fails or times out.
        """
        try:
            self.browser.open(BASE_URL, timeout=REQUEST_TIMEOUT)
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
    
    def _build_search_options(self) -> SearchOptions:
        """Build SearchOptions from command-line arguments.
        
        Returns:
            SearchOptions instance with all search parameters.
        """
        # Parse state codes if provided
        states = None
        if hasattr(self.args, 'states') and self.args.states:
            states = [s.strip().upper() for s in self.args.states.split(',')]
        
        return SearchOptions(
            keywords=self.args.schlagwoerter,
            keyword_option=self.args.schlagwortOptionen,
            states=states,
            register_type=getattr(self.args, 'register_type', None),
            register_number=getattr(self.args, 'register_number', None),
            include_deleted=getattr(self.args, 'include_deleted', False),
            similar_sounding=getattr(self.args, 'similar_sounding', False),
            results_per_page=getattr(self.args, 'results_per_page', 100),
        )
    
    def search_company(self) -> list[dict]:
        """Search for companies matching the provided keywords.
        
        Returns:
            A list of dictionaries containing company information.
            
        Raises:
            NetworkError: If network requests fail.
            FormError: If form selection or submission fails.
            ParseError: If HTML parsing fails.
        """
        search_opts = self._build_search_options()
        cache_key = search_opts.cache_key()
        
        # Try to load from cache (use cache_key as both query and options for simplicity)
        if not self.args.force:
            cached_html = self.cache.get(cache_key, "")
            if cached_html is not None:
                logger.info("Returning cached content for query: %s", search_opts.keywords)
                return ResultParser.parse_search_results(cached_html)
        
        # Fetch fresh data from website
        html = self._fetch_search_results(search_opts)
        
        # Save to cache
        self.cache.set(cache_key, "", html)
        
        return ResultParser.parse_search_results(html)
    
    def _fetch_search_results(self, search_opts: SearchOptions) -> str:
        """Fetch search results from the website.
        
        Args:
            search_opts: Search options specifying all search parameters.
            
        Returns:
            HTML content of search results page.
            
        Raises:
            NetworkError: If network requests fail.
            FormError: If form selection or submission fails.
        """
        # Navigate to extended search
        self._navigate_to_search()
        
        # Submit search form
        return self._submit_search(search_opts)
    
    def _navigate_to_search(self) -> None:
        """Navigate from start page to extended search form.
        
        Raises:
            FormError: If navigation form is not found.
            NetworkError: If form submission fails.
        """
        try:
            self.browser.select_form(name="naviForm")
        except mechanize.FormNotFoundError as e:
            raise FormError(
                f"Navigation form not found. The website structure may have changed: {e}"
            ) from e
        
        self.browser.form.new_control(
            'hidden', 
            'naviForm:erweiterteSucheLink', 
            {'value': 'naviForm:erweiterteSucheLink'}
        )
        self.browser.form.new_control('hidden', 'target', {'value': 'erweiterteSucheLink'})
        
        try:
            self.browser.submit()
        except urllib.error.URLError as e:
            raise NetworkError(
                f"Failed to submit navigation form: {e.reason}", 
                original_error=e
            ) from e
        
        logger.debug("Page title after navigation: %s", self.browser.title())
    
    def _submit_search(self, search_opts: SearchOptions) -> str:
        """Submit the search form and return results HTML.
        
        Args:
            search_opts: Search options specifying all search parameters.
            
        Returns:
            HTML content of search results page.
            
        Raises:
            FormError: If search form is not found.
            NetworkError: If form submission fails.
        """
        try:
            self.browser.select_form(name="form")
        except mechanize.FormNotFoundError as e:
            raise FormError(
                f"Search form not found. The website structure may have changed: {e}"
            ) from e
        
        # Required: Keywords
        self.browser["form:schlagwoerter"] = search_opts.keywords
        option_id = KEYWORD_OPTIONS.get(search_opts.keyword_option)
        self.browser["form:schlagwortOptionen"] = [str(option_id)]
        
        # Optional: State filtering
        if search_opts.states:
            for state_code in search_opts.states:
                if state_code in STATE_CODES:
                    try:
                        control_name = f"form:bundesland{state_code}"
                        self.browser.form.find_control(control_name).value = ["on"]
                        logger.debug("Enabled state filter: %s", state_code)
                    except mechanize.ControlNotFoundError:
                        logger.warning("State control not found: %s", control_name)
        
        # Optional: Register type
        if search_opts.register_type:
            try:
                self.browser["form:registerArt"] = [search_opts.register_type]
                logger.debug("Set register type: %s", search_opts.register_type)
            except mechanize.ControlNotFoundError:
                logger.warning("Register type control not found")
        
        # Optional: Register number
        if search_opts.register_number:
            try:
                self.browser["form:registerNummer"] = search_opts.register_number
                logger.debug("Set register number: %s", search_opts.register_number)
            except mechanize.ControlNotFoundError:
                logger.warning("Register number control not found")
        
        # Optional: Include deleted entries
        if search_opts.include_deleted:
            try:
                self.browser.form.find_control("form:suchOptionenGeloescht").value = ["true"]
                logger.debug("Enabled include deleted option")
            except mechanize.ControlNotFoundError:
                logger.warning("Include deleted control not found")
        
        # Optional: Similar sounding (phonetic search)
        if search_opts.similar_sounding:
            try:
                self.browser.form.find_control("form:suchOptionenAehnlich").value = ["true"]
                logger.debug("Enabled similar sounding option")
            except mechanize.ControlNotFoundError:
                logger.warning("Similar sounding control not found")
        
        # Optional: Results per page
        if search_opts.results_per_page in RESULTS_PER_PAGE_OPTIONS:
            try:
                self.browser["form:ergebnisseProSeite"] = [str(search_opts.results_per_page)]
                logger.debug("Set results per page: %d", search_opts.results_per_page)
            except mechanize.ControlNotFoundError:
                logger.warning("Results per page control not found")
        
        try:
            response = self.browser.submit()
        except urllib.error.URLError as e:
            raise NetworkError(
                f"Failed to submit search form: {e.reason}", 
                original_error=e
            ) from e
        
        logger.debug("Page title after search: %s", self.browser.title())
        
        return response.read().decode("utf-8")
    
    # Backward compatibility methods
    def _get_cache_key(self, query: str, options: str) -> str:
        """Generate cache key. Deprecated: use cache.get/set instead."""
        return self.cache._get_cache_key(query, options)
    
    def _get_cache_path(self, query: str, options: str) -> pathlib.Path:
        """Get cache path. Deprecated: use cache.get/set instead."""
        return self.cache._get_cache_path(query, options)
    
    def _load_from_cache(self, query: str, options: str) -> Optional[CacheEntry]:
        """Load from cache. Deprecated: use cache.get instead."""
        html = self.cache.get(query, options)
        if html is None:
            return None
        return CacheEntry(query=query, options=options, timestamp=time.time(), html=html)
    
    def _save_to_cache(self, query: str, options: str, html: str) -> None:
        """Save to cache. Deprecated: use cache.set instead."""
        self.cache.set(query, options, html)


# =============================================================================
# CLI Layer
# =============================================================================

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


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.
    
    Returns:
        Parsed arguments namespace.
    """
    state_codes_help = ", ".join(f"{k}={v}" for k, v in sorted(STATE_CODES.items()))
    
    parser = argparse.ArgumentParser(
        description='A handelsregister CLI for the German commercial register',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  %(prog)s -s "Deutsche Bahn" -so all
  %(prog)s -s "GASAG AG" -so exact --json
  %(prog)s -s "Munich" --states BE,BY --register-type HRB
  %(prog)s -s "Bank" --include-deleted --similar-sounding

State codes: {state_codes_help}
        """
    )
    
    # General options
    parser.add_argument(
        "-d", "--debug",
        help="Enable debug mode and activate logging",
        action="store_true"
    )
    parser.add_argument(
        "-f", "--force",
        help="Force a fresh pull and skip the cache",
        action="store_true"
    )
    parser.add_argument(
        "-j", "--json",
        help="Return response as JSON",
        action="store_true"
    )
    
    # Search parameters
    search_group = parser.add_argument_group('Search parameters')
    search_group.add_argument(
        "-s", "--schlagwoerter",
        help="Search for the provided keywords (required)",
        required=True,
        metavar="KEYWORDS"
    )
    search_group.add_argument(
        "-so", "--schlagwortOptionen",
        help="Keyword matching: all=all keywords; min=at least one; exact=exact name",
        choices=["all", "min", "exact"],
        default="all",
        metavar="OPTION"
    )
    search_group.add_argument(
        "--states",
        help="Comma-separated list of state codes to filter by (e.g., BE,BY,HH)",
        metavar="CODES"
    )
    search_group.add_argument(
        "--register-type",
        dest="register_type",
        help="Filter by register type",
        choices=REGISTER_TYPES,
        metavar="TYPE"
    )
    search_group.add_argument(
        "--register-number",
        dest="register_number",
        help="Search for a specific register number",
        metavar="NUMBER"
    )
    search_group.add_argument(
        "--include-deleted",
        dest="include_deleted",
        help="Include deleted/historical entries in results",
        action="store_true"
    )
    search_group.add_argument(
        "--similar-sounding",
        dest="similar_sounding",
        help="Use phonetic/similarity search (Kölner Phonetik)",
        action="store_true"
    )
    search_group.add_argument(
        "--results-per-page",
        dest="results_per_page",
        help="Number of results per page",
        type=int,
        choices=RESULTS_PER_PAGE_OPTIONS,
        default=100,
        metavar="N"
    )
    
    args = parser.parse_args()
    
    # Configure logging based on debug flag
    if args.debug:
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            stream=sys.stdout
        )
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
        hr = HandelsRegister(args)
        hr.open_startpage()
        companies = hr.search_company()
        
        if companies:
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
