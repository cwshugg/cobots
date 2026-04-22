"""
test_result.py - Unit tests for the ParseResult dataclass.
"""

import os
import sys
import unittest

# Bootstrap: add skills/ to path.
_SKILLS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
if _SKILLS_DIR not in sys.path:
    sys.path.insert(0, _SKILLS_DIR)


from cobots_lib.docparse.result import ParseResult


class TestParseResult(unittest.TestCase):
    """Tests for ParseResult dataclass construction and defaults."""

    def test_basic_construction(self):
        """ParseResult can be constructed with required fields."""
        r = ParseResult(
            content="hello",
            output_format="text",
            source_path="/tmp/test.txt",
            source_format=".txt",
            handler_name="Test",
        )
        self.assertEqual(r.content, "hello")
        self.assertEqual(r.output_format, "text")
        self.assertEqual(r.source_path, "/tmp/test.txt")
        self.assertEqual(r.source_format, ".txt")
        self.assertEqual(r.handler_name, "Test")

    def test_defaults(self):
        """metadata and warnings default to empty."""
        r = ParseResult(
            content="",
            output_format="markdown",
            source_path="f.md",
            source_format=".md",
            handler_name="Test",
        )
        self.assertEqual(r.metadata, {})
        self.assertEqual(r.warnings, [])

    def test_metadata_and_warnings(self):
        """Custom metadata and warnings are preserved."""
        r = ParseResult(
            content="x",
            output_format="text",
            source_path="f",
            source_format=".txt",
            handler_name="T",
            metadata={"word_count": 42},
            warnings=["large file"],
        )
        self.assertEqual(r.metadata["word_count"], 42)
        self.assertEqual(r.warnings, ["large file"])

    def test_metadata_isolation(self):
        """Each ParseResult gets its own metadata/warnings dicts."""
        r1 = ParseResult(
            content="", output_format="text",
            source_path="a", source_format=".txt",
            handler_name="T",
        )
        r2 = ParseResult(
            content="", output_format="text",
            source_path="b", source_format=".txt",
            handler_name="T",
        )
        r1.metadata["key"] = "val"
        r1.warnings.append("warn")
        self.assertNotIn("key", r2.metadata)
        self.assertEqual(r2.warnings, [])


if __name__ == "__main__":
    unittest.main()
