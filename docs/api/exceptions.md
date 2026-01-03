# Exceptions

This page documents the exception types for error handling.

---

## Exception Hierarchy

```
Exception
└── HandelsregisterError (Base exception)
    ├── NetworkError
    ├── ParseError
    ├── FormError
    └── CacheError
```

---

## HandelsregisterError

::: handelsregister.HandelsregisterError
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

Base exception for all Handelsregister-related errors.

### Usage

```python
from handelsregister import search, HandelsregisterError

try:
    companies = search("Bank")
except HandelsregisterError as e:
    print(f"Handelsregister error: {e}")
```

---

## NetworkError

::: handelsregister.NetworkError
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

Raised when connection to the register portal fails.

### Usage

```python
from handelsregister import search, NetworkError

try:
    companies = search("Bank")
except NetworkError as e:
    print(f"Could not connect: {e}")
    # Maybe try again later or notify user
```

---

## ParseError

::: handelsregister.ParseError
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

Raised when the HTML response cannot be parsed.

This usually indicates the register portal has changed its HTML structure.

### Usage

```python
from handelsregister import search, ParseError

try:
    companies = search("Bank")
except ParseError as e:
    print(f"Could not parse response: {e}")
    print("The register portal may have changed.")
    print("Please report this issue on GitHub.")
```

---

## FormError

::: handelsregister.FormError
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

Raised when there's an error with form submission.

### Usage

```python
from handelsregister import search, FormError

try:
    companies = search("Bank")
except FormError as e:
    print(f"Form error: {e}")
```

---

## CacheError

::: handelsregister.CacheError
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

Raised when there's an error with the caching system.

### Usage

```python
from handelsregister import search, CacheError

try:
    companies = search("Bank")
except CacheError as e:
    print(f"Cache error: {e}")
    # Try without cache
    companies = search("Bank", force_refresh=True)
```

---

## Complete Error Handling

```python
from handelsregister import (
    search,
    get_details,
    HandelsregisterError,
    NetworkError,
    ParseError,
    FormError,
    CacheError,
)
import logging

logger = logging.getLogger(__name__)

def robust_search(keywords, **kwargs):
    """Search with comprehensive error handling."""
    try:
        return search(keywords, **kwargs)
    
    except NetworkError as e:
        logger.error(f"Connection failed: {e}")
        raise
    
    except ParseError as e:
        logger.error(f"Parse error: {e}")
        raise
    
    except FormError as e:
        logger.error(f"Form error: {e}")
        raise
    
    except CacheError as e:
        logger.warning(f"Cache error: {e}, retrying without cache")
        return search(keywords, use_cache=False, **kwargs)
    
    except HandelsregisterError as e:
        logger.error(f"General error: {e}")
        raise

def robust_get_details(company):
    """Get details with error handling."""
    try:
        return get_details(company)
    
    except HandelsregisterError as e:
        logger.error(f"Could not get details for {company.name}: {e}")
        return None
```

---

## Rate Limiting

!!! warning "Rate Limit"
    The register portal allows a maximum of **60 requests per hour**. While there's no dedicated `RateLimitError`, exceeding this limit may result in `NetworkError` or connection issues.

### Implementing Rate Limiting

```python
import time
from handelsregister import search

def search_with_delay(keywords_list):
    """Search with rate limiting."""
    results = {}
    for keywords in keywords_list:
        results[keywords] = search(keywords)
        time.sleep(60)  # 1 minute between requests
    return results
```

---

## See Also

- [Using as Library](../guide/library.md) – Error handling examples
- [Best Practices](../guide/library.md#best-practices) – Retry patterns
