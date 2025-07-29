"""FastReader package.

This file enables Python to treat the `fastreader` directory as a package.
"""

# Expose create_app at package level for WSGI servers if needed
from .app import create_app  # noqa: F401