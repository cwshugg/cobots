"""
errors.py - Custom exception hierarchy for the docparse library.

All exceptions inherit from `DocparseError` so callers can catch broadly
or specifically.
"""


class DocparseError(Exception):
    """Base exception for all docparse errors."""


class UnsupportedFormatError(DocparseError):
    """No handler registered for the file format."""


class DependencyMissingError(DocparseError):
    """Handler's required dependency is not installed.

    The message should include install instructions so the user knows
    how to resolve the issue.
    """


class ParseError(DocparseError):
    """Handler failed to parse the file.

    Attributes:
        detail: Internal detail for logging (not for untrusted display).
    """

    def __init__(self, message: str, detail: str = ""):
        super().__init__(message)
        self.detail = detail


class DetectionError(DocparseError):
    """File format cannot be determined."""


class SecurityError(DocparseError):
    """Security check failed (zip bomb, path traversal, etc.)."""
