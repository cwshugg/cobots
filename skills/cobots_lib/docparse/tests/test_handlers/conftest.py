"""
conftest.py - Shared test configuration for handler tests.

Inherits path setup from the parent conftest and provides
handler-specific fixtures.
"""

import os
import sys

# -----------------------------------------------------------------------
# Path bootstrap: add the skills/ directory to sys.path.
# -----------------------------------------------------------------------
_SKILLS_DIR = os.path.normpath(
    os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "..", ".."
    )
)
if _SKILLS_DIR not in sys.path:
    sys.path.insert(0, _SKILLS_DIR)

# -----------------------------------------------------------------------
# Shared constants
# -----------------------------------------------------------------------
FIXTURES_DIR = os.path.join(
    os.path.dirname(__file__), "..", "fixtures"
)
