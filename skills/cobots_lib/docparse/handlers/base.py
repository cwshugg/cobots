"""
base.py - BaseHandler abstract base class for docparse handlers.

Every format handler must inherit from `BaseHandler` and implement
the abstract members: ``extensions``, ``name``, and ``parse``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from cobots_lib.docparse.result import ParseResult


class BaseHandler(ABC):
    """Abstract base for all document format handlers.

    Implementations **must** follow the security requirements from the
    architecture (Section 3):

    * Subprocess calls: array-form, ``shell=False``, timeouts (3.1)
    * XML parsing: ``defusedxml`` only (3.2)
    * Deserialization: safe loaders only (3.3)
    * Temp files: ``TemporaryDirectory`` with context managers (3.4)
    * Archives: decompression limits and path validation (3.5)
    """

    @property
    @abstractmethod
    def extensions(self) -> list[str]:
        """File extensions this handler supports, lowercase with dot.

        Example: ``[".doc"]``.  The registry normalises lookups to
        lowercase; handlers must register only lowercase extensions.
        """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable handler name for diagnostics."""

    @abstractmethod
    def parse(self, file_path: str, **kwargs) -> ParseResult:
        """Parse the file and return a `ParseResult`."""

    def available(self) -> bool:
        """Return ``True`` if this handler's dependencies are installed.

        The default implementation returns ``True``.  Handlers with
        optional dependencies should override this.
        """
        return True
