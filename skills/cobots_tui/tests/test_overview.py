"""
test_overview.py - Tests for the Overview tab widgets.

Covers unit tests for each overview widget, pure function tests for
``relative_time``, integration tests for the Overview tab in the
TUI, and review-fix verification tests.
"""

import asyncio
import os
import sys
import tempfile
import types
import unittest
from datetime import datetime, timedelta, timezone

# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------
_SKILLS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
if _SKILLS_DIR not in sys.path:
    sys.path.insert(0, _SKILLS_DIR)

_SKILL_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
if _SKILL_DIR not in sys.path:
    sys.path.insert(0, _SKILL_DIR)

from unittest.mock import MagicMock
sys.modules.setdefault("venv", MagicMock())
sys.modules.setdefault("venv.venv", MagicMock())

from data import TaskData, ReportData, ActivityEvent, StatusSnapshot
from tests.helpers import (
    create_mock_workspace,
    write_task_file,
    write_report_file,
    make_snapshot,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_task(
    task_id: str = "aaaa1111",
    title: str = "Test Task",
    status: str = "pending",
    owner: str = "bob",
    created_timestamp: str = "2026-04-22 10:00:00",
) -> TaskData:
    """Creates a minimal TaskData for unit testing."""
    return TaskData(
        id=task_id,
        title=title,
        status=status,
        author="alice",
        owner=owner,
        created_timestamp=created_timestamp,
        linked_tasks=(),
        path="/tmp/fake.task.md",
        relative_path="tasks/fake.task.md",
    )


def _make_report(
    report_id: str = "rrrr0001",
    title: str = "Test Report",
    author: str = "lorey",
    created_timestamp: str = "2026-04-22 11:00:00",
) -> ReportData:
    """Creates a minimal ReportData for unit testing."""
    return ReportData(
        id=report_id,
        title=title,
        author=author,
        created_timestamp=created_timestamp,
        path="/tmp/fake.report.md",
        relative_path="reports/fake.report.md",
    )


def _make_event(
    timestamp: str = "2026-04-22 10:00:00",
    event_type: str = "task_created",
    summary: str = "Something happened",
    entity_id: str = "aaaa1111",
) -> ActivityEvent:
    """Creates a minimal ActivityEvent for unit testing."""
    return ActivityEvent(
        timestamp=timestamp,
        event_type=event_type,
        summary=summary,
        entity_id=entity_id,
    )


def _skip_if_no_textual():
    """Skip test if textual is not installed."""
    try:
        import textual
        return False
    except ImportError:
        return True


# ===================================================================
# Pure function tests — relative_time
# ===================================================================


class TestRelativeTime(unittest.TestCase):
    """Tests for the ``relative_time`` pure function."""

    def test_seconds_ago(self) -> None:
        """Events less than 60 seconds ago show seconds."""
        from tui.widgets.overview.activity_feed import relative_time
        result = relative_time("2026-04-22 12:00:30", "2026-04-22 12:00:45")
        self.assertEqual(result, "15s ago")

    def test_zero_seconds_ago(self) -> None:
        """Exact same timestamp returns '0s ago'."""
        from tui.widgets.overview.activity_feed import relative_time
        result = relative_time("2026-04-22 12:00:00", "2026-04-22 12:00:00")
        self.assertEqual(result, "0s ago")

    def test_minutes_ago(self) -> None:
        """Events 1-59 minutes ago show minutes."""
        from tui.widgets.overview.activity_feed import relative_time
        result = relative_time("2026-04-22 11:30:00", "2026-04-22 12:00:00")
        self.assertEqual(result, "30m ago")

    def test_hours_ago(self) -> None:
        """Events 1-23 hours ago show hours."""
        from tui.widgets.overview.activity_feed import relative_time
        result = relative_time("2026-04-22 09:00:00", "2026-04-22 12:00:00")
        self.assertEqual(result, "3h ago")

    def test_days_ago(self) -> None:
        """Events 1-29 days ago show days."""
        from tui.widgets.overview.activity_feed import relative_time
        result = relative_time("2026-04-19 12:00:00", "2026-04-22 12:00:00")
        self.assertEqual(result, "3d ago")

    def test_30_plus_days_returns_date(self) -> None:
        """Events 30+ days ago return the raw date prefix."""
        from tui.widgets.overview.activity_feed import relative_time
        result = relative_time("2026-03-01 12:00:00", "2026-04-22 12:00:00")
        self.assertEqual(result, "2026-03-01")

    def test_negative_delta_returns_just_now(self) -> None:
        """Future events (negative delta) return 'just now'."""
        from tui.widgets.overview.activity_feed import relative_time
        result = relative_time("2026-04-22 13:00:00", "2026-04-22 12:00:00")
        self.assertEqual(result, "just now")

    def test_invalid_event_timestamp(self) -> None:
        """Malformed event timestamps fall back to date prefix."""
        from tui.widgets.overview.activity_feed import relative_time
        result = relative_time("not-a-date", "2026-04-22 12:00:00")
        self.assertEqual(result, "not-a-date")

    def test_empty_event_timestamp(self) -> None:
        """Empty event timestamp returns 'unknown'."""
        from tui.widgets.overview.activity_feed import relative_time
        result = relative_time("", "2026-04-22 12:00:00")
        self.assertEqual(result, "unknown")

    def test_invalid_now_timestamp(self) -> None:
        """Malformed now_ts falls back to date prefix of event_ts."""
        from tui.widgets.overview.activity_feed import relative_time
        result = relative_time("2026-04-22 12:00:00", "bad-time")
        self.assertEqual(result, "2026-04-22")

    def test_one_minute_boundary(self) -> None:
        """Exactly 60 seconds shows '1m ago', not '60s ago'."""
        from tui.widgets.overview.activity_feed import relative_time
        result = relative_time("2026-04-22 11:59:00", "2026-04-22 12:00:00")
        self.assertEqual(result, "1m ago")

    def test_one_hour_boundary(self) -> None:
        """Exactly 60 minutes shows '1h ago', not '60m ago'."""
        from tui.widgets.overview.activity_feed import relative_time
        result = relative_time("2026-04-22 11:00:00", "2026-04-22 12:00:00")
        self.assertEqual(result, "1h ago")

    def test_one_day_boundary(self) -> None:
        """Exactly 24 hours shows '1d ago', not '24h ago'."""
        from tui.widgets.overview.activity_feed import relative_time
        result = relative_time("2026-04-21 12:00:00", "2026-04-22 12:00:00")
        self.assertEqual(result, "1d ago")


# ===================================================================
# Unit tests — constants helpers
# ===================================================================


class TestGetStatusColor(unittest.TestCase):
    """Tests for the ``get_status_color`` helper in constants.py."""

    def test_known_status_returns_mapped_color(self) -> None:
        """Known statuses return their mapped color."""
        from constants import get_status_color, CERULEAN
        self.assertEqual(get_status_color("done"), CERULEAN)

    def test_unknown_status_returns_parchment(self) -> None:
        """Unknown statuses fall back to PARCHMENT."""
        from constants import get_status_color, PARCHMENT
        self.assertEqual(
            get_status_color("totally-custom-status"),
            PARCHMENT,
        )

    def test_status_colors_covers_all_default_statuses(self) -> None:
        """STATUS_COLORS has an entry for every default status value.

        Review fix #4: verifies that ``STATUS_COLORS`` keys include all
        statuses defined in ``CobotsConfig.DEFAULT_TASK_STATUS_VALUES``.
        """
        from constants import STATUS_COLORS
        from cobots_lib.workspace.config import CobotsConfig
        for status in CobotsConfig.DEFAULT_TASK_STATUS_VALUES:
            self.assertIn(
                status,
                STATUS_COLORS,
                f"STATUS_COLORS is missing default status: {status}",
            )


# ===================================================================
# Widget unit tests (TUI-based, using app.run_test)
# ===================================================================


@unittest.skipIf(_skip_if_no_textual(), "textual not installed")
class TestKpiPanel(unittest.TestCase):
    """Tests for KpiPanel widget rendering."""

    def test_kpi_panel_shows_digits(self) -> None:
        """Digits widgets display correct totals from snapshot."""
        from tui.app import CobotsStatusApp
        from textual.widgets import Digits

        tasks = (
            _make_task(task_id="t1", status="done"),
            _make_task(task_id="t2", status="pending"),
            _make_task(task_id="t3", status="underway"),
        )
        snap = make_snapshot(
            tasks=tasks,
            task_counts_by_status=types.MappingProxyType(
                {"done": 1, "pending": 1, "underway": 1}
            ),
            report_count=7,
            reports=tuple(_make_report(report_id=f"r{i}") for i in range(7)),
        )

        async def _run():
            with tempfile.TemporaryDirectory() as tmp:
                ws = create_mock_workspace(tmp)
                app = CobotsStatusApp(
                    workspace_path=ws, no_refresh=True, activity_count=5,
                )
                async with app.run_test(size=(120, 40)) as pilot:
                    await pilot.pause()
                    from tui.widgets.overview.overview_pane import (
                        OverviewPane,
                    )
                    pane = app.query_one(OverviewPane)
                    pane.update_from_snapshot(snap)
                    await pilot.pause()

                    total = app.query_one("#kpi-total-tasks", Digits)
                    active = app.query_one("#kpi-active", Digits)
                    reports = app.query_one("#kpi-reports", Digits)
                    self.assertEqual(total.value, "3")
                    self.assertEqual(active.value, "2")
                    self.assertEqual(reports.value, "7")

        asyncio.run(_run())

    def test_kpi_panel_zero_tasks(self) -> None:
        """All Digits show '0' when there are no tasks, no crash."""
        from tui.app import CobotsStatusApp
        from textual.widgets import Digits

        snap = make_snapshot()

        async def _run():
            with tempfile.TemporaryDirectory() as tmp:
                ws = create_mock_workspace(tmp)
                app = CobotsStatusApp(
                    workspace_path=ws, no_refresh=True, activity_count=5,
                )
                async with app.run_test(size=(120, 40)) as pilot:
                    await pilot.pause()
                    from tui.widgets.overview.overview_pane import (
                        OverviewPane,
                    )
                    pane = app.query_one(OverviewPane)
                    pane.update_from_snapshot(snap)
                    await pilot.pause()

                    total = app.query_one("#kpi-total-tasks", Digits)
                    active = app.query_one("#kpi-active", Digits)
                    reports = app.query_one("#kpi-reports", Digits)
                    self.assertEqual(total.value, "0")
                    self.assertEqual(active.value, "0")
                    self.assertEqual(reports.value, "0")

        asyncio.run(_run())

    def test_kpi_panel_completion_bar(self) -> None:
        """Gauge shows correct percentage for a mixed snapshot."""
        from tui.app import CobotsStatusApp
        from textual.widgets import Static

        tasks = tuple(
            _make_task(task_id=f"t{i}", status=("done" if i < 6 else "pending"))
            for i in range(10)
        )
        snap = make_snapshot(
            tasks=tasks,
            task_counts_by_status=types.MappingProxyType(
                {"done": 6, "pending": 4}
            ),
        )

        async def _run():
            with tempfile.TemporaryDirectory() as tmp:
                ws = create_mock_workspace(tmp)
                app = CobotsStatusApp(
                    workspace_path=ws, no_refresh=True, activity_count=5,
                )
                async with app.run_test(size=(120, 40)) as pilot:
                    await pilot.pause()
                    from tui.widgets.overview.overview_pane import (
                        OverviewPane,
                    )
                    pane = app.query_one(OverviewPane)
                    pane.update_from_snapshot(snap)
                    await pilot.pause()

                    bar = app.query_one("#kpi-completion-bar", Static)
                    rendered = bar.content
                    self.assertIn("60%", rendered)

        asyncio.run(_run())


@unittest.skipIf(_skip_if_no_textual(), "textual not installed")
class TestStatusChart(unittest.TestCase):
    """Tests for StatusChart widget rendering."""

    def test_status_chart_renders_bars(self) -> None:
        """Each status gets a bar with correct count."""
        from tui.app import CobotsStatusApp
        from tui.widgets.overview.status_chart import StatusChart

        snap = make_snapshot(
            tasks=(
                _make_task(status="done"),
                _make_task(status="pending"),
            ),
            task_counts_by_status=types.MappingProxyType(
                {"done": 5, "pending": 3, "underway": 1}
            ),
        )

        async def _run():
            with tempfile.TemporaryDirectory() as tmp:
                ws = create_mock_workspace(tmp)
                app = CobotsStatusApp(
                    workspace_path=ws, no_refresh=True, activity_count=5,
                )
                async with app.run_test(size=(120, 40)) as pilot:
                    await pilot.pause()
                    chart = app.query_one(StatusChart)
                    chart.update_from_snapshot(snap)
                    await pilot.pause()

                    rendered = chart.content
                    self.assertIn("done", rendered)
                    self.assertIn("pending", rendered)
                    self.assertIn("underway", rendered)
                    self.assertIn("5", rendered)
                    self.assertIn("3", rendered)

        asyncio.run(_run())

    def test_status_chart_empty_snapshot(self) -> None:
        """Shows '(no tasks)' when snapshot has no status counts."""
        from tui.app import CobotsStatusApp
        from tui.widgets.overview.status_chart import StatusChart

        snap = make_snapshot()

        async def _run():
            with tempfile.TemporaryDirectory() as tmp:
                ws = create_mock_workspace(tmp)
                app = CobotsStatusApp(
                    workspace_path=ws, no_refresh=True, activity_count=5,
                )
                async with app.run_test(size=(120, 40)) as pilot:
                    await pilot.pause()
                    chart = app.query_one(StatusChart)
                    chart.update_from_snapshot(snap)
                    await pilot.pause()

                    rendered = chart.content
                    self.assertIn("no tasks", rendered)

        asyncio.run(_run())

    def test_status_chart_single_status(self) -> None:
        """Works correctly with only one status present."""
        from tui.app import CobotsStatusApp
        from tui.widgets.overview.status_chart import StatusChart

        snap = make_snapshot(
            tasks=(_make_task(status="done"),),
            task_counts_by_status=types.MappingProxyType({"done": 1}),
        )

        async def _run():
            with tempfile.TemporaryDirectory() as tmp:
                ws = create_mock_workspace(tmp)
                app = CobotsStatusApp(
                    workspace_path=ws, no_refresh=True, activity_count=5,
                )
                async with app.run_test(size=(120, 40)) as pilot:
                    await pilot.pause()
                    chart = app.query_one(StatusChart)
                    chart.update_from_snapshot(snap)
                    await pilot.pause()

                    rendered = chart.content
                    self.assertIn("done", rendered)
                    self.assertIn("1", rendered)

        asyncio.run(_run())

    def test_status_chart_unknown_status_no_crash(self) -> None:
        """Custom/unknown statuses render without crashing."""
        from tui.app import CobotsStatusApp
        from tui.widgets.overview.status_chart import StatusChart

        snap = make_snapshot(
            tasks=(_make_task(status="in-review"),),
            task_counts_by_status=types.MappingProxyType(
                {"in-review": 2}
            ),
        )

        async def _run():
            with tempfile.TemporaryDirectory() as tmp:
                ws = create_mock_workspace(tmp)
                app = CobotsStatusApp(
                    workspace_path=ws, no_refresh=True, activity_count=5,
                )
                async with app.run_test(size=(120, 40)) as pilot:
                    await pilot.pause()
                    chart = app.query_one(StatusChart)
                    chart.update_from_snapshot(snap)
                    await pilot.pause()

                    rendered = chart.content
                    self.assertIn("in-review", rendered)

        asyncio.run(_run())


@unittest.skipIf(_skip_if_no_textual(), "textual not installed")
class TestOwnerChart(unittest.TestCase):
    """Tests for OwnerChart widget rendering."""

    def test_owner_chart_renders_bars(self) -> None:
        """Each owner gets a bar with its count."""
        from tui.app import CobotsStatusApp
        from tui.widgets.overview.owner_chart import OwnerChart

        snap = make_snapshot(
            task_counts_by_owner=types.MappingProxyType(
                {"bob": 5, "alice": 3}
            ),
        )

        async def _run():
            with tempfile.TemporaryDirectory() as tmp:
                ws = create_mock_workspace(tmp)
                app = CobotsStatusApp(
                    workspace_path=ws, no_refresh=True, activity_count=5,
                )
                async with app.run_test(size=(120, 40)) as pilot:
                    await pilot.pause()
                    chart = app.query_one(OwnerChart)
                    chart.update_from_snapshot(snap)
                    await pilot.pause()

                    rendered = chart.content
                    self.assertIn("bob", rendered)
                    self.assertIn("alice", rendered)
                    self.assertIn("5", rendered)

        asyncio.run(_run())

    def test_owner_chart_max_display(self) -> None:
        """Caps at 8 owners and shows overflow message."""
        from tui.app import CobotsStatusApp
        from tui.widgets.overview.owner_chart import OwnerChart

        owners = {f"user{i}": 10 - i for i in range(12)}
        snap = make_snapshot(
            task_counts_by_owner=types.MappingProxyType(owners),
        )

        async def _run():
            with tempfile.TemporaryDirectory() as tmp:
                ws = create_mock_workspace(tmp)
                app = CobotsStatusApp(
                    workspace_path=ws, no_refresh=True, activity_count=5,
                )
                async with app.run_test(size=(120, 40)) as pilot:
                    await pilot.pause()
                    chart = app.query_one(OwnerChart)
                    chart.update_from_snapshot(snap)
                    await pilot.pause()

                    rendered = chart.content
                    self.assertIn("… and 4 more", rendered)

        asyncio.run(_run())

    def test_owner_chart_empty(self) -> None:
        """Shows '(no owners)' when snapshot has no owner counts."""
        from tui.app import CobotsStatusApp
        from tui.widgets.overview.owner_chart import OwnerChart

        snap = make_snapshot()

        async def _run():
            with tempfile.TemporaryDirectory() as tmp:
                ws = create_mock_workspace(tmp)
                app = CobotsStatusApp(
                    workspace_path=ws, no_refresh=True, activity_count=5,
                )
                async with app.run_test(size=(120, 40)) as pilot:
                    await pilot.pause()
                    chart = app.query_one(OwnerChart)
                    chart.update_from_snapshot(snap)
                    await pilot.pause()

                    rendered = chart.content
                    self.assertIn("no owners", rendered)

        asyncio.run(_run())


@unittest.skipIf(_skip_if_no_textual(), "textual not installed")
class TestActiveTasksList(unittest.TestCase):
    """Tests for ActiveTasksList widget rendering."""

    def test_active_tasks_filters_correctly(self) -> None:
        """Only non-completed tasks appear in the list."""
        from tui.app import CobotsStatusApp
        from tui.widgets.overview.active_tasks_list import ActiveTasksList

        tasks = (
            _make_task(task_id="t1", title="Pending One", status="pending"),
            _make_task(task_id="t2", title="Underway One", status="underway"),
            _make_task(task_id="t3", title="Done One", status="done"),
            _make_task(task_id="t4", title="Abandoned One", status="abandoned"),
        )
        snap = make_snapshot(tasks=tasks)

        async def _run():
            with tempfile.TemporaryDirectory() as tmp:
                ws = create_mock_workspace(tmp)
                app = CobotsStatusApp(
                    workspace_path=ws, no_refresh=True, activity_count=5,
                )
                async with app.run_test(size=(120, 40)) as pilot:
                    await pilot.pause()
                    widget = app.query_one(ActiveTasksList)
                    widget.update_from_snapshot(snap)
                    await pilot.pause()

                    rendered = widget.content
                    self.assertIn("Pending One", rendered)
                    self.assertIn("Underway One", rendered)
                    self.assertNotIn("Done One", rendered)
                    self.assertNotIn("Abandoned One", rendered)

        asyncio.run(_run())

    def test_active_tasks_max_display(self) -> None:
        """Caps at 8 tasks and shows '… and N more' message."""
        from tui.app import CobotsStatusApp
        from tui.widgets.overview.active_tasks_list import ActiveTasksList

        tasks = tuple(
            _make_task(
                task_id=f"t{i:04d}", title=f"Task {i}", status="pending",
            )
            for i in range(12)
        )
        snap = make_snapshot(tasks=tasks)

        async def _run():
            with tempfile.TemporaryDirectory() as tmp:
                ws = create_mock_workspace(tmp)
                app = CobotsStatusApp(
                    workspace_path=ws, no_refresh=True, activity_count=5,
                )
                async with app.run_test(size=(120, 40)) as pilot:
                    await pilot.pause()
                    widget = app.query_one(ActiveTasksList)
                    widget.update_from_snapshot(snap)
                    await pilot.pause()

                    rendered = widget.content
                    self.assertIn("… and 4 more", rendered)

        asyncio.run(_run())

    def test_active_tasks_empty(self) -> None:
        """Shows '(none)' when all tasks are completed."""
        from tui.app import CobotsStatusApp
        from tui.widgets.overview.active_tasks_list import ActiveTasksList

        tasks = (
            _make_task(task_id="t1", status="done"),
            _make_task(task_id="t2", status="abandoned"),
        )
        snap = make_snapshot(tasks=tasks)

        async def _run():
            with tempfile.TemporaryDirectory() as tmp:
                ws = create_mock_workspace(tmp)
                app = CobotsStatusApp(
                    workspace_path=ws, no_refresh=True, activity_count=5,
                )
                async with app.run_test(size=(120, 40)) as pilot:
                    await pilot.pause()
                    widget = app.query_one(ActiveTasksList)
                    widget.update_from_snapshot(snap)
                    await pilot.pause()

                    rendered = widget.content
                    self.assertIn("none", rendered)

        asyncio.run(_run())

    def test_active_tasks_sanitizes_text(self) -> None:
        """Rich markup in task titles is escaped."""
        from tui.app import CobotsStatusApp
        from tui.widgets.overview.active_tasks_list import ActiveTasksList

        tasks = (
            _make_task(
                task_id="t1",
                title="[bold]Injected[/bold]",
                status="pending",
            ),
        )
        snap = make_snapshot(tasks=tasks)

        async def _run():
            with tempfile.TemporaryDirectory() as tmp:
                ws = create_mock_workspace(tmp)
                app = CobotsStatusApp(
                    workspace_path=ws, no_refresh=True, activity_count=5,
                )
                async with app.run_test(size=(120, 40)) as pilot:
                    await pilot.pause()
                    widget = app.query_one(ActiveTasksList)
                    widget.update_from_snapshot(snap)
                    await pilot.pause()

                    rendered = widget.content
                    # The raw markup tags should appear escaped,
                    # NOT rendered as bold.
                    self.assertIn("\\[bold]", rendered)

        asyncio.run(_run())


@unittest.skipIf(_skip_if_no_textual(), "textual not installed")
class TestRecentReportsList(unittest.TestCase):
    """Tests for RecentReportsList widget rendering."""

    def test_recent_reports_shows_latest(self) -> None:
        """Shows at most 5 reports, newest first."""
        from tui.app import CobotsStatusApp
        from tui.widgets.overview.recent_reports_list import (
            RecentReportsList,
        )

        reports = tuple(
            _make_report(
                report_id=f"r{i:04d}",
                title=f"Report {i}",
                created_timestamp=f"2026-04-{20+i:02d} 10:00:00",
            )
            for i in range(8)
        )
        snap = make_snapshot(reports=reports, report_count=8)

        async def _run():
            with tempfile.TemporaryDirectory() as tmp:
                ws = create_mock_workspace(tmp)
                app = CobotsStatusApp(
                    workspace_path=ws, no_refresh=True, activity_count=5,
                )
                async with app.run_test(size=(120, 40)) as pilot:
                    await pilot.pause()
                    widget = app.query_one(RecentReportsList)
                    widget.update_from_snapshot(snap)
                    await pilot.pause()

                    rendered = widget.content
                    # First 5 should be present.
                    self.assertIn("Report 0", rendered)
                    self.assertIn("Report 4", rendered)
                    # 6th and beyond should NOT be shown.
                    self.assertNotIn("Report 5", rendered)

        asyncio.run(_run())

    def test_recent_reports_empty(self) -> None:
        """Shows '(none)' with no reports."""
        from tui.app import CobotsStatusApp
        from tui.widgets.overview.recent_reports_list import (
            RecentReportsList,
        )

        snap = make_snapshot()

        async def _run():
            with tempfile.TemporaryDirectory() as tmp:
                ws = create_mock_workspace(tmp)
                app = CobotsStatusApp(
                    workspace_path=ws, no_refresh=True, activity_count=5,
                )
                async with app.run_test(size=(120, 40)) as pilot:
                    await pilot.pause()
                    widget = app.query_one(RecentReportsList)
                    widget.update_from_snapshot(snap)
                    await pilot.pause()

                    rendered = widget.content
                    self.assertIn("none", rendered)

        asyncio.run(_run())


@unittest.skipIf(_skip_if_no_textual(), "textual not installed")
class TestActivityFeedWidget(unittest.TestCase):
    """Tests for ActivityFeedWidget rendering."""

    def test_feed_shows_events(self) -> None:
        """Feed displays event summaries after update_from_snapshot."""
        from tui.app import CobotsStatusApp

        now_str = "2026-04-22 12:00:00"
        events = (
            _make_event(
                timestamp="2026-04-22 11:55:00",
                event_type="task_created",
                summary="Created task alpha",
            ),
            _make_event(
                timestamp="2026-04-22 11:30:00",
                event_type="task_updated",
                summary="Updated task beta",
            ),
            _make_event(
                timestamp="2026-04-22 10:00:00",
                event_type="report_created",
                summary="Created report gamma",
            ),
        )
        snap = make_snapshot(
            activity_timeline=events,
            snapshot_timestamp=now_str,
        )

        async def _run():
            with tempfile.TemporaryDirectory() as tmp:
                ws = create_mock_workspace(tmp)
                app = CobotsStatusApp(
                    workspace_path=ws, no_refresh=True, activity_count=5,
                )
                async with app.run_test(size=(120, 40)) as pilot:
                    await pilot.pause()
                    from tui.widgets.overview.activity_feed import (
                        ActivityFeedWidget,
                    )
                    widget = app.query_one(ActivityFeedWidget)
                    widget.update_from_snapshot(snap)
                    await pilot.pause()

                    rendered = widget.content
                    self.assertIn("Created task alpha", rendered)
                    self.assertIn("Updated task beta", rendered)
                    self.assertIn("Created report gamma", rendered)

        asyncio.run(_run())

    def test_feed_empty_timeline(self) -> None:
        """Feed shows '(no recent activity)' when timeline is empty."""
        from tui.app import CobotsStatusApp

        snap = make_snapshot(activity_timeline=())

        async def _run():
            with tempfile.TemporaryDirectory() as tmp:
                ws = create_mock_workspace(tmp)
                app = CobotsStatusApp(
                    workspace_path=ws, no_refresh=True, activity_count=5,
                )
                async with app.run_test(size=(120, 40)) as pilot:
                    await pilot.pause()
                    from tui.widgets.overview.activity_feed import (
                        ActivityFeedWidget,
                    )
                    widget = app.query_one(ActivityFeedWidget)
                    widget.update_from_snapshot(snap)
                    await pilot.pause()

                    rendered = widget.content
                    self.assertIn("no recent activity", rendered)

        asyncio.run(_run())

    def test_feed_import(self) -> None:
        """ActivityFeedWidget can be imported from its module."""
        from tui.widgets.overview.activity_feed import ActivityFeedWidget
        self.assertTrue(callable(ActivityFeedWidget))


# ===================================================================
# Integration tests — full app with Overview tab
# ===================================================================


@unittest.skipIf(_skip_if_no_textual(), "textual not installed")
class TestOverviewIntegration(unittest.TestCase):
    """Integration tests for the Overview tab in the full TUI app."""

    def test_app_starts_with_overview_tab(self) -> None:
        """App composes without errors and Overview tab exists."""
        from tui.app import CobotsStatusApp
        from tui.widgets.overview.overview_pane import OverviewPane

        async def _run():
            with tempfile.TemporaryDirectory() as tmp:
                ws = create_mock_workspace(tmp)
                app = CobotsStatusApp(
                    workspace_path=ws, no_refresh=True, activity_count=5,
                )
                async with app.run_test(size=(120, 40)) as pilot:
                    await pilot.pause()
                    # OverviewPane should be queryable.
                    pane = app.query_one(OverviewPane)
                    self.assertIsNotNone(pane)

        asyncio.run(_run())

    def test_overview_is_default_active_tab(self) -> None:
        """TabbedContent.active == 'tab-overview' on startup."""
        from tui.app import CobotsStatusApp
        from textual.widgets import TabbedContent

        async def _run():
            with tempfile.TemporaryDirectory() as tmp:
                ws = create_mock_workspace(tmp)
                app = CobotsStatusApp(
                    workspace_path=ws, no_refresh=True, activity_count=5,
                )
                async with app.run_test(size=(120, 40)) as pilot:
                    await pilot.pause()
                    tc = app.query_one(TabbedContent)
                    self.assertEqual(tc.active, "tab-overview")

        asyncio.run(_run())

    def test_overview_pane_receives_snapshot(self) -> None:
        """After refresh, OverviewPane children have non-empty content."""
        from tui.app import CobotsStatusApp

        async def _run():
            with tempfile.TemporaryDirectory() as tmp:
                ws = create_mock_workspace(tmp)
                # Write some actual task/report files.
                tasks_dir = os.path.join(ws, "tasks")
                reports_dir = os.path.join(ws, "reports")
                write_task_file(tasks_dir, task_id="aa" * 8, status="pending")
                write_report_file(reports_dir, report_id="bb" * 8)

                app = CobotsStatusApp(
                    workspace_path=ws, no_refresh=True, activity_count=5,
                )
                async with app.run_test(size=(120, 40)) as pilot:
                    # Wait for initial load_snapshot to complete.
                    await pilot.pause()
                    await pilot.pause()
                    await pilot.pause()

                    from tui.widgets.overview.status_chart import (
                        StatusChart,
                    )
                    chart = app.query_one(StatusChart)
                    rendered = chart.content
                    # Should have some content (not the empty default).
                    self.assertTrue(len(rendered) > 0)

        asyncio.run(_run())

    def test_tab_navigation_cycles_three_tabs(self) -> None:
        """h/l keys cycle through Overview → Tasks → Reports."""
        from tui.app import CobotsStatusApp
        from textual.widgets import TabbedContent

        async def _run():
            with tempfile.TemporaryDirectory() as tmp:
                ws = create_mock_workspace(tmp)
                app = CobotsStatusApp(
                    workspace_path=ws, no_refresh=True, activity_count=5,
                )
                async with app.run_test(size=(120, 40)) as pilot:
                    await pilot.pause()
                    tc = app.query_one(TabbedContent)

                    # Start on Overview.
                    self.assertEqual(tc.active, "tab-overview")

                    # l → Tasks
                    await pilot.press("l")
                    await pilot.pause()
                    self.assertEqual(tc.active, "tab-tasks")

                    # l → Reports
                    await pilot.press("l")
                    await pilot.pause()
                    self.assertEqual(tc.active, "tab-reports")

                    # l → wraps to Overview
                    await pilot.press("l")
                    await pilot.pause()
                    self.assertEqual(tc.active, "tab-overview")

                    # h → wraps to Reports
                    await pilot.press("h")
                    await pilot.pause()
                    self.assertEqual(tc.active, "tab-reports")

        asyncio.run(_run())

    def test_overview_focus_on_tab_switch(self) -> None:
        """When switching to Overview, OverviewPane receives focus."""
        from tui.app import CobotsStatusApp
        from tui.widgets.overview.overview_pane import OverviewPane

        async def _run():
            with tempfile.TemporaryDirectory() as tmp:
                ws = create_mock_workspace(tmp)
                app = CobotsStatusApp(
                    workspace_path=ws, no_refresh=True, activity_count=5,
                )
                async with app.run_test(size=(120, 40)) as pilot:
                    await pilot.pause()
                    # Switch away and back.
                    await pilot.press("l")
                    await pilot.pause()
                    await pilot.press("h")
                    await pilot.pause()
                    await pilot.pause()
                    focused = app.focused
                    self.assertIsInstance(focused, OverviewPane)

        asyncio.run(_run())


# ===================================================================
# Review fix verification tests
# ===================================================================


class TestReviewFixes(unittest.TestCase):
    """Verifies the outstanding review findings are addressed."""

    def test_dim_parchment_in_tcss_comment(self) -> None:
        """Review fix #1: DIM_PARCHMENT is in the TCSS color comment."""
        tcss_path = os.path.join(
            os.path.dirname(__file__), "..", "tui", "styles", "status.tcss",
        )
        with open(tcss_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("Dim Parchment", content)
        self.assertIn("#8A8478", content)

    def test_no_duplicate_status_config_import(self) -> None:
        """Review fix #2: StatusConfig imported once at module level."""
        cli_path = os.path.join(
            os.path.dirname(__file__), "..", "cobots-tui.py",
        )
        with open(cli_path, "r", encoding="utf-8") as f:
            content = f.read()
        # Should have exactly one `from cobots_lib...import StatusConfig`.
        import_count = content.count(
            "from cobots_lib.workspace.config import StatusConfig"
        )
        self.assertEqual(import_count, 1)

    def test_clamp_cli_args_function_exists(self) -> None:
        """Review fix #3: clamp_cli_args helper extracted in CLI."""
        cli_path = os.path.join(
            os.path.dirname(__file__), "..", "cobots-tui.py",
        )
        with open(cli_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("def clamp_cli_args(", content)

    def test_activity_log_sanitizes_fallback(self) -> None:
        """Review fix #5: fallback label in activity_log is sanitized."""
        log_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "tui",
            "widgets",
            "activity_log.py",
        )
        with open(log_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("sanitize_display_text(event.event_type)", content)

    def test_no_unused_re_import_in_security(self) -> None:
        """Review fix #6: security.py has no unused 'import re'."""
        sec_path = os.path.join(
            os.path.dirname(__file__), "..", "security.py",
        )
        with open(sec_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertNotIn("import re", content)


# ===================================================================
# UI polish tests — borders and centered KPIs
# ===================================================================


class TestOverviewBordersInTCSS(unittest.TestCase):
    """Verifies that the TCSS file declares borders for overview widgets."""

    @classmethod
    def setUpClass(cls) -> None:
        """Load the TCSS file content once for all tests."""
        tcss_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "tui",
            "styles",
            "status.tcss",
        )
        with open(tcss_path, "r", encoding="utf-8") as f:
            cls.tcss_content = f.read()

    def test_kpi_panel_has_border(self) -> None:
        """KpiPanel section declares a round border."""
        self.assertIn("border: round #8A8478", self.tcss_content)

    def test_status_chart_has_border(self) -> None:
        """StatusChart section declares a round border."""
        # Find the StatusChart block specifically.
        idx = self.tcss_content.find("StatusChart {")
        self.assertNotEqual(idx, -1, "StatusChart block missing")
        block = self.tcss_content[idx:idx + 200]
        self.assertIn("border: round #8A8478", block)

    def test_owner_chart_has_border(self) -> None:
        """OwnerChart section declares a round border."""
        idx = self.tcss_content.find("OwnerChart {")
        self.assertNotEqual(idx, -1, "OwnerChart block missing")
        block = self.tcss_content[idx:idx + 200]
        self.assertIn("border: round #8A8478", block)

    def test_active_tasks_list_has_border(self) -> None:
        """ActiveTasksList section declares a round border."""
        idx = self.tcss_content.find("ActiveTasksList {")
        self.assertNotEqual(idx, -1, "ActiveTasksList block missing")
        block = self.tcss_content[idx:idx + 200]
        self.assertIn("border: round #8A8478", block)

    def test_recent_reports_list_has_border(self) -> None:
        """RecentReportsList section declares a round border."""
        idx = self.tcss_content.find("RecentReportsList {")
        self.assertNotEqual(idx, -1, "RecentReportsList block missing")
        block = self.tcss_content[idx:idx + 200]
        self.assertIn("border: round #8A8478", block)

    def test_activity_feed_has_border(self) -> None:
        """ActivityFeedWidget section declares a round border."""
        idx = self.tcss_content.find("ActivityFeedWidget {")
        self.assertNotEqual(idx, -1, "ActivityFeedWidget block missing")
        block = self.tcss_content[idx:idx + 200]
        self.assertIn("border: round #8A8478", block)

    def test_border_title_color_declared(self) -> None:
        """All bordered widgets declare a border-title-color."""
        for widget in (
            "KpiPanel",
            "StatusChart",
            "OwnerChart",
            "ActiveTasksList",
            "RecentReportsList",
            "ActivityFeedWidget",
        ):
            idx = self.tcss_content.find(f"{widget} {{")
            self.assertNotEqual(idx, -1, f"{widget} block missing")
            block = self.tcss_content[idx:idx + 200]
            self.assertIn(
                "border-title-color: #F5ECD7",
                block,
                f"{widget} missing border-title-color",
            )


class TestOverviewBorderTitles(unittest.TestCase):
    """Verifies that overview widgets set border_title on instances.

    The border_title must be set in ``__init__`` (via ``self.border_title``)
    rather than as a class variable, because a class-level assignment
    shadows the Textual ``_BorderTitle`` descriptor and prevents Textual
    from rendering the title.
    """

    def test_status_chart_border_title(self) -> None:
        """StatusChart instance has the expected border_title."""
        from tui.widgets.overview.status_chart import StatusChart
        widget = StatusChart()
        self.assertEqual(widget.border_title, "Status Breakdown")

    def test_owner_chart_border_title(self) -> None:
        """OwnerChart instance has the expected border_title."""
        from tui.widgets.overview.owner_chart import OwnerChart
        widget = OwnerChart()
        self.assertEqual(widget.border_title, "By Owner")

    def test_active_tasks_list_border_title(self) -> None:
        """ActiveTasksList instance has the expected border_title."""
        from tui.widgets.overview.active_tasks_list import (
            ActiveTasksList,
        )
        widget = ActiveTasksList()
        self.assertEqual(widget.border_title, "Active Tasks")

    def test_recent_reports_list_border_title(self) -> None:
        """RecentReportsList instance has the expected border_title."""
        from tui.widgets.overview.recent_reports_list import (
            RecentReportsList,
        )
        widget = RecentReportsList()
        self.assertEqual(widget.border_title, "Recent Reports")

    def test_activity_feed_border_title(self) -> None:
        """ActivityFeedWidget instance has the expected border_title."""
        from tui.widgets.overview.activity_feed import (
            ActivityFeedWidget,
        )
        widget = ActivityFeedWidget()
        self.assertEqual(widget.border_title, "Recent Activity")

    def test_kpi_panel_border_title(self) -> None:
        """KpiPanel instance has the expected border_title."""
        from tui.widgets.overview.kpi_panel import KpiPanel
        widget = KpiPanel()
        self.assertEqual(widget.border_title, "Dashboard")

    def test_no_class_level_border_title(self) -> None:
        """No widget should shadow the Textual descriptor with a class var."""
        from tui.widgets.overview.status_chart import StatusChart
        from tui.widgets.overview.owner_chart import OwnerChart
        from tui.widgets.overview.active_tasks_list import ActiveTasksList
        from tui.widgets.overview.recent_reports_list import RecentReportsList
        from tui.widgets.overview.activity_feed import ActivityFeedWidget
        from tui.widgets.overview.kpi_panel import KpiPanel

        for cls in (
            StatusChart, OwnerChart, ActiveTasksList,
            RecentReportsList, ActivityFeedWidget, KpiPanel,
        ):
            self.assertNotIn(
                "border_title", cls.__dict__,
                f"{cls.__name__} must not have a class-level border_title "
                f"(it shadows Textual's _BorderTitle descriptor)",
            )


class TestKpiCenteringInTCSS(unittest.TestCase):
    """Verifies that TCSS rules center KPI digits and labels."""

    @classmethod
    def setUpClass(cls) -> None:
        """Load the TCSS file content once for all tests."""
        tcss_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "tui",
            "styles",
            "status.tcss",
        )
        with open(tcss_path, "r", encoding="utf-8") as f:
            cls.tcss_content = f.read()

    def test_kpi_card_has_center_alignment(self) -> None:
        """The .kpi-card rule includes center alignment."""
        idx = self.tcss_content.find(".kpi-card {")
        self.assertNotEqual(idx, -1, ".kpi-card block missing")
        block = self.tcss_content[idx:idx + 200]
        self.assertIn("align: center middle", block)
        self.assertIn("content-align: center middle", block)

    def test_kpi_label_has_text_align_center(self) -> None:
        """The .kpi-label rule includes text-align: center."""
        idx = self.tcss_content.find(".kpi-label {")
        self.assertNotEqual(idx, -1, ".kpi-label block missing")
        block = self.tcss_content[idx:idx + 200]
        self.assertIn("text-align: center", block)

    def test_kpi_label_has_full_width(self) -> None:
        """The .kpi-label rule sets width: 100%."""
        idx = self.tcss_content.find(".kpi-label {")
        self.assertNotEqual(idx, -1, ".kpi-label block missing")
        block = self.tcss_content[idx:idx + 200]
        self.assertIn("width: 100%", block)

    def test_digits_has_text_align_center(self) -> None:
        """The Digits rule includes text-align: center."""
        idx = self.tcss_content.find("Digits {")
        self.assertNotEqual(idx, -1, "Digits block missing")
        block = self.tcss_content[idx:idx + 150]
        self.assertIn("text-align: center", block)

    def test_digits_has_full_width(self) -> None:
        """The Digits rule sets width: 100%."""
        idx = self.tcss_content.find("Digits {")
        self.assertNotEqual(idx, -1, "Digits block missing")
        block = self.tcss_content[idx:idx + 150]
        self.assertIn("width: 100%", block)


class TestInlineHeadersRemoved(unittest.TestCase):
    """Verifies that redundant inline bold headers were removed.

    Since border titles now provide section headers, the old inline
    ``[bold]Title[/bold]`` lines at the start of widget content are
    redundant and should be absent from the widget source files.
    """

    def _read_widget_source(self, filename: str) -> str:
        """Reads a widget source file from the overview directory."""
        path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "tui",
            "widgets",
            "overview",
            filename,
        )
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def test_status_chart_no_inline_header(self) -> None:
        """StatusChart no longer prepends '[bold]Status Breakdown'."""
        src = self._read_widget_source("status_chart.py")
        self.assertNotIn("[bold]Status Breakdown[/bold]", src)

    def test_owner_chart_no_inline_header(self) -> None:
        """OwnerChart no longer prepends '[bold]By Owner'."""
        src = self._read_widget_source("owner_chart.py")
        self.assertNotIn("[bold]By Owner[/bold]", src)

    def test_active_tasks_list_no_inline_header(self) -> None:
        """ActiveTasksList no longer prepends '[bold]Active Tasks'."""
        src = self._read_widget_source("active_tasks_list.py")
        self.assertNotIn("[bold]Active Tasks[/bold]", src)

    def test_recent_reports_list_no_inline_header(self) -> None:
        """RecentReportsList no longer prepends '[bold]Recent Reports'."""
        src = self._read_widget_source("recent_reports_list.py")
        self.assertNotIn("[bold]Recent Reports[/bold]", src)


@unittest.skipIf(_skip_if_no_textual(), "textual not installed")
class TestDynamicTruncation(unittest.TestCase):
    """Tests that text truncation adapts to widget width."""

    def test_active_tasks_uses_dynamic_width(self) -> None:
        """ActiveTasksList truncates title based on self.size.width."""
        from tui.app import CobotsStatusApp
        from tui.widgets.overview.active_tasks_list import ActiveTasksList

        long_title = "A" * 80
        tasks = (_make_task(task_id="t1", title=long_title, status="pending"),)
        snap = make_snapshot(tasks=tasks)

        async def _run():
            with tempfile.TemporaryDirectory() as tmp:
                ws = create_mock_workspace(tmp)
                app = CobotsStatusApp(
                    workspace_path=ws, no_refresh=True, activity_count=5,
                )
                async with app.run_test(size=(120, 40)) as pilot:
                    await pilot.pause()
                    widget = app.query_one(ActiveTasksList)
                    widget.update_from_snapshot(snap)
                    await pilot.pause()

                    rendered = widget.content
                    # Widget is inside a grid, so actual width < 120.
                    # Compute expected available width from actual widget size.
                    w = widget.size.width
                    expected_available = max(10, w - 22) if w > 0 else 35
                    expected_title = long_title[:expected_available]
                    self.assertIn(expected_title, rendered)
                    # If the widget is narrower than 80+prefix, the full
                    # title should be truncated.
                    if expected_available < 80:
                        self.assertNotIn(long_title, rendered)

        asyncio.run(_run())

    def test_active_tasks_narrow_width_truncates(self) -> None:
        """ActiveTasksList truncates more aggressively at narrow widths."""
        from tui.app import CobotsStatusApp
        from tui.widgets.overview.active_tasks_list import ActiveTasksList

        long_title = "A" * 80
        tasks = (_make_task(task_id="t1", title=long_title, status="pending"),)
        snap = make_snapshot(tasks=tasks)

        async def _run():
            with tempfile.TemporaryDirectory() as tmp:
                ws = create_mock_workspace(tmp)
                app = CobotsStatusApp(
                    workspace_path=ws, no_refresh=True, activity_count=5,
                )
                # Very narrow terminal: only 40 columns.
                async with app.run_test(size=(40, 40)) as pilot:
                    await pilot.pause()
                    widget = app.query_one(ActiveTasksList)
                    widget.update_from_snapshot(snap)
                    await pilot.pause()

                    rendered = widget.content
                    # Full 80-char title should NOT appear.
                    self.assertNotIn(long_title, rendered)
                    # Some portion should still be visible.
                    self.assertIn("AAAA", rendered)

        asyncio.run(_run())

    def test_recent_reports_uses_dynamic_width(self) -> None:
        """RecentReportsList truncates title based on self.size.width."""
        from tui.app import CobotsStatusApp
        from tui.widgets.overview.recent_reports_list import (
            RecentReportsList,
        )

        long_title = "B" * 80
        reports = (
            _make_report(report_id="r0001", title=long_title),
        )
        snap = make_snapshot(reports=reports, report_count=1)

        async def _run():
            with tempfile.TemporaryDirectory() as tmp:
                ws = create_mock_workspace(tmp)
                app = CobotsStatusApp(
                    workspace_path=ws, no_refresh=True, activity_count=5,
                )
                async with app.run_test(size=(120, 40)) as pilot:
                    await pilot.pause()
                    widget = app.query_one(RecentReportsList)
                    widget.update_from_snapshot(snap)
                    await pilot.pause()

                    rendered = widget.content
                    # Widget is inside a grid, so actual width < 120.
                    w = widget.size.width
                    expected_available = max(10, w - 36) if w > 0 else 30
                    expected_title = long_title[:expected_available]
                    self.assertIn(expected_title, rendered)
                    if expected_available < 80:
                        self.assertNotIn(long_title, rendered)

        asyncio.run(_run())

    def test_activity_feed_uses_dynamic_width(self) -> None:
        """ActivityFeedWidget truncates summary based on self.size.width."""
        from tui.app import CobotsStatusApp
        from tui.widgets.overview.activity_feed import ActivityFeedWidget

        long_summary = "C" * 80
        events = (
            _make_event(
                timestamp="2026-04-22 11:55:00",
                event_type="task_created",
                summary=long_summary,
            ),
        )
        snap = make_snapshot(
            activity_timeline=events,
            snapshot_timestamp="2026-04-22 12:00:00",
        )

        async def _run():
            with tempfile.TemporaryDirectory() as tmp:
                ws = create_mock_workspace(tmp)
                app = CobotsStatusApp(
                    workspace_path=ws, no_refresh=True, activity_count=5,
                )
                async with app.run_test(size=(120, 40)) as pilot:
                    await pilot.pause()
                    widget = app.query_one(ActivityFeedWidget)
                    widget.update_from_snapshot(snap)
                    await pilot.pause()

                    rendered = widget.content
                    # Widget spans both columns, so it's wider.
                    w = widget.size.width
                    expected_available = max(10, w - 19) if w > 0 else 45
                    expected_summary = long_summary[:expected_available]
                    self.assertIn(expected_summary, rendered)
                    if expected_available < 80:
                        self.assertNotIn(long_summary, rendered)

        asyncio.run(_run())

    def test_no_hardcoded_truncation_in_source(self) -> None:
        """Verify hardcoded truncation constants have been removed."""
        import os

        widget_dir = os.path.join(
            os.path.dirname(__file__), "..", "tui", "widgets", "overview",
        )

        # active_tasks_list.py should NOT have [:35] on title
        with open(os.path.join(widget_dir, "active_tasks_list.py")) as f:
            src = f.read()
        self.assertNotIn("[:35]", src)
        self.assertIn("self.size.width", src)

        # recent_reports_list.py should NOT have [:30] on title
        with open(os.path.join(widget_dir, "recent_reports_list.py")) as f:
            src = f.read()
        self.assertNotIn("[:30]", src)
        self.assertIn("self.size.width", src)

        # activity_feed.py should NOT have [:45] on summary
        with open(os.path.join(widget_dir, "activity_feed.py")) as f:
            src = f.read()
        self.assertNotIn("[:45]", src)
        self.assertIn("self.size.width", src)


@unittest.skipIf(_skip_if_no_textual(), "textual not installed")
class TestResizeRerender(unittest.TestCase):
    """Tests that widgets re-render on resize via _last_snapshot."""

    def test_active_tasks_stores_last_snapshot(self) -> None:
        """ActiveTasksList caches the snapshot for resize re-render."""
        from tui.app import CobotsStatusApp
        from tui.widgets.overview.active_tasks_list import ActiveTasksList

        tasks = (_make_task(task_id="t1", title="Test", status="pending"),)
        snap = make_snapshot(tasks=tasks)

        async def _run():
            with tempfile.TemporaryDirectory() as tmp:
                ws = create_mock_workspace(tmp)
                app = CobotsStatusApp(
                    workspace_path=ws, no_refresh=True, activity_count=5,
                )
                async with app.run_test(size=(120, 40)) as pilot:
                    await pilot.pause()
                    widget = app.query_one(ActiveTasksList)
                    widget.update_from_snapshot(snap)
                    await pilot.pause()
                    self.assertIs(widget._last_snapshot, snap)

        asyncio.run(_run())

    def test_recent_reports_stores_last_snapshot(self) -> None:
        """RecentReportsList caches the snapshot for resize re-render."""
        from tui.app import CobotsStatusApp
        from tui.widgets.overview.recent_reports_list import (
            RecentReportsList,
        )

        reports = (_make_report(report_id="r0001", title="Test"),)
        snap = make_snapshot(reports=reports, report_count=1)

        async def _run():
            with tempfile.TemporaryDirectory() as tmp:
                ws = create_mock_workspace(tmp)
                app = CobotsStatusApp(
                    workspace_path=ws, no_refresh=True, activity_count=5,
                )
                async with app.run_test(size=(120, 40)) as pilot:
                    await pilot.pause()
                    widget = app.query_one(RecentReportsList)
                    widget.update_from_snapshot(snap)
                    await pilot.pause()
                    self.assertIs(widget._last_snapshot, snap)

        asyncio.run(_run())

    def test_activity_feed_stores_last_snapshot(self) -> None:
        """ActivityFeedWidget caches the snapshot for resize re-render."""
        from tui.app import CobotsStatusApp
        from tui.widgets.overview.activity_feed import ActivityFeedWidget

        events = (
            _make_event(
                timestamp="2026-04-22 11:55:00",
                event_type="task_created",
                summary="Test event",
            ),
        )
        snap = make_snapshot(
            activity_timeline=events,
            snapshot_timestamp="2026-04-22 12:00:00",
        )

        async def _run():
            with tempfile.TemporaryDirectory() as tmp:
                ws = create_mock_workspace(tmp)
                app = CobotsStatusApp(
                    workspace_path=ws, no_refresh=True, activity_count=5,
                )
                async with app.run_test(size=(120, 40)) as pilot:
                    await pilot.pause()
                    widget = app.query_one(ActivityFeedWidget)
                    widget.update_from_snapshot(snap)
                    await pilot.pause()
                    self.assertIs(widget._last_snapshot, snap)

        asyncio.run(_run())

    def test_active_tasks_has_on_resize(self) -> None:
        """ActiveTasksList defines on_resize for re-rendering."""
        from tui.widgets.overview.active_tasks_list import ActiveTasksList
        self.assertTrue(hasattr(ActiveTasksList, "on_resize"))
        self.assertTrue(callable(getattr(ActiveTasksList, "on_resize")))

    def test_recent_reports_has_on_resize(self) -> None:
        """RecentReportsList defines on_resize for re-rendering."""
        from tui.widgets.overview.recent_reports_list import (
            RecentReportsList,
        )
        self.assertTrue(hasattr(RecentReportsList, "on_resize"))
        self.assertTrue(callable(getattr(RecentReportsList, "on_resize")))

    def test_activity_feed_has_on_resize(self) -> None:
        """ActivityFeedWidget defines on_resize for re-rendering."""
        from tui.widgets.overview.activity_feed import ActivityFeedWidget
        self.assertTrue(hasattr(ActivityFeedWidget, "on_resize"))
        self.assertTrue(callable(getattr(ActivityFeedWidget, "on_resize")))

    def test_on_resize_noop_without_snapshot(self) -> None:
        """on_resize is a no-op when _last_snapshot is None."""
        from tui.app import CobotsStatusApp
        from tui.widgets.overview.active_tasks_list import ActiveTasksList

        async def _run():
            with tempfile.TemporaryDirectory() as tmp:
                ws = create_mock_workspace(tmp)
                app = CobotsStatusApp(
                    workspace_path=ws, no_refresh=True, activity_count=5,
                )
                async with app.run_test(size=(120, 40)) as pilot:
                    await pilot.pause()
                    widget = app.query_one(ActiveTasksList)
                    # Should not raise even with no snapshot.
                    widget.on_resize(None)
                    await pilot.pause()

        asyncio.run(_run())


if __name__ == "__main__":
    unittest.main()
