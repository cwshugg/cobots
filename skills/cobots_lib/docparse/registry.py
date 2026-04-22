"""
registry.py - HandlerRegistry for the docparse library.

Maps file extensions to handler instances with an explicit priority
system.  Higher priority wins when multiple handlers claim the same
extension.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from cobots_lib.docparse.constants import PRIORITY_DEFAULT

if TYPE_CHECKING:
    from cobots_lib.docparse.handlers.base import BaseHandler

_log = logging.getLogger(__name__)


class HandlerRegistry:
    """Registry mapping file extensions to format handlers.

    Handlers are registered with a priority; the highest-priority
    *available* handler wins on lookup.
    """

    def __init__(self) -> None:
        # Maps extension -> list of (priority, handler), sorted
        # descending by priority.
        self._handlers: dict[
            str, list[tuple[int, BaseHandler]]
        ] = {}

    # -----------------------------------------------------------------
    # Registration
    # -----------------------------------------------------------------

    def register(
        self,
        handler: BaseHandler,
        priority: int = PRIORITY_DEFAULT,
    ) -> None:
        """Register *handler* for all its declared extensions.

        Higher *priority* wins when multiple handlers claim the same
        extension.

        Args:
            handler: A handler instance.
            priority: Priority level (higher wins).
        """
        for ext in handler.extensions:
            ext_lower = ext.lower()
            bucket = self._handlers.setdefault(ext_lower, [])
            bucket.append((priority, handler))
            # Keep sorted by priority descending.
            bucket.sort(key=lambda t: t[0], reverse=True)
            _log.debug(
                "Registered handler %s for %s (priority %d)",
                handler.name,
                ext_lower,
                priority,
            )

    # -----------------------------------------------------------------
    # Lookup
    # -----------------------------------------------------------------

    def get_handler(self, extension: str) -> BaseHandler | None:
        """Return the highest-priority available handler for *extension*.

        The extension is normalised to lowercase before lookup.

        Returns:
            A handler instance, or ``None`` if no available handler.
        """
        ext_lower = extension.lower()
        bucket = self._handlers.get(ext_lower, [])
        for _priority, handler in bucket:
            if handler.available():
                _log.debug(
                    "Resolved %s -> %s", ext_lower, handler.name
                )
                return handler
            _log.debug(
                "Skipping %s for %s (not available)",
                handler.name,
                ext_lower,
            )
        return None

    # -----------------------------------------------------------------
    # Introspection
    # -----------------------------------------------------------------

    def supported_extensions(self) -> list[str]:
        """Return extensions with at least one *available* handler."""
        result: list[str] = []
        for ext in sorted(self._handlers):
            for _priority, handler in self._handlers[ext]:
                if handler.available():
                    result.append(ext)
                    break
        return result

    def all_extensions(self) -> list[str]:
        """Return all registered extensions (including unavailable)."""
        return sorted(self._handlers)

    def handler_status(self) -> list[dict[str, Any]]:
        """Return status info for all registered handlers.

        Returns:
            A list of dicts with keys ``name``, ``extensions``,
            ``available``, and ``priority``.
        """
        seen: dict[int, dict[str, Any]] = {}
        for ext, bucket in self._handlers.items():
            for priority, handler in bucket:
                hid = id(handler)
                if hid not in seen:
                    seen[hid] = {
                        "name": handler.name,
                        "extensions": list(handler.extensions),
                        "available": handler.available(),
                        "priority": priority,
                    }
        # Sort by name for deterministic output.
        return sorted(seen.values(), key=lambda d: d["name"])
