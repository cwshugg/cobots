"""
result.py - ParseResult dataclass for the docparse library.

Represents the result of parsing a document, including the extracted
content, output format, source information, optional metadata, and
any non-fatal warnings.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ParseResult:
    """Result of parsing a document.

    Attributes:
        content: The extracted text (Markdown or plain).
        output_format: ``"markdown"`` or ``"text"``.
        source_path: Original file path or ``"<stdin>"``.
        source_format: Detected format extension (e.g. ``".pdf"``).
        handler_name: Which handler produced this result.
        metadata: Optional metadata dict.  Well-known keys:
            ``title``, ``author``, ``page_count``, ``slide_count``,
            ``sheet_names``, ``word_count``, ``subject``, ``date``.
            PII-containing fields (title, author, date, subject) are
            only populated when ``include_metadata=True``.  Currently,
            ``subject`` and ``date`` are populated for ``.eml`` files.
            ``title`` and ``author`` are reserved for future handler
            support.
        warnings: Non-fatal warnings collected during parsing.
    """

    content: str
    output_format: str
    source_path: str
    source_format: str
    handler_name: str
    metadata: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
