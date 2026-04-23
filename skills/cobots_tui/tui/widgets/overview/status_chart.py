"""
status_chart.py - Horizontal bar chart of task counts by status.

Renders Rich-markup bars (█ filled, ░ empty) for each status found in
the snapshot.  Colors come from ``get_status_color()`` which falls back
to PARCHMENT for unknown/custom statuses.
"""

from textual.widgets import Static

from constants import get_status_color
from data import StatusSnapshot
from tui.widgets.overview._chart_utils import render_bar, BAR_WIDTH, LABEL_WIDTH


class StatusChart(Static):
    """Horizontal bar chart of task counts by status.

    Iterates ALL statuses present in ``snap.task_counts_by_status``,
    sorted descending by count.  Does NOT hardcode a fixed status list.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__("[dim]Loading…[/dim]", **kwargs)
        self.border_title = "Status Breakdown"
        self._last_snapshot: StatusSnapshot | None = None

    def update_from_snapshot(self, snap: StatusSnapshot) -> None:
        """Rebuilds the chart from the current snapshot."""
        self._last_snapshot = snap

        counts = snap.status_counts_dict()
        if not counts:
            self.update("[dim](no tasks)[/dim]")
            return

        # Sort descending by count (most common first).
        sorted_items = sorted(
            counts.items(), key=lambda kv: kv[1], reverse=True
        )
        max_val = sorted_items[0][1] if sorted_items else 1

        dynamic_width = (
            max(10, self.size.width - LABEL_WIDTH - 8)
            if self.size.width > 0
            else BAR_WIDTH
        )

        lines: list[str] = []
        for status, count in sorted_items:
            color = get_status_color(status)
            lines.append(render_bar(status, count, max_val, color, bar_width=dynamic_width))

        self.update("\n".join(lines))

    def on_resize(self, event) -> None:
        """Re-render on resize to adjust bar width."""
        if self._last_snapshot is not None:
            self.update_from_snapshot(self._last_snapshot)
