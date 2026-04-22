"""
detection.py - Format detection utilities for the docparse library.

Provides extension-based and magic-byte-based format detection.
"""

from __future__ import annotations

import logging
import os

from cobots_lib.docparse.errors import DetectionError

_log = logging.getLogger(__name__)


def detect_format_by_extension(file_path: str) -> str | None:
    """Detect the format of a file by its extension.

    Args:
        file_path: Path (or filename) to examine.

    Returns:
        The lowercased extension including dot (e.g. ``".pdf"``), or
        ``None`` if the path has no extension.
    """
    _, ext = os.path.splitext(file_path)
    if ext:
        return ext.lower()
    return None


def detect_format_by_magic(file_path: str) -> str | None:
    """Detect the format of a file using magic-byte analysis.

    Lazily imports ``magika`` (a MarkItDown dependency) to avoid
    import-time overhead on the common extension-based path.

    Args:
        file_path: Path to the file.

    Returns:
        The detected extension or ``None``.
    """
    try:
        from magika import Magika  # type: ignore[import-untyped]
    except ImportError:
        _log.debug("magika not available for magic-byte detection")
        return None

    try:
        m = Magika()
        result = m.identify_path(file_path)
        mime = result.output.mime_type
        _log.debug("magika detected MIME type: %s", mime)
        return _MIME_TO_EXT.get(mime)
    except Exception:
        _log.debug("magika detection failed", exc_info=True)
        return None


def detect_format(
    file_path: str,
    filename_hint: str | None = None,
    validate: bool = False,
) -> str:
    """Detect the format of a file.

    Strategy:
      1. Try extension-based detection on *file_path*.
      2. If no extension and *filename_hint* is given, use its
         extension.
      3. Fall back to magic-byte detection.
      4. If *validate* is ``True``, cross-check extension against
         magic detection.

    Args:
        file_path: Path to the file.
        filename_hint: Optional filename hint (e.g. for stdin input).
        validate: When ``True``, verify extension matches content.

    Returns:
        The detected extension (e.g. ``".pdf"``).

    Raises:
        DetectionError: If the format cannot be determined.
    """
    ext = detect_format_by_extension(file_path)

    if ext is None and filename_hint:
        ext = detect_format_by_extension(filename_hint)

    if ext is None:
        ext = detect_format_by_magic(file_path)

    if ext is None:
        raise DetectionError(
            f"Cannot determine format for: {file_path}"
        )

    if validate and os.path.isfile(file_path):
        magic_ext = detect_format_by_magic(file_path)
        if magic_ext and magic_ext != ext:
            _log.warning(
                "Extension %s does not match detected format %s "
                "for %s",
                ext,
                magic_ext,
                file_path,
            )

    return ext


# ---------------------------------------------------------------------------
# MIME → extension mapping (subset relevant to docparse)
# ---------------------------------------------------------------------------

_MIME_TO_EXT: dict[str, str] = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument"
    ".wordprocessingml.document": ".docx",
    "application/msword": ".doc",
    "application/vnd.openxmlformats-officedocument"
    ".spreadsheetml.sheet": ".xlsx",
    "application/vnd.ms-excel": ".xls",
    "application/vnd.openxmlformats-officedocument"
    ".presentationml.presentation": ".pptx",
    "application/vnd.ms-powerpoint": ".ppt",
    "text/html": ".html",
    "text/csv": ".csv",
    "application/json": ".json",
    "text/xml": ".xml",
    "application/xml": ".xml",
    "application/epub+zip": ".epub",
    "application/vnd.ms-outlook": ".msg",
    "text/plain": ".txt",
    "text/markdown": ".md",
    "text/x-yaml": ".yaml",
    "application/x-yaml": ".yaml",
    "text/x-rst": ".rst",
    "text/x-tex": ".tex",
    "text/rtf": ".rtf",
    "application/rtf": ".rtf",
    "message/rfc822": ".eml",
    "application/vnd.oasis.opendocument.text": ".odt",
    "application/vnd.oasis.opendocument.spreadsheet": ".ods",
    "application/vnd.oasis.opendocument.presentation": ".odp",
}
