"""
kpi_panel.py - Hero KPI numbers and completion gauge.

Displays three Digits widgets (TASKS, ACTIVE, REPORTS) in a horizontal
row, plus a single-line completion progress bar below them.
"""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Digits, Static

from constants import (
    CERULEAN,
    DIM_PARCHMENT,
    GRAPEFRUIT,
    COMPLETED_STATUSES,
)
from data import StatusSnapshot


class KpiPanel(Widget):
    """Three key-performance-indicator Digits plus a completion gauge bar.

    Spans both grid columns (``column-span: 2``) via TCSS.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.border_title = "Dashboard"

    def compose(self) -> ComposeResult:
        """Yields the KPI row and completion bar."""
        with Horizontal(id="kpi-row"):
            with Vertical(classes="kpi-card"):
                yield Digits("0", id="kpi-total-tasks")
                yield Static("TASKS", classes="kpi-label")
            with Vertical(classes="kpi-card"):
                yield Digits("0", id="kpi-active")
                yield Static("ACTIVE", classes="kpi-label")
            with Vertical(classes="kpi-card"):
                yield Digits("0", id="kpi-reports")
                yield Static("REPORTS", classes="kpi-label")
        yield Static("", id="kpi-completion-bar")

    def update_from_snapshot(self, snap: StatusSnapshot) -> None:
        """Refreshes all KPI values from the current snapshot."""
        counts = snap.status_counts_dict()
        total = len(snap.tasks)

        # Active = total minus completed statuses (dynamic, not hardcoded).
        completed = sum(
            counts.get(s, 0)
            for s in COMPLETED_STATUSES
        )
        active = total - completed

        # "done" count for the completion gauge — conventionally the
        # first status that appears in COMPLETED_STATUSES minus
        # "abandoned".  We use counts.get("done", 0) as a fallback-safe
        # approach, but really we just count anything marked "done".
        done = counts.get("done", 0)
        pct = (done / total * 100) if total > 0 else 0

        # Update Digits widgets.
        try:
            self.query_one("#kpi-total-tasks", Digits).update(str(total))
        except Exception:
            pass
        try:
            active_digits = self.query_one("#kpi-active", Digits)
            active_digits.update(str(active))
            if active > 0:
                active_digits.styles.color = GRAPEFRUIT
                active_digits.styles.text_style = "bold"
            else:
                active_digits.styles.color = None
                active_digits.styles.text_style = ""
        except Exception:
            pass
        try:
            self.query_one("#kpi-reports", Digits).update(
                str(snap.report_count)
            )
        except Exception:
            pass

        # Build the completion gauge bar.
        bar_width = 40
        filled = int((pct / 100) * bar_width)
        empty = bar_width - filled
        text = (
            f"  Completion  [{CERULEAN}]{'━' * filled}[/{CERULEAN}]"
            f"[{DIM_PARCHMENT}]{'━' * empty}[/{DIM_PARCHMENT}]"
            f"  {pct:.0f}%"
        )
        try:
            self.query_one("#kpi-completion-bar", Static).update(text)
        except Exception:
            pass
