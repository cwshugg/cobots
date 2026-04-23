"""
owner_chart.py - Horizontal bar chart of task counts by owner.

Uses the same bar-rendering style as ``status_chart.py`` but cycles
through accent colors for visual differentiation of owners.
"""

from textual.widgets import Static

from constants import (
    CERULEAN,
    APRICOT_CREAM,
    GRAPEFRUIT,
    PARCHMENT,
    DIM_PARCHMENT,
)
from data import StatusSnapshot
from tui.widgets.overview._chart_utils import render_bar, BAR_WIDTH, LABEL_WIDTH

# Maximum number of owners displayed before showing an overflow message.
MAX_DISPLAY: int = 8

# Cycling accent colors for owner bars.
_OWNER_COLORS: tuple[str, ...] = (
    CERULEAN,
    APRICOT_CREAM,
    GRAPEFRUIT,
    PARCHMENT,
)


class OwnerChart(Static):
    """Horizontal bar chart of task counts by owner.

    Sorted descending by count.  Caps at ``MAX_DISPLAY`` owners with
    an overflow message for the remainder.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__("[dim]Loading…[/dim]", **kwargs)
        self.border_title = "By Owner"
        self._last_snapshot: StatusSnapshot | None = None

    def update_from_snapshot(self, snap: StatusSnapshot) -> None:
        """Rebuilds the chart from the current snapshot."""
        self._last_snapshot = snap

        counts = snap.owner_counts_dict()
        if not counts:
            self.update("[dim](no owners)[/dim]")
            return

        # Sort descending by count (most active owner first).
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
        for idx, (owner, count) in enumerate(sorted_items[:MAX_DISPLAY]):
            color = _OWNER_COLORS[idx % len(_OWNER_COLORS)]
            lines.append(render_bar(owner, count, max_val, color, bar_width=dynamic_width))

        overflow = len(sorted_items) - MAX_DISPLAY
        if overflow > 0:
            lines.append(
                f"  [{DIM_PARCHMENT}]… and {overflow} more"
                f"[/{DIM_PARCHMENT}]"
            )

        self.update("\n".join(lines))

    def on_resize(self, event) -> None:
        """Re-render on resize to adjust bar width."""
        if self._last_snapshot is not None:
            self.update_from_snapshot(self._last_snapshot)
