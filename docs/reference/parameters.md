# API Parameters

Complete reference of all parameters for the `search()` function.

## Parameter Overview

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `keywords` | `str` | Required | Search term for company names |
| `states` | `List[str]` | `None` | Filter by federal states |
| `register_type` | `str` | `None` | Filter by register type |
| `register_court` | `str` | `None` | Specific register court |
| `register_number` | `str` | `None` | Specific register number |
| `only_active` | `bool` | `False` | Only currently registered |
| `exact` | `bool` | `False` | Exact name match |
| `similar_sounding` | `bool` | `False` | Include similar-sounding names |
| `use_cache` | `bool` | `True` | Use cached results |

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

### register_court

Filter by specific register court.

```python
# Only Berlin Charlottenburg
search("Bank", register_court="Berlin (Charlottenburg)")

# Only Munich
search("Bank", register_court="München")
```

**Type:** `str` or `None`

**Note:** Court names must match exactly as they appear in the register.

---

### register_number

Search for a specific register number.

```python
# Find by register number
search("", register_number="HRB 12345")

# Combined with court
search("", 
       register_court="Berlin (Charlottenburg)", 
       register_number="HRB 44343")
```

**Type:** `str` or `None`

---

### only_active

Filter for currently registered companies only.

```python
# Only active companies
search("Bank", only_active=True)

# Include deleted/merged (default)
search("Bank", only_active=False)
```

**Type:** `bool`

**Default:** `False`

---

### exact

Require exact name match instead of partial.

```python
# Exact match - finds only "GASAG AG"
search("GASAG AG", exact=True)

# Partial match - finds "GASAG AG", "GASAG Beteiligungs GmbH", etc.
search("GASAG", exact=False)
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

### use_cache

Whether to use cached results.

```python
# Use cache (default)
search("Bank", use_cache=True)

# Always fetch fresh data
search("Bank", use_cache=False)
```

**Type:** `bool`

**Default:** `True`

---

## Complete Example

```python
from handelsregister import search

# Full example with all parameters
companies = search(
    keywords="Bank",              # Search for "Bank"
    states=["BE", "HH"],          # In Berlin and Hamburg
    register_type="HRB",          # Only corporations
    register_court=None,          # Any court
    register_number=None,         # Any number
    only_active=True,             # Only active companies
    exact=False,                  # Partial match OK
    similar_sounding=False,       # No phonetic search
    use_cache=True,               # Use cache
)

print(f"Found: {len(companies)} companies")
```

---

## CLI Equivalent

| Python Parameter | CLI Option |
|-----------------|------------|
| `keywords` | `-s, --search` |
| `states` | `--states` |
| `register_type` | `--register-type` |
| `only_active` | `--active-only` |
| `exact` | `--exact` |
| `use_cache=False` | `--no-cache` |

```bash
handelsregister \
    -s "Bank" \
    --states BE,HH \
    --register-type HRB \
    --active-only
```

---

## See Also

- [State Codes](states.md) – Valid state codes
- [Register Types](registers.md) – Valid register types
- [Using as Library](../guide/library.md) – More examples

