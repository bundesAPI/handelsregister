# Handelsregister

Python-Package für das gemeinsame Registerportal der deutschen Bundesländer.

Nutzbar als **Kommandozeilen-Tool** oder als **Library** in eigenen Anwendungen.

## Rechtliche Hinweise

Das Handelsregister stellt ein öffentliches Verzeichnis dar, das im Rahmen des Registerrechts Eintragungen über die angemeldeten Kaufleute in einem bestimmten geografischen Raum führt. Eintragungspflichtig sind die im HGB, AktG und GmbHG abschließend aufgezählten Tatsachen oder Rechtsverhältnisse.

Die Einsichtnahme in das Handelsregister sowie in die dort eingereichten Dokumente ist gemäß **§ 9 Abs. 1 HGB** jeder Person zu Informationszwecken gestattet. Die Recherche nach einzelnen Firmen, die Einsicht in die Unternehmensträgerdaten und die Nutzung der Handelsregisterbekanntmachungen ist kostenfrei möglich.

> **⚠️ Achtung:** Es ist unzulässig, mehr als **60 Abrufe pro Stunde** zu tätigen (vgl. [Nutzungsordnung](https://www.handelsregister.de/rp_web/information.xhtml)). Das Registerportal ist regelmäßig das Ziel automatisierter Massenabfragen. Den [FAQs](https://www.handelsregister.de/rp_web/information.xhtml) zufolge erreiche die Frequenz dieser Abfragen sehr häufig eine Höhe, bei der die Straftatbestände der Rechtsnormen **§§ 303a, b StGB** vorliegen.

## Installation

Installation mit [uv](https://docs.astral.sh/uv/) (empfohlen):

```bash
git clone https://github.com/bundesAPI/handelsregister.git
cd handelsregister
uv sync
```

Alternativ mit pip:

```bash
pip install git+https://github.com/bundesAPI/handelsregister.git
```

## Verwendung als Library

### Einfache API

```python
from handelsregister import search, State, RegisterType

# Einfache Suche
unternehmen = search("Deutsche Bahn")

# Mit Optionen (empfohlen: Enums für Autovervollständigung)
banken = search(
    keywords="Bank",
    states=[State.BE, State.HH],    # Nur Berlin und Hamburg
    register_type=RegisterType.HRB, # Nur HRB-Einträge
    include_deleted=False,          # Keine gelöschten
)

# String-basierte API funktioniert weiterhin
banken = search(
    keywords="Bank",
    states=["BE", "HH"],
    register_type="HRB",
    include_deleted=False,
)

# Ergebnisse verarbeiten
for firma in banken:
    print(f"{firma['name']} - {firma['register_num']}")
    print(f"  Gericht: {firma['court']}")
    print(f"  Status: {firma['status']}")
```

### Erweiterte API

Für mehr Kontrolle kann die `HandelsRegister`-Klasse direkt verwendet werden:

```python
from handelsregister import (
    HandelsRegister, SearchOptions, SearchCache,
    State, KeywordMatch, RegisterType
)

# Mit SearchOptions (empfohlen: Enums)
options = SearchOptions(
    keywords="Energie",
    keyword_option=KeywordMatch.ALL,
    states=[State.BY, State.BW],
    register_type=RegisterType.HRB,
    similar_sounding=True,      # Phonetische Suche
    results_per_page=100,
)

# String-basierte API funktioniert weiterhin
options = SearchOptions(
    keywords="Energie",
    keyword_option="all",
    states=["BY", "BW"],
    register_type="HRB",
    similar_sounding=True,
    results_per_page=100,
)

hr = HandelsRegister(debug=False)
hr.open_startpage()
ergebnisse = hr.search_with_options(options)

# Mit eigenem Cache
cache = SearchCache(ttl_seconds=7200)  # 2 Stunden TTL
hr = HandelsRegister(cache=cache)
```

### Detailabruf

Zu Suchergebnissen können erweiterte Unternehmensinformationen abgerufen werden:

```python
from handelsregister import search, get_details, KeywordMatch

# Erst suchen (empfohlen: Enum)
unternehmen = search("GASAG AG", keyword_option=KeywordMatch.EXACT)

# String-basierte API funktioniert weiterhin
unternehmen = search("GASAG AG", keyword_option="exact")

# Dann Details abrufen
if unternehmen:
    details = get_details(unternehmen[0], detail_type="SI")
    
    print(f"Firma: {details.name}")
    print(f"Rechtsform: {details.legal_form}")
    print(f"Kapital: {details.capital} {details.currency}")
    print(f"Adresse: {details.address}")
    
    for gf in details.representatives:
        print(f"  {gf.role}: {gf.name}")
```

**Verfügbare Detail-Typen:**

| Typ | Beschreibung |
|-----|--------------|
| `SI` | Strukturierter Registerinhalt (empfohlen, maschinenlesbar) |
| `AD` | Aktueller Abdruck (formatierter Text) |
| `UT` | Unternehmensträger (Gesellschafter/Inhaber) |

### Rückgabeformat

**Suchergebnisse** werden als Dictionary zurückgegeben:

```python
{
    'name': 'GASAG AG',
    'court': 'Berlin District court Berlin (Charlottenburg) HRB 44343',
    'register_num': 'HRB 44343 B',
    'state': 'Berlin',
    'status': 'currently registered',
    'statusCurrent': 'CURRENTLY_REGISTERED',
    'documents': 'ADCDHDDKUTVÖSI',
    'history': [('Alter Firmenname', 'Berlin')]
}
```

**CompanyDetails** enthält erweiterte Informationen:

```python
{
    'name': 'GASAG AG',
    'register_num': 'HRB 44343 B',
    'court': 'Amtsgericht Berlin (Charlottenburg)',
    'state': 'Berlin',
    'status': 'aktuell',
    'legal_form': 'Aktiengesellschaft',
    'capital': '307.200.000',
    'currency': 'EUR',
    'address': {
        'street': 'GASAG-Platz 1',
        'postal_code': '10965',
        'city': 'Berlin',
        'country': 'Deutschland'
    },
    'purpose': 'Versorgung mit Energie...',
    'representatives': [
        {'name': 'Dr. Max Mustermann', 'role': 'Vorstand', 'location': 'Berlin'}
    ],
    'owners': [],
    'registration_date': '01.01.1990',
    'last_update': None,
    'deletion_date': None
}
```

## Verwendung als CLI

Die CLI kann über `handelsregister` oder die kürzere Variante `hrg` aufgerufen werden.

### Kommandozeilen-Schnittstelle

```
handelsregister.py [-h] [-d] [-f] [-j] -s SCHLAGWÖRTER [-so OPTION]
                   [--states CODES] [--register-type TYP]
                   [--register-number NUMMER] [--include-deleted]
                   [--similar-sounding] [--results-per-page N]
                   [--details] [--detail-type TYP]

Optionen:
  -h, --help            Hilfe anzeigen
  -d, --debug           Debug-Modus aktivieren
  -f, --force           Cache ignorieren und neue Daten abrufen
  -j, --json            Ausgabe als JSON

Suchparameter:
  -s, --schlagwoerter   Suchbegriffe (erforderlich)
  -so, --schlagwortOptionen
                        Suchmodus: all=alle Begriffe; min=mindestens einer; exact=exakter Name
  --states CODES        Kommagetrennte Bundesland-Codes (z.B. BE,BY,HH)
  --register-type TYP   Registerart filtern (HRA, HRB, GnR, PR, VR)
  --register-number     Nach bestimmter Registernummer suchen
  --include-deleted     Auch gelöschte Einträge anzeigen
  --similar-sounding    Phonetische Suche (Kölner Phonetik)
  --results-per-page N  Ergebnisse pro Seite (10, 25, 50, 100)

Detailoptionen:
  --details             Erweiterte Unternehmensinfos abrufen
  --detail-type TYP     Art der Details: SI=strukturiert, AD=Abdruck, UT=Inhaber
```

### Bundesland-Codes

| Code | Bundesland |
|------|------------|
| BW | Baden-Württemberg |
| BY | Bayern |
| BE | Berlin |
| BR | Brandenburg |
| HB | Bremen |
| HH | Hamburg |
| HE | Hessen |
| MV | Mecklenburg-Vorpommern |
| NI | Niedersachsen |
| NW | Nordrhein-Westfalen |
| RP | Rheinland-Pfalz |
| SL | Saarland |
| SN | Sachsen |
| ST | Sachsen-Anhalt |
| SH | Schleswig-Holstein |
| TH | Thüringen |

### Beispiele

```bash
# Einfache Suche
uv run handelsregister -s "Deutsche Bahn" -so all
# Oder kürzer:
uv run hrg -s "Deutsche Bahn" -so all

# Suche mit JSON-Ausgabe
uv run handelsregister -s "GASAG AG" -so exact --json
# Oder:
uv run hrg -s "GASAG AG" -so exact --json

# Nach Bundesland und Registerart filtern
uv run handelsregister -s "Bank" --states BE,HH --register-type HRB
# Oder:
uv run hrg -s "Bank" --states BE,HH --register-type HRB

# Gelöschte Einträge mit phonetischer Suche
uv run handelsregister -s "Mueller" --include-deleted --similar-sounding

# Cache ignorieren (neue Daten abrufen)
uv run handelsregister -s "Volkswagen" -f --debug

# Mit Detailabruf (Geschäftsführer, Kapital, Adresse)
uv run handelsregister -s "GASAG AG" --details

# Details als JSON (für Weiterverarbeitung)
uv run handelsregister -s "GASAG AG" --details --json

# Spezifischer Detail-Typ (Unternehmensträger)
uv run handelsregister -s "Test GmbH" --details --detail-type UT
```

## Tests

```bash
# Unit-Tests ausführen (schnell, ohne Netzwerkzugriff)
uv run pytest

# Alle Tests inkl. Integrationstests (greift auf Live-API zu)
uv run pytest -m integration

# Mit ausführlicher Ausgabe
uv run pytest -v
```

## API-Parameter

***URL:*** https://www.handelsregister.de/rp_web/erweitertesuche.xhtml

Das gemeinsame Registerportal der Länder ermöglicht die Recherche nach einzelnen Firmen zu Informationszwecken. Einträge lassen sich über verschiedene Parameter filtern:

### Suchparameter

| Parameter | Werte | Beschreibung |
|-----------|-------|--------------|
| `schlagwoerter` | Text | Suchbegriffe. Platzhalter: `*` (beliebig viele Zeichen), `?` (genau ein Zeichen) |
| `schlagwortOptionen` | 1, 2, 3 | 1=alle enthalten; 2=mindestens einer; 3=exakter Firmenname |
| `suchOptionenAehnlich` | true | Phonetische Suche (Kölner Phonetik) |
| `suchOptionenGeloescht` | true | Auch gelöschte Firmen finden |
| `ergebnisseProSeite` | 10, 25, 50, 100 | Anzahl Ergebnisse pro Seite |

### Filterparameter

| Parameter | Werte | Beschreibung |
|-----------|-------|--------------|
| `registerArt` | alle, HRA, HRB, GnR, PR, VR | Registerart |
| `registerNummer` | Text | Registernummer |
| `registerGericht` | Code | Registergericht (z.B. D3201 für Ansbach) |
| `niederlassung` | Text | Niederlassung / Sitz |
| `postleitzahl` | Text | Postleitzahl |
| `ort` | Text | Ort |
| `strasse` | Text | Straße |

### Bundesland-Filter

| Parameter | Bundesland |
|-----------|------------|
| `bundeslandBW` | Baden-Württemberg |
| `bundeslandBY` | Bayern |
| `bundeslandBE` | Berlin |
| `bundeslandBR` | Brandenburg |
| `bundeslandHB` | Bremen |
| `bundeslandHH` | Hamburg |
| `bundeslandHE` | Hessen |
| `bundeslandMV` | Mecklenburg-Vorpommern |
| `bundeslandNI` | Niedersachsen |
| `bundeslandNW` | Nordrhein-Westfalen |
| `bundeslandRP` | Rheinland-Pfalz |
| `bundeslandSL` | Saarland |
| `bundeslandSN` | Sachsen |
| `bundeslandST` | Sachsen-Anhalt |
| `bundeslandSH` | Schleswig-Holstein |
| `bundeslandTH` | Thüringen |

### Rechtsformen

| Code | Rechtsform |
|------|------------|
| 1 | Aktiengesellschaft |
| 2 | Eingetragene Genossenschaft |
| 3 | Eingetragener Verein |
| 4 | Einzelkauffrau |
| 5 | Einzelkaufmann |
| 6 | Europäische Aktiengesellschaft (SE) |
| 7 | Europäische wirtschaftliche Interessenvereinigung |
| 8 | Gesellschaft mit beschränkter Haftung |
| 9 | HRA Juristische Person |
| 10 | Kommanditgesellschaft |
| 12 | Offene Handelsgesellschaft |
| 13 | Partnerschaft |
| 18 | Seerechtliche Gesellschaft |
| 19 | Versicherungsverein auf Gegenseitigkeit |
| 40 | Anstalt öffentlichen Rechts |
| 46 | Bergrechtliche Gesellschaft |
| 48 | Körperschaft öffentlichen Rechts |
| 49 | Europäische Genossenschaft (SCE) |
| 51 | Stiftung privaten Rechts |
| 52 | Stiftung öffentlichen Rechts |

## Lizenz

Dieses Projekt ist Teil der [bundesAPI](https://github.com/bundesAPI) Initiative.
