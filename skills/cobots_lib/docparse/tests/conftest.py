"""
conftest.py - Shared test configuration for docparse tests.

Performs path setup once so individual test files don't need to
duplicate the boilerplate.  Also provides shared fixtures.
"""

import os
import sys

# -----------------------------------------------------------------------
# Path bootstrap: add the skills/ directory to sys.path so that
# ``cobots_lib.docparse`` is importable in test environments that
# lack a proper package install.
# -----------------------------------------------------------------------
_SKILLS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
if _SKILLS_DIR not in sys.path:
    sys.path.insert(0, _SKILLS_DIR)

# -----------------------------------------------------------------------
# Shared constants
# -----------------------------------------------------------------------
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
