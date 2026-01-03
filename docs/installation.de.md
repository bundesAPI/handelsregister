# Installation

Diese Anleitung beschreibt die Installation des Handelsregister-Packages auf verschiedenen Systemen.

## Voraussetzungen

- **Python 3.9** oder höher
- **pip** oder **uv** als Paketmanager

## Installation mit uv (Empfohlen)

[uv](https://docs.astral.sh/uv/) ist ein moderner, schneller Python-Paketmanager. Er ist die empfohlene Methode zur Installation:

```bash
# Repository klonen
git clone https://github.com/bundesAPI/handelsregister.git
cd handelsregister

# Abhängigkeiten installieren
uv sync
```

Das Kommandozeilen-Tool ist dann verfügbar:

```bash
uv run handelsregister -s "Deutsche Bahn"
```

### Entwicklungsumgebung

Für die Entwicklung mit zusätzlichen Werkzeugen:

```bash
# Mit Entwicklungsabhängigkeiten
uv sync --extra dev

# Tests ausführen
uv run pytest
```

### Dokumentation lokal bauen

```bash
# Mit Dokumentationsabhängigkeiten
uv sync --extra docs

# Dokumentation starten
uv run mkdocs serve
```

---

## Installation mit pip

### Direkt von GitHub

```bash
pip install git+https://github.com/bundesAPI/handelsregister.git
```

### In einem Virtual Environment

```bash
# Virtual Environment erstellen
python -m venv venv

# Aktivieren (Linux/macOS)
source venv/bin/activate

# Aktivieren (Windows)
venv\Scripts\activate

# Installieren
pip install git+https://github.com/bundesAPI/handelsregister.git
```

### Aus lokalem Klon

```bash
# Repository klonen
git clone https://github.com/bundesAPI/handelsregister.git
cd handelsregister

# Als editierbares Package installieren
pip install -e .

# Mit Entwicklungsabhängigkeiten
pip install -e ".[dev]"
```

---

## Abhängigkeiten

Das Package hat folgende Abhängigkeiten:

| Package | Version | Beschreibung |
|---------|---------|--------------|
| `mechanize` | ≥0.4.8 | Browser-Automatisierung |
| `beautifulsoup4` | ≥4.11.0 | HTML-Parsing |

### Optionale Abhängigkeiten

=== "Entwicklung"

    ```
    black>=22.6.0       # Code-Formatierung
    pytest>=7.0.0       # Testing
    ```

=== "Dokumentation"

    ```
    mkdocs>=1.5.0                   # Dokumentationsgenerator
    mkdocs-material>=9.5.0          # Material Theme
    mkdocstrings[python]>=0.24.0    # API-Dokumentation
    mkdocs-static-i18n>=1.2.0       # Internationalisierung
    ```

---

## Systemspezifische Hinweise

### macOS

Auf macOS ist Python 3 in der Regel vorinstalliert. Falls nicht:

```bash
# Mit Homebrew
brew install python

# uv installieren
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Linux (Debian/Ubuntu)

```bash
# Python und pip installieren
sudo apt update
sudo apt install python3 python3-pip python3-venv

# uv installieren
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Windows

1. Python von [python.org](https://www.python.org/downloads/) herunterladen
2. Bei der Installation "Add Python to PATH" aktivieren
3. uv installieren:

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

---

## Überprüfung der Installation

Nach der Installation können Sie die Installation überprüfen:

=== "Als Modul"

    ```bash
    python -c "import handelsregister; print('Installation erfolgreich!')"
    ```

=== "CLI"

    ```bash
    handelsregister --help
    ```

=== "Mit uv"

    ```bash
    uv run python -c "import handelsregister; print('Installation erfolgreich!')"
    ```

---

## Häufige Probleme

### ModuleNotFoundError: No module named 'mechanize'

Die Abhängigkeiten wurden nicht korrekt installiert. Führen Sie erneut aus:

```bash
pip install mechanize beautifulsoup4
```

### SSL-Zertifikatsfehler

Auf manchen Systemen gibt es Probleme mit SSL-Zertifikaten:

```bash
# macOS: Zertifikate installieren
/Applications/Python\ 3.x/Install\ Certificates.command
```

### Permission Denied bei globaler Installation

Verwenden Sie `--user` oder ein Virtual Environment:

```bash
pip install --user git+https://github.com/bundesAPI/handelsregister.git
```

---

## Nächste Schritte

Nach erfolgreicher Installation:

- :material-rocket-launch: [Schnellstart](quickstart.md) – Erste Schritte mit dem Package
- :material-code-braces: [Library-Dokumentation](guide/library.md) – Integration in Python-Anwendungen
- :material-console: [CLI-Dokumentation](guide/cli.md) – Nutzung der Kommandozeile

