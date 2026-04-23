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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._last_snapshot: StatusSnapshot | None = None

    def update_from_snapshot(self, snapshot: StatusSnapshot) -> None:
        """Refreshes the activity log from a new snapshot."""
        self._last_snapshot = snapshot

        if not snapshot.activity_timeline:
            self.update("[dim](no recent activity)[/dim]")
            return

        # Compute available width for the header rule line
        width = max(20, self.size.width - 2) if self.size.width > 0 else 40
        label = " Recent Activity "
        side = (width - len(label)) // 2
        header = f"[bold {DIM_PARCHMENT}]{'━' * side}{label}{'━' * (width - side - len(label))}[/]"

        lines: list[str] = [header]
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

    def on_resize(self, event) -> None:
        """Re-render the header at the new width when the terminal is resized."""
        if self._last_snapshot is not None:
            self.update_from_snapshot(self._last_snapshot)
