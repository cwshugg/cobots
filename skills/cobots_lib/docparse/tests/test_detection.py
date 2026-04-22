"""
test_detection.py - Unit tests for format detection utilities.
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

from cobots_lib.docparse.detection import (
    detect_format,
    detect_format_by_extension,
    detect_format_by_magic,
)
from cobots_lib.docparse.errors import DetectionError


class TestDetectFormatByExtension(unittest.TestCase):
    """Tests for extension-based detection."""

    def test_pdf_extension(self):
        self.assertEqual(
            detect_format_by_extension("report.pdf"), ".pdf"
        )

    def test_uppercase_extension(self):
        self.assertEqual(
            detect_format_by_extension("REPORT.PDF"), ".pdf"
        )

    def test_mixed_case(self):
        self.assertEqual(
            detect_format_by_extension("doc.Docx"), ".docx"
        )

    def test_no_extension(self):
        self.assertIsNone(detect_format_by_extension("noext"))

    def test_dot_only(self):
        # os.path.splitext(".hidden") returns (".hidden", "")
        # so there is no extension for hidden/dotfiles.
        result = detect_format_by_extension(".hidden")
        self.assertIsNone(result)

    def test_multiple_dots(self):
        self.assertEqual(
            detect_format_by_extension("file.tar.gz"), ".gz"
        )


class TestDetectFormatByMagic(unittest.TestCase):
    """Tests for magic-byte detection (mocked)."""

    @patch("cobots_lib.docparse.detection.Magika", create=True)
    def test_magic_detection_unavailable(self, mock_magika_cls):
        """Returns None when magika is not importable."""
        # Simulate ImportError by patching the import.
        with patch.dict("sys.modules", {"magika": None}):
            result = detect_format_by_magic("/fake/file.bin")
            self.assertIsNone(result)


class TestDetectFormat(unittest.TestCase):
    """Tests for the combined detect_format function."""

    def test_extension_based(self):
        """Uses extension when available."""
        self.assertEqual(detect_format("report.pdf"), ".pdf")

    def test_filename_hint(self):
        """Falls back to filename_hint when path has no ext."""
        with tempfile.NamedTemporaryFile(
            suffix="", delete=False
        ) as f:
            f.write(b"test")
            tmppath = f.name
        try:
            ext = detect_format(
                tmppath, filename_hint="hint.yaml"
            )
            self.assertEqual(ext, ".yaml")
        finally:
            os.unlink(tmppath)

    def test_raises_detection_error(self):
        """Raises DetectionError when format cannot be determined."""
        with tempfile.NamedTemporaryFile(
            suffix="", delete=False
        ) as f:
            f.write(b"test")
            tmppath = f.name
        try:
            # Mock magic detection to return None so we get a real
            # DetectionError (magika may detect text/plain otherwise).
            with patch(
                "cobots_lib.docparse.detection"
                ".detect_format_by_magic",
                return_value=None,
            ):
                with self.assertRaises(DetectionError):
                    detect_format(tmppath)
        finally:
            os.unlink(tmppath)


if __name__ == "__main__":
    unittest.main()
