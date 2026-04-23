"""
active_tasks_list.py - Compact list of in-flight (non-completed) tasks.

Renders colored status dots next to task short-IDs and truncated titles.
Caps display at ``MAX_DISPLAY`` entries with an overflow message.
"""

from textual.widgets import Static

from constants import (
    DIM_PARCHMENT,
    COMPLETED_STATUSES,
    get_status_color,
)
from data import StatusSnapshot
from security import sanitize_display_text

# Maximum number of active tasks shown before truncating.
MAX_DISPLAY: int = 8


class ActiveTasksList(Static):
    """Compact Rich-text list of active (non-completed) tasks.

    Uses colored ``●`` dots whose color is derived dynamically via
    ``get_status_color()`` — no hardcoded status assumptions.
    """

    _last_snapshot: StatusSnapshot | None = None

    def __init__(self, **kwargs) -> None:
        super().__init__("[dim]Loading…[/dim]", **kwargs)
        self.border_title = "Active Tasks"

    def update_from_snapshot(self, snap: StatusSnapshot) -> None:
        """Rebuilds the list from the current snapshot."""
        self._last_snapshot = snap

        # Filter to active tasks: status NOT in COMPLETED_STATUSES.
        active_tasks = [
            t for t in snap.tasks
            if t.status not in COMPLETED_STATUSES
        ]

        if not active_tasks:
            self.update("[dim](none)[/dim]")
            return

        # Compute available width for title text.
        # Prefix: "  ● shortid  " = ~18 chars + border/padding ~4
        prefix_width = 22
        available = (
            max(10, self.size.width - prefix_width)
            if self.size.width > 0
            else 35
        )

        lines: list[str] = []
        for task in active_tasks[:MAX_DISPLAY]:
            color = get_status_color(task.status)
            dot = f"[{color}]●[/{color}]"
            short_id = sanitize_display_text(task.id[:8])
            title = sanitize_display_text(task.title)[:available]
            lines.append(
                f"  {dot} [{DIM_PARCHMENT}]{short_id}"
                f"[/{DIM_PARCHMENT}]  {title}"
            )

        overflow = len(active_tasks) - MAX_DISPLAY
        if overflow > 0:
            lines.append(
                f"  [{DIM_PARCHMENT}]… and {overflow} more"
                f"[/{DIM_PARCHMENT}]"
            )

        self.update("\n".join(lines))

    def on_resize(self, event) -> None:
        """Re-render on resize to adjust text truncation."""
        if self._last_snapshot is not None:
            self.update_from_snapshot(self._last_snapshot)
