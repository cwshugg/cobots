"""
test_security_findings.py - Tests for security fixes from report 62893d1d8de22f6e.

Covers:
  - Finding 1: Output size limit enforcement in all 9 handlers
  - Finding 2: ODF XML pre-validation with defusedxml
  - Finding 3: EML handler explicit html.parser usage
  - Finding 4: LibreOffice profile MacroSecurityLevel=3
  - Finding 5: Shell metacharacters include < and >
  - Finding 6: Recursion depth limit enforcement
  - Finding 7: Lock file restrictive permissions
  - Finding 8: Security test coverage gaps (addressed here)
"""

import os
import stat
import sys
import tempfile
import unittest
import zipfile
from unittest.mock import MagicMock, patch

# Path setup.
_SKILLS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
if _SKILLS_DIR not in sys.path:
    sys.path.insert(0, _SKILLS_DIR)

from cobots_lib.docparse.constants import (
    MAX_OUTPUT_SIZE,
    RECURSION_DEPTH_LIMIT,
    SHELL_METACHARACTERS,
)
from cobots_lib.docparse.converter import DocumentConverter
from cobots_lib.docparse.errors import ParseError, SecurityError
from cobots_lib.docparse.handlers.base import BaseHandler
from cobots_lib.docparse.registry import HandlerRegistry
from cobots_lib.docparse.result import ParseResult
from cobots_lib.docparse.security import (
    validate_filename_chars,
    validate_odf_xml,
    write_lo_profile_security,
)


# -----------------------------------------------------------------------
# Finding 1: Output size limit enforcement
# -----------------------------------------------------------------------


class TestOutputSizeTruncation(unittest.TestCase):
    """Verify all handlers enforce MAX_OUTPUT_SIZE."""

    def test_rtf_handler_truncates_large_output(self):
        """RTF handler truncates content exceeding MAX_OUTPUT_SIZE."""
        from cobots_lib.docparse.handlers.rtf_handler import (
            RtfHandler,
        )

        handler = RtfHandler()
        oversized = "x" * (MAX_OUTPUT_SIZE + 1000)

        with tempfile.NamedTemporaryFile(
            suffix=".rtf", delete=False, mode="w"
        ) as f:
            # Write minimal RTF wrapping oversized content.
            f.write(r"{\rtf1 " + oversized + "}")
            path = f.name

        try:
            # Mock rtf_to_text to return oversized content.
            with patch(
                "striprtf.striprtf.rtf_to_text",
                return_value=oversized,
            ):
                result = handler.parse(path)
                self.assertLessEqual(
                    len(result.content), MAX_OUTPUT_SIZE
                )
        finally:
            os.unlink(path)

    def test_yaml_handler_truncates_large_output(self):
        """YAML handler truncates content exceeding MAX_OUTPUT_SIZE."""
        from cobots_lib.docparse.handlers.yaml_handler import (
            YamlHandler,
        )

        handler = YamlHandler()

        with tempfile.NamedTemporaryFile(
            suffix=".yaml", delete=False, mode="w"
        ) as f:
            # Write content that, when wrapped, exceeds limit.
            f.write("x" * (MAX_OUTPUT_SIZE + 1000))
            path = f.name

        try:
            result = handler.parse(path)
            self.assertLessEqual(
                len(result.content), MAX_OUTPUT_SIZE
            )
        finally:
            os.unlink(path)

    def test_rst_handler_truncates_large_output(self):
        """RST handler truncates content exceeding MAX_OUTPUT_SIZE."""
        from cobots_lib.docparse.handlers.rst_handler import (
            RstHandler,
        )

        handler = RstHandler()

        with tempfile.NamedTemporaryFile(
            suffix=".rst", delete=False, mode="w"
        ) as f:
            f.write("x" * (MAX_OUTPUT_SIZE + 1000))
            path = f.name

        try:
            result = handler.parse(path)
            self.assertLessEqual(
                len(result.content), MAX_OUTPUT_SIZE
            )
        finally:
            os.unlink(path)

    def test_tex_handler_truncates_large_output(self):
        """TeX handler truncates content exceeding MAX_OUTPUT_SIZE."""
        from cobots_lib.docparse.handlers.tex_handler import (
            TexHandler,
        )

        handler = TexHandler()

        with tempfile.NamedTemporaryFile(
            suffix=".tex", delete=False, mode="w"
        ) as f:
            f.write("x" * (MAX_OUTPUT_SIZE + 1000))
            path = f.name

        try:
            result = handler.parse(path)
            self.assertLessEqual(
                len(result.content), MAX_OUTPUT_SIZE
            )
        finally:
            os.unlink(path)

    def test_eml_handler_truncates_large_output(self):
        """EML handler truncates content exceeding MAX_OUTPUT_SIZE."""
        from cobots_lib.docparse.handlers.eml_handler import (
            EmlHandler,
        )

        handler = EmlHandler()

        # Create an EML with a huge text body.
        big_body = "x" * (MAX_OUTPUT_SIZE + 1000)
        eml_content = (
            "From: a@b.com\r\n"
            "To: c@d.com\r\n"
            "Subject: Big\r\n"
            "Date: Mon, 1 Jan 2024 00:00:00 +0000\r\n"
            "Content-Type: text/plain; charset=utf-8\r\n"
            "\r\n"
            f"{big_body}\r\n"
        )

        with tempfile.NamedTemporaryFile(
            suffix=".eml", delete=False, mode="w"
        ) as f:
            f.write(eml_content)
            path = f.name

        try:
            result = handler.parse(path)
            self.assertLessEqual(
                len(result.content), MAX_OUTPUT_SIZE
            )
        finally:
            os.unlink(path)


# -----------------------------------------------------------------------
# Finding 2: ODF XML pre-validation with defusedxml
# -----------------------------------------------------------------------


class TestOdfXmlPreValidation(unittest.TestCase):
    """Tests for validate_odf_xml()."""

    def test_clean_odf_passes(self):
        """A normal ODF file passes XML pre-validation."""
        with tempfile.TemporaryDirectory() as td:
            odf_path = os.path.join(td, "test.odt")
            with zipfile.ZipFile(odf_path, "w") as zf:
                zf.writestr(
                    "content.xml",
                    '<?xml version="1.0"?><document/>',
                )
                zf.writestr(
                    "styles.xml",
                    '<?xml version="1.0"?><styles/>',
                )
            # Should not raise.
            validate_odf_xml(odf_path)

    def test_billion_laughs_rejected(self):
        """XML bomb (billion laughs) in content.xml is rejected."""
        # Construct a billion-laughs payload.
        bomb = (
            '<?xml version="1.0"?>\n'
            "<!DOCTYPE lolz [\n"
            '  <!ENTITY lol "lol">\n'
            '  <!ENTITY lol2 "&lol;&lol;&lol;&lol;&lol;'
            '&lol;&lol;&lol;&lol;&lol;">\n'
            '  <!ENTITY lol3 "&lol2;&lol2;&lol2;&lol2;&lol2;'
            '&lol2;&lol2;&lol2;&lol2;&lol2;">\n'
            "]>\n"
            "<root>&lol3;</root>"
        )

        with tempfile.TemporaryDirectory() as td:
            odf_path = os.path.join(td, "bomb.odt")
            with zipfile.ZipFile(odf_path, "w") as zf:
                zf.writestr("content.xml", bomb)

            with self.assertRaises(SecurityError) as ctx:
                validate_odf_xml(odf_path)
            self.assertIn(
                "Malicious XML", str(ctx.exception)
            )

    def test_missing_xml_files_ok(self):
        """ODF without content.xml doesn't raise (no XML to validate)."""
        with tempfile.TemporaryDirectory() as td:
            odf_path = os.path.join(td, "minimal.odt")
            with zipfile.ZipFile(odf_path, "w") as zf:
                zf.writestr("mimetype", "application/vnd.oasis.opendocument.text")
            # Should not raise.
            validate_odf_xml(odf_path)

    def test_invalid_zip_raises_parse_error(self):
        """Non-ZIP file raises ParseError."""
        with tempfile.NamedTemporaryFile(
            suffix=".odt", delete=False
        ) as f:
            f.write(b"not a zip")
            path = f.name
        try:
            with self.assertRaises(ParseError):
                validate_odf_xml(path)
        finally:
            os.unlink(path)


# -----------------------------------------------------------------------
# Finding 3: EML handler explicit html.parser
# -----------------------------------------------------------------------


class TestEmlExplicitHtmlParser(unittest.TestCase):
    """Verify EML handler uses explicit html.parser for markdownify."""

    def test_html_body_uses_html_parser(self):
        """HTML email bodies are parsed with html.parser explicitly."""
        from cobots_lib.docparse.handlers.eml_handler import (
            EmlHandler,
        )

        # Create an EML with HTML body.
        eml_content = (
            "From: a@b.com\r\n"
            "To: c@d.com\r\n"
            "Subject: HTML Test\r\n"
            "Date: Mon, 1 Jan 2024 00:00:00 +0000\r\n"
            "Content-Type: text/html; charset=utf-8\r\n"
            "\r\n"
            "<html><body><p>Hello <b>world</b></p></body></html>\r\n"
        )

        with tempfile.NamedTemporaryFile(
            suffix=".eml", delete=False, mode="w"
        ) as f:
            f.write(eml_content)
            path = f.name

        try:
            handler = EmlHandler()

            try:
                from bs4 import BeautifulSoup as OrigBS
            except ImportError:
                self.skipTest("bs4 not available")

            parser_used = []
            original_init = OrigBS.__init__

            def spy_init(self_bs, *args, **kwargs):
                parser_used.append(kwargs.get("features"))
                return original_init(self_bs, *args, **kwargs)

            with patch.object(OrigBS, "__init__", spy_init):
                result = handler.parse(path)

            # Verify html.parser was explicitly specified.
            self.assertTrue(len(parser_used) > 0)
            self.assertEqual(parser_used[0], "html.parser")
            # And the conversion produced output.
            self.assertIn("world", result.content)
        finally:
            os.unlink(path)


# -----------------------------------------------------------------------
# Finding 4: LibreOffice profile MacroSecurityLevel=3
# -----------------------------------------------------------------------


class TestLoProfileSecurity(unittest.TestCase):
    """Tests for write_lo_profile_security()."""

    def test_creates_registry_file(self):
        """write_lo_profile_security creates registrymodifications.xcu."""
        with tempfile.TemporaryDirectory() as td:
            profile_dir = os.path.join(td, "lo-profile")
            os.makedirs(profile_dir)
            write_lo_profile_security(profile_dir)

            xcu_path = os.path.join(
                profile_dir,
                "user",
                "registrymodifications.xcu",
            )
            self.assertTrue(os.path.isfile(xcu_path))

    def test_registry_file_contains_macro_security(self):
        """The XCU file sets MacroSecurityLevel=3."""
        with tempfile.TemporaryDirectory() as td:
            profile_dir = os.path.join(td, "lo-profile")
            os.makedirs(profile_dir)
            write_lo_profile_security(profile_dir)

            xcu_path = os.path.join(
                profile_dir,
                "user",
                "registrymodifications.xcu",
            )
            with open(xcu_path) as f:
                content = f.read()

            self.assertIn("MacroSecurityLevel", content)
            self.assertIn("<value>3</value>", content)

    def test_creates_user_subdir(self):
        """user/ subdirectory is created if missing."""
        with tempfile.TemporaryDirectory() as td:
            profile_dir = os.path.join(td, "lo-profile")
            os.makedirs(profile_dir)
            write_lo_profile_security(profile_dir)

            user_dir = os.path.join(profile_dir, "user")
            self.assertTrue(os.path.isdir(user_dir))

    def test_doc_handler_writes_lo_profile(self):
        """DocHandler._run_libreoffice calls write_lo_profile_security."""
        from cobots_lib.docparse.handlers.doc_handler import (
            DocHandler,
        )

        handler = DocHandler()

        # Track whether write_lo_profile_security is called.
        with patch(
            "cobots_lib.docparse.handlers.doc_handler."
            "write_lo_profile_security"
        ) as mock_write, patch(
            "cobots_lib.docparse.handlers.doc_handler."
            "run_libreoffice_with_lock"
        ) as mock_lo, patch(
            "cobots_lib.docparse.handlers.doc_handler.shutil.which",
            return_value="/usr/bin/libreoffice",
        ):
            mock_lo.return_value = MagicMock(returncode=0)

            # The method will try to find a converted file and
            # delegate to MarkItDown — let it fail after we've
            # confirmed the profile write happens.
            try:
                handler._run_libreoffice(
                    "/tmp/test.doc", "test.doc", ".doc"
                )
            except Exception:
                pass  # Expected — no real output file exists.

            # Verify write_lo_profile_security was called.
            mock_write.assert_called_once()

    def test_ppt_handler_writes_lo_profile(self):
        """PptHandler.parse calls write_lo_profile_security."""
        from cobots_lib.docparse.handlers.ppt_handler import (
            PptHandler,
        )

        with patch(
            "cobots_lib.docparse.handlers.ppt_handler."
            "write_lo_profile_security"
        ) as mock_write, patch(
            "cobots_lib.docparse.handlers.ppt_handler."
            "run_libreoffice_with_lock"
        ) as mock_lo, patch(
            "cobots_lib.docparse.handlers.ppt_handler.shutil.which",
            return_value="/usr/bin/libreoffice",
        ):
            mock_lo.return_value = MagicMock(returncode=0)

            handler = PptHandler()
            try:
                handler.parse("/tmp/test.ppt")
            except Exception:
                pass  # Expected — no real output file.

            mock_write.assert_called_once()

    def test_odf_handler_lo_fallback_writes_profile(self):
        """OdfHandler LO fallback calls write_lo_profile_security."""
        from cobots_lib.docparse.handlers.odf_handler import (
            OdfHandler,
        )

        with patch(
            "cobots_lib.docparse.handlers.odf_handler."
            "write_lo_profile_security"
        ) as mock_write, patch(
            "cobots_lib.docparse.handlers.odf_handler."
            "run_libreoffice_with_lock"
        ) as mock_lo:
            mock_lo.return_value = MagicMock(returncode=0)

            handler = OdfHandler()
            try:
                handler._parse_with_libreoffice(
                    "/tmp/test.odt", ".odt"
                )
            except Exception:
                pass  # Expected — no real output file.

            mock_write.assert_called_once()


# -----------------------------------------------------------------------
# Finding 5: Shell metacharacters include < and >
# -----------------------------------------------------------------------


class TestShellMetacharacters(unittest.TestCase):
    """Verify < and > are in SHELL_METACHARACTERS."""

    def test_less_than_in_set(self):
        self.assertIn("<", SHELL_METACHARACTERS)

    def test_greater_than_in_set(self):
        self.assertIn(">", SHELL_METACHARACTERS)

    def test_less_than_rejected_in_filename(self):
        """Filename with < is rejected."""
        with self.assertRaises(SecurityError):
            validate_filename_chars("/path/file<evil.txt")

    def test_greater_than_rejected_in_filename(self):
        """Filename with > is rejected."""
        with self.assertRaises(SecurityError):
            validate_filename_chars("/path/file>evil.txt")


# -----------------------------------------------------------------------
# Finding 6: Recursion depth limit enforcement
# -----------------------------------------------------------------------


class TestRecursionDepthLimit(unittest.TestCase):
    """Verify RECURSION_DEPTH_LIMIT is enforced in DocumentConverter."""

    def test_depth_zero_ok(self):
        """Depth 0 is within the limit."""
        reg = HandlerRegistry()

        class _MockHandler(BaseHandler):
            @property
            def extensions(self):
                return [".mock"]

            @property
            def name(self):
                return "Mock"

            def parse(self, file_path, **kwargs):
                return ParseResult(
                    content="ok",
                    output_format="text",
                    source_path=file_path,
                    source_format=".mock",
                    handler_name="Mock",
                )

        reg.register(_MockHandler())
        converter = DocumentConverter(registry=reg)

        with tempfile.NamedTemporaryFile(
            suffix=".mock", delete=False
        ) as f:
            f.write(b"test")
            path = f.name

        try:
            result = converter.convert(path, _depth=0)
            self.assertEqual(result.content, "ok")
        finally:
            os.unlink(path)

    def test_depth_one_ok(self):
        """Depth 1 is within the limit (RECURSION_DEPTH_LIMIT=1)."""
        reg = HandlerRegistry()

        class _MockHandler(BaseHandler):
            @property
            def extensions(self):
                return [".mock"]

            @property
            def name(self):
                return "Mock"

            def parse(self, file_path, **kwargs):
                return ParseResult(
                    content="ok",
                    output_format="text",
                    source_path=file_path,
                    source_format=".mock",
                    handler_name="Mock",
                )

        reg.register(_MockHandler())
        converter = DocumentConverter(registry=reg)

        with tempfile.NamedTemporaryFile(
            suffix=".mock", delete=False
        ) as f:
            f.write(b"test")
            path = f.name

        try:
            result = converter.convert(path, _depth=1)
            self.assertEqual(result.content, "ok")
        finally:
            os.unlink(path)

    def test_depth_exceeding_limit_rejected(self):
        """Depth exceeding RECURSION_DEPTH_LIMIT raises SecurityError."""
        reg = HandlerRegistry()

        class _MockHandler(BaseHandler):
            @property
            def extensions(self):
                return [".mock"]

            @property
            def name(self):
                return "Mock"

            def parse(self, file_path, **kwargs):
                return ParseResult(
                    content="ok",
                    output_format="text",
                    source_path=file_path,
                    source_format=".mock",
                    handler_name="Mock",
                )

        reg.register(_MockHandler())
        converter = DocumentConverter(registry=reg)

        with tempfile.NamedTemporaryFile(
            suffix=".mock", delete=False
        ) as f:
            f.write(b"test")
            path = f.name

        try:
            with self.assertRaises(SecurityError) as ctx:
                converter.convert(
                    path, _depth=RECURSION_DEPTH_LIMIT + 1
                )
            self.assertIn(
                "Recursion depth limit", str(ctx.exception)
            )
        finally:
            os.unlink(path)


# -----------------------------------------------------------------------
# Finding 7: Lock file restrictive permissions
# -----------------------------------------------------------------------


class TestLockFilePermissions(unittest.TestCase):
    """Verify LibreOffice lock file gets restrictive permissions."""

    def test_lock_file_created_with_0o600(self):
        """Lock file should be created with owner-only perms."""
        from cobots_lib.docparse.security import (
            run_libreoffice_with_lock,
        )
        from cobots_lib.docparse.constants import (
            LIBREOFFICE_LOCK_FILENAME,
        )

        lock_path = os.path.join(
            tempfile.gettempdir(), LIBREOFFICE_LOCK_FILENAME
        )

        # Clean up any pre-existing lock file.
        if os.path.exists(lock_path):
            os.unlink(lock_path)

        # Mock subprocess.run so we don't actually call LO.
        with patch(
            "cobots_lib.docparse.security.subprocess.run"
        ) as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            run_libreoffice_with_lock(["echo", "test"])

        # Check that the lock file exists with correct perms.
        self.assertTrue(os.path.exists(lock_path))
        file_stat = os.stat(lock_path)
        mode = stat.S_IMODE(file_stat.st_mode)
        self.assertEqual(
            mode, 0o600,
            f"Lock file has mode {oct(mode)}, expected 0o600"
        )

        # Clean up.
        os.unlink(lock_path)


if __name__ == "__main__":
    unittest.main()
