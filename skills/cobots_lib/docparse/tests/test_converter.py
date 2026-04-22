"""
test_converter.py - Unit tests for the DocumentConverter orchestrator.
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

# Path setup is done by conftest.py; ensure it's loaded when
# running this file directly.
from cobots_lib.docparse.tests.conftest import FIXTURES_DIR  # noqa: F401

from cobots_lib.docparse.converter import DocumentConverter
from cobots_lib.docparse.errors import (
    DependencyMissingError,
    ParseError,
    SecurityError,
    UnsupportedFormatError,
)
from cobots_lib.docparse.handlers.base import BaseHandler
from cobots_lib.docparse.registry import HandlerRegistry
from cobots_lib.docparse.result import ParseResult


class _MockHandler(BaseHandler):
    """Simple mock handler for converter tests."""

    def __init__(self, exts=None, name="Mock", content="result"):
        self._exts = exts or [".mock"]
        self._name = name
        self._content = content

    @property
    def extensions(self):
        return self._exts

    @property
    def name(self):
        return self._name

    def parse(self, file_path, **kwargs):
        return ParseResult(
            content=self._content,
            output_format="text",
            source_path=file_path,
            source_format=self._exts[0],
            handler_name=self._name,
        )


class TestDocumentConverter(unittest.TestCase):
    """Tests for DocumentConverter."""

    def _make_file(self, suffix=".mock", content=b"test"):
        """Create a temp file and return its path."""
        f = tempfile.NamedTemporaryFile(
            suffix=suffix, delete=False
        )
        f.write(content)
        f.close()
        return f.name

    def tearDown(self):
        """Clean up any temp files."""
        # Test methods store paths in self._cleanup if needed.
        for path in getattr(self, "_cleanup", []):
            if os.path.exists(path):
                os.unlink(path)

    def test_convert_with_mock_handler(self):
        """Converter delegates to the correct handler."""
        reg = HandlerRegistry()
        handler = _MockHandler(
            exts=[".mock"], content="hello world"
        )
        reg.register(handler)

        converter = DocumentConverter(registry=reg)
        path = self._make_file(suffix=".mock")
        self._cleanup = [path]

        result = converter.convert(path)
        self.assertEqual(result.content, "hello world")
        self.assertEqual(result.handler_name, "Mock")

    def test_convert_unsupported_format(self):
        """Raises UnsupportedFormatError for unknown formats."""
        reg = HandlerRegistry()
        converter = DocumentConverter(registry=reg)
        path = self._make_file(suffix=".xyz")
        self._cleanup = [path]

        with self.assertRaises(UnsupportedFormatError):
            converter.convert(path)

    def test_convert_bytes(self):
        """convert_bytes writes to temp file and converts."""
        reg = HandlerRegistry()
        handler = _MockHandler(
            exts=[".txt"], content="from bytes"
        )
        reg.register(handler)

        converter = DocumentConverter(registry=reg)
        result = converter.convert_bytes(
            b"data", "test.txt"
        )
        self.assertEqual(result.content, "from bytes")
        self.assertEqual(result.source_path, "<bytes>")

    def test_convert_bytes_size_limit(self):
        """convert_bytes rejects oversized input."""
        reg = HandlerRegistry()
        converter = DocumentConverter(registry=reg)
        # Create data larger than MAX_STDIN_SIZE.
        with self.assertRaises(ParseError):
            converter.convert_bytes(
                b"x" * (500 * 1024 * 1024 + 1),
                "big.txt",
            )

    def test_output_format_auto(self):
        """Auto format uses handler's native format."""
        reg = HandlerRegistry()
        handler = _MockHandler(exts=[".mock"])
        reg.register(handler)

        converter = DocumentConverter(registry=reg)
        path = self._make_file(suffix=".mock")
        self._cleanup = [path]

        result = converter.convert(
            path, output_format="auto"
        )
        self.assertEqual(result.output_format, "text")

    def test_output_format_markdown_from_text(self):
        """Requesting markdown from text handler works."""
        reg = HandlerRegistry()
        handler = _MockHandler(exts=[".mock"])
        reg.register(handler)

        converter = DocumentConverter(registry=reg)
        path = self._make_file(suffix=".mock")
        self._cleanup = [path]

        result = converter.convert(
            path, output_format="markdown"
        )
        self.assertEqual(result.output_format, "markdown")

    def test_supported_formats(self):
        """supported_formats delegates to registry."""
        reg = HandlerRegistry()
        reg.register(_MockHandler(exts=[".a"]))
        reg.register(_MockHandler(exts=[".b"]))

        converter = DocumentConverter(registry=reg)
        fmts = converter.supported_formats()
        self.assertIn(".a", fmts)
        self.assertIn(".b", fmts)

    def test_handler_status(self):
        """handler_status delegates to registry."""
        reg = HandlerRegistry()
        reg.register(_MockHandler(exts=[".a"], name="A"))
        converter = DocumentConverter(registry=reg)
        status = converter.handler_status()
        self.assertTrue(len(status) >= 1)
        names = [s["name"] for s in status]
        self.assertIn("A", names)

    def test_convert_bytes_path_traversal_sanitized(self):
        """convert_bytes strips path traversal from filename."""
        reg = HandlerRegistry()
        handler = _MockHandler(
            exts=[".txt"], content="safe"
        )
        reg.register(handler)

        converter = DocumentConverter(registry=reg)
        # Attempt path traversal in filename — should be sanitized
        # to just the basename.
        result = converter.convert_bytes(
            b"data", "../../../etc/passwd.txt"
        )
        self.assertEqual(result.content, "safe")

    def test_convert_bytes_empty_basename_sanitized(self):
        """convert_bytes handles empty basename after sanitization."""
        reg = HandlerRegistry()
        handler = _MockHandler(
            exts=[".mock"], content="ok"
        )
        reg.register(handler)

        converter = DocumentConverter(registry=reg)
        # A filename like "../../" would produce an empty basename.
        # The code should fall back to "stdin_input".
        # This will fail at format detection (no extension), which
        # is the correct behavior.
        with self.assertRaises(Exception):
            converter.convert_bytes(b"data", "../../")

    def test_convert_bytes_rejects_shell_metacharacters(self):
        """convert_bytes rejects filenames with shell metacharacters."""
        reg = HandlerRegistry()
        converter = DocumentConverter(registry=reg)
        with self.assertRaises(SecurityError):
            converter.convert_bytes(b"data", "file;rm.txt")

    def test_convert_bytes_custom_source_path(self):
        """convert_bytes respects source_path kwarg."""
        reg = HandlerRegistry()
        handler = _MockHandler(
            exts=[".txt"], content="from url"
        )
        reg.register(handler)

        converter = DocumentConverter(registry=reg)
        result = converter.convert_bytes(
            b"data",
            "doc.txt",
            source_path="https://example.com/doc.txt",
        )
        self.assertEqual(
            result.source_path,
            "https://example.com/doc.txt",
        )

    def test_dependency_missing_error_for_unavailable_handler(self):
        """DependencyMissingError when handlers exist but are unavailable."""

        class _UnavailableHandler(BaseHandler):
            @property
            def extensions(self):
                return [".unavail"]

            @property
            def name(self):
                return "Unavailable"

            def available(self):
                return False

            def parse(self, file_path, **kwargs):
                pass

        reg = HandlerRegistry()
        reg.register(_UnavailableHandler())
        converter = DocumentConverter(registry=reg)
        path = self._make_file(suffix=".unavail")
        self._cleanup = [path]

        with self.assertRaises(DependencyMissingError):
            converter.convert(path)


if __name__ == "__main__":
    unittest.main()
