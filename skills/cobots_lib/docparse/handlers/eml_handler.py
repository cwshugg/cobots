"""
eml_handler.py - EML email format handler.

Uses Python's ``email`` stdlib to parse ``.eml`` files and extracts
headers and body content.  HTML bodies are converted to Markdown via
``markdownify``.
"""

from __future__ import annotations

import email
import email.policy
import logging
import os

from cobots_lib.docparse.constants import MAX_OUTPUT_SIZE
from cobots_lib.docparse.errors import ParseError
from cobots_lib.docparse.handlers.base import BaseHandler
from cobots_lib.docparse.result import ParseResult

_log = logging.getLogger(__name__)


class EmlHandler(BaseHandler):
    """Handler for ``.eml`` files."""

    @property
    def extensions(self) -> list[str]:
        return [".eml"]

    @property
    def name(self) -> str:
        return "EML"

    def available(self) -> bool:
        """Check that ``markdownify`` is importable (needed for HTML
        body conversion).
        """
        try:
            import markdownify  # noqa: F401
            return True
        except ImportError:
            return False

    def parse(self, file_path: str, **kwargs) -> ParseResult:
        try:
            with open(file_path, "rb") as fh:
                msg = email.message_from_binary_file(
                    fh, policy=email.policy.default
                )
        except Exception as exc:
            raise ParseError(
                "Failed to parse EML file.",
                detail=f"{type(exc).__name__}: {exc}",
            ) from exc

        # Extract headers.
        headers = {
            "From": msg.get("From", ""),
            "To": msg.get("To", ""),
            "Date": msg.get("Date", ""),
            "Subject": msg.get("Subject", ""),
        }

        header_block = (
            f"**From:** {headers['From']}\n"
            f"**To:** {headers['To']}\n"
            f"**Date:** {headers['Date']}\n"
            f"**Subject:** {headers['Subject']}\n"
            "\n---\n\n"
        )

        # Extract body.
        body = self._extract_body(msg)

        content = header_block + body

        # Enforce output size limit.
        if len(content) > MAX_OUTPUT_SIZE:
            content = content[:MAX_OUTPUT_SIZE]

        metadata: dict = {
            "word_count": len(content.split()),
        }
        if kwargs.get("include_metadata"):
            metadata["subject"] = headers["Subject"]
            metadata["date"] = headers["Date"]

        ext = os.path.splitext(file_path)[1].lower()
        return ParseResult(
            content=content,
            output_format="markdown",
            source_path=file_path,
            source_format=ext,
            handler_name=self.name,
            metadata=metadata,
        )

    @staticmethod
    def _extract_body(msg: email.message.Message) -> str:
        """Extract the best text body from a MIME message.

        Prefers ``text/plain``; falls back to ``text/html`` converted
        to Markdown via ``markdownify``.
        """
        plain_body = None
        html_body = None

        if msg.is_multipart():
            for part in msg.walk():
                ct = part.get_content_type()
                if ct == "text/plain" and plain_body is None:
                    payload = part.get_content()
                    if isinstance(payload, str):
                        plain_body = payload
                elif ct == "text/html" and html_body is None:
                    payload = part.get_content()
                    if isinstance(payload, str):
                        html_body = payload
        else:
            ct = msg.get_content_type()
            payload = msg.get_content()
            if isinstance(payload, str):
                if ct == "text/plain":
                    plain_body = payload
                elif ct == "text/html":
                    html_body = payload

        if plain_body:
            return plain_body

        if html_body:
            try:
                from bs4 import BeautifulSoup
                from markdownify import MarkdownConverter
                # Explicitly use html.parser (Python stdlib) to
                # prevent lxml-xml from being selected, which could
                # process XML entities (XXE risk).
                soup = BeautifulSoup(
                    html_body, features="html.parser"
                )
                return MarkdownConverter(
                    strip=["img"]
                ).convert_soup(soup)
            except Exception:
                _log.debug(
                    "markdownify conversion failed",
                    exc_info=True,
                )
                return html_body

        return "(no text body)"
