"""
ppt_handler.py - Legacy .ppt format handler.

Requires LibreOffice headless to convert ``.ppt`` → ``.pptx``,
then delegates to MarkItDownHandler.
"""

from __future__ import annotations

import logging
import os
import shutil

from cobots_lib.docparse.constants import (
    LIBREOFFICE_TIMEOUT,
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


class PptHandler(BaseHandler):
    """Handler for legacy ``.ppt`` files (via LibreOffice)."""

    @property
    def extensions(self) -> list[str]:
        return [".ppt"]

    @property
    def name(self) -> str:
        return "Legacy PowerPoint"

    def available(self) -> bool:
        return shutil.which("libreoffice") is not None

    def parse(self, file_path: str, **kwargs) -> ParseResult:
        if not shutil.which("libreoffice"):
            raise DependencyMissingError(
                "Legacy .ppt conversion requires LibreOffice. "
                "Install with: apt install libreoffice"
            )

        abs_path = os.path.abspath(file_path)
        ext = os.path.splitext(file_path)[1].lower()

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
                "pptx",
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
                td_name, f"{basename}.pptx"
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
