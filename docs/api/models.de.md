# Datenmodelle

Diese Seite dokumentiert die Dataclasses für die strukturierte Datendarstellung.

---

## Company

::: handelsregister.Company
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

### Felder

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `name` | `str` | Firmenname |
| `register_court` | `str` | Registergericht |
| `register_num` | `str` | Registernummer (z.B. "HRB 12345") |
| `register_type` | `str` | Registerart (HRA, HRB, etc.) |
| `status` | `str` | Registrierungsstatus |
| `state` | `str` | Bundesland-Code (z.B. "BE") |
| `history` | `List[HistoryEntry]` | Historische Einträge |

### Beispiel

```python
firma = Company(
    name="Deutsche Bank AG",
    register_court="Frankfurt am Main",
    register_num="HRB 12345",
    register_type="HRB",
    status="aktuell eingetragen",
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

### Felder

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `name` | `str` | Firmenname |
| `register_court` | `str` | Registergericht |
| `register_number` | `str` | Registernummer |
| `register_type` | `str` | Registerart |
| `status` | `str` | Registrierungsstatus |
| `capital` | `str \| None` | Stammkapital/Grundkapital |
| `currency` | `str \| None` | Währung (EUR) |
| `address` | `Address \| None` | Geschäftsadresse |
| `representatives` | `List[Representative]` | Geschäftsführer, Vorstandsmitglieder |
| `owners` | `List[Owner]` | Gesellschafter (Personengesellschaften) |
| `business_purpose` | `str \| None` | Unternehmensgegenstand |
| `history` | `List[HistoryEntry]` | Vollständige Historie |

### Beispiel

```python
details = CompanyDetails(
    name="GASAG AG",
    register_court="Berlin (Charlottenburg)",
    register_number="44343",
    register_type="HRB",
    status="aktuell eingetragen",
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

### Felder

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `street` | `str \| None` | Straße und Hausnummer |
| `postal_code` | `str \| None` | Postleitzahl |
| `city` | `str \| None` | Stadt |
| `country` | `str \| None` | Land |

### Beispiel

```python
adresse = Address(
    street="GASAG-Platz 1",
    postal_code="10963",
    city="Berlin",
    country="Deutschland"
)

print(adresse)
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

### Felder

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `name` | `str` | Vollständiger Name |
| `role` | `str \| None` | Rolle (Geschäftsführer, Vorstand, etc.) |
| `birth_date` | `str \| None` | Geburtsdatum |
| `location` | `str \| None` | Wohnort |

### Beispiel

```python
vertreter = Representative(
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

### Felder

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `name` | `str` | Gesellschaftername |
| `owner_type` | `str \| None` | Typ (Kommanditist, Komplementär, etc.) |
| `share` | `str \| None` | Einlagebetrag |
| `liability` | `str \| None` | Haftungsbetrag |

### Beispiel

```python
gesellschafter = Owner(
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

### Felder

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `date` | `str \| None` | Eintragungsdatum |
| `entry_type` | `str \| None` | Art des Eintrags |
| `content` | `str` | Eintragsinhalt |

### Beispiel

```python
eintrag = HistoryEntry(
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

### Interne Verwendung

Diese Dataclass wird intern verwendet, um Suchparameter zu übergeben.

```python
optionen = SearchOptions(
    keywords="Bank",
    states=["BE", "HH"],
    register_type="HRB",
    only_active=True,
    exact=False
)
```

