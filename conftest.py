"""Pytest configuration for handelsregister tests."""

import pytest


def pytest_collection_modifyitems(config, items):
    """Skip integration tests by default unless explicitly requested."""
    if config.getoption("-m"):
        # If markers are explicitly specified, respect them
        return
    
    skip_integration = pytest.mark.skip(reason="Integration tests skipped by default. Use -m integration to run.")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)
