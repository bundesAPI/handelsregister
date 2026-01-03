"""Exception classes for the Handelsregister package."""

from typing import Optional


class HandelsregisterError(Exception):
    """Base exception for all Handelsregister errors."""


class NetworkError(HandelsregisterError):
    """Raised when a network request fails."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error


class ParseError(HandelsregisterError):
    """Raised when HTML parsing fails."""

    def __init__(self, message: str, html_snippet: Optional[str] = None):
        super().__init__(message)
        self.html_snippet = html_snippet


class FormError(HandelsregisterError):
    """Raised when form interaction fails."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error


class CacheError(HandelsregisterError):
    """Raised when cache operations fail."""


class PartialResultError(HandelsregisterError):
    """Raised when a batch operation completes with some failures.

    This exception contains information about which operations succeeded
    and which failed, allowing for graceful degradation.
    """

    def __init__(
        self,
        message: str,
        successful: list,
        failed: list[tuple[object, Exception]],
    ):
        super().__init__(message)
        self.successful = successful
        self.failed = failed  # List of (item, exception) tuples
