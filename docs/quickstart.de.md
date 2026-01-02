# Schnellstart

Starten Sie mit Handelsregister in nur wenigen Minuten.

## Installation

```bash
git clone https://github.com/bundesAPI/handelsregister.git
cd handelsregister
uv sync
```

---

## Erste Suche

### Mit Python

```python
from handelsregister import search

# Unternehmen suchen
ergebnisse = search("Deutsche Bahn")

# Ergebnisse ausgeben
for firma in ergebnisse:
    print(f"{firma['name']}")
    print(f"  Register: {firma['register_court']} {firma['register_num']}")
    print(f"  Status: {firma['status']}")
    print()
```

**Ausgabe:**

```
Deutsche Bahn Aktiengesellschaft
  Register: Berlin (Charlottenburg) HRB 50000
  Status: aktuell eingetragen

DB Fernverkehr Aktiengesellschaft
  Register: Frankfurt am Main HRB 12345
  Status: aktuell eingetragen
...
```

### Mit CLI

```bash
# Suche nach "Deutsche Bahn"
handelsregister -s "Deutsche Bahn"

# Als JSON-Ausgabe
handelsregister -s "Deutsche Bahn" --json
```

---

## Ergebnisse filtern

### Nach Bundesland

```python
from handelsregister import search

# Nur Berliner Unternehmen
ergebnisse = search("Bank", states=["BE"])
```

```bash
# CLI: Nur Berlin
handelsregister -s "Bank" --states BE
```

### Nach Registerart

```python
# Nur Kapitalgesellschaften (HRB)
ergebnisse = search("GmbH", register_type="HRB")
```

```bash
# CLI
handelsregister -s "GmbH" --register-type HRB
```

### Kombinierte Filter

```python
# Banken in Berlin oder Hamburg, nur HRB
ergebnisse = search(
    keywords="Bank",
    states=["BE", "HH"],
    register_type="HRB",
    only_active=True
)
```

---

## Details abrufen

```python
from handelsregister import search, get_details

# Suchen
firmen = search("GASAG AG", exact=True)

if firmen:
    # Detailinformationen abrufen
    details = get_details(firmen[0])
    
    print(f"Firma: {details.name}")
    print(f"Kapital: {details.capital} {details.currency}")
    print(f"Adresse: {details.address}")
    
    print("Vertreter:")
    for vertreter in details.representatives:
        print(f"  - {vertreter.name} ({vertreter.role})")
```

---

## Caching

Das Package cached Ergebnisse automatisch:

```python
from handelsregister import search

# Erste Suche: Fragt das Registerportal an
ergebnisse1 = search("Deutsche Bank")

# Zweite Suche: Nutzt Cache (schneller)
ergebnisse2 = search("Deutsche Bank")

# Frische Suche erzwingen (Cache umgehen)
ergebnisse3 = search("Deutsche Bank", use_cache=False)
```

Standard Cache-Dauer: **24 Stunden**

---

## Fehlerbehandlung

```python
from handelsregister import search, SearchError, RateLimitError

try:
    ergebnisse = search("Deutsche Bahn")
except RateLimitError:
    print("Zu viele Anfragen! Maximal 60 pro Stunde erlaubt.")
except SearchError as e:
    print(f"Suchfehler: {e}")
```

---

## Nächste Schritte

<div class="grid cards" markdown>

-   :material-book-open-variant:{ .lg .middle } __Benutzerhandbuch__

    ---

    Detaillierte Dokumentation aller Funktionen

    [:octicons-arrow-right-24: Benutzerhandbuch](guide/index.md)

-   :material-api:{ .lg .middle } __API-Referenz__

    ---

    Vollständige technische Referenz

    [:octicons-arrow-right-24: API-Referenz](api/index.md)

-   :material-code-braces:{ .lg .middle } __Beispiele__

    ---

    Praktische Code-Beispiele

    [:octicons-arrow-right-24: Beispiele](examples/simple.md)

</div>

