# Advanced Examples

More complex examples for advanced use cases.

## Batch Processing

### Process Multiple Keywords

```python
import time
from handelsregister import search

keywords = ["Bank", "Versicherung", "Immobilien", "Consulting"]

all_results = {}
for keyword in keywords:
    print(f"Searching: {keyword}")
    results = search(keyword, states=["BE"])
    all_results[keyword] = results
    
    # Respect rate limit
    time.sleep(60)

# Summary
for keyword, results in all_results.items():
    print(f"{keyword}: {len(results)} companies")
```

### Process All States

```python
import time
from handelsregister import search

STATES = ["BW", "BY", "BE", "BB", "HB", "HH", "HE", "MV", 
          "NI", "NW", "RP", "SL", "SN", "ST", "SH", "TH"]

results_by_state = {}
for state in STATES:
    print(f"Processing {state}...")
    results = search("Bank", states=[state], register_type="HRB")
    results_by_state[state] = len(results)
    time.sleep(60)

# Sort by count
sorted_states = sorted(results_by_state.items(), key=lambda x: x[1], reverse=True)
for state, count in sorted_states:
    print(f"{state}: {count} banks")
```

---

## Data Analysis

### Using pandas

```python
import pandas as pd
from handelsregister import search

# Search and convert to DataFrame
companies = search("Bank", states=["BE", "HH"])
df = pd.DataFrame(companies)

# Analysis
print("Companies by court:")
print(df['court'].value_counts())

print("\nCompanies by register type:")
print(df['register_type'].value_counts())

print("\nCompanies by status:")
print(df['status'].value_counts())
```

### Export to CSV

```python
import pandas as pd
from handelsregister import search, get_details

companies = search("Bank", states=["BE"])

# Get details for each
data = []
for company in companies[:10]:  # Limit for demo
    details = get_details(company)
    data.append({
        'name': details.name,
        'court': details.court,
        'number': details.register_number,
        'capital': details.capital,
        'city': details.address.city if details.address else None,
    })

df = pd.DataFrame(data)
df.to_csv('berlin_banks.csv', index=False)
```

---

## Parallel Processing

### Using ThreadPoolExecutor

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
from handelsregister import search
import time

keywords = ["Bank", "Versicherung", "Immobilien", "IT", "Consulting"]

def search_keyword(keyword):
    """Search with rate limit delay."""
    time.sleep(60)  # Rate limit
    return keyword, search(keyword, states=["BE"])

# Process in parallel with rate limiting
with ThreadPoolExecutor(max_workers=1) as executor:
    futures = {executor.submit(search_keyword, kw): kw for kw in keywords}
    
    for future in as_completed(futures):
        keyword, results = future.result()
        print(f"{keyword}: {len(results)} companies")
```

---

## Custom Caching

### Custom TTL

```python
from handelsregister import HandelsRegister, SearchCache

# Cache for 1 hour only
cache = SearchCache(ttl_hours=1)
hr = HandelsRegister(cache=cache)

# Use custom instance
companies = hr.search("Bank")
```

### Custom Cache Directory

```python
from handelsregister import SearchCache, HandelsRegister

# Use custom directory
cache = SearchCache(cache_dir="/tmp/hr-cache")
hr = HandelsRegister(cache=cache)

companies = hr.search("Bank")
```

### Cache Statistics

```python
from handelsregister import SearchCache

cache = SearchCache()

# Get statistics
stats = cache.get_stats()
print(f"Total entries: {stats['total']}")
print(f"Valid entries: {stats['valid']}")
print(f"Expired entries: {stats['expired']}")
print(f"Cache size: {stats['size_mb']:.2f} MB")

# Cleanup expired entries
removed = cache.cleanup_expired()
print(f"Removed {removed} expired entries")
```

---

## Building Reports

### Company Report

```python
from handelsregister import search, get_details

def generate_report(company_name: str) -> str:
    """Generate a detailed company report."""
    companies = search(company_name, keyword_option="exact")
    
    if not companies:
        return f"Company not found: {company_name}"
    
    details = get_details(companies[0])
    
    report = []
    report.append("=" * 60)
    report.append(f"  {details.name}")
    report.append("=" * 60)
    report.append("")
    
    report.append("REGISTRATION")
    report.append(f"  Court:  {details.court}")
    report.append(f"  Number: {details.register_type} {details.register_number}")
    report.append(f"  Status: {details.status}")
    report.append("")
    
    if details.capital:
        report.append("CAPITAL")
        report.append(f"  {details.capital} {details.currency}")
        report.append("")
    
    if details.address:
        report.append("ADDRESS")
        report.append(f"  {details.address.street}")
        report.append(f"  {details.address.postal_code} {details.address.city}")
        report.append("")
    
    if details.representatives:
        report.append("REPRESENTATIVES")
        for rep in details.representatives:
            report.append(f"  - {rep.name}")
            if rep.role:
                report.append(f"    Role: {rep.role}")
        report.append("")
    
    if details.business_purpose:
        report.append("BUSINESS PURPOSE")
        purpose = details.business_purpose
        if len(purpose) > 200:
            purpose = purpose[:200] + "..."
        report.append(f"  {purpose}")
    
    return "\n".join(report)

# Usage
print(generate_report("GASAG AG"))
```

---

## Rate Limit Handling

### Automatic Retry

```python
import time
from handelsregister import search, RateLimitError

def search_with_retry(keywords, max_retries=3, **kwargs):
    """Search with automatic retry on rate limit."""
    for attempt in range(max_retries):
        try:
            return search(keywords, **kwargs)
        except RateLimitError:
            if attempt == max_retries - 1:
                raise
            wait_time = 60 * (attempt + 1)
            print(f"Rate limited, waiting {wait_time}s...")
            time.sleep(wait_time)

# Usage
companies = search_with_retry("Bank", states=["BE"])
```

### Rate Limiter Class

```python
import time
from collections import deque
from handelsregister import search

class RateLimiter:
    """Enforce rate limiting for API calls."""
    
    def __init__(self, max_requests: int = 60, window_seconds: int = 3600):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = deque()
    
    def wait_if_needed(self):
        """Wait if rate limit would be exceeded."""
        now = time.time()
        
        # Remove old requests
        while self.requests and self.requests[0] < now - self.window_seconds:
            self.requests.popleft()
        
        if len(self.requests) >= self.max_requests:
            wait_time = self.requests[0] + self.window_seconds - now
            if wait_time > 0:
                print(f"Rate limit reached, waiting {wait_time:.0f}s...")
                time.sleep(wait_time)
        
        self.requests.append(now)
    
    def search(self, *args, **kwargs):
        """Search with rate limiting."""
        self.wait_if_needed()
        return search(*args, **kwargs)

# Usage
limiter = RateLimiter()

keywords = ["Bank", "Insurance", "Consulting"]
for keyword in keywords:
    results = limiter.search(keyword)
    print(f"{keyword}: {len(results)} results")
```

---

## See Also

- [Simple Examples](simple.md) – Basic examples
- [Integration Examples](integrations.md) – Framework integrations
- [API Reference](../api/index.md) – Technical documentation

