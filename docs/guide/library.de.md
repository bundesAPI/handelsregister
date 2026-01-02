# Als Library verwenden

Dieses Kapitel erklärt, wie Sie Handelsregister als Python-Library in Ihren Anwendungen verwenden.

## Grundlegende Verwendung

### Die `search()`-Funktion

Die `search()`-Funktion ist der Haupteinstiegspunkt für Unternehmenssuchen:

```python
from handelsregister import search

# Einfache Suche
firmen = search("Deutsche Bahn")

# Ergebnisse verarbeiten
for firma in firmen:
    print(f"Name: {firma['name']}")
    print(f"Gericht: {firma['register_court']}")
    print(f"Nummer: {firma['register_num']}")
    print(f"Status: {firma['status']}")
    print("---")
```

### Rückgabewert

Die Funktion gibt eine Liste von Dictionaries mit folgenden Schlüsseln zurück:

| Schlüssel | Typ | Beschreibung |
|-----------|-----|--------------|
| `name` | `str` | Firmenname |
| `register_court` | `str` | Registergericht |
| `register_num` | `str` | Registernummer (z.B. "HRB 12345") |
| `status` | `str` | Registrierungsstatus |
| `state` | `str` | Bundesland-Code (z.B. "BE") |
| `history` | `list` | Liste historischer Einträge |

---

## Suchparameter

### Alle Parameter

```python
firmen = search(
    keywords="Bank",              # Suchbegriff (erforderlich)
    states=["BE", "HH"],          # Nach Bundesländern filtern
    register_type="HRB",          # Nach Registerart filtern
    register_court="Berlin",      # Spezifisches Registergericht
    register_number="12345",      # Spezifische Registernummer
    only_active=True,             # Nur aktuell eingetragene
    exact=False,                  # Exakte Namensübereinstimmung
    use_cache=True,               # Caching verwenden
    similar_sounding=False,       # Ähnlich klingende Namen einschließen
)
```

### Parameter im Detail

#### `keywords` (erforderlich)
Der Suchbegriff für Firmennamen:

```python
# Teilübereinstimmung
search("Deutsche")  # Findet "Deutsche Bahn", "Deutsche Bank", etc.

# Mehrere Wörter
search("Deutsche Bank AG")
```

#### `states`
Nach deutschen Bundesländern filtern mit ISO-Codes:

```python
# Ein Bundesland
search("Bank", states=["BE"])

# Mehrere Bundesländer
search("Bank", states=["BE", "HH", "BY"])
```

Siehe [Bundesländer-Codes](../reference/states.md) für alle Codes.

#### `register_type`
Nach Registerart filtern:

```python
# Nur HRB (Kapitalgesellschaften)
search("GmbH", register_type="HRB")

# Nur HRA (Einzelunternehmen, Personengesellschaften)
search("KG", register_type="HRA")
```

Siehe [Registerarten](../reference/registers.md) für alle Arten.

#### `only_active`
Nach aktuell eingetragenen Unternehmen filtern:

```python
# Nur aktive Unternehmen
search("Bank", only_active=True)

# Gelöschte/fusionierte einschließen
search("Bank", only_active=False)
```

#### `exact`
Exakte Namensübereinstimmung erfordern:

```python
# Nur exakte Übereinstimmung
search("GASAG AG", exact=True)

# Teilübereinstimmungen erlaubt (Standard)
search("GASAG", exact=False)
```

---

## Mit Ergebnissen arbeiten

### Ergebnisse durchlaufen

```python
firmen = search("Deutsche Bahn")

# Als Liste
for firma in firmen:
    verarbeite(firma)

# Mit Index
for i, firma in enumerate(firmen):
    print(f"{i+1}. {firma['name']}")

# In Python filtern
berliner_firmen = [
    f for f in firmen 
    if f['state'] == 'BE'
]
```

### Auf Ergebnisse prüfen

```python
firmen = search("xyz123nichtvorhanden")

if not firmen:
    print("Keine Unternehmen gefunden")
else:
    print(f"{len(firmen)} Unternehmen gefunden")
```

### In DataFrame konvertieren

```python
import pandas as pd
from handelsregister import search

firmen = search("Bank", states=["BE"])

# In DataFrame konvertieren
df = pd.DataFrame(firmen)

# Analysieren
print(df.groupby('register_court').size())
```

---

## Fortgeschrittene Verwendung

### Die HandelsRegister-Klasse verwenden

Für mehr Kontrolle verwenden Sie die `HandelsRegister`-Klasse direkt:

```python
from handelsregister import HandelsRegister

# Instanz erstellen
hr = HandelsRegister()

# Suche mit voller Kontrolle
ergebnisse = hr.search(
    keywords="Bank",
    register_type="HRB",
    states=["BE"]
)

# Details abrufen
if ergebnisse:
    details = hr.get_details(ergebnisse[0])
```

### Benutzerdefinierte Cache-Konfiguration

```python
from handelsregister import HandelsRegister, SearchCache

# Benutzerdefinierter Cache mit 1-Stunden-TTL
cache = SearchCache(ttl_hours=1)

hr = HandelsRegister(cache=cache)
ergebnisse = hr.search("Bank")
```

### Ohne Caching

```python
# Cache für diese Suche deaktivieren
firmen = search("Bank", use_cache=False)

# Oder global
hr = HandelsRegister(cache=None)
```

---

## Fehlerbehandlung

```python
from handelsregister import (
    search,
    SearchError,
    RateLimitError,
    ConnectionError,
    ParseError
)

try:
    firmen = search("Bank")
except RateLimitError:
    print("Rate-Limit überschritten (max 60/Stunde)")
    # Warten und erneut versuchen
except ConnectionError:
    print("Verbindung zum Registerportal nicht möglich")
except ParseError:
    print("Fehler beim Parsen der Antwort")
except SearchError as e:
    print(f"Allgemeiner Suchfehler: {e}")
```

### Wiederholungslogik

```python
import time
from handelsregister import search, RateLimitError

def suche_mit_wiederholung(keywords, max_versuche=3):
    for versuch in range(max_versuche):
        try:
            return search(keywords)
        except RateLimitError:
            if versuch < max_versuche - 1:
                wartezeit = (versuch + 1) * 60  # 1, 2, 3 Minuten
                print(f"Rate-limitiert, warte {wartezeit}s...")
                time.sleep(wartezeit)
            else:
                raise
```

---

## Best Practices

### 1. Rate-Limits respektieren

```python
import time

suchbegriffe = ["Bank", "Versicherung", "AG", ...]

for keywords in suchbegriffe:
    ergebnisse = search(keywords)
    verarbeite(ergebnisse)
    time.sleep(60)  # 1 Minute zwischen Suchen warten
```

### 2. Caching nutzen

```python
# Cache ist standardmäßig aktiviert
# Ergebnisse werden 24 Stunden wiederverwendet

firmen = search("Bank")  # Erster Aufruf: Portal-Anfrage
firmen = search("Bank")  # Zweiter Aufruf: aus Cache
```

### 3. Server-seitig filtern

```python
# Gut: Auf dem Server filtern
firmen = search("Bank", states=["BE"], register_type="HRB")

# Weniger effizient: Client-seitig filtern
firmen = search("Bank")
berlin_hrb = [f for f in firmen if f['state'] == 'BE']
```

### 4. Leere Ergebnisse behandeln

```python
firmen = search(keywords)

if not firmen:
    logger.info(f"Keine Ergebnisse für '{keywords}'")
    return []

# Verarbeitung fortsetzen
```

---

## Siehe auch

- [API-Referenz: search()](../api/functions.md) – Technische Details
- [Details abrufen](details.md) – Erweiterte Informationen abrufen
- [Beispiele](../examples/simple.md) – Code-Beispiele

