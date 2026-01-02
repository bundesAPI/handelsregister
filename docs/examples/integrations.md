# Integration Examples

Examples of integrating Handelsregister with popular frameworks and tools.

## FastAPI

### Simple API Endpoint

```python
from fastapi import FastAPI, HTTPException
from handelsregister import search, get_details, SearchError

app = FastAPI(title="Company Search API")

@app.get("/search")
async def search_companies(
    q: str,
    state: str = None,
    limit: int = 10
):
    """Search for companies."""
    try:
        states = [state] if state else None
        companies = search(q, states=states)
        return {
            "query": q,
            "count": len(companies),
            "results": companies[:limit]
        }
    except SearchError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/company/{court}/{number}")
async def get_company(court: str, number: str):
    """Get company details by register."""
    try:
        companies = search(
            "",
            register_number=number
        )
        if not companies:
            raise HTTPException(status_code=404, detail="Company not found")
        
        details = get_details(companies[0])
        return {
            "name": details.name,
            "capital": details.capital,
            "address": {
                "street": details.address.street if details.address else None,
                "city": details.address.city if details.address else None,
            },
            "representatives": [
                {"name": r.name, "role": r.role}
                for r in details.representatives
            ]
        }
    except SearchError as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Flask

### Simple Flask App

```python
from flask import Flask, request, jsonify
from handelsregister import search, get_details, SearchError

app = Flask(__name__)

@app.route('/search')
def search_companies():
    """Search endpoint."""
    query = request.args.get('q', '')
    state = request.args.get('state')
    
    if not query:
        return jsonify({"error": "Query required"}), 400
    
    try:
        states = [state] if state else None
        companies = search(query, states=states)
        return jsonify({
            "count": len(companies),
            "results": companies
        })
    except SearchError as e:
        return jsonify({"error": str(e)}), 500

@app.route('/company/<name>')
def company_details(name):
    """Get company details."""
    try:
        companies = search(name, keyword_option="exact")
        if not companies:
            return jsonify({"error": "Not found"}), 404
        
        details = get_details(companies[0])
        return jsonify({
            "name": details.name,
            "capital": details.capital,
            "currency": details.currency
        })
    except SearchError as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
```

---

## Django

### Django Management Command

```python
# myapp/management/commands/search_companies.py
from django.core.management.base import BaseCommand
from handelsregister import search

class Command(BaseCommand):
    help = 'Search for companies in the commercial register'

    def add_arguments(self, parser):
        parser.add_argument('query', type=str)
        parser.add_argument('--state', type=str, default=None)
        parser.add_argument('--limit', type=int, default=10)

    def handle(self, *args, **options):
        query = options['query']
        states = [options['state']] if options['state'] else None
        limit = options['limit']
        
        companies = search(query, states=states)
        
        self.stdout.write(f"Found {len(companies)} companies\n")
        for company in companies[:limit]:
            self.stdout.write(f"  - {company['name']}")
```

### Django Model Integration

```python
# models.py
from django.db import models
from handelsregister import search, get_details

class Company(models.Model):
    name = models.CharField(max_length=255)
    court = models.CharField(max_length=100)
    register_number = models.CharField(max_length=50)
    capital = models.DecimalField(max_digits=15, decimal_places=2, null=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    @classmethod
    def create_from_register(cls, company_name):
        """Create company from register data."""
        companies = search(company_name, exact=True)
        if not companies:
            raise ValueError(f"Company not found: {company_name}")
        
        details = get_details(companies[0])
        
        return cls.objects.create(
            name=details.name,
            court=details.court,
            register_number=details.register_number,
            capital=float(details.capital) if details.capital else None
        )
    
    def refresh_from_register(self):
        """Update company data from register."""
        companies = search(self.name, exact=True)
        if companies:
            details = get_details(companies[0])
            self.capital = float(details.capital) if details.capital else None
            self.save()
```

---

## Celery

### Background Tasks

```python
# tasks.py
from celery import Celery
from handelsregister import search, get_details
import time

app = Celery('tasks', broker='redis://localhost:6379/0')

@app.task(bind=True, max_retries=3)
def search_companies_task(self, query, states=None):
    """Search companies in background."""
    try:
        return search(query, states=states)
    except Exception as e:
        self.retry(countdown=60)

@app.task
def batch_search_task(keywords):
    """Search multiple keywords with rate limiting."""
    results = {}
    for keyword in keywords:
        results[keyword] = search(keyword)
        time.sleep(60)  # Rate limit
    return results

# Usage
result = search_companies_task.delay("Bank", states=["BE"])
companies = result.get(timeout=30)
```

---

## SQLAlchemy

### Store Results in Database

```python
from sqlalchemy import create_engine, Column, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from handelsregister import search, get_details

Base = declarative_base()
engine = create_engine('sqlite:///companies.db')
Session = sessionmaker(bind=engine)

class Company(Base):
    __tablename__ = 'companies'
    
    id = Column(String, primary_key=True)
    name = Column(String)
    court = Column(String)
    register_number = Column(String)
    capital = Column(Float)
    updated_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(engine)

def save_company(company_name):
    """Search and save company to database."""
    session = Session()
    
    companies = search(company_name, exact=True)
    if not companies:
        return None
    
    details = get_details(companies[0])
    
    company = Company(
        id=f"{details.court}_{details.register_num}",
        name=details.name,
        court=details.court,
        register_num=details.register_num,
        capital=float(details.capital) if details.capital else None
    )
    
    session.merge(company)
    session.commit()
    
    return company
```

---

## Jupyter Notebook

### Interactive Analysis

```python
# Cell 1: Setup
from handelsregister import search, get_details
import pandas as pd
import matplotlib.pyplot as plt

# Cell 2: Search and explore
companies = search("Bank", states=["BE", "HH", "BY"])
df = pd.DataFrame(companies)
df.head()

# Cell 3: Visualize by state
df['state'].value_counts().plot(kind='bar')
plt.title('Banks by State')
plt.xlabel('State')
plt.ylabel('Count')
plt.show()

# Cell 4: Get details for top companies
for _, row in df.head(3).iterrows():
    details = get_details(row.to_dict())
    print(f"{details.name}: {details.capital} {details.currency}")
```

---

## CLI Scripts

### Bash Integration

```bash
#!/bin/bash
# search_and_notify.sh

# Search for new companies
results=$(handelsregister -s "Startup" --states BE --json)

# Count results
count=$(echo "$results" | jq 'length')

if [ "$count" -gt 0 ]; then
    echo "Found $count new startups in Berlin"
    
    # Save to file with date
    echo "$results" > "startups_$(date +%Y%m%d).json"
    
    # Optional: Send notification
    # curl -X POST "https://slack.com/webhook" -d "{\"text\": \"Found $count startups\"}"
fi
```

### Python Script with Logging

```python
#!/usr/bin/env python3
"""Daily company search script with logging."""

import logging
import json
from datetime import datetime
from handelsregister import search

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('company_search.log'),
        logging.StreamHandler()
    ]
)

def main():
    logging.info("Starting company search")
    
    keywords = ["Bank", "FinTech", "InsurTech"]
    
    all_results = {}
    for keyword in keywords:
        logging.info(f"Searching: {keyword}")
        results = search(keyword, states=["BE"])
        all_results[keyword] = results
        logging.info(f"Found {len(results)} companies")
    
    # Save results
    filename = f"results_{datetime.now():%Y%m%d_%H%M%S}.json"
    with open(filename, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    logging.info(f"Results saved to {filename}")

if __name__ == '__main__':
    main()
```

---

## See Also

- [Simple Examples](simple.md) – Basic examples
- [Advanced Examples](advanced.md) – Complex use cases
- [API Reference](../api/index.md) – Technical documentation

