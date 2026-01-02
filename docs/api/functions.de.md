# Öffentliche Funktionen

Diese Seite dokumentiert die öffentlichen Funktionen des Handelsregister-Packages.

---

## search

::: handelsregister.search
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

### Verwendungsbeispiele

```python
from handelsregister import search

# Einfache Suche
firmen = search("Deutsche Bahn")

# Mit Filtern
firmen = search(
    keywords="Bank",
    register_art="HRB",
    register_gericht="Berlin"
)

# Suche nach Registernummer
firmen = search(
    schlagwoerter="",
    register_nummer="12345",
    register_gericht="Berlin (Charlottenburg)"
)
```

### Rückgabewert

Gibt eine Liste von Dictionaries mit Unternehmensinformationen zurück:

```python
[
    {
        "name": "Deutsche Bank AG",
        "register_court": "Frankfurt am Main",
        "register_num": "HRB 12345",
        "register_type": "HRB",
        "status": "aktuell eingetragen",
        "state": "HE",
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

### Verwendungsbeispiele

```python
from handelsregister import search, get_details

# Zuerst suchen
firmen = search("GASAG AG")

# Dann Details abrufen
if firmen:
    details = get_details(firmen[0])
    
    print(details.name)
    print(details.capital)
    print(details.address)
    print(details.representatives)
```

### Rückgabewert

Gibt ein `CompanyDetails`-Objekt mit vollständigen Unternehmensinformationen zurück.

Siehe [Datenmodelle: CompanyDetails](models.md#handelsregister.CompanyDetails) für Details.

---

## main

::: handelsregister.main
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

Der CLI-Einstiegspunkt. Diese Funktion wird aufgerufen, wenn `handelsregister` über die Kommandozeile ausgeführt wird.

### Verwendung

```bash
# Über Kommandozeile ausführen
handelsregister -s "Deutsche Bahn"

# Oder über Python
python -m handelsregister -s "Deutsche Bahn"
```
