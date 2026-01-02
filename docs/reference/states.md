# State Codes

This table shows the ISO 3166-2:DE codes for German federal states used in the `states` parameter.

## State Code Reference

| Code | State (German) | State (English) |
|------|----------------|-----------------|
| `BW` | Baden-Württemberg | Baden-Württemberg |
| `BY` | Bayern | Bavaria |
| `BE` | Berlin | Berlin |
| `BB` | Brandenburg | Brandenburg |
| `HB` | Bremen | Bremen |
| `HH` | Hamburg | Hamburg |
| `HE` | Hessen | Hesse |
| `MV` | Mecklenburg-Vorpommern | Mecklenburg-Western Pomerania |
| `NI` | Niedersachsen | Lower Saxony |
| `NW` | Nordrhein-Westfalen | North Rhine-Westphalia |
| `RP` | Rheinland-Pfalz | Rhineland-Palatinate |
| `SL` | Saarland | Saarland |
| `SN` | Sachsen | Saxony |
| `ST` | Sachsen-Anhalt | Saxony-Anhalt |
| `SH` | Schleswig-Holstein | Schleswig-Holstein |
| `TH` | Thüringen | Thuringia |

---

## Usage Examples

### Python

```python
from handelsregister import search

# Search in Berlin
companies = search("Bank", states=["BE"])

# Search in multiple states
companies = search("Bank", states=["BE", "HH", "BY"])

# All major cities
major_cities = ["BE", "HH", "BY", "NW", "HE"]
companies = search("Bank", states=major_cities)
```

### CLI

```bash
# Single state
handelsregister -s "Bank" --states BE

# Multiple states
handelsregister -s "Bank" --states BE,HH,BY
```

---

## State Groups

### City-States

```python
CITY_STATES = ["BE", "HH", "HB"]
```

### Eastern Germany (former GDR)

```python
EASTERN_STATES = ["BE", "BB", "MV", "SN", "ST", "TH"]
```

### Western Germany

```python
WESTERN_STATES = ["BW", "BY", "HB", "HH", "HE", "NI", "NW", "RP", "SL", "SH"]
```

### Southern Germany

```python
SOUTHERN_STATES = ["BW", "BY"]
```

### Northern Germany

```python
NORTHERN_STATES = ["HB", "HH", "MV", "NI", "SH"]
```

---

## Map

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

## See Also

- [Register Types](registers.md) – HRA, HRB, etc.
- [Legal Forms](legal-forms.md) – GmbH, AG, etc.
- [API Parameters](parameters.md) – All search parameters

