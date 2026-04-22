"""
test_doc_handler.py - Tests for the legacy .doc handler.
"""

import os
import shutil
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

from cobots_lib.docparse.handlers.doc_handler import DocHandler
from cobots_lib.docparse.errors import DependencyMissingError


class TestDocHandler(unittest.TestCase):
    """Tests for DocHandler."""

    def setUp(self):
        self.handler = DocHandler()

    def test_extensions(self):
        self.assertEqual(self.handler.extensions, [".doc"])

    def test_name(self):
        self.assertEqual(self.handler.name, "Legacy Word")

    def test_available_with_antiword(self):
        """available() is True when antiword is on PATH."""
        with patch("shutil.which") as mock_which:
            mock_which.side_effect = lambda x: (
                "/usr/bin/antiword" if x == "antiword" else None
            )
            self.assertTrue(self.handler.available())

    def test_available_with_catdoc(self):
        """available() is True when catdoc is on PATH."""
        with patch("shutil.which") as mock_which:
            mock_which.side_effect = lambda x: (
                "/usr/bin/catdoc" if x == "catdoc" else None
            )
            self.assertTrue(self.handler.available())

    def test_available_with_libreoffice(self):
        """available() is True when libreoffice is on PATH."""
        with patch("shutil.which") as mock_which:
            mock_which.side_effect = lambda x: (
                "/usr/bin/libreoffice"
                if x == "libreoffice"
                else None
            )
            self.assertTrue(self.handler.available())

    def test_unavailable_when_nothing(self):
        """available() is False when no system tools found."""
        with patch("shutil.which", return_value=None):
            self.assertFalse(self.handler.available())

    @patch("shutil.which", return_value=None)
    def test_parse_raises_when_unavailable(self, mock_which):
        """parse() raises DependencyMissingError when nothing
        available."""
        import tempfile

        with tempfile.NamedTemporaryFile(
            suffix=".doc", delete=False
        ) as f:
            f.write(b"fake doc content")
            path = f.name
        try:
            with self.assertRaises(DependencyMissingError):
                self.handler.parse(path)
        finally:
            os.unlink(path)

    @unittest.skipUnless(
        shutil.which("antiword"),
        "antiword not installed",
    )
    def test_parse_with_antiword_integration(self):
        """Integration: parse a .doc file with antiword."""
        # This test only runs if antiword is installed.
        # We would need a real .doc fixture for this.
        pass


if __name__ == "__main__":
    unittest.main()
