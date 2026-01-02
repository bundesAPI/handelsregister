# Rechtliche Hinweise

Diese Seite enthält wichtige rechtliche Informationen zur Nutzung des Handelsregister-Packages.

## Nutzungsbeschränkungen

!!! danger "Wichtig: Rate-Limits"

    Es ist **unzulässig**, mehr als **60 Abrufe pro Stunde** beim Handelsregisterportal zu tätigen.
    
    Das Registerportal ist das Ziel automatisierter Massenabfragen, deren Frequenz häufig die Straftatbestände der **§§ 303a, b StGB** (Computersabotage) erfüllt.

## Rechtsgrundlage

### Einsichtnahme (§ 9 Abs. 1 HGB)

Gemäß **§ 9 Abs. 1 HGB** (Handelsgesetzbuch) ist die Einsichtnahme in das Handelsregister jeder Person zu Informationszwecken gestattet.

> "Die Einsichtnahme in das Handelsregister sowie in die zum Handelsregister eingereichten Dokumente ist jedem zu Informationszwecken gestattet."

### Datenschutz (DSGVO)

Die aus dem Handelsregister erhaltenen Daten können personenbezogene Daten enthalten. Bei der Verwendung dieser Daten müssen Sie die **Datenschutz-Grundverordnung (DSGVO)** und das **Bundesdatenschutzgesetz (BDSG)** einhalten.

Insbesondere:

- Personenbezogene Daten dürfen nur für legitime Zwecke verarbeitet werden
- Grundsätze der Datenminimierung gelten
- Betroffene haben Rechte bezüglich ihrer Daten

---

## Nutzungsbedingungen von handelsregister.de

Das Handelsregisterportal (handelsregister.de) hat eigene Nutzungsbedingungen, die zu beachten sind:

1. **Keine Massenabfragen** - Automatisierter Abruf großer Datenmengen ist untersagt
2. **Kein kommerzieller Weiterverkauf** - Daten dürfen nicht ohne Genehmigung kommerziell weiterverkauft oder verbreitet werden
3. **Persönliche Haftung** - Nutzer haften persönlich für ihre Nutzung des Portals

---

## Haftungsausschluss

### Keine Garantie

Dieses Package wird "wie besehen" ohne jegliche Garantie bereitgestellt. Die Autoren und Mitwirkenden:

- Garantieren nicht die Richtigkeit, Vollständigkeit oder Aktualität der Daten
- Haften nicht für Schäden, die aus der Nutzung dieses Packages entstehen
- Garantieren nicht die Verfügbarkeit oder Funktionsfähigkeit des Packages

### Nutzerverantwortung

Nutzer dieses Packages sind verantwortlich für:

- Einhaltung der Rate-Limits
- Beachtung geltender Gesetze und Vorschriften
- Ordnungsgemäßen Umgang mit personenbezogenen Daten
- Alle Konsequenzen ihrer Nutzung

---

## Verbotene Nutzungen

Dieses Package darf **nicht** verwendet werden für:

1. **Massenhafte Datensammlung** - Systematische Erfassung aller oder großer Teile der Registerdaten
2. **Denial of Service** - Aktionen, die die Verfügbarkeit des Portals beeinträchtigen könnten
3. **Kommerzieller Datenweiterverkauf** - Verkauf von Registerdaten ohne Genehmigung
4. **Stalking oder Belästigung** - Nutzung von Unternehmens- oder Personendaten für schädliche Zwecke
5. **Betrug** - Jegliche betrügerische oder täuschende Zwecke

---

## Best Practices

Für eine verantwortungsvolle Nutzung dieses Packages:

### Rate-Limits respektieren

```python
import time

# Zwischen Anfragen warten
for suchbegriff in suchbegriffe:
    ergebnisse = search(suchbegriff)
    time.sleep(60)  # Max 60 Anfragen pro Stunde
```

### Caching nutzen

```python
# Caching ist standardmäßig aktiviert
ergebnisse = search("Bank")  # Einmal abgerufen, 24h gecacht
```

### Anfragen minimieren

```python
# Gut: Server-seitig filtern
firmen = search("Bank", states=["BE"], register_type="HRB")

# Schlecht: Alles abrufen, lokal filtern
alle_firmen = search("Bank")  # Viel größere Antwort
gefiltert = [f for f in alle_firmen if f['state'] == 'BE']
```

---

## Probleme melden

Wenn Sie Probleme mit diesem Package entdecken, die zu Missbrauch führen könnten, melden Sie diese bitte verantwortungsvoll:

1. Öffnen Sie ein GitHub-Issue (für nicht-sicherheitsrelevante Probleme)
2. Kontaktieren Sie die Maintainer direkt (für Sicherheitsprobleme)

---

## Lizenz

Dieses Package ist unter der **MIT-Lizenz** lizenziert.

```
MIT License

Copyright (c) 2024 BundesAPI

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## Kontakt

Für Fragen zu rechtlichen Angelegenheiten:

- **GitHub Issues**: [github.com/bundesAPI/handelsregister/issues](https://github.com/bundesAPI/handelsregister/issues)
- **BundesAPI**: [github.com/bundesAPI](https://github.com/bundesAPI)

