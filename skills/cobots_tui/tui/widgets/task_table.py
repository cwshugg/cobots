"""
task_table.py - Task DataTable widget for the TUI.

Displays tasks in a sortable DataTable with color-coded status badges.
All cell values are sanitized via :func:`sanitize_display_text`.
"""

from rich.text import Text

from constants import STATUS_COLORS, PARCHMENT
from tui.widgets.vim_nav_table import VimNavigableTable
from data import StatusSnapshot, TaskData
from security import sanitize_display_text


class TaskTable(VimNavigableTable):
    """DataTable displaying workspace tasks."""

    DEFAULT_CSS = """
    TaskTable {
        height: 1fr;
    }
    """

    def on_mount(self) -> None:
        self.cursor_type = "row"
        self.zebra_stripes = True
        self.add_columns("ID", "Status", "Title", "Owner", "Created")

    def update_from_snapshot(self, snapshot: StatusSnapshot) -> None:
        """Clears and repopulates the table from a snapshot.

        Preserves the cursor row position across refreshes.  If the
        previously selected row index exceeds the new row count, the
        cursor is clamped to the last row.
        """
        saved_row = self.cursor_coordinate.row if self.row_count > 0 else 0
        self.clear()
        for task in snapshot.tasks:
            color = STATUS_COLORS.get(task.status, PARCHMENT)
            status_text = Text(sanitize_display_text(task.status))
            status_text.stylize(color)
            self.add_row(
                sanitize_display_text(task.id[:10]),
                status_text,
                sanitize_display_text(task.title),
                sanitize_display_text(task.owner or "(unassigned)"),
                sanitize_display_text(task.created_timestamp),
                key=task.id,
            )
        if self.row_count > 0:
            restored = min(saved_row, self.row_count - 1)
            self.move_cursor(row=restored)

    def get_selected_item(self, snapshot: StatusSnapshot) -> TaskData | None:
        """Returns the :class:`TaskData` for the currently highlighted row."""
        if self.row_count == 0:
            return None
        try:
            row_key, _ = self.coordinate_to_cell_key(self.cursor_coordinate)
        except Exception:
            return None
        task_id = str(row_key.value)
        for task in snapshot.tasks:
            if task.id == task_id:
                return task
        return None
