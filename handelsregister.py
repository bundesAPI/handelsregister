#!/usr/bin/env python3
"""
Python client for the German Handelsregister (commercial register).

This package provides both a CLI tool and a library interface to search the
Handelsregister portal without using a browser. Built as part of the bundesAPI
initiative to make German government data more accessible.
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
from typing import Optional, Any

# Third-party imports
import diskcache
import mechanize
from bs4 import BeautifulSoup
from bs4.element import Tag
from pydantic import BaseModel, Field, ConfigDict, field_validator
from ratelimit import limits, sleep_and_retry
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

# Configure module logger
logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

DEFAULT_CACHE_TTL_SECONDS: int = 3600  # 1 hour default TTL for search results
DETAILS_CACHE_TTL_SECONDS: int = 86400  # 24 hours TTL for company details
BASE_URL: str = "https://www.handelsregister.de"
REQUEST_TIMEOUT: int = 10
MAX_RETRIES: int = 3  # Maximum number of retry attempts for network requests
RETRY_WAIT_MIN: int = 2  # Minimum wait time between retries in seconds
RETRY_WAIT_MAX: int = 10  # Maximum wait time between retries in seconds
RATE_LIMIT_CALLS: int = 60  # Maximum requests per hour (per portal terms of service)
RATE_LIMIT_PERIOD: int = 3600  # Rate limit period in seconds (1 hour)

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
    """Represents a cached search result with metadata.
    
    Note: Kept as dataclass for internal use only. Not part of public API.
    """
    query: str
    options: str
    timestamp: float
    html: str
    
    def is_expired(self, ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS) -> bool:
        """Checks if the cache entry has expired.
        
        Args:
            ttl_seconds: Time-to-live in seconds.
            
        Returns:
            True if expired, False otherwise.
        """
        return (time.time() - self.timestamp) > ttl_seconds
    
    def to_dict(self) -> dict:
        """Converts to dictionary for JSON serialization."""
        return {
            'query': self.query,
            'options': self.options,
            'timestamp': self.timestamp,
            'html': self.html
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CacheEntry':
        """Creates a CacheEntry from a dictionary."""
        return cls(
            query=data['query'],
            options=data['options'],
            timestamp=data['timestamp'],
            html=data['html']
        )


class SearchOptions(BaseModel):
    """Encapsulates all search parameters for the Handelsregister.
    
    Uses Pydantic for validation and serialization.
    
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
    model_config = ConfigDict(frozen=False, validate_assignment=True)
    
    keywords: str = Field(..., min_length=1, description="Search keywords")
    keyword_option: str = Field(default="all", pattern="^(all|min|exact)$")
    states: Optional[list[str]] = Field(default=None, description="State codes to filter by")
    register_type: Optional[str] = Field(default=None, pattern="^(HRA|HRB|GnR|PR|VR)$")
    register_number: Optional[str] = None
    include_deleted: bool = False
    similar_sounding: bool = False
    results_per_page: int = Field(default=100, ge=10, le=100)
    
    @field_validator('states')
    @classmethod
    def validate_states(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        """Validates state codes against known values."""
        if v is None:
            return None
        valid_codes = set(STATE_CODES.keys())
        for state in v:
            if state.upper() not in valid_codes:
                raise ValueError(f"Invalid state code: {state}. Valid: {', '.join(sorted(valid_codes))}")
        return [s.upper() for s in v]
    
    @field_validator('results_per_page')
    @classmethod
    def validate_results_per_page(cls, v: int) -> int:
        """Validates results_per_page is a valid option."""
        if v not in RESULTS_PER_PAGE_OPTIONS:
            raise ValueError(f"results_per_page must be one of {RESULTS_PER_PAGE_OPTIONS}")
        return v
    
    def cache_key(self) -> str:
        """Generates a unique key for caching based on all options."""
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


class HistoryEntry(BaseModel):
    """Represents a historical name/location entry for a company."""
    model_config = ConfigDict(frozen=True)
    
    name: str
    location: str


class Address(BaseModel):
    """Represents a business address with validation."""
    model_config = ConfigDict(frozen=False)
    
    street: Optional[str] = None
    postal_code: Optional[str] = Field(default=None, pattern=r"^\d{5}$|^$|None")
    city: Optional[str] = None
    country: str = "Deutschland"
    
    @field_validator('postal_code', mode='before')
    @classmethod
    def validate_postal_code(cls, v: Any) -> Optional[str]:
        """Allow None or valid German postal codes."""
        if v is None or v == "":
            return None
        if isinstance(v, str) and len(v) == 5 and v.isdigit():
            return v
        # Be lenient - just return as-is for non-standard codes
        return str(v) if v else None
    
    def __str__(self) -> str:
        """Formats address as string."""
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
        """Convert to dictionary (for backward compatibility)."""
        return self.model_dump()


class Representative(BaseModel):
    """Represents a company representative (Geschäftsführer, Vorstand, etc.)."""
    model_config = ConfigDict(frozen=False)
    
    name: str = Field(..., min_length=1, description="Name of the representative")
    role: str = Field(..., description="Role (e.g., Geschäftsführer, Vorstand)")
    location: Optional[str] = None
    birth_date: Optional[str] = None
    restrictions: Optional[str] = None  # e.g., "einzelvertretungsberechtigt"
    
    def to_dict(self) -> dict:
        """Converts to dictionary (for backward compatibility)."""
        return self.model_dump()


class Owner(BaseModel):
    """Represents a company owner/shareholder (Gesellschafter)."""
    model_config = ConfigDict(frozen=False)
    
    name: str = Field(..., min_length=1, description="Name of the owner")
    share: Optional[str] = None  # e.g., "50%", "25.000 EUR"
    owner_type: Optional[str] = None  # e.g., "Kommanditist", "Gesellschafter"
    location: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Converts to dictionary (for backward compatibility)."""
        return self.model_dump()


class CompanyDetails(BaseModel):
    """Extended company information from detail views.
    
    Contains all information available from the Handelsregister detail
    views (AD, SI, UT). Uses Pydantic for validation and serialization.
    """
    model_config = ConfigDict(frozen=False, validate_assignment=True)
    
    # Basic identification (from search results)
    name: str = Field(..., description="Company name")
    register_num: str = Field(default="", description="Register number (e.g., HRB 12345 B)")
    court: str = Field(default="", description="Registration court")
    state: str = Field(default="", description="Federal state")
    status: str = Field(default="", description="Registration status")
    
    # Extended information (from detail views)
    legal_form: Optional[str] = Field(default=None, description="Legal form (AG, GmbH, KG, etc.)")
    capital: Optional[str] = Field(default=None, description="Share capital / Stammkapital")
    currency: Optional[str] = Field(default=None, description="Currency (EUR, etc.)")
    address: Optional[Address] = None
    purpose: Optional[str] = Field(default=None, description="Business purpose / Unternehmensgegenstand")
    representatives: list[Representative] = Field(default_factory=list)
    owners: list[Owner] = Field(default_factory=list)
    registration_date: Optional[str] = Field(default=None, description="Registration date")
    last_update: Optional[str] = Field(default=None, description="Last update date")
    deletion_date: Optional[str] = Field(default=None, description="Deletion date (if deleted)")
    
    # Additional metadata
    raw_data: Optional[dict] = Field(default=None, repr=False, exclude=True)
    
    def to_dict(self) -> dict:
        """Converts to dictionary for JSON serialization (backward compatibility)."""
        data = self.model_dump(exclude={'raw_data'})
        # Convert nested models to dicts
        if self.address:
            data['address'] = self.address.to_dict()
        data['representatives'] = [r.to_dict() for r in self.representatives]
        data['owners'] = [o.to_dict() for o in self.owners]
        return data
    
    @classmethod
    def from_company(cls, company: dict) -> 'CompanyDetails':
        """Creates CompanyDetails from a basic company search result dict."""
        return cls(
            name=company.get('name', ''),
            register_num=company.get('register_num', ''),
            court=company.get('court', ''),
            state=company.get('state', ''),
            status=company.get('status', ''),
        )


class Company(BaseModel):
    """Represents a company record from the Handelsregister."""
    model_config = ConfigDict(frozen=False, populate_by_name=True)
    
    court: str
    name: str
    state: str
    status: str
    status_normalized: str = Field(default="", alias='statusCurrent')
    documents: str
    register_num: Optional[str] = None
    history: list[HistoryEntry] = Field(default_factory=list)

    def to_dict(self) -> dict:
        """Converts to dictionary for backward compatibility."""
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
    """Caches search results and company details using DiskCache.
    
    Uses DiskCache for efficient, thread-safe caching with automatic TTL
    expiration. Different TTLs for search results (1h default) vs details
    (24h default) since details change less frequently.
    """
    
    def __init__(
        self, 
        cache_dir: Optional[pathlib.Path] = None,
        ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS,
        details_ttl_seconds: int = DETAILS_CACHE_TTL_SECONDS,
    ) -> None:
        """Initialize the cache.
        
        Args:
            cache_dir: Directory to store cache files. Defaults to temp directory.
            ttl_seconds: Time-to-live for search result cache entries in seconds.
            details_ttl_seconds: Time-to-live for details cache entries in seconds.
        """
        self.ttl_seconds = ttl_seconds
        self.details_ttl_seconds = details_ttl_seconds
        self.cache_dir = cache_dir or (
            pathlib.Path(tempfile.gettempdir()) / "handelsregister_cache"
        )
        # Initialize DiskCache with size limit (500MB default)
        self._cache = diskcache.Cache(
            str(self.cache_dir),
            size_limit=500 * 1024 * 1024,
        )
    
    def _get_cache_key(self, query: str, options: str) -> str:
        """Generate a safe cache key by hashing the query parameters."""
        key_data = f"{query}|{options}"
        return hashlib.sha256(key_data.encode('utf-8')).hexdigest()
    
    def _get_cache_path(self, query: str, options: str) -> pathlib.Path:
        """Get the cache file path for a query (for backward compatibility)."""
        cache_key = self._get_cache_key(query, options)
        return self.cache_dir / f"{cache_key}.json"
    
    def get(self, query: str, options: str) -> Optional[str]:
        """Returns cached HTML if available and not expired.
        
        Args:
            query: Search query string (or cache key for details).
            options: Search options string.
            
        Returns:
            Cached HTML content, or None if not cached or expired.
            
        DiskCache handles expiration automatically based on the TTL set
        when the entry was stored.
        """
        cache_key = self._get_cache_key(query, options)
        return self._cache.get(cache_key, default=None)
    
    def set(self, query: str, options: str, html: str) -> None:
        """Caches HTML content with automatic TTL.
        
        Args:
            query: Search query string.
            options: Search options string.
            html: HTML content to cache.
        """
        cache_key = self._get_cache_key(query, options)
        # Use longer TTL for details cache
        ttl = self.details_ttl_seconds if query.startswith("details:") else self.ttl_seconds
        try:
            self._cache.set(cache_key, html, expire=ttl)
        except Exception as e:
            logger.warning("Failed to write cache: %s", e)
    
    def clear(self, details_only: bool = False) -> int:
        """Deletes all cache entries.
        
        Args:
            details_only: If True, only delete details cache entries.
                         Note: With DiskCache this clears all entries as we
                         cannot efficiently filter by key prefix.
            
        Returns:
            Number of entries deleted.
        """
        if details_only:
            # For details_only, we need to iterate and delete matching keys
            count = 0
            for key in list(self._cache):
                # Keys starting with details prefix have "details:" in query
                # Since we hash keys, we need to track this differently
                # For simplicity, we just clear all when details_only is True
                try:
                    del self._cache[key]
                    count += 1
                except KeyError:
                    pass
            return count
        else:
            count = len(self._cache)
            self._cache.clear()
            return count
    
    def get_stats(self) -> dict:
        """Returns cache statistics.
        
        Returns:
            Dict with total_files, search_files, details_files, and
            total_size_bytes.
        """
        return {
            'total_files': len(self._cache),
            'search_files': len(self._cache),  # DiskCache doesn't distinguish
            'details_files': 0,  # Would need metadata tracking
            'total_size_bytes': self._cache.volume(),
        }
    
    def close(self) -> None:
        """Closes the cache connection."""
        self._cache.close()
    
    def __enter__(self) -> 'SearchCache':
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()


# =============================================================================
# Parser Layer
# =============================================================================

class DetailsParser:
    """Parses detail view HTML (SI, AD, UT) into CompanyDetails objects."""
    
    # Common patterns for extracting data
    CAPITAL_PATTERN = re.compile(
        r'(?:Stamm|Grund)kapital[:\s]*([0-9.,]+)\s*(EUR|€|DM)?',
        re.IGNORECASE
    )
    DATE_PATTERN = re.compile(r'\d{1,2}\.\d{1,2}\.\d{4}')
    
    @classmethod
    def parse_si(cls, html: str, base_info: Optional[dict] = None) -> CompanyDetails:
        """Parses structured register content (SI - Strukturierter Registerinhalt).
        
        Args:
            html: HTML content of the SI detail view.
            base_info: Optional base company info from search results.
            
        Returns:
            CompanyDetails with parsed information.
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
        """Extracts data from SI tables."""
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
        """Extracts data from SI sections (divs, panels, etc.)."""
        for div in soup.find_all(['div', 'span', 'p']):
            text = div.get_text(strip=True)
            
            if details.capital is None:
                capital_match = cls.CAPITAL_PATTERN.search(text)
                if capital_match:
                    details.capital = capital_match.group(1)
                    if capital_match.group(2):
                        details.currency = capital_match.group(2).replace('€', 'EUR')
            
            if details.legal_form is None:
                details.legal_form = cls._extract_legal_form(text)
            
            reps = cls._extract_representatives(div)
            if reps:
                details.representatives.extend(reps)
        
        return details
    
    @classmethod
    def _map_field(cls, label: str, value: str, details: CompanyDetails) -> CompanyDetails:
        """Maps a label-value pair to the appropriate CompanyDetails field."""
        if not value:
            return details
        
        if any(x in label for x in ['firma', 'name']) and not details.name:
            details.name = value
        elif 'rechtsform' in label:
            details.legal_form = value
        elif 'sitz' in label or 'geschäftsanschrift' in label:
            details.address = cls._parse_address(value)
        elif 'kapital' in label:
            amount_pattern = re.match(r'([0-9.,]+)\s*(EUR|€|DM)?', value)
            if amount_pattern:
                details.capital = amount_pattern.group(1).strip()
                if amount_pattern.group(2):
                    details.currency = amount_pattern.group(2).replace('€', 'EUR')
            else:
                details.capital = value
        elif 'gegenstand' in label or 'unternehmensgegenstand' in label:
            details.purpose = value
        elif 'registernummer' in label or 'aktenzeichen' in label:
            if not details.register_num:
                details.register_num = value
        elif 'eintrag' in label and 'datum' in label:
            details.registration_date = value
        elif 'lösch' in label:
            details.deletion_date = value
        
        return details
    
    @classmethod
    def _parse_address(cls, text: str) -> Address:
        """Parses an address string into an Address object."""
        plz_city_match = re.search(r'(\d{5})\s+(.+?)(?:,|$)', text)
        
        if plz_city_match:
            postal_code = plz_city_match.group(1)
            city = plz_city_match.group(2).strip()
            street_part = text[:plz_city_match.start()].strip().rstrip(',')
            return Address(
                street=street_part if street_part else None,
                postal_code=postal_code,
                city=city,
            )
        else:
            return Address(city=text)
    
    @classmethod
    def _extract_legal_form(cls, text: str) -> Optional[str]:
        """Extracts legal form from text.
        
        Order matters: more specific forms (like GmbH & Co. KG) must be
        checked before less specific ones (like GmbH or KG).
        """
        legal_forms = [
            ('GmbH & Co. KG', 'GmbH & Co. KG'),
            ('GmbH & Co. OHG', 'GmbH & Co. OHG'),
            ('UG (haftungsbeschränkt) & Co. KG', 'UG & Co. KG'),
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
            if full_name.lower() in text_lower:
                return full_name
            if f' {abbreviation}' in text or text.endswith(abbreviation):
                return full_name
            if abbreviation in text and '&' in abbreviation:
                return full_name
        
        return None
    
    @classmethod
    def _extract_representatives(cls, element: Tag) -> list[Representative]:
        """Extracts representative information from an element."""
        representatives = []
        text = element.get_text()
        
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
    
    @classmethod
    def parse_ad(cls, html: str, base_info: Optional[dict] = None) -> CompanyDetails:
        """Parses current printout (AD - Aktueller Abdruck).
        
        The AD view contains the current state of the register entry as
        formatted text rather than structured tables.
        
        Args:
            html: HTML content of the AD detail view.
            base_info: Optional base company info from search results.
            
        Returns:
            CompanyDetails with parsed information.
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        details = CompanyDetails(
            name=base_info.get('name', '') if base_info else '',
            register_num=base_info.get('register_num', '') if base_info else '',
            court=base_info.get('court', '') if base_info else '',
            state=base_info.get('state', '') if base_info else '',
            status=base_info.get('status', '') if base_info else '',
        )
        
        content_div = soup.find('div', class_=re.compile(r'content|abdruck|register', re.I))
        if content_div is None:
            content_div = soup.find('body')
        
        if content_div:
            text = content_div.get_text()
            
            details.legal_form = cls._extract_legal_form(text)
            
            capital_match = cls.CAPITAL_PATTERN.search(text)
            if capital_match:
                details.capital = capital_match.group(1)
                if capital_match.group(2):
                    details.currency = capital_match.group(2).replace('€', 'EUR')
            
            purpose_match = re.search(
                r'Gegenstand(?:\s+des\s+Unternehmens)?[:\s]*(.+?)(?:Stammkapital|Grundkapital|Geschäftsführer|Vorstand|Vertretung|$)',
                text, re.IGNORECASE | re.DOTALL
            )
            if purpose_match:
                details.purpose = purpose_match.group(1).strip()
            
            details.representatives = cls._extract_representatives_from_text(text)
            details = cls._parse_si_tables(soup, details)
        
        return details
    
    @classmethod
    def parse_ut(cls, html: str, base_info: Optional[dict] = None) -> CompanyDetails:
        """Parses company owner information (UT - Unternehmensträger).
        
        The UT view focuses on ownership and shareholder information.
        
        Args:
            html: HTML content of the UT detail view.
            base_info: Optional base company info from search results.
            
        Returns:
            CompanyDetails with owner information.
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        details = CompanyDetails(
            name=base_info.get('name', '') if base_info else '',
            register_num=base_info.get('register_num', '') if base_info else '',
            court=base_info.get('court', '') if base_info else '',
            state=base_info.get('state', '') if base_info else '',
            status=base_info.get('status', '') if base_info else '',
        )
        
        details = cls._parse_si_tables(soup, details)
        text = soup.get_text()
        details.owners = cls._extract_owners(text)
        details.representatives = cls._extract_representatives_from_text(text)
        
        return details
    
    @classmethod
    def _extract_representatives_from_text(cls, text: str) -> list[Representative]:
        """Extracts all representatives from free-form text."""
        representatives = []
        seen_names = set()
        
        patterns = [
            (r'Geschäftsführer(?:in)?[:\s]*([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)+)', 
             'Geschäftsführer'),
            (r'Vorstand[:\s]*([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)+)', 
             'Vorstand'),
            (r'Prokurist(?:in)?[:\s]*([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)+)', 
             'Prokurist'),
            (r'Persönlich\s+haftende[r]?\s+Gesellschafter(?:in)?[:\s]*([A-ZÄÖÜ][^\n,;]+)', 
             'Persönlich haftender Gesellschafter'),
        ]
        
        for pattern, role in patterns:
            for match in re.finditer(pattern, text):
                name = match.group(1).strip()
                name = re.sub(r'\s*\([^)]*\)\s*', '', name).strip()
                name = re.sub(r'\s+', ' ', name)
                
                if name and len(name) > 3 and name not in seen_names:
                    seen_names.add(name)
                    location = None
                    full_match = match.group(0)
                    loc_match = re.search(r'\(([^)]+)\)', full_match)
                    if loc_match:
                        location = loc_match.group(1)
                    
                    representatives.append(Representative(
                        name=name,
                        role=role,
                        location=location,
                    ))
        
        return representatives
    
    @classmethod
    def _extract_owners(cls, text: str) -> list[Owner]:
        """Extracts owner/shareholder information from text."""
        owners = []
        seen_names = set()
        
        owner_patterns = [
            (r'Gesellschafter[:\s]+([^,\n]+?)(?:[,\s]+(?:Anteil|Einlage)[:\s]*([0-9.,]+\s*(?:EUR|€|%)))?(?:\n|$|,)',
             'Gesellschafter'),
            (r'Kommanditist(?:in)?[:\s]+([^,\n]+?)(?:[,\s]+(?:Anteil|Einlage|Haftsumme)[:\s]*([0-9.,]+\s*(?:EUR|€|%)))?(?:\n|$|,)',
             'Kommanditist'),
            (r'Komplementär(?:in)?[:\s]+([^,\n]+)',
             'Komplementär'),
        ]
        
        for pattern, owner_type in owner_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                name = match.group(1).strip()
                name = re.sub(r'\s+', ' ', name)
                share = None
                if len(match.groups()) > 1 and match.group(2):
                    share = match.group(2).strip()
                
                if name and len(name) > 2 and name not in seen_names:
                    seen_names.add(name)
                    owners.append(Owner(
                        name=name,
                        share=share,
                        owner_type=owner_type,
                    ))
        
        return owners


class ResultParser:
    """Parses HTML search results into structured company data."""
    
    @staticmethod
    def parse_search_results(html: str) -> list[dict]:
        """Extracts company records from search results HTML.
        
        Args:
            html: HTML content of the search results page.
            
        Returns:
            List of dictionaries with company information.
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
        """Parses a single search result row into a company dictionary.
        
        Args:
            row: BeautifulSoup Tag representing a table row.
            
        Returns:
            Dictionary containing company information.
            
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
        """Extracts and normalizes the register number from court string.
        
        Args:
            court: Court field containing the register number.
            state: State, used to add appropriate suffix.
            
        Returns:
            Normalized register number, or None if not found.
        """
        reg_match = re.search(r'(HRA|HRB|GnR|VR|PR)\s*\d+(\s+[A-Z])?(?!\w)', court)
        
        if not reg_match:
            return None
            
        register_num = reg_match.group(0)
        reg_type = register_num.split()[0]
        suffix = SUFFIX_MAP.get(state, {}).get(reg_type)
        if suffix and not register_num.endswith(suffix):
            register_num += suffix
            
        return register_num
    
    @staticmethod
    def _parse_history(cells: list[str]) -> list[tuple[str, str]]:
        """Parses history entries from cell data.
        
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
    """Parses a single search result row into a company dictionary.
    
    Deprecated: Use ResultParser.parse_result_row() instead.
    """
    return ResultParser.parse_result_row(result)


def get_companies_in_searchresults(html: str) -> list[dict]:
    """Extracts company records from search results HTML.
    
    Deprecated: Use ResultParser.parse_search_results() instead.
    """
    return ResultParser.parse_search_results(html)


# =============================================================================
# Browser Layer
# =============================================================================

class HandelsRegister:
    """Browser-Automatisierung für die Handelsregister-Suche.
    
    Verwaltet die Interaktion mit der Handelsregister-Website, Navigation,
    Formular-Übermittlung und Ergebnis-Abruf.
    
    Beispiel:
        >>> hr = HandelsRegister(debug=False)
        >>> hr.open_startpage()
        >>> results = hr.search_with_options(SearchOptions(keywords="Bank", states=["BE"]))
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
        """Creates and configures a mechanize browser instance.
        
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
        """Gets the cache directory path."""
        return self.cache.cache_dir
    
    @sleep_and_retry
    @limits(calls=RATE_LIMIT_CALLS, period=RATE_LIMIT_PERIOD)
    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=RETRY_WAIT_MIN, max=RETRY_WAIT_MAX),
        retry=retry_if_exception_type(urllib.error.URLError),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def open_startpage(self) -> None:
        """Opens the Handelsregister start page with automatic retries.
        
        Uses exponential backoff for retries on network failures.
        Rate limited to 60 requests per hour per portal terms of service.
        
        Raises:
            NetworkError: If the connection fails after all retry attempts.
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
        """Builds SearchOptions from command-line arguments.
        
        Returns:
            SearchOptions instance with all search parameters.
        """
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
        """Fetches search results from the website.
        
        Args:
            search_opts: Search options specifying all search parameters.
            
        Returns:
            HTML content of search results page.
            
        Raises:
            NetworkError: If network requests fail.
            FormError: If form selection or submission fails.
        """
        self._navigate_to_search()
        return self._submit_search(search_opts)
    
    @sleep_and_retry
    @limits(calls=RATE_LIMIT_CALLS, period=RATE_LIMIT_PERIOD)
    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=RETRY_WAIT_MIN, max=RETRY_WAIT_MAX),
        retry=retry_if_exception_type(urllib.error.URLError),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def _navigate_to_search(self) -> None:
        """Navigates from start page to extended search form with retries.
        
        Uses exponential backoff for retries on network failures.
        Rate limited to 60 requests per hour per portal terms of service.
        
        Raises:
            FormError: If navigation form is not found.
            NetworkError: If form submission fails after all retries.
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
    
    @sleep_and_retry
    @limits(calls=RATE_LIMIT_CALLS, period=RATE_LIMIT_PERIOD)
    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=RETRY_WAIT_MIN, max=RETRY_WAIT_MAX),
        retry=retry_if_exception_type(urllib.error.URLError),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def _submit_search(self, search_opts: SearchOptions) -> str:
        """Submits the search form and returns results HTML with retries.
        
        Uses exponential backoff for retries on network failures.
        Rate limited to 60 requests per hour per portal terms of service.
        
        Args:
            search_opts: Search options specifying all search parameters.
            
        Returns:
            HTML content of search results page.
            
        Raises:
            FormError: If search form is not found.
            NetworkError: If form submission fails after all retries.
        """
        try:
            self.browser.select_form(name="form")
        except mechanize.FormNotFoundError as e:
            raise FormError(
                f"Search form not found. The website structure may have changed: {e}"
            ) from e
        
        self.browser["form:schlagwoerter"] = search_opts.keywords
        option_id = KEYWORD_OPTIONS.get(search_opts.keyword_option)
        self.browser["form:schlagwortOptionen"] = [str(option_id)]
        
        if search_opts.states:
            for state_code in search_opts.states:
                if state_code in STATE_CODES:
                    try:
                        state_name = STATE_CODES[state_code]
                        control_name = f"form:{state_name}_input"
                        self.browser.form.find_control(control_name).value = ["on"]
                        logger.debug("Enabled state filter: %s (%s)", state_code, state_name)
                    except mechanize.ControlNotFoundError:
                        logger.warning("State control not found: %s", control_name)
        
        if search_opts.register_type:
            try:
                self.browser["form:registerArt_input"] = [search_opts.register_type]
                logger.debug("Set register type: %s", search_opts.register_type)
            except mechanize.ControlNotFoundError:
                logger.warning("Register type control not found")
        
        if search_opts.register_number:
            try:
                self.browser["form:registerNummer"] = search_opts.register_number
                logger.debug("Set register number: %s", search_opts.register_number)
            except mechanize.ControlNotFoundError:
                logger.warning("Register number control not found")
        
        if search_opts.include_deleted:
            try:
                self.browser.form.find_control("form:auchGeloeschte_input").value = ["on"]
                logger.debug("Enabled include deleted option")
            except mechanize.ControlNotFoundError:
                logger.warning("Include deleted control not found")
        
        if search_opts.similar_sounding:
            try:
                self.browser.form.find_control("form:aenlichLautendeSchlagwoerterBoolChkbox_input").value = ["on"]
                logger.debug("Enabled similar sounding option")
            except mechanize.ControlNotFoundError:
                logger.warning("Similar sounding control not found")
        
        if search_opts.results_per_page in RESULTS_PER_PAGE_OPTIONS:
            try:
                self.browser["form:ergebnisseProSeite_input"] = [str(search_opts.results_per_page)]
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
    
    # =========================================================================
    # Detail Fetching Methods
    # =========================================================================
    
    def get_company_details(
        self,
        company: dict,
        detail_type: str = "SI",
        force_refresh: bool = False,
    ) -> CompanyDetails:
        """Fetches detailed company information.
        
        Args:
            company: Company dict from search results (must contain row_index).
            detail_type: Type of details to fetch:
                - "SI": Strukturierter Registerinhalt (structured, recommended)
                - "AD": Aktueller Abdruck (current printout)
                - "UT": Unternehmensträger (company owners)
            force_refresh: Skip cache and fetch fresh data.
            
        Returns:
            CompanyDetails with all available information.
            
        Raises:
            NetworkError: If the request fails.
            ParseError: If parsing fails.
            ValueError: If company dict is missing required fields.
        """
        valid_types = ["SI", "AD", "UT", "CD", "HD", "VÖ"]
        if detail_type not in valid_types:
            raise ValueError(f"Invalid detail_type: {detail_type}. Must be one of {valid_types}")
        
        cache_key = f"details:{detail_type}:{company.get('register_num', '')}:{company.get('court', '')}"
        
        if not force_refresh:
            cached_html = self.cache.get(cache_key, "")
            if cached_html is not None:
                logger.info("Cache hit for details: %s", cache_key)
                return self._parse_details(cached_html, company, detail_type)
        
        html = self._fetch_detail_page(company, detail_type)
        self.cache.set(cache_key, "", html)
        
        return self._parse_details(html, company, detail_type)
    
    @sleep_and_retry
    @limits(calls=RATE_LIMIT_CALLS, period=RATE_LIMIT_PERIOD)
    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=RETRY_WAIT_MIN, max=RETRY_WAIT_MAX),
        retry=retry_if_exception_type(urllib.error.URLError),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def _fetch_detail_page(self, company: dict, detail_type: str) -> str:
        """Fetches a detail page for a company with retries.
        
        The Handelsregister uses JSF/PrimeFaces which requires specific
        form parameters. We reconstruct these based on the search results.
        Uses exponential backoff for retries on network failures.
        Rate limited to 60 requests per hour per portal terms of service.
        
        Args:
            company: Company dict with at least 'row_index' from search.
            detail_type: Type of detail page (SI, AD, UT, etc.).
            
        Returns:
            HTML content of the detail page.
        """
        row_index = company.get('row_index', 0)
        
        detail_type_mapping = {
            'AD': 'ergebnissForm:selectedSuchErgebnisFormTable:{row}:j_idt161:0:fade',
            'CD': 'ergebnissForm:selectedSuchErgebnisFormTable:{row}:j_idt161:1:fade',
            'HD': 'ergebnissForm:selectedSuchErgebnisFormTable:{row}:j_idt161:2:fade',
            'UT': 'ergebnissForm:selectedSuchErgebnisFormTable:{row}:j_idt161:4:fade',
            'VÖ': 'ergebnissForm:selectedSuchErgebnisFormTable:{row}:j_idt161:5:fade',
            'SI': 'ergebnissForm:selectedSuchErgebnisFormTable:{row}:j_idt161:6:fade',
        }
        
        control_name = detail_type_mapping.get(detail_type, detail_type_mapping['SI'])
        control_name = control_name.format(row=row_index)
        
        try:
            self.browser.select_form(name="ergebnissForm")
            self.browser.form.new_control('hidden', control_name, {'value': control_name})
            response = self.browser.submit()
            return response.read().decode("utf-8")
            
        except mechanize.FormNotFoundError:
            logger.warning("Results form not found, using alternative fetch method")
            return self._fetch_detail_alternative(company, detail_type)
        except urllib.error.URLError as e:
            raise NetworkError(
                f"Failed to fetch detail page: {e.reason}",
                original_error=e
            ) from e
    
    def _fetch_detail_alternative(self, company: dict, detail_type: str) -> str:
        """Alternative method to fetch details when form is not available.
        
        This method constructs a direct request based on company information.
        Full implementation requires JSF viewstate handling.
        """
        register_num = company.get('register_num', '')
        _court = company.get('court', '')
        _state = company.get('state', '')
        
        logger.warning(
            "Alternative fetch not fully implemented for %s %s", 
            register_num, detail_type
        )
        return ""
    
    def _parse_details(
        self, 
        html: str, 
        company: dict, 
        detail_type: str
    ) -> CompanyDetails:
        """Parses detail HTML into CompanyDetails.
        
        Args:
            html: HTML content of detail page.
            company: Base company info from search.
            detail_type: Type of detail page.
            
        Returns:
            Parsed CompanyDetails.
        """
        if detail_type == "SI":
            return DetailsParser.parse_si(html, company)
        elif detail_type == "AD":
            return DetailsParser.parse_ad(html, company)
        elif detail_type == "UT":
            return DetailsParser.parse_ut(html, company)
        else:
            return DetailsParser.parse_si(html, company)
    
    def search_with_details(
        self,
        options: SearchOptions,
        fetch_details: bool = True,
        detail_type: str = "SI",
        force_refresh: bool = False,
    ) -> list[CompanyDetails]:
        """Searches for companies and optionally fetches details.
        
        Args:
            options: Search options.
            fetch_details: Whether to fetch details for each result.
            detail_type: Type of details to fetch (SI, AD, UT).
            force_refresh: Skip cache.
            
        Returns:
            List of CompanyDetails with full information.
        """
        companies = self.search_with_options(options, force_refresh=force_refresh)
        
        if not fetch_details:
            return [CompanyDetails.from_company(c) for c in companies]
        
        results: list[CompanyDetails] = []
        for i, company in enumerate(companies):
            company['row_index'] = i
            try:
                details = self.get_company_details(
                    company, 
                    detail_type=detail_type,
                    force_refresh=force_refresh
                )
                results.append(details)
            except (NetworkError, ParseError) as e:
                logger.warning("Failed to fetch details for %s: %s", 
                             company.get('name', 'unknown'), e)
                results.append(CompanyDetails.from_company(company))
        
        return results
    
    def _get_cache_key(self, query: str, options: str) -> str:
        """Generates cache key. Deprecated: use cache.get/set instead."""
        return self.cache._get_cache_key(query, options)
    
    def _get_cache_path(self, query: str, options: str) -> pathlib.Path:
        """Gets cache path. Deprecated: use cache.get/set instead."""
        return self.cache._get_cache_path(query, options)
    
    def _load_from_cache(self, query: str, options: str) -> Optional[CacheEntry]:
        """Loads from cache. Deprecated: use cache.get instead."""
        html = self.cache.get(query, options)
        if html is None:
            return None
        return CacheEntry(query=query, options=options, timestamp=time.time(), html=html)
    
    def _save_to_cache(self, query: str, options: str, html: str) -> None:
        """Saves to cache. Deprecated: use cache.set instead."""
        self.cache.set(query, options, html)


# =============================================================================
# CLI Layer
# =============================================================================

def pr_company_info(c: dict) -> None:
    """Prints company information to stdout.
    
    Args:
        c: Dictionary containing company information.
    """
    for tag in ('name', 'court', 'register_num', 'district', 'state', 'statusCurrent'):
        print(f"{tag}: {c.get(tag, '-')}")
    print('history:')
    for name, loc in c.get('history', []):
        print(name, loc)


def parse_args() -> argparse.Namespace:
    """Parses command-line arguments.
    
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
    
    # Detail options
    detail_group = parser.add_argument_group('Detail options')
    detail_group.add_argument(
        "--details",
        help="Fetch detailed information for each company result",
        action="store_true"
    )
    detail_group.add_argument(
        "--detail-type",
        dest="detail_type",
        help="Type of details to fetch: SI=structured, AD=printout, UT=owners",
        choices=["SI", "AD", "UT"],
        default="SI",
        metavar="TYPE"
    )
    
    args = parser.parse_args()
    
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


def get_details(
    company: dict,
    detail_type: str = "SI",
    force_refresh: bool = False,
    debug: bool = False,
) -> CompanyDetails:
    """Ruft detaillierte Unternehmensinformationen ab.
    
    Diese Funktion ruft erweiterte Informationen zu einem Unternehmen ab,
    das zuvor über search() gefunden wurde.
    
    Args:
        company: Unternehmen-Dictionary aus den Suchergebnissen.
        detail_type: Art der Details:
            - "SI": Strukturierter Registerinhalt (empfohlen)
            - "AD": Aktueller Abdruck
            - "UT": Unternehmensträger
        force_refresh: Cache ignorieren.
        debug: Debug-Logging aktivieren.
        
    Returns:
        CompanyDetails mit allen verfügbaren Informationen.
        
    Beispiel:
        >>> from handelsregister import search, get_details
        >>> 
        >>> # Erst suchen
        >>> companies = search("GASAG AG", keyword_option="exact")
        >>> 
        >>> # Dann Details abrufen
        >>> if companies:
        ...     details = get_details(companies[0])
        ...     print(f"Kapital: {details.capital} {details.currency}")
        ...     print(f"Rechtsform: {details.legal_form}")
    """
    if debug:
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    hr = HandelsRegister(debug=debug)
    hr.open_startpage()
    
    register_num = company.get('register_num', '')
    name = company.get('name', '')
    
    if register_num:
        search_opts = SearchOptions(
            keywords=name,
            keyword_option="exact",
        )
    else:
        search_opts = SearchOptions(
            keywords=name,
            keyword_option="all",
        )
    
    hr.search_with_options(search_opts, force_refresh=force_refresh)
    company['row_index'] = 0
    return hr.get_company_details(company, detail_type, force_refresh)


def pr_company_details(details: CompanyDetails) -> None:
    """Prints detailed company information to stdout.
    
    Args:
        details: CompanyDetails object with all information.
    """
    print(f"{'='*60}")
    print(f"Firma: {details.name}")
    print(f"Registernummer: {details.register_num}")
    print(f"Gericht: {details.court}")
    print(f"Bundesland: {details.state}")
    print(f"Status: {details.status}")
    
    if details.legal_form:
        print(f"Rechtsform: {details.legal_form}")
    
    if details.capital:
        currency = details.currency or "EUR"
        print(f"Kapital: {details.capital} {currency}")
    
    if details.address:
        print(f"Adresse: {details.address}")
    
    if details.purpose:
        print(f"Gegenstand: {details.purpose[:100]}{'...' if len(details.purpose) > 100 else ''}")
    
    if details.representatives:
        print("Vertretung:")
        for rep in details.representatives:
            loc = f" ({rep.location})" if rep.location else ""
            print(f"  - {rep.role}: {rep.name}{loc}")
    
    if details.owners:
        print("Gesellschafter:")
        for owner in details.owners:
            share = f" - {owner.share}" if owner.share else ""
            print(f"  - {owner.name}{share}")
    
    if details.registration_date:
        print(f"Eingetragen: {details.registration_date}")
    
    print()


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
        
        fetch_details = getattr(args, 'details', False)
        detail_type = getattr(args, 'detail_type', 'SI')
        
        if fetch_details:
            search_opts = hr._build_search_options()
            companies_details = hr.search_with_details(
                search_opts,
                fetch_details=True,
                detail_type=detail_type,
                force_refresh=getattr(args, 'force', False),
            )
            
            if companies_details:
                if args.json:
                    print(json.dumps([d.to_dict() for d in companies_details]))
                else:
                    for details in companies_details:
                        pr_company_details(details)
        else:
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
