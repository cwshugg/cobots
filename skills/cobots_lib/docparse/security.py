"""
security.py - Security utilities for the docparse library.

Provides path validation, archive validation, filename sanitisation,
file-size checking, and a LibreOffice serialisation lock.  All
functions raise `SecurityError` on violations.
"""

from __future__ import annotations

import fcntl
import logging
import os
import subprocess
import tempfile
import zipfile
from typing import List

from cobots_lib.docparse.constants import (
    LARGE_FILE_WARNING_THRESHOLD,
    LIBREOFFICE_LOCK_FILENAME,
    LIBREOFFICE_TIMEOUT,
    MAX_ARCHIVE_ENTRIES,
    MAX_COMPRESSION_RATIO,
    MAX_DECOMPRESSED_SIZE,
    SHELL_METACHARACTERS,
    TEMP_DIR_MODE,
)
from cobots_lib.docparse.errors import ParseError, SecurityError

_log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# LibreOffice profile hardening
# ---------------------------------------------------------------------------

#: Minimal ``registrymodifications.xcu`` that sets
#: ``MacroSecurityLevel=3`` (Very High).  Writing this into a fresh
#: LO profile directory guarantees macros are disabled regardless of
#: the host LibreOffice build's defaults.
_LO_REGISTRY_XCU = """\
<?xml version="1.0" encoding="UTF-8"?>
<oor:items xmlns:oor="http://openoffice.org/2001/registry"
           xmlns:xs="http://www.w3.org/2001/XMLSchema"
           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
 <item oor:path="/org.openoffice.Office.Common/Security/Scripting">
  <prop oor:name="MacroSecurityLevel" oor:op="fuse">
   <value>3</value>
  </prop>
 </item>
</oor:items>"""


def write_lo_profile_security(lo_profile_dir: str) -> None:
    """Write a ``registrymodifications.xcu`` that sets
    ``MacroSecurityLevel=3`` into the given LibreOffice profile
    directory.

    Creates the ``user/`` subdirectory if it does not exist.

    Args:
        lo_profile_dir: The top-level LibreOffice profile directory
            (the path used in ``-env:UserInstallation``).
    """
    user_dir = os.path.join(lo_profile_dir, "user")
    os.makedirs(user_dir, exist_ok=True)
    registry_path = os.path.join(
        user_dir, "registrymodifications.xcu"
    )
    with open(registry_path, "w", encoding="utf-8") as fh:
        fh.write(_LO_REGISTRY_XCU)


# ---------------------------------------------------------------------------
# ODF XML pre-validation
# ---------------------------------------------------------------------------


def validate_odf_xml(archive_path: str) -> None:
    """Pre-validate XML files inside an ODF archive using
    ``defusedxml``.

    ``odfpy`` internally uses Python's ``xml.sax`` parser which is
    susceptible to billion-laughs / XML bomb attacks via internal
    entity expansion.  This function extracts key XML files from the
    ODF ZIP and passes them through ``defusedxml.sax.parseString()``
    as a validation step *before* ``odfpy`` processes them.

    Args:
        archive_path: Path to the ODF file (ZIP archive).

    Raises:
        SecurityError: If defusedxml detects a malicious XML payload.
        ParseError: If the archive cannot be read.
    """
    import xml.sax

    try:
        import defusedxml.sax
    except ImportError:
        _log.warning(
            "defusedxml is not installed — skipping ODF XML "
            "pre-validation.  Install with: pip install defusedxml"
        )
        return

    # Key XML files inside ODF archives that odfpy parses.
    xml_names = ["content.xml", "styles.xml", "meta.xml"]

    try:
        with zipfile.ZipFile(archive_path, "r") as zf:
            namelist = zf.namelist()
            for name in xml_names:
                if name in namelist:
                    xml_data = zf.read(name)
                    try:
                        defusedxml.sax.parseString(
                            xml_data, xml.sax.ContentHandler()
                        )
                    except defusedxml.common.EntitiesForbidden:
                        raise SecurityError(
                            f"Malicious XML detected in ODF entry "
                            f"'{name}': entity expansion forbidden."
                        )
                    except defusedxml.common.DTDForbidden:
                        raise SecurityError(
                            f"Malicious XML detected in ODF entry "
                            f"'{name}': DTD processing forbidden."
                        )
                    except defusedxml.common.ExternalReferenceForbidden:
                        raise SecurityError(
                            f"Malicious XML detected in ODF entry "
                            f"'{name}': external reference forbidden."
                        )
                    except Exception as exc:
                        # Non-security XML parse errors are fine —
                        # odfpy will handle them during actual load.
                        _log.debug(
                            "XML pre-validation parse error in %s "
                            "(non-security): %s",
                            name,
                            exc,
                        )
    except zipfile.BadZipFile:
        raise ParseError(
            "ODF file is not a valid ZIP archive.",
            detail=f"BadZipFile: {archive_path}",
        )
    except SecurityError:
        raise  # Re-raise security errors.
    except Exception as exc:
        raise ParseError(
            "Failed to pre-validate ODF XML content.",
            detail=f"{type(exc).__name__}: {exc}",
        )


# ---------------------------------------------------------------------------
# Path validation
# ---------------------------------------------------------------------------


def validate_file_path(
    file_path: str,
    base_dir: str | None = None,
) -> str:
    """Resolve and validate a file path.

    1. Resolve to absolute path via ``os.path.realpath()`` (follows
       symlinks).
    2. If *base_dir* is set, verify the resolved path is within
       *base_dir*.
    3. Verify the file exists and is a regular file.
    4. Reject filenames containing shell metacharacters.

    Args:
        file_path: The path to validate.
        base_dir: Optional directory the path must reside in.

    Returns:
        The resolved absolute path.

    Raises:
        SecurityError: If any check fails.
    """
    resolved = os.path.realpath(file_path)

    # Check shell metacharacters in the basename.
    validate_filename_chars(resolved)

    if base_dir is not None:
        resolved_base = os.path.realpath(base_dir)
        # Ensure the resolved path starts with base_dir + separator
        # (or equals base_dir exactly, for edge cases).
        if not (
            resolved == resolved_base
            or resolved.startswith(resolved_base + os.sep)
        ):
            raise SecurityError(
                f"Path escapes base directory: {file_path}"
            )

    if not os.path.exists(resolved):
        raise SecurityError(f"File does not exist: {file_path}")

    if not os.path.isfile(resolved):
        raise SecurityError(f"Path is not a regular file: {file_path}")

    return resolved


def validate_filename_chars(file_path: str) -> None:
    """Reject filenames containing shell metacharacters.

    Only the *basename* component is checked.

    Raises:
        SecurityError: If dangerous characters are found.
    """
    basename = os.path.basename(file_path)
    found = SHELL_METACHARACTERS.intersection(basename)
    if found:
        chars = ", ".join(sorted(found))
        raise SecurityError(
            f"Filename contains dangerous characters ({chars}): "
            f"{basename}"
        )


# ---------------------------------------------------------------------------
# Archive validation
# ---------------------------------------------------------------------------


def validate_archive(
    archive_path: str,
    max_size: int = MAX_DECOMPRESSED_SIZE,
    max_ratio: int = MAX_COMPRESSION_RATIO,
    max_entries: int = MAX_ARCHIVE_ENTRIES,
) -> None:
    """Validate a ZIP archive against decompression safety limits.

    Checks total decompressed size, per-entry compression ratio,
    entry count, and path traversal in entry names.

    Args:
        archive_path: Path to the ZIP file.
        max_size: Maximum total decompressed size in bytes.
        max_ratio: Maximum allowed compression ratio per entry.
        max_entries: Maximum number of entries allowed.

    Raises:
        SecurityError: If any safety check fails.
        ParseError: If the file is not a valid ZIP archive.
    """
    try:
        zf = zipfile.ZipFile(archive_path, "r")
    except zipfile.BadZipFile:
        raise ParseError(
            "File is not a valid ZIP archive or is corrupted.",
            detail=f"BadZipFile: {archive_path}",
        )
    except Exception as exc:
        raise ParseError(
            "Failed to open archive for validation.",
            detail=f"{type(exc).__name__}: {exc}",
        )

    with zf:
        entries = zf.infolist()

        # Entry count check.
        if len(entries) > max_entries:
            raise SecurityError(
                f"Archive has too many entries ({len(entries)} > "
                f"{max_entries})."
            )

        total_size = 0
        for info in entries:
            # Path traversal check.
            name = info.filename
            if ".." in name.split("/"):
                raise SecurityError(
                    f"Archive entry contains path traversal: {name}"
                )
            # Normalise and verify containment (defense-in-depth).
            joined = os.path.normpath(
                os.path.join("/safe", name)
            )
            if not joined.startswith("/safe"):
                raise SecurityError(
                    f"Archive entry escapes extraction directory: "
                    f"{name}"
                )

            # Compression ratio check.
            if info.compress_size > 0:
                ratio = info.file_size / info.compress_size
                if ratio > max_ratio:
                    raise SecurityError(
                        f"Archive entry has suspicious compression "
                        f"ratio ({ratio:.0f}:1 > {max_ratio}:1): "
                        f"{name}"
                    )

            # Accumulate total decompressed size.
            total_size += info.file_size
            if total_size > max_size:
                raise SecurityError(
                    f"Archive total decompressed size exceeds limit "
                    f"({total_size} > {max_size} bytes)."
                )


# ---------------------------------------------------------------------------
# File size checking
# ---------------------------------------------------------------------------


def check_file_size(file_path: str) -> list[str]:
    """Return warnings if the file exceeds size thresholds.

    Returns:
        A list of warning strings (empty if the file is small).
    """
    warnings: list[str] = []
    try:
        size = os.path.getsize(file_path)
    except OSError:
        return warnings

    if size > LARGE_FILE_WARNING_THRESHOLD:
        mb = size / (1024 * 1024)
        warnings.append(
            f"Large file ({mb:.1f} MB) — conversion may be slow."
        )
    return warnings


# ---------------------------------------------------------------------------
# LibreOffice serialisation lock
# ---------------------------------------------------------------------------


def run_libreoffice_with_lock(
    args: list[str],
    timeout: int = LIBREOFFICE_TIMEOUT,
) -> subprocess.CompletedProcess:
    """Run a LibreOffice subprocess with a file-based lock.

    LibreOffice headless has single-instance constraints; concurrent
    calls can fail or corrupt output.  This function serialises
    invocations using ``fcntl.flock``.

    Args:
        args: The full command-line argument list (including
            ``"libreoffice"``).
        timeout: Subprocess timeout in seconds.

    Returns:
        The ``CompletedProcess`` result.

    Raises:
        ParseError: On subprocess failure.
    """
    lock_path = os.path.join(
        tempfile.gettempdir(), LIBREOFFICE_LOCK_FILENAME
    )
    # Use os.open() with restrictive permissions (0o600) to avoid
    # creating a world-readable lock file in /tmp.
    fd = os.open(lock_path, os.O_WRONLY | os.O_CREAT, 0o600)
    with os.fdopen(fd, "w") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        try:
            result = subprocess.run(
                args,
                capture_output=True,
                timeout=timeout,
                shell=False,
            )
            if result.returncode != 0:
                stderr = result.stderr.decode(
                    "utf-8", errors="replace"
                )
                raise ParseError(
                    "LibreOffice conversion failed.",
                    detail=f"returncode={result.returncode}, "
                    f"stderr={stderr[:500]}",
                )
            return result
        except subprocess.TimeoutExpired:
            raise ParseError(
                "LibreOffice conversion timed out "
                f"(>{timeout}s)."
            )
        finally:
            fcntl.flock(lock_file, fcntl.LOCK_UN)


class _SecureTempDir:
    """Context manager wrapping a ``TemporaryDirectory`` with
    restrictive permissions.

    Usage::

        with secure_temp_dir() as path:
            ...  # *path* is the directory name string
    """

    def __init__(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        os.chmod(self._td.name, TEMP_DIR_MODE)

    def __enter__(self) -> str:
        return self._td.name

    def __exit__(self, *exc_info) -> None:
        self._td.cleanup()


def secure_temp_dir() -> _SecureTempDir:
    """Create a temporary directory with restrictive permissions.

    Returns a context manager whose ``__enter__`` yields the
    directory path (a ``str``).
    """
    return _SecureTempDir()
