# Data Models

This page documents the dataclasses used for structured data representation.

---

## Company

::: handelsregister.Company
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Company name |
| `register_court` | `str` | Register court |
| `register_num` | `str` | Register number (e.g., "HRB 12345") |
| `register_type` | `str` | Register type (HRA, HRB, etc.) |
| `status` | `str` | Registration status |
| `state` | `str` | State code (e.g., "BE") |
| `history` | `List[HistoryEntry]` | Historical entries |

### Example

```python
company = Company(
    name="Deutsche Bank AG",
    register_court="Frankfurt am Main",
    register_num="HRB 12345",
    register_type="HRB",
    status="currently registered",
    state="HE",
    history=[]
)
```

---

## CompanyDetails

::: handelsregister.CompanyDetails
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Company name |
| `register_court` | `str` | Register court |
| `register_number` | `str` | Register number |
| `register_type` | `str` | Register type |
| `status` | `str` | Registration status |
| `capital` | `str \| None` | Share capital |
| `currency` | `str \| None` | Currency (EUR) |
| `address` | `Address \| None` | Business address |
| `representatives` | `List[Representative]` | Directors, board members |
| `owners` | `List[Owner]` | Shareholders (partnerships) |
| `business_purpose` | `str \| None` | Business purpose |
| `history` | `List[HistoryEntry]` | Complete history |

### Example

```python
details = CompanyDetails(
    name="GASAG AG",
    register_court="Berlin (Charlottenburg)",
    register_number="44343",
    register_type="HRB",
    status="currently registered",
    capital="306977800.00",
    currency="EUR",
    address=Address(
        street="GASAG-Platz 1",
        postal_code="10963",
        city="Berlin",
        country="Deutschland"
    ),
    representatives=[
        Representative(name="Dr. Gerhard Holtmeier", role="Vorstandsvorsitzender")
    ],
    owners=[],
    business_purpose="Versorgung mit Energie...",
    history=[]
)
```

---

## Address

::: handelsregister.Address
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `street` | `str \| None` | Street and house number |
| `postal_code` | `str \| None` | Postal code |
| `city` | `str \| None` | City |
| `country` | `str \| None` | Country |

### Example

```python
address = Address(
    street="GASAG-Platz 1",
    postal_code="10963",
    city="Berlin",
    country="Deutschland"
)

print(address)
# GASAG-Platz 1
# 10963 Berlin
# Deutschland
```

---

## Representative

::: handelsregister.Representative
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Full name |
| `role` | `str \| None` | Role (Geschäftsführer, Vorstand, etc.) |
| `birth_date` | `str \| None` | Date of birth |
| `location` | `str \| None` | Place of residence |

### Example

```python
rep = Representative(
    name="Dr. Gerhard Holtmeier",
    role="Vorstandsvorsitzender",
    birth_date="1960-05-15",
    location="Berlin"
)
```

---

## Owner

::: handelsregister.Owner
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Owner name |
| `owner_type` | `str \| None` | Type (Kommanditist, Komplementär, etc.) |
| `share` | `str \| None` | Share amount |
| `liability` | `str \| None` | Liability amount |

### Example

```python
owner = Owner(
    name="Max Mustermann",
    owner_type="Kommanditist",
    share="100000.00 EUR",
    liability="100000.00 EUR"
)
```

---

## HistoryEntry

::: handelsregister.HistoryEntry
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `date` | `str \| None` | Entry date |
| `entry_type` | `str \| None` | Type of entry |
| `content` | `str` | Entry content |

### Example

```python
entry = HistoryEntry(
    date="2024-01-15",
    entry_type="Neueintragung",
    content="Die Gesellschaft ist eingetragen..."
)
```

---

## SearchOptions

::: handelsregister.SearchOptions
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

### Internal Use

This dataclass is used internally to pass search parameters.

```python
options = SearchOptions(
    keywords="Bank",
    states=["BE", "HH"],
    register_type="HRB",
    only_active=True,
    exact=False
)
```

