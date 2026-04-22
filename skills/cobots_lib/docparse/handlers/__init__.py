"""
handlers/__init__.py - Default registry construction for docparse.

Provides ``build_default_registry()`` which instantiates all built-in
handlers and registers them with appropriate priorities.
"""

from __future__ import annotations

from cobots_lib.docparse.constants import (
    PRIORITY_CUSTOM,
    PRIORITY_DEFAULT,
)
from cobots_lib.docparse.registry import HandlerRegistry


def build_default_registry() -> HandlerRegistry:
    """Instantiate all built-in handlers and register them.

    Returns:
        A fully populated ``HandlerRegistry``.
    """
    registry = HandlerRegistry()

    # Import handlers (inside function to avoid circular imports
    # and to keep import time minimal until actually needed).
    from cobots_lib.docparse.handlers.markitdown_handler import (
        MarkItDownHandler,
    )
    from cobots_lib.docparse.handlers.doc_handler import DocHandler
    from cobots_lib.docparse.handlers.ppt_handler import PptHandler
    from cobots_lib.docparse.handlers.rtf_handler import RtfHandler
    from cobots_lib.docparse.handlers.eml_handler import EmlHandler
    from cobots_lib.docparse.handlers.odf_handler import OdfHandler
    from cobots_lib.docparse.handlers.yaml_handler import (
        YamlHandler,
    )
    from cobots_lib.docparse.handlers.rst_handler import RstHandler
    from cobots_lib.docparse.handlers.tex_handler import TexHandler

    # Register MarkItDown as the broad default (lowest priority).
    registry.register(MarkItDownHandler(), priority=PRIORITY_DEFAULT)

    # Register custom gap-filling handlers (higher priority).
    for handler_cls in [
        DocHandler,
        PptHandler,
        RtfHandler,
        EmlHandler,
        OdfHandler,
        YamlHandler,
        RstHandler,
        TexHandler,
    ]:
        registry.register(handler_cls(), priority=PRIORITY_CUSTOM)

    return registry
