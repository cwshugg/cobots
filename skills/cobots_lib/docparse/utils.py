"""
utils.py - Shared utility functions for the docparse library.

Provides common helpers used across multiple handler modules.
"""

from __future__ import annotations

import logging

_log = logging.getLogger(__name__)


def read_text(path: str, encoding: str | None = None) -> str:
    """Read a text file with encoding detection fallback.

    Strategy: respect explicit *encoding* → try UTF-8 → replace
    errors with U+FFFD.

    Args:
        path: Path to the text file.
        encoding: Optional explicit encoding to try first.

    Returns:
        The file content as a string.
    """
    if encoding:
        try:
            with open(path, "r", encoding=encoding) as fh:
                return fh.read()
        except (UnicodeDecodeError, LookupError):
            _log.warning(
                "Requested encoding %s failed, falling back to "
                "UTF-8 with replacement",
                encoding,
            )

    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    except UnicodeDecodeError:
        with open(path, "r", encoding="utf-8",
                  errors="replace") as fh:
            return fh.read()
