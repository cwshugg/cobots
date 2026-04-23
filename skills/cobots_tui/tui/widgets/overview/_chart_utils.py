"""
_chart_utils.py - Shared bar-chart rendering utilities.

Provides a common bar-rendering function and constants used by
both StatusChart and OwnerChart.
"""

from constants import DIM_PARCHMENT
from security import sanitize_display_text

# Character width of the filled+empty bar area.
BAR_WIDTH: int = 25

# Maximum character width for labels before truncation.
LABEL_WIDTH: int = 12


def compute_bar_width(widget_width: int) -> int:
    """Computes dynamic bar width based on widget width."""
    if widget_width > 0:
        return max(10, widget_width - LABEL_WIDTH - 8)
    return BAR_WIDTH


def render_bar(
    label: str, value: int, max_val: int, color: str,
    bar_width: int = BAR_WIDTH,
) -> str:
    """Returns a single Rich-markup bar line.

    Args:
        label:     Name (will be sanitized and truncated).
        value:     Count for this item.
        max_val:   Maximum count across all items (for scaling).
        color:     Rich color string for the filled portion.
        bar_width: Character width of the bar area (default BAR_WIDTH).
    """
    filled = int((value / max_val) * bar_width) if max_val > 0 else 0
    empty = bar_width - filled
    safe_label = sanitize_display_text(label)[:LABEL_WIDTH]
    return (
        f"  {safe_label:<{LABEL_WIDTH}}"
        f"[{color}]{'█' * filled}[/{color}]"
        f"[{DIM_PARCHMENT}]{'░' * empty}[/{DIM_PARCHMENT}]"
        f" {value}"
    )
