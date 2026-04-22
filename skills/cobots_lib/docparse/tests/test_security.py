"""
test_security.py - Unit tests for security utilities.

Tests path validation, archive validation, filename sanitisation,
and file-size checking.
"""

import os
import struct
import sys
import tempfile
import unittest
import zipfile

# Path setup is done by conftest.py; ensure it's loaded when
# running this file directly.
from cobots_lib.docparse.tests.conftest import FIXTURES_DIR  # noqa: F401

from cobots_lib.docparse.errors import ParseError, SecurityError
from cobots_lib.docparse.security import (
    check_file_size,
    validate_archive,
    validate_file_path,
    validate_filename_chars,
)


class TestValidateFilePath(unittest.TestCase):
    """Tests for validate_file_path."""

    def test_valid_file(self):
        """Valid file path is returned resolved."""
        with tempfile.NamedTemporaryFile(
            suffix=".txt", delete=False
        ) as f:
            f.write(b"test")
            path = f.name
        try:
            result = validate_file_path(path)
            self.assertEqual(result, os.path.realpath(path))
        finally:
            os.unlink(path)

    def test_nonexistent_file(self):
        """Raises SecurityError for missing files."""
        with self.assertRaises(SecurityError):
            validate_file_path("/nonexistent/path/file.txt")

    def test_directory_rejected(self):
        """Raises SecurityError for directories."""
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(SecurityError):
                validate_file_path(td)

    def test_base_dir_containment(self):
        """File within base_dir passes validation."""
        with tempfile.TemporaryDirectory() as td:
            filepath = os.path.join(td, "test.txt")
            with open(filepath, "w") as f:
                f.write("test")
            result = validate_file_path(filepath, base_dir=td)
            self.assertTrue(result.startswith(td))

    def test_base_dir_escape_rejected(self):
        """Symlink escaping base_dir is rejected."""
        with tempfile.TemporaryDirectory() as base_dir:
            with tempfile.TemporaryDirectory() as outside:
                # Create a real file outside base_dir.
                outside_file = os.path.join(
                    outside, "secret.txt"
                )
                with open(outside_file, "w") as f:
                    f.write("secret")

                # Create a symlink inside base_dir pointing
                # outside.
                link = os.path.join(base_dir, "link.txt")
                os.symlink(outside_file, link)

                with self.assertRaises(SecurityError):
                    validate_file_path(link, base_dir=base_dir)

    def test_shell_metacharacters_rejected(self):
        """Filenames with shell metacharacters are rejected."""
        with tempfile.TemporaryDirectory() as td:
            # Create a file with a dangerous name.
            bad_name = os.path.join(td, "file;rm.txt")
            with open(bad_name, "w") as f:
                f.write("test")
            with self.assertRaises(SecurityError):
                validate_file_path(bad_name)


class TestValidateFilenameChars(unittest.TestCase):
    """Tests for validate_filename_chars."""

    def test_clean_filename(self):
        """Clean filenames do not raise."""
        validate_filename_chars("/safe/path/file.txt")

    def test_metachar_semicolon(self):
        with self.assertRaises(SecurityError):
            validate_filename_chars("/path/file;rm.txt")

    def test_metachar_pipe(self):
        with self.assertRaises(SecurityError):
            validate_filename_chars("/path/file|cat.txt")

    def test_metachar_dollar(self):
        with self.assertRaises(SecurityError):
            validate_filename_chars("/path/$file.txt")

    def test_metachar_backtick(self):
        with self.assertRaises(SecurityError):
            validate_filename_chars("/path/`file`.txt")


class TestValidateArchive(unittest.TestCase):
    """Tests for validate_archive."""

    def _make_zip(self, td, entries):
        """Create a ZIP file with given entries.

        entries: list of (name, data_bytes)
        """
        zpath = os.path.join(td, "test.zip")
        with zipfile.ZipFile(zpath, "w") as zf:
            for name, data in entries:
                zf.writestr(name, data)
        return zpath

    def test_valid_archive(self):
        """A normal ZIP passes validation."""
        with tempfile.TemporaryDirectory() as td:
            zpath = self._make_zip(
                td, [("file.txt", "hello")]
            )
            # Should not raise.
            validate_archive(zpath)

    def test_path_traversal_rejected(self):
        """Archive with ../etc/passwd entry is rejected."""
        with tempfile.TemporaryDirectory() as td:
            zpath = self._make_zip(
                td, [("../etc/passwd", "root:x:0:0")]
            )
            with self.assertRaises(SecurityError):
                validate_archive(zpath)

    def test_too_many_entries_rejected(self):
        """Archive with too many entries is rejected."""
        with tempfile.TemporaryDirectory() as td:
            entries = [
                (f"file_{i}.txt", "x") for i in range(50)
            ]
            zpath = self._make_zip(td, entries)
            with self.assertRaises(SecurityError):
                validate_archive(zpath, max_entries=10)

    def test_excessive_decompressed_size_rejected(self):
        """Archive exceeding max decompressed size is rejected."""
        with tempfile.TemporaryDirectory() as td:
            # Create a file with 1 MB of data.
            big_data = "A" * (1024 * 1024)
            zpath = self._make_zip(
                td, [("big.txt", big_data)]
            )
            with self.assertRaises(SecurityError):
                validate_archive(
                    zpath, max_size=1000
                )  # 1000 bytes limit

    def test_non_zip_file_raises_parse_error(self):
        """Non-ZIP files raise ParseError, not crash."""
        with tempfile.TemporaryDirectory() as td:
            not_zip = os.path.join(td, "notazip.zip")
            with open(not_zip, "w") as f:
                f.write("This is not a ZIP file.")
            with self.assertRaises(ParseError):
                validate_archive(not_zip)

    def test_high_compression_ratio_rejected(self):
        """Archive entry with suspicious compression ratio is rejected."""
        with tempfile.TemporaryDirectory() as td:
            zpath = os.path.join(td, "bomb.zip")
            # Create a ZIP with highly compressible data (all zeros).
            # At maximum compression, the ratio will be very high.
            data = b"\x00" * (1024 * 1024)  # 1 MB of zeros
            with zipfile.ZipFile(
                zpath, "w", compression=zipfile.ZIP_DEFLATED
            ) as zf:
                zf.writestr("zeros.bin", data)
            # Use a very low max_ratio to trigger the check.
            with self.assertRaises(SecurityError) as ctx:
                validate_archive(zpath, max_ratio=2)
            self.assertIn(
                "compression ratio", str(ctx.exception)
            )


class TestCheckFileSize(unittest.TestCase):
    """Tests for check_file_size."""

    def test_small_file_no_warnings(self):
        """Small files produce no warnings."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"small")
            path = f.name
        try:
            warnings = check_file_size(path)
            self.assertEqual(warnings, [])
        finally:
            os.unlink(path)

    def test_nonexistent_file_no_warnings(self):
        """Missing files produce no warnings (not an error)."""
        warnings = check_file_size("/nonexistent/file")
        self.assertEqual(warnings, [])


if __name__ == "__main__":
    unittest.main()
