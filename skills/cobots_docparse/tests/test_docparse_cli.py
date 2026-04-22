"""
test_docparse_cli.py - Unit tests for the docparse CLI.

Follows the same pattern as test_ntfy_cli.py: patches venv activation,
imports the CLI module dynamically, and tests subcommand behaviour.
"""

import argparse
import io
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

# -----------------------------------------------------------------------
# Bootstrap
# -----------------------------------------------------------------------
_SKILLS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
if _SKILLS_DIR not in sys.path:
    sys.path.insert(0, _SKILLS_DIR)

_CLI_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..")
)
if _CLI_DIR not in sys.path:
    sys.path.insert(0, _CLI_DIR)

# Patch venv activation before importing the CLI module.
sys.modules.setdefault("venv", MagicMock())
sys.modules.setdefault("venv.venv", MagicMock())

import importlib

docparse_cli = importlib.import_module("docparse-cli")


FIXTURES_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "..",
    "cobots_lib",
    "docparse",
    "tests",
    "fixtures",
)
FIXTURES_DIR = os.path.normpath(FIXTURES_DIR)


class TestCmdParse(unittest.TestCase):
    """Tests for the ``parse`` subcommand."""

    def _make_args(self, **kwargs):
        """Create a Namespace for the parse subcommand."""
        defaults = {
            "command": "parse",
            "file": os.path.join(FIXTURES_DIR, "sample.txt"),
            "output": None,
            "format": "auto",
            "filename": None,
            "encoding": None,
            "metadata": False,
            "quiet": False,
            "verbose": False,
            "validate": False,
            "timeout": 300,
            "max_size": 500,
            "max_decompressed_size": 1024,
            "base_dir": None,
        }
        defaults.update(kwargs)
        return argparse.Namespace(**defaults)

    def test_parse_text_file(self):
        """Parse a .txt file successfully."""
        args = self._make_args()
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            code = docparse_cli.cmd_parse(args)
        self.assertEqual(code, 0)
        self.assertIn("quick brown fox", out.getvalue())

    def test_parse_yaml_file(self):
        """Parse a .yaml file successfully."""
        args = self._make_args(
            file=os.path.join(FIXTURES_DIR, "sample.yaml")
        )
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            code = docparse_cli.cmd_parse(args)
        self.assertEqual(code, 0)
        self.assertIn("```yaml", out.getvalue())

    def test_parse_with_output_flag(self):
        """--output writes to a file."""
        with tempfile.NamedTemporaryFile(
            suffix=".md", delete=False
        ) as f:
            outpath = f.name
        try:
            args = self._make_args(output=outpath)
            code = docparse_cli.cmd_parse(args)
            self.assertEqual(code, 0)
            with open(outpath) as fh:
                content = fh.read()
            self.assertIn("quick brown fox", content)
        finally:
            os.unlink(outpath)

    def test_parse_with_metadata(self):
        """--metadata prepends a YAML header."""
        args = self._make_args(metadata=True)
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            code = docparse_cli.cmd_parse(args)
        self.assertEqual(code, 0)
        output = out.getvalue()
        self.assertIn("---", output)

    def test_parse_nonexistent_file(self):
        """Nonexistent file returns exit code 1."""
        args = self._make_args(file="/nonexistent/file.txt")
        with patch("sys.stderr", new_callable=io.StringIO):
            code = docparse_cli.cmd_parse(args)
        self.assertEqual(code, 1)

    def test_parse_unsupported_format(self):
        """Unsupported format returns exit code 1."""
        with tempfile.NamedTemporaryFile(
            suffix=".zzz", delete=False
        ) as f:
            f.write(b"test")
            path = f.name
        try:
            args = self._make_args(file=path)
            with patch(
                "sys.stderr", new_callable=io.StringIO
            ):
                code = docparse_cli.cmd_parse(args)
            self.assertEqual(code, 1)
        finally:
            os.unlink(path)

    def test_parse_with_base_dir(self):
        """--base-dir passes through correctly."""
        fixtures = os.path.realpath(FIXTURES_DIR)
        args = self._make_args(
            file=os.path.join(fixtures, "sample.txt"),
            base_dir=fixtures,
        )
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            code = docparse_cli.cmd_parse(args)
        self.assertEqual(code, 0)

    def test_parse_stdin(self):
        """Parsing from stdin (file='-') works."""
        yaml_data = b"key: value\nlist:\n  - one\n"
        args = self._make_args(
            file="-",
            filename="test.yaml",
        )
        mock_buffer = io.BytesIO(yaml_data)
        with patch("sys.stdin") as mock_stdin:
            mock_stdin.buffer = mock_buffer
            with patch(
                "sys.stdout", new_callable=io.StringIO
            ) as out:
                code = docparse_cli.cmd_parse(args)
        self.assertEqual(code, 0)
        self.assertIn("key: value", out.getvalue())

    def test_parse_stdin_size_limit(self):
        """Stdin input exceeding the size limit returns error."""
        args = self._make_args(
            file="-",
            filename="test.txt",
            max_size=1,  # 1 MB limit
        )
        # Create data slightly over 1 MB.
        big_data = b"x" * (1 * 1024 * 1024 + 1)
        mock_buffer = io.BytesIO(big_data)
        with patch("sys.stdin") as mock_stdin:
            mock_stdin.buffer = mock_buffer
            with patch(
                "sys.stderr", new_callable=io.StringIO
            ):
                code = docparse_cli.cmd_parse(args)
        self.assertEqual(code, 1)


class TestCmdFormats(unittest.TestCase):
    """Tests for the ``formats`` subcommand."""

    def test_formats_output(self):
        """formats subcommand prints a table with headers."""
        args = argparse.Namespace(command="formats")
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            code = docparse_cli.cmd_formats(args)
        self.assertEqual(code, 0)
        output = out.getvalue()
        self.assertIn("Extension", output)
        self.assertIn("Handler", output)
        self.assertIn("Available", output)

    def test_formats_one_extension_per_row(self):
        """Each extension gets its own row (no comma-separated groups)."""
        args = argparse.Namespace(command="formats")
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            code = docparse_cli.cmd_formats(args)
        self.assertEqual(code, 0)
        lines = out.getvalue().strip().splitlines()
        # Skip the header and separator lines.
        data_lines = lines[2:]
        for line in data_lines:
            # The extension column (first field) must never contain a comma.
            ext_field = line.split()[0]
            self.assertNotIn(",", ext_field)

    def test_formats_sorted_alphabetically(self):
        """Extensions are sorted alphabetically."""
        args = argparse.Namespace(command="formats")
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            code = docparse_cli.cmd_formats(args)
        self.assertEqual(code, 0)
        lines = out.getvalue().strip().splitlines()
        data_lines = lines[2:]
        extensions = [line.split()[0] for line in data_lines]
        self.assertEqual(extensions, sorted(extensions))


class TestCmdCheckDeps(unittest.TestCase):
    """Tests for the ``check-deps`` subcommand."""

    def test_check_deps_output(self):
        """check-deps subcommand prints dependency status."""
        args = argparse.Namespace(command="check-deps")
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            code = docparse_cli.cmd_check_deps(args)
        self.assertEqual(code, 0)
        output = out.getvalue()
        self.assertIn("Dependency", output)
        self.assertIn("antiword", output)
        self.assertIn("libreoffice", output)


class TestMainEntryPoint(unittest.TestCase):
    """Tests for the main() function."""

    def test_main_parse(self):
        """main() dispatches parse correctly."""
        test_args = [
            "docparse-cli.py",
            "parse",
            os.path.join(FIXTURES_DIR, "sample.txt"),
        ]
        with patch("sys.argv", test_args):
            with patch(
                "sys.stdout", new_callable=io.StringIO
            ):
                code = docparse_cli.main()
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
