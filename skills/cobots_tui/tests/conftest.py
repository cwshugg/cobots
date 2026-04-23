"""conftest.py - Shared test configuration and path setup."""
import os
import sys
from unittest.mock import MagicMock

_SKILLS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
if _SKILLS_DIR not in sys.path:
    sys.path.insert(0, _SKILLS_DIR)
_SKILL_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
if _SKILL_DIR not in sys.path:
    sys.path.insert(0, _SKILL_DIR)
sys.modules.setdefault("venv", MagicMock())
sys.modules.setdefault("venv.venv", MagicMock())
