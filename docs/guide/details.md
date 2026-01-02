# Fetching Details

Learn how to retrieve extended company information beyond basic search results.

## Overview

The basic search returns limited information. For complete details, use the `get_details()` function:

| Search Result | Details |
|---------------|---------|
| Company name | ✓ Plus historical names |
| Register court | ✓ |
| Register number | ✓ |
| Status | ✓ Plus registration dates |
| | **Additional:** |
| | Capital (Stammkapital/Grundkapital) |
| | Business address |
| | Representatives (directors, board) |
| | Business purpose |
| | Owners (for partnerships) |
| | Complete history |

---

## Basic Usage

```python
from handelsregister import search, get_details

# First, search for the company
companies = search("GASAG AG", exact=True)

if companies:
    # Then fetch details
    details = get_details(companies[0])
    
    print(f"Company: {details.name}")
    print(f"Capital: {details.capital} {details.currency}")
```

---

## The CompanyDetails Object

The `get_details()` function returns a `CompanyDetails` dataclass:

### Basic Information

```python
details = get_details(company)

# Basic info
print(details.name)              # "GASAG AG"
print(details.register_court)    # "Berlin (Charlottenburg)"
print(details.register_number)   # "HRB 44343"
print(details.register_type)     # "HRB"
print(details.status)            # "currently registered"
```

### Capital

```python
# Share capital
print(details.capital)     # "306977800.00"
print(details.currency)    # "EUR"

# Formatted output
if details.capital:
    amount = float(details.capital)
    print(f"Capital: {amount:,.2f} {details.currency}")
    # Output: Capital: 306,977,800.00 EUR
```

### Address

The address is returned as an `Address` object:

```python
address = details.address

print(address.street)       # "GASAG-Platz 1"
print(address.postal_code)  # "10963"
print(address.city)         # "Berlin"
print(address.country)      # "Deutschland"

# Full address
print(address)
# GASAG-Platz 1
# 10963 Berlin
# Deutschland
```

### Representatives

Representatives (directors, board members) are returned as a list:

```python
for rep in details.representatives:
    print(f"Name: {rep.name}")
    print(f"Role: {rep.role}")
    print(f"Birth date: {rep.birth_date}")
    print(f"Location: {rep.location}")
    print("---")
```

**Output:**

```
Name: Dr. Gerhard Holtmeier
Role: Vorstandsvorsitzender
Birth date: 1960-05-15
Location: Berlin
---
Name: Stefan Michels
Role: Vorstand
Birth date: 1972-03-22
Location: Potsdam
---
```

### Owners (Partnerships)

For partnerships (KG, OHG, GbR), owner information is available:

```python
if details.owners:
    for owner in details.owners:
        print(f"Name: {owner.name}")
        print(f"Type: {owner.owner_type}")
        print(f"Share: {owner.share}")
        print(f"Liability: {owner.liability}")
```

### Business Purpose

```python
print("Business Purpose:")
print(details.business_purpose)
```

### History

The complete history of register entries:

```python
for entry in details.history:
    print(f"Date: {entry.date}")
    print(f"Type: {entry.entry_type}")
    print(f"Content: {entry.content[:100]}...")
    print("---")
```

---

## Complete Example

```python
from handelsregister import search, get_details

def show_company_details(name: str):
    """Display complete details for a company."""
    
    # Search
    companies = search(name, exact=True)
    
    if not companies:
        print(f"No company found: {name}")
        return
    
    # Get details
    details = get_details(companies[0])
    
    # Header
    print("=" * 60)
    print(f"  {details.name}")
    print("=" * 60)
    
    # Registration
    print(f"\nRegister: {details.register_court}")
    print(f"Number:   {details.register_type} {details.register_number}")
    print(f"Status:   {details.status}")
    
    # Capital
    if details.capital:
        amount = float(details.capital)
        print(f"\nCapital:  {amount:,.2f} {details.currency}")
    
    # Address
    if details.address:
        print(f"\nAddress:")
        print(f"  {details.address.street}")
        print(f"  {details.address.postal_code} {details.address.city}")
    
    # Representatives
    if details.representatives:
        print(f"\nRepresentatives ({len(details.representatives)}):")
        for rep in details.representatives:
            role = f" ({rep.role})" if rep.role else ""
            print(f"  • {rep.name}{role}")
    
    # Business purpose
    if details.business_purpose:
        print(f"\nBusiness Purpose:")
        # Truncate if too long
        purpose = details.business_purpose
        if len(purpose) > 200:
            purpose = purpose[:200] + "..."
        print(f"  {purpose}")

# Usage
show_company_details("GASAG AG")
```

---

## Caching Details

Details are cached separately from search results:

```python
# First call: fetches from portal
details1 = get_details(company)

# Second call: uses cache
details2 = get_details(company)

# Force fresh fetch
details3 = get_details(company, use_cache=False)
```

---

## Batch Processing

For multiple companies, process sequentially with delays:

```python
import time
from handelsregister import search, get_details

companies = search("Bank", states=["BE"])

all_details = []
for i, company in enumerate(companies[:10]):  # Limit for safety
    print(f"Fetching {i+1}/{len(companies)}: {company['name']}")
    
    details = get_details(company)
    all_details.append(details)
    
    # Respect rate limit: 60/hour = 1/minute
    time.sleep(60)

print(f"\nFetched details for {len(all_details)} companies")
```

---

## Error Handling

```python
from handelsregister import get_details, SearchError

try:
    details = get_details(company)
except SearchError as e:
    print(f"Could not fetch details: {e}")
    # Fallback to basic info from search result
    print(f"Company: {company['name']}")
```

---

## See Also

- [API Reference: get_details()](../api/functions.md) – Technical documentation
- [Data Models](../api/models.md) – CompanyDetails, Address, Representative
- [Caching](cache.md) – How caching works

