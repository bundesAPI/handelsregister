# Public Functions

This page documents the public functions available in the Handelsregister package.

---

## search

::: handelsregister.search
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

### Usage Examples

```python
from handelsregister import search

# Simple search
companies = search("Deutsche Bahn")

# With filters
companies = search(
    keywords="Bank",
    register_art="HRB",
    register_gericht="Berlin"
)

# Search by register number
companies = search(
    schlagwoerter="",
    register_nummer="12345",
    register_gericht="Berlin (Charlottenburg)"
)
```

### Return Value

Returns a list of dictionaries with company information:

```python
[
    {
        "name": "Deutsche Bank AG",
        "court": "Frankfurt am Main",
        "register_num": "HRB 12345 B",
        "state": "Hessen",
        "status": "currently registered",
        "history": []
    },
    ...
]
```

---

## get_details

::: handelsregister.get_details
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

### Usage Examples

```python
from handelsregister import search, get_details

# Search first
companies = search("GASAG AG")

# Then get details
if companies:
    details = get_details(companies[0])
    
    print(details.name)
    print(details.capital)
    print(details.address)
    print(details.representatives)
```

### Return Value

Returns a `CompanyDetails` object with full company information.

See [Data Models: CompanyDetails](models.md#handelsregister.CompanyDetails) for details.

---

## main

::: handelsregister.cli.main
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

The CLI entry point. This function is called when running `handelsregister` from the command line.

### Usage

```bash
# Run via command line
handelsregister -s "Deutsche Bahn"

# Or via Python
python -m handelsregister -s "Deutsche Bahn"
```
