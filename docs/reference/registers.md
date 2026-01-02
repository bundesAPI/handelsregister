# Register Types

This table shows the different register types available in the German commercial register system.

## Register Type Reference

| Code | German Name | English Name | Typical Legal Forms |
|------|-------------|--------------|---------------------|
| `HRA` | Handelsregister Abteilung A | Commercial Register Section A | Sole proprietors, partnerships (OHG, KG) |
| `HRB` | Handelsregister Abteilung B | Commercial Register Section B | Corporations (GmbH, AG, SE, KGaA) |
| `GnR` | Genossenschaftsregister | Cooperative Register | Cooperatives (eG) |
| `PR` | Partnerschaftsregister | Partnership Register | Professional partnerships (PartG) |
| `VR` | Vereinsregister | Association Register | Registered associations (e.V.) |

---

## Detailed Descriptions

### HRA (Section A)

**Commercial Register Section A** contains:

- **Einzelkaufleute** (Sole proprietors)
- **OHG** (General partnerships)
- **KG** (Limited partnerships)
- **GmbH & Co. KG** (Special limited partnerships)
- **EWIV** (European Economic Interest Groupings)

```python
# Search for partnerships
companies = search("KG", register_type="HRA")
```

### HRB (Section B)

**Commercial Register Section B** contains:

- **GmbH** (Limited liability companies)
- **AG** (Stock corporations)
- **SE** (European companies)
- **KGaA** (Partnerships limited by shares)
- **UG (haftungsbeschränkt)** (Mini-GmbH)

```python
# Search for corporations
companies = search("GmbH", register_type="HRB")
```

### GnR (Cooperative Register)

**Cooperative Register** contains:

- **eG** (Registered cooperatives)
- **SCE** (European cooperatives)

```python
# Search for cooperatives
companies = search("Genossenschaft", register_type="GnR")
```

### PR (Partnership Register)

**Partnership Register** contains:

- **PartG** (Professional partnerships)
- **PartG mbB** (Professional partnerships with limited liability)

Common for lawyers, accountants, doctors, architects.

```python
# Search for professional partnerships
companies = search("Rechtsanwälte", register_type="PR")
```

### VR (Association Register)

**Association Register** contains:

- **e.V.** (Registered associations)

```python
# Search for associations
companies = search("Verein", register_type="VR")
```

---

## Usage Examples

### Python

```python
from handelsregister import search

# Only HRB (corporations)
corporations = search("Bank", register_type="HRB")

# Only HRA (partnerships)
partnerships = search("Consulting", register_type="HRA")

# Search across register types
# (don't specify register_type)
all_types = search("Mustermann")
```

### CLI

```bash
# Only HRB
handelsregister -s "Bank" --register-type HRB

# Only HRA
handelsregister -s "KG" --register-type HRA

# Cooperatives
handelsregister -s "Wohnungsbau" --register-type GnR
```

---

## Statistics

Approximate distribution of entries in Germany:

| Register | Approximate Entries | Percentage |
|----------|---------------------|------------|
| HRB | ~1,500,000 | ~60% |
| HRA | ~700,000 | ~28% |
| GnR | ~20,000 | ~1% |
| PR | ~15,000 | ~1% |
| VR | ~250,000 | ~10% |

---

## See Also

- [State Codes](states.md) – German state codes
- [Legal Forms](legal-forms.md) – GmbH, AG, etc.
- [API Parameters](parameters.md) – All search parameters

