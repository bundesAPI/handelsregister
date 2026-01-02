# Exceptions

Diese Seite dokumentiert die Exception-Typen für die Fehlerbehandlung.

---

## Exception-Hierarchie

```
Exception
└── HandelsregisterError (Basis-Exception)
    ├── NetworkError
    ├── ParseError
    ├── FormError
    └── CacheError
```

---

## HandelsregisterError

::: handelsregister.HandelsregisterError
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

Basis-Exception für alle Handelsregister-bezogenen Fehler.

### Verwendung

```python
from handelsregister import search, HandelsregisterError

try:
    firmen = search("Bank")
except HandelsregisterError as e:
    print(f"Handelsregister-Fehler: {e}")
```

---

## NetworkError

::: handelsregister.NetworkError
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

Wird ausgelöst, wenn die Verbindung zum Registerportal fehlschlägt.

### Verwendung

```python
from handelsregister import search, NetworkError

try:
    firmen = search("Bank")
except NetworkError as e:
    print(f"Verbindung nicht möglich: {e}")
    # Später erneut versuchen oder Benutzer benachrichtigen
```

---

## ParseError

::: handelsregister.ParseError
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

Wird ausgelöst, wenn die HTML-Antwort nicht geparst werden kann.

Dies deutet normalerweise darauf hin, dass das Registerportal seine HTML-Struktur geändert hat.

### Verwendung

```python
from handelsregister import search, ParseError

try:
    firmen = search("Bank")
except ParseError as e:
    print(f"Antwort konnte nicht geparst werden: {e}")
    print("Das Registerportal hat sich möglicherweise geändert.")
    print("Bitte melden Sie dieses Problem auf GitHub.")
```

---

## FormError

::: handelsregister.FormError
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

Wird ausgelöst, wenn ein Fehler bei der Formularübermittlung auftritt.

### Verwendung

```python
from handelsregister import search, FormError

try:
    firmen = search("Bank")
except FormError as e:
    print(f"Formular-Fehler: {e}")
```

---

## CacheError

::: handelsregister.CacheError
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

Wird ausgelöst, wenn ein Fehler mit dem Caching-System auftritt.

### Verwendung

```python
from handelsregister import search, CacheError

try:
    firmen = search("Bank")
except CacheError as e:
    print(f"Cache-Fehler: {e}")
    # Ohne Cache versuchen
    firmen = search("Bank", use_cache=False)
```

---

## Vollständige Fehlerbehandlung

```python
from handelsregister import (
    search,
    get_details,
    HandelsregisterError,
    NetworkError,
    ParseError,
    FormError,
    CacheError,
)
import logging

logger = logging.getLogger(__name__)

def robuste_suche(keywords, **kwargs):
    """Suche mit umfassender Fehlerbehandlung."""
    try:
        return search(keywords, **kwargs)
    
    except NetworkError as e:
        logger.error(f"Verbindung fehlgeschlagen: {e}")
        raise
    
    except ParseError as e:
        logger.error(f"Parse-Fehler: {e}")
        raise
    
    except FormError as e:
        logger.error(f"Formular-Fehler: {e}")
        raise
    
    except CacheError as e:
        logger.warning(f"Cache-Fehler: {e}, wiederhole ohne Cache")
        return search(keywords, use_cache=False, **kwargs)
    
    except HandelsregisterError as e:
        logger.error(f"Allgemeiner Fehler: {e}")
        raise

def robuste_details(firma):
    """Details mit Fehlerbehandlung abrufen."""
    try:
        return get_details(firma)
    
    except HandelsregisterError as e:
        logger.error(f"Details für {firma['name']} nicht abrufbar: {e}")
        return None
```

---

## Rate-Limiting

!!! warning "Rate-Limit"
    Das Registerportal erlaubt maximal **60 Anfragen pro Stunde**. Es gibt zwar keinen dedizierten `RateLimitError`, aber das Überschreiten dieses Limits kann zu `NetworkError` oder Verbindungsproblemen führen.

### Rate-Limiting implementieren

```python
import time
from handelsregister import search

def suche_mit_verzoegerung(suchbegriffe_liste):
    """Suche mit Rate-Limiting."""
    ergebnisse = {}
    for keywords in suchbegriffe_liste:
        ergebnisse[keywords] = search(keywords)
        time.sleep(60)  # 1 Minute zwischen Anfragen
    return ergebnisse
```

---

## Siehe auch

- [Als Library verwenden](../guide/library.md) – Beispiele zur Fehlerbehandlung
- [Best Practices](../guide/library.md#best-practices) – Retry-Muster
