"""Python client for the German Handelsregister (commercial register).

This package provides both a CLI tool and a library interface to search the
Handelsregister portal without using a browser. Built as part of the bundesAPI
initiative to make German government data more accessible.
"""

from __future__ import annotations

# Import all public API components for backward compatibility
from .cache import SearchCache
from .client import HandelsRegister
from .constants import (
    KEYWORD_OPTIONS,
    REGISTER_TYPES,
    RESULTS_PER_PAGE_OPTIONS,
    STATE_CODES,
    SUFFIX_MAP,
    build_url,
    schlagwortOptionen,
)
from .exceptions import (
    CacheError,
    FormError,
    HandelsregisterError,
    NetworkError,
    ParseError,
    PartialResultError,
)
from .models import (
    Address,
    CacheEntry,
    Company,
    CompanyDetails,
    HistoryEntry,
    Owner,
    Representative,
    SearchOptions,
)
from .parser import (
    DetailsParser,
    ResultParser,
    get_companies_in_searchresults,
    parse_result,
)
from .settings import (
    BASE_URL,
    DEFAULT_CACHE_TTL_SECONDS,
    DETAILS_CACHE_TTL_SECONDS,
    MAX_RETRIES,
    RATE_LIMIT_CALLS,
    RATE_LIMIT_PERIOD,
    REQUEST_TIMEOUT,
    RETRY_WAIT_MAX,
    RETRY_WAIT_MIN,
    Settings,
    settings,
)

# Import public API functions
from .cli import get_details, pr_company_details, pr_company_info, search, search_batch

# Package metadata
__version__ = "0.2.0"
__all__ = [
    # Main classes
    "HandelsRegister",
    "SearchCache",
    "SearchOptions",
    # Data models
    "Address",
    "CacheEntry",
    "Company",
    "CompanyDetails",
    "HistoryEntry",
    "Owner",
    "Representative",
    # Parsers
    "DetailsParser",
    "ResultParser",
    # Exceptions
    "CacheError",
    "FormError",
    "HandelsregisterError",
    "NetworkError",
    "ParseError",
    "PartialResultError",
    # Public API functions
    "search",
    "search_batch",
    "get_details",
    "pr_company_info",
    "pr_company_details",
    # Constants
    "KEYWORD_OPTIONS",
    "REGISTER_TYPES",
    "RESULTS_PER_PAGE_OPTIONS",
    "STATE_CODES",
    "SUFFIX_MAP",
    "build_url",
    "schlagwortOptionen",
    # Settings
    "Settings",
    "settings",
    "BASE_URL",
    "DEFAULT_CACHE_TTL_SECONDS",
    "DETAILS_CACHE_TTL_SECONDS",
    "REQUEST_TIMEOUT",
    "MAX_RETRIES",
    "RETRY_WAIT_MIN",
    "RETRY_WAIT_MAX",
    "RATE_LIMIT_CALLS",
    "RATE_LIMIT_PERIOD",
    # Backward compatibility functions
    "parse_result",
    "get_companies_in_searchresults",
]

