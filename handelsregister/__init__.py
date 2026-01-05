"""Python client for the German Handelsregister (commercial register).

This package provides both a CLI tool and a library interface to search the
Handelsregister portal without using a browser. Built as part of the bundesAPI
initiative to make German government data more accessible.
"""

from __future__ import annotations

# Import all public API components for backward compatibility
from .cache import SearchCache

# Import public API functions
from .cli import get_details, pr_company_details, pr_company_info, search, search_batch
from .client import HandelsRegister
from .constants import (
    KEYWORD_OPTIONS,
    REGISTER_TYPES,
    RESULTS_PER_PAGE_OPTIONS,
    STATE_CODES,
    SUFFIX_MAP,
    KeywordMatch,
    RegisterType,
    State,
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
from .si_xml import SIXMLParser, parse_si_xml

# Package metadata
__version__ = "0.3.0"
__all__ = [
    "BASE_URL",
    "DEFAULT_CACHE_TTL_SECONDS",
    "DETAILS_CACHE_TTL_SECONDS",
    "KEYWORD_OPTIONS",
    "KeywordMatch",
    "MAX_RETRIES",
    "RATE_LIMIT_CALLS",
    "RATE_LIMIT_PERIOD",
    "RegisterType",
    "REGISTER_TYPES",
    "REQUEST_TIMEOUT",
    "RESULTS_PER_PAGE_OPTIONS",
    "RETRY_WAIT_MAX",
    "RETRY_WAIT_MIN",
    "State",
    "STATE_CODES",
    "SUFFIX_MAP",
    # Main classes
    "Address",
    "CacheEntry",
    "CacheError",
    "Company",
    "CompanyDetails",
    "DetailsParser",
    "FormError",
    "HandelsRegister",
    "HandelsregisterError",
    "HistoryEntry",
    "NetworkError",
    "Owner",
    "ParseError",
    "PartialResultError",
    "Representative",
    "ResultParser",
    "SearchCache",
    "SearchOptions",
    "Settings",
    "SIXMLParser",
    "build_url",
    "get_companies_in_searchresults",
    "get_details",
    "parse_result",
    "parse_si_xml",
    "pr_company_details",
    "pr_company_info",
    "schlagwortOptionen",
    "search",
    "search_batch",
    "settings",
]
