"""
activity_feed.py - Compact activity feed for the Overview tab.

Displays the most recent workspace events with relative timestamps,
colored event-type icons, and truncated summaries.
"""

from datetime import datetime, timezone

from tui.widgets.snapshot_widget import SnapshotWidget

from constants import CERULEAN, APRICOT_CREAM, GRAPEFRUIT, DIM_PARCHMENT
from data import StatusSnapshot
from security import sanitize_display_text

# Maximum number of events to display.
MAX_DISPLAY: int = 5

# Mapping from event_type to (symbol, color).
EVENT_ICONS: dict[str, tuple[str, str]] = {
    "task_created": ("+", APRICOT_CREAM),
    "task_updated": ("~", GRAPEFRUIT),
    "report_created": ("◆", CERULEAN),
}


def relative_time(event_ts: str, now_ts: str) -> str:
    """Computes a human-readable relative time string.

    Args:
        event_ts: Event timestamp in "%Y-%m-%d %H:%M:%S" format.
        now_ts: Current snapshot timestamp in "%Y-%m-%d %H:%M:%S" format.

    Returns:
        A string like "2m ago", "1h ago", "3d ago", or the raw date if parsing fails.
    """
    try:
        event_dt = datetime.strptime(event_ts, "%Y-%m-%d %H:%M:%S").replace(
            tzinfo=timezone.utc
        )
        now_dt = datetime.strptime(now_ts, "%Y-%m-%d %H:%M:%S").replace(
            tzinfo=timezone.utc
        )
        delta = now_dt - event_dt
        total_seconds = int(delta.total_seconds())

        if total_seconds < 0:
            return "just now"
        if total_seconds < 60:
            return f"{total_seconds}s ago"
        minutes = total_seconds // 60
        if minutes < 60:
            return f"{minutes}m ago"
        hours = minutes // 60
        if hours < 24:
            return f"{hours}h ago"
        days = hours // 24
        if days < 30:
            return f"{days}d ago"
        return event_ts[:10]
    except (ValueError, TypeError):
        return event_ts[:10] if event_ts else "unknown"


class ActivityFeedWidget(SnapshotWidget):
    """Compact feed of the most recent workspace activity events.

    Spans both grid columns (``column-span: 2``) via TCSS.
    Shows up to ``MAX_DISPLAY`` events with relative timestamps,
    colored type icons, and truncated summaries.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__("[dim]Loading…[/dim]", **kwargs)
        self.border_title = "Recent Activity"
        self.add_class("overview-card")

    def update_from_snapshot(self, snap: StatusSnapshot) -> None:
        """Rebuilds the feed from the current snapshot."""
        self._last_snapshot = snap

        events = snap.activity_timeline[:MAX_DISPLAY]

        if not events:
            self.update("[dim](no recent activity)[/dim]")
            return

        # Prefix: "  rel_time  symbol  " ≈ 15 chars + border ~4
        prefix_width = 19
        available = (
            max(10, self.size.width - prefix_width)
            if self.size.width > 0
            else 45
        )

        lines: list[str] = []
        for event in events:
            symbol, color = EVENT_ICONS.get(
                event.event_type,
                ("·", DIM_PARCHMENT),
            )
            rel = relative_time(event.timestamp, snap.snapshot_timestamp)
            summary = sanitize_display_text(event.summary)[:available]
            lines.append(
                f"  [{DIM_PARCHMENT}]{rel:>8}[/{DIM_PARCHMENT}]  "
                f"[{color}]{symbol}[/{color}]  "
                f"{summary}"
            )

        self.update("\n".join(lines))
