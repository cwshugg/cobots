"""
test_api.py - Unit tests for the public API module (__init__.py).

Tests the module-level singleton, wrapper functions, and error
propagation.
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

_SKILLS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
if _SKILLS_DIR not in sys.path:
    sys.path.insert(0, _SKILLS_DIR)

import cobots_lib.docparse as docparse_mod
from cobots_lib.docparse import (
    parse_file,
    parse_bytes,
    supported_formats,
    ParseResult,
)
from cobots_lib.docparse.errors import UnsupportedFormatError


class TestPublicAPI(unittest.TestCase):
    """Tests for the docparse public API."""

    def test_supported_formats_returns_list(self):
        """supported_formats returns a non-empty list."""
        fmts = supported_formats()
        self.assertIsInstance(fmts, list)
        self.assertTrue(len(fmts) > 0)

    def test_parse_file_real_txt(self):
        """parse_file works on a real text file."""
        fixtures_dir = os.path.join(
            os.path.dirname(__file__), "fixtures"
        )
        path = os.path.join(fixtures_dir, "sample.txt")
        result = parse_file(path)
        self.assertIsInstance(result, ParseResult)
        self.assertIn("quick brown fox", result.content)

    def test_parse_bytes_yaml(self):
        """parse_bytes works with YAML content."""
        data = b"key: value\nlist:\n  - one\n  - two\n"
        result = parse_bytes(data, "test.yaml")
        self.assertIsInstance(result, ParseResult)
        self.assertIn("key: value", result.content)
        self.assertEqual(result.source_path, "<bytes>")

    def test_parse_file_unsupported(self):
        """parse_file raises UnsupportedFormatError for unknown."""
        with tempfile.NamedTemporaryFile(
            suffix=".zzz", delete=False
        ) as f:
            f.write(b"test")
            path = f.name
        try:
            with self.assertRaises(UnsupportedFormatError):
                parse_file(path)
        finally:
            os.unlink(path)

    def test_singleton_reuse(self):
        """The module-level singleton is reused across calls."""
        # Reset singleton.
        docparse_mod._converter = None
        _ = supported_formats()
        first = docparse_mod._converter
        _ = supported_formats()
        second = docparse_mod._converter
        self.assertIs(first, second)


if __name__ == "__main__":
    unittest.main()
