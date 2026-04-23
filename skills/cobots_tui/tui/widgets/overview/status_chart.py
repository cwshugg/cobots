"""
status_chart.py - Horizontal bar chart of task counts by status.

Renders Rich-markup bars (█ filled, ░ empty) for each status found in
the snapshot.  Colors come from ``get_status_color()`` which falls back
to PARCHMENT for unknown/custom statuses.
"""

from textual.widgets import Static

from constants import DIM_PARCHMENT, get_status_color
from data import StatusSnapshot
from security import sanitize_display_text

# Character width of the filled+empty bar area.
BAR_WIDTH: int = 25


def _render_bar(
    label: str, value: int, max_val: int, color: str
) -> str:
    """Returns a single Rich-markup bar line.

    Args:
        label:   Status name (will be sanitized).
        value:   Count for this status.
        max_val: Maximum count across all statuses (for scaling).
        color:   Rich color string for the filled portion.
    """
    filled = int((value / max_val) * BAR_WIDTH) if max_val > 0 else 0
    empty = BAR_WIDTH - filled
    safe_label = sanitize_display_text(label)
    return (
        f"  {safe_label:<12}"
        f"[{color}]{'█' * filled}[/{color}]"
        f"[{DIM_PARCHMENT}]{'░' * empty}[/{DIM_PARCHMENT}]"
        f" {value}"
    )


class StatusChart(Static):
    """Horizontal bar chart of task counts by status.

    Iterates ALL statuses present in ``snap.task_counts_by_status``,
    sorted descending by count.  Does NOT hardcode a fixed status list.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__("[dim]Loading…[/dim]", **kwargs)
        self.border_title = "Status Breakdown"

    def update_from_snapshot(self, snap: StatusSnapshot) -> None:
        """Rebuilds the chart from the current snapshot."""
        counts = snap.status_counts_dict()
        if not counts:
            self.update("[dim](no tasks)[/dim]")
            return

        # Sort descending by count (most common first).
        sorted_items = sorted(
            counts.items(), key=lambda kv: kv[1], reverse=True
        )
        max_val = sorted_items[0][1] if sorted_items else 1

        lines: list[str] = []
        for status, count in sorted_items:
            color = get_status_color(status)
            lines.append(_render_bar(status, count, max_val, color))

        self.update("\n".join(lines))
