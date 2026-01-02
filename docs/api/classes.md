# Classes

This page documents the main classes of the Handelsregister package.

---

## HandelsRegister

::: handelsregister.HandelsRegister
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3
      members:
        - __init__
        - search
        - get_details

### Usage Examples

```python
from handelsregister import HandelsRegister

# Create instance
hr = HandelsRegister()

# Search
companies = hr.search("Deutsche Bahn")

# Get details
if companies:
    details = hr.get_details(companies[0])
```

### With Custom Cache

```python
from handelsregister import HandelsRegister, SearchCache

# Custom cache with 1-hour TTL
cache = SearchCache(ttl_hours=1)
hr = HandelsRegister(cache=cache)

# Without cache
hr = HandelsRegister(cache=None)
```

---

## SearchCache

::: handelsregister.SearchCache
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3
      members:
        - __init__
        - get
        - set
        - clear
        - cleanup_expired
        - get_stats

### Usage Examples

```python
from handelsregister import SearchCache

# Default cache
cache = SearchCache()

# Custom TTL
cache = SearchCache(ttl_hours=1)

# Custom directory
cache = SearchCache(cache_dir="/tmp/hr-cache")

# Get statistics
stats = cache.get_stats()
print(f"Entries: {stats['total']}")
print(f"Size: {stats['size_mb']:.2f} MB")

# Cleanup
cache.cleanup_expired()

# Clear all
cache.clear()
```

---

## ResultParser

::: handelsregister.ResultParser
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

### Internal Use

This class is primarily for internal use. It parses HTML search results from the register portal.

```python
from handelsregister import ResultParser

parser = ResultParser()
companies = parser.parse(html_content)
```

---

## DetailsParser

::: handelsregister.DetailsParser
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

### Internal Use

This class is primarily for internal use. It parses HTML detail pages from the register portal.

```python
from handelsregister import DetailsParser

parser = DetailsParser()
details = parser.parse(html_content)
```

