# Quickstart

Get started with Handelsregister in just a few minutes.

## Installation

```bash
git clone https://github.com/bundesAPI/handelsregister.git
cd handelsregister
uv sync
```

---

## First Search

### Using Python

```python
from handelsregister import search

# Search for companies
results = search("Deutsche Bahn")

# Display results
for company in results:
    print(f"{company['name']}")
    print(f"  Register: {company['register_court']} {company['register_num']}")
    print(f"  Status: {company['status']}")
    print()
```

**Output:**

```
Deutsche Bahn Aktiengesellschaft
  Register: Berlin (Charlottenburg) HRB 50000
  Status: currently registered

DB Fernverkehr Aktiengesellschaft
  Register: Frankfurt am Main HRB 12345
  Status: currently registered
...
```

### Using CLI

```bash
# Search for "Deutsche Bahn"
handelsregister -s "Deutsche Bahn"

# As JSON output
handelsregister -s "Deutsche Bahn" --json
```

---

## Filtering Results

### By State

```python
from handelsregister import search

# Only Berlin companies
results = search("Bank", states=["BE"])
```

```bash
# CLI: Berlin only
handelsregister -s "Bank" --states BE
```

### By Register Type

```python
# Only corporations (HRB)
results = search("GmbH", register_type="HRB")
```

```bash
# CLI
handelsregister -s "GmbH" --register-type HRB
```

### Combined Filters

```python
# Banks in Berlin or Hamburg, only HRB
results = search(
    keywords="Bank",
    states=["BE", "HH"],
    register_type="HRB",
    only_active=True
)
```

---

## Fetching Details

```python
from handelsregister import search, get_details

# Search
companies = search("GASAG AG", exact=True)

if companies:
    # Fetch detailed information
    details = get_details(companies[0])
    
    print(f"Company: {details.name}")
    print(f"Capital: {details.capital} {details.currency}")
    print(f"Address: {details.address}")
    
    print("Representatives:")
    for rep in details.representatives:
        print(f"  - {rep.name} ({rep.role})")
```

---

## Caching

The package automatically caches results:

```python
from handelsregister import search

# First search: requests the register portal
results1 = search("Deutsche Bank")

# Second search: uses cache (faster)
results2 = search("Deutsche Bank")

# Force fresh search (bypass cache)
results3 = search("Deutsche Bank", use_cache=False)
```

Default cache duration: **24 hours**

---

## Error Handling

```python
from handelsregister import search, SearchError, RateLimitError

try:
    results = search("Deutsche Bahn")
except RateLimitError:
    print("Too many requests! Max 60 per hour allowed.")
except SearchError as e:
    print(f"Search error: {e}")
```

---

## Next Steps

<div class="grid cards" markdown>

-   :material-book-open-variant:{ .lg .middle } __User Guide__

    ---

    Detailed documentation for all features

    [:octicons-arrow-right-24: User Guide](guide/index.md)

-   :material-api:{ .lg .middle } __API Reference__

    ---

    Complete technical reference

    [:octicons-arrow-right-24: API Reference](api/index.md)

-   :material-code-braces:{ .lg .middle } __Examples__

    ---

    Practical code examples

    [:octicons-arrow-right-24: Examples](examples/simple.md)

</div>
