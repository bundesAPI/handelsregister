# Bundesländer-Codes

Diese Tabelle zeigt die ISO 3166-2:DE Codes für deutsche Bundesländer, die im `states`-Parameter verwendet werden.

## Bundesländer-Referenz

| Code | Bundesland | Hauptstadt |
|------|------------|------------|
| `BW` | Baden-Württemberg | Stuttgart |
| `BY` | Bayern | München |
| `BE` | Berlin | Berlin |
| `BB` | Brandenburg | Potsdam |
| `HB` | Bremen | Bremen |
| `HH` | Hamburg | Hamburg |
| `HE` | Hessen | Wiesbaden |
| `MV` | Mecklenburg-Vorpommern | Schwerin |
| `NI` | Niedersachsen | Hannover |
| `NW` | Nordrhein-Westfalen | Düsseldorf |
| `RP` | Rheinland-Pfalz | Mainz |
| `SL` | Saarland | Saarbrücken |
| `SN` | Sachsen | Dresden |
| `ST` | Sachsen-Anhalt | Magdeburg |
| `SH` | Schleswig-Holstein | Kiel |
| `TH` | Thüringen | Erfurt |

---

## Verwendungsbeispiele

### Python

```python
from handelsregister import search

# Suche in Berlin
firmen = search("Bank", states=["BE"])

# Suche in mehreren Bundesländern
firmen = search("Bank", states=["BE", "HH", "BY"])

# Alle Großstädte
grossstaedte = ["BE", "HH", "BY", "NW", "HE"]
firmen = search("Bank", states=grossstaedte)
```

### CLI

```bash
# Ein Bundesland
handelsregister -s "Bank" --states BE

# Mehrere Bundesländer
handelsregister -s "Bank" --states BE,HH,BY
```

---

## Bundesland-Gruppen

### Stadtstaaten

```python
STADTSTAATEN = ["BE", "HH", "HB"]
```

### Ostdeutschland (ehemalige DDR)

```python
OSTDEUTSCHE_LAENDER = ["BE", "BB", "MV", "SN", "ST", "TH"]
```

### Westdeutschland

```python
WESTDEUTSCHE_LAENDER = ["BW", "BY", "HB", "HH", "HE", "NI", "NW", "RP", "SL", "SH"]
```

### Süddeutschland

```python
SUEDDEUTSCHE_LAENDER = ["BW", "BY"]
```

### Norddeutschland

```python
NORDDEUTSCHE_LAENDER = ["HB", "HH", "MV", "NI", "SH"]
```

---

## Karte

```
     SH
   HH
HB     MV
   NI    BB   BE
      ST
   NW         SN
         TH
     HE
   RP    BY
SL    BW
```

---

## Siehe auch

- [Registerarten](registers.md) – HRA, HRB, etc.
- [Rechtsformen](legal-forms.md) – GmbH, AG, etc.
- [API-Parameter](parameters.md) – Alle Suchparameter

