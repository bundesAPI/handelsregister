# API-Referenz

Vollständige technische Dokumentation für das Handelsregister-Package.

## Übersicht

Das Package stellt folgende Hauptkomponenten bereit:

| Komponente | Typ | Beschreibung |
|------------|-----|--------------|
| [`search()`](functions.md#handelsregister.search) | Funktion | Unternehmen suchen |
| [`get_details()`](functions.md#handelsregister.get_details) | Funktion | Detaillierte Unternehmensinformationen abrufen |
| [`HandelsRegister`](classes.md#handelsregister.HandelsRegister) | Klasse | Hauptklasse für Registerzugriff |
| [`SearchCache`](classes.md#handelsregister.SearchCache) | Klasse | Caching-Mechanismus |
| [`Company`](models.md#handelsregister.Company) | Dataclass | Unternehmen aus Suchergebnissen |
| [`CompanyDetails`](models.md#handelsregister.CompanyDetails) | Dataclass | Detaillierte Unternehmensinformationen |

---

## Schnelllinks

<div class="grid cards" markdown>

-   :material-function:{ .lg .middle } __Funktionen__

    ---

    Öffentliche Funktionen für Suche und Datenabruf.

    [:octicons-arrow-right-24: Funktionen](functions.md)

-   :material-class:{ .lg .middle } __Klassen__

    ---

    Kernklassen für Registerzugriff und Caching.

    [:octicons-arrow-right-24: Klassen](classes.md)

-   :material-database:{ .lg .middle } __Datenmodelle__

    ---

    Dataclasses für strukturierte Datendarstellung.

    [:octicons-arrow-right-24: Datenmodelle](models.md)

-   :material-alert-circle:{ .lg .middle } __Exceptions__

    ---

    Exception-Typen für Fehlerbehandlung.

    [:octicons-arrow-right-24: Exceptions](exceptions.md)

</div>

---

## Modulstruktur

```
handelsregister
├── search()              # Hauptsuchfunktion
├── get_details()         # Unternehmensdetails abrufen
├── clear_cache()         # Cache löschen
│
├── HandelsRegister       # Hauptklasse
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
├── Datenmodelle
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

## Verwendungsmuster

```python
from handelsregister import (
    # Funktionen
    search,
    get_details,
    clear_cache,
    
    # Klassen
    HandelsRegister,
    SearchCache,
    
    # Datenmodelle
    Company,
    CompanyDetails,
    Address,
    Representative,
    
    # Exceptions
    SearchError,
    RateLimitError,
)

# Grundlegende Verwendung
firmen = search("Deutsche Bahn")

# Mit Fehlerbehandlung
try:
    firmen = search("Bank", states=["BE"])
    for firma in firmen:
        details = get_details(firma)
        verarbeite(details)
except RateLimitError:
    print("Rate-Limit überschritten")
except SearchError as e:
    print(f"Fehler: {e}")
```

---

## Type Hints

Das Package ist vollständig typisiert. Sie können Type Hints in Ihrem Code verwenden:

```python
from handelsregister import search, get_details
from handelsregister import Company, CompanyDetails
from typing import List

def finde_banken(bundesland: str) -> List[Company]:
    """Findet alle Banken in einem Bundesland."""
    return search("Bank", states=[bundesland], register_type="HRB")

def hole_kapital(firma: Company) -> str | None:
    """Gibt das Kapital eines Unternehmens zurück."""
    details: CompanyDetails = get_details(firma)
    return details.capital
```

