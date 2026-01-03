"""Pytest configuration for handelsregister tests."""

import contextlib

import pytest

from handelsregister import HandelsRegister


def pytest_collection_modifyitems(config, items):
    """Skip integration tests by default unless explicitly requested."""
    if config.getoption("-m"):
        # If markers are explicitly specified, respect them
        return

    skip_integration = pytest.mark.skip(
        reason="Integration tests skipped by default. Use -m integration to run."
    )
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)


@pytest.fixture(scope="class")
def shared_hr_client(request):
    """Shared HandelsRegister client for integration tests to reduce API calls.

    This fixture creates a single HandelsRegister instance that is shared across
    all tests in a test class. The startpage is opened once, and the browser
    session is reused to minimize API requests.

    Usage:
        def test_something(self, shared_hr_client):
            # Use shared_hr_client instead of creating a new instance
            results = shared_hr_client.search_with_options(...)
    """
    # Only create shared client for integration tests
    if "integration" not in request.keywords:
        return None

    # Create a shared client instance
    client = HandelsRegister(debug=False)
    # Open startpage once for the entire test class
    client.open_startpage()

    # Yield client to tests
    yield client

    # Cleanup after all tests in the class are done
    if hasattr(client.browser, "close"):
        with contextlib.suppress(Exception):
            client.browser.close()
