"""
rst_handler.py - reStructuredText format handler.

Reads the file as-is and wraps it in a fenced code block.
RST is already structured text — this preserves readability.
"""

from __future__ import annotations

import logging
import os

from cobots_lib.docparse.handlers.base import BaseHandler
from cobots_lib.docparse.result import ParseResult
from cobots_lib.docparse.constants import MAX_OUTPUT_SIZE
from cobots_lib.docparse.utils import read_text

_log = logging.getLogger(__name__)


class RstHandler(BaseHandler):
    """Handler for ``.rst`` files."""

    @property
    def extensions(self) -> list[str]:
        return [".rst"]

    @property
    def name(self) -> str:
        return "reStructuredText"

    def parse(self, file_path: str, **kwargs) -> ParseResult:
        encoding = kwargs.get("encoding")
        content = read_text(file_path, encoding)
        wrapped = f"```rst\n{content}\n```"

        # Enforce output size limit.
        if len(wrapped) > MAX_OUTPUT_SIZE:
            wrapped = wrapped[:MAX_OUTPUT_SIZE]

        ext = os.path.splitext(file_path)[1].lower()
        return ParseResult(
            content=wrapped,
            output_format="markdown",
            source_path=file_path,
            source_format=ext,
            handler_name=self.name,
            metadata={"word_count": len(content.split())},
        )
