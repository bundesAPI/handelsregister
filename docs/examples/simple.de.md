# Einfache Beispiele

Grundlegende Beispiele zum Einstieg mit dem Handelsregister-Package.

## Suchbeispiele

### Einfache Suche

```python
from handelsregister import search

# Suche nach Unternehmen mit "Deutsche Bahn"
firmen = search("Deutsche Bahn")

print(f"{len(firmen)} Unternehmen gefunden")
for firma in firmen:
    print(f"  - {firma['name']}")
```

### Suche mit Bundesland-Filter

```python
from handelsregister import search

# Suche nach Banken in Berlin
banken = search("Bank", states=["BE"])

print(f"Banken in Berlin: {len(banken)}")
```

### Suche mit mehreren Filtern

```python
from handelsregister import search

# Aktive GmbHs in Hamburg
firmen = search(
    keywords="Consulting",
    states=["HH"],
    register_type="HRB",
    only_active=True
)
```

### Exakte Namenssuche

```python
from handelsregister import search

# Exakten Firmennamen suchen
firmen = search("GASAG AG", exact=True)

if firmen:
    print(f"Gefunden: {firmen[0]['name']}")
else:
    print("Unternehmen nicht gefunden")
```

---

## Mit Ergebnissen arbeiten

### Auf Unternehmensdaten zugreifen

```python
from handelsregister import search

firmen = search("Siemens AG", exact=True)

if firmen:
    firma = firmen[0]
    
    print(f"Name: {firma['name']}")
    print(f"Gericht: {firma['register_court']}")
    print(f"Nummer: {firma['register_num']}")
    print(f"Status: {firma['status']}")
    print(f"Bundesland: {firma['state']}")
```

### In Liste von Namen konvertieren

```python
from handelsregister import search

firmen = search("Bank", states=["BE"])

# Nur die Namen extrahieren
namen = [f['name'] for f in firmen]
print(namen)
```

### Ergebnisse in Python filtern

```python
from handelsregister import search

firmen = search("Bank")

# Nach bestimmten Kriterien filtern
grosse_banken = [
    f for f in firmen
    if "AG" in f['name'] and f['status'] == 'aktuell eingetragen'
]
```

---

## Details abrufen

### Grundlegende Details

```python
from handelsregister import search, get_details

# Nach Unternehmen suchen
firmen = search("GASAG AG", exact=True)

if firmen:
    # Vollständige Details abrufen
    details = get_details(firmen[0])
    
    print(f"Name: {details.name}")
    print(f"Kapital: {details.capital} {details.currency}")
```

### Auf Adresse zugreifen

```python
from handelsregister import search, get_details

firmen = search("GASAG AG", exact=True)
details = get_details(firmen[0])

if details.address:
    print(f"Straße: {details.address.street}")
    print(f"Ort: {details.address.postal_code} {details.address.city}")
```

### Vertreter auflisten

```python
from handelsregister import search, get_details

firmen = search("Deutsche Bahn AG", exact=True)
details = get_details(firmen[0])

print("Geschäftsführung:")
for vertreter in details.representatives:
    print(f"  - {vertreter.name}: {vertreter.role}")
```

---

## CLI-Beispiele

### Einfache CLI-Suche

```bash
# Einfache Suche
handelsregister -s "Deutsche Bahn"

# Suche in bestimmtem Bundesland
handelsregister -s "Bank" --states BE

# Mehrere Bundesländer
handelsregister -s "Bank" --states BE,HH,BY
```

### Ausgabeformate

```bash
# Standardausgabe
handelsregister -s "GASAG"

# JSON-Ausgabe
handelsregister -s "GASAG" --json

# Kompakte Ausgabe
handelsregister -s "GASAG" --compact
```

### Mit Details

```bash
# Unternehmensdetails abrufen
handelsregister -s "GASAG AG" --exact --details
```

### In Datei speichern

```bash
# JSON in Datei speichern
handelsregister -s "Bank" --states BE --json > berliner_banken.json

# Ergebnisse zählen
handelsregister -s "Bank" --json | jq 'length'
```

---

## Fehlerbehandlung

### Einfache Fehlerbehandlung

```python
from handelsregister import search, SearchError

try:
    firmen = search("Bank")
    print(f"{len(firmen)} Unternehmen gefunden")
except SearchError as e:
    print(f"Suche fehlgeschlagen: {e}")
```

### Auf leere Ergebnisse prüfen

```python
from handelsregister import search

firmen = search("xyz123nichtvorhanden")

if not firmen:
    print("Keine Unternehmen gefunden")
else:
    print(f"{len(firmen)} Unternehmen gefunden")
```

---

## Nächste Schritte

- [Fortgeschrittene Beispiele](advanced.md) – Komplexere Anwendungsfälle
- [Integrationsbeispiele](integrations.md) – Verwendung mit anderen Tools
- [API-Referenz](../api/index.md) – Vollständige Dokumentation

