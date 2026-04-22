"""
cobots_lib.docparse - Document parsing library for the Cobots Collective.

Provides a unified API for converting documents in a wide range of
formats (PDF, Office, legacy Office, email, markup, data formats) into
readable text (Markdown preferred, plain text fallback).
"""

from cobots_lib.docparse.converter import DocumentConverter
from cobots_lib.docparse.result import ParseResult
from cobots_lib.docparse.errors import (
    DocparseError,
    UnsupportedFormatError,
    DependencyMissingError,
    ParseError,
    DetectionError,
    SecurityError,
)

__all__ = [
    "parse_file",
    "parse_bytes",
    "supported_formats",
    "DocumentConverter",
    "ParseResult",
    "DocparseError",
    "UnsupportedFormatError",
    "DependencyMissingError",
    "ParseError",
    "DetectionError",
    "SecurityError",
]


# Module-level singleton converter (lazy-initialised).
_converter: DocumentConverter | None = None


def _get_converter() -> DocumentConverter:
    """Return the module-level singleton ``DocumentConverter``.

    Lazy-initialised on first call.  Fine for single-threaded CLI
    use.  For multi-threaded library consumers, create your own
    ``DocumentConverter`` instance.
    """
    global _converter
    if _converter is None:
        _converter = DocumentConverter()
    return _converter


def parse_file(file_path: str, **kwargs) -> ParseResult:
    """Parse a file and return the result.

    See ``DocumentConverter.convert()`` for accepted keyword
    arguments.

    Args:
        file_path: Path to the document.
        **kwargs: Forwarded to the converter.

    Returns:
        A ``ParseResult`` with the extracted content.

    Raises:
        UnsupportedFormatError: No handler for the format.
        DependencyMissingError: Handler deps not installed.
        ParseError: File could not be parsed.
        SecurityError: Security check failed (includes
            file-not-found — see ``validate_file_path``).
    """
    return _get_converter().convert(file_path, **kwargs)


def parse_bytes(data: bytes, filename: str, **kwargs) -> ParseResult:
    """Parse in-memory bytes and return the result.

    A temporary file is created in a secure temporary directory
    (mode 0o700), the bytes are written to it, and the file is
    parsed.  The temp directory and all contents are deleted after
    parsing completes, including on exception.

    Args:
        data: The raw document bytes.
        filename: A filename hint for format detection
            (e.g. ``"report.pdf"``).
        **kwargs: Forwarded to the converter.

    Returns:
        A ``ParseResult`` with the extracted content.
    """
    return _get_converter().convert_bytes(data, filename, **kwargs)


def supported_formats() -> list[str]:
    """Return a list of all supported file extensions."""
    return _get_converter().supported_formats()
