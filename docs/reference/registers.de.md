# Registerarten

Diese Tabelle zeigt die verschiedenen Registerarten im deutschen Handelsregistersystem.

## Registerarten-Referenz

| Code | Name | Typische Rechtsformen |
|------|------|----------------------|
| `HRA` | Handelsregister Abteilung A | Einzelkaufleute, Personengesellschaften (OHG, KG) |
| `HRB` | Handelsregister Abteilung B | Kapitalgesellschaften (GmbH, AG, SE, KGaA) |
| `GnR` | Genossenschaftsregister | Genossenschaften (eG) |
| `PR` | Partnerschaftsregister | Partnerschaftsgesellschaften (PartG) |
| `VR` | Vereinsregister | Eingetragene Vereine (e.V.) |

---

## Detaillierte Beschreibungen

### HRA (Abteilung A)

**Handelsregister Abteilung A** enthält:

- **Einzelkaufleute** (e.K., e.Kfm., e.Kfr.)
- **OHG** (Offene Handelsgesellschaften)
- **KG** (Kommanditgesellschaften)
- **GmbH & Co. KG** (Besondere Kommanditgesellschaften)
- **EWIV** (Europäische wirtschaftliche Interessenvereinigungen)

```python
# Suche nach Personengesellschaften
firmen = search("KG", register_type="HRA")
```

### HRB (Abteilung B)

**Handelsregister Abteilung B** enthält:

- **GmbH** (Gesellschaften mit beschränkter Haftung)
- **AG** (Aktiengesellschaften)
- **SE** (Europäische Gesellschaften)
- **KGaA** (Kommanditgesellschaften auf Aktien)
- **UG (haftungsbeschränkt)** (Unternehmergesellschaften)

```python
# Suche nach Kapitalgesellschaften
firmen = search("GmbH", register_type="HRB")
```

### GnR (Genossenschaftsregister)

**Genossenschaftsregister** enthält:

- **eG** (Eingetragene Genossenschaften)
- **SCE** (Europäische Genossenschaften)

```python
# Suche nach Genossenschaften
firmen = search("Genossenschaft", register_type="GnR")
```

### PR (Partnerschaftsregister)

**Partnerschaftsregister** enthält:

- **PartG** (Partnerschaftsgesellschaften)
- **PartG mbB** (Partnerschaftsgesellschaften mit beschränkter Berufshaftung)

Üblich für Rechtsanwälte, Steuerberater, Ärzte, Architekten.

```python
# Suche nach Partnerschaftsgesellschaften
firmen = search("Rechtsanwälte", register_type="PR")
```

### VR (Vereinsregister)

**Vereinsregister** enthält:

- **e.V.** (Eingetragene Vereine)

```python
# Suche nach Vereinen
firmen = search("Verein", register_type="VR")
```

---

## Verwendungsbeispiele

### Python

```python
from handelsregister import search

# Nur HRB (Kapitalgesellschaften)
kapitalgesellschaften = search("Bank", register_type="HRB")

# Nur HRA (Personengesellschaften)
personengesellschaften = search("Consulting", register_type="HRA")

# Suche über alle Registerarten
# (register_type nicht angeben)
alle_arten = search("Mustermann")
```

### CLI

```bash
# Nur HRB
handelsregister -s "Bank" --register-type HRB

# Nur HRA
handelsregister -s "KG" --register-type HRA

# Genossenschaften
handelsregister -s "Wohnungsbau" --register-type GnR
```

---

## Statistiken

Ungefähre Verteilung der Einträge in Deutschland:

| Register | Ungefähre Anzahl | Anteil |
|----------|------------------|--------|
| HRB | ~1.500.000 | ~60% |
| HRA | ~700.000 | ~28% |
| GnR | ~20.000 | ~1% |
| PR | ~15.000 | ~1% |
| VR | ~250.000 | ~10% |

---

## Siehe auch

- [Bundesländer-Codes](states.md) – Deutsche Bundesländer-Codes
- [Rechtsformen](legal-forms.md) – GmbH, AG, etc.
- [API-Parameter](parameters.md) – Alle Suchparameter

