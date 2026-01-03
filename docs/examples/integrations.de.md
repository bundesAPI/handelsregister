# Integrationsbeispiele

Beispiele für die Integration von Handelsregister mit beliebten Frameworks und Tools.

## FastAPI

### Einfacher API-Endpunkt

```python
from fastapi import FastAPI, HTTPException
from handelsregister import search, get_details, SearchError

app = FastAPI(title="Unternehmenssuche API")

@app.get("/search")
async def suche_unternehmen(
    q: str,
    bundesland: str = None,
    limit: int = 10
):
    """Sucht nach Unternehmen."""
    try:
        states = [bundesland] if bundesland else None
        firmen = search(q, states=states)
        return {
            "abfrage": q,
            "anzahl": len(firmen),
            "ergebnisse": firmen[:limit]
        }
    except SearchError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/unternehmen/{gericht}/{nummer}")
async def hole_unternehmen(gericht: str, nummer: str):
    """Ruft Unternehmensdetails nach Register ab."""
    try:
        firmen = search(
            "",
            court=gericht,
            register_number=nummer
        )
        if not firmen:
            raise HTTPException(status_code=404, detail="Unternehmen nicht gefunden")
        
        details = get_details(firmen[0])
        return {
            "name": details.name,
            "kapital": details.capital,
            "adresse": {
                "strasse": details.address.street if details.address else None,
                "stadt": details.address.city if details.address else None,
            },
            "vertreter": [
                {"name": v.name, "rolle": v.role}
                for v in details.representatives
            ]
        }
    except SearchError as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Flask

### Einfache Flask-App

```python
from flask import Flask, request, jsonify
from handelsregister import search, get_details, SearchError

app = Flask(__name__)

@app.route('/suche')
def suche_unternehmen():
    """Such-Endpunkt."""
    abfrage = request.args.get('q', '')
    bundesland = request.args.get('bundesland')
    
    if not abfrage:
        return jsonify({"fehler": "Abfrage erforderlich"}), 400
    
    try:
        states = [bundesland] if bundesland else None
        firmen = search(abfrage, states=states)
        return jsonify({
            "anzahl": len(firmen),
            "ergebnisse": firmen
        })
    except SearchError as e:
        return jsonify({"fehler": str(e)}), 500

@app.route('/unternehmen/<name>')
def unternehmens_details(name):
    """Unternehmensdetails abrufen."""
    try:
        firmen = search(name, keyword_option="exact")
        if not firmen:
            return jsonify({"fehler": "Nicht gefunden"}), 404
        
        details = get_details(firmen[0])
        return jsonify({
            "name": details.name,
            "kapital": details.capital,
            "waehrung": details.currency
        })
    except SearchError as e:
        return jsonify({"fehler": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
```

---

## Django

### Django Management Command

```python
# myapp/management/commands/suche_unternehmen.py
from django.core.management.base import BaseCommand
from handelsregister import search

class Command(BaseCommand):
    help = 'Sucht nach Unternehmen im Handelsregister'

    def add_arguments(self, parser):
        parser.add_argument('abfrage', type=str)
        parser.add_argument('--bundesland', type=str, default=None)
        parser.add_argument('--limit', type=int, default=10)

    def handle(self, *args, **options):
        abfrage = options['abfrage']
        states = [options['bundesland']] if options['bundesland'] else None
        limit = options['limit']
        
        firmen = search(abfrage, states=states)
        
        self.stdout.write(f"{len(firmen)} Unternehmen gefunden\n")
        for firma in firmen[:limit]:
            self.stdout.write(f"  - {firma.name}")
```

### Django Model Integration

```python
# models.py
from django.db import models
from handelsregister import search, get_details

class Unternehmen(models.Model):
    name = models.CharField(max_length=255)
    registergericht = models.CharField(max_length=100)
    registernummer = models.CharField(max_length=50)
    kapital = models.DecimalField(max_digits=15, decimal_places=2, null=True)
    aktualisiert = models.DateTimeField(auto_now=True)
    
    @classmethod
    def erstelle_aus_register(cls, firmenname):
        """Erstellt Unternehmen aus Registerdaten."""
        firmen = search(firmenname, keyword_option="exact")
        if not firmen:
            raise ValueError(f"Unternehmen nicht gefunden: {firmenname}")
        
        details = get_details(firmen[0])
        
        return cls.objects.create(
            name=details.name,
            registergericht=details.court,
            registernummer=details.register_number,
            kapital=float(details.capital) if details.capital else None
        )
    
    def aktualisiere_aus_register(self):
        """Aktualisiert Unternehmensdaten aus Register."""
        firmen = search(self.name, keyword_option="exact")
        if firmen:
            details = get_details(firmen[0])
            self.kapital = float(details.capital) if details.capital else None
            self.save()
```

---

## Celery

### Hintergrund-Tasks

```python
# tasks.py
from celery import Celery
from handelsregister import search, get_details
import time

app = Celery('tasks', broker='redis://localhost:6379/0')

@app.task(bind=True, max_retries=3)
def suche_unternehmen_task(self, abfrage, states=None):
    """Sucht Unternehmen im Hintergrund."""
    try:
        return search(abfrage, states=states)
    except Exception as e:
        self.retry(countdown=60)

@app.task
def stapel_suche_task(suchbegriffe):
    """Sucht mehrere Suchbegriffe mit Rate-Limiting."""
    ergebnisse = {}
    for suchbegriff in suchbegriffe:
        ergebnisse[suchbegriff] = search(suchbegriff)
        time.sleep(60)  # Rate-Limit
    return ergebnisse

# Verwendung
result = suche_unternehmen_task.delay("Bank", states=["BE"])
firmen = result.get(timeout=30)
```

---

## SQLAlchemy

### Ergebnisse in Datenbank speichern

```python
from sqlalchemy import create_engine, Column, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from handelsregister import search, get_details

Base = declarative_base()
engine = create_engine('sqlite:///unternehmen.db')
Session = sessionmaker(bind=engine)

class Unternehmen(Base):
    __tablename__ = 'unternehmen'
    
    id = Column(String, primary_key=True)
    name = Column(String)
    registergericht = Column(String)
    registernummer = Column(String)
    kapital = Column(Float)
    aktualisiert = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(engine)

def speichere_unternehmen(firmenname):
    """Sucht und speichert Unternehmen in Datenbank."""
    session = Session()
    
    firmen = search(firmenname, keyword_option="exact")
    if not firmen:
        return None
    
    details = get_details(firmen[0])
    
    unternehmen = Unternehmen(
        id=f"{details.court}_{details.register_number}",
        name=details.name,
        registergericht=details.court,
        registernummer=details.register_number,
        kapital=float(details.capital) if details.capital else None
    )
    
    session.merge(unternehmen)
    session.commit()
    
    return unternehmen
```

---

## Jupyter Notebook

### Interaktive Analyse

```python
# Zelle 1: Setup
from handelsregister import search, get_details
import pandas as pd
import matplotlib.pyplot as plt

# Zelle 2: Suchen und erkunden
firmen = search("Bank", states=["BE", "HH", "BY"])
# Company-Objekte in Dicts für pandas konvertieren
df = pd.DataFrame([f.to_dict() for f in firmen])
df.head()

# Zelle 3: Nach Bundesland visualisieren
df['state'].value_counts().plot(kind='bar')
plt.title('Banken nach Bundesland')
plt.xlabel('Bundesland')
plt.ylabel('Anzahl')
plt.show()

# Zelle 4: Details für Top-Unternehmen abrufen
# Company-Objekte direkt verwenden (nicht DataFrame-Zeilen)
for firma in firmen[:3]:
    details = get_details(firma)
    print(f"{details.name}: {details.capital} {details.currency}")
```

---

## CLI-Skripte

### Bash-Integration

```bash
#!/bin/bash
# suche_und_benachrichtige.sh

# Nach neuen Unternehmen suchen
ergebnisse=$(handelsregister -s "Startup" --states BE --json)

# Ergebnisse zählen
anzahl=$(echo "$ergebnisse" | jq 'length')

if [ "$anzahl" -gt 0 ]; then
    echo "$anzahl neue Startups in Berlin gefunden"
    
    # Mit Datum speichern
    echo "$ergebnisse" > "startups_$(date +%Y%m%d).json"
    
    # Optional: Benachrichtigung senden
    # curl -X POST "https://slack.com/webhook" -d "{\"text\": \"$anzahl Startups gefunden\"}"
fi
```

### Python-Skript mit Logging

```python
#!/usr/bin/env python3
"""Tägliches Unternehmenssuche-Skript mit Logging."""

import logging
import json
from datetime import datetime
from handelsregister import search

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('unternehmenssuche.log'),
        logging.StreamHandler()
    ]
)

def main():
    logging.info("Starte Unternehmenssuche")
    
    suchbegriffe = ["Bank", "FinTech", "InsurTech"]
    
    alle_ergebnisse = {}
    for suchbegriff in suchbegriffe:
        logging.info(f"Suche: {suchbegriff}")
        ergebnisse = search(suchbegriff, states=["BE"])
        alle_ergebnisse[suchbegriff] = ergebnisse
        logging.info(f"{len(ergebnisse)} Unternehmen gefunden")
    
    # Ergebnisse speichern
    dateiname = f"ergebnisse_{datetime.now():%Y%m%d_%H%M%S}.json"
    with open(dateiname, 'w') as f:
        json.dump(alle_ergebnisse, f, indent=2)
    
    logging.info(f"Ergebnisse gespeichert in {dateiname}")

if __name__ == '__main__':
    main()
```

---

## Siehe auch

- [Einfache Beispiele](simple.md) – Grundlegende Beispiele
- [Fortgeschrittene Beispiele](advanced.md) – Komplexe Anwendungsfälle
- [API-Referenz](../api/index.md) – Technische Dokumentation

