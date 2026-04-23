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

    # ------------------------------------------------------------------
    # Shared helpers for subclasses (TaskTable / ReportTable)
    # ------------------------------------------------------------------

    def _get_selected_id(self) -> str | None:
        """Returns the row key value of the currently selected row, or None."""
        if self.row_count == 0:
            return None
        try:
            row_key, _ = self.coordinate_to_cell_key(self.cursor_coordinate)
        except Exception:
            return None
        return str(row_key.value)

    def _save_cursor(self) -> int:
        """Returns the current cursor row index."""
        return self.cursor_coordinate.row if self.row_count > 0 else 0

    def _restore_cursor(self, saved_row: int) -> None:
        """Restores cursor to saved position, clamped to current row count."""
        if self.row_count > 0:
            self.move_cursor(row=min(saved_row, self.row_count - 1))
