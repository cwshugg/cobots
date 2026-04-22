"""
test_markitdown_handler.py - Tests for the MarkItDown wrapper handler.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

_SKILLS_DIR = os.path.normpath(
    os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "..", ".."
    )
)
if _SKILLS_DIR not in sys.path:
    sys.path.insert(0, _SKILLS_DIR)

from cobots_lib.docparse.handlers.markitdown_handler import (
    MarkItDownHandler,
)
from cobots_lib.docparse.errors import ParseError
from cobots_lib.docparse.result import ParseResult


FIXTURES_DIR = os.path.join(
    os.path.dirname(__file__), "..", "fixtures"
)


class TestMarkItDownHandler(unittest.TestCase):
    """Tests for MarkItDownHandler."""

    def test_extensions(self):
        """Handler claims the expected extensions."""
        h = MarkItDownHandler()
        self.assertIn(".pdf", h.extensions)
        self.assertIn(".docx", h.extensions)
        self.assertIn(".txt", h.extensions)

    def test_name(self):
        h = MarkItDownHandler()
        self.assertEqual(h.name, "MarkItDown")

    @patch(
        "cobots_lib.docparse.handlers"
        ".markitdown_handler.MarkItDownHandler._get_markitdown"
    )
    def test_parse_delegates_to_markitdown(self, mock_get_md):
        """parse() delegates to MarkItDown.convert()."""
        mock_md = MagicMock()
        mock_result = MagicMock()
        mock_result.text_content = "# Title\n\nContent here."
        mock_md.convert.return_value = mock_result
        mock_get_md.return_value = mock_md

        h = MarkItDownHandler()
        txt_path = os.path.join(FIXTURES_DIR, "sample.txt")
        result = h.parse(txt_path)

        self.assertIsInstance(result, ParseResult)
        self.assertEqual(result.output_format, "markdown")
        self.assertIn("Title", result.content)
        mock_md.convert.assert_called_once_with(txt_path)

    @patch(
        "cobots_lib.docparse.handlers"
        ".markitdown_handler.MarkItDownHandler._get_markitdown"
    )
    def test_parse_error_handling(self, mock_get_md):
        """parse() wraps exceptions as ParseError."""
        mock_md = MagicMock()
        mock_md.convert.side_effect = RuntimeError("boom")
        mock_get_md.return_value = mock_md

        h = MarkItDownHandler()
        txt_path = os.path.join(FIXTURES_DIR, "sample.txt")
        with self.assertRaises(ParseError):
            h.parse(txt_path)

    def test_available(self):
        """available() returns True when markitdown is installed."""
        h = MarkItDownHandler()
        # Since we installed markitdown in the venv, it should be
        # available.
        self.assertTrue(h.available())

    def test_parse_real_txt(self):
        """Integration: parse a real .txt file."""
        h = MarkItDownHandler()
        if not h.available():
            self.skipTest("markitdown not installed")
        txt_path = os.path.join(FIXTURES_DIR, "sample.txt")
        result = h.parse(txt_path)
        self.assertIn("quick brown fox", result.content)


if __name__ == "__main__":
    unittest.main()
