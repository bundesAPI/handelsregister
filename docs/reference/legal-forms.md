# Legal Forms

This table shows the common German legal forms (Rechtsformen) and their characteristics.

## Legal Form Reference

### Corporations (HRB)

| Abbreviation | German Name | English Name | Min. Capital |
|--------------|-------------|--------------|--------------|
| GmbH | Gesellschaft mit beschränkter Haftung | Limited liability company | €25,000 |
| UG | Unternehmergesellschaft (haftungsbeschränkt) | Mini-GmbH | €1 |
| AG | Aktiengesellschaft | Stock corporation | €50,000 |
| SE | Societas Europaea | European company | €120,000 |
| KGaA | Kommanditgesellschaft auf Aktien | Partnership limited by shares | €50,000 |

### Partnerships (HRA)

| Abbreviation | German Name | English Name | Liability |
|--------------|-------------|--------------|-----------|
| e.K. | Eingetragener Kaufmann | Sole proprietor | Personal |
| OHG | Offene Handelsgesellschaft | General partnership | Personal |
| KG | Kommanditgesellschaft | Limited partnership | Mixed |
| GmbH & Co. KG | GmbH & Co. Kommanditgesellschaft | Special limited partnership | Limited |

### Other Forms

| Abbreviation | German Name | English Name | Register |
|--------------|-------------|--------------|----------|
| eG | Eingetragene Genossenschaft | Cooperative | GnR |
| PartG | Partnerschaftsgesellschaft | Professional partnership | PR |
| PartG mbB | Partnerschaftsgesellschaft mbB | Professional partnership (limited) | PR |
| e.V. | Eingetragener Verein | Registered association | VR |

---

## Detailed Descriptions

### GmbH (Limited Liability Company)

The most common corporate form in Germany.

- **Minimum capital:** €25,000
- **Liability:** Limited to company assets
- **Governance:** Geschäftsführer (managing directors)
- **Shares:** Anteile (not publicly tradable)

```python
# Search for GmbHs
companies = search("Consulting GmbH", register_type="HRB")
```

### UG (Mini-GmbH)

A special variant of the GmbH for founders with little capital.

- **Minimum capital:** €1
- **Must retain:** 25% of annual profit until €25,000 reached
- **Then:** Can convert to regular GmbH

```python
companies = search("UG", register_type="HRB")
```

### AG (Stock Corporation)

Used for larger companies, especially those seeking public capital.

- **Minimum capital:** €50,000
- **Governance:** Vorstand (board) + Aufsichtsrat (supervisory board)
- **Shares:** Aktien (can be publicly traded)

```python
companies = search("AG", register_type="HRB")
```

### KG (Limited Partnership)

Partnership with general and limited partners.

- **Komplementär:** General partner (unlimited liability)
- **Kommanditist:** Limited partner (liability limited to contribution)

```python
companies = search("KG", register_type="HRA")
```

### GmbH & Co. KG

Special limited partnership where the general partner is a GmbH.

- Combines limited liability with partnership taxation
- Very common in Germany

```python
companies = search("GmbH & Co. KG", register_type="HRA")
```

---

## Search Patterns

### By Legal Form

```python
from handelsregister import search

# GmbHs only
gmbhs = search("keyword GmbH", register_type="HRB")

# AGs only
ags = search("keyword AG", register_type="HRB")

# All limited partnerships
kgs = search("KG", register_type="HRA")
```

### Multiple Forms

```python
# Search broadly, then filter
all_companies = search("Mustermann")

# Filter by suffix
gmbhs = [c for c in all_companies if "GmbH" in c['name']]
ags = [c for c in all_companies if c['name'].endswith(" AG")]
```

---

## Legal Form Statistics

Approximate number of active companies in Germany:

| Legal Form | Count | Percentage |
|------------|-------|------------|
| GmbH | ~1,200,000 | 48% |
| UG | ~150,000 | 6% |
| GmbH & Co. KG | ~200,000 | 8% |
| KG | ~50,000 | 2% |
| AG | ~15,000 | <1% |
| e.K. | ~450,000 | 18% |
| OHG | ~10,000 | <1% |
| eG | ~20,000 | <1% |
| e.V. | ~600,000 | - |

---

## See Also

- [Register Types](registers.md) – HRA, HRB, etc.
- [State Codes](states.md) – German state codes
- [API Parameters](parameters.md) – All search parameters

