"""
report_table.py - Report DataTable widget for the TUI.

Displays reports in a DataTable.  Row selection pushes a
:class:`ReportDetailScreen` for the selected report.
All cell values are sanitized via :func:`sanitize_display_text`.
"""

from textual.widgets import DataTable

from tui.widgets.vim_nav_table import VimNavigableTable
from data import StatusSnapshot, ReportData
from security import sanitize_display_text


class ReportTable(VimNavigableTable):
    """DataTable displaying workspace reports."""

    DEFAULT_CSS = """
    ReportTable {
        height: 1fr;
    }
    """

    def on_mount(self) -> None:
        self.cursor_type = "row"
        self.zebra_stripes = True
        self.add_columns("ID", "Title", "Author", "Created")

    def update_from_snapshot(self, snapshot: StatusSnapshot) -> None:
        """Clears and repopulates the table from a snapshot.

        Preserves the cursor row position across refreshes.  If the
        previously selected row index exceeds the new row count, the
        cursor is clamped to the last row.
        """
        saved_row = self._save_cursor()
        self.clear()
        for report in snapshot.reports:
            self.add_row(
                sanitize_display_text(report.id[:10]),
                sanitize_display_text(report.title),
                sanitize_display_text(report.author),
                sanitize_display_text(report.created_timestamp),
                key=report.id,
            )
        self._restore_cursor(saved_row)

    def get_selected_item(self, snapshot: StatusSnapshot) -> ReportData | None:
        """Returns the :class:`ReportData` for the currently highlighted row."""
        item_id = self._get_selected_id()
        if item_id is None:
            return None
        return next((r for r in snapshot.reports if r.id == item_id), None)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Pushes a detail screen when a report row is selected (Enter)."""
        snapshot = self.app.snapshot
        if snapshot is None:
            return
        report_id = str(event.row_key.value)
        for report in snapshot.reports:
            if report.id == report_id:
                from tui.screens.report_detail_screen import ReportDetailScreen
                self.app.push_screen(
                    ReportDetailScreen(
                        report_path=report.path,
                        report_title=report.title,
                    )
                )
                break
