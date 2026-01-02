#!/usr/bin/env python3
"""
Compatibility shim for backward compatibility.

This file maintains backward compatibility with the old single-file structure.
All imports are re-exported from the new package structure.

DEPRECATED: This file will be removed in a future version.
Please update your imports to use the new package structure:
    from handelsregister import search, HandelsRegister, SearchOptions
"""

from __future__ import annotations

import warnings

# Issue deprecation warning
warnings.warn(
    "Importing from handelsregister.py directly is deprecated. "
    "Please use 'from handelsregister import ...' instead. "
    "The old single-file structure will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export everything from the new package structure
from handelsregister import *  # noqa: F403, F401
