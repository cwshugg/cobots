"""
test_data.py - Unit tests for the data layer.

Tests dataclasses, parsing functions, snapshot builder, and activity
timeline logic.
"""

import os
import sys
import tempfile
import types
import unittest

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

# Mock venv activation.
from unittest.mock import MagicMock
sys.modules.setdefault("venv", MagicMock())
sys.modules.setdefault("venv.venv", MagicMock())

from data import (
    TaskData,
    ReportData,
    ActivityEvent,
    StatusSnapshot,
    load_task,
    load_report,
    load_snapshot,
    build_activity_timeline,
    _read_body_safe,
    MAX_FILE_SIZE,
)
from tests.helpers import create_mock_workspace, write_task_file, write_report_file


class TestLoadTaskValid(unittest.TestCase):
    """load_task with a well-formed task file."""

    def test_parses_task(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = create_mock_workspace(tmp)
            tasks_dir = os.path.join(ws, "tasks")
            path = write_task_file(tasks_dir)

            task = load_task(path, ws)
            self.assertIsNotNone(task)
            self.assertEqual(task.id, "aaaa1111bbbb2222")
            self.assertEqual(task.title, "Test Task")
            self.assertEqual(task.status, "pending")
            self.assertEqual(task.author, "alice")
            self.assertEqual(task.owner, "bob")
            self.assertIsInstance(task.linked_tasks, tuple)


class TestLoadTaskMalformed(unittest.TestCase):
    """load_task with malformed frontmatter returns None."""

    def test_returns_none(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = create_mock_workspace(tmp)
            tasks_dir = os.path.join(ws, "tasks")
            path = os.path.join(tasks_dir, "bad.task.md")
            with open(path, "w") as f:
                f.write("No frontmatter here, just text.")

            task = load_task(path, ws)
            self.assertIsNone(task)


class TestLoadTaskOversized(unittest.TestCase):
    """load_task with a file exceeding MAX_FILE_SIZE returns None."""

    def test_returns_none_for_large_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = create_mock_workspace(tmp)
            tasks_dir = os.path.join(ws, "tasks")
            path = os.path.join(tasks_dir, "huge.task.md")
            with open(path, "w") as f:
                f.write("---\nid: huge\ntitle: big\n---\n")
                f.write("x" * (MAX_FILE_SIZE + 1))

            task = load_task(path, ws)
            self.assertIsNone(task)


class TestLoadTaskOutsideWorkspace(unittest.TestCase):
    """load_task with a path outside the workspace returns None."""

    def test_returns_none(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = create_mock_workspace(tmp)
            outside = os.path.join(tmp, "outside.task.md")
            with open(outside, "w") as f:
                f.write("---\nid: outside\ntitle: Outside\n---\nBody.")

            task = load_task(outside, ws)
            self.assertIsNone(task)


class TestLoadReportValid(unittest.TestCase):
    """load_report with a well-formed report file."""

    def test_parses_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = create_mock_workspace(tmp)
            reports_dir = os.path.join(ws, "reports")
            path = write_report_file(reports_dir)

            report = load_report(path, ws)
            self.assertIsNotNone(report)
            self.assertEqual(report.id, "cccc3333dddd4444")
            self.assertEqual(report.title, "Test Report")
            self.assertEqual(report.author, "lorey")


class TestLoadSnapshotEmpty(unittest.TestCase):
    """load_snapshot on an empty workspace."""

    def test_zero_counts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = create_mock_workspace(tmp)
            snap = load_snapshot(workspace_path=ws)

            self.assertEqual(len(snap.tasks), 0)
            self.assertEqual(len(snap.reports), 0)
            self.assertEqual(snap.report_count, 0)
            self.assertEqual(len(snap.activity_timeline), 0)


class TestLoadSnapshotAggregation(unittest.TestCase):
    """load_snapshot correctly computes aggregation counts."""

    def test_counts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = create_mock_workspace(tmp)
            tasks_dir = os.path.join(ws, "tasks")
            reports_dir = os.path.join(ws, "reports")

            write_task_file(tasks_dir, task_id="task0001aaa00001",
                          status="pending", owner="alice")
            write_task_file(tasks_dir, task_id="task0002bbb00002",
                          status="pending", owner="bob")
            write_task_file(tasks_dir, task_id="task0003ccc00003",
                          status="done", owner="alice")
            write_report_file(reports_dir, report_id="rpt00001aaa00001")

            snap = load_snapshot(workspace_path=ws)

            self.assertEqual(len(snap.tasks), 3)
            self.assertEqual(snap.report_count, 1)
            self.assertEqual(dict(snap.task_counts_by_status).get("pending"), 2)
            self.assertEqual(dict(snap.task_counts_by_status).get("done"), 1)
            self.assertEqual(dict(snap.task_counts_by_owner).get("alice"), 2)
            self.assertEqual(dict(snap.task_counts_by_owner).get("bob"), 1)


class TestActivityTimelineOrdering(unittest.TestCase):
    """Activity timeline is sorted newest-first."""

    def test_newest_first(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = create_mock_workspace(tmp)
            tasks_dir = os.path.join(ws, "tasks")
            reports_dir = os.path.join(ws, "reports")

            write_task_file(tasks_dir, task_id="t001000000000001",
                          created_timestamp="2026-01-01 00:00:00")
            write_task_file(tasks_dir, task_id="t002000000000002",
                          created_timestamp="2026-06-01 00:00:00")
            write_report_file(reports_dir, report_id="r001000000000001",
                            created_timestamp="2026-03-01 00:00:00")

            snap = load_snapshot(workspace_path=ws)

            timestamps = [e.timestamp for e in snap.activity_timeline]
            self.assertEqual(timestamps, sorted(timestamps, reverse=True))


class TestActivityTimelineLimit(unittest.TestCase):
    """Activity timeline respects the activity_count limit."""

    def test_limit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = create_mock_workspace(tmp)
            tasks_dir = os.path.join(ws, "tasks")

            for i in range(10):
                write_task_file(
                    tasks_dir,
                    task_id=f"tlimit{i:010d}",
                    created_timestamp=f"2026-01-{i+1:02d} 00:00:00",
                )

            snap = load_snapshot(workspace_path=ws, activity_count=3)
            self.assertLessEqual(len(snap.activity_timeline), 3)


class TestFrozenDataclassImmutability(unittest.TestCase):
    """Frozen dataclasses reject attribute assignment."""

    def test_task_immutable(self) -> None:
        task = TaskData(
            id="a", title="b", status="c", author="d", owner="e",
            created_timestamp="f", linked_tasks=(), path="/x", relative_path="x",
        )
        with self.assertRaises(AttributeError):
            task.title = "modified"  # type: ignore

    def test_snapshot_immutable(self) -> None:
        snap = StatusSnapshot(
            workspace_name="w", workspace_root="/w",
            tasks=(), reports=(),
            task_counts_by_status=types.MappingProxyType({}),
            task_counts_by_owner=types.MappingProxyType({}),
            report_count=0, activity_timeline=(),
            snapshot_timestamp="now",
        )
        with self.assertRaises(AttributeError):
            snap.workspace_name = "modified"  # type: ignore


class TestReadBodySafeOversized(unittest.TestCase):
    """_read_body_safe returns empty string for files exceeding MAX_FILE_SIZE.

    Addresses security finding F1: _read_body_safe() now enforces
    MAX_FILE_SIZE before reading, closing the TOCTOU window.
    """

    def test_oversized_file_returns_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = create_mock_workspace(tmp)
            tasks_dir = os.path.join(ws, "tasks")
            path = write_task_file(tasks_dir, task_id="oversizedtask001")
            # Grow the file beyond MAX_FILE_SIZE.
            with open(path, "a") as f:
                f.write("x" * (MAX_FILE_SIZE + 1))

            result = _read_body_safe(path)
            self.assertEqual(result, "")

    def test_normal_file_returns_body(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = create_mock_workspace(tmp)
            tasks_dir = os.path.join(ws, "tasks")
            path = write_task_file(
                tasks_dir,
                task_id="normaltask000001",
                body="Hello world.",
            )

            result = _read_body_safe(path)
            self.assertIn("Hello world.", result)

    def test_nonexistent_file_returns_empty(self) -> None:
        result = _read_body_safe("/nonexistent/path/to/file.md")
        self.assertEqual(result, "")

    def test_oversized_file_excluded_from_timeline(self) -> None:
        """An oversized task file should produce no discussion events."""
        with tempfile.TemporaryDirectory() as tmp:
            ws = create_mock_workspace(tmp)
            tasks_dir = os.path.join(ws, "tasks")
            # Write a task with a discussion header in the body.
            path = write_task_file(
                tasks_dir,
                task_id="bigdiscuss000001",
                body="## 2026-05-01 12:00:00 - alice\nDiscussion text.",
            )
            # Grow the file beyond MAX_FILE_SIZE.
            with open(path, "a") as f:
                f.write("x" * (MAX_FILE_SIZE + 1))

            task = TaskData(
                id="bigdiscuss000001",
                title="Oversized Task",
                status="pending",
                author="alice",
                owner="bob",
                created_timestamp="2026-01-01 00:00:00",
                linked_tasks=(),
                path=path,
                relative_path="tasks/bigdiscuss000001.task.md",
            )
            timeline = build_activity_timeline(
                (task,), (), ws, count=100
            )
            # Only the task_created event should appear (no discussion events
            # from the oversized body).
            event_types = [e.event_type for e in timeline]
            self.assertNotIn("task_updated", event_types)


class TestSnapshotSortDescending(unittest.TestCase):
    """load_snapshot sorts tasks and reports newest-first."""

    def test_tasks_sorted_descending(self) -> None:
        """Tasks are sorted by created_timestamp descending."""
        with tempfile.TemporaryDirectory() as tmp:
            ws = create_mock_workspace(tmp)
            tasks_dir = os.path.join(ws, "tasks")

            write_task_file(
                tasks_dir,
                task_id="old_task000000001",
                created_timestamp="2026-01-01 00:00:00",
            )
            write_task_file(
                tasks_dir,
                task_id="new_task000000002",
                created_timestamp="2026-06-15 12:00:00",
            )
            write_task_file(
                tasks_dir,
                task_id="mid_task000000003",
                created_timestamp="2026-03-10 06:00:00",
            )

            snap = load_snapshot(workspace_path=ws)

            timestamps = [t.created_timestamp for t in snap.tasks]
            self.assertEqual(
                timestamps, sorted(timestamps, reverse=True)
            )
            # Newest task should be first.
            self.assertEqual(snap.tasks[0].id, "new_task000000002")
            self.assertEqual(snap.tasks[-1].id, "old_task000000001")

    def test_reports_sorted_descending(self) -> None:
        """Reports are sorted by created_timestamp descending."""
        with tempfile.TemporaryDirectory() as tmp:
            ws = create_mock_workspace(tmp)
            reports_dir = os.path.join(ws, "reports")

            write_report_file(
                reports_dir,
                report_id="old_rpt0000000001",
                created_timestamp="2026-01-01 00:00:00",
            )
            write_report_file(
                reports_dir,
                report_id="new_rpt0000000002",
                created_timestamp="2026-06-15 12:00:00",
            )
            write_report_file(
                reports_dir,
                report_id="mid_rpt0000000003",
                created_timestamp="2026-03-10 06:00:00",
            )

            snap = load_snapshot(workspace_path=ws)

            timestamps = [r.created_timestamp for r in snap.reports]
            self.assertEqual(
                timestamps, sorted(timestamps, reverse=True)
            )
            self.assertEqual(snap.reports[0].id, "new_rpt0000000002")
            self.assertEqual(snap.reports[-1].id, "old_rpt0000000001")

    def test_single_task_is_sorted(self) -> None:
        """A single-element list is trivially sorted."""
        with tempfile.TemporaryDirectory() as tmp:
            ws = create_mock_workspace(tmp)
            tasks_dir = os.path.join(ws, "tasks")
            write_task_file(tasks_dir, task_id="solo_task00000001")

            snap = load_snapshot(workspace_path=ws)
            self.assertEqual(len(snap.tasks), 1)

    def test_empty_workspace_is_sorted(self) -> None:
        """An empty workspace has no tasks or reports to sort."""
        with tempfile.TemporaryDirectory() as tmp:
            ws = create_mock_workspace(tmp)
            snap = load_snapshot(workspace_path=ws)
            self.assertEqual(len(snap.tasks), 0)
            self.assertEqual(len(snap.reports), 0)


class TestSparklineEventsField(unittest.TestCase):
    """sparkline_events contains all events uncapped for sparkline display."""

    def test_sparkline_events_default_empty(self) -> None:
        """StatusSnapshot constructed without sparkline_events defaults to ()."""
        snap = StatusSnapshot(
            workspace_name="w", workspace_root="/w",
            tasks=(), reports=(),
            task_counts_by_status=types.MappingProxyType({}),
            task_counts_by_owner=types.MappingProxyType({}),
            report_count=0, activity_timeline=(),
            snapshot_timestamp="now",
        )
        self.assertEqual(snap.sparkline_events, ())

    def test_sparkline_events_uncapped_vs_activity_timeline_capped(self) -> None:
        """sparkline_events has all events while activity_timeline is capped."""
        with tempfile.TemporaryDirectory() as tmp:
            ws = create_mock_workspace(tmp)
            tasks_dir = os.path.join(ws, "tasks")

            for i in range(10):
                write_task_file(
                    tasks_dir,
                    task_id=f"sparkle{i:010d}",
                    created_timestamp=f"2026-01-{i+1:02d} 00:00:00",
                )

            snap = load_snapshot(workspace_path=ws, activity_count=3)
            # activity_timeline is capped at 3
            self.assertLessEqual(len(snap.activity_timeline), 3)
            # sparkline_events should contain ALL events (at least 10)
            self.assertGreaterEqual(len(snap.sparkline_events), 10)

    def test_sparkline_events_populated_on_load(self) -> None:
        """load_snapshot populates sparkline_events for a workspace with data."""
        with tempfile.TemporaryDirectory() as tmp:
            ws = create_mock_workspace(tmp)
            tasks_dir = os.path.join(ws, "tasks")
            reports_dir = os.path.join(ws, "reports")

            write_task_file(tasks_dir, task_id="sparktask00000001")
            write_report_file(reports_dir, report_id="sparkrpt000000001")

            snap = load_snapshot(workspace_path=ws)
            # Should have at least 2 events (1 task created + 1 report created)
            self.assertGreaterEqual(len(snap.sparkline_events), 2)


class TestOwnerNormalization(unittest.TestCase):
    """Owner names are normalized to lowercase in aggregation counts."""

    def test_owner_counts_lowercase(self) -> None:
        """Mixed-case owners are merged under lowercase keys."""
        with tempfile.TemporaryDirectory() as tmp:
            ws = create_mock_workspace(tmp)
            tasks_dir = os.path.join(ws, "tasks")

            write_task_file(tasks_dir, task_id="owntest000000001",
                          owner="Alice")
            write_task_file(tasks_dir, task_id="owntest000000002",
                          owner="alice")
            write_task_file(tasks_dir, task_id="owntest000000003",
                          owner="ALICE")

            snap = load_snapshot(workspace_path=ws)
            owner_counts = snap.owner_counts_dict()

            # All three should be merged under "alice"
            self.assertEqual(owner_counts.get("alice"), 3)
            # No uppercase variants should exist
            self.assertNotIn("Alice", owner_counts)
            self.assertNotIn("ALICE", owner_counts)

    def test_unassigned_owner_lowercase(self) -> None:
        """Tasks with no owner are counted as '(unassigned)'."""
        with tempfile.TemporaryDirectory() as tmp:
            ws = create_mock_workspace(tmp)
            tasks_dir = os.path.join(ws, "tasks")

            write_task_file(tasks_dir, task_id="noown00000000001",
                          owner="")

            snap = load_snapshot(workspace_path=ws)
            owner_counts = snap.owner_counts_dict()
            self.assertIn("(unassigned)", owner_counts)
