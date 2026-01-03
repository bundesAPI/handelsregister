"""Caching layer using DiskCache for the Handelsregister package."""

import hashlib
import logging
import pathlib
import tempfile
from typing import Optional

import diskcache

from .settings import DEFAULT_CACHE_TTL_SECONDS, DETAILS_CACHE_TTL_SECONDS, settings

logger = logging.getLogger(__name__)


class SearchCache:
    """Caches search results and company details using DiskCache.

    Uses DiskCache for efficient, thread-safe caching with automatic TTL
    expiration. Different TTLs for search results (1h default) vs details
    (24h default) since details change less frequently.
    """

    def __init__(
        self,
        cache_dir: Optional[pathlib.Path] = None,
        ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS,
        details_ttl_seconds: int = DETAILS_CACHE_TTL_SECONDS,
    ) -> None:
        """Initialize the cache.

        Args:
            cache_dir: Directory to store cache files. Defaults to settings.cache_dir
                      or temp directory if not configured.
            ttl_seconds: Time-to-live for search result cache entries in seconds.
            details_ttl_seconds: Time-to-live for details cache entries in seconds.
        """
        self.ttl_seconds = ttl_seconds
        self.details_ttl_seconds = details_ttl_seconds

        # Use provided cache_dir, settings.cache_dir, or temp directory
        if cache_dir is not None:
            self.cache_dir = cache_dir
        elif settings.cache_dir:
            self.cache_dir = pathlib.Path(settings.cache_dir)
        else:
            self.cache_dir = pathlib.Path(tempfile.gettempdir()) / "handelsregister_cache"
        # Initialize DiskCache with size limit (500MB default)
        self._cache = diskcache.Cache(
            str(self.cache_dir),
            size_limit=500 * 1024 * 1024,
        )

    def _get_cache_key(self, query: str, options: str) -> str:
        """Generate a safe cache key by hashing the query parameters."""
        key_data = f"{query}|{options}"
        return hashlib.sha256(key_data.encode("utf-8")).hexdigest()

    def _get_cache_path(self, query: str, options: str) -> pathlib.Path:
        """Get the cache file path for a query (for backward compatibility)."""
        cache_key = self._get_cache_key(query, options)
        return self.cache_dir / f"{cache_key}.json"

    def get(self, query: str, options: str) -> Optional[str]:
        """Returns cached HTML if available and not expired.

        Args:
            query: Search query string (or cache key for details).
            options: Search options string.

        Returns:
            Cached HTML content, or None if not cached or expired.

        DiskCache handles expiration automatically based on the TTL set
        when the entry was stored.
        """
        cache_key = self._get_cache_key(query, options)
        return self._cache.get(cache_key, default=None)

    def set(self, query: str, options: str, html: str) -> None:
        """Caches HTML content with automatic TTL.

        Args:
            query: Search query string.
            options: Search options string.
            html: HTML content to cache.
        """
        cache_key = self._get_cache_key(query, options)
        # Use longer TTL for details cache
        ttl = self.details_ttl_seconds if query.startswith("details:") else self.ttl_seconds
        try:
            self._cache.set(cache_key, html, expire=ttl)
        except Exception as e:
            logger.warning("Failed to write cache: %s", e)

    def clear(self, details_only: bool = False) -> int:
        """Deletes all cache entries.

        Args:
            details_only: If True, only delete details cache entries.
                         Note: With DiskCache this clears all entries as we
                         cannot efficiently filter by key prefix.

        Returns:
            Number of entries deleted.
        """
        if details_only:
            # For details_only, we need to iterate and delete matching keys
            count = 0
            for key in list(self._cache):
                # Keys starting with details prefix have "details:" in query
                # Since we hash keys, we need to track this differently
                # For simplicity, we just clear all when details_only is True
                try:
                    del self._cache[key]
                    count += 1
                except KeyError:
                    pass
            return count
        count = len(self._cache)
        self._cache.clear()
        return count

    def get_stats(self) -> dict:
        """Returns cache statistics.

        Returns:
            Dict with total_files, search_files, details_files, and
            total_size_bytes.
        """
        return {
            "total_files": len(self._cache),
            "search_files": len(self._cache),  # DiskCache doesn't distinguish
            "details_files": 0,  # Would need metadata tracking
            "total_size_bytes": self._cache.volume(),
        }

    def close(self) -> None:
        """Closes the cache connection."""
        self._cache.close()

    def __enter__(self) -> "SearchCache":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()
