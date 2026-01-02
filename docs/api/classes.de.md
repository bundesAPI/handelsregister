# Klassen

Diese Seite dokumentiert die Hauptklassen des Handelsregister-Packages.

---

## HandelsRegister

::: handelsregister.HandelsRegister
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3
      members:
        - __init__
        - search
        - get_details

### Verwendungsbeispiele

```python
from handelsregister import HandelsRegister

# Instanz erstellen
hr = HandelsRegister()

# Suchen
firmen = hr.search("Deutsche Bahn")

# Details abrufen
if firmen:
    details = hr.get_details(firmen[0])
```

### Mit benutzerdefiniertem Cache

```python
from handelsregister import HandelsRegister, SearchCache

# Benutzerdefinierter Cache mit 1-Stunden-TTL
cache = SearchCache(ttl_hours=1)
hr = HandelsRegister(cache=cache)

# Ohne Cache
hr = HandelsRegister(cache=None)
```

---

## SearchCache

::: handelsregister.SearchCache
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3
      members:
        - __init__
        - get
        - set
        - clear
        - cleanup_expired
        - get_stats

### Verwendungsbeispiele

```python
from handelsregister import SearchCache

# Standard-Cache
cache = SearchCache()

# Benutzerdefinierte TTL
cache = SearchCache(ttl_hours=1)

# Benutzerdefiniertes Verzeichnis
cache = SearchCache(cache_dir="/tmp/hr-cache")

# Statistiken abrufen
stats = cache.get_stats()
print(f"Einträge: {stats['total']}")
print(f"Größe: {stats['size_mb']:.2f} MB")

# Bereinigen
cache.cleanup_expired()

# Alles löschen
cache.clear()
```

---

## ResultParser

::: handelsregister.ResultParser
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

### Interne Verwendung

Diese Klasse ist hauptsächlich für die interne Verwendung. Sie parst HTML-Suchergebnisse vom Registerportal.

```python
from handelsregister import ResultParser

parser = ResultParser()
firmen = parser.parse(html_inhalt)
```

---

## DetailsParser

::: handelsregister.DetailsParser
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

### Interne Verwendung

Diese Klasse ist hauptsächlich für die interne Verwendung. Sie parst HTML-Detailseiten vom Registerportal.

```python
from handelsregister import DetailsParser

parser = DetailsParser()
details = parser.parse(html_inhalt)
```

