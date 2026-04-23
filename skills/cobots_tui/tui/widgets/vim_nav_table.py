"""
vim_nav_table.py - DataTable base class with vim-style navigation.

Provides ``j`` / ``k`` / ``g`` / ``G`` keybindings layered on top of the
standard arrow-key and Home/End navigation built into
:class:`textual.widgets.DataTable`.
"""

from textual.binding import Binding
from textual.widgets import DataTable


class VimNavigableTable(DataTable):
    """DataTable extended with vim-style cursor navigation.

    Additional keybindings (active only when this widget has focus):

    ======== ==========================================
    Key      Action
    ======== ==========================================
    ``j``    Move cursor down  (same as ``↓``)
    ``k``    Move cursor up    (same as ``↑``)
    ``g``    Jump to first row (same as ``Ctrl+Home``)
    ``G``    Jump to last row  (same as ``Ctrl+End``)
    ======== ==========================================

    These are *additive* — arrow keys, Page Up/Down, Home/End all
    continue to work exactly as before.
    """

    BINDINGS = [
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("g", "scroll_top", "First Row", show=False),
        Binding("G", "scroll_bottom", "Last Row", show=False),
    ]
