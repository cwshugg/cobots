"""
doc_handler.py - Legacy .doc format handler.

Cascading fallback: antiword → catdoc → LibreOffice headless.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess

from cobots_lib.docparse.constants import (
    LIBREOFFICE_TIMEOUT,
    MAX_OUTPUT_SIZE,
    SUBPROCESS_TIMEOUT,
)
from cobots_lib.docparse.errors import (
    DependencyMissingError,
    ParseError,
)
from cobots_lib.docparse.handlers.base import BaseHandler
from cobots_lib.docparse.result import ParseResult
from cobots_lib.docparse.security import (
    run_libreoffice_with_lock,
    secure_temp_dir,
    write_lo_profile_security,
)

_log = logging.getLogger(__name__)


class DocHandler(BaseHandler):
    """Handler for legacy ``.doc`` files.

    Tries antiword, catdoc, and LibreOffice headless in order.
    """

    @property
    def extensions(self) -> list[str]:
        return [".doc"]

    @property
    def name(self) -> str:
        return "Legacy Word"

    def available(self) -> bool:
        return (
            shutil.which("antiword") is not None
            or shutil.which("catdoc") is not None
            or shutil.which("libreoffice") is not None
        )

    def parse(self, file_path: str, **kwargs) -> ParseResult:
        abs_path = os.path.abspath(file_path)
        ext = os.path.splitext(file_path)[1].lower()

        # Try antiword.
        if shutil.which("antiword"):
            try:
                return self._run_antiword(
                    abs_path, file_path, ext
                )
            except ParseError:
                _log.warning(
                    "antiword failed, trying catdoc"
                )

        # Try catdoc.
        if shutil.which("catdoc"):
            try:
                return self._run_catdoc(
                    abs_path, file_path, ext
                )
            except ParseError:
                _log.warning(
                    "catdoc failed, trying LibreOffice"
                )

        # Try LibreOffice headless.
        if shutil.which("libreoffice"):
            return self._run_libreoffice(
                abs_path, file_path, ext, **kwargs
            )

        raise DependencyMissingError(
            "Legacy .doc conversion requires one of: "
            "antiword (apt install antiword), "
            "catdoc (apt install catdoc), "
            "or LibreOffice (apt install libreoffice)."
        )

    # ----------------------------------------------------------------
    # antiword
    # ----------------------------------------------------------------

    def _run_antiword(
        self, abs_path: str, file_path: str, ext: str
    ) -> ParseResult:
        try:
            result = subprocess.run(
                ["antiword", "--", abs_path],
                capture_output=True,
                timeout=SUBPROCESS_TIMEOUT,
                check=True,
                shell=False,
            )
        except subprocess.TimeoutExpired:
            raise ParseError(
                "antiword timed out.",
                detail=f"timeout={SUBPROCESS_TIMEOUT}s",
            )
        except subprocess.CalledProcessError as exc:
            raise ParseError(
                "antiword failed to convert .doc file.",
                detail=f"returncode={exc.returncode}",
            ) from exc

        content = result.stdout.decode("utf-8", errors="replace")
        if len(content) > MAX_OUTPUT_SIZE:
            content = content[:MAX_OUTPUT_SIZE]

        return ParseResult(
            content=content,
            output_format="text",
            source_path=file_path,
            source_format=ext,
            handler_name=f"{self.name} (antiword)",
            metadata={"word_count": len(content.split())},
        )

    # ----------------------------------------------------------------
    # catdoc
    # ----------------------------------------------------------------

    def _run_catdoc(
        self, abs_path: str, file_path: str, ext: str
    ) -> ParseResult:
        try:
            result = subprocess.run(
                ["catdoc", "--", abs_path],
                capture_output=True,
                timeout=SUBPROCESS_TIMEOUT,
                check=True,
                shell=False,
            )
        except subprocess.TimeoutExpired:
            raise ParseError(
                "catdoc timed out.",
                detail=f"timeout={SUBPROCESS_TIMEOUT}s",
            )
        except subprocess.CalledProcessError as exc:
            raise ParseError(
                "catdoc failed to convert .doc file.",
                detail=f"returncode={exc.returncode}",
            ) from exc

        content = result.stdout.decode("utf-8", errors="replace")
        if len(content) > MAX_OUTPUT_SIZE:
            content = content[:MAX_OUTPUT_SIZE]

        return ParseResult(
            content=content,
            output_format="text",
            source_path=file_path,
            source_format=ext,
            handler_name=f"{self.name} (catdoc)",
            metadata={"word_count": len(content.split())},
        )

    # ----------------------------------------------------------------
    # LibreOffice headless
    # ----------------------------------------------------------------

    def _run_libreoffice(
        self,
        abs_path: str,
        file_path: str,
        ext: str,
        **kwargs,
    ) -> ParseResult:
        with secure_temp_dir() as td_name:
            lo_profile = os.path.join(td_name, "lo-profile")
            os.makedirs(lo_profile, exist_ok=True)
            write_lo_profile_security(lo_profile)

            args = [
                "libreoffice",
                "--headless",
                "--norestore",
                "--nologo",
                "--nodefault",
                "--nofirststartwizard",
                f"-env:UserInstallation=file://{lo_profile}",
                "--convert-to",
                "docx",
                "--outdir",
                td_name,
                abs_path,
            ]

            run_libreoffice_with_lock(
                args, timeout=LIBREOFFICE_TIMEOUT
            )

            basename = os.path.splitext(
                os.path.basename(file_path)
            )[0]
            converted = os.path.join(
                td_name, f"{basename}.docx"
            )
            if not os.path.isfile(converted):
                raise ParseError(
                    "LibreOffice conversion produced no output.",
                    detail=f"Expected: {converted}",
                )

            from cobots_lib.docparse.handlers.markitdown_handler import (
                MarkItDownHandler,
            )

            md_handler = MarkItDownHandler()
            result = md_handler.parse(converted, **kwargs)
            return ParseResult(
                content=result.content,
                output_format=result.output_format,
                source_path=file_path,
                source_format=ext,
                handler_name=f"{self.name} (via LibreOffice)",
                metadata=result.metadata,
                warnings=result.warnings,
            )
