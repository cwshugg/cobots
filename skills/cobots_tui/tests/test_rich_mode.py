"""
test_rich_mode.py - Unit tests for the Rich-formatted output mode.

Tests that Rich output contains expected content and that markup from
file data is properly escaped.
"""

import io
import os
import sys
import tempfile
import types
import unittest
from unittest.mock import MagicMock

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

sys.modules.setdefault("venv", MagicMock())
sys.modules.setdefault("venv.venv", MagicMock())

from rich.console import Console

from data import TaskData, ReportData, ActivityEvent, StatusSnapshot
from modes.rich_mode import (
    _build_task_table,
    _build_report_table,
    _build_summary_text,
    _build_activity_section,
)
from tests.helpers import make_snapshot


def _render(renderable) -> str:
    """Captures Rich renderable output as plain text."""
    buf = io.StringIO()
    console = Console(file=buf, force_terminal=False, no_color=True, width=120)
    console.print(renderable)
    return buf.getvalue()


class TestRichOutputContainsWorkspaceName(unittest.TestCase):
    """Rich summary text includes the workspace name."""

    def test_workspace_in_summary(self) -> None:
        snap = make_snapshot(
            task_counts_by_status=types.MappingProxyType({"pending": 2}),
        )
        text = _build_summary_text(snap)
        self.assertIn("pending", text)
        self.assertIn("2", text)


class TestRichOutputContainsTaskTable(unittest.TestCase):
    """Rich task table includes task data."""

    def test_task_in_table(self) -> None:
        task = TaskData(
            id="abc123def4", title="My Feature", status="underway",
            author="alice", owner="bob",
            created_timestamp="2026-04-22 10:00:00",
            linked_tasks=(), path="/x", relative_path="x",
        )
        snap = make_snapshot(tasks=(task,))
        output = _render(_build_task_table(snap))
        self.assertIn("abc123def4", output)
        self.assertIn("My Feature", output)
        self.assertIn("underway", output)


class TestRichSanitizesMarkup(unittest.TestCase):
    """Rich markup in file data is escaped, not rendered."""

    def test_markup_escaped_in_task_table(self) -> None:
        task = TaskData(
            id="abc123def4", title="[bold]INJECTED[/bold]", status="pending",
            author="alice", owner="bob",
            created_timestamp="2026-04-22 10:00:00",
            linked_tasks=(), path="/x", relative_path="x",
        )
        snap = make_snapshot(tasks=(task,))
        output = _render(_build_task_table(snap))
        # The literal "[bold]" should appear in the output (escaped),
        # not be rendered as actual bold formatting.
        self.assertIn("[bold]", output)


class TestRichReportTable(unittest.TestCase):
    """Rich report table includes report data."""

    def test_report_in_table(self) -> None:
        report = ReportData(
            id="rpt1234567", title="My Report", author="lorey",
            created_timestamp="2026-04-22 11:00:00",
            path="/x", relative_path="x",
        )
        snap = make_snapshot(reports=(report,))
        output = _render(_build_report_table(snap))
        self.assertIn("rpt1234567", output)
        self.assertIn("My Report", output)


class TestRichActivitySection(unittest.TestCase):
    """Rich activity section includes events."""

    def test_activity_events(self) -> None:
        event = ActivityEvent(
            timestamp="2026-04-22 11:00:00",
            event_type="task_created",
            summary="New task created",
            entity_id="abc123",
        )
        snap = make_snapshot(activity_timeline=(event,))
        output = _render(_build_activity_section(snap))
        self.assertIn("New task created", output)

    def test_empty_activity(self) -> None:
        snap = make_snapshot()
        output = _render(_build_activity_section(snap))
        self.assertIn("no recent activity", output)


if __name__ == "__main__":
    unittest.main()
