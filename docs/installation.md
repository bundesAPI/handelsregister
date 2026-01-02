# Installation

This guide describes how to install the Handelsregister package on various systems.

## Requirements

- **Python 3.9** or higher
- **pip** or **uv** as package manager

## Installation with uv (Recommended)

[uv](https://docs.astral.sh/uv/) is a modern, fast Python package manager. It's the recommended installation method:

```bash
# Clone the repository
git clone https://github.com/bundesAPI/handelsregister.git
cd handelsregister

# Install dependencies
uv sync
```

The command-line tool is then available:

```bash
uv run handelsregister -s "Deutsche Bahn"
```

### Development Environment

For development with additional tools:

```bash
# With development dependencies
uv sync --extra dev

# Run tests
uv run pytest
```

### Build Documentation Locally

```bash
# With documentation dependencies
uv sync --extra docs

# Start documentation server
uv run mkdocs serve
```

---

## Installation with pip

### Directly from GitHub

```bash
pip install git+https://github.com/bundesAPI/handelsregister.git
```

### In a Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (Linux/macOS)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install
pip install git+https://github.com/bundesAPI/handelsregister.git
```

### From Local Clone

```bash
# Clone repository
git clone https://github.com/bundesAPI/handelsregister.git
cd handelsregister

# Install as editable package
pip install -e .

# With development dependencies
pip install -e ".[dev]"
```

---

## Dependencies

The package has the following dependencies:

| Package | Version | Description |
|---------|---------|-------------|
| `mechanize` | ≥0.4.8 | Browser automation |
| `beautifulsoup4` | ≥4.11.0 | HTML parsing |

### Optional Dependencies

=== "Development"

    ```
    black>=22.6.0       # Code formatting
    pytest>=7.0.0       # Testing
    ```

=== "Documentation"

    ```
    mkdocs>=1.5.0                   # Documentation generator
    mkdocs-material>=9.5.0          # Material theme
    mkdocstrings[python]>=0.24.0    # API documentation
    mkdocs-static-i18n>=1.2.0       # Internationalization
    ```

---

## System-Specific Notes

### macOS

Python 3 is usually pre-installed on macOS. If not:

```bash
# With Homebrew
brew install python

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Linux (Debian/Ubuntu)

```bash
# Install Python and pip
sudo apt update
sudo apt install python3 python3-pip python3-venv

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Windows

1. Download Python from [python.org](https://www.python.org/downloads/)
2. Enable "Add Python to PATH" during installation
3. Install uv:

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

---

## Verify Installation

After installation, you can verify it:

=== "As Module"

    ```bash
    python -c "import handelsregister; print('Installation successful!')"
    ```

=== "CLI"

    ```bash
    handelsregister --help
    ```

=== "With uv"

    ```bash
    uv run python -c "import handelsregister; print('Installation successful!')"
    ```

---

## Common Issues

### ModuleNotFoundError: No module named 'mechanize'

Dependencies were not installed correctly. Run again:

```bash
pip install mechanize beautifulsoup4
```

### SSL Certificate Errors

Some systems have issues with SSL certificates:

```bash
# macOS: Install certificates
/Applications/Python\ 3.x/Install\ Certificates.command
```

### Permission Denied on Global Installation

Use `--user` or a virtual environment:

```bash
pip install --user git+https://github.com/bundesAPI/handelsregister.git
```

---

## Next Steps

After successful installation:

- :material-rocket-launch: [Quickstart](quickstart.md) – First steps with the package
- :material-code-braces: [Library Documentation](guide/library.md) – Integration into Python applications
- :material-console: [CLI Documentation](guide/cli.md) – Using the command line

