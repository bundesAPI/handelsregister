# Kommandozeile (CLI)

Das Handelsregister-Package enthält eine leistungsfähige Kommandozeilen-Schnittstelle für schnelle Abfragen.

## Grundlegende Verwendung

```bash
# Einfache Suche
handelsregister -s "Deutsche Bahn"
# Oder die kürzere Variante verwenden:
hrg -s "Deutsche Bahn"

# Mit uv
uv run handelsregister -s "Deutsche Bahn"
# Oder:
uv run hrg -s "Deutsche Bahn"
```

---

## Suchoptionen

### `-s, --search`
Der Suchbegriff (erforderlich):

```bash
handelsregister -s "Bank"
handelsregister -s "Deutsche Bahn AG"
```

### `--states`
Nach Bundesländern filtern (kommagetrennt):

```bash
# Ein Bundesland
handelsregister -s "Bank" --states BE

# Mehrere Bundesländer
handelsregister -s "Bank" --states BE,HH,BY
```

### `--register-type`
Nach Registerart filtern:

```bash
# Nur HRB (Kapitalgesellschaften)
handelsregister -s "GmbH" --register-type HRB

# Nur HRA (Personengesellschaften)
handelsregister -s "KG" --register-type HRA
```

### `--exact`
Exakte Namensübereinstimmung erfordern:

```bash
handelsregister -s "GASAG AG" --exact
```

### `--active-only`
Nur aktuell eingetragene Unternehmen anzeigen:

```bash
handelsregister -s "Bank" --active-only
```

---

## Ausgabeformate

### Standardausgabe

```bash
handelsregister -s "GASAG"
```

```
3 Unternehmen gefunden:

1. GASAG AG
   Gericht: Berlin (Charlottenburg)
   Nummer: HRB 44343
   Status: aktuell eingetragen

2. GASAG Beteiligungs GmbH
   Gericht: Berlin (Charlottenburg)
   Nummer: HRB 87654
   Status: aktuell eingetragen
...
```

### JSON-Ausgabe

```bash
handelsregister -s "GASAG" --json
```

```json
[
  {
    "name": "GASAG AG",
    "court": "Berlin (Charlottenburg)",
    "register_num": "HRB 44343",
    "status": "aktuell eingetragen",
    "state": "BE"
  },
  ...
]
```

### Kompakte Ausgabe

```bash
handelsregister -s "GASAG" --compact
```

```
GASAG AG | Berlin (Charlottenburg) | HRB 44343
GASAG Beteiligungs GmbH | Berlin (Charlottenburg) | HRB 87654
```

---

## Details abrufen

### `--details`
Erweiterte Informationen abrufen:

```bash
handelsregister -s "GASAG AG" --exact --details
```

```
GASAG AG
=========
Gericht: Berlin (Charlottenburg)
Nummer: HRB 44343
Status: aktuell eingetragen

Kapital: 306.977.800,00 EUR

Adresse:
  GASAG-Platz 1
  10963 Berlin

Vertreter:
  - Dr. Gerhard Holtmeier (Vorstandsvorsitzender)
  - Stefan Michels (Vorstand)
  - Jörg Simon (Vorstand)

Unternehmensgegenstand:
  Gegenstand des Unternehmens ist die Versorgung mit Energie...
```

### `--details --json`
Details im JSON-Format:

```bash
handelsregister -s "GASAG AG" --exact --details --json
```

---

## Caching-Optionen

### `--no-cache`
Cache überspringen, immer frische Daten abrufen:

```bash
handelsregister -s "Bank" --no-cache
```

### `--clear-cache`
Den gesamten Cache löschen:

```bash
handelsregister --clear-cache
```

---

## Weitere Optionen

### `--help`
Hilfe anzeigen:

```bash
handelsregister --help
```

```
usage: handelsregister [-h] [-s SEARCH] [--states STATES]
                       [--register-type TYPE] [--exact]
                       [--active-only] [--details] [--json]
                       [--compact] [--no-cache] [--clear-cache]

Abfrage des deutschen Handelsregisters

options:
  -h, --help            Hilfe anzeigen
  -s, --search SEARCH   Suchbegriff
  --states STATES       Nach Bundesländern filtern (kommagetrennt)
  --register-type TYPE  Nach Registerart filtern
  --exact               Exakte Namensübereinstimmung
  --active-only         Nur aktuell eingetragene
  --details             Unternehmensdetails abrufen
  --json                JSON-Ausgabe
  --compact             Kompakte Ausgabe
  --no-cache            Cache überspringen
  --clear-cache         Cache löschen
```

### `--version`
Version anzeigen:

```bash
handelsregister --version
```

---

## Beispiele

### Banken in Berlin suchen

```bash
handelsregister -s "Bank" --states BE --register-type HRB
```

### In JSON-Datei exportieren

```bash
handelsregister -s "Versicherung" --states BY --json > versicherungen_by.json
```

### Mit jq verarbeiten

```bash
handelsregister -s "Bank" --json | jq '.[].name'
```

### Durch Bundesländer iterieren

```bash
for bundesland in BE HH BY; do
    echo "=== $bundesland ==="
    handelsregister -s "Bank" --states $bundesland --compact
    sleep 60  # Rate-Limit beachten
done
```

### Details für bestimmtes Unternehmen abrufen

```bash
handelsregister -s "Deutsche Bahn AG" --exact --details
```

---

## Exit-Codes

| Code | Bedeutung |
|------|-----------|
| 0 | Erfolg |
| 1 | Keine Ergebnisse gefunden |
| 2 | Verbindungsfehler |
| 3 | Rate-Limit überschritten |
| 4 | Ungültige Argumente |

### Exit-Codes in Skripten verwenden

```bash
handelsregister -s "Bank" --states BE

if [ $? -eq 0 ]; then
    echo "Suche erfolgreich"
elif [ $? -eq 1 ]; then
    echo "Keine Ergebnisse gefunden"
elif [ $? -eq 3 ]; then
    echo "Rate-Limit - später erneut versuchen"
fi
```

---

## Umgebungsvariablen

| Variable | Beschreibung | Standard |
|----------|--------------|----------|
| `HANDELSREGISTER_CACHE_DIR` | Cache-Verzeichnis | `~/.cache/handelsregister` |
| `HANDELSREGISTER_CACHE_TTL` | Cache-TTL in Stunden | `24` |
| `HANDELSREGISTER_DEBUG` | Debug-Ausgabe aktivieren | `0` |

```bash
# Beispiel: Eigenes Cache-Verzeichnis
export HANDELSREGISTER_CACHE_DIR=/tmp/hr-cache
handelsregister -s "Bank"

# Beispiel: Cache deaktivieren
export HANDELSREGISTER_CACHE_TTL=0
handelsregister -s "Bank"
```

---

## Siehe auch

- [Als Library verwenden](library.md) – Python-Integration
- [Referenztabellen](../reference/states.md) – Bundesländer-Codes, Registerarten
- [Beispiele](../examples/simple.md) – Weitere Beispiele

