"""
yaml_handler.py - YAML format handler.

Reads raw YAML content and wraps it in a fenced code block.
Does **not** parse the YAML — this eliminates the YAML
deserialisation attack surface entirely.
"""

from __future__ import annotations

import logging
import os

from cobots_lib.docparse.handlers.base import BaseHandler
from cobots_lib.docparse.result import ParseResult
from cobots_lib.docparse.constants import MAX_OUTPUT_SIZE
from cobots_lib.docparse.errors import ParseError
from cobots_lib.docparse.utils import read_text

_log = logging.getLogger(__name__)


class YamlHandler(BaseHandler):
    """Handler for ``.yaml`` / ``.yml`` files.

    Wraps the raw text in a fenced YAML code block.
    """

    @property
    def extensions(self) -> list[str]:
        return [".yaml", ".yml"]

    @property
    def name(self) -> str:
        return "YAML"

    def parse(self, file_path: str, **kwargs) -> ParseResult:
        encoding = kwargs.get("encoding")
        content = read_text(file_path, encoding)
        wrapped = f"```yaml\n{content}\n```"

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
