"""
test_rtf_handler.py - Tests for the RTF handler.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Path setup is done by conftest.py; ensure it's loaded when
# running this file directly.
from cobots_lib.docparse.tests.test_handlers.conftest import (
    FIXTURES_DIR,
)

from cobots_lib.docparse.handlers.rtf_handler import RtfHandler
from cobots_lib.docparse.errors import ParseError


class TestRtfHandler(unittest.TestCase):
    """Tests for RtfHandler."""

    def setUp(self):
        self.handler = RtfHandler()

    def test_extensions(self):
        self.assertEqual(self.handler.extensions, [".rtf"])

    def test_name(self):
        self.assertEqual(self.handler.name, "RTF")

    def test_available(self):
        """striprtf should be installed."""
        self.assertTrue(self.handler.available())

    def test_parse_real_fixture(self):
        """Integration: parse a real RTF file."""
        path = os.path.join(FIXTURES_DIR, "sample.rtf")
        result = self.handler.parse(path)
        self.assertEqual(result.output_format, "text")
        # Should contain extracted text.
        self.assertIn("sample RTF document", result.content)

    def test_parse_metadata(self):
        path = os.path.join(FIXTURES_DIR, "sample.rtf")
        result = self.handler.parse(path)
        self.assertIn("word_count", result.metadata)
        self.assertGreater(result.metadata["word_count"], 0)

    def test_parse_error_when_rtf_to_text_fails(self):
        """ParseError is raised when striprtf raises an exception."""
        path = os.path.join(FIXTURES_DIR, "sample.rtf")
        with patch(
            "striprtf.striprtf.rtf_to_text",
            side_effect=ValueError("bad RTF"),
        ):
            with self.assertRaises(ParseError) as ctx:
                self.handler.parse(path)
            self.assertIn(
                "Failed to convert RTF content",
                str(ctx.exception),
            )


if __name__ == "__main__":
    unittest.main()
