"""
test_tui.py - Unit tests for the TUI application.

Uses Textual's ``app.run_test()`` async testing API to verify basic
app composition and keybinding behavior.
"""

import asyncio
import os
import sys
import tempfile
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

from unittest.mock import MagicMock
sys.modules.setdefault("venv", MagicMock())
sys.modules.setdefault("venv.venv", MagicMock())

from tests.helpers import create_mock_workspace, write_task_file, write_report_file


def _skip_if_no_textual():
    """Skip test if textual is not installed."""
    try:
        import textual
        return False
    except ImportError:
        return True


@unittest.skipIf(_skip_if_no_textual(), "textual not installed")
class TestAppStarts(unittest.TestCase):
    """CobotsStatusApp composes without errors."""

    def test_app_starts(self) -> None:
        from tui.app import CobotsStatusApp

        async def _run():
            with tempfile.TemporaryDirectory() as tmp:
                ws = create_mock_workspace(tmp)
                app = CobotsStatusApp(
                    workspace_path=ws,
                    no_refresh=True,
                    activity_count=5,
                )
                async with app.run_test(size=(120, 40)) as pilot:
                    # App should compose without errors.
                    self.assertIsNotNone(pilot.app)

        asyncio.run(_run())


@unittest.skipIf(_skip_if_no_textual(), "textual not installed")
class TestRefreshKeybinding(unittest.TestCase):
    """Pressing 'r' triggers a refresh action."""

    def test_refresh(self) -> None:
        from tui.app import CobotsStatusApp

        async def _run():
            with tempfile.TemporaryDirectory() as tmp:
                ws = create_mock_workspace(tmp)
                app = CobotsStatusApp(
                    workspace_path=ws,
                    no_refresh=True,
                    activity_count=5,
                )
                async with app.run_test(size=(120, 40)) as pilot:
                    # Press 'r' to refresh — should not crash.
                    await pilot.press("r")
                    # Give the worker time to complete.
                    await pilot.pause()

        asyncio.run(_run())


@unittest.skipIf(_skip_if_no_textual(), "textual not installed")
class TestArrowKeyNavigation(unittest.TestCase):
    """Arrow keys navigate rows when a DataTable has focus."""

    def test_table_focused_on_mount(self) -> None:
        """A DataTable should receive focus automatically on mount."""
        from tui.app import CobotsStatusApp
        from textual.widgets import DataTable

        async def _run():
            with tempfile.TemporaryDirectory() as tmp:
                ws = create_mock_workspace(tmp)
                app = CobotsStatusApp(
                    workspace_path=ws,
                    no_refresh=True,
                    activity_count=5,
                )
                async with app.run_test(size=(120, 40)) as pilot:
                    # Allow call_later to fire.
                    await pilot.pause()
                    await pilot.pause()
                    focused = app.focused
                    self.assertIsInstance(focused, DataTable)

        asyncio.run(_run())

    def test_arrow_keys_move_cursor(self) -> None:
        """Up/down arrow keys should move cursor in the focused DataTable."""
        from tui.app import CobotsStatusApp
        from tui.widgets.task_table import TaskTable

        async def _run():
            with tempfile.TemporaryDirectory() as tmp:
                ws = create_mock_workspace(tmp)
                tasks_dir = os.path.join(ws, "tasks")
                write_task_file(tasks_dir, task_id="aaaa1111bbbb2222", title="Task A")
                write_task_file(tasks_dir, task_id="bbbb2222cccc3333", title="Task B")
                write_task_file(tasks_dir, task_id="cccc3333dddd4444", title="Task C")

                app = CobotsStatusApp(
                    workspace_path=ws,
                    no_refresh=True,
                    activity_count=5,
                )
                async with app.run_test(size=(120, 40)) as pilot:
                    await pilot.pause()
                    await pilot.pause()
                    table = app.query_one(TaskTable)
                    table.focus()
                    await pilot.pause()

                    # Start at row 0, press down twice.
                    start_row = table.cursor_coordinate.row
                    await pilot.press("down")
                    await pilot.pause()
                    after_down = table.cursor_coordinate.row
                    # Cursor should have moved (or stayed at 0 if table is
                    # empty, but we added 3 tasks so it should move).
                    if table.row_count > 1:
                        self.assertGreater(after_down, start_row)

                    # Press up to go back.
                    await pilot.press("up")
                    await pilot.pause()
                    after_up = table.cursor_coordinate.row
                    self.assertEqual(after_up, start_row)

        asyncio.run(_run())


@unittest.skipIf(_skip_if_no_textual(), "textual not installed")
class TestVimJKNavigation(unittest.TestCase):
    """Vim j/k keybindings navigate rows in focused DataTable."""

    def test_j_moves_cursor_down(self) -> None:
        from tui.app import CobotsStatusApp
        from tui.widgets.task_table import TaskTable

        async def _run():
            with tempfile.TemporaryDirectory() as tmp:
                ws = create_mock_workspace(tmp)
                tasks_dir = os.path.join(ws, "tasks")
                write_task_file(tasks_dir, task_id="aaaa1111bbbb2222", title="Task A")
                write_task_file(tasks_dir, task_id="bbbb2222cccc3333", title="Task B")

                app = CobotsStatusApp(
                    workspace_path=ws,
                    no_refresh=True,
                    activity_count=5,
                )
                async with app.run_test(size=(120, 40)) as pilot:
                    await pilot.pause()
                    await pilot.pause()
                    table = app.query_one(TaskTable)
                    table.focus()
                    await pilot.pause()

                    start_row = table.cursor_coordinate.row
                    await pilot.press("j")
                    await pilot.pause()
                    if table.row_count > 1:
                        self.assertGreater(
                            table.cursor_coordinate.row, start_row
                        )

        asyncio.run(_run())

    def test_k_moves_cursor_up(self) -> None:
        from tui.app import CobotsStatusApp
        from tui.widgets.task_table import TaskTable

        async def _run():
            with tempfile.TemporaryDirectory() as tmp:
                ws = create_mock_workspace(tmp)
                tasks_dir = os.path.join(ws, "tasks")
                write_task_file(tasks_dir, task_id="aaaa1111bbbb2222", title="Task A")
                write_task_file(tasks_dir, task_id="bbbb2222cccc3333", title="Task B")

                app = CobotsStatusApp(
                    workspace_path=ws,
                    no_refresh=True,
                    activity_count=5,
                )
                async with app.run_test(size=(120, 40)) as pilot:
                    await pilot.pause()
                    await pilot.pause()
                    table = app.query_one(TaskTable)
                    table.focus()
                    await pilot.pause()

                    # Move down first, then back up with k.
                    await pilot.press("j")
                    await pilot.pause()
                    row_after_j = table.cursor_coordinate.row
                    await pilot.press("k")
                    await pilot.pause()
                    row_after_k = table.cursor_coordinate.row
                    if table.row_count > 1:
                        self.assertLess(row_after_k, row_after_j)

        asyncio.run(_run())


@unittest.skipIf(_skip_if_no_textual(), "textual not installed")
class TestVimGJumpNavigation(unittest.TestCase):
    """Vim g/G jump to first/last row in focused DataTable."""

    def test_g_jumps_to_first_row(self) -> None:
        from tui.app import CobotsStatusApp
        from tui.widgets.task_table import TaskTable

        async def _run():
            with tempfile.TemporaryDirectory() as tmp:
                ws = create_mock_workspace(tmp)
                tasks_dir = os.path.join(ws, "tasks")
                write_task_file(tasks_dir, task_id="aaaa1111bbbb2222", title="Task A")
                write_task_file(tasks_dir, task_id="bbbb2222cccc3333", title="Task B")
                write_task_file(tasks_dir, task_id="cccc3333dddd4444", title="Task C")

                app = CobotsStatusApp(
                    workspace_path=ws,
                    no_refresh=True,
                    activity_count=5,
                )
                async with app.run_test(size=(120, 40)) as pilot:
                    await pilot.pause()
                    await pilot.pause()
                    table = app.query_one(TaskTable)
                    table.focus()
                    await pilot.pause()

                    # Move down, then press g to go back to first row.
                    await pilot.press("j")
                    await pilot.press("j")
                    await pilot.pause()
                    await pilot.press("g")
                    await pilot.pause()
                    self.assertEqual(table.cursor_coordinate.row, 0)

        asyncio.run(_run())

    def test_G_jumps_to_last_row(self) -> None:
        from tui.app import CobotsStatusApp
        from tui.widgets.task_table import TaskTable

        async def _run():
            with tempfile.TemporaryDirectory() as tmp:
                ws = create_mock_workspace(tmp)
                tasks_dir = os.path.join(ws, "tasks")
                write_task_file(tasks_dir, task_id="aaaa1111bbbb2222", title="Task A")
                write_task_file(tasks_dir, task_id="bbbb2222cccc3333", title="Task B")
                write_task_file(tasks_dir, task_id="cccc3333dddd4444", title="Task C")

                app = CobotsStatusApp(
                    workspace_path=ws,
                    no_refresh=True,
                    activity_count=5,
                )
                async with app.run_test(size=(120, 40)) as pilot:
                    await pilot.pause()
                    await pilot.pause()
                    table = app.query_one(TaskTable)
                    table.focus()
                    await pilot.pause()

                    # Press G (shift+g) to jump to last row.
                    await pilot.press("G")
                    await pilot.pause()
                    if table.row_count > 0:
                        self.assertEqual(
                            table.cursor_coordinate.row,
                            table.row_count - 1,
                        )

        asyncio.run(_run())


@unittest.skipIf(_skip_if_no_textual(), "textual not installed")
class TestVimHLTabSwitching(unittest.TestCase):
    """Vim h/l keybindings switch between tabs."""

    def test_l_switches_to_next_tab(self) -> None:
        from tui.app import CobotsStatusApp
        from textual.widgets import TabbedContent

        async def _run():
            with tempfile.TemporaryDirectory() as tmp:
                ws = create_mock_workspace(tmp)
                app = CobotsStatusApp(
                    workspace_path=ws,
                    no_refresh=True,
                    activity_count=5,
                )
                async with app.run_test(size=(120, 40)) as pilot:
                    await pilot.pause()
                    await pilot.pause()
                    tc = app.query_one(TabbedContent)
                    initial_tab = tc.active

                    # Press l to switch to next tab.
                    await pilot.press("l")
                    await pilot.pause()
                    await pilot.pause()
                    self.assertNotEqual(tc.active, initial_tab)

        asyncio.run(_run())

    def test_h_switches_to_previous_tab(self) -> None:
        from tui.app import CobotsStatusApp
        from textual.widgets import TabbedContent

        async def _run():
            with tempfile.TemporaryDirectory() as tmp:
                ws = create_mock_workspace(tmp)
                app = CobotsStatusApp(
                    workspace_path=ws,
                    no_refresh=True,
                    activity_count=5,
                )
                async with app.run_test(size=(120, 40)) as pilot:
                    await pilot.pause()
                    await pilot.pause()
                    tc = app.query_one(TabbedContent)
                    initial_tab = tc.active

                    # Go next first, then come back with h.
                    await pilot.press("l")
                    await pilot.pause()
                    await pilot.pause()
                    self.assertNotEqual(tc.active, initial_tab)

                    await pilot.press("h")
                    await pilot.pause()
                    await pilot.pause()
                    self.assertEqual(tc.active, initial_tab)

        asyncio.run(_run())

    def test_table_focused_after_tab_switch(self) -> None:
        """DataTable in the newly activated tab should receive focus."""
        from tui.app import CobotsStatusApp
        from textual.widgets import DataTable

        async def _run():
            with tempfile.TemporaryDirectory() as tmp:
                ws = create_mock_workspace(tmp)
                app = CobotsStatusApp(
                    workspace_path=ws,
                    no_refresh=True,
                    activity_count=5,
                )
                async with app.run_test(size=(120, 40)) as pilot:
                    await pilot.pause()
                    await pilot.pause()
                    # Switch to reports tab.
                    await pilot.press("l")
                    await pilot.pause()
                    await pilot.pause()
                    focused = app.focused
                    self.assertIsInstance(focused, DataTable)

        asyncio.run(_run())


@unittest.skipIf(_skip_if_no_textual(), "textual not installed")
class TestCursorPreservationOnRefresh(unittest.TestCase):
    """Cursor position is preserved when the table is refreshed."""

    def test_task_table_cursor_preserved(self) -> None:
        """Task table preserves cursor row across snapshot updates."""
        from tui.app import CobotsStatusApp
        from tui.widgets.task_table import TaskTable

        async def _run():
            with tempfile.TemporaryDirectory() as tmp:
                ws = create_mock_workspace(tmp)
                tasks_dir = os.path.join(ws, "tasks")
                write_task_file(
                    tasks_dir,
                    task_id="aaaa1111bbbb2222",
                    title="Task A",
                    created_timestamp="2026-01-01 00:00:00",
                )
                write_task_file(
                    tasks_dir,
                    task_id="bbbb2222cccc3333",
                    title="Task B",
                    created_timestamp="2026-02-01 00:00:00",
                )
                write_task_file(
                    tasks_dir,
                    task_id="cccc3333dddd4444",
                    title="Task C",
                    created_timestamp="2026-03-01 00:00:00",
                )

                app = CobotsStatusApp(
                    workspace_path=ws,
                    no_refresh=True,
                    activity_count=5,
                )
                async with app.run_test(size=(120, 40)) as pilot:
                    await pilot.pause()
                    await pilot.pause()
                    table = app.query_one(TaskTable)
                    table.focus()
                    await pilot.pause()

                    # Move to row 2.
                    await pilot.press("down")
                    await pilot.press("down")
                    await pilot.pause()
                    self.assertEqual(table.cursor_coordinate.row, 2)

                    # Refresh triggers update_from_snapshot.
                    await pilot.press("r")
                    await pilot.pause()
                    await pilot.pause()

                    # Cursor should still be at row 2.
                    self.assertEqual(table.cursor_coordinate.row, 2)

        asyncio.run(_run())

    def test_cursor_clamped_when_rows_shrink(self) -> None:
        """Cursor clamps to last row when item count decreases."""
        from tui.app import CobotsStatusApp
        from tui.widgets.task_table import TaskTable
        from data import load_snapshot

        async def _run():
            with tempfile.TemporaryDirectory() as tmp:
                ws = create_mock_workspace(tmp)
                tasks_dir = os.path.join(ws, "tasks")
                paths = []
                for i, tid in enumerate([
                    "aaaa1111bbbb2222",
                    "bbbb2222cccc3333",
                    "cccc3333dddd4444",
                ]):
                    p = write_task_file(
                        tasks_dir,
                        task_id=tid,
                        title=f"Task {i}",
                        created_timestamp=f"2026-0{i+1}-01 00:00:00",
                    )
                    paths.append(p)

                app = CobotsStatusApp(
                    workspace_path=ws,
                    no_refresh=True,
                    activity_count=5,
                )
                async with app.run_test(size=(120, 40)) as pilot:
                    await pilot.pause()
                    await pilot.pause()
                    table = app.query_one(TaskTable)
                    table.focus()
                    await pilot.pause()

                    # Move to last row (row 2).
                    await pilot.press("down")
                    await pilot.press("down")
                    await pilot.pause()
                    self.assertEqual(table.cursor_coordinate.row, 2)

                    # Remove two tasks, leaving only 1 row.
                    os.remove(paths[0])
                    os.remove(paths[1])

                    # Refresh.
                    await pilot.press("r")
                    await pilot.pause()
                    await pilot.pause()

                    # Cursor should be clamped to row 0 (only row).
                    self.assertEqual(table.row_count, 1)
                    self.assertEqual(table.cursor_coordinate.row, 0)

        asyncio.run(_run())

    def test_report_table_cursor_preserved(self) -> None:
        """Report table preserves cursor row across snapshot updates."""
        from tui.app import CobotsStatusApp
        from tui.widgets.report_table import ReportTable

        async def _run():
            with tempfile.TemporaryDirectory() as tmp:
                ws = create_mock_workspace(tmp)
                reports_dir = os.path.join(ws, "reports")
                write_report_file(
                    reports_dir,
                    report_id="rpt0000100000001",
                    title="Report A",
                    created_timestamp="2026-01-01 00:00:00",
                )
                write_report_file(
                    reports_dir,
                    report_id="rpt0000200000002",
                    title="Report B",
                    created_timestamp="2026-02-01 00:00:00",
                )
                write_report_file(
                    reports_dir,
                    report_id="rpt0000300000003",
                    title="Report C",
                    created_timestamp="2026-03-01 00:00:00",
                )

                app = CobotsStatusApp(
                    workspace_path=ws,
                    no_refresh=True,
                    activity_count=5,
                )
                async with app.run_test(size=(120, 40)) as pilot:
                    await pilot.pause()
                    await pilot.pause()

                    # Switch to Reports tab.
                    await pilot.press("l")
                    await pilot.pause()
                    await pilot.pause()

                    table = app.query_one(ReportTable)
                    table.focus()
                    await pilot.pause()

                    # Move to row 1.
                    await pilot.press("down")
                    await pilot.pause()
                    self.assertEqual(table.cursor_coordinate.row, 1)

                    # Refresh.
                    await pilot.press("r")
                    await pilot.pause()
                    await pilot.pause()

                    # Cursor should still be at row 1.
                    self.assertEqual(table.cursor_coordinate.row, 1)

        asyncio.run(_run())

    def test_empty_table_no_crash(self) -> None:
        """Refreshing an empty table does not crash."""
        from tui.app import CobotsStatusApp
        from tui.widgets.task_table import TaskTable

        async def _run():
            with tempfile.TemporaryDirectory() as tmp:
                ws = create_mock_workspace(tmp)
                app = CobotsStatusApp(
                    workspace_path=ws,
                    no_refresh=True,
                    activity_count=5,
                )
                async with app.run_test(size=(120, 40)) as pilot:
                    await pilot.pause()
                    await pilot.pause()
                    table = app.query_one(TaskTable)
                    self.assertEqual(table.row_count, 0)

                    # Refresh on empty table should not crash.
                    await pilot.press("r")
                    await pilot.pause()
                    await pilot.pause()
                    self.assertEqual(table.row_count, 0)

        asyncio.run(_run())


@unittest.skipIf(_skip_if_no_textual(), "textual not installed")
class TestDescendingSortInTui(unittest.TestCase):
    """Tasks and reports appear newest-first in the TUI tables."""

    def test_tasks_newest_first_in_table(self) -> None:
        """Task table rows are ordered newest-first."""
        from tui.app import CobotsStatusApp
        from tui.widgets.task_table import TaskTable

        async def _run():
            with tempfile.TemporaryDirectory() as tmp:
                ws = create_mock_workspace(tmp)
                tasks_dir = os.path.join(ws, "tasks")
                write_task_file(
                    tasks_dir,
                    task_id="old_task000000001",
                    title="Old Task",
                    created_timestamp="2026-01-01 00:00:00",
                )
                write_task_file(
                    tasks_dir,
                    task_id="new_task000000002",
                    title="New Task",
                    created_timestamp="2026-06-01 00:00:00",
                )

                app = CobotsStatusApp(
                    workspace_path=ws,
                    no_refresh=True,
                    activity_count=5,
                )
                async with app.run_test(size=(120, 40)) as pilot:
                    await pilot.pause()
                    await pilot.pause()
                    table = app.query_one(TaskTable)

                    # First row should be the newest task.
                    self.assertEqual(table.row_count, 2)
                    item = table.get_selected_item(app.snapshot)
                    self.assertIsNotNone(item)
                    self.assertEqual(item.id, "new_task000000002")

        asyncio.run(_run())


@unittest.skipIf(_skip_if_no_textual(), "textual not installed")
class TestReportDetailScreenDismiss(unittest.TestCase):
    """ESC and q keys dismiss the ReportDetailScreen."""

    def test_escape_dismisses_report_detail_screen(self) -> None:
        """Pressing ESC on the detail screen pops it and returns to main."""
        from tui.app import CobotsStatusApp
        from tui.screens.report_detail_screen import ReportDetailScreen
        from tui.widgets.report_table import ReportTable

        async def _run():
            with tempfile.TemporaryDirectory() as tmp:
                ws = create_mock_workspace(tmp)
                reports_dir = os.path.join(ws, "reports")
                write_report_file(
                    reports_dir,
                    report_id="rpt_esc_test00001",
                    title="ESC Test Report",
                    body="Body for ESC test.",
                )

                app = CobotsStatusApp(
                    workspace_path=ws,
                    no_refresh=True,
                    activity_count=5,
                )
                async with app.run_test(size=(120, 40)) as pilot:
                    await pilot.pause()
                    await pilot.pause()

                    # Switch to Reports tab.
                    await pilot.press("l")
                    await pilot.pause()
                    await pilot.pause()

                    table = app.query_one(ReportTable)
                    table.focus()
                    await pilot.pause()

                    # Select the report row to push the detail screen.
                    await pilot.press("enter")
                    await pilot.pause()
                    await pilot.pause()

                    # Verify the detail screen is now active.
                    self.assertIsInstance(
                        app.screen, ReportDetailScreen
                    )

                    # Press ESC to dismiss.
                    await pilot.press("escape")
                    await pilot.pause()

                    # The detail screen should be gone; we should be
                    # back on the main screen.
                    self.assertNotIsInstance(
                        app.screen, ReportDetailScreen
                    )

        asyncio.run(_run())

    def test_q_dismisses_report_detail_screen(self) -> None:
        """Pressing q on the detail screen pops it instead of quitting."""
        from tui.app import CobotsStatusApp
        from tui.screens.report_detail_screen import ReportDetailScreen
        from tui.widgets.report_table import ReportTable

        async def _run():
            with tempfile.TemporaryDirectory() as tmp:
                ws = create_mock_workspace(tmp)
                reports_dir = os.path.join(ws, "reports")
                write_report_file(
                    reports_dir,
                    report_id="rpt_q_test0000001",
                    title="Q Test Report",
                    body="Body for q-dismiss test.",
                )

                app = CobotsStatusApp(
                    workspace_path=ws,
                    no_refresh=True,
                    activity_count=5,
                )
                async with app.run_test(size=(120, 40)) as pilot:
                    await pilot.pause()
                    await pilot.pause()

                    # Switch to Reports tab.
                    await pilot.press("l")
                    await pilot.pause()
                    await pilot.pause()

                    table = app.query_one(ReportTable)
                    table.focus()
                    await pilot.pause()

                    # Open the detail screen.
                    await pilot.press("enter")
                    await pilot.pause()
                    await pilot.pause()

                    self.assertIsInstance(
                        app.screen, ReportDetailScreen
                    )

                    # Press q to dismiss (should NOT quit the app).
                    await pilot.press("q")
                    await pilot.pause()

                    # Should be back on the main screen.
                    self.assertNotIsInstance(
                        app.screen, ReportDetailScreen
                    )

        asyncio.run(_run())


if __name__ == "__main__":
    unittest.main()
