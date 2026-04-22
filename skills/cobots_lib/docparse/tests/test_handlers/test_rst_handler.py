"""
test_rst_handler.py - Tests for the reStructuredText handler.
"""

import os
import sys
import unittest

_SKILLS_DIR = os.path.normpath(
    os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "..", ".."
    )
)
if _SKILLS_DIR not in sys.path:
    sys.path.insert(0, _SKILLS_DIR)

from cobots_lib.docparse.handlers.rst_handler import RstHandler

FIXTURES_DIR = os.path.join(
    os.path.dirname(__file__), "..", "fixtures"
)


class TestRstHandler(unittest.TestCase):
    """Tests for RstHandler."""

    def setUp(self):
        self.handler = RstHandler()

    def test_extensions(self):
        self.assertEqual(self.handler.extensions, [".rst"])

    def test_name(self):
        self.assertEqual(self.handler.name, "reStructuredText")

    def test_available(self):
        self.assertTrue(self.handler.available())

    def test_parse_wraps_in_code_block(self):
        path = os.path.join(FIXTURES_DIR, "sample.rst")
        result = self.handler.parse(path)
        self.assertTrue(result.content.startswith("```rst\n"))
        self.assertTrue(result.content.endswith("\n```"))
        self.assertEqual(result.output_format, "markdown")

    def test_parse_contains_original_content(self):
        path = os.path.join(FIXTURES_DIR, "sample.rst")
        result = self.handler.parse(path)
        self.assertIn("Sample RST Document", result.content)
        self.assertIn("Section One", result.content)

    def test_metadata_word_count(self):
        path = os.path.join(FIXTURES_DIR, "sample.rst")
        result = self.handler.parse(path)
        self.assertIn("word_count", result.metadata)
        self.assertGreater(result.metadata["word_count"], 0)


if __name__ == "__main__":
    unittest.main()
