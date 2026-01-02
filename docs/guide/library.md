# Using as Library

This chapter explains how to use Handelsregister as a Python library in your applications.

## Basic Usage

### The `search()` Function

The `search()` function is the main entry point for company searches:

```python
from handelsregister import search

# Simple search
companies = search("Deutsche Bahn")

# Process results
for company in companies:
    print(f"Name: {company['name']}")
    print(f"Court: {company['register_court']}")
    print(f"Number: {company['register_num']}")
    print(f"Status: {company['status']}")
    print("---")
```

### Return Value

The function returns a list of dictionaries with the following keys:

| Key | Type | Description |
|-----|------|-------------|
| `name` | `str` | Company name |
| `register_court` | `str` | Register court |
| `register_num` | `str` | Register number (e.g., "HRB 12345") |
| `status` | `str` | Registration status |
| `state` | `str` | State code (e.g., "BE") |
| `history` | `list` | List of historical entries |

---

## Search Parameters

### All Parameters

```python
companies = search(
    keywords="Bank",              # Search term (required)
    states=["BE", "HH"],          # Filter by states
    register_type="HRB",          # Filter by register type
    register_court="Berlin",      # Specific register court
    register_number="12345",      # Specific register number
    only_active=True,             # Only currently registered
    exact=False,                  # Exact name match
    use_cache=True,               # Use caching
    similar_sounding=False,       # Include similar-sounding names
)
```

### Parameter Details

#### `keywords` (required)
The search term for company names:

```python
# Partial match
search("Deutsche")  # Finds "Deutsche Bahn", "Deutsche Bank", etc.

# Multiple words
search("Deutsche Bank AG")
```

#### `states`
Filter by German federal states using ISO codes:

```python
# Single state
search("Bank", states=["BE"])

# Multiple states
search("Bank", states=["BE", "HH", "BY"])
```

See [State Codes](../reference/states.md) for all codes.

#### `register_type`
Filter by register type:

```python
# Only HRB (corporations)
search("GmbH", register_type="HRB")

# Only HRA (sole proprietors, partnerships)
search("KG", register_type="HRA")
```

See [Register Types](../reference/registers.md) for all types.

#### `only_active`
Filter for currently registered companies:

```python
# Only active companies
search("Bank", only_active=True)

# Include deleted/merged companies
search("Bank", only_active=False)
```

#### `exact`
Require exact name match:

```python
# Exact match only
search("GASAG AG", exact=True)

# Partial matches allowed (default)
search("GASAG", exact=False)
```

---

## Working with Results

### Iterating Results

```python
companies = search("Deutsche Bahn")

# As list
for company in companies:
    process(company)

# With index
for i, company in enumerate(companies):
    print(f"{i+1}. {company['name']}")

# Filter in Python
berlin_companies = [
    c for c in companies 
    if c['state'] == 'BE'
]
```

### Checking for Results

```python
companies = search("xyz123nonexistent")

if not companies:
    print("No companies found")
else:
    print(f"Found {len(companies)} companies")
```

### Converting to DataFrame

```python
import pandas as pd
from handelsregister import search

companies = search("Bank", states=["BE"])

# Convert to DataFrame
df = pd.DataFrame(companies)

# Analyze
print(df.groupby('register_court').size())
```

---

## Advanced Usage

### Using the HandelsRegister Class

For more control, use the `HandelsRegister` class directly:

```python
from handelsregister import HandelsRegister

# Create instance
hr = HandelsRegister()

# Search with full control
results = hr.search(
    keywords="Bank",
    register_type="HRB",
    states=["BE"]
)

# Get details
if results:
    details = hr.get_details(results[0])
```

### Custom Cache Configuration

```python
from handelsregister import HandelsRegister, SearchCache

# Custom cache with 1-hour TTL
cache = SearchCache(ttl_hours=1)

hr = HandelsRegister(cache=cache)
results = hr.search("Bank")
```

### Without Caching

```python
# Disable cache for this search
companies = search("Bank", use_cache=False)

# Or globally
hr = HandelsRegister(cache=None)
```

---

## Error Handling

```python
from handelsregister import (
    search,
    SearchError,
    RateLimitError,
    ConnectionError,
    ParseError
)

try:
    companies = search("Bank")
except RateLimitError:
    print("Rate limit exceeded (max 60/hour)")
    # Wait and retry
except ConnectionError:
    print("Could not connect to register portal")
except ParseError:
    print("Error parsing response")
except SearchError as e:
    print(f"General search error: {e}")
```

### Retry Logic

```python
import time
from handelsregister import search, RateLimitError

def search_with_retry(keywords, max_retries=3):
    for attempt in range(max_retries):
        try:
            return search(keywords)
        except RateLimitError:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 60  # 1, 2, 3 minutes
                print(f"Rate limited, waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise
```

---

## Best Practices

### 1. Respect Rate Limits

```python
import time

keywords_list = ["Bank", "Versicherung", "AG", ...]

for keywords in keywords_list:
    results = search(keywords)
    process(results)
    time.sleep(60)  # Wait 1 minute between searches
```

### 2. Use Caching

```python
# Cache is enabled by default
# Results are reused for 24 hours

companies = search("Bank")  # First call: hits portal
companies = search("Bank")  # Second call: from cache
```

### 3. Filter Server-Side

```python
# Good: Filter on the server
companies = search("Bank", states=["BE"], register_type="HRB")

# Less efficient: Filter client-side
companies = search("Bank")
berlin_hrb = [c for c in companies if c['state'] == 'BE']
```

### 4. Handle Empty Results

```python
companies = search(keywords)

if not companies:
    logger.info(f"No results for '{keywords}'")
    return []

# Continue processing
```

---

## See Also

- [API Reference: search()](../api/functions.md) – Technical details
- [Fetching Details](details.md) – How to get extended information
- [Examples](../examples/simple.md) – Code examples

