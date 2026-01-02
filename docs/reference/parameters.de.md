# API-Parameter

Vollständige Referenz aller Parameter für die `search()`-Funktion.

## Parameterübersicht

| Parameter | Typ | Standard | Beschreibung |
|-----------|-----|----------|--------------|
| `keywords` | `str` | Erforderlich | Suchbegriff für Firmennamen |
| `states` | `List[str]` | `None` | Nach Bundesländern filtern |
| `register_type` | `str` | `None` | Nach Registerart filtern |
| `register_court` | `str` | `None` | Spezifisches Registergericht |
| `register_number` | `str` | `None` | Spezifische Registernummer |
| `only_active` | `bool` | `False` | Nur aktuell eingetragene |
| `exact` | `bool` | `False` | Exakte Namensübereinstimmung |
| `similar_sounding` | `bool` | `False` | Ähnlich klingende Namen einschließen |
| `use_cache` | `bool` | `True` | Gecachte Ergebnisse verwenden |

---

## Parameter im Detail

### keywords (erforderlich)

Der Hauptsuchbegriff. Sucht in Firmennamen.

```python
# Ein Wort
search("Bank")

# Mehrere Wörter
search("Deutsche Bank AG")

# Teilname
search("Deutsche")  # Findet "Deutsche Bahn", "Deutsche Bank", etc.
```

**Tipps:**

- Verwenden Sie markante Wörter für bessere Ergebnisse
- Vermeiden Sie sehr häufige Wörter wie "GmbH" allein
- Fügen Sie die Rechtsform für spezifischere Ergebnisse hinzu: "Mustermann GmbH"

---

### states

Liste von Bundesländer-Codes zum Filtern der Ergebnisse. Siehe [Bundesländer-Codes](states.md).

```python
# Ein Bundesland
search("Bank", states=["BE"])

# Mehrere Bundesländer
search("Bank", states=["BE", "HH", "BY"])

# Alle Bundesländer (Standard - nicht angeben)
search("Bank")
```

**Typ:** `List[str]` oder `None`

**Gültige Werte:** `BW`, `BY`, `BE`, `BB`, `HB`, `HH`, `HE`, `MV`, `NI`, `NW`, `RP`, `SL`, `SN`, `ST`, `SH`, `TH`

---

### register_type

Nach Registerart filtern. Siehe [Registerarten](registers.md).

```python
# Nur Kapitalgesellschaften (GmbH, AG)
search("Bank", register_type="HRB")

# Nur Personengesellschaften (KG, OHG)
search("Consulting", register_type="HRA")

# Genossenschaften
search("Wohnungsbau", register_type="GnR")
```

**Typ:** `str` oder `None`

**Gültige Werte:** `HRA`, `HRB`, `GnR`, `PR`, `VR`

---

### register_court

Nach spezifischem Registergericht filtern.

```python
# Nur Berlin Charlottenburg
search("Bank", register_court="Berlin (Charlottenburg)")

# Nur München
search("Bank", register_court="München")
```

**Typ:** `str` oder `None`

**Hinweis:** Gerichtsnamen müssen exakt übereinstimmen, wie sie im Register erscheinen.

---

### register_number

Nach spezifischer Registernummer suchen.

```python
# Nach Registernummer suchen
search("", register_number="HRB 12345")

# Kombiniert mit Gericht
search("", 
       register_court="Berlin (Charlottenburg)", 
       register_number="HRB 44343")
```

**Typ:** `str` oder `None`

---

### only_active

Nur nach aktuell eingetragenen Unternehmen filtern.

```python
# Nur aktive Unternehmen
search("Bank", only_active=True)

# Gelöschte/fusionierte einschließen (Standard)
search("Bank", only_active=False)
```

**Typ:** `bool`

**Standard:** `False`

---

### exact

Exakte Namensübereinstimmung statt Teilübereinstimmung erfordern.

```python
# Exakte Übereinstimmung - findet nur "GASAG AG"
search("GASAG AG", exact=True)

# Teilübereinstimmung - findet "GASAG AG", "GASAG Beteiligungs GmbH", etc.
search("GASAG", exact=False)
```

**Typ:** `bool`

**Standard:** `False`

---

### similar_sounding

Unternehmen mit ähnlich klingenden Namen einschließen (phonetische Suche).

```python
# Ähnliche Namen einschließen (Meyer, Meier, Mayer, etc.)
search("Müller", similar_sounding=True)
```

**Typ:** `bool`

**Standard:** `False`

**Hinweis:** Dies kann die Anzahl der Ergebnisse erheblich erhöhen.

---

### use_cache

Ob gecachte Ergebnisse verwendet werden sollen.

```python
# Cache verwenden (Standard)
search("Bank", use_cache=True)

# Immer frische Daten abrufen
search("Bank", use_cache=False)
```

**Typ:** `bool`

**Standard:** `True`

---

## Vollständiges Beispiel

```python
from handelsregister import search

# Vollständiges Beispiel mit allen Parametern
firmen = search(
    keywords="Bank",              # Suche nach "Bank"
    states=["BE", "HH"],          # In Berlin und Hamburg
    register_type="HRB",          # Nur Kapitalgesellschaften
    register_court=None,          # Beliebiges Gericht
    register_number=None,         # Beliebige Nummer
    only_active=True,             # Nur aktive Unternehmen
    exact=False,                  # Teilübereinstimmung OK
    similar_sounding=False,       # Keine phonetische Suche
    use_cache=True,               # Cache verwenden
)

print(f"Gefunden: {len(firmen)} Unternehmen")
```

---

## CLI-Entsprechung

| Python-Parameter | CLI-Option |
|------------------|------------|
| `keywords` | `-s, --search` |
| `states` | `--states` |
| `register_type` | `--register-type` |
| `only_active` | `--active-only` |
| `exact` | `--exact` |
| `use_cache=False` | `--no-cache` |

```bash
handelsregister \
    -s "Bank" \
    --states BE,HH \
    --register-type HRB \
    --active-only
```

---

## Siehe auch

- [Bundesländer-Codes](states.md) – Gültige Bundesländer-Codes
- [Registerarten](registers.md) – Gültige Registerarten
- [Als Library verwenden](../guide/library.md) – Weitere Beispiele

