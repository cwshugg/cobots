"""
activity_log.py - Recent activity timeline widget.

Displays the most recent workspace activity events (newest first) in a
scrollable Static widget.
"""

from textual.widgets import Static

from constants import CERULEAN, APRICOT_CREAM, GRAPEFRUIT, DIM_PARCHMENT
from data import StatusSnapshot
from security import sanitize_display_text

# Mapping from event_type to display label and color.
EVENT_STYLES: dict[str, tuple[str, str]] = {
    "task_created": ("TASK+", CERULEAN),
    "task_updated": ("TASK~", APRICOT_CREAM),
    "report_created": ("REPORT+", GRAPEFRUIT),
}


class ActivityLog(Static):
    """Scrollable log of recent workspace activity events."""

    DEFAULT_CSS = """
    ActivityLog {
        height: auto;
        max-height: 15;
        padding: 0 1;
        overflow-y: auto;
    }
    """

    def update_from_snapshot(self, snapshot: StatusSnapshot) -> None:
        """Refreshes the activity log from a new snapshot."""
        if not snapshot.activity_timeline:
            self.update("[dim](no recent activity)[/dim]")
            return

        lines: list[str] = [f"[bold {DIM_PARCHMENT}]━━ Recent Activity ━━[/]"]
        for event in snapshot.activity_timeline:
            label, color = EVENT_STYLES.get(
                event.event_type,
                (sanitize_display_text(event.event_type), "white"),
            )
            lines.append(
                f"  {sanitize_display_text(event.timestamp)}  "
                f"[{color}]{label}[/{color}]  "
                f"{sanitize_display_text(event.summary)}"
            )
        self.update("\n".join(lines))
