# Simple Examples

Basic examples to get started with the Handelsregister package.

## Search Examples

### Basic Search

```python
from handelsregister import search

# Search for companies containing "Deutsche Bahn"
companies = search("Deutsche Bahn")

print(f"Found {len(companies)} companies")
for company in companies:
    print(f"  - {company.name}")
```

### Search with State Filter

```python
from handelsregister import search

# Search for banks in Berlin
banks = search("Bank", states=["BE"])

print(f"Banks in Berlin: {len(banks)}")
```

### Search with Multiple Filters

```python
from handelsregister import search

# Active GmbHs in Hamburg
companies = search(
    keywords="Consulting",
    states=["HH"],
    register_type="HRB",
    include_deleted=False
)
```

### Exact Name Search

```python
from handelsregister import search

# Find exact company name
companies = search("GASAG AG", keyword_option="exact")

if companies:
    print(f"Found: {companies[0].name}")
else:
    print("Company not found")
```

---

## Working with Results

### Accessing Company Data

```python
from handelsregister import search

companies = search("Siemens AG", keyword_option="exact")

if companies:
    company = companies[0]
    
    print(f"Name: {company.name}")
    print(f"Court: {company.court}")
    print(f"Number: {company.register_num}")
    print(f"Status: {company.status}")
    print(f"State: {company.state}")
```

### Converting to List of Names

```python
from handelsregister import search

companies = search("Bank", states=["BE"])

# Extract just the names
names = [c.name for c in companies]
print(names)
```

### Filtering Results in Python

```python
from handelsregister import search

companies = search("Bank")

# Filter for specific criteria
large_banks = [
    c for c in companies
    if "AG" in c.name and c.status == 'currently registered'
]
```

---

## Getting Details

### Basic Details

```python
from handelsregister import search, get_details

# Search for company
companies = search("GASAG AG", keyword_option="exact")

if companies:
    # Get full details
    details = get_details(companies[0])
    
    print(f"Name: {details.name}")
    print(f"Capital: {details.capital} {details.currency}")
```

### Accessing Address

```python
from handelsregister import search, get_details

companies = search("GASAG AG", keyword_option="exact")
details = get_details(companies[0])

if details.address:
    print(f"Street: {details.address.street}")
    print(f"City: {details.address.postal_code} {details.address.city}")
```

### Listing Representatives

```python
from handelsregister import search, get_details

companies = search("Deutsche Bahn AG", keyword_option="exact")
details = get_details(companies[0])

print("Management:")
for rep in details.representatives:
    print(f"  - {rep.name}: {rep.role}")
```

---

## CLI Examples

### Basic CLI Search

```bash
# Simple search
handelsregister -s "Deutsche Bahn"

# Search in specific state
handelsregister -s "Bank" --states BE

# Multiple states
handelsregister -s "Bank" --states BE,HH,BY
```

### Output Formats

```bash
# Default output
handelsregister -s "GASAG"

# JSON output
handelsregister -s "GASAG" --json

# Compact output
handelsregister -s "GASAG" --compact
```

### With Details

```bash
# Get company details
handelsregister -s "GASAG AG" --exact --details
```

### Save to File

```bash
# Save JSON to file
handelsregister -s "Bank" --states BE --json > berlin_banks.json

# Count results
handelsregister -s "Bank" --json | jq 'length'
```

---

## Error Handling

### Basic Error Handling

```python
from handelsregister import search, SearchError

try:
    companies = search("Bank")
    print(f"Found {len(companies)} companies")
except SearchError as e:
    print(f"Search failed: {e}")
```

### Checking for Empty Results

```python
from handelsregister import search

companies = search("xyz123nonexistent")

if not companies:
    print("No companies found")
else:
    print(f"Found {len(companies)} companies")
```

---

## Next Steps

- [Advanced Examples](advanced.md) – More complex use cases
- [Integration Examples](integrations.md) – Using with other tools
- [API Reference](../api/index.md) – Complete documentation

