"""
test_yaml_handler.py - Tests for the YAML handler.
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

from cobots_lib.docparse.handlers.yaml_handler import YamlHandler

FIXTURES_DIR = os.path.join(
    os.path.dirname(__file__), "..", "fixtures"
)


class TestYamlHandler(unittest.TestCase):
    """Tests for YamlHandler."""

    def setUp(self):
        self.handler = YamlHandler()

    def test_extensions(self):
        self.assertEqual(self.handler.extensions, [".yaml", ".yml"])

    def test_name(self):
        self.assertEqual(self.handler.name, "YAML")

    def test_available(self):
        self.assertTrue(self.handler.available())

    def test_parse_wraps_in_code_block(self):
        """Content is wrapped in a fenced YAML code block."""
        path = os.path.join(FIXTURES_DIR, "sample.yaml")
        result = self.handler.parse(path)
        self.assertTrue(result.content.startswith("```yaml\n"))
        self.assertTrue(result.content.endswith("\n```"))
        self.assertEqual(result.output_format, "markdown")

    def test_parse_contains_original_content(self):
        """Original YAML content is preserved inside the block."""
        path = os.path.join(FIXTURES_DIR, "sample.yaml")
        result = self.handler.parse(path)
        self.assertIn("name: Sample Config", result.content)
        self.assertIn("debug: true", result.content)

    def test_metadata_word_count(self):
        """word_count metadata is populated."""
        path = os.path.join(FIXTURES_DIR, "sample.yaml")
        result = self.handler.parse(path)
        self.assertIn("word_count", result.metadata)
        self.assertGreater(result.metadata["word_count"], 0)


if __name__ == "__main__":
    unittest.main()
