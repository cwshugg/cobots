"""
overview_pane.py - Composite container for the Overview tab.

Houses all overview child widgets in a 2-column CSS grid and delegates
snapshot updates to each child via a single ``update_from_snapshot()``
method.
"""

from textual.app import ComposeResult
from textual.css.query import NoMatches
from textual.widget import Widget

from data import StatusSnapshot
from tui.widgets.overview.kpi_panel import KpiPanel
from tui.widgets.overview.status_chart import StatusChart
from tui.widgets.overview.owner_chart import OwnerChart
from tui.widgets.overview.active_tasks_list import ActiveTasksList
from tui.widgets.overview.recent_reports_list import RecentReportsList
from tui.widgets.overview.activity_feed import ActivityFeedWidget


class OverviewPane(Widget):
    """CSS-grid container for the Overview dashboard tab.

    Layout is defined in ``status.tcss`` (2-column grid with
    full-width hero and activity feed rows).
    """

    can_focus = True

    def compose(self) -> ComposeResult:
        """Yields all child overview widgets in grid order."""
        yield KpiPanel()                    # row 1, column-span: 2
        yield StatusChart()                 # row 2, col 1
        yield ActiveTasksList()             # row 2, col 2
        yield OwnerChart()                  # row 3, col 1
        yield RecentReportsList()           # row 3, col 2
        yield ActivityFeedWidget()          # row 4, column-span: 2

    def update_from_snapshot(self, snap: StatusSnapshot) -> None:
        """Delegates update to all child overview widgets.

        Each child is expected to implement ``update_from_snapshot(snap)``.
        Missing children (due to compose errors) are silently skipped.
        """
        _WIDGET_TYPES = [
            KpiPanel,
            StatusChart,
            OwnerChart,
            ActiveTasksList,
            RecentReportsList,
            ActivityFeedWidget,
        ]
        for wtype in _WIDGET_TYPES:
            try:
                self.query_one(wtype).update_from_snapshot(snap)
            except NoMatches:
                pass
