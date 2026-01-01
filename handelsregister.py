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
class Address:
    """Represents a business address."""
    street: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    country: str = "Deutschland"
    
    def __str__(self) -> str:
        """Format address as string."""
        parts = []
        if self.street:
            parts.append(self.street)
        if self.postal_code and self.city:
            parts.append(f"{self.postal_code} {self.city}")
        elif self.city:
            parts.append(self.city)
        if self.country and self.country != "Deutschland":
            parts.append(self.country)
        return ", ".join(parts) if parts else ""
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'street': self.street,
            'postal_code': self.postal_code,
            'city': self.city,
            'country': self.country,
        }


@dataclass
class Representative:
    """Represents a company representative (Geschäftsführer, Vorstand, etc.)."""
    name: str
    role: str  # e.g., "Geschäftsführer", "Vorstand", "Prokurist"
    location: Optional[str] = None
    birth_date: Optional[str] = None
    restrictions: Optional[str] = None  # e.g., "einzelvertretungsberechtigt"
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'role': self.role,
            'location': self.location,
            'birth_date': self.birth_date,
            'restrictions': self.restrictions,
        }


@dataclass
class Owner:
    """Represents a company owner/shareholder (Gesellschafter)."""
    name: str
    share: Optional[str] = None  # e.g., "50%", "25.000 EUR"
    owner_type: Optional[str] = None  # e.g., "Kommanditist", "Gesellschafter"
    location: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'share': self.share,
            'owner_type': self.owner_type,
            'location': self.location,
        }


@dataclass
class CompanyDetails:
    """Extended company information from detail views.
    
    This class contains all information available from the Handelsregister
    detail views (AD, SI, UT).
    """
    # Basic identification (from search results)
    name: str
    register_num: str
    court: str
    state: str
    status: str
    
    # Extended information (from detail views)
    legal_form: Optional[str] = None  # Rechtsform (AG, GmbH, KG, etc.)
    capital: Optional[str] = None  # Stammkapital / Grundkapital
    currency: Optional[str] = None  # EUR, etc.
    address: Optional[Address] = None
    purpose: Optional[str] = None  # Unternehmensgegenstand
    representatives: list[Representative] = field(default_factory=list)
    owners: list[Owner] = field(default_factory=list)
    registration_date: Optional[str] = None  # Eintragungsdatum
    last_update: Optional[str] = None  # Letzte Änderung
    deletion_date: Optional[str] = None  # Löschungsdatum (if deleted)
    
    # Additional metadata
    raw_data: Optional[dict] = field(default=None, repr=False)  # Original parsed data
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'register_num': self.register_num,
            'court': self.court,
            'state': self.state,
            'status': self.status,
            'legal_form': self.legal_form,
            'capital': self.capital,
            'currency': self.currency,
            'address': self.address.to_dict() if self.address else None,
            'purpose': self.purpose,
            'representatives': [r.to_dict() for r in self.representatives],
            'owners': [o.to_dict() for o in self.owners],
            'registration_date': self.registration_date,
            'last_update': self.last_update,
            'deletion_date': self.deletion_date,
        }
    
    @classmethod
    def from_company(cls, company: dict) -> 'CompanyDetails':
        """Create CompanyDetails from a basic company search result dict."""
        return cls(
            name=company.get('name', ''),
            register_num=company.get('register_num', ''),
            court=company.get('court', ''),
            state=company.get('state', ''),
            status=company.get('status', ''),
        )


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

class DetailsParser:
    """Parses detail view HTML (SI, AD, UT) into structured CompanyDetails."""
    
    # Common patterns for extracting data
    CAPITAL_PATTERN = re.compile(
        r'(?:Stamm|Grund)kapital[:\s]*([0-9.,]+)\s*(EUR|€|DM)?',
        re.IGNORECASE
    )
    DATE_PATTERN = re.compile(r'\d{1,2}\.\d{1,2}\.\d{4}')
    
    @classmethod
    def parse_si(cls, html: str, base_info: Optional[dict] = None) -> CompanyDetails:
        """Parse structured register content (SI - Strukturierter Registerinhalt).
        
        Args:
            html: The HTML content of the SI detail view.
            base_info: Optional base company info from search results.
            
        Returns:
            CompanyDetails with all parsed information.
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Initialize with base info or empty
        details = CompanyDetails(
            name=base_info.get('name', '') if base_info else '',
            register_num=base_info.get('register_num', '') if base_info else '',
            court=base_info.get('court', '') if base_info else '',
            state=base_info.get('state', '') if base_info else '',
            status=base_info.get('status', '') if base_info else '',
        )
        
        # Parse structured content - typically in tables or definition lists
        details = cls._parse_si_tables(soup, details)
        details = cls._parse_si_sections(soup, details)
        
        return details
    
    @classmethod
    def _parse_si_tables(cls, soup: BeautifulSoup, details: CompanyDetails) -> CompanyDetails:
        """Extract data from SI tables."""
        # Look for tables with company data
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True).lower()
                    value = cells[1].get_text(strip=True)
                    
                    details = cls._map_field(label, value, details)
        
        return details
    
    @classmethod
    def _parse_si_sections(cls, soup: BeautifulSoup, details: CompanyDetails) -> CompanyDetails:
        """Extract data from SI sections (divs, panels, etc.)."""
        # Look for labeled sections
        for div in soup.find_all(['div', 'span', 'p']):
            text = div.get_text(strip=True)
            
            # Extract capital
            if details.capital is None:
                capital_match = cls.CAPITAL_PATTERN.search(text)
                if capital_match:
                    details.capital = capital_match.group(1)
                    if capital_match.group(2):
                        details.currency = capital_match.group(2).replace('€', 'EUR')
            
            # Extract legal form
            if details.legal_form is None:
                details.legal_form = cls._extract_legal_form(text)
            
            # Extract representatives
            reps = cls._extract_representatives(div)
            if reps:
                details.representatives.extend(reps)
        
        return details
    
    @classmethod
    def _map_field(cls, label: str, value: str, details: CompanyDetails) -> CompanyDetails:
        """Map a label-value pair to the appropriate CompanyDetails field."""
        if not value:
            return details
        
        # Firma / Name
        if any(x in label for x in ['firma', 'name']) and not details.name:
            details.name = value
        
        # Rechtsform
        elif 'rechtsform' in label:
            details.legal_form = value
        
        # Sitz / Adresse
        elif 'sitz' in label or 'geschäftsanschrift' in label:
            details.address = cls._parse_address(value)
        
        # Stammkapital / Grundkapital
        elif 'kapital' in label:
            # Try to extract amount and currency from value
            # Pattern: number followed by optional currency
            amount_pattern = re.match(r'([0-9.,]+)\s*(EUR|€|DM)?', value)
            if amount_pattern:
                details.capital = amount_pattern.group(1).strip()
                if amount_pattern.group(2):
                    details.currency = amount_pattern.group(2).replace('€', 'EUR')
            else:
                details.capital = value
        
        # Gegenstand
        elif 'gegenstand' in label or 'unternehmensgegenstand' in label:
            details.purpose = value
        
        # Registernummer
        elif 'registernummer' in label or 'aktenzeichen' in label:
            if not details.register_num:
                details.register_num = value
        
        # Eintragung
        elif 'eintrag' in label and 'datum' in label:
            details.registration_date = value
        
        # Löschung
        elif 'lösch' in label:
            details.deletion_date = value
        
        return details
    
    @classmethod
    def _parse_address(cls, text: str) -> Address:
        """Parse an address string into an Address object."""
        # Try to extract postal code and city
        plz_city_match = re.search(r'(\d{5})\s+(.+?)(?:,|$)', text)
        
        if plz_city_match:
            postal_code = plz_city_match.group(1)
            city = plz_city_match.group(2).strip()
            # Everything before the postal code is the street
            street_part = text[:plz_city_match.start()].strip().rstrip(',')
            return Address(
                street=street_part if street_part else None,
                postal_code=postal_code,
                city=city,
            )
        else:
            # Just use the whole text as city
            return Address(city=text)
    
    @classmethod
    def _extract_legal_form(cls, text: str) -> Optional[str]:
        """Extract legal form from text.
        
        The order matters: more specific forms (like GmbH & Co. KG) must be
        checked before less specific ones (like GmbH or KG).
        """
        # Order matters: more specific forms first
        legal_forms = [
            # Compound forms first
            ('GmbH & Co. KG', 'GmbH & Co. KG'),
            ('GmbH & Co. OHG', 'GmbH & Co. OHG'),
            ('UG (haftungsbeschränkt) & Co. KG', 'UG & Co. KG'),
            # Then standard forms
            ('Europäische Aktiengesellschaft', 'SE'),
            ('Aktiengesellschaft', 'AG'),
            ('Gesellschaft mit beschränkter Haftung', 'GmbH'),
            ('UG (haftungsbeschränkt)', 'UG'),
            ('Kommanditgesellschaft', 'KG'),
            ('Offene Handelsgesellschaft', 'OHG'),
            ('Eingetragene Genossenschaft', 'eG'),
            ('Eingetragener Verein', 'e.V.'),
            ('Partnerschaftsgesellschaft', 'PartG'),
            ('Einzelkaufmann', 'e.K.'),
            ('Einzelkauffrau', 'e.Kfr.'),
        ]
        
        text_lower = text.lower()
        for full_name, abbreviation in legal_forms:
            # Check for full name
            if full_name.lower() in text_lower:
                return full_name
            # Check for abbreviation (with word boundaries)
            if f' {abbreviation}' in text or text.endswith(abbreviation):
                return full_name
            # Also check without space for compound names
            if abbreviation in text and '&' in abbreviation:
                return full_name
        
        return None
    
    @classmethod
    def _extract_representatives(cls, element: Tag) -> list[Representative]:
        """Extract representative information from an element."""
        representatives = []
        text = element.get_text()
        
        # Common role patterns
        role_patterns = [
            (r'Geschäftsführer(?:in)?[:\s]+([^,;]+)', 'Geschäftsführer'),
            (r'Vorstand[:\s]+([^,;]+)', 'Vorstand'),
            (r'Prokurist(?:in)?[:\s]+([^,;]+)', 'Prokurist'),
            (r'Inhaber(?:in)?[:\s]+([^,;]+)', 'Inhaber'),
            (r'Persönlich haftende(?:r)? Gesellschafter(?:in)?[:\s]+([^,;]+)', 
             'Persönlich haftender Gesellschafter'),
        ]
        
        for pattern, role in role_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                name = match.group(1).strip()
                if name and len(name) > 2:
                    # Check for location in parentheses
                    location = None
                    loc_match = re.search(r'\(([^)]+)\)', name)
                    if loc_match:
                        location = loc_match.group(1)
                        name = name[:loc_match.start()].strip()
                    
                    representatives.append(Representative(
                        name=name,
                        role=role,
                        location=location,
                    ))
        
        return representatives


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
    """Browser-Automatisierung für die Handelsregister-Suche.
    
    Diese Klasse verwaltet die Interaktion mit der Handelsregister-Website,
    einschließlich Navigation, Formular-Übermittlung und Ergebnis-Abruf.
    
    Beispiel (programmatische Nutzung):
        >>> hr = HandelsRegister(debug=False)
        >>> hr.open_startpage()
        >>> results = hr.search("Deutsche Bahn", keyword_option="all")
        
    Beispiel (mit SearchOptions):
        >>> opts = SearchOptions(keywords="Bank", states=["BE", "HH"])
        >>> hr = HandelsRegister()
        >>> hr.open_startpage()
        >>> results = hr.search_with_options(opts)
    """
    
    def __init__(
        self,
        args: Optional[argparse.Namespace] = None,
        cache: Optional[SearchCache] = None,
        debug: bool = False,
    ) -> None:
        """Initialisiert den HandelsRegister-Client.
        
        Args:
            args: CLI-Argumente (optional, für Rückwärtskompatibilität).
            cache: Cache-Instanz (optional, wird automatisch erstellt).
            debug: Debug-Logging aktivieren.
        """
        self.args = args
        self.cache = cache or SearchCache()
        self._debug = debug if args is None else getattr(args, 'debug', False)
        self.browser = self._create_browser(debug=self._debug)
    
    @classmethod
    def from_options(
        cls,
        options: SearchOptions,
        cache: Optional[SearchCache] = None,
        debug: bool = False,
    ) -> 'HandelsRegister':
        """Erstellt einen Client mit SearchOptions.
        
        Args:
            options: Suchoptionen.
            cache: Cache-Instanz (optional).
            debug: Debug-Logging aktivieren.
            
        Returns:
            Konfigurierte HandelsRegister-Instanz.
        """
        instance = cls(args=None, cache=cache, debug=debug)
        instance._default_options = options
        return instance
    
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
    
    def search_with_options(
        self,
        options: SearchOptions,
        force_refresh: bool = False,
    ) -> list[dict]:
        """Führt eine Suche mit SearchOptions durch.
        
        Args:
            options: Suchoptionen.
            force_refresh: Cache ignorieren.
            
        Returns:
            Liste von Dictionaries mit Unternehmensdaten.
            
        Raises:
            NetworkError: Bei Netzwerkfehlern.
            FormError: Bei Formular-Problemen.
            ParseError: Bei Parse-Fehlern.
        """
        cache_key = options.cache_key()
        
        # Try to load from cache
        if not force_refresh:
            cached_html = self.cache.get(cache_key, "")
            if cached_html is not None:
                logger.info("Cache-Treffer für: %s", options.keywords)
                return ResultParser.parse_search_results(cached_html)
        
        # Fetch fresh data from website
        html = self._fetch_search_results(options)
        
        # Save to cache
        self.cache.set(cache_key, "", html)
        
        return ResultParser.parse_search_results(html)
    
    def search_company(self) -> list[dict]:
        """Sucht nach Unternehmen basierend auf CLI-Argumenten.
        
        Hinweis: Für programmatische Nutzung wird search_with_options() empfohlen.
        
        Returns:
            Liste von Dictionaries mit Unternehmensdaten.
            
        Raises:
            NetworkError: Bei Netzwerkfehlern.
            FormError: Bei Formular-Problemen.
            ParseError: Bei Parse-Fehlern.
        """
        if self.args is None:
            raise ValueError("search_company() benötigt args. Nutze search_with_options() stattdessen.")
        
        search_opts = self._build_search_options()
        force_refresh = getattr(self.args, 'force', False)
        return self.search_with_options(search_opts, force_refresh=force_refresh)
    
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


# =============================================================================
# Public API
# =============================================================================

def search(
    keywords: str,
    keyword_option: str = "all",
    states: Optional[list[str]] = None,
    register_type: Optional[str] = None,
    register_number: Optional[str] = None,
    include_deleted: bool = False,
    similar_sounding: bool = False,
    results_per_page: int = 100,
    force_refresh: bool = False,
    debug: bool = False,
) -> list[dict]:
    """Durchsucht das Handelsregister nach Unternehmen.
    
    Dies ist die Haupt-API für die programmatische Nutzung des Packages.
    
    Args:
        keywords: Suchbegriffe (erforderlich).
        keyword_option: Suchmodus - "all" (alle Begriffe), "min" (mindestens einer), 
                       "exact" (exakter Firmenname). Standard: "all".
        states: Liste von Bundesland-Codes zum Filtern (z.B. ["BE", "BY", "HH"]).
        register_type: Registerart-Filter (HRA, HRB, GnR, PR, VR).
        register_number: Spezifische Registernummer suchen.
        include_deleted: Auch gelöschte Einträge anzeigen.
        similar_sounding: Phonetische Suche (Kölner Phonetik) verwenden.
        results_per_page: Ergebnisse pro Seite (10, 25, 50, 100). Standard: 100.
        force_refresh: Cache ignorieren und neue Daten abrufen.
        debug: Debug-Logging aktivieren.
        
    Returns:
        Liste von Dictionaries mit Unternehmensdaten. Jedes Dictionary enthält:
        - name: Firmenname
        - court: Registergericht
        - register_num: Registernummer (z.B. "HRB 12345 B")
        - state: Bundesland
        - status: Aktueller Status
        - statusCurrent: Normalisierter Status (z.B. "CURRENTLY_REGISTERED")
        - documents: Verfügbare Dokumente
        - history: Liste von (Name, Ort) Tupeln mit historischen Einträgen
        
    Raises:
        NetworkError: Bei Netzwerkfehlern.
        FormError: Wenn die Website-Struktur sich geändert hat.
        ParseError: Bei Fehlern beim Parsen der Ergebnisse.
        
    Beispiel:
        >>> from handelsregister import search
        >>> 
        >>> # Einfache Suche
        >>> companies = search("Deutsche Bahn")
        >>> 
        >>> # Mit Filtern
        >>> banks = search("Bank", states=["BE", "HH"], register_type="HRB")
        >>> 
        >>> for company in banks:
        ...     print(f"{company['name']} - {company['register_num']}")
    """
    # Configure logging if debug mode
    if debug:
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # Build args namespace for HandelsRegister
    args = argparse.Namespace(
        debug=debug,
        force=force_refresh,
        json=False,
        schlagwoerter=keywords,
        schlagwortOptionen=keyword_option,
        states=",".join(states) if states else None,
        register_type=register_type,
        register_number=register_number,
        include_deleted=include_deleted,
        similar_sounding=similar_sounding,
        results_per_page=results_per_page,
    )
    
    hr = HandelsRegister(args)
    hr.open_startpage()
    return hr.search_company()


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
