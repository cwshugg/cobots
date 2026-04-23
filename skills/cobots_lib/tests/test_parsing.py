"""
test_parsing.py - Unit tests for cobots_lib.parsing.

Tests parse_frontmatter() and parse_discussion_headers(), including
edge cases such as malformed YAML, missing delimiters, and empty bodies.
"""

import os
import sys
import tempfile
import unittest

# ---------------------------------------------------------------------------
# Bootstrap: ensure cobots_lib is importable.
# ---------------------------------------------------------------------------
_SKILLS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)
if _SKILLS_DIR not in sys.path:
    sys.path.insert(0, _SKILLS_DIR)

from cobots_lib.parsing import parse_frontmatter, parse_discussion_headers


class TestParseFrontmatterValid(unittest.TestCase):
    """parse_frontmatter with well-formed content."""

    def test_returns_dict_and_body(self) -> None:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write("---\ntitle: Hello\nauthor: alice\n---\nBody text here.")
            path = f.name
        try:
            fm, body = parse_frontmatter(path)
            self.assertEqual(fm["title"], "Hello")
            self.assertEqual(fm["author"], "alice")
            self.assertEqual(body, "Body text here.")
        finally:
            os.unlink(path)


class TestParseFrontmatterNoDelimiters(unittest.TestCase):
    """parse_frontmatter with content that has no --- delimiters."""

    def test_returns_empty_dict_and_full_content(self) -> None:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write("No frontmatter here, just plain text.")
            path = f.name
        try:
            fm, body = parse_frontmatter(path)
            self.assertEqual(fm, {})
            self.assertEqual(body, "No frontmatter here, just plain text.")
        finally:
            os.unlink(path)


class TestParseFrontmatterMalformedYaml(unittest.TestCase):
    """parse_frontmatter with invalid YAML between --- delimiters."""

    def test_returns_empty_dict_on_yaml_error(self) -> None:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write("---\n: invalid: [yaml: {broken\n---\nBody.")
            path = f.name
        try:
            fm, body = parse_frontmatter(path)
            self.assertEqual(fm, {})
            # On malformed YAML we return the entire original content
            self.assertIn("---", body)
        finally:
            os.unlink(path)


class TestParseFrontmatterSingleDelimiter(unittest.TestCase):
    """parse_frontmatter with only one --- line (no closing)."""

    def test_returns_empty_dict(self) -> None:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write("---\ntitle: Hello\nBody text")
            path = f.name
        try:
            fm, body = parse_frontmatter(path)
            self.assertEqual(fm, {})
        finally:
            os.unlink(path)


class TestParseDiscussionHeaders(unittest.TestCase):
    """parse_discussion_headers extracts timestamp-author pairs."""

    def test_extracts_headers(self) -> None:
        body = (
            "Some text.\n"
            "## 2026-04-22 10:30:00 - Alice\n"
            "Discussion entry 1.\n"
            "## 2026-04-22 11:00:00 - Bob\n"
            "Discussion entry 2.\n"
        )
        headers = parse_discussion_headers(body)
        self.assertEqual(len(headers), 2)
        self.assertEqual(headers[0], ("2026-04-22 10:30:00", "Alice"))
        self.assertEqual(headers[1], ("2026-04-22 11:00:00", "Bob"))

    def test_empty_body_returns_empty(self) -> None:
        headers = parse_discussion_headers("")
        self.assertEqual(headers, [])

    def test_no_headers_returns_empty(self) -> None:
        body = "Just some text\nNothing special\n# Heading level 1\n"
        headers = parse_discussion_headers(body)
        self.assertEqual(headers, [])


if __name__ == "__main__":
    unittest.main()
