# API Parameters

Complete reference of all parameters for the `search()` function.

## Parameter Overview

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `keywords` | `str` | Required | Search term for company names |
| `keyword_option` | `KeywordMatch` or `str` | `"all"` | How to match keywords: "all", "min", or "exact" |
| `states` | `List[State]` or `List[str]` | `None` | Filter by federal states |
| `register_type` | `RegisterType` or `str` | `None` | Filter by register type |
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
from handelsregister import search, State

# Single state (recommended: Enum)
search("Bank", states=[State.BE])

# Multiple states (recommended: Enums)
search("Bank", states=[State.BE, State.HH, State.BY])

# String-based API still works
search("Bank", states=["BE"])
search("Bank", states=["BE", "HH", "BY"])

# All states (default - don't specify)
search("Bank")
```

**Type:** `List[State]` or `List[str]` or `None`

**Valid values:** `BW`, `BY`, `BE`, `BB`, `HB`, `HH`, `HE`, `MV`, `NI`, `NW`, `RP`, `SL`, `SN`, `ST`, `SH`, `TH`

**Recommended:** Use `State` enum for IDE autocomplete: `State.BE`, `State.HH`, etc.

---

### register_type

Filter by register type. See [Register Types](registers.md).

```python
from handelsregister import search, RegisterType

# Only corporations (GmbH, AG) - recommended: Enum
search("Bank", register_type=RegisterType.HRB)

# Only partnerships (KG, OHG)
search("Consulting", register_type=RegisterType.HRA)

# Cooperatives
search("Wohnungsbau", register_type=RegisterType.GnR)

# String-based API still works
search("Bank", register_type="HRB")
```

**Type:** `RegisterType` or `str` or `None`

**Valid values:** `HRA`, `HRB`, `GnR`, `PR`, `VR`

**Recommended:** Use `RegisterType` enum for IDE autocomplete: `RegisterType.HRB`, `RegisterType.HRA`, etc.

---

### keyword_option

How to match keywords in the search.

```python
from handelsregister import search, KeywordMatch

# All keywords must match (default) - recommended: Enum
search("Deutsche Bank", keyword_option=KeywordMatch.ALL)

# At least one keyword must match
search("Deutsche Bank", keyword_option=KeywordMatch.MIN)

# Exact name match
search("GASAG AG", keyword_option=KeywordMatch.EXACT)

# String-based API still works
search("Deutsche Bank", keyword_option="all")
search("GASAG AG", keyword_option="exact")
```

**Type:** `KeywordMatch` or `str`

**Default:** `"all"` or `KeywordMatch.ALL`

**Valid values:** `"all"` / `KeywordMatch.ALL`, `"min"` / `KeywordMatch.MIN`, `"exact"` / `KeywordMatch.EXACT`

**Recommended:** Use `KeywordMatch` enum for IDE autocomplete: `KeywordMatch.ALL`, `KeywordMatch.EXACT`, etc.

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
from handelsregister import search, State, KeywordMatch, RegisterType

# Full example with all parameters (recommended: Enums)
companies = search(
    keywords="Bank",                      # Search for "Bank"
    keyword_option=KeywordMatch.ALL,     # All keywords must match
    states=[State.BE, State.HH],         # In Berlin and Hamburg
    register_type=RegisterType.HRB,      # Only corporations
    register_number=None,                # Any number
    include_deleted=False,               # Only active companies
    similar_sounding=False,              # No phonetic search
    results_per_page=100,                # Maximum results
    force_refresh=False,                 # Use cache
    debug=False,                         # No debug output
)

# String-based API still works
companies = search(
    keywords="Bank",
    keyword_option="all",
    states=["BE", "HH"],
    register_type="HRB",
    register_number=None,
    include_deleted=False,
    similar_sounding=False,
    results_per_page=100,
    force_refresh=False,
    debug=False,
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

