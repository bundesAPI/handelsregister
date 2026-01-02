"""Settings and configuration management using pydantic-settings."""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from yarl import URL


class Settings(BaseSettings):
    """Centralized configuration for the Handelsregister client.
    
    All settings can be overridden via environment variables with the
    HRG_ prefix. For example:
    
        export HRG_CACHE_TTL_SECONDS=7200
        export HRG_DEBUG=true
        export HRG_CACHE_DIR=/tmp/hr-cache
    
    Attributes:
        cache_ttl_seconds: TTL for search result cache (default: 1 hour).
        details_ttl_seconds: TTL for details cache (default: 24 hours).
        base_url: Base URL for the Handelsregister portal.
        request_timeout: HTTP request timeout in seconds.
        max_retries: Maximum retry attempts for failed requests.
        retry_wait_min: Minimum wait between retries in seconds.
        retry_wait_max: Maximum wait between retries in seconds.
        rate_limit_calls: Maximum requests per rate limit period.
        rate_limit_period: Rate limit period in seconds (default: 1 hour).
        cache_dir: Optional custom cache directory path.
        debug: Enable debug logging.
    """
    model_config = SettingsConfigDict(
        env_prefix="HRG_",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    # Cache settings
    cache_ttl_seconds: int = Field(default=3600, description="TTL for search cache in seconds")
    details_ttl_seconds: int = Field(default=86400, description="TTL for details cache in seconds")
    cache_dir: Optional[str] = Field(default=None, description="Custom cache directory path")
    
    # Network settings
    base_url: str = Field(default="https://www.handelsregister.de", description="Base URL")
    request_timeout: int = Field(default=10, ge=1, le=60, description="Request timeout in seconds")
    
    # Retry settings
    max_retries: int = Field(default=3, ge=1, le=10, description="Maximum retry attempts")
    retry_wait_min: int = Field(default=2, ge=1, description="Minimum retry wait in seconds")
    retry_wait_max: int = Field(default=10, ge=1, description="Maximum retry wait in seconds")
    
    # Rate limiting (per portal terms of service: max 60 requests/hour)
    rate_limit_calls: int = Field(default=60, ge=1, description="Max requests per period")
    rate_limit_period: int = Field(default=3600, description="Rate limit period in seconds")
    
    # Debug settings
    debug: bool = Field(default=False, description="Enable debug logging")
    
    @property
    def base_url_parsed(self) -> URL:
        """Returns base_url as a yarl.URL object."""
        return URL(self.base_url)


# Initialize global settings (can be overridden by environment variables)
settings = Settings()

# Backward-compatible constants (use settings.xxx for new code)
DEFAULT_CACHE_TTL_SECONDS: int = settings.cache_ttl_seconds
DETAILS_CACHE_TTL_SECONDS: int = settings.details_ttl_seconds
BASE_URL: URL = settings.base_url_parsed
REQUEST_TIMEOUT: int = settings.request_timeout
MAX_RETRIES: int = settings.max_retries
RETRY_WAIT_MIN: int = settings.retry_wait_min
RETRY_WAIT_MAX: int = settings.retry_wait_max
RATE_LIMIT_CALLS: int = settings.rate_limit_calls
RATE_LIMIT_PERIOD: int = settings.rate_limit_period

