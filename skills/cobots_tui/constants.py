"""
constants.py - Shared constants for the cobots_tui skill.

Centralizes values that are referenced by multiple modules (modes,
widgets, etc.) to avoid duplication and the maintenance hazard of
keeping multiple copies in sync.
"""

# ---------------------------------------------------------------------------
# Color palette
# ---------------------------------------------------------------------------
# Custom color scheme used throughout the TUI and Rich output.
#
# | Name           | Hex     | Usage                                   |
# |----------------|---------|-----------------------------------------|
# | Warm Charcoal  | #2D2B28 | Background (dark mode)                  |
# | Parchment      | #F5ECD7 | Primary text                            |
# | Cerulean       | #227C9D | Accent 1 — links, cool tones, "done"   |
# | Apricot Cream  | #FFCB77 | Accent 2 — warm highlights              |
# | Grapefruit     | #FE6D73 | Accent 3 — alerts, emphasis             |
# | Dim Parchment  | #8A8478 | Muted text — "abandoned" status         |

WARM_CHARCOAL = "#2D2B28"
PARCHMENT = "#F5ECD7"
CERULEAN = "#227C9D"
APRICOT_CREAM = "#FFCB77"
GRAPEFRUIT = "#FE6D73"
DIM_PARCHMENT = "#8A8478"

# Mapping from task status to Rich/Textual color names.
# Used by rich_mode, summary_bar, and task_table to colorize status badges.
STATUS_COLORS: dict[str, str] = {
    "pending": APRICOT_CREAM,
    "underway": GRAPEFRUIT,
    "done": CERULEAN,
    "abandoned": DIM_PARCHMENT,
}
