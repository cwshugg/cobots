"""
converter.py - DocumentConverter orchestrator for the docparse library.

Coordinates format detection, handler selection, security validation,
and timeout enforcement.
"""

from __future__ import annotations

import logging
import os
import signal
import threading

from cobots_lib.docparse.constants import (
    DEFAULT_TIMEOUT,
    MAX_STDIN_SIZE,
    RECURSION_DEPTH_LIMIT,
)
from cobots_lib.docparse.detection import detect_format
from cobots_lib.docparse.errors import (
    DependencyMissingError,
    ParseError,
    SecurityError,
    UnsupportedFormatError,
)
from cobots_lib.docparse.registry import HandlerRegistry
from cobots_lib.docparse.result import ParseResult
from cobots_lib.docparse.security import (
    check_file_size,
    secure_temp_dir,
    validate_file_path,
    validate_filename_chars,
)

_log = logging.getLogger(__name__)


class DocumentConverter:
    """Orchestrates document conversion.

    Uses a ``HandlerRegistry`` to look up handlers by format and
    delegates parsing to the matched handler.

    Args:
        registry: A pre-built registry.  If ``None``, the default
            registry is built lazily on first use.
    """

    def __init__(
        self, registry: HandlerRegistry | None = None
    ) -> None:
        if registry is None:
            from cobots_lib.docparse.handlers import (
                build_default_registry,
            )
            registry = build_default_registry()
        self._registry = registry

    # ----------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------

    def convert(self, file_path: str, **kwargs) -> ParseResult:
        """Convert a file to text / Markdown.

        Keyword args:
            output_format: ``"markdown"``, ``"text"``, or ``"auto"``
                (default ``"auto"``).
            encoding: Override input encoding.
            base_dir: Restrict file access to paths within this dir.
            timeout: Per-handler timeout in seconds (default 300).
            include_metadata: Populate PII metadata fields.
            validate: Cross-check extension vs magic bytes.
            max_decompressed_size: Archive size limit in bytes.

        Returns:
            A ``ParseResult``.

        Raises:
            UnsupportedFormatError: No handler for the format.
            DependencyMissingError: Handler deps not installed.
            ParseError: File could not be parsed.
            SecurityError: Security check failed (includes
                file-not-found — see ``validate_file_path``).
        """
        # Separate converter-level kwargs from handler-level kwargs.
        base_dir = kwargs.pop("base_dir", None)
        filename_hint = kwargs.pop("filename_hint", None)
        validate = kwargs.pop("validate", False)
        timeout = kwargs.pop("timeout", DEFAULT_TIMEOUT)
        output_format_req = kwargs.pop("output_format", "auto")
        depth = kwargs.pop("_depth", 0)
        # Remaining kwargs go to the handler (encoding,
        # include_metadata, max_decompressed_size, etc.)

        # Enforce recursion depth limit to prevent unbounded
        # recursive archive processing.
        if depth > RECURSION_DEPTH_LIMIT:
            raise SecurityError(
                f"Recursion depth limit exceeded "
                f"({depth} > {RECURSION_DEPTH_LIMIT})."
            )

        resolved = validate_file_path(file_path, base_dir)

        # File size warnings.
        warnings = check_file_size(resolved)
        for w in warnings:
            _log.warning(w)

        # Detect format.
        ext = detect_format(
            resolved,
            filename_hint=filename_hint,
            validate=validate,
        )
        _log.info("Detected format: %s for %s", ext, resolved)

        # Find handler.
        handler = self._registry.get_handler(ext)
        if handler is None:
            # Distinguish "no handler registered" from "handlers
            # exist but none are available (missing deps)".
            if ext in self._registry.all_extensions():
                raise DependencyMissingError(
                    f"Handlers for '{ext}' exist but none are "
                    f"available (missing dependencies)."
                )
            supported = self._registry.supported_extensions()
            raise UnsupportedFormatError(
                f"No handler for format '{ext}'. "
                f"Supported: {', '.join(supported)}"
            )

        # Execute handler with timeout.
        result = self._run_with_timeout(
            handler, resolved, timeout, **kwargs
        )

        # Propagate file-level warnings.
        result.warnings.extend(warnings)

        # Apply output_format logic.
        result = self._apply_output_format(
            result, output_format_req
        )

        return result

    def convert_bytes(
        self, data: bytes, filename: str, **kwargs
    ) -> ParseResult:
        """Convert in-memory bytes to text / Markdown.

        Creates a secure temporary directory, writes the bytes to a
        file inside it, converts, and cleans up.

        Args:
            data: Raw document bytes.
            filename: Filename hint for format detection.
            **kwargs: Passed through to ``convert()``.
                ``source_path`` (str): Override the ``source_path``
                label in the result (default ``"<bytes>"``).

        Returns:
            A ``ParseResult``.
        """
        if len(data) > MAX_STDIN_SIZE:
            raise ParseError(
                f"Input data exceeds maximum size "
                f"({len(data)} > {MAX_STDIN_SIZE} bytes)."
            )

        # Sanitize filename to prevent path traversal — only keep
        # the basename so "../../../etc/evil" becomes "etc/evil" → ""
        # or just the leaf name.
        safe_name = os.path.basename(filename)
        if not safe_name:
            safe_name = "stdin_input"
        validate_filename_chars(safe_name)

        # Pop source_path before forwarding kwargs to convert().
        source_label = kwargs.pop("source_path", "<bytes>")

        with secure_temp_dir() as td_name:
            temp_file = os.path.join(td_name, safe_name)
            with open(temp_file, "wb") as fh:
                fh.write(data)

            result = self.convert(temp_file, **kwargs)
            result.source_path = source_label
            return result

    def supported_formats(self) -> list[str]:
        """Return extensions with at least one available handler."""
        return self._registry.supported_extensions()

    def handler_status(self) -> list[dict]:
        """Return status info for all registered handlers."""
        return self._registry.handler_status()

    # ----------------------------------------------------------------
    # Internal
    # ----------------------------------------------------------------

    def _run_with_timeout(
        self,
        handler,
        file_path: str,
        timeout: int,
        **kwargs,
    ) -> ParseResult:
        """Execute ``handler.parse()`` with a timeout.

        On Unix, uses ``signal.alarm`` for clean timeout handling.
        Falls back to a thread-based approach elsewhere.
        """
        if hasattr(signal, "SIGALRM") and threading.current_thread() is threading.main_thread():
            return self._run_with_signal_timeout(
                handler, file_path, timeout, **kwargs
            )
        return self._run_with_thread_timeout(
            handler, file_path, timeout, **kwargs
        )

    def _run_with_signal_timeout(
        self,
        handler,
        file_path: str,
        timeout: int,
        **kwargs,
    ) -> ParseResult:
        """Signal-based timeout (Unix main thread only)."""

        def _alarm_handler(signum, frame):
            raise ParseError(
                f"Handler '{handler.name}' timed out "
                f"(>{timeout}s)."
            )

        old_handler = signal.signal(
            signal.SIGALRM, _alarm_handler
        )
        signal.alarm(timeout)
        try:
            return handler.parse(file_path, **kwargs)
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)

    def _run_with_thread_timeout(
        self,
        handler,
        file_path: str,
        timeout: int,
        **kwargs,
    ) -> ParseResult:
        """Thread-based timeout fallback.

        Note: Python threads cannot be forcibly killed.  If the
        handler exceeds the timeout the thread is left running as a
        daemon (so it won't block process exit).  The preferred
        ``signal.alarm``-based timeout (used on Unix main thread)
        does not have this limitation.  The thread-based path exists
        only as a fallback for non-Unix platforms or when called from
        a non-main thread.
        """
        result_holder: list[ParseResult | None] = [None]
        error_holder: list[Exception | None] = [None]

        def _target():
            try:
                result_holder[0] = handler.parse(
                    file_path, **kwargs
                )
            except Exception as exc:
                error_holder[0] = exc

        thread = threading.Thread(target=_target)
        thread.daemon = True
        thread.start()
        thread.join(timeout=timeout)

        if thread.is_alive():
            raise ParseError(
                f"Handler '{handler.name}' timed out "
                f"(>{timeout}s)."
            )
        if error_holder[0] is not None:
            raise error_holder[0]
        if result_holder[0] is None:
            raise ParseError(
                f"Handler '{handler.name}' returned no result."
            )
        return result_holder[0]

    @staticmethod
    def _apply_output_format(
        result: ParseResult,
        requested: str,
    ) -> ParseResult:
        """Apply output-format logic per architecture Section 10.

        * ``"auto"``: use handler's native format.
        * ``"markdown"`` requested but handler produced ``"text"``:
          content is valid Markdown as-is.
        * ``"text"`` requested but handler produced ``"markdown"``:
          keep as-is; ``output_format`` reflects actual format.
        """
        if requested == "auto":
            return result

        if (
            requested == "markdown"
            and result.output_format == "text"
        ):
            # Plain text is valid Markdown; just update the label.
            result.output_format = "markdown"

        # For "text" requested but handler produced "markdown",
        # we keep the actual format — the CLI documents this.

        return result
