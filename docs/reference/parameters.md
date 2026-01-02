# API Parameters

Complete reference of all parameters for the `search()` function.

## Parameter Overview

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `keywords` | `str` | Required | Search term for company names |
| `keyword_option` | `str` | `"all"` | How to match keywords: "all", "min", or "exact" |
| `states` | `List[str]` | `None` | Filter by federal states |
| `register_type` | `str` | `None` | Filter by register type |
| `register_number` | `str` | `None` | Specific register number |
| `include_deleted` | `bool` | `False` | Include deleted/historical entries |
| `similar_sounding` | `bool` | `False` | Include similar-sounding names |
| `results_per_page` | `int` | `100` | Number of results per page (10, 25, 50, 100) |
| `force_refresh` | `bool` | `False` | Bypass cache and fetch fresh data |
| `debug` | `bool` | `False` | Enable debug logging |

---

## Parameter Details

### keywords (required)

The main search term. Searches in company names.

```python
# Single word
search("Bank")

# Multiple words
search("Deutsche Bank AG")

# Partial name
search("Deutsche")  # Finds "Deutsche Bahn", "Deutsche Bank", etc.
```

**Tips:**

- Use distinctive words for better results
- Avoid very common words like "GmbH" alone
- Add legal form for more specific results: "Mustermann GmbH"

---

### states

List of state codes to filter results. See [State Codes](states.md).

```python
# Single state
search("Bank", states=["BE"])

# Multiple states
search("Bank", states=["BE", "HH", "BY"])

# All states (default - don't specify)
search("Bank")
```

**Type:** `List[str]` or `None`

**Valid values:** `BW`, `BY`, `BE`, `BB`, `HB`, `HH`, `HE`, `MV`, `NI`, `NW`, `RP`, `SL`, `SN`, `ST`, `SH`, `TH`

---

### register_type

Filter by register type. See [Register Types](registers.md).

```python
# Only corporations (GmbH, AG)
search("Bank", register_type="HRB")

# Only partnerships (KG, OHG)
search("Consulting", register_type="HRA")

# Cooperatives
search("Wohnungsbau", register_type="GnR")
```

**Type:** `str` or `None`

**Valid values:** `HRA`, `HRB`, `GnR`, `PR`, `VR`

---

### keyword_option

How to match keywords in the search.

```python
# All keywords must match (default)
search("Deutsche Bank", keyword_option="all")

# At least one keyword must match
search("Deutsche Bank", keyword_option="min")

# Exact name match
search("GASAG AG", keyword_option="exact")
```

**Type:** `str`

**Default:** `"all"`

**Valid values:** `"all"`, `"min"`, `"exact"`

---

### register_number

Search for a specific register number.

```python
# Find by register number
search("", register_number="HRB 12345")

# Combined with keywords
search("GASAG", register_number="HRB 44343")
```

**Type:** `str` or `None`

---

### include_deleted

Include deleted/historical entries in results.

```python
# Include deleted entries
search("Bank", include_deleted=True)

# Only currently registered (default)
search("Bank", include_deleted=False)
```

**Type:** `bool`

**Default:** `False`

---

### similar_sounding

Include companies with similar-sounding names (phonetic search).

```python
# Include similar names (Meyer, Meier, Mayer, etc.)
search("Müller", similar_sounding=True)
```

**Type:** `bool`

**Default:** `False`

**Note:** This can significantly increase the number of results.

---

### results_per_page

Number of results to return per page.

```python
# Get 50 results per page
search("Bank", results_per_page=50)

# Get maximum results (100)
search("Bank", results_per_page=100)
```

**Type:** `int`

**Default:** `100`

**Valid values:** `10`, `25`, `50`, `100`

---

### force_refresh

Bypass cache and fetch fresh data from the website.

```python
# Use cache (default)
search("Bank", force_refresh=False)

# Always fetch fresh data
search("Bank", force_refresh=True)
```

**Type:** `bool`

**Default:** `False`

---

### debug

Enable debug logging for troubleshooting.

```python
# Enable debug output
search("Bank", debug=True)
```

**Type:** `bool`

**Default:** `False`

---

## Complete Example

```python
from handelsregister import search

# Full example with all parameters
companies = search(
    keywords="Bank",              # Search for "Bank"
    keyword_option="all",         # All keywords must match
    states=["BE", "HH"],          # In Berlin and Hamburg
    register_type="HRB",          # Only corporations
    register_number=None,         # Any number
    include_deleted=False,        # Only active companies
    similar_sounding=False,        # No phonetic search
    results_per_page=100,         # Maximum results
    force_refresh=False,          # Use cache
    debug=False,                  # No debug output
)

print(f"Found: {len(companies)} companies")
```

---

## CLI Equivalent

| Python Parameter | CLI Option |
|-----------------|------------|
| `keywords` | `-s, --schlagwoerter` |
| `keyword_option` | `-so, --schlagwortOptionen` |
| `states` | `--states` |
| `register_type` | `--register-type` |
| `register_number` | `--register-number` |
| `include_deleted` | `--include-deleted` |
| `similar_sounding` | `--similar-sounding` |
| `results_per_page` | `--results-per-page` |
| `force_refresh=True` | `-f, --force` |
| `debug=True` | `-d, --debug` |

```bash
handelsregister \
    -s "Bank" \
    --states BE,HH \
    --register-type HRB \
    --schlagwortOptionen all
```

---

## See Also

- [State Codes](states.md) – Valid state codes
- [Register Types](registers.md) – Valid register types
- [Using as Library](../guide/library.md) – More examples

