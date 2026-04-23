"""
activity_log.py - Recent activity timeline widget.

Displays the most recent workspace activity events (newest first) in a
scrollable Static widget.
"""

from tui.widgets.snapshot_widget import SnapshotWidget

from constants import CERULEAN, APRICOT_CREAM, GRAPEFRUIT, DIM_PARCHMENT
from data import StatusSnapshot
from security import sanitize_display_text

# Mapping from event_type to display label and color.
EVENT_STYLES: dict[str, tuple[str, str]] = {
    "task_created": ("TASK+", CERULEAN),
    "task_updated": ("TASK~", APRICOT_CREAM),
    "report_created": ("REPORT+", GRAPEFRUIT),
}


class ActivityLog(SnapshotWidget):
    """Scrollable log of recent workspace activity events."""

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
