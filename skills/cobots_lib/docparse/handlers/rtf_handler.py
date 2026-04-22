"""
rtf_handler.py - RTF format handler.

Uses ``striprtf`` to convert RTF content to plain text.
"""

from __future__ import annotations

import logging
import os

from cobots_lib.docparse.constants import MAX_OUTPUT_SIZE
from cobots_lib.docparse.errors import ParseError
from cobots_lib.docparse.handlers.base import BaseHandler
from cobots_lib.docparse.result import ParseResult

_log = logging.getLogger(__name__)


class RtfHandler(BaseHandler):
    """Handler for ``.rtf`` files via ``striprtf``."""

    @property
    def extensions(self) -> list[str]:
        return [".rtf"]

    @property
    def name(self) -> str:
        return "RTF"

    def available(self) -> bool:
        """Return ``True`` if ``striprtf`` is importable."""
        try:
            import striprtf  # noqa: F401
            return True
        except ImportError:
            return False

    def parse(self, file_path: str, **kwargs) -> ParseResult:
        try:
            from striprtf.striprtf import rtf_to_text
        except ImportError:
            raise ParseError(
                "striprtf is required for RTF conversion. "
                "Install with: pip install striprtf"
            )

        encoding = kwargs.get("encoding")

        # Read file bytes and decode.
        try:
            with open(file_path, "rb") as fh:
                raw = fh.read()
        except OSError as exc:
            raise ParseError(
                f"Failed to read RTF file: {exc}",
                detail=str(exc),
            ) from exc

        # Decode.
        text_content: str
        if encoding:
            try:
                text_content = raw.decode(encoding)
            except (UnicodeDecodeError, LookupError):
                _log.warning(
                    "Requested encoding %s failed, falling back",
                    encoding,
                )
                text_content = raw.decode(
                    "utf-8", errors="replace"
                )
        else:
            try:
                text_content = raw.decode("utf-8")
            except UnicodeDecodeError:
                text_content = raw.decode(
                    "utf-8", errors="replace"
                )

        # Convert RTF to plain text.
        try:
            content = rtf_to_text(text_content)
        except Exception as exc:
            raise ParseError(
                "Failed to convert RTF content.",
                detail=f"{type(exc).__name__}: {exc}",
            ) from exc

        # Enforce output size limit.
        if len(content) > MAX_OUTPUT_SIZE:
            content = content[:MAX_OUTPUT_SIZE]

        ext = os.path.splitext(file_path)[1].lower()
        return ParseResult(
            content=content,
            output_format="text",
            source_path=file_path,
            source_format=ext,
            handler_name=self.name,
            metadata={"word_count": len(content.split())},
        )
