# Rechtsformen

Diese Tabelle zeigt die gängigen deutschen Rechtsformen und ihre Eigenschaften.

## Rechtsformen-Referenz

### Kapitalgesellschaften (HRB)

| Abkürzung | Name | Mindestkapital |
|-----------|------|----------------|
| GmbH | Gesellschaft mit beschränkter Haftung | 25.000 € |
| UG | Unternehmergesellschaft (haftungsbeschränkt) | 1 € |
| AG | Aktiengesellschaft | 50.000 € |
| SE | Societas Europaea | 120.000 € |
| KGaA | Kommanditgesellschaft auf Aktien | 50.000 € |

### Personengesellschaften (HRA)

| Abkürzung | Name | Haftung |
|-----------|------|---------|
| e.K. | Eingetragener Kaufmann | Persönlich |
| OHG | Offene Handelsgesellschaft | Persönlich |
| KG | Kommanditgesellschaft | Gemischt |
| GmbH & Co. KG | GmbH & Co. Kommanditgesellschaft | Beschränkt |

### Weitere Formen

| Abkürzung | Name | Register |
|-----------|------|----------|
| eG | Eingetragene Genossenschaft | GnR |
| PartG | Partnerschaftsgesellschaft | PR |
| PartG mbB | Partnerschaftsgesellschaft mbB | PR |
| e.V. | Eingetragener Verein | VR |

---

## Detaillierte Beschreibungen

### GmbH (Gesellschaft mit beschränkter Haftung)

Die häufigste Kapitalgesellschaftsform in Deutschland.

- **Mindestkapital:** 25.000 €
- **Haftung:** Auf Gesellschaftsvermögen beschränkt
- **Führung:** Geschäftsführer
- **Anteile:** Geschäftsanteile (nicht börsenhandelbar)

```python
# Suche nach GmbHs
firmen = search("Consulting GmbH", register_type="HRB")
```

### UG (Unternehmergesellschaft)

Eine Sondervariante der GmbH für Gründer mit wenig Kapital.

- **Mindestkapital:** 1 €
- **Thesaurierungspflicht:** 25% des Jahresgewinns bis 25.000 € erreicht
- **Danach:** Umwandlung in reguläre GmbH möglich

```python
firmen = search("UG", register_type="HRB")
```

### AG (Aktiengesellschaft)

Für größere Unternehmen, besonders solche, die Börsenkapital suchen.

- **Mindestkapital:** 50.000 €
- **Führung:** Vorstand + Aufsichtsrat
- **Anteile:** Aktien (können börsengehandelt werden)

```python
firmen = search("AG", register_type="HRB")
```

### KG (Kommanditgesellschaft)

Personengesellschaft mit persönlich haftenden und beschränkt haftenden Gesellschaftern.

- **Komplementär:** Persönlich haftender Gesellschafter
- **Kommanditist:** Beschränkt haftender Gesellschafter

```python
firmen = search("KG", register_type="HRA")
```

### GmbH & Co. KG

Besondere Kommanditgesellschaft, bei der der Komplementär eine GmbH ist.

- Kombiniert beschränkte Haftung mit Personengesellschafts-Besteuerung
- Sehr verbreitet in Deutschland

```python
firmen = search("GmbH & Co. KG", register_type="HRA")
```

---

## Suchmuster

### Nach Rechtsform

```python
from handelsregister import search

# Nur GmbHs
gmbhs = search("Suchbegriff GmbH", register_type="HRB")

# Nur AGs
ags = search("Suchbegriff AG", register_type="HRB")

# Alle Kommanditgesellschaften
kgs = search("KG", register_type="HRA")
```

### Mehrere Formen

```python
# Breit suchen, dann filtern
alle_firmen = search("Mustermann")

# Nach Suffix filtern
gmbhs = [f for f in alle_firmen if "GmbH" in f['name']]
ags = [f for f in alle_firmen if f['name'].endswith(" AG")]
```

---

## Rechtsform-Statistiken

Ungefähre Anzahl aktiver Unternehmen in Deutschland:

| Rechtsform | Anzahl | Anteil |
|------------|--------|--------|
| GmbH | ~1.200.000 | 48% |
| UG | ~150.000 | 6% |
| GmbH & Co. KG | ~200.000 | 8% |
| KG | ~50.000 | 2% |
| AG | ~15.000 | <1% |
| e.K. | ~450.000 | 18% |
| OHG | ~10.000 | <1% |
| eG | ~20.000 | <1% |
| e.V. | ~600.000 | - |

---

## Siehe auch

- [Registerarten](registers.md) – HRA, HRB, etc.
- [Bundesländer-Codes](states.md) – Deutsche Bundesländer-Codes
- [API-Parameter](parameters.md) – Alle Suchparameter

