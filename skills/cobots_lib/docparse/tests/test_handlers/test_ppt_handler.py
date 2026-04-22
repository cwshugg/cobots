"""
test_ppt_handler.py - Tests for the legacy .ppt handler.
"""

import os
import shutil
import sys
import unittest
from unittest.mock import patch

_SKILLS_DIR = os.path.normpath(
    os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "..", ".."
    )
)
if _SKILLS_DIR not in sys.path:
    sys.path.insert(0, _SKILLS_DIR)

from cobots_lib.docparse.handlers.ppt_handler import PptHandler
from cobots_lib.docparse.errors import DependencyMissingError


class TestPptHandler(unittest.TestCase):
    """Tests for PptHandler."""

    def setUp(self):
        self.handler = PptHandler()

    def test_extensions(self):
        self.assertEqual(self.handler.extensions, [".ppt"])

    def test_name(self):
        self.assertEqual(self.handler.name, "Legacy PowerPoint")

    def test_available_with_libreoffice(self):
        with patch(
            "cobots_lib.docparse.handlers"
            ".ppt_handler.shutil.which",
            return_value="/usr/bin/libreoffice",
        ):
            self.assertTrue(self.handler.available())

    def test_unavailable_without_libreoffice(self):
        with patch(
            "cobots_lib.docparse.handlers"
            ".ppt_handler.shutil.which",
            return_value=None,
        ):
            self.assertFalse(self.handler.available())

    @patch(
        "cobots_lib.docparse.handlers"
        ".ppt_handler.shutil.which",
        return_value=None,
    )
    def test_parse_raises_when_unavailable(self, mock_which):
        """parse() raises DependencyMissingError."""
        import tempfile

        with tempfile.NamedTemporaryFile(
            suffix=".ppt", delete=False
        ) as f:
            f.write(b"fake ppt content")
            path = f.name
        try:
            with self.assertRaises(DependencyMissingError):
                self.handler.parse(path)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
