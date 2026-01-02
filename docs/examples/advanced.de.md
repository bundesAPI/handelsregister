# Fortgeschrittene Beispiele

Komplexere Beispiele für fortgeschrittene Anwendungsfälle.

## Stapelverarbeitung

### Mehrere Suchbegriffe verarbeiten

```python
import time
from handelsregister import search

suchbegriffe = ["Bank", "Versicherung", "Immobilien", "Consulting"]

alle_ergebnisse = {}
for suchbegriff in suchbegriffe:
    print(f"Suche: {suchbegriff}")
    ergebnisse = search(suchbegriff, states=["BE"])
    alle_ergebnisse[suchbegriff] = ergebnisse
    
    # Rate-Limit beachten
    time.sleep(60)

# Zusammenfassung
for suchbegriff, ergebnisse in alle_ergebnisse.items():
    print(f"{suchbegriff}: {len(ergebnisse)} Unternehmen")
```

### Alle Bundesländer verarbeiten

```python
import time
from handelsregister import search

BUNDESLAENDER = ["BW", "BY", "BE", "BB", "HB", "HH", "HE", "MV", 
                 "NI", "NW", "RP", "SL", "SN", "ST", "SH", "TH"]

ergebnisse_pro_land = {}
for land in BUNDESLAENDER:
    print(f"Verarbeite {land}...")
    ergebnisse = search("Bank", states=[land], register_type="HRB")
    ergebnisse_pro_land[land] = len(ergebnisse)
    time.sleep(60)

# Nach Anzahl sortieren
sortierte_laender = sorted(ergebnisse_pro_land.items(), key=lambda x: x[1], reverse=True)
for land, anzahl in sortierte_laender:
    print(f"{land}: {anzahl} Banken")
```

---

## Datenanalyse

### Mit pandas

```python
import pandas as pd
from handelsregister import search

# Suchen und in DataFrame konvertieren
firmen = search("Bank", states=["BE", "HH"])
df = pd.DataFrame(firmen)

# Analyse
print("Unternehmen nach Gericht:")
print(df['register_court'].value_counts())

print("\nUnternehmen nach Registerart:")
print(df['register_type'].value_counts())

print("\nUnternehmen nach Status:")
print(df['status'].value_counts())
```

### Export nach CSV

```python
import pandas as pd
from handelsregister import search, get_details

firmen = search("Bank", states=["BE"])

# Details für jedes Unternehmen abrufen
daten = []
for firma in firmen[:10]:  # Limit für Demo
    details = get_details(firma)
    daten.append({
        'name': details.name,
        'gericht': details.register_court,
        'nummer': details.register_number,
        'kapital': details.capital,
        'stadt': details.address.city if details.address else None,
    })

df = pd.DataFrame(daten)
df.to_csv('berliner_banken.csv', index=False)
```

---

## Parallele Verarbeitung

### Mit ThreadPoolExecutor

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
from handelsregister import search
import time

suchbegriffe = ["Bank", "Versicherung", "Immobilien", "IT", "Consulting"]

def suche_suchbegriff(suchbegriff):
    """Suche mit Rate-Limit-Verzögerung."""
    time.sleep(60)  # Rate-Limit
    return suchbegriff, search(suchbegriff, states=["BE"])

# Parallel verarbeiten mit Rate-Limiting
with ThreadPoolExecutor(max_workers=1) as executor:
    futures = {executor.submit(suche_suchbegriff, sb): sb for sb in suchbegriffe}
    
    for future in as_completed(futures):
        suchbegriff, ergebnisse = future.result()
        print(f"{suchbegriff}: {len(ergebnisse)} Unternehmen")
```

---

## Benutzerdefiniertes Caching

### Benutzerdefinierte TTL

```python
from handelsregister import HandelsRegister, SearchCache

# Cache nur für 1 Stunde
cache = SearchCache(ttl_hours=1)
hr = HandelsRegister(cache=cache)

# Benutzerdefinierte Instanz verwenden
firmen = hr.search("Bank")
```

### Benutzerdefiniertes Cache-Verzeichnis

```python
from handelsregister import SearchCache, HandelsRegister

# Benutzerdefiniertes Verzeichnis verwenden
cache = SearchCache(cache_dir="/tmp/hr-cache")
hr = HandelsRegister(cache=cache)

firmen = hr.search("Bank")
```

### Cache-Statistiken

```python
from handelsregister import SearchCache

cache = SearchCache()

# Statistiken abrufen
stats = cache.get_stats()
print(f"Einträge gesamt: {stats['total']}")
print(f"Gültige Einträge: {stats['valid']}")
print(f"Abgelaufene Einträge: {stats['expired']}")
print(f"Cache-Größe: {stats['size_mb']:.2f} MB")

# Abgelaufene Einträge bereinigen
entfernt = cache.cleanup_expired()
print(f"{entfernt} abgelaufene Einträge entfernt")
```

---

## Berichte erstellen

### Unternehmensbericht

```python
from handelsregister import search, get_details

def erstelle_bericht(firmenname: str) -> str:
    """Erstellt einen detaillierten Unternehmensbericht."""
    firmen = search(firmenname, exact=True)
    
    if not firmen:
        return f"Unternehmen nicht gefunden: {firmenname}"
    
    details = get_details(firmen[0])
    
    bericht = []
    bericht.append("=" * 60)
    bericht.append(f"  {details.name}")
    bericht.append("=" * 60)
    bericht.append("")
    
    bericht.append("REGISTRIERUNG")
    bericht.append(f"  Gericht: {details.register_court}")
    bericht.append(f"  Nummer:  {details.register_type} {details.register_number}")
    bericht.append(f"  Status:  {details.status}")
    bericht.append("")
    
    if details.capital:
        bericht.append("KAPITAL")
        bericht.append(f"  {details.capital} {details.currency}")
        bericht.append("")
    
    if details.address:
        bericht.append("ADRESSE")
        bericht.append(f"  {details.address.street}")
        bericht.append(f"  {details.address.postal_code} {details.address.city}")
        bericht.append("")
    
    if details.representatives:
        bericht.append("VERTRETER")
        for v in details.representatives:
            bericht.append(f"  - {v.name}")
            if v.role:
                bericht.append(f"    Rolle: {v.role}")
        bericht.append("")
    
    if details.business_purpose:
        bericht.append("UNTERNEHMENSGEGENSTAND")
        zweck = details.business_purpose
        if len(zweck) > 200:
            zweck = zweck[:200] + "..."
        bericht.append(f"  {zweck}")
    
    return "\n".join(bericht)

# Verwendung
print(erstelle_bericht("GASAG AG"))
```

---

## Rate-Limit-Behandlung

### Automatische Wiederholung

```python
import time
from handelsregister import search, RateLimitError

def suche_mit_wiederholung(keywords, max_versuche=3, **kwargs):
    """Suche mit automatischer Wiederholung bei Rate-Limit."""
    for versuch in range(max_versuche):
        try:
            return search(keywords, **kwargs)
        except RateLimitError:
            if versuch == max_versuche - 1:
                raise
            wartezeit = 60 * (versuch + 1)
            print(f"Rate-limitiert, warte {wartezeit}s...")
            time.sleep(wartezeit)

# Verwendung
firmen = suche_mit_wiederholung("Bank", states=["BE"])
```

### Rate-Limiter-Klasse

```python
import time
from collections import deque
from handelsregister import search

class RateLimiter:
    """Erzwingt Rate-Limiting für API-Aufrufe."""
    
    def __init__(self, max_anfragen: int = 60, fenster_sekunden: int = 3600):
        self.max_anfragen = max_anfragen
        self.fenster_sekunden = fenster_sekunden
        self.anfragen = deque()
    
    def warte_falls_noetig(self):
        """Wartet, wenn Rate-Limit überschritten würde."""
        jetzt = time.time()
        
        # Alte Anfragen entfernen
        while self.anfragen and self.anfragen[0] < jetzt - self.fenster_sekunden:
            self.anfragen.popleft()
        
        if len(self.anfragen) >= self.max_anfragen:
            wartezeit = self.anfragen[0] + self.fenster_sekunden - jetzt
            if wartezeit > 0:
                print(f"Rate-Limit erreicht, warte {wartezeit:.0f}s...")
                time.sleep(wartezeit)
        
        self.anfragen.append(jetzt)
    
    def suche(self, *args, **kwargs):
        """Suche mit Rate-Limiting."""
        self.warte_falls_noetig()
        return search(*args, **kwargs)

# Verwendung
limiter = RateLimiter()

suchbegriffe = ["Bank", "Versicherung", "Consulting"]
for suchbegriff in suchbegriffe:
    ergebnisse = limiter.suche(suchbegriff)
    print(f"{suchbegriff}: {len(ergebnisse)} Ergebnisse")
```

---

## Siehe auch

- [Einfache Beispiele](simple.md) – Grundlegende Beispiele
- [Integrationsbeispiele](integrations.md) – Framework-Integrationen
- [API-Referenz](../api/index.md) – Technische Dokumentation

