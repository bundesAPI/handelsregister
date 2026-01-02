# Details abrufen

Lernen Sie, wie Sie erweiterte Unternehmensinformationen über die einfachen Suchergebnisse hinaus abrufen.

## Übersicht

Die einfache Suche liefert begrenzte Informationen. Für vollständige Details verwenden Sie die `get_details()`-Funktion:

| Suchergebnis | Details |
|--------------|---------|
| Firmenname | ✓ Plus historische Namen |
| Registergericht | ✓ |
| Registernummer | ✓ |
| Status | ✓ Plus Eintragungsdaten |
| | **Zusätzlich:** |
| | Kapital (Stammkapital/Grundkapital) |
| | Geschäftsadresse |
| | Vertreter (Geschäftsführer, Vorstand) |
| | Unternehmensgegenstand |
| | Gesellschafter (bei Personengesellschaften) |
| | Vollständige Historie |

---

## Grundlegende Verwendung

```python
from handelsregister import search, get_details

# Zuerst nach dem Unternehmen suchen
firmen = search("GASAG AG", exact=True)

if firmen:
    # Dann Details abrufen
    details = get_details(firmen[0])
    
    print(f"Firma: {details.name}")
    print(f"Kapital: {details.capital} {details.currency}")
```

---

## Das CompanyDetails-Objekt

Die `get_details()`-Funktion gibt eine `CompanyDetails`-Dataclass zurück:

### Grundinformationen

```python
details = get_details(firma)

# Grundinfo
print(details.name)              # "GASAG AG"
print(details.register_court)    # "Berlin (Charlottenburg)"
print(details.register_number)   # "HRB 44343"
print(details.register_type)     # "HRB"
print(details.status)            # "aktuell eingetragen"
```

### Kapital

```python
# Stammkapital/Grundkapital
print(details.capital)     # "306977800.00"
print(details.currency)    # "EUR"

# Formatierte Ausgabe
if details.capital:
    betrag = float(details.capital)
    print(f"Kapital: {betrag:,.2f} {details.currency}")
    # Ausgabe: Kapital: 306,977,800.00 EUR
```

### Adresse

Die Adresse wird als `Address`-Objekt zurückgegeben:

```python
adresse = details.address

print(adresse.street)       # "GASAG-Platz 1"
print(adresse.postal_code)  # "10963"
print(adresse.city)         # "Berlin"
print(adresse.country)      # "Deutschland"

# Vollständige Adresse
print(adresse)
# GASAG-Platz 1
# 10963 Berlin
# Deutschland
```

### Vertreter

Vertreter (Geschäftsführer, Vorstandsmitglieder) werden als Liste zurückgegeben:

```python
for vertreter in details.representatives:
    print(f"Name: {vertreter.name}")
    print(f"Rolle: {vertreter.role}")
    print(f"Geburtsdatum: {vertreter.birth_date}")
    print(f"Ort: {vertreter.location}")
    print("---")
```

**Ausgabe:**

```
Name: Dr. Gerhard Holtmeier
Rolle: Vorstandsvorsitzender
Geburtsdatum: 1960-05-15
Ort: Berlin
---
Name: Stefan Michels
Rolle: Vorstand
Geburtsdatum: 1972-03-22
Ort: Potsdam
---
```

### Gesellschafter (Personengesellschaften)

Für Personengesellschaften (KG, OHG, GbR) sind Gesellschafterinformationen verfügbar:

```python
if details.owners:
    for gesellschafter in details.owners:
        print(f"Name: {gesellschafter.name}")
        print(f"Typ: {gesellschafter.owner_type}")
        print(f"Anteil: {gesellschafter.share}")
        print(f"Haftung: {gesellschafter.liability}")
```

### Unternehmensgegenstand

```python
print("Unternehmensgegenstand:")
print(details.business_purpose)
```

### Historie

Die vollständige Historie der Registereintragungen:

```python
for eintrag in details.history:
    print(f"Datum: {eintrag.date}")
    print(f"Typ: {eintrag.entry_type}")
    print(f"Inhalt: {eintrag.content[:100]}...")
    print("---")
```

---

## Vollständiges Beispiel

```python
from handelsregister import search, get_details

def zeige_firmendetails(name: str):
    """Zeigt vollständige Details für ein Unternehmen an."""
    
    # Suchen
    firmen = search(name, exact=True)
    
    if not firmen:
        print(f"Kein Unternehmen gefunden: {name}")
        return
    
    # Details abrufen
    details = get_details(firmen[0])
    
    # Kopfzeile
    print("=" * 60)
    print(f"  {details.name}")
    print("=" * 60)
    
    # Registrierung
    print(f"\nRegister: {details.register_court}")
    print(f"Nummer:   {details.register_type} {details.register_number}")
    print(f"Status:   {details.status}")
    
    # Kapital
    if details.capital:
        betrag = float(details.capital)
        print(f"\nKapital:  {betrag:,.2f} {details.currency}")
    
    # Adresse
    if details.address:
        print(f"\nAdresse:")
        print(f"  {details.address.street}")
        print(f"  {details.address.postal_code} {details.address.city}")
    
    # Vertreter
    if details.representatives:
        print(f"\nVertreter ({len(details.representatives)}):")
        for v in details.representatives:
            rolle = f" ({v.role})" if v.role else ""
            print(f"  • {v.name}{rolle}")
    
    # Unternehmensgegenstand
    if details.business_purpose:
        print(f"\nUnternehmensgegenstand:")
        # Kürzen wenn zu lang
        zweck = details.business_purpose
        if len(zweck) > 200:
            zweck = zweck[:200] + "..."
        print(f"  {zweck}")

# Verwendung
zeige_firmendetails("GASAG AG")
```

---

## Details-Caching

Details werden separat von Suchergebnissen gecacht:

```python
# Erster Aufruf: Ruft vom Portal ab
details1 = get_details(firma)

# Zweiter Aufruf: Nutzt Cache
details2 = get_details(firma)

# Frischen Abruf erzwingen
details3 = get_details(firma, use_cache=False)
```

---

## Stapelverarbeitung

Für mehrere Unternehmen sequentiell mit Verzögerungen verarbeiten:

```python
import time
from handelsregister import search, get_details

firmen = search("Bank", states=["BE"])

alle_details = []
for i, firma in enumerate(firmen[:10]):  # Limit zur Sicherheit
    print(f"Rufe ab {i+1}/{len(firmen)}: {firma['name']}")
    
    details = get_details(firma)
    alle_details.append(details)
    
    # Rate-Limit beachten: 60/Stunde = 1/Minute
    time.sleep(60)

print(f"\nDetails für {len(alle_details)} Unternehmen abgerufen")
```

---

## Fehlerbehandlung

```python
from handelsregister import get_details, SearchError

try:
    details = get_details(firma)
except SearchError as e:
    print(f"Details konnten nicht abgerufen werden: {e}")
    # Fallback auf Grundinfo aus Suchergebnis
    print(f"Firma: {firma['name']}")
```

---

## Siehe auch

- [API-Referenz: get_details()](../api/functions.md) – Technische Dokumentation
- [Datenmodelle](../api/models.md) – CompanyDetails, Address, Representative
- [Caching](cache.md) – Wie Caching funktioniert

