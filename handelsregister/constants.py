"""Constants and configuration for the Handelsregister package."""

from yarl import URL

# Mapping of keyword option names to form values
KEYWORD_OPTIONS: dict[str, int] = {"all": 1, "min": 2, "exact": 3}

# Mapping of states to register type suffixes
SUFFIX_MAP: dict[str, dict[str, str]] = {
    "Berlin": {"HRB": " B"},
    "Bremen": {"HRA": " HB", "HRB": " HB", "GnR": " HB", "VR": " HB", "PR": " HB"},
}

# German state codes for filtering (bundesland parameters)
STATE_CODES: dict[str, str] = {
    "BW": "Baden-Württemberg",
    "BY": "Bayern",
    "BE": "Berlin",
    "BR": "Brandenburg",
    "HB": "Bremen",
    "HH": "Hamburg",
    "HE": "Hessen",
    "MV": "Mecklenburg-Vorpommern",
    "NI": "Niedersachsen",
    "NW": "Nordrhein-Westfalen",
    "RP": "Rheinland-Pfalz",
    "SL": "Saarland",
    "SN": "Sachsen",
    "ST": "Sachsen-Anhalt",
    "SH": "Schleswig-Holstein",
    "TH": "Thüringen",
}

# Register types
REGISTER_TYPES: list[str] = ["HRA", "HRB", "GnR", "PR", "VR"]

# Results per page options
RESULTS_PER_PAGE_OPTIONS: list[int] = [10, 25, 50, 100]

# For backward compatibility
schlagwortOptionen = KEYWORD_OPTIONS  # noqa: N816


def build_url(path: str = "", base_url: URL | None = None, **query_params) -> URL:
    """Builds a URL from BASE_URL with path and optional query parameters.

    Uses yarl for safe URL construction with proper encoding.

    Args:
        path: Path to append to BASE_URL (e.g., "rp_web/erweitertesuche.xhtml").
        base_url: Base URL to use (defaults to settings.base_url_parsed).
        **query_params: Query parameters to add to the URL.

    Returns:
        yarl.URL object with the constructed URL.

    Example:
        >>> url = build_url("rp_web/search", q="Bank", page="1")
        >>> str(url)
        'https://www.handelsregister.de/rp_web/search?q=Bank&page=1'
    """
    from .settings import settings

    url_base = base_url if base_url is not None else settings.base_url_parsed
    url = url_base / path if path else url_base
    if query_params:
        url = url.with_query(query_params)
    return url
