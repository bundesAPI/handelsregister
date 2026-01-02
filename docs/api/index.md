# API Reference

Complete technical documentation for the Handelsregister package.

## Overview

The package exposes the following main components:

| Component | Type | Description |
|-----------|------|-------------|
| [`search()`](functions.md#handelsregister.search) | Function | Search for companies |
| [`get_details()`](functions.md#handelsregister.get_details) | Function | Get detailed company information |
| [`HandelsRegister`](classes.md#handelsregister.HandelsRegister) | Class | Main class for register access |
| [`SearchCache`](classes.md#handelsregister.SearchCache) | Class | Caching mechanism |
| [`Company`](models.md#handelsregister.Company) | Dataclass | Company from search results |
| [`CompanyDetails`](models.md#handelsregister.CompanyDetails) | Dataclass | Detailed company information |

---

## Quick Links

<div class="grid cards" markdown>

-   :material-function:{ .lg .middle } __Functions__

    ---

    Public functions for searching and fetching data.

    [:octicons-arrow-right-24: Functions](functions.md)

-   :material-class:{ .lg .middle } __Classes__

    ---

    Core classes for register access and caching.

    [:octicons-arrow-right-24: Classes](classes.md)

-   :material-database:{ .lg .middle } __Data Models__

    ---

    Dataclasses for structured data representation.

    [:octicons-arrow-right-24: Data Models](models.md)

-   :material-alert-circle:{ .lg .middle } __Exceptions__

    ---

    Exception types for error handling.

    [:octicons-arrow-right-24: Exceptions](exceptions.md)

</div>

---

## Module Structure

```
handelsregister
├── search()              # Main search function
├── get_details()         # Get company details
├── clear_cache()         # Clear the cache
│
├── HandelsRegister       # Main class
│   ├── search()
│   ├── get_details()
│   └── ...
│
├── SearchCache           # Caching
│   ├── get()
│   ├── set()
│   ├── clear()
│   └── ...
│
├── Data Models
│   ├── Company
│   ├── CompanyDetails
│   ├── Address
│   ├── Representative
│   ├── Owner
│   └── HistoryEntry
│
└── Exceptions
    ├── SearchError
    ├── RateLimitError
    ├── ConnectionError
    └── ParseError
```

---

## Usage Pattern

```python
from handelsregister import (
    # Functions
    search,
    get_details,
    clear_cache,
    
    # Classes
    HandelsRegister,
    SearchCache,
    
    # Data Models
    Company,
    CompanyDetails,
    Address,
    Representative,
    
    # Exceptions
    SearchError,
    RateLimitError,
)

# Basic usage
companies = search("Deutsche Bahn")

# With error handling
try:
    companies = search("Bank", states=["BE"])
    for company in companies:
        details = get_details(company)
        process(details)
except RateLimitError:
    print("Rate limit exceeded")
except SearchError as e:
    print(f"Error: {e}")
```

---

## Type Hints

The package is fully typed. You can use type hints in your code:

```python
from handelsregister import search, get_details
from handelsregister import Company, CompanyDetails
from typing import List

def find_banks(state: str) -> List[Company]:
    """Find all banks in a state."""
    return search("Bank", states=[state], register_type="HRB")

def get_capital(company: Company) -> str | None:
    """Get the capital of a company."""
    details: CompanyDetails = get_details(company)
    return details.capital
```

