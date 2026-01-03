"""Data models for the Handelsregister package using Pydantic."""

import time
from dataclasses import dataclass
from typing import Any, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .constants import (
    RESULTS_PER_PAGE_OPTIONS,
    STATE_CODES,
    KeywordMatch,
    RegisterType,
    State,
)
from .settings import DEFAULT_CACHE_TTL_SECONDS


@dataclass
class CacheEntry:
    """Represents a cached search result with metadata.

    Note: Kept as dataclass for internal use only. Not part of public API.
    """

    query: str
    options: str
    timestamp: float
    html: str

    def is_expired(self, ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS) -> bool:
        """Checks if the cache entry has expired.

        Args:
            ttl_seconds: Time-to-live in seconds.

        Returns:
            True if expired, False otherwise.
        """
        return (time.time() - self.timestamp) > ttl_seconds

    def to_dict(self) -> dict:
        """Converts to dictionary for JSON serialization."""
        return {
            "query": self.query,
            "options": self.options,
            "timestamp": self.timestamp,
            "html": self.html,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CacheEntry":
        """Creates a CacheEntry from a dictionary."""
        return cls(
            query=data["query"],
            options=data["options"],
            timestamp=data["timestamp"],
            html=data["html"],
        )


class SearchOptions(BaseModel):
    """Encapsulates all search parameters for the Handelsregister.

    Uses Pydantic for validation and serialization.

    Attributes:
        keywords: Search keywords (schlagwoerter).
        keyword_option: How to match keywords (all, min, exact). Can be KeywordMatch enum or string.
        states: List of state codes to filter by (e.g., ['BE', 'HH']). Can be State enum or string.
        register_type: Register type filter (HRA, HRB, GnR, PR, VR). Can be RegisterType enum or string.
        register_number: Specific register number to search for.
        include_deleted: Include deleted/historical entries.
        similar_sounding: Use phonetic/similarity search.
        results_per_page: Number of results per page (10, 25, 50, 100). Must be in RESULTS_PER_PAGE_OPTIONS.
    """

    model_config = ConfigDict(frozen=False, validate_assignment=True)

    keywords: str = Field(..., min_length=1, description="Search keywords")
    keyword_option: Union[str, KeywordMatch] = Field(default="all", pattern="^(all|min|exact)$")
    states: Optional[list[Union[str, State]]] = Field(
        default=None, description="State codes to filter by"
    )
    register_type: Optional[Union[str, RegisterType]] = Field(
        default=None, pattern="^(HRA|HRB|GnR|PR|VR)$"
    )
    register_number: Optional[str] = None
    include_deleted: bool = False
    similar_sounding: bool = False
    results_per_page: int = Field(default=100, ge=10, le=100)

    @field_validator("keyword_option", mode="before")
    @classmethod
    def validate_keyword_option(cls, v: Union[str, KeywordMatch]) -> str:
        """Accepts both KeywordMatch enum and string."""
        if isinstance(v, KeywordMatch):
            return v.value
        return v

    @field_validator("states", mode="before")
    @classmethod
    def validate_states(cls, v: Optional[list[Union[str, State]]]) -> Optional[list[str]]:
        """Validates state codes against known values. Accepts both State enum and string."""
        if v is None:
            return None
        valid_codes = set(STATE_CODES.keys())
        result = []
        for state in v:
            # Extract value from enum if needed
            state_value = state.value if isinstance(state, State) else state
            state_upper = state_value.upper()
            if state_upper not in valid_codes:
                error_msg = (
                    f"Invalid state code: {state_value}. "
                    f"Valid: {', '.join(sorted(valid_codes))}"
                )
                raise ValueError(error_msg)
            result.append(state_upper)
        return result

    @field_validator("register_type", mode="before")
    @classmethod
    def validate_register_type(cls, v: Optional[Union[str, RegisterType]]) -> Optional[str]:
        """Accepts both RegisterType enum and string."""
        if v is None:
            return None
        if isinstance(v, RegisterType):
            return v.value
        return v

    @field_validator("results_per_page")
    @classmethod
    def validate_results_per_page(cls, v: int) -> int:
        """Validates results_per_page is a valid option."""
        if v not in RESULTS_PER_PAGE_OPTIONS:
            error_msg = f"results_per_page must be one of {RESULTS_PER_PAGE_OPTIONS}"
            raise ValueError(error_msg)
        return v

    def cache_key(self) -> str:
        """Generates a unique key for caching based on all options."""
        parts = [
            self.keywords,
            self.keyword_option,
            ",".join(sorted(self.states or [])),
            self.register_type or "",
            self.register_number or "",
            str(self.include_deleted),
            str(self.similar_sounding),
            str(self.results_per_page),
        ]
        return "|".join(parts)


class HistoryEntry(BaseModel):
    """Represents a historical name/location entry for a company."""

    model_config = ConfigDict(frozen=True)

    name: str
    location: str


class Address(BaseModel):
    """Represents a business address with validation."""

    model_config = ConfigDict(frozen=False)

    street: Optional[str] = None
    postal_code: Optional[str] = Field(default=None, pattern=r"^\d{5}$|^$|None")
    city: Optional[str] = None
    country: str = "Deutschland"

    @field_validator("postal_code", mode="before")
    @classmethod
    def validate_postal_code(cls, v: Any) -> Optional[str]:
        """Allow None or valid German postal codes."""
        if v is None or v == "":
            return None
        if isinstance(v, str) and len(v) == 5 and v.isdigit():
            return v
        # Be lenient - just return as-is for non-standard codes
        return str(v) if v else None

    def __str__(self) -> str:
        """Formats address as string."""
        parts = []
        if self.street:
            parts.append(self.street)
        if self.postal_code and self.city:
            parts.append(f"{self.postal_code} {self.city}")
        elif self.city:
            parts.append(self.city)
        if self.country and self.country != "Deutschland":
            parts.append(self.country)
        return ", ".join(parts) if parts else ""

    def to_dict(self) -> dict:
        """Convert to dictionary (for backward compatibility)."""
        return self.model_dump()


class Representative(BaseModel):
    """Represents a company representative (Geschäftsführer, Vorstand, etc.)."""

    model_config = ConfigDict(frozen=False)

    name: str = Field(..., min_length=1, description="Name of the representative")
    role: str = Field(..., description="Role (e.g., Geschäftsführer, Vorstand)")
    location: Optional[str] = None
    birth_date: Optional[str] = None
    restrictions: Optional[str] = None  # e.g., "einzelvertretungsberechtigt"

    def to_dict(self) -> dict:
        """Converts to dictionary (for backward compatibility)."""
        return self.model_dump()


class Owner(BaseModel):
    """Represents a company owner/shareholder (Gesellschafter)."""

    model_config = ConfigDict(frozen=False)

    name: str = Field(..., min_length=1, description="Name of the owner")
    share: Optional[str] = None  # e.g., "50%", "25.000 EUR"
    owner_type: Optional[str] = None  # e.g., "Kommanditist", "Gesellschafter"
    location: Optional[str] = None

    def to_dict(self) -> dict:
        """Converts to dictionary (for backward compatibility)."""
        return self.model_dump()


class CompanyDetails(BaseModel):
    """Extended company information from detail views.

    Contains all information available from the Handelsregister detail
    views (AD, SI, UT). Uses Pydantic for validation and serialization.
    """

    model_config = ConfigDict(frozen=False, validate_assignment=True)

    # Basic identification (from search results)
    name: str = Field(..., description="Company name")
    register_num: str = Field(default="", description="Register number (e.g., HRB 12345 B)")
    court: str = Field(default="", description="Registration court")
    state: str = Field(default="", description="Federal state")
    status: str = Field(default="", description="Registration status")

    # Extended information (from detail views)
    legal_form: Optional[str] = Field(default=None, description="Legal form (AG, GmbH, KG, etc.)")
    capital: Optional[str] = Field(default=None, description="Share capital / Stammkapital")
    currency: Optional[str] = Field(default=None, description="Currency (EUR, etc.)")
    address: Optional[Address] = None
    purpose: Optional[str] = Field(
        default=None, description="Business purpose / Unternehmensgegenstand"
    )
    representatives: list[Representative] = Field(default_factory=list)
    owners: list[Owner] = Field(default_factory=list)
    registration_date: Optional[str] = Field(default=None, description="Registration date")
    last_update: Optional[str] = Field(default=None, description="Last update date")
    deletion_date: Optional[str] = Field(default=None, description="Deletion date (if deleted)")

    # Additional metadata
    raw_data: Optional[dict] = Field(default=None, repr=False, exclude=True)

    def to_dict(self) -> dict:
        """Converts to dictionary for JSON serialization (backward compatibility)."""
        # Pydantic's model_dump() automatically handles nested models
        return self.model_dump(exclude={"raw_data"}, mode="python")

    @classmethod
    def from_company(cls, company: Union["Company", dict[str, Any]]) -> "CompanyDetails":
        """Creates CompanyDetails from a Company search result or dict.

        Args:
            company: Company object or dict with company information.

        Returns:
            CompanyDetails with basic information from the company.
        """
        if isinstance(company, dict):
            # Backward compatibility: accept dict
            return cls(
                name=company.get("name", ""),
                register_num=company.get("register_num", "") or "",
                court=company.get("court", ""),
                state=company.get("state", ""),
                status=company.get("status", ""),
            )
        # Company object
        return cls(
            name=company.name,
            register_num=company.register_num or "",
            court=company.court,
            state=company.state,
            status=company.status,
        )


class Company(BaseModel):
    """Represents a company record from the Handelsregister.

    This is the primary model for search results. It provides validation
    and type safety while maintaining backward compatibility with dict access.
    """

    model_config = ConfigDict(frozen=False, populate_by_name=True)

    court: str
    name: str
    state: str
    status: str
    status_normalized: str = Field(default="", alias="statusCurrent")
    documents: str
    register_num: Optional[str] = None
    history: list[HistoryEntry] = Field(default_factory=list)
    row_index: Optional[int] = Field(default=None, exclude=True)  # Internal use for detail fetching

    def to_dict(self) -> dict:
        """Converts to dictionary for backward compatibility."""
        data = self.model_dump(by_alias=True, exclude={"row_index"})
        # Convert history from HistoryEntry objects to tuples for backward compatibility
        data["history"] = [(h.name, h.location) for h in self.history]
        return data

    def get(self, key: str, default: Any = None) -> Any:
        """Dict-like access for backward compatibility."""
        return getattr(self, key, default)
