"""
test_registry.py - Unit tests for the HandlerRegistry.
"""

import os
import sys
import unittest

_SKILLS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
if _SKILLS_DIR not in sys.path:
    sys.path.insert(0, _SKILLS_DIR)

from cobots_lib.docparse.constants import (
    PRIORITY_CUSTOM,
    PRIORITY_DEFAULT,
    PRIORITY_PREMIUM,
)
from cobots_lib.docparse.handlers.base import BaseHandler
from cobots_lib.docparse.registry import HandlerRegistry
from cobots_lib.docparse.result import ParseResult


# -----------------------------------------------------------------------
# Stub handlers for testing
# -----------------------------------------------------------------------


class _StubHandler(BaseHandler):
    """Minimal stub handler for registry tests."""

    def __init__(self, exts, name, is_available=True):
        self._exts = exts
        self._name = name
        self._available = is_available

    @property
    def extensions(self):
        return self._exts

    @property
    def name(self):
        return self._name

    def parse(self, file_path, **kwargs):
        return ParseResult(
            content="stub",
            output_format="text",
            source_path=file_path,
            source_format=self._exts[0],
            handler_name=self._name,
        )

    def available(self):
        return self._available


class TestHandlerRegistry(unittest.TestCase):
    """Tests for HandlerRegistry."""

    def test_register_and_lookup(self):
        """A registered handler is returned by get_handler."""
        reg = HandlerRegistry()
        h = _StubHandler([".test"], "Test")
        reg.register(h)
        self.assertIs(reg.get_handler(".test"), h)

    def test_lookup_returns_none_for_unknown(self):
        """get_handler returns None for unregistered extensions."""
        reg = HandlerRegistry()
        self.assertIsNone(reg.get_handler(".unknown"))

    def test_extension_normalization(self):
        """Lookup is case-insensitive."""
        reg = HandlerRegistry()
        h = _StubHandler([".pdf"], "PDF")
        reg.register(h)
        self.assertIs(reg.get_handler(".PDF"), h)
        self.assertIs(reg.get_handler(".Pdf"), h)

    def test_priority_ordering(self):
        """Higher priority handler wins."""
        reg = HandlerRegistry()
        low = _StubHandler([".doc"], "LowPri")
        high = _StubHandler([".doc"], "HighPri")
        reg.register(low, priority=PRIORITY_DEFAULT)
        reg.register(high, priority=PRIORITY_CUSTOM)
        self.assertIs(reg.get_handler(".doc"), high)

    def test_unavailable_handler_skipped(self):
        """Unavailable handlers are skipped in get_handler."""
        reg = HandlerRegistry()
        unavail = _StubHandler(
            [".doc"], "Unavail", is_available=False
        )
        avail = _StubHandler([".doc"], "Avail")
        reg.register(unavail, priority=PRIORITY_PREMIUM)
        reg.register(avail, priority=PRIORITY_DEFAULT)
        self.assertIs(reg.get_handler(".doc"), avail)

    def test_supported_extensions(self):
        """supported_extensions returns only extensions with
        available handlers."""
        reg = HandlerRegistry()
        reg.register(_StubHandler([".a"], "A", is_available=True))
        reg.register(_StubHandler([".b"], "B", is_available=False))
        supported = reg.supported_extensions()
        self.assertIn(".a", supported)
        self.assertNotIn(".b", supported)

    def test_all_extensions(self):
        """all_extensions returns all registered extensions."""
        reg = HandlerRegistry()
        reg.register(_StubHandler([".a"], "A"))
        reg.register(_StubHandler([".b"], "B", is_available=False))
        all_exts = reg.all_extensions()
        self.assertIn(".a", all_exts)
        self.assertIn(".b", all_exts)

    def test_handler_status(self):
        """handler_status returns correct dicts."""
        reg = HandlerRegistry()
        h = _StubHandler([".x", ".y"], "XY")
        reg.register(h, priority=PRIORITY_CUSTOM)
        statuses = reg.handler_status()
        self.assertEqual(len(statuses), 1)
        s = statuses[0]
        self.assertEqual(s["name"], "XY")
        self.assertEqual(s["extensions"], [".x", ".y"])
        self.assertTrue(s["available"])
        self.assertEqual(s["priority"], PRIORITY_CUSTOM)

    def test_multiple_handlers_same_extension(self):
        """Multiple handlers for the same extension are tracked."""
        reg = HandlerRegistry()
        h1 = _StubHandler([".doc"], "H1")
        h2 = _StubHandler([".doc"], "H2")
        reg.register(h1, priority=PRIORITY_DEFAULT)
        reg.register(h2, priority=PRIORITY_CUSTOM)
        # H2 wins (higher priority).
        self.assertIs(reg.get_handler(".doc"), h2)


if __name__ == "__main__":
    unittest.main()
