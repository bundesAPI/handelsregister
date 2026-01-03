# Command Line (CLI)

The Handelsregister package includes a powerful command-line interface for quick queries.

## Basic Usage

```bash
# Simple search
handelsregister -s "Deutsche Bahn"
# Or use the shorter alias:
hrg -s "Deutsche Bahn"

# With uv
uv run handelsregister -s "Deutsche Bahn"
# Or:
uv run hrg -s "Deutsche Bahn"
```

---

## Search Options

### `-s, --search`
The search term (required):

```bash
handelsregister -s "Bank"
handelsregister -s "Deutsche Bahn AG"
```

### `--states`
Filter by states (comma-separated):

```bash
# Single state
handelsregister -s "Bank" --states BE

# Multiple states
handelsregister -s "Bank" --states BE,HH,BY
```

### `--register-type`
Filter by register type:

```bash
# Only HRB (corporations)
handelsregister -s "GmbH" --register-type HRB

# Only HRA (partnerships)
handelsregister -s "KG" --register-type HRA
```

### `--exact`
Require exact name match:

```bash
handelsregister -s "GASAG AG" --exact
```

### `--active-only`
Only show currently registered companies:

```bash
handelsregister -s "Bank" --active-only
```

---

## Output Formats

### Default Output

```bash
handelsregister -s "GASAG"
```

```
Found 3 companies:

1. GASAG AG
   Court: Berlin (Charlottenburg)
   Number: HRB 44343
   Status: currently registered

2. GASAG Beteiligungs GmbH
   Court: Berlin (Charlottenburg)
   Number: HRB 87654
   Status: currently registered
...
```

### JSON Output

```bash
handelsregister -s "GASAG" --json
```

```json
[
  {
    "name": "GASAG AG",
    "register_court": "Berlin (Charlottenburg)",
    "register_num": "HRB 44343",
    "status": "currently registered",
    "state": "BE"
  },
  ...
]
```

### Compact Output

```bash
handelsregister -s "GASAG" --compact
```

```
GASAG AG | Berlin (Charlottenburg) | HRB 44343
GASAG Beteiligungs GmbH | Berlin (Charlottenburg) | HRB 87654
```

---

## Fetching Details

### `--details`
Fetch extended information:

```bash
handelsregister -s "GASAG AG" --exact --details
```

```
GASAG AG
=========
Court: Berlin (Charlottenburg)
Number: HRB 44343
Status: currently registered

Capital: 306,977,800.00 EUR

Address:
  GASAG-Platz 1
  10963 Berlin

Representatives:
  - Dr. Gerhard Holtmeier (Vorstandsvorsitzender)
  - Stefan Michels (Vorstand)
  - Jörg Simon (Vorstand)

Business Purpose:
  Gegenstand des Unternehmens ist die Versorgung mit Energie...
```

### `--details --json`
Details in JSON format:

```bash
handelsregister -s "GASAG AG" --exact --details --json
```

---

## Caching Options

### `--no-cache`
Skip cache, always fetch fresh data:

```bash
handelsregister -s "Bank" --no-cache
```

### `--clear-cache`
Clear the entire cache:

```bash
handelsregister --clear-cache
```

---

## Other Options

### `--help`
Show help message:

```bash
handelsregister --help
```

```
usage: handelsregister [-h] [-s SEARCH] [--states STATES]
                       [--register-type TYPE] [--exact]
                       [--active-only] [--details] [--json]
                       [--compact] [--no-cache] [--clear-cache]

Query the German commercial register

options:
  -h, --help            show this help message and exit
  -s, --search SEARCH   Search term
  --states STATES       Filter by states (comma-separated)
  --register-type TYPE  Filter by register type
  --exact               Exact name match
  --active-only         Only currently registered
  --details             Fetch company details
  --json                JSON output
  --compact             Compact output
  --no-cache            Skip cache
  --clear-cache         Clear cache
```

### `--version`
Show version:

```bash
handelsregister --version
```

---

## Examples

### Search for Banks in Berlin

```bash
handelsregister -s "Bank" --states BE --register-type HRB
```

### Export to JSON File

```bash
handelsregister -s "Versicherung" --states BY --json > insurance_by.json
```

### Pipe to jq for Processing

```bash
handelsregister -s "Bank" --json | jq '.[].name'
```

### Loop Through States

```bash
for state in BE HH BY; do
    echo "=== $state ==="
    handelsregister -s "Bank" --states $state --compact
    sleep 60  # Respect rate limit
done
```

### Get Details for Specific Company

```bash
handelsregister -s "Deutsche Bahn AG" --exact --details
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | No results found |
| 2 | Connection error |
| 3 | Rate limit exceeded |
| 4 | Invalid arguments |

### Using Exit Codes in Scripts

```bash
handelsregister -s "Bank" --states BE

if [ $? -eq 0 ]; then
    echo "Search successful"
elif [ $? -eq 1 ]; then
    echo "No results found"
elif [ $? -eq 3 ]; then
    echo "Rate limit - try again later"
fi
```

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `HANDELSREGISTER_CACHE_DIR` | Cache directory | `~/.cache/handelsregister` |
| `HANDELSREGISTER_CACHE_TTL` | Cache TTL in hours | `24` |
| `HANDELSREGISTER_DEBUG` | Enable debug output | `0` |

```bash
# Example: Custom cache directory
export HANDELSREGISTER_CACHE_DIR=/tmp/hr-cache
handelsregister -s "Bank"

# Example: Disable cache
export HANDELSREGISTER_CACHE_TTL=0
handelsregister -s "Bank"
```

---

## See Also

- [Using as Library](library.md) – Python integration
- [Reference Tables](../reference/states.md) – State codes, register types
- [Examples](../examples/simple.md) – More examples

