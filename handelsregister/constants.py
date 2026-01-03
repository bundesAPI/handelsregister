"""Constants and configuration for the Handelsregister package."""

from enum import Enum
from typing import Optional

from yarl import URL


class State(str, Enum):
    """German federal states (Bundesländer).

    Usage:
        >>> from handelsregister import State
        >>> search("Bank", states=[State.BE, State.HH])
    """

    BW = "BW"  # Baden-Württemberg
    BY = "BY"  # Bayern
    BE = "BE"  # Berlin
    BR = "BR"  # Brandenburg
    HB = "HB"  # Bremen
    HH = "HH"  # Hamburg
    HE = "HE"  # Hessen
    MV = "MV"  # Mecklenburg-Vorpommern
    NI = "NI"  # Niedersachsen
    NW = "NW"  # Nordrhein-Westfalen
    RP = "RP"  # Rheinland-Pfalz
    SL = "SL"  # Saarland
    SN = "SN"  # Sachsen
    ST = "ST"  # Sachsen-Anhalt
    SH = "SH"  # Schleswig-Holstein
    TH = "TH"  # Thüringen

    @property
    def name_de(self) -> str:
        """Returns the German name of the state."""
        return STATE_CODES[self.value]

    def __str__(self) -> str:
        return self.value


class KeywordMatch(str, Enum):
    """Keyword matching options for search.

    Usage:
        >>> from handelsregister import KeywordMatch
        >>> search("Bank", keyword_option=KeywordMatch.EXACT)
    """

    ALL = "all"  # All keywords must match
    MIN = "min"  # At least one keyword must match
    EXACT = "exact"  # Exact name match

    @property
    def form_value(self) -> int:
        """Returns the form value for this option."""
        return KEYWORD_OPTIONS[self.value]

    def __str__(self) -> str:
        return self.value


class RegisterType(str, Enum):
    """Register types in the Handelsregister.

    Usage:
        >>> from handelsregister import RegisterType
        >>> search("Bank", register_type=RegisterType.HRB)
    """

    HRA = "HRA"  # Handelsregister A (Partnerships)
    HRB = "HRB"  # Handelsregister B (Corporations)
    GnR = "GnR"  # Genossenschaftsregister (Cooperatives)
    PR = "PR"  # Partnerschaftsregister (Partnerships)
    VR = "VR"  # Vereinsregister (Associations)

    def __str__(self) -> str:
        return self.value


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

# Results per page options (must be one of these values)
RESULTS_PER_PAGE_OPTIONS: list[int] = [10, 25, 50, 100]

# For backward compatibility
schlagwortOptionen = KEYWORD_OPTIONS  # noqa: N816


def build_url(path: str = "", base_url: Optional[URL] = None, **query_params) -> URL:
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
