"""
test_odf_handler.py - Tests for the ODF handler.
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

from cobots_lib.docparse.handlers.odf_handler import OdfHandler
from cobots_lib.docparse.errors import DependencyMissingError


class TestOdfHandler(unittest.TestCase):
    """Tests for OdfHandler."""

    def setUp(self):
        self.handler = OdfHandler()

    def test_extensions(self):
        self.assertEqual(
            self.handler.extensions,
            [".odt", ".ods", ".odp"],
        )

    def test_name(self):
        self.assertEqual(self.handler.name, "ODF")

    def test_available_with_odfpy(self):
        """available() returns True when odfpy is importable."""
        with patch.object(
            OdfHandler, "_has_odfpy", return_value=True
        ):
            self.assertTrue(self.handler.available())

    def test_available_with_libreoffice(self):
        """available() returns True when LibreOffice is on PATH."""
        with patch.object(
            OdfHandler, "_has_odfpy", return_value=False
        ):
            with patch.object(
                OdfHandler,
                "_has_libreoffice",
                return_value=True,
            ):
                self.assertTrue(self.handler.available())

    def test_unavailable_when_nothing(self):
        """available() returns False when neither is available."""
        with patch.object(
            OdfHandler, "_has_odfpy", return_value=False
        ):
            with patch.object(
                OdfHandler,
                "_has_libreoffice",
                return_value=False,
            ):
                self.assertFalse(self.handler.available())

    @patch.object(OdfHandler, "_has_odfpy", return_value=False)
    @patch.object(
        OdfHandler, "_has_libreoffice", return_value=False
    )
    def test_parse_raises_when_unavailable(
        self, mock_lo, mock_odfpy
    ):
        """parse() raises DependencyMissingError when nothing
        available."""
        import tempfile
        import zipfile

        with tempfile.TemporaryDirectory() as td:
            # Create a minimal valid ZIP (ODF is ZIP-based).
            odt_path = os.path.join(td, "test.odt")
            with zipfile.ZipFile(odt_path, "w") as zf:
                zf.writestr("content.xml", "<doc/>")

            with self.assertRaises(DependencyMissingError):
                self.handler.parse(odt_path)


if __name__ == "__main__":
    unittest.main()
