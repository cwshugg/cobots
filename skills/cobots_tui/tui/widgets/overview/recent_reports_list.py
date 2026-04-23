"""
recent_reports_list.py - Compact list of the most recent reports.

Displays the last ``MAX_DISPLAY`` reports with date, author, and a
truncated title.  All text is sanitized before rendering.
"""

from textual.widgets import Static

from constants import CERULEAN, DIM_PARCHMENT
from data import StatusSnapshot
from security import sanitize_display_text

# Maximum number of reports to display.
MAX_DISPLAY: int = 5


class RecentReportsList(Static):
    """Compact Rich-text list of the most recent workspace reports."""

    def __init__(self, **kwargs) -> None:
        super().__init__("[dim]Loading…[/dim]", **kwargs)
        self.border_title = "Recent Reports"
        self._last_snapshot: StatusSnapshot | None = None

    def update_from_snapshot(self, snap: StatusSnapshot) -> None:
        """Rebuilds the list from the current snapshot."""
        self._last_snapshot = snap

        if not snap.reports:
            self.update("[dim](none)[/dim]")
            return

        # Prefix: "  date  (author)  " ≈ 32 chars + border ~4
        prefix_width = 36
        available = (
            max(10, self.size.width - prefix_width)
            if self.size.width > 0
            else 30
        )

        lines: list[str] = []
        for report in snap.reports[:MAX_DISPLAY]:
            date = sanitize_display_text(report.created_timestamp[:10])
            author = sanitize_display_text(report.author.lower() if report.author else "unknown")
            title = sanitize_display_text(report.title)[:available]
            lines.append(
                f"  [{CERULEAN}]{date}[/{CERULEAN}]  "
                f"[{DIM_PARCHMENT}]({author})[/{DIM_PARCHMENT}]  "
                f"{title}"
            )

        self.update("\n".join(lines))

    def on_resize(self, event) -> None:
        """Re-render on resize to adjust text truncation."""
        if self._last_snapshot is not None:
            self.update_from_snapshot(self._last_snapshot)
