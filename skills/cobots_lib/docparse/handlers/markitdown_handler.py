"""
markitdown_handler.py - MarkItDown wrapper handler.

Delegates to Microsoft's MarkItDown library for the majority of
supported formats.  Performs pre-delegation archive validation for
ZIP-based formats.
"""

from __future__ import annotations

import logging
import os

from cobots_lib.docparse.constants import (
    MARKITDOWN_EXTENSIONS,
    MAX_DECOMPRESSED_SIZE,
    MAX_OUTPUT_SIZE,
    ZIP_BASED_EXTENSIONS,
)
from cobots_lib.docparse.errors import ParseError
from cobots_lib.docparse.handlers.base import BaseHandler
from cobots_lib.docparse.result import ParseResult
from cobots_lib.docparse.security import validate_archive

_log = logging.getLogger(__name__)


class MarkItDownHandler(BaseHandler):
    """Wrapper around Microsoft MarkItDown.

    Covers ~80 % of supported formats with Markdown output.
    """

    def __init__(self) -> None:
        self._md = None  # Lazy init

    # ----------------------------------------------------------------
    # BaseHandler interface
    # ----------------------------------------------------------------

    @property
    def extensions(self) -> list[str]:
        return list(MARKITDOWN_EXTENSIONS)

    @property
    def name(self) -> str:
        return "MarkItDown"

    def available(self) -> bool:
        """Return ``True`` if ``markitdown`` is importable."""
        try:
            import markitdown  # noqa: F401
            return True
        except ImportError:
            return False

    def parse(self, file_path: str, **kwargs) -> ParseResult:
        """Parse the file using MarkItDown.

        For ZIP-based formats, validates the archive before
        delegating.
        """
        ext = os.path.splitext(file_path)[1].lower()

        # Pre-delegation archive validation for ZIP-based formats.
        if ext in ZIP_BASED_EXTENSIONS:
            _log.debug(
                "Validating ZIP archive before MarkItDown: %s",
                file_path,
            )
            validate_archive(
                file_path,
                max_size=kwargs.get(
                    "max_decompressed_size",
                    None,
                )
                or MAX_DECOMPRESSED_SIZE,
            )

        md = self._get_markitdown()

        try:
            result = md.convert(file_path)
            content = result.text_content or ""
        except Exception as exc:
            raise ParseError(
                f"MarkItDown failed to convert {os.path.basename(file_path)}",
                detail=f"{type(exc).__name__}: {exc}",
            ) from exc

        # Enforce output size limit.
        if len(content) > MAX_OUTPUT_SIZE:
            content = content[:MAX_OUTPUT_SIZE]

        # Build metadata.
        metadata: dict = {}
        word_count = len(content.split())
        metadata["word_count"] = word_count

        return ParseResult(
            content=content,
            output_format="markdown",
            source_path=file_path,
            source_format=ext,
            handler_name=self.name,
            metadata=metadata,
        )

    # ----------------------------------------------------------------
    # Internal
    # ----------------------------------------------------------------

    def _get_markitdown(self):
        """Lazy-initialise the MarkItDown instance."""
        if self._md is None:
            from markitdown import MarkItDown
            self._md = MarkItDown()
        return self._md
