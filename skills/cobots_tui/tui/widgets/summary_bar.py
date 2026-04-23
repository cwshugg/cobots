"""
summary_bar.py - Aggregate statistics bar widget.

Displays task counts by status, total reports, and last refresh time
in a horizontal bar docked near the top of the TUI.
"""

from textual.widgets import Static

from constants import get_status_color
from data import StatusSnapshot
from security import sanitize_display_text


class SummaryBar(Static):
    """Horizontal bar showing aggregate workspace statistics."""

    def update_from_snapshot(self, snapshot: StatusSnapshot) -> None:
        """Refreshes the bar content from a new snapshot."""
        counts = snapshot.status_counts_dict()
        parts: list[str] = []
        for status in sorted(counts.keys()):
            count = counts[status]
            color = get_status_color(status)
            parts.append(
                f"[{color}]{sanitize_display_text(status)}: "
                f"{count}[/{color}]"
            )
        task_summary = "  ".join(parts) if parts else "No tasks"
        text = (
            f"[bold]Tasks:[/bold] {task_summary}  "
            f"[bold]Reports:[/bold] {snapshot.report_count}  "
            f"[dim]Updated: "
            f"{sanitize_display_text(snapshot.snapshot_timestamp)}[/dim]"
        )
        self.update(text)
