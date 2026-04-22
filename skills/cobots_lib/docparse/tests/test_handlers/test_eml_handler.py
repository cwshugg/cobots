"""
test_eml_handler.py - Tests for the EML handler.
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

from cobots_lib.docparse.handlers.eml_handler import EmlHandler

FIXTURES_DIR = os.path.join(
    os.path.dirname(__file__), "..", "fixtures"
)


class TestEmlHandler(unittest.TestCase):
    """Tests for EmlHandler."""

    def setUp(self):
        self.handler = EmlHandler()

    def test_extensions(self):
        self.assertEqual(self.handler.extensions, [".eml"])

    def test_name(self):
        self.assertEqual(self.handler.name, "EML")

    def test_available(self):
        """markdownify should be installed (via markitdown)."""
        self.assertTrue(self.handler.available())

    def test_parse_real_fixture(self):
        """Parse a real .eml file."""
        path = os.path.join(FIXTURES_DIR, "sample.eml")
        result = self.handler.parse(path)
        self.assertEqual(result.output_format, "markdown")
        self.assertIn("sender@example.com", result.content)
        self.assertIn("Sample Email", result.content)
        self.assertIn("quick brown fox", result.content)

    def test_parse_headers_present(self):
        """Headers are formatted in the output."""
        path = os.path.join(FIXTURES_DIR, "sample.eml")
        result = self.handler.parse(path)
        self.assertIn("**From:**", result.content)
        self.assertIn("**To:**", result.content)
        self.assertIn("**Subject:**", result.content)

    def test_metadata_with_include_metadata(self):
        """PII metadata populated when include_metadata=True."""
        path = os.path.join(FIXTURES_DIR, "sample.eml")
        result = self.handler.parse(
            path, include_metadata=True
        )
        self.assertIn("subject", result.metadata)
        self.assertIn("date", result.metadata)

    def test_metadata_without_include_metadata(self):
        """PII metadata not in metadata when not requested."""
        path = os.path.join(FIXTURES_DIR, "sample.eml")
        result = self.handler.parse(path)
        self.assertNotIn("subject", result.metadata)
        self.assertNotIn("date", result.metadata)


if __name__ == "__main__":
    unittest.main()
